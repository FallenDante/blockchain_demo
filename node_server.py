from hashlib import sha256
import json,time
class Block :
    def __init__(self,index,transactions,timestamp,previous_hash):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash

    def compute_hash(self):
        block_string = json.dumps(self.__dict__,sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

class BlockChain:
    # difficulty of PoW algorithm
    difficulty = 2
    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain.The block has index 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block(0,[],time.time(),"")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self,block):
        """
        Function that tries different values of nonce to get a hash
        that satisfies our difficulty criteria.
        """
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0'*BlockChain.difficulty):
            block.nonce +=1
            computed_hash = block.compute_hash()
        return computed_hash

    def is_valid_proof(self,block,block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash.startswith('0'*BlockChain.difficulty) and  block.compute_hash() == block_hash)

    def add_block(self,block,proof):
        """
        添加区块到区块链
        :param block:  区块
        :param proof: 工作量证明.计算出的hash值
        :return:
        """
        previous_hash = self.last_block.hash
        # 验证上一个hash值
        if block.previous_hash != previous_hash:
            return False
        # 验证工作量
        if not self.is_valid_proof(block,proof):
            return False
        block.hash = proof
        self.chain.append(block)
        return True

    def add_new_transaction(self,transaction):
        self.unconfirmed_transactions.append(transaction)

    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out Proof of Work.
        """
        if not self.unconfirmed_transactions:
            return False
        last_block = self.last_block
        new_block = Block(last_block.index+1,transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),previous_hash=last_block.hash)
        proof  = self.proof_of_work(new_block)
        if self.add_block(block=new_block,proof=proof):
            self.unconfirmed_transactions = []
            return new_block.index


from flask import Flask, request
import requests

app = Flask(__name__)

# the node's copy of blockchain
blockchain = BlockChain()


@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["author", "content"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invlaid transaction data", 404

    tx_data["timestamp"] = time.time()

    blockchain.add_new_transaction(tx_data)

    return "Success", 201


# endpoint to query unconfirmed transactions
@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)


# the address to other participating members of the network
peers = set()


# endpoint to add new peers to the network.
@app.route('/add_nodes', methods=['POST'])
def register_new_peers():
    nodes = request.get_json()
    if not nodes:
        return "Invalid data", 400
    for node in nodes:
        peers.add(node)

    return "Success", 201

# endpoint to add new peers to the network.
@app.route('/add_nodes', methods=['POST'])
def register_new_peers():
    nodes = request.get_json()
    if not nodes:
        return "Invalid data", 400
    for node in nodes:
        peers.add(node)

    return "Success", 201


# endpoint to add a block mined by someone else to
# the node's chain. The block is first verified by the node
# and then added to the chain.
@app.route('/add_block', methods=['POST'])
def validate_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp",
                  block_data["previous_hash"]])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201

def announce_new_block(block):
    """
    A function to announce to the network once a block has been mined.
    Other blocks can simply verify the proof of work and add it to their
    respective chains.
    """
    for peer in peers:
        url = "http://{}/add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))
app.run(debug=True, port=8000)
