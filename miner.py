#!/usr/bin/env python3
import json
import time
import random
import hashlib
import logging
import eventlet
import database
import functions
import miner_config
from block import Block
from flask import Flask
import hashlib as hasher
from flask import request
from multiprocessing import Process, Pipe

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

node = Flask(__name__)

def mine(a):
    while True:
        """Mining is the only way that new coins can be created.
        In order to prevent too many coins to be created, the process
        is slowed down by a proof of work algorithm.
        """
        # Get the last proof of work

        last_block = database.get_last_block()
        try:
            last_proof = last_block.data['proof-of-work']
        except Exception:
            last_proof = 0

        print('starting a new search round\n')
        # Find the proof of work for the current block being mined
        # Note: The program will hang here until a new proof of work is found
        proof = functions.proof_of_work(last_proof)
        # If we didn't guess the proof, start mining again
        # if proof[0] == False:
        #     # Update blockchain and save it to file
        #     BLOCKCHAIN = proof[1]
        #     i = 0
        #     for item in BLOCKCHAIN:
        #         package = []
        #         package.append('chunk')
        #         package.append(item)
        #         package.append(i)
        #         a.send(package)
        #         requests.get(MINER_NODE_URL + "/blocks?update=" + 'syncing'+str(i))
        #         while(a.recv() != i):
        #             wait = True
        #
        #         i += 1
        #
        #     sha = hasher.sha256()
        #     sha.update( str(json.dumps(BLOCKCHAIN)).encode('utf-8') )
        #     digest = str(sha.hexdigest())
        #     package = []
        #     package.append('digest')
        #     package.append(digest)
        #     a.send(package)
        #     requests.get(MINER_NODE_URL + "/blocks?update=" + 'syncing_digest')
        #     print('synced with an external chain\n')
        #     continue
        #else:
        if proof != False:
            # Once we find a valid proof of work, we know we can mine a block so
            # we reward the miner by adding a transaction
            #First we load all pending transactions sent to the node server
            # data = None
            # with eventlet.Timeout(5, False):
            #     url     = MINER_NODE_URL + "/txion?update=" + MINER_ADDRESS
            #     payload = {"source": "miner", "option":"pendingtxs", "address": MINER_ADDRESS}
            #     headers = {"Content-Type": "application/json"}
            #
            #     data = requests.post(url, json=payload, headers=headers).text
            #     eventlet.sleep(0)
            #
            # if data is not None:
            #     NODE_PENDING_TRANSACTIONS = json.loads(data)
            # else:
            #     print('local request failed')
            #     continue

            NODE_PENDING_TRANSACTIONS = []
            pending_transactions = database.get_pending_transaction()
            while pending_transactions != 0:
                NODE_PENDING_TRANSACTIONS.append(
                    {
                        'from': pending_transactions[0],
                        'from_address': pending_transactions[1],
                        'to_address': pending_transactions[2],
                        'amount': pending_transactions[3],
                        'signature': pending_transactions[4],
                        'message': pending_transactions[5]
                    }
                )
                database.del_pending_transaction(pending_transactions[6])
                pending_transactions = database.get_pending_transaction()

            # #Then we add the mining reward
            # NODE_PENDING_TRANSACTIONS.append(
            # { 'from': 'network',
            #   'to': MINER_ADDRESS,
            #   'amount': 1 }
            # )

            NODE_PENDING_TRANSACTIONS = functions.validate_transactions(list(NODE_PENDING_TRANSACTIONS))

            # Now we can gather the data needed to create the new block
            new_block_data = {
            'proof-of-work': proof,
            'transactions': NODE_PENDING_TRANSACTIONS
            }
            new_block_index = int(last_block[0]) + 1
            new_block_timestamp = time.time()
            last_block_hash = last_block[5]
            # Empty transaction list
            NODE_PENDING_TRANSACTIONS = []
            # Now create the new block
            mined_block = Block(new_block_index, new_block_timestamp, new_block_data, last_block_hash, proof)
            #BLOCKCHAIN.append(mined_block)
            block_to_add = {
                'index': str(mined_block.index),
                'timestamp': str(mined_block.timestamp),
                'data': mined_block.data,
                'hash': mined_block.hash,
                'previous_hash': mined_block.previous_hash,
                "prover": mined_block.prover
            }
            database.add_block(block_to_add)
            functions.check_stats()
            #BLOCKCHAIN.append(block_to_add)
            # Let the client know this node mined a block
            print(json.dumps({
              'index': new_block_index,
              'timestamp': str(new_block_timestamp),
              'data': new_block_data,
              'hash': last_block_hash
            }) + "\n")

            # with eventlet.Timeout(5,False):
            #     i = 0
            #     for item in BLOCKCHAIN:
            #         package = []
            #         package.append('chunk')
            #         package.append(item)
            #         package.append(i)
            #         a.send(package)
            #         requests.get(MINER_NODE_URL + "/blocks?update=" + "internal_syncing")
            #         while(a.recv() != i):
            #             wait = True
            #
            #         i += 1
            #
            #     sha = hasher.sha256()
            #     sha.update( str(json.dumps(BLOCKCHAIN)).encode('utf-8') )
            #     digest = str(sha.hexdigest())
            #     package = []
            #     package.append('digest')
            #     package.append(digest)
            #     a.send(package)
            #     requests.get(MINER_NODE_URL + "/blocks?update=" + "internal_syncing")
            #     eventlet.sleep(0)

