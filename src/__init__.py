import src.OtherDES as encryption
import src.myEncryption.DES as my_encryption

# TODO remove that

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


if __name__ == "__main__":
    #original_des()
    my_des()
