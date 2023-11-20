'''
    Implements a dash web app that displays zmq messages going through the system.
'''

# Imports
import os
import sys
import time
import json
import subprocess
import traceback
import zmq

from dashPage import DashServer

def argParse():
    import argparse
    parser = argparse.ArgumentParser(description='Run the ZMQ Message Viewer')
    parser.add_argument('--debug', action='store_true', help='Run the server in debug mode')
    parser.add_argument('--port', type=int, default=8050, help='Port to run the server on')
    parser.add_argument('--server_config', type=str, default='monitorConfig.yaml', help='Path to the server configuration file')
    parser.add_argument('--navigation_config', type=str, default='navigationConfig.yaml', help='Path to the navigation configuration file')
    return parser.parse_args()

if __name__ == '__main__':
    args = argParse()
    server = DashServer(args)
    server.setBaseLayout()
    server.run_server(debug=args.debug, port=args.port)
    