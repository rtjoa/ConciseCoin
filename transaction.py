import hashlib
import rsa

class Transaction:
  def __init__(self, txIns, txOuts):
    self.txIns = txIns
    self.txOuts = txOuts

  def sign(self, privKey, inputIndex):
    data = self.txIns[inputIndex]
    self.txIns[inputIndex].signature = rsa.sign(data, privKey, 'SHA-256')

  def hash(self):
    hasher = hashlib.sha256()
    insHashData = str([txIn.getDataToHash() for txIn in self.txIns])
    outsHashData = str([txOut.getDataToHash() for txOut in self.txOuts])
    hasher.update((insHashData + outsHashData).encode('utf-8'))
    return hasher.hexdigest()

class TxIn:
  def __init__(self, prevTxHash, prevTxOutIndex):
    self.prevTxHash = prevTxHash
    self.prevTxOutIndex = prevTxOutIndex
    self.signature = None
  
  def getDataToHash(self):
    return str(self.prevTxHash) + str(self.prevTxOutIndex) + str(self.signature)

class TxOut:
  def __init__(self, address, value):
    self.address = address
    self.value = value
    self.txHash = None
    self.idx = None
  
  def getDataToHash(self):
    return str(self.address) + str(self.value)

'''
-- Transaction --
__init__(txIns, txOuts)

sign(privKey, inputIndex)
hash()

'''