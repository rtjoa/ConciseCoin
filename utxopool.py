from transaction import TxOut
import rsa

COINBASE_AMT = 25

class UTXOPool:
  def __init__(self):
    self.txOuts = []

  def clone(self):
    newPool = UTXOPool()
    for txOut in self.txOuts:
      newTxOut = TxOut(txOut.address, txOut.value)
      newTxOut.txHash = txOut.txHash
      newTxOut.idx = txOut.idx
      newPool.txOuts.append(newTxOut)
    return newPool

  def handleTxs(self, txList): # throws ValueError
    for tx in txList:
      self.verifyTx(tx)
      self.acceptTx(tx)
  
  def acceptTx(self, tx):
    # Remove consumed txOuts
    for txIn in tx.txIns:
      for i, txOut in enumerate(self.txOuts):
        if txIn.prevTxHash == txOut.txHash and txIn.prevTxOutIndex == txOut.idx:
          self.txOuts[i] = None
    self.txOuts = [txOut for txOut in self.txOuts if not txOut == None]

    # Add created txOuts
    for idx, txOut in enumerate(tx.txOuts):
      txOut.txHash = tx.hash()
      txOut.idx = idx
      self.txOuts.append(txOut)

  def handleCoinbase(self, coinbaseTx):
    if len(coinbaseTx.txIns):
      raise Exception("Coinbase tx cannot consume any coins.")
    if sum([txOut.value for txOut in coinbaseTx.txOuts]) > COINBASE_AMT:
      raise ("Coinbase tx can only create {} coins".format(COINBASE_AMT))
    self.acceptTx(coinbaseTx)

  def verifyTx(self, tx):
    prevTxOuts = [None] * len(tx.txIns)
    for idx, txIn in enumerate(tx.txIns):
      for txOut in self.txOuts:
        if txIn.prevTxHash == txOut.txHash and txIn.prevTxOutIndex == txOut.idx:
          prevTxOuts[idx] = txOut

    # all outputs claimed AS INPUTS by tx are in the current UTXO pool
    for txOut in prevTxOuts:
      if txOut == None:
        raise ValueError("Output not in pool!")
        
    # the signatures on txIn are valid
    for idx, (txIn, prevTxOut) in enumerate(zip(tx.txIns, prevTxOuts)):
      if txIn.signature == None:
        raise ValueError("Input is unsigned!")
      try:
        signature = txIn.signature

        if not rsa.verify(tx.getDataToSign(idx), signature, prevTxOut.address.use()):
          print("This code should never be reached because rsa.verify returns a VerificationError when it fails!")
          raise ValueError
      except:
        raise ValueError("Invalid signature!")

    # no UTXO is claimed multiple times, i.e. double spend
    uniqueTxIns = len(set([txIn.representUnsigned() for txIn in tx.txIns]))
    if uniqueTxIns != len(tx.txIns):
      raise ValueError("Double spending!")

    # all output values are not negative
    for txOut in tx.txOuts:
      if txOut.value < 0:
        raise ValueError("Negative output value found!")

    # sum of input values is greater than or equal to output values
    created = sum(txOut.value for txOut in tx.txOuts)
    consumed = sum(prevTxOut.value for prevTxOut in prevTxOuts)
    if created > consumed:
      raise ValueError("Sum of outputs is greater than previous outputs!")