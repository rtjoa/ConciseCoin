import hashlib
import time
import json
from cryptography import PubKey, sign


class Transaction:
    def __init__(self, txIns, txOuts):
        self.txIns = txIns
        self.txOuts = txOuts
        self.timestamp = time.time()

    def clone(self):
        txIns = [txIn.clone() for txIn in self.txIns]
        txOuts = [txOut.clone() for txOut in self.txOuts]
        dupe = Transaction(txIns, txOuts)
        dupe.timestamp = self.timestamp
        return dupe

    def equals(self, other):
        return self.toJSON() == other.toJSON()

    @staticmethod
    def fromJSON(j):
        jsonTx = json.loads(j)
        txIns = []
        txOuts = []

        for txIn in jsonTx['txIns']:
            newTxIn = TxIn(txIn['prevTxHash'], txIn['prevTxOutIndex'])
            newTxIn.signature = eval(txIn['signature']) # todo: eval creates security vulnerability
            txIns.append(newTxIn)
        for txOut in jsonTx['txOuts']:
            if txOut['address'] == None:
                newPubKey = None
            else:
                newPubKey = PubKey.wrap(txOut['address'])
            newTxOut = TxOut(newPubKey, txOut['value'])
            newTxOut.txHash = txOut['txHash']
            newTxOut.idx = txOut['idx']
            txOuts.append(newTxOut)

        tx = Transaction(txIns, txOuts)
        tx.timestamp = jsonTx['timestamp']
        return tx

    def toJSON(self):
        def customEncoder(o):
            if isinstance(o, bytes):
                return repr(o)
            return o.__dict__
        return json.dumps(self, default=customEncoder, indent=2)

    # Representation to be hashed
    def represent(self):
        ins = ";".join([txIn.representSigned() for txIn in self.txIns])
        outs = ";".join([txOut.represent() for txOut in self.txOuts])
        return str(self.timestamp) + ins + outs

    def sign(self, privKey, inputIndex):
        # will need to make this signature variable a string
        self.txIns[inputIndex].signature = sign(
            self.getDataToSign(inputIndex), privKey)

    def hash(self):
        hasher = hashlib.sha256()
        hasher.update(self.represent().encode('utf-8'))
        return hasher.hexdigest()

    def getDataToSign(self, inputIndex):
        return (self.txIns[inputIndex].representUnsigned() + str([txOut.represent() for txOut in self.txOuts])).encode('utf-8')


class TxIn:
    def __init__(self, prevTxHash, prevTxOutIndex):
        self.prevTxHash = prevTxHash
        self.prevTxOutIndex = prevTxOutIndex
        self.signature = None

    def clone(self):
        dupe = TxIn(self.prevTxHash, self.prevTxOutIndex)
        dupe.signature = self.signature
        return dupe

    def representSigned(self):
        return str(self.prevTxHash) + str(self.prevTxOutIndex) + str(self.signature)

    def representUnsigned(self):
        return str(self.prevTxHash) + str(self.prevTxOutIndex)


class TxOut:
    def __init__(self, address, value):
        self.address = address
        self.value = value
        self.txHash = None
        self.idx = None

    def clone(self):
        dupe = TxOut(self.address, self.value)
        dupe.txHash = self.txHash
        dupe.idx = self.idx
        return dupe

    def represent(self):
        if not self.address:
            return str(self.value)
        return str(self.address.__dict__) + str(self.value)
