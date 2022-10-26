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
from flask import Flask
import hashlib as hasher
from flask import request
from multiprocessing import Process, Pipe

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

node = Flask(__name__)

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
    data = request.get_json()
    if int(data['block']) >= 0:
        if int(data['block']) >= int(database.get_last_block()[0]) + 1:
            return json.dumps({"error": "This block hasn't mined"})
        else:
            block = database.get_block(block_id=int(data['block']))[1]
            block = {
                'index': str(block[0]),
                'timestamp': str(block[1]),
                'data': block[2],
                'hash': block[5],
                'previous_hash': block[3],
                'prover': block[4]
            }
            return json.dumps(block)
    elif int(data['block']) == -1:
        block = database.get_last_block()
        block = {
            'index': str(block[0]),
            'timestamp': str(block[1]),
            'data': block[2],
            'hash': block[5],
            'previous_hash': block[3],
            'prover': block[4]
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
            if len(new_txion['sig_message'])<=128:
                if functions.validate_signature(new_txion['from_address'],new_txion['signature'],new_txion['sig_message']):
                    if functions.check_signature_data(new_txion['sig_message'], new_txion['datetime'], new_txion['from_address'], new_txion['to_address'],
                                            new_txion['amount'], new_txion['message']) == True:
                        new_txion['amount'] = functions.toFixed(float(new_txion['amount']), 10)
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
            else:
                return "Transaction submission failed. Message too long\n"

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
    print("""=========================================\n
        KamiCoin v0.1.1 - BLOCKCHAIN SYSTEM\n
        =========================================\n\n
        You can find more help at: https://github.com/Revabrio/KamiCoin\n
        You can find more help for wallet at: https://github.com/Revabrio/KamiCoin_Wallet\n
        \n\n\n""")
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

    p1 = Process(target=functions.mine, args=(a,))
    p1.start()

    # #Start server to recieve transactions
    p2 = Process(target=node.run(host=miner_config.MINER_NODE_IP, port=miner_config.MINER_NODE_PORT), args=(b,))
    p2.start()