import zmq
import time
import signal
from threading import Thread

import pickle
import cv2

# This script is a fake sever that send messages to the fakezmqclient.py script.

# Global variable to signal threads to exit
exit_flag = False
counter = 0

def fakeServer(port, topic, message, sleep_time):
    global counter
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:{}".format(port))
    while not exit_flag:
        counter += 1
        socket.send_string(f'{topic} {message + str(counter)}')
        time.sleep(sleep_time/2)

def fakeVideoServer(port, topic, videoFile, sleep_time):
        # Read the video file and send frame by frame on client with a 1 second delay
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.bind("tcp://*:{}".format(port))
        while not exit_flag:
            with cv2.VideoCapture(videoFile) as f:
                while True:
                    ret, frame = f.read()
                    if ret:
                        socket.send_string(f'{topic} {pickle.dumps(frame)}')
                        time.sleep(sleep_time)
                    else:
                        break

def signal_handler(sig, frame):
    global exit_flag
    print("Ctrl+C received. Exiting...")
    exit_flag = True

def main():
    # Set up the Ctrl+C signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Create a thread for each server
    threads = []
    for i in range(10):
        t = Thread(target=fakeServer, args=(5555+i, f'topic{i}', f'message{i}', i))
        t.start()
        threads.append(t)
    # create a image publisher
    while not exit_flag:
        time.sleep(1)
    for t in threads:
        t.stop()

if __name__ == "__main__":
    main()