@node.route('/getWork', methods=['GET'])
def getWork():
    if not request.json:
        return json.dumps({"error"})
    else:
        try:
            user_iden = request.json.get('userIdentificator')
            miner_name = request.json.get('minerName')
            miner_type = request.json.get('minerType')
            if database.get_work_user_data(user_iden, miner_name) == 0:
                database.add_new_work_user(user_iden, miner_name, miner_type, database.get_config_data(complexity=1))
            functions.check_stats()
            if float(database.get_config_data(max_coins=1)) > float(database.get_stat_new_coins()):
                if float(time.time()) - float(database.get_work_user_data(user_iden, miner_name)[3]) > 120:
                    database.update_work_user_data(user_iden, miner_name, level=1, time_start=-1, success_works=-1, num=-1, salt=-1,
                                                   hash=-1, hashrate=-1)
                user_complexity = int(database.get_work_user_data(user_iden, miner_name)[7])
                num_min = int(user_complexity/functions.get_random_float())
                num_max = user_complexity
                num = random.randint(num_min, num_max)
                salt = database.get_last_block()[5]
                hash_work = hashlib.sha256((str(num)+salt).encode('utf-8')).hexdigest()
                database.update_work_user_data(user_iden, miner_name, time_start=int(time.time()), num=num, salt=salt, hash=hash_work)
                if database.get_work_user_data(user_iden, miner_name)[7] == -1:
                    pass
                return json.dumps({"salt": salt, "hash": hash_work, "max": num_max})
            else:
                return json.dumps({"error": 2})
        except:
            return json.dumps({"error"})

@node.route('/checkWork', methods=['POST'])
def checkWork():
    if not request.json:
        return json.dumps({"error": 1})
    else:
        try:
            user_iden = request.json.get('userIdentificator')
            miner_name = request.json.get('minerName')
            miner_type = request.json.get('minerType')
            number = request.json.get('number')
            hashrate = request.json.get('hashrate')
            if database.get_work_user_data(user_iden, miner_name) == 0:
                return json.dumps({"error": 1})
            if int(database.get_work_user_data(user_iden, miner_name)[4]) != -1:
                if time.time() - float(database.get_work_user_data(user_iden, miner_name)[3]) < 120:
                    if int(number) == int(database.get_work_user_data(user_iden, miner_name)[4]):
                        functions.check_stats()
                        if float(database.get_config_data(max_coins=1)) > float(database.get_stat_new_coins()):
                            old_complexity = int(database.get_work_user_data(user_iden, miner_name)[7])
                            new_complexity = functions.get_complexity(time.time() - int(database.get_work_user_data(user_iden, miner_name)[3]), old_complexity)
                            database.update_work_user_data(user_iden, miner_name, num=-1,
                                                           success_works=int(database.get_work_user_data(user_iden, miner_name)[2])+1,
                                                           complexity=new_complexity, hashrate=hashrate)
                            functions.add_balance(user_iden, functions.get_complexity_reward(old_complexity))
                            return json.dumps({"success": 1})
                        else:
                            return json.dumps({"error": 2})
                    else:
                        database.update_work_user_data(user_iden, miner_name, bad_works=int(database.get_work_user_data(user_iden, miner_name)[10])+1)
                        return json.dumps({"success": 0})
                else:
                    return json.dumps({"success": 0})
            else:
                return json.dumps({"success": 0})
        except:
            return json.dumps({"error": 1})

@node.route('/getMiner', methods=['POST'])
def getMiner():
    if not request.json:
        return json.dumps({"error": 1})
    else:
        try:
            user_iden = request.json.get('userIdentificator')
            miners = database.get_user_miners(user_iden)
            temp = []
            for miner in miners:
                temp.append({
                    'userIdentificator': miner[0],
                    'success_works': miner[2],
                    'bad_works': miner[10],
                    'complexity': miner[8],
                    'minerName': miner[8],
                    'minerType': miner[9]
                })
            return_miners = {'userIdentificator': {'miners': {temp}}}
        except:
            pass

@node.route('/blocks', methods=['GET','POST'])
def get_blocks():
    # Load current blockchain. Only you, should update your blockchain
    if request.args.get("update") == 'internal_syncing' or (str(request.args.get("update")))[:7] == 'syncing':
        global BLOCKCHAIN
        global received_blockchain
        with eventlet.Timeout(5, False):
            data = b.recv()
            eventlet.sleep(0)
        if data is not None:
            if data[0] == 'chunk':
                if data[2] == 0:
                    received_blockchain = []
                received_blockchain.append(data[1])
                b.send(data[2])
            elif data[0] == 'digest':
                sha = hasher.sha256()
                sha.update( str(json.dumps(received_blockchain)).encode('utf-8') )
                digest = str(sha.hexdigest())
                if digest == data[1]:
                    BLOCKCHAIN = received_blockchain
                else:
                    print('Received blockchain is corrupted.')
    return json.dumps({"error": "Unknown parameters"})

