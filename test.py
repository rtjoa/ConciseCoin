import rsa
from blockchain import *
from transaction import *
import hashlib
import random
import time
import math
import json


blockchain = Blockchain()
genesisHash = blockchain.blocks[0].hash()

alicePub, alicePriv = rsa.newkeys(512)
bobPub, bobPriv = rsa.newkeys(512)
charliePub, charliePriv = rsa.newkeys(512)
alicePub = PubKeyWrapper(alicePub)
bobPub = PubKeyWrapper(bobPub)
charliePub = PubKeyWrapper(charliePub)

'''
for _ in range(0,30):
  startTime = time.time()
  coinBaseToAliceBlock = mine(blockchain, [], alicePub)
  print("Mined block in {} sec".format(time.time() - startTime))
  blockchain.addBlock(coinBaseToAliceBlock)
'''

print(0)
coinBaseToAliceBlock = Block(blockchain.blocks[0].hash(), alicePub, [], 0, 0)
blockchain.addBlock(coinBaseToAliceBlock)
aliceCoinbaseTxIn = TxIn(coinBaseToAliceBlock.txs[0].hash(), 0)
#aliceToBobBlock = mine(blockchain, [tx], alicePub)

# choose which error you want to test, or 'no error' for a valid block
FORCED_ERROR = 'no error'

tx = Transaction([aliceCoinbaseTxIn],[TxOut(bobPub,10),TxOut(alicePub,15)])

if FORCED_ERROR == 'output not in pool':
  fakeTxIn = TxIn('not a valid hash output', 10)
  tx = Transaction([fakeTxIn],[])

elif FORCED_ERROR == 'double spend':
  tx = Transaction([aliceCoinbaseTxIn, aliceCoinbaseTxIn],[TxOut(bobPub,10),TxOut(alicePub,15)])

elif FORCED_ERROR == 'negative output':
  tx = Transaction([aliceCoinbaseTxIn],[TxOut(bobPub,-1),TxOut(alicePub,25)])
  
elif FORCED_ERROR == 'outputs greater':
  tx = Transaction([aliceCoinbaseTxIn],[TxOut(bobPub,11),TxOut(alicePub,15)])

if FORCED_ERROR == 'invalid sig':
  tx.sign(charliePriv, 0)
  
elif FORCED_ERROR != 'unsigned':
  tx.sign(alicePriv, 0)

aliceToBobBlock = Block(coinBaseToAliceBlock.hash(), alicePub, [tx], 0, 0)
blockchain.addBlock(aliceToBobBlock)


#print("BEFORE TRANSLATION")
#jsonStr = blockchain.toJSON()
#print(jsonStr)
#duplicate = blockchain.fromJSON(jsonStr)
#print("AFTER TRANSLATION")
#json2 = duplicate.toJSON()
#print(json2)

print("BEFORE TRANSLATION")
jsonTx = tx.toJSON()
print(jsonTx)
duplicate = Transaction.fromJSON(jsonTx)
print("AFTER TRANSLATION")
json2 = duplicate.toJSON()
print(json2)