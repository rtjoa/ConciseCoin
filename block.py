from transaction import Transaction, TxOut
import time
import blockchain
import hashlib


class Block:
    def __init__(self, prevHash, coinbaseRecipient, txs, nonce, difficulty):
        self.prevHash = prevHash
        self.txs = [tx.clone() for tx in txs]
        self.nonce = nonce
        self.timestamp = time.time()
        self.difficulty = difficulty
        coinbase = Transaction(
            [], [TxOut(coinbaseRecipient, blockchain.COINBASE_AMT)])
        self.txs.insert(0, coinbase)

    def hash(self):
        hasher = hashlib.sha256()
        hasher.update((str(self.prevHash)+str([tx.represent() for tx in self.txs])+str(
            self.nonce)+str(self.difficulty)+str(self.timestamp)).encode('utf-8'))
        return hasher.hexdigest()

    def satisfiedDifficulty(self):
        asBin = bin(int(self.hash(), 16))
        return 258 - len(asBin)

    @staticmethod
    def fromJSON():
        return Block(None, None, None, None, None)

    def toJSON(self):
        return ""