@node.route('/block_num', methods=['GET'])
def get_num_blocks():
    return json.dumps({"blocks_num": int(database.get_last_block()[0]) + 1})

@node.route('/block_get', methods=['GET'])
def get_block():
    if int(request.args.get("block")) >= 0:
        if int(request.args.get("block")) >= int(database.get_last_block()[0]) + 1:
            return json.dumps({"error": "This block hasn't mined"})
        else:
            block = database.get_block(block_id=int(request.args.get("block")))[1]
            block = {
                "index": str(block[0]),
                "timestamp": str(block[1]),
                "data": str(block[2]),
                "hash": block[5],
                "previous_hash": block[3],
                "prover": block[4]
            }
            return json.dumps(block)
    elif int(request.args.get("block")) == -1:
        block = database.get_last_block()
        block = {
            "index": str(block[0]),
            "timestamp": str(block[1]),
            "data": str(block[2]),
            "hash": block[5],
            "previous_hash": block[3],
            "prover": block[4]
        }
        return json.dumps(block)
    return json.dumps({"error": "Unknown parameters"})

@node.route('/txion', methods=['GET','POST'])
def transaction():
    """Each transaction sent to this node gets validated and submitted.
    Then it waits to be added to the blockchain. Transactions only move
    coins, they don't create it.
    """
    if request.method == 'POST':
        # On each new POST request, we extract the transaction data
        new_txion = request.get_json()
        if new_txion['source'] == "wallet" and new_txion['option'] == "newtx":
            # Then we add the transaction to our list
            if functions.validate_signature(new_txion['from_address'],new_txion['signature'],new_txion['message']):
                if functions.check_signature_data(new_txion['message'], new_txion['from_address'], new_txion['to_address'],
                                        new_txion['amount']) == True:
                    if float(new_txion['amount']) > 0.0000000001:
                        new_txion['from'] = ''
                        database.add_pending_transaction(new_txion)
                        #NODE_PENDING_TRANSACTIONS.append(new_txion)
                        # Because the transaction was successfully
                        # submitted, we log it to our console
                        print("New transaction")
                        print("FROM: {0}".format(new_txion['from_address']))
                        print("TO: {0}".format(new_txion['to_address']))
                        print("AMOUNT: {0}\n".format(new_txion['amount']))
                        # Then we let the client know it worked out
                        return "Transaction submission successful\n"
                    else:
                        return "Transaction submission failed. Summ < 0.0000000001\n"
                else:
                    return "Transaction submission failed. Wrong signature\n"
            else:
                return "Transaction submission failed. Wrong signature\n"

        elif new_txion['source'] == "wallet" and new_txion['option'] == "balance":
            print(new_txion['wallet'])
            return str(functions.toFixed(functions.get_wallet_balance(new_txion['wallet']), 10))
             # f = open('ledger.txt')
             # filedata = []
             # for line in f:
             #     if line != '\n':
             #         filedata.append(line)
             # f.close()
             # wallet_found = False
             # for line in filedata:
             #     data = line.split(':')
             #     if data[0] == new_txion['wallet']:
             #         wallet_found = True
             #         return data[1]
             # if wallet_found == False:
             #     return "0"


        #Send pending transactions to the mining process
        elif new_txion['source'] == "miner" and new_txion["option"] == "pendingtxs":
            pass
            #pending = json.dumps(NODE_PENDING_TRANSACTIONS)
            # Empty transaction list
            #NODE_PENDING_TRANSACTIONS[:] = []
            #return pending
        else:
            return 'Arguments not specified'

def welcome_msg():
    print("""       =========================================\n
        SIMPLE COIN v1.0.0 - BLOCKCHAIN SYSTEM\n
       =========================================\n\n
        You can find more help at: https://github.com/Scotchmann/SimpleCoin\n
        Make sure you are using the latest version or you may end in
        a parallel chain.\n\n\n""")
    print('Miner has been started at '+miner_config.MINER_NODE_URL+'! Good luck!\n')

if __name__ == '__main__':
    database.update_config_data(start_hour=time.strftime("%H"))
    welcome_msg()
    b, a = Pipe(duplex=True)
    answer = functions.initialize_miner()
    if answer == True:
        answer_consensus = functions.consensus()
        if answer_consensus == True:
            print('Blockchain successfully initialized')
        else:
            print('Blockchain has been initialized with an external chain')
    else:
        print('Blockchain is empty, another chains dont exist, creating new chain')
        database.add_block(functions.create_genesis_block())

    p1 = Process(target=mine, args=(a,))
    p1.start()

    # #Start server to recieve transactions
    p2 = Process(target=node.run(host=miner_config.MINER_NODE_IP, port=miner_config.MINER_NODE_PORT), args=(b,))
    p2.start()