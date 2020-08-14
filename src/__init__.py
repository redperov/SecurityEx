import src.OtherDES as encryption
import src.myEncryption.DES as my_encryption
import time

# TODO remove that
from src.myEncryption.DiffieHellman import DiffieHellman


def original_des():
    data = b"Please encrypt my data"
    k = encryption.des(b"DESCRYPT", encryption.ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=encryption.PAD_NORMAL)
    d = k.encrypt(data)
    print("Encrypted: %r" % d)
    print("Decrypted: %r" % k.decrypt(d))
    assert k.decrypt(d) == data


def my_des():
    data = b"Please encrypt my data"
    k = my_encryption.DES(b"DESCRYPT", b"\0\0\0\0\0\0\0\0", pad=b"$")
    d = k.encrypt(data)
    print("Encrypted: %r" % d)
    print("Decrypted: %r" % k.decrypt(d))
    assert k.decrypt(d) == data


def my_dh():
    diffie_hellman_1 = DiffieHellman()
    diffie_hellman_2 = DiffieHellman()

    pk_1 = diffie_hellman_1.get_public_key()
    pk_2 = diffie_hellman_2.get_public_key()

    shared_1 = diffie_hellman_1.generate_shared_key(pk_2)
    time.sleep(5)
    shared_2 = diffie_hellman_2.generate_shared_key(pk_1)

    print(shared_1)
    print(shared_2)


if __name__ == "__main__":
    # original_des()
    my_dh()
