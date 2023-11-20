import zmq
import threading
import time
from typing import Callable, List, Dict, ByteString

from collections import deque

class ZmqSubscriber():
    '''
        This class implements a zmq subscriber that subscribes to a list of servers and topics.
    '''
    def __init__(self):
        self.zmqServerPortTopics = []
        self.zmqMostRecentData = {}
        self.zmqMetrics = {}
        self.zmqRecordingUUIDs = []
        self.threads = []
        self.metricsHistry = {}
        self.dataTypeDict = {}

    def _recodMessage(self, uuid: str, message: ByteString):
        '''
            This function writes the message to a file.

            TODO: We should probably add a timestamp to thet datastream for playback purposes.
        '''
        with open(f'{uuid}.txt', 'ab') as f:
            f.write(f'!Q{len(message)}'.encode())
            f.wrie(message)

    def _subscribeToServer(self, server_ip, port, topic, uuid):
        '''
            This function subscribes to a zmq server and topic and places the messages in the most recent data dictionary.

            This function is meant to be run in a thread and is not meant to be called directly.
        '''
        context = zmq.Context()
        subscriber = context.socket(zmq.SUB)
        if topic is None:
            subscriber.connect("tcp://{}:{}".format(server_ip, port))
            subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
        else:
            subscriber.connect("tcp://{}:{}".format(server_ip, port))
            subscriber.setsockopt_string(zmq.SUBSCRIBE, topic)
        
        self.zmqMetrics[uuid] = {'message_count':0, 'start_time':time.time(), 'payload_bytes':0}

        while True:
            message = subscriber.recv_string()
            #Place the message and the time it was received in the most recent data dictionary
            self.zmqMostRecentData[uuid] = {'message': message, 'time': time.time()}
            # Increment the number of messages received
            self.zmqMetrics[uuid]['message_count'] += 1
            # Increment the number of bytes received
            self.zmqMetrics[uuid]['payload_bytes'] += len(message)
            # If the uuid is being recorded, then write the message to a file
            if uuid in self.zmqRecordingUUIDs:
                self._recodMessage(uuid, message)

    def _crafteUUID(self, server_ip, port, topic):
        '''
            This function crafts a uuid from the server ip, port, and topic.
        '''
        return f'{server_ip}-{port}-{topic}'

    def getStatus(self, uuid: str) -> str:
        '''
            Naive implementation of a status check. If the uuid is not in the dictionary, then return unknown.
            If the uuid is in the dictionary, then check the time. If the time is greater than 5 seconds, then
            return disconnected. Otherwise, return connected.

            TODO: We should probably add a timeout to the thread that is subscribing to the server and topic.
                If the thread times out, then we should return disconnected.
        '''
        print(f"uuid: {uuid}, self.zmqMostRecentData: {self.zmqMostRecentData.keys()} status: {uuid in self.zmqMostRecentData.keys()}")
        if uuid not in self.zmqMostRecentData.keys():
            return 'Unknown'
        elif time.time() - self.zmqMostRecentData[uuid]['time'] > 5:
            return 'Disconnected'
        else:
            return 'Connected'

    def isZmqServerPortTopicSubscribed(self, server_ip: str, port: str | int, topic: str) -> bool:
        '''
            This function checks if the server, port, and topic are already subscribed to.
        '''
        uuid = self._crafteUUID(server_ip, port, topic)
        return uuid in self.zmqServerPortTopics

    def addZmqServerPortTopic(self, server_ip: str, port: str | int, topic: str, data_type) -> str:
        '''
            This function adds a zmq server, port, and topic to the list of servers to subscribe to.
            It also starts a thread to subscribe to the server and topic.
        '''
        uuid = self._crafteUUID(server_ip, port, topic)
        # If the uuid is already in the dictionary, then return the uuid and log
        if uuid in self.dataTypeDict:
            print(f"ERROR: UUID {uuid} already exists in the dictionary")
            return uuid
        self.metricsHistry[uuid] = deque(maxlen=10)
        self.dataTypeDict[uuid] = data_type
        self.zmqServerPortTopics.append({'ip':server_ip, 'port':port, 'topic':topic, 'dataType': data_type, 'uuid':uuid})
        # Start a thread to subscribe to the server and topic
        t = threading.Thread(target=self._subscribeToServer, args=(server_ip, port, topic, uuid))
        t.start()
        self.threads.append(t)
        return uuid
    
    def lookupUUID(self, server_ip: str, port: str | int, topic: str) -> str:
        '''
            This function looks up the uuid for a server, port, and topic.

            TODO: Should I throw if it doesn't exist?
        '''
        return self._crafteUUID(server_ip, port, topic)

    def getUUIDs(self) -> List[str]:
        '''
            This function returns a list of uuids that are subscribed to.
        '''
        return [serverPortTopic['uuid'] for serverPortTopic in self.zmqServerPortTopics]
    
    def getDataType(self, uuid) -> str | None:
        '''
            This function returns the data type of the uuid.

            This is used to determine how to display the data.
        '''
        return self.dataTypeDict.get(uuid, None)

    def getMostRecentData(self, uuid) -> str | None:
        '''
            This function returns the most recent data for a uuid.
        '''
        # There is no garuntee that the uuid will be in the dictionary
        # If it is not, then return None
        return self.zmqMostRecentData.get(uuid, None)
    
    def getMostRecentDataAll(self) -> Dict[str, any]:
        '''
            This function returns the most recent data for all uuids.
        '''
        return self.zmqMostRecentData
    
    def getAverageMetricsFromHistory(self, uuid):
        '''
            This function returns the average metrics from the history.
            
            TODO: This function is not used. Should we use it?
        '''
        #Average the metrics in the history
        returnMessage = {'message_rate':0, 'payload_rate':0, 'time_delta':0}
        for metric in self.metricsHistry[uuid]:
            returnMessage['message_rate'] += metric['message_rate']
            returnMessage['payload_rate'] += metric['payload_rate']
            returnMessage['time_delta'] += metric['time_delta']
        returnMessage['message_rate'] /= metric['time_delta']
        returnMessage['payload_rate'] /= metric['time_delta']
        return returnMessage

    def getMetrics(self) -> Dict[str, Dict[str, int]]:
        '''
            This function returns the metrics for all uuids.

            TODO: Spawn a thread to calculate the average metrics and return the most recent metrics here.
        '''
        end_time = time.time()
        returnMessage = {}
        for uuid, metrics in self.zmqMetrics.items():
            # Calculate the playload rate in KB/s and the message rate in messages/s
            # returnMessage[uuid] = {'message_rate':metrics['message_count'], 'payload_rate':metrics['payload_bytes']/1024}
            # self.zmqMetrics[uuid] = {'message_count':0, 'start_time':time.time(), 'payload_bytes':0}
            temp = {}
            temp['message_rate'] = metrics['message_count']
            # In KB/s
            temp['payload_rate'] = metrics['payload_bytes'] / 1024
            temp['time_delta'] = end_time - metrics['start_time']
            # Reset the metrics
            self.zmqMetrics[uuid] = {'message_count':0, 'start_time':time.time(), 'payload_bytes':0}
            # Add the metrics to the history
            self.metricsHistry[uuid].append(temp)
            # Generate the resturn message using the history
            returnMessage[uuid] = self.getAverageMetricsFromHistory(uuid)
        return returnMessage
    
    def startRecording(self, uuid: str) -> None:
        self.zmqRecordingUUIDs.append(uuid)

    def stopRecording(self, uuid: str) -> None :
        self.zmqRecordingUUIDs.remove(uuid)