import json
import rsa
import hashlib
import time
import math
from transaction import *
from utxopool import UTXOPool

COINBASE_AMT = 25
DEFAULT_DIFFICULTY = 10
DIFFICULTY_RECALC_INTERVAL = 10
TARGET_MINE_TIME = 20

class Blockchain:
  def __init__(self):
    self.blocks = [Block(None, None, [], 0, DEFAULT_DIFFICULTY)]
    self.pool = UTXOPool()
    
  @staticmethod
  def validate(blockchain):
    # first - check previous hashes
    for i in range(len(blockchain.blocks)-1):
      if blockchain.blocks[i].hash() != blockchain.blocks[i+1].prevHash:
        return False
    
    # second - reconstruct blockchain with txs and coinbase recipients
    dummyChain = Blockchain()
    dummyChain.blocks[0].timestamp = blockchain.blocks[0].timestamp
    for block in blockchain.blocks[1:]:
      newBlock = Block(dummyChain.blocks[-1].hash(), [tx.clone() for tx in block.txs][0].txOuts[0].address, [tx.clone() for tx in block.txs], block.nonce, block.difficulty)
      newBlock.txs.pop(0)
      newBlock.timestamp = block.timestamp
      
      try:
        dummyChain.addBlockException(newBlock)
      except Exception as e:
        print(e)
        return False
    
    for i in range(len(blockchain.blocks)-1):
      difficulty = blockchain.nextDifficulty(i)
      if blockchain.blocks[i+1].satisfiedDifficulty() < difficulty:
          print("Difficulty not satisfied")
          return False
    
    return True

  def addBlockException(self, block):
    dummyPool = self.pool.clone()
    dummyPool.handleCoinbase(block.txs[0])
    # check block hash < difficulty too!!
    dummyPool.handleTxs(block.txs[1:])
    self.pool = dummyPool
    self.blocks.append(block)

  @staticmethod
  def fromJSON(j):
    blockchain = Blockchain()
    jsonChain = json.loads(j)

    # copy over blocks
    newBlocks = []
    for block in jsonChain['blocks']:
      newBlockTxs = []

      for tx in block['txs']:
        newBlockTxIns = []
        newBlockTxOuts = []

        for txIn in tx['txIns']:
          newBlockTxIn = TxIn(txIn['prevTxHash'], txIn['prevTxOutIndex'])
          newBlockTxIn.signature = eval(txIn['signature'])
          newBlockTxIns.append(newBlockTxIn)
        for txOut in tx['txOuts']:
          if txOut['address'] == None:
            newPubKey = None
          else:
            newPubKey = PubKeyWrapper(rsa.key.PublicKey(txOut['address']['n'], txOut['address']['e']))
          newBlockTxOut = TxOut(newPubKey, txOut['value'])
          newBlockTxOut.txHash = txOut['txHash']
          newBlockTxOut.idx = txOut['idx']
          newBlockTxOuts.append(newBlockTxOut)

        newBlockTx = Transaction(newBlockTxIns, newBlockTxOuts)
        newBlockTx.timestamp = tx['timestamp']
        newBlockTxs.append(newBlockTx)
      
      coinbaseRecipientDict = block['txs'][0]['txOuts'][0]['address']
      if coinbaseRecipientDict == None:
        coinbaseRecipient = None
      else:
        coinbaseRecipient = PubKeyWrapper(rsa.key.PublicKey(coinbaseRecipientDict['n'], coinbaseRecipientDict['e']))
        
      prevHash = newBlocks[-1].hash() if len(newBlocks) else None
      newBlock = Block(prevHash, coinbaseRecipient, newBlockTxs, block['nonce'], block['difficulty'])

      # remove duplicate coinbase transaction
      newBlock.txs.pop(0)
      newBlock.timestamp = block['timestamp']
      newBlocks.append(newBlock)
    blockchain.blocks = newBlocks

    # copy over pool
    newPoolTxOuts = []
    for txOut in jsonChain['pool']['txOuts']:
      if txOut['address'] == None:
        newPubKey = None
      else:
        newPubKey = PubKeyWrapper(rsa.key.PublicKey(txOut['address']['n'], txOut['address']['e']))
      newPoolTxOut = TxOut(newPubKey, txOut['value'])
      newPoolTxOut.txHash = txOut['txHash']
      newPoolTxOut.idx = txOut['idx']
      newPoolTxOuts.append(newPoolTxOut)
    blockchain.pool.txOuts = newPoolTxOuts

    # don't need to remove duplicate genesis block because everything was replaced
    return blockchain
  
  def toJSON(self):
    def customEncoder(o):
      if isinstance(o, bytes):
        return repr(o)
      return o.__dict__
    return json.dumps(self, default=customEncoder, indent=2)
  
  def addBlock(self, block):
    try:
      dummyPool = self.pool.clone()
      dummyPool.handleCoinbase(block.txs[0])
      # check block hash < difficulty too!!
      dummyPool.handleTxs(block.txs[1:])
      self.pool = dummyPool
      self.blocks.append(block)
    except Exception as e:
      print(e)
      
  def nextDifficulty(self, blockIndex = None):
      if blockIndex == None:
          blockIndex = len(self.blocks)-1
          
      dummyBlocks = self.blocks[:blockIndex+1]
      top = dummyBlocks[-1]
      if len(dummyBlocks) % DIFFICULTY_RECALC_INTERVAL:
          return top.difficulty
      i = max(-1 * DIFFICULTY_RECALC_INTERVAL, -len(dummyBlocks))
      mineTime = (top.timestamp - dummyBlocks[i].timestamp)/abs(i)
      intendedMineTimeMultiplier = TARGET_MINE_TIME/mineTime
      return round(top.difficulty + math.log(intendedMineTimeMultiplier, 2))

class Block:
  def __init__(self, prevHash, coinbaseRecipient, txs, nonce, difficulty):
    self.prevHash = prevHash
    self.txs = [tx.clone() for tx in txs]
    self.nonce = nonce
    self.timestamp = time.time()
    self.difficulty = difficulty
    coinbase = Transaction([], [TxOut(coinbaseRecipient, COINBASE_AMT)])
    self.txs.insert(0, coinbase)
  
  def hash(self):
    hasher = hashlib.sha256()
    hasher.update((str(self.prevHash)+str([tx.represent() for tx in self.txs])+str(self.nonce)+str(self.difficulty)+str(self.timestamp)).encode('utf-8'))
    return hasher.hexdigest()

  def satisfiedDifficulty(self):
     asBin = bin(int(self.hash(),16))
     return 258 - len(asBin)
  
  @staticmethod
  def fromJSON():
    return Block(None, None, None, None, None)
  
  def toJSON(self):
    return ""