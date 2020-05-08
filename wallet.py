import rsa
from blockchain import *
from transaction import *
import time
import sys
import json
import os.path
import platform
import socket
from threading import Thread
from node import Node

VERSION = 0.1
SAVE_FILE = 'save.txt'
DEBUG = True

py = platform.python_version()

if py[0] != '3':
    print("Python 3 required. Current: {}".format(py))
    print("Closing in 10 seconds.")
    time.sleep(10)
    sys.exit()

print("=== YosCoin Wallet v{} ===".format(VERSION))

node = Node()

if os.path.exists(SAVE_FILE):
    try:
        node = Node.loadFromFile(SAVE_FILE)
        print("Node loaded from save file.")
    except Exception as e:
        print("Existing node load failed. Creating new instead.")
        if DEBUG:
            raise e
else:
    print("New node generated.")

node.connect()

if not node.chain:
    print("Requesting chain from other nodes.")
    node.requestChain()

time.sleep(1)

print()
print("Available commands: addPeer <peer>, mine, stopMining, quit.")

while 1:
    command = input(">> ")
    terms = command.split(" ")
    if terms[0] == "quit":
        node.listener.close()
        node.saveToFile(SAVE_FILE)
        sys.exit()
    elif terms[0] == "mine":
        node.mine()
    elif terms[0] == "requestChain":
        node.requestChain()
    elif terms[0] == "shareChain":
        node.shareChain()
    elif terms[0] == "stopMining":
        node.stopMining()
    elif terms[0] == "addPeer":
        node.addPeer(terms[1])
    else:
        print("Unknown command!")