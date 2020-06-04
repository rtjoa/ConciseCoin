import rsa

# Public key used as node addresses
class PubKey:
    def __init__(self, n, e):
        self.n = n
        self.e = e

    # Construct from a dict
    @staticmethod
    def wrap(rsaPubKey):
        return PubKey(rsaPubKey['n'], rsaPubKey['e'])

    def use(self):
        return rsa.key.PublicKey(self.n, self.e)

    def equals(self, other):
        return self.__dict__ == other.__dict__

# Private key used to sign
class PrivKey:
    def __init__(self, n, e, d, p, q):
        self.n = n
        self.e = e
        self.d = d
        self.p = p
        self.q = q

    @staticmethod
    def generate():
        return PrivKey.wrap(rsa.newkeys(512)[1])

    # Construct from a dict
    @staticmethod
    def wrap(rsaPrivKey):
        return PrivKey(rsaPrivKey['n'], rsaPrivKey['e'], rsaPrivKey['d'], rsaPrivKey['p'], rsaPrivKey['q'])

    def use(self):
        return rsa.key.PrivateKey(self.n, self.e, self.d, self.p, self.q)

    def equals(self, other):
        return self.__dict__ == other.__dict__


# Throws exception if invalid
def verify(message, signature, pubKey):
    rsa.verify(message, signature, pubKey.use())

# Uses privKey to create and return a signature for message
def sign(message, privKey):
    return rsa.sign(message, privKey.use(), 'SHA-256')
