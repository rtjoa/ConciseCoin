import socket
from threading import Thread
import json
from blockchain import *
import random

MAGIC_PORT = 51412
HARDCODED_PEERS = ['25.100.101.237']

class Node:
    def __init__(self, privKey = None, peers = [], chain = None):
        self.privKey = privKey or PrivKeyWrapper(rsa.newkeys(512)[1])
        self.pubKey = PubKeyWrapper(self.privKey.__dict__)
        self.chain = chain
        self.peers = peers
        self.peersSendSocks = []
        self.peersSendHosts = []
        self.pendingTxs = []
        for peer in HARDCODED_PEERS:
            if not peer in self.peers:
                self.peers.append(peer)
        self.listener = None
        self.mining = False
    
    @staticmethod
    def loadFromFile(path):
        f  = open(path, 'r')
        obj = json.loads(f.read())
        f.close()
        peers = obj['peers']
        privKey = PrivKeyWrapper(obj['privKey'])
        chain = Blockchain.fromJSON(obj['chain'])
        return Node(privKey, peers, chain)
    
    def saveToFile(self, path):
        obj = {
            "chain": self.chain.toJSON() if self.chain else None,
            "peers": self.peers,
            "privKey": self.privKey # todo: don't store this as plaintext
        }
        f = open(path, 'w')
        f.write(json.dumps(obj, default=lambda o:o.__dict__))
        f.close()
    
    def connect(self):
        self.exposeToNewPeers()
        for peer in self.peers:
            self.connectToPeer(peer)

    def mine(self):
        if not self.chain:
            print("No chain to mine on!")
            return
        if self.mining:
            print("Already mining!")
            return
        self.mining = True
        def m():
            attempts = 0
            while self.mining:
                difficulty = self.chain.blocks[-1].difficulty
                nonce = random.randint(0,10**10)
                attempts += 1
                childDiff = self.chain.nextDifficulty()
                attemptBlock = Block(self.chain.blocks[-1].hash(), self.pubKey, self.pendingTxs, nonce, childDiff)
                asBin = bin(int(attemptBlock.hash(),16))
                if len(asBin) <= 258 - difficulty:
                    print("Took {} attempts".format(attempts))
                    self.chain.addBlock(attemptBlock)
                    self.shareChain()
        Thread(target = m).start()
        
    def stopMining(self):
        self.mining = False
    
    def shareChain(self):
        chain = self.chain.toJSON()
        self.sendToPeers({
            "type": "CHAIN",
            "data": chain
        })
        
    def requestChain(self):
        self.sendToPeers({
            "type": "REQUEST_CHAIN"
        })
        
    def sendMsg(self, msg):
        self.sendToPeers({
            "type": "MESSAGE",
            "data": msg
        })
    
    def receiveContinually(self, clientname, address):
        while 1:
            chunk=clientname.recv(4096)
            if len(chunk):
                print(repr(chunk))
                self.handleRequest(json.loads(chunk))
    
    def handleRequest(self, request):
        return
                        
    def exposeToNewPeers(self):
        self.listener = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(('',MAGIC_PORT))
        
        def listen():
            while not self.listener._closed:
                try:
                    self.listener.listen(1)
                    # print("Listening on port {}.".format(self.listener.getsockname()[1]))
                    (clientname,address)=self.listener.accept()
                    Thread(target=self.receiveContinually, args=[clientname, address]).start()
                    print("Received connection from {}, attempting connect back.".format(address))
                    self.addPeer(address[0])
                except OSError as e:
                    if e.winerror == 10038:
                        # Expected error upon socket close in another thread
                        # Unavoidable w/o a janky hack
                        pass
                    else:
                        raise e
        
        Thread(target = listen).start()
    
    def sendToPeers(self, request):
        for sock in self.peersSendSocks:
            sock.send(json.dumps(request).encode("utf-8"))
    
    def addPeer(self, host):
        if not host in self.peers:
            self.peers.append(host)
        self.connectToPeer(host)
        
    def connectToPeer(self, host):
        def t(host):
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            if host in self.peersSendHosts:
                return
            sock.connect((host, MAGIC_PORT))
            # print("Connected")
            self.peersSendSocks.append(sock)
            self.peersSendHosts.append(host)
        Thread(target=t, args=[host]).start()