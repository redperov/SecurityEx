# Type of work mode
from src.myEncryption import vectors

# constants
KEY_SIZE = 8
ENCRYPT = 0x00
DECRYPT = 0x01


class DES:
    """
    Performs DES encryption/decryption.
    """

    def __init__(self, key, iv=None, pad=None):
        """
        Constructor
        :param key: encryption key (of size 8 bytes)
        :param iv: initial vector
        :param pad: padding
        """
        self.block_size = KEY_SIZE
        self._iv = iv
        self._padding = pad

        # Validation checks
        if len(key) != KEY_SIZE:
            raise ValueError("Key must be of size 8 bytes")

        if iv and len(iv) != self.block_size:
            raise ValueError("Illegal IV size")

        # Variable initialisation
        self.left = []
        self.right = []
        self.Kn = [[0] * 48] * 16  # 16 48-bit keys (K1 - K16)
        self.final = []

        self._set_key(key)

    def _set_key(self, key):
        """
        Sets the encryption key
        :param key: encryption key
        """
        self._key = key
        self._create_sub_keys()

    def _create_sub_keys(self):
        """
        Creates 16 sub-keys from the initial key.
        """
        key = self._permute(vectors.pc1, self._string_to_bitlist(self._key))

        # Split the key into left and right sections
        self.left = key[:28]
        self.right = key[28:]
        i = 0

        while i < 16:
            j = 0

            # Perform circular left shifts
            while j < vectors.left_rotations[i]:
                self.left.append(self.left[0])
                del self.left[0]

                self.right.append(self.right[0])
                del self.right[0]

                j += 1

            # Create one of the 16 sub-keys through pc2 permutation
            self.Kn[i] = self._permute(vectors.pc2, self.left + self.right)

            i += 1

    def __des_crypt(self, block, crypt_type):
        """
        Performs bit manipulation on the given block
        :param block: block to manipulate
        :param crypt_type: manipulation type
        :return: manipulated block
        """
        """Crypt the block of data through DES bit-manipulation"""
        block = self._permute(vectors.ip, block)
        self.left = block[:32]
        self.right = block[32:]

        # Encryption starts from Kn[1] through to Kn[16]
        if crypt_type == ENCRYPT:
            iteration = 0
            iteration_adjustment = 1
        # Decryption starts from Kn[16] down to Kn[1]
        else:
            iteration = 15
            iteration_adjustment = -1

        i = 0

        while i < 16:
            # Make a copy of R[i-1], this will later become L[i]
            tempR = self.right[:]

            # Permute R[i - 1] to start creating R[i]
            self.right = self._permute(vectors.expansion_table, self.right)

            # Exclusive or R[i - 1] with K[i], create B[1] to B[8] whilst here
            self.right = list(map(lambda x, y: x ^ y, self.right, self.Kn[iteration]))
            B = [self.right[:6], self.right[6:12], self.right[12:18], self.right[18:24], self.right[24:30],
                 self.right[30:36], self.right[36:42],
                 self.right[42:]]

            # Permute B[1] to B[8] using the S-Boxes
            j = 0
            Bn = [0] * 32
            pos = 0
            while j < 8:
                # Work out the offsets
                m = (B[j][0] << 1) + B[j][5]
                n = (B[j][1] << 3) + (B[j][2] << 2) + (B[j][3] << 1) + B[j][4]

                # Find the permutation value
                v = vectors.sbox[j][(m << 4) + n]

                # Turn value into bits, add it to result: Bn
                Bn[pos] = (v & 8) >> 3
                Bn[pos + 1] = (v & 4) >> 2
                Bn[pos + 2] = (v & 2) >> 1
                Bn[pos + 3] = v & 1

                pos += 4
                j += 1

            # Permute the concatenation of B[1] to B[8] (Bn)
            self.right = self._permute(vectors.p, Bn)

            # Xor with L[i - 1]
            self.right = list(map(lambda x, y: x ^ y, self.right, self.left))

            # L[i] becomes R[i - 1]
            self.left = tempR

            i += 1
            iteration += iteration_adjustment

        # Final permutation of R[16]L[16]
        self.final = self._permute(vectors.fp, self.right + self.left)
        return self.final

    def crypt(self, data, crypt_type):
        """
        Manipulates the data in block.
        :param data: data to manipulate
        :param crypt_type: manipulation type
        :return: manipulated data
        """

        # Error check the data
        if not data:
            return ''
        if len(data) % self.block_size != 0:
            if crypt_type == DECRYPT:  # Decryption must work on 8 byte blocks
                raise ValueError(
                    "Invalid data length, data must be a multiple of " + str(self.block_size) + " bytes\n.")
            if not self._padding:
                raise ValueError("Invalid data length, data must be a multiple of " + str(
                    self.block_size) + " bytes\n. Try setting the optional padding character")
            else:
                data += (self.block_size - (len(data) % self.block_size)) * self._padding

        # Split the data into blocks, crypting each one seperately
        i = 0
        result = []
        while i < len(data):
            block = self._string_to_bitlist(data[i:i + 8])

            processed_block = self.__des_crypt(block, crypt_type)

            result.append(self._bitlist_to_string(processed_block))

            i += 8

        # Return the fully manipulated string
        return bytes.fromhex('').join(result)

    def encrypt(self, data, pad=None):
        """encrypt(data, [pad]) -> bytes

        data : Bytes to be encrypted
        pad  : Optional argument for encryption padding. Must only be one byte

        The data must be a multiple of 8 bytes and will be encrypted
        with the already specified key. Data does not have to be a
        multiple of 8 bytes if the padding character is supplied.
        """
        data = self._pad_data(data, pad)
        return self.crypt(data, ENCRYPT)

    def decrypt(self, data, pad=None):
        """decrypt(data, [pad]) -> bytes

        data : Bytes to be decrypted
        pad  : Optional argument for decryption padding. Must only be one byte

        The data must be a multiple of 8 bytes and will be decrypted
        with the already specified key. If the optional padding character
        is supplied, then the un-encrypted data will have the padding characters
         removed from the end of the bytes. This pad removal only occurs on the last 8 bytes of
        the data (last data block).
        """
        data = self.crypt(data, DECRYPT)
        return self._remove_padding(data, pad)

    def _permute(self, table, block):
        return list(map(lambda x: block[x], table))

    def _string_to_bitlist(self, data):
        """
        Converts the string to a bit list.
        :param data: data to convert
        :return: bit-list
        """
        data_length = len(data) * KEY_SIZE
        result = [0] * data_length
        counter = 0

        for char in data:
            i = 7

            while i >= 0:

                if char & (1 << i) != 0:
                    result[counter] = 1
                else:
                    result[counter] = 0
                counter += 1
                i -= 1

        return result

    def _bitlist_to_string(self, data):
        """
        Converts the bit-list into a string.
        :param data: data to convert
        :return: string
        """
        result = []
        position = 0
        char = 0
        while position < len(data):
            char += data[position] << (7 - (position % 8))
            if (position % 8) == 7:
                result.append(char)
                char = 0
            position += 1

        return bytes(result)

    def _pad_data(self, data, pad):
        """
        Pads the data
        """
        # Check if the data requires padding
        if len(data) % self.block_size == 0:
            return data

        if not pad:
            # Get the default padding.
            pad = self._padding

        if not pad:
            raise ValueError("The data requires padding")
        data += (self.block_size - (len(data) % self.block_size)) * pad

        return data

    def _remove_padding(self, data, pad):
        """
        Removes the padding
        """
        if not pad:
            # Get the default padding.
            pad = self._padding

        if pad:
            data = data[:-self.block_size] + \
                   data[-self.block_size:].rstrip(pad)

        return data
