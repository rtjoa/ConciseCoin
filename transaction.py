import hashlib
import rsa
import time
import json

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
    # if (isinstance(other, Transaction)):
    #   if (self.timestamp==other.timestamp and len(self.txIns)==len(other.txIns) and len(self.txOuts)==len(other.txOuts)):
    #     for i in range(len(self.txIns)):
    #       if (self.txIns[i].prevTxHash!=other.txIns[i].prevTxHash or self.txIns[i].prevTxOutIndex!=other.txIns[i].prevTxOutIndex
    #       or self.txIns[i].signature!=other.txIns[i].signature):
    #         return False
    #     for i in range(len(self.txOuts)):
    #       if (self.txOuts[i].address!=other.txOuts[i].address or self.txOuts[i].value!=other.txOuts[i].value
    #       or self.txOuts[i].txHash!=other.txOuts[i].txHash or self.txOuts[i].idx!=other.txOuts[i].idx):
    #         return False 
    #     return True
    # return False

  @staticmethod
  def fromJSON(j):
      jsonTx = json.loads(j)
      txIns = []
      txOuts = []
      
      for txIn in jsonTx['txIns']:
        newTxIn = TxIn(txIn['prevTxHash'], txIn['prevTxOutIndex'])
        newTxIn.signature = eval(txIn['signature'])
        txIns.append(newTxIn)
      for txOut in jsonTx['txOuts']:
        if txOut['address'] == None:
          newPubKey = None
        else:
          newPubKey = PubKeyWrapper(rsa.key.PublicKey(txOut['address']['n'], txOut['address']['e']))
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
        # TODO: Make less illegal
        return repr(o)
      return o.__dict__
     return json.dumps(self, default=customEncoder, indent=2)
  
  def represent(self):
      ins = ";".join([txIn.representSigned() for txIn in self.txIns])
      outs = ";".join([txOut.represent() for txOut in self.txOuts])
      return str(self.timestamp) + ins + outs

  def sign(self, privKey, inputIndex):
    # will need to make this signature variable a string
    self.txIns[inputIndex].signature = rsa.sign(self.getDataToSign(inputIndex), privKey, 'SHA-256')

  def hash(self):
    hasher = hashlib.sha256()
    insHashData = str([txIn.representSigned() for txIn in self.txIns])
    outsHashData = str([txOut.represent() for txOut in self.txOuts])
    hasher.update((insHashData + outsHashData).encode('utf-8') + str(self.timestamp).encode('utf-8'))
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

class PubKeyWrapper:
  def __init__(self, pubKey):
      self.n = pubKey['n']
      self.e = pubKey['e']
  def use(self):
      return rsa.key.PublicKey(self.n, self.e)
  def equals(self, other):
      return self.__dict__ == other.__dict__

class PrivKeyWrapper:
  def __init__(self, privKey):
      self.n = privKey['n']
      self.e = privKey['e']
      self.d = privKey['d']
      self.p = privKey['p']
      self.q = privKey['q']
  def use(self):
    return rsa.key.PrivateKey(self.n, self.e, self.d, self.p, self.q)