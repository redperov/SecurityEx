import binascii
import hashlib
import os

from src.myEncryption.kdf import perform_kdf


class DiffieHellman:
    def __init__(self):
        # TODO move to config file
        self.prime = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF
        self.generator = 2

        # Generate a private key using the kernel's random number generator
        self._private_key = int(binascii.hexlify(os.urandom(32)), base=16)

        # TODO should it generate the public key? or is it done elsewhere
        # Generates the public key according to: generator^thisPrivateKey mod prime
        self._public_key = pow(self.generator, self._private_key, self.prime)

    def get_private_key(self):
        return self._private_key

    def get_public_key(self):
        return self._public_key

    def generate_shared_key(self, other_public_key):
        # Generate the shared key according to: generator^(thisPrivateKey*otherPrivateKey) mod prime
        shared_key = pow(other_public_key, self._private_key, self.prime)
        print(str.format("Received shared key before kdf: {0}", shared_key))
        shared_key_bytes = str(shared_key).encode()
        print(str.format("Received shared key after kdf: {0}", perform_kdf(shared_key_bytes)))
        # TODO why is the shared key hashed?
        # return hashlib.sha256(str(self.shared_key)).hexdigest()

        # TODO make sure it returns bytes
        return perform_kdf(shared_key_bytes)
