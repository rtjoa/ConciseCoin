#! /usr/bin/env python
import rsa
from blockchain import Blockchain, Block
from transaction import Transaction, TxIn, TxOut

blockchain = Blockchain()
genesisHash = blockchain.blocks[0].hash()

alicePub, alicePriv = rsa.newkeys(512)
bobPub, bobPriv = rsa.newkeys(512)


coinBaseToAliceBlock = Block(genesisHash, alicePub, [], 0, 0)
blockchain.addBlock(coinBaseToAliceBlock)

coinBaseToAliceTx = coinBaseToAliceBlock.txs[0]
aliceCoinbaseTxIn = TxIn(coinBaseToAliceTx.hash(), 0)

aliceToBobTx = Transaction([aliceCoinbaseTxIn],[TxOut(bobPub,10),TxOut(alicePub,15)])
aliceToBobBlock = Block(genesisHash, alicePub, [aliceToBobTx], 0, 0)
blockchain.addBlock(aliceToBobBlock)