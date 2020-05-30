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

def runCommand(command):
    global prevCmd
    terms = command.split(" ")
    if terms[0] == "quit":
        node.listener.close()
        node.stopMining()
        node.saveToFile(SAVE_FILE)
        sys.exit()
    elif terms[0] == "mine":
        node.mine()
    elif terms[0] == "requestChain":
        node.requestChain()
    elif terms[0] == "shareChain":
        node.shareChain()
    elif terms[0] == "ping":
        node.ping()
    elif terms[0] == "stopMining":
        node.stopMining()
    elif terms[0] == "addPeer":
        node.addPeer(terms[1])
    elif terms[0] == "balance":
        print(node.balance())
    elif terms[0] == "give":
        node.give(PubKeyWrapper({"n": int(terms[1]), "e": int(terms[2])}), float(terms[3]))
    elif terms[0] == "validate":
        print(Blockchain.validate(node.chain))
    elif terms[0] == "genesis":
        node.chain = Blockchain()
    elif terms[0] == "height":
        print(len(node.chain.blocks))
    elif terms[0] == "debug":
        node.debug = not node.debug
        print("Debug set to {}".format(node.debug))
    elif terms[0] == "prev":
        try:
            prevCmd
        except NameError:
            print("No previous command.")
            return
        print(">> " + prevCmd)
        runCommand(prevCmd)
    elif terms[0] == "eval":
        try:
            print(eval(input("In: ")))
        except Exception as e:
            print(e)
    else:
        print("Unknown command!")
    
    if terms[0] != "prev":
        prevCmd = command
        
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
print("Available commands: addPeer <peer>, balance, give <peer> <amt>, mine, quit, requestChain, shareChain, stopMining.")

while 1:
    command = input(">> ")
    runCommand(command)

