import socket
from threading import Thread
import json
from blockchain import *
import random

MAGIC_PORT = 51412
HARDCODED_PEERS = ['25.100.101.237']

class Node:
    def __init__(self, privKey = None, peers = [], chain = None):
        self.privKey = privKey or PrivKeyWrapper(rsa.newkeys(512)[1]) # generate new keys if not supplied
        self.pubKey = PubKeyWrapper(self.privKey.__dict__) # a PrivKey contains info of a PubKey
        self.chain = chain
        self.peers = peers
        self.peerSocks = {}
        self.pendingTxs = []
        for peer in HARDCODED_PEERS:
            if not peer in self.peers:
                self.peers.append(peer)
        self.listener = None
        self.mining = False
    
    # Factory method to load node from json file
    @staticmethod
    def loadFromFile(path):
        f  = open(path, 'r')
        obj = json.loads(f.read())
        f.close()
        peers = obj['peers']
        privKey = PrivKeyWrapper(obj['privKey'])
        if obj['chain'] != 'null' and obj['chain']:
            chain = Blockchain.fromJSON(obj['chain'])
        else:
            chain = None
        return Node(privKey, peers, chain)
    
    # Write json representation to a file
    def saveToFile(self, path):
        obj = {
            "chain": self.chain.toJSON() if self.chain else None,
            "peers": self.peers,
            "privKey": self.privKey # todo: don't store this as plaintext
        }
        f = open(path, 'w')
        f.write(json.dumps(obj, default=lambda o:o.__dict__))
        f.close()
        
    def give(self, address, amt):
        if amt > self.balance():
            print("Insufficient balance")
            return
        
        myOuts = [txOut for txOut in self.chain.pool.txOuts if txOut.address.equals(self.pubKey)]
        
        toGive = amt
        consumed = []
        
        created = [TxOut(address, amt)]
        
        for out in myOuts:
            consumed.append(TxIn(out.txHash, out.idx))
            if out.value >= toGive:
                created.append( TxOut(self.pubKey, out.value - toGive) )
            toGive -= out.value

        tx = Transaction(consumed, created)
        tx.sign(self.privKey.use(), 0)
        tx.sign(self.privKey.use(), 1)
        
        self.sendToPeers({
            "type": 'TRANSACTION',
            "data": tx.toJSON()
        })
    
    # Mine until stopMining() called
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
                nonce = random.randint(0,10**10)
                attempts += 1
                childDiff = self.chain.nextDifficulty()
                attemptBlock = Block(self.chain.blocks[-1].hash(), self.pubKey, self.pendingTxs, nonce, childDiff)
                
                if attemptBlock.satisfiedDifficulty() >= childDiff:
                    print("Took {} attempts".format(attempts))
                    self.chain.addBlock(attemptBlock)
                    self.shareChain()
        Thread(target = m).start()
        
    def stopMining(self):
        self.mining = False
    
    # Shares chain with all peers BUT IT SHOULD ONLY SHARE WITH ONE INSTEAD
    def shareChain(self, recipient='all'):
        chain = self.chain.toJSON()
        self.sendToPeers({
            "type": "CHAIN",
            "data": chain
        }, recipient)
    
    def ping(self, recipient='all'):
        self.sendToPeers({
            "type": "PING"
        }, recipient)
    
    def requestChain(self):
        self.sendToPeers({
            "type": "REQUEST_CHAIN"
        })
        
    def sendMsg(self, msg):
        self.sendToPeers({
            "type": "MESSAGE",
            "data": msg
        })
    
    def balance(self):
        return sum(txOut.value for txOut in self.chain.pool.txOuts if txOut.address.equals(self.pubKey))
        
    def handleRequest(self, request, source):
        if request['type'] == "REQUEST_CHAIN":
            self.shareChain(source)
        elif request['type'] == "CHAIN":
            candidate = Blockchain.fromJSON(request['data'])
            if len(candidate.blocks) > len(self.chain.blocks): # todo: and candidate is valid
                self.chain = candidate
        elif request['type'] == "TRANSACTION":
            candidate = Transaction.fromJSON(request['data'])
            if not verifyTx(candidate):
                print("Invalid transaction!")
            for tx in range(self.pendingTxs):
                if candidate.equals(tx):
                    print("Duplicate transaction proposed!")
                break
            self.pendingTxs.append(candidate)
            self.sendToPeers(request)
        elif request['type'] == "PING":
            print("Ping from {}".format(source))
        else:
            print("Unknown request type!")
        return

    # Run once after intialization to connect node to network
    def connect(self):
        # Expose magic port to new connections
        self.listener = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(('',MAGIC_PORT))
        Thread(target = self.listen).start()
        
        # Connect to peers
        for peer in self.peers:
            self.connectToPeer(peer)
            
    # Listen on the magic port
    def listen(self):
        while not self.listener._closed:
            try:
                # Listen for a new connection
                self.listener.listen(1)
                (clientname,address)=self.listener.accept() 
                
                # Upon connection, create a thread to receive data
                Thread(target=self.receiveContinually, args=[clientname, address]).start()
                print("Received connection from {}, attempting connect back.".format(address))
                
                # Adds connection to list of known peers
                self.addPeer(address[0])
            except OSError as e:
                if e.winerror == 10038:
                    # Expected error upon socket close in another thread
                    # Unavoidable w/o a janky hack
                    pass
                else:
                    raise e
                    
    def receiveContinually(self, clientname, address):
        while 1:
            try:
                chunk=clientname.recv(2**30)
            except ConnectionResetError as e:
                if e.errno==54:
                    break
                else:
                    raise e
            if len(chunk):
                if chunk != b'null':
                    self.handleRequest(json.loads(chunk), address[0])
                    
    def sendToPeers(self, request, recipient='all'):
        data = json.dumps(request).encode("utf-8")
        for peer in self.peerSocks:
            if recipient == 'all' or recipient == peer:
                self.peerSocks[peer].send(data)
    
    def addPeer(self, peer):
        if not peer in self.peers:
            self.peers.append(peer)
        if peer in self.peerSocks:
            try:
                self.peerSocks[peer].send('null'.encode('utf-8'))
                return
            except:
                pass
        self.connectToPeer(peer)
        
    def connectToPeer(self, peer):
        def t(peer):
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            #print("Duplicate peer!")
            try:
                sock.connect((peer, MAGIC_PORT))
                self.peerSocks[peer] = sock
            except TimeoutError as e:
                pass
                # print(peer)
                # raise e
                # print(e.__dict__)
            except ConnectionRefusedError as e:
                if e.errno == 10061:
                    pass
                
        Thread(target=t, args=[peer]).start()