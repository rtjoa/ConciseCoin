import json
import rsa
import hashlib
from transaction import *
from utxopool import UTXOPool

class Blockchain:
  def __init__(self):
    self.blocks = [Block(None, None, [], 0, 0)]
    self.pool = UTXOPool()
    self.pendingTxs = []
  
  @staticmethod
  def fromJSON():
    return Blockchain()
  
  def toJSON(self):
    return ""
  
  def addBlock(self, block):
    if not self.pool.verifyTxs(block.txs):
      print("INVALID TRANSACTIONS!!!")
      return False
    # check block hash < difficulty too!!
    self.pool.handleTxs(block.txs)
    self.blocks.append(block)
    return True

def mine(blockchain, pendingTxs, coinbaseRecipient):
  difficulty = 5 #hard-coded, subject to change
  attempts = 0
  while True:
    nonce = random.randomint(0,10**10)
    attemptBlock = Block( blocks[-1].hash(), coinbaseRecipient, txs, nonce, difficulty )
    if attemptBlock.hash().startswith('0' * difficulty):
      return attemptBlock
    attempts += 1

COINBASE = 25

class Block:
  def __init__(self, prevHash, coinbaseRecipient, txs, nonce, difficulty):
    self.prevHash = prevHash
    self.txs = txs
    self.nonce = nonce
    self.difficulty = difficulty
    coinbase = Transaction([], [TxOut(coinbaseRecipient, COINBASE)])
    self.txs.insert(0, coinbase)
  
  def hash(self):
    hasher = hashlib.sha256()
    hasher.update((str(self.prevHash)+str(self.txs)+str(self.nonce)+str(self.difficulty)).encode('utf-8'))
    return hasher.hexdigest()
  
  @staticmethod
  def fromJSON():
    return Block(None, None, None, None, None)
  
  def toJSON(self):
    return ""
    
'''
-- Block Class --

Class constant

Instance vars:
  prevHash
  txs
  nonce
  difficulty

__init__(prevHash, coinbaseRecipient, txs, nonce, difficulty)
  self.txs = txs
  self.txs.append(coinBaseTractions)

Instance methods:
  hash
'''