from blockchain import Blockchain
import time
import sys
import os.path
from node import Node
from cryptography import PubKey

VERSION = 1.0
SAVE_FILE = 'save.txt'

# Wraps Node with commands/saving functionality
class Wallet:
    def __init__(self):
        self.node = Node()
        self.prevCmd = None
        self.running = False

    def run(self):
        print("=== ConciseCoin Wallet v{} ===".format(VERSION))
        print()
        print("Available commands: addPeer <peer>, balance, debug, genesis, give <address n> <address e> <amt>, height, mine, ping, quit, requestChain, shareChain, stopMining.")
        print()

        if os.path.exists(SAVE_FILE):
            self.loadNode(SAVE_FILE)

        self.node.connect()
        time.sleep(1)

        self.running = True
        while self.running:
            self.runCommand(input(">> "))

    def loadNode(self, path):
        try:
            self.node = Node.loadFromFile(path)
            print("Node loaded from save file.")
        except Exception:
            print("Existing node load failed.")

    def runCommand(self, command):
        terms = command.split(" ")
        if terms[0] == "quit":
            self.saveQuit()
        elif terms[0] == "mine":
            self.node.mine()
        elif terms[0] == "requestChain":
            self.node.requestChain()
        elif terms[0] == "shareChain":
            self.node.shareChain()
        elif terms[0] == "ping":
            self.node.ping()
        elif terms[0] == "stopMining":
            self.node.stopMining()
        elif terms[0] == "addPeer":
            self.node.addPeer(terms[1])
        elif terms[0] == "balance":
            print(self.node.balance())
        elif terms[0] == "give":
            self.node.give(
                PubKey(int(terms[1]), int(terms[2])), float(terms[3]))
        elif terms[0] == "validate":
            print(Blockchain.validate(self.node.chain))
        elif terms[0] == "genesis":
            self.node.chain = Blockchain()
        elif terms[0] == "height":
            print(len(self.node.chain.blocks))
        elif terms[0] == "debug":
            self.node.debug = not self.node.debug
            print("Debug set to {}".format(self.node.debug))
        elif terms[0] == "prev":
            if self.prevCmd:
                print(">> " + self.prevCmd)
                self.runCommand(self.prevCmd)
            else:
                print("No previous command.")
        elif terms[0] == "eval":
            try:
                print(eval(input("In: ")))
            except Exception as e:
                print(e)
        else:
            print("Unknown command!")

        if terms[0] != "prev":
            self.prevCmd = command
    
    def saveQuit(self): 
        self.node.listener.close()
        self.node.stopMining()
        self.node.saveToFile(SAVE_FILE)
        print("Saved to {}".format(SAVE_FILE))
        self.running = False

if __name__ == "__main__":
    wallet = Wallet()
    wallet.run()
