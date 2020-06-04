import socket
from threading import Thread
import json
from transaction import Transaction, TxIn, TxOut
from blockchain import Blockchain
from block import Block
import random
from cryptography import PrivKey, PubKey

MAGIC_PORT = 51412
HARDCODED_PEERS = []

# Manage a member of the blockchain
class Node:
    def __init__(self, privKey=None, peers=[], chain=None):
        self.privKey = privKey or PrivKey.generate()  # generate new keys if not supplied
        # a PrivKey contains info of a PubKey
        self.pubKey = PubKey.wrap(self.privKey.__dict__)
        self.chain = chain or Blockchain()
        self.peers = peers
        self.peerSocks = {}
        self.pendingTxs = []
        for peer in HARDCODED_PEERS:
            if not peer in self.peers:
                self.peers.append(peer)
        self.listener = None
        self.mining = False
        self.debug = False

    # Factory method to load node from json file
    @staticmethod
    def loadFromFile(path):
        f = open(path, 'r')
        obj = json.loads(f.read())
        f.close()
        peers = obj['peers']
        privKey = PrivKey.wrap(obj['privKey'])
        if obj['chain'] != 'null' and obj['chain']:
            chain = Blockchain.fromJSON(obj['chain'])
        else:
            chain = None
        return Node(privKey, peers, chain)

    # Write json representation to a file
    def saveToFile(self, path):
        obj = {
            "chain": self.chain.toJSON(),
            "peers": self.peers,
            "privKey": self.privKey  # todo: don't store this as plaintext
        }
        f = open(path, 'w')
        f.write(json.dumps(obj, default=lambda o: o.__dict__))
        f.close()

    def give(self, address, amt):
        if amt > self.balance():
            print("Insufficient balance")
            return

        myOuts = [
            txOut for txOut in self.chain.pool.txOuts if txOut.address.equals(self.pubKey)]

        toGive = amt
        consumed = []

        created = [TxOut(address, amt)]

        for out in myOuts:
            consumed.append(TxIn(out.txHash, out.idx))
            if out.value >= toGive:
                created.append(TxOut(self.pubKey, out.value - toGive))
            toGive -= out.value
            if toGive <= 0:
                break

        tx = Transaction(consumed, created)
        for i in range(len(consumed)):
            tx.sign(self.privKey, i)

        self.pendingTxs.append(tx)

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
                nonce = random.randint(0, 10**10)
                attempts += 1
                childDiff = self.chain.nextDifficulty()
                attemptBlock = Block(
                    self.chain.blocks[-1].hash(), self.pubKey, self.pendingTxs, nonce, childDiff)

                if attemptBlock.satisfiedDifficulty() >= childDiff:
                    print("Mined block in {} attempts".format(attempts))
                    self.chain.addBlock(attemptBlock)
                    self.shareChain()
                    self.mining = False
        t = Thread(target=m)
        t.daemon = True
        t.start()

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
            if len(candidate.blocks) > len(self.chain.blocks) and Blockchain.validate(candidate):
                self.chain = candidate
        elif request['type'] == "TRANSACTION":
            candidate = Transaction.fromJSON(request['data'])
            try:
                self.chain.pool.verifyTx(candidate)
            except Exception as e:
                print("Invalid transaction!")
                if self.debug:
                    raise e
            for tx in self.pendingTxs:
                if candidate.equals(tx):
                    if self.debug:
                        print("Duplicate transaction proposed!")
                    return
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
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(('', MAGIC_PORT))
        t = Thread(target=self.listen)
        t.daemon = True
        t.start()

        # Connect to peers
        for peer in self.peers:
            self.connectToPeer(peer)

        # Request chain from peers
        if not self.chain:
            self.requestChain()

    # Listen on the magic port
    def listen(self):
        while not self.listener._closed:
            try:
                # Listen for a new connection
                self.listener.listen(1)
                (clientname, address) = self.listener.accept()

                # Upon connection, create a thread to receive data
                t = Thread(target=self.receiveContinually,
                       args=[clientname, address])
                t.daemon = True
                t.start()
                print(
                    "Received connection from {}, attempting connect back.".format(address))

                # Adds connection to list of known peers
                self.addPeer(address[0])
            except OSError as e:
                if e.winerror == 10038:
                    # Expected error upon socket close in another thread
                    # Unavoidable w/o a janky hack
                    pass
                else:
                    raise e
    
    # Receive all messages from a connected peer
    def receiveContinually(self, clientname, address):
        while 1:
            try:
                # Every message should include an <END>, so loop until it is received
                chunk = b''
                while not b'<END>' in chunk:
                    chunk += clientname.recv(4096)
                chunk = chunk.replace(b'<END>', b'')
                if len(chunk):
                    if self.debug:
                        print("Received:")
                        print(chunk)
                    if chunk != b'':
                        self.handleRequest(json.loads(chunk), address[0])
            except ConnectionResetError as e:
                if e.errno == 54:
                    break
                else:
                    raise e

    def sendToPeers(self, request, recipient='all'):
        data = (json.dumps(request) + "<END>").encode("utf-8")
        for peer in self.peerSocks:
            if recipient == 'all' or recipient == peer:
                self.peerSocks[peer].send(data)
                if self.debug:
                    print("Sent to {}:".format(peer))
                    print(data)

    def addPeer(self, peer):
        if not peer in self.peers:
            self.peers.append(peer)
        if peer in self.peerSocks:
            try:
                self.peerSocks[peer].send('<END>'.encode('utf-8'))
                return
            except:
                pass
        self.connectToPeer(peer)

    def connectToPeer(self, peer):
        def m(peer):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect((peer, MAGIC_PORT))
                self.peerSocks[peer] = sock
            except TimeoutError:
                pass
            except ConnectionRefusedError as e:
                if e.errno == 10061:
                    pass

        t = Thread(target=m, args=[peer])
        t.daemon = True
        t.start()
