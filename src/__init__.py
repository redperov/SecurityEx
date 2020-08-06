import src.OtherDES as encryption

def main():
    data = b"Please encrypt my data"
    k = encryption.des(b"DESCRYPT", encryption.CBC, b"\0\0\0\0\0\0\0\0", pad=None, padmode=encryption.PAD_PKCS5)
    d = k.encrypt(data)
    print("Encrypted: %r" % d)
    print("Decrypted: %r" % k.decrypt(d))
    assert k.decrypt(d) == data


if __name__ == "__main__":
    main()