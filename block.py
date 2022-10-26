import hashlib as hasher

class Block:
    def __init__(self, index, timestamp, data, previous_hash, prover):
        """Return a new Block object. Each block is "chained" to its previous
        by calling its unique hash.

        Args:
            index (int): Block number.
            timestamp (int): Block creation timestamp.
            data (str): Data to be sent.
            previous_hash(str): String representing previous block unique hash.

        Attrib:
            index (int): Block number.
            timestamp (int): Block creation timestamp.
            data (str): Data to be sent.
            previous_hash(str): String representing previous block unique hash.
            hash(str): Current block unique hash.

        """
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.prover = prover
        self.hash = self.hash_block()

    def hash_block(self):
        """Creates the unique hash for the block. It uses sha256."""
        sha = hasher.sha256()
        sha.update((str(self.index) + str(self.timestamp) + str(self.data) + str(self.previous_hash) + str(self.prover)).encode('utf-8'))
        return sha.hexdigest()