import zmq
import threading
import time
from typing import Callable, List, Dict, ByteString

from collections import deque

class ZmqSubscriber(object):
    '''
        Implements a zmq subscriber that subscribes to a list of servers and topics.

        This class is a singleton.
    '''
    def __init__(self):
        self.zmqServerPortTopics = []
        self.zmqMostRecentData = {}
        self.zmqMetrics = {}
        self.zmqRecordingUUIDs = []
        self.threads = []
        self.metricsHistry = {}
        self.dataTypeDict = {}
        self.metrics = {}
        # Spawn a thread to calculate the average metrics
        t = threading.Thread(target=self.__calculateAverageMetrics)
        t.start()

    def __new__(cls):
        '''
            This function implements the singleton pattern.
        '''
        if not hasattr(cls, 'instance'):
            cls.instance = super(ZmqSubscriber, cls).__new__(cls)
        return cls.instance

    def _recordMessage(self, uuid: str, message: ByteString):
        '''
            TODO: I should probably add a timestamp to thet datastream for playback purposes.
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
                self._recordMessage(uuid, message)

    def _crafteUUID(self, server_ip, port, topic):
        return f'{server_ip}-{port}-{topic}'

    def getStatus(self, uuid: str) -> str:
        '''
            Naive implementation of a status check. If the uuid is not in the dictionary, then return unknown.
            If the uuid is in the dictionary, then check the time. If the time is greater than 5 seconds, then
            return disconnected. Otherwise, return connected.

            TODO: We should probably add a timeout to the thread that is subscribing to the server and topic.
                If the thread times out, then we should return disconnected.
        '''
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

    def getMetrics(self, filterIds: List[str] | None = None) -> Dict[str, Dict[str, int]]:
        '''
            This function returns the metrics for all uuids.
        '''
        if filterIds is None:
            return self.metrics
        returnMessage = {}
        for uuid in self.getUUIDs():
            if uuid not in filterIds:
                continue
            returnMessage[uuid] = {
                'message_rate': self.metrics[uuid]['message_rate'],
                'payload_rate': self.metrics[uuid]['payload_rate'],
                'time_delta': self.metrics[uuid]['time_delta'],
                'previous_time': self.metrics[uuid]['previous_time'],
            }
        return returnMessage
    
    def __calculateAverageMetrics(self):
        '''
            This function calculates the average metrics for all uuids.

            This function is meant to be run in a thread and is not meant to be called directly.
        '''
        previous_time = time.time()
        while True:
            time.sleep(1)
            time_delta = time.time() - previous_time
            # Update the metrics for each uuid
            for uuid in self.getUUIDs():
                message_rate = self.zmqMetrics[uuid]['message_count'] / time_delta
                payload_rate = self.zmqMetrics[uuid]['payload_bytes'] / 1024 / time_delta
                self.metrics[uuid] = {
                    'message_rate': message_rate,
                    'payload_rate': payload_rate,
                    'time_delta': time_delta,
                    'previous_time': previous_time,
                }
                self.zmqMetrics[uuid]['message_count'] = 0
                self.zmqMetrics[uuid]['payload_bytes'] = 0
            previous_time = time.time()
    
    def startRecording(self, uuid: str) -> None:
        self.zmqRecordingUUIDs.append(uuid)

    def stopRecording(self, uuid: str) -> None:
        self.zmqRecordingUUIDs.remove(uuid)