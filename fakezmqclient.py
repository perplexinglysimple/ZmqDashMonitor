import zmq
import time
import threading
# This script is a fake client that recieves from themessages to the fakezmqclient.py script.

def fakeClient(port, topic, message):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:{}".format(port))
    socket.setsockopt_string(zmq.SUBSCRIBE, topic)
    while True:
        message = socket.recv_string()
        print(message)
        time.sleep(1)

def main():
    # Create a thread for each server
    for i in range(10):
        t = threading.Thread(target=fakeClient, args=(5555+i, f'topic{i}', f'message{i}'))
        t.start()
    while True:
        time.sleep(1)
        
if __name__ == "__main__":
    main()