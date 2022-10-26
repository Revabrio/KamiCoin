import json
import time
import ecdsa
import base64
import random
import os.path
import requests
import eventlet
import database
from block import Block
import hashlib as hasher

def create_genesis_block():
    """To create each block, it needs the hash of the previous one. First
    block has no previous, so it must be created manually (with index zero
     and arbitrary previous hash)"""
    block = Block(0, time.time(),
        {'proof-of-work': 9,'transactions': None},
         '0', '0')

    block = {
        'index': str(block.index),
        'timestamp': str(block.timestamp),
        'data': block.data,
        'hash': block.hash,
        'previous_hash': 0,
        'prover': block.prover
    }

    return block

def find_new_chains(blockchain):
    # Get the blockchains of every other node
    longest_chain = blockchain
    for node_url in []:
        # Get their chains using a GET request
        try:
            chain = None
            with eventlet.Timeout(5, False):
                chain = requests.get(node_url + "/blocks").content
                eventlet.sleep(0)
            if chain is not None:
                # Convert the JSON object to a Python dictionary
                chain = json.loads(chain)
            else:
                print('Request to '+node_url+' has exceeded it\'s timeout.')
                continue

            # Verify other node block is correct
            if len(chain) > len(longest_chain):
                longest_chain = chain

        except Exception:
            print('Connection to '+node_url+' failed')
    return longest_chain

def consensus():
    blockchain = 0
    # Get the blocks from other nodes
    longest_chain = find_new_chains(blockchain)
    # If our chain isn't longest, then we store the longest chain
    BLOCKCHAIN = blockchain

    # If the longest chain wasn't ours, then we set our chain to the longest
    if longest_chain == BLOCKCHAIN:
        # Keep searching for proof
        return False

    # validated = validate_blockchain(longest_chain, blockchain)
    # print('VALIDATED: '+str(validated))
    # if validated:
    #     # Give up searching proof, update chain and start over again
    #     BLOCKCHAIN = longest_chain
    #     print('external blockcain passed validation\n')
    #     return BLOCKCHAIN
    # else:
    #     print('external blockcain did not pass validation\n')
    #     return False

def validate_blockchain(alien_chain, my_chain):

    index = 0

    if len(my_chain) > 1 and alien_chain[len(my_chain)-1]['hash'] == my_chain[-1]['hash']:
        index = len(my_chain)
    else:
        index = 0
        open('ledger.txt', 'w').close()

    if not os.path.isfile('ledger.txt'):
        open('ledger.txt', 'a').close()
        index = 0

    length_of_chain = len(alien_chain)

    while(index < length_of_chain):
        if index == 0:
            index += 1
            continue
        # 1st - verification integrity
        sha = hasher.sha256()
        sha.update( (str(alien_chain[index]['previous_hash']) + str(alien_chain[index]['prover'])).encode('utf-8'))
        digest = str(sha.hexdigest())
        if (digest[:len(database.get_config_data(target=1))] != database.get_config_data(target=1)):
            print('digest does not match')
            return False
        # 2st - verification of double spending
        #transactions = (chain[index]["data"]).replace("'", '"')
        transactions = json.loads((alien_chain[index]["data"]).replace("'", '"'))

        if len(validate_transactions(transactions["transactions"])) != len(transactions["transactions"]):
            return False

        index += 1

    return True

def get_wallet_balance(wallet_address):
    balance = 0.0
    block_id = 0
    while block_id <= int(database.get_last_block()[0]):
        transactions = json.loads(database.get_block(block_id=block_id)[1][2])
        transactions = transactions['transactions']
        if transactions == None or transactions == []:
            pass
        else:
            for transaction in transactions:
                if transaction['from_address'] == wallet_address:
                    balance -= float(transaction['amount'])
                if transaction['to_address'] == wallet_address:
                    balance += float(transaction['amount'])
        block_id += 1
    return balance

def check_signature_data(message, from_address, to_address, amount):
    data = message.split('|||')
    if data[1] == from_address:
        if data[2] == to_address:
            if data[3] == str(amount):
                return True
            else:
                return False
        else:
            return False
    else:
        return False

def validate_signature(public_key,signature,message):
    """Verify if the signature is correct. This is used to prove if
    it's you (and not someon else) trying to do a transaction with your
    address. Called when a user try to submit a new transaction.
    """
    public_key = (base64.b64decode(public_key)).hex()
    signature = base64.b64decode(signature)
    vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key), curve=ecdsa.SECP256k1)
    try:
        return(vk.verify(signature, message.encode()))
    except:
        return False

def sign_ECDSA_msg(private_key, public_key, to, amount):
    """Sign the message to be sent
    private_key: must be hex

    return
    signature: base64 (to make it shorter)
    message: str
    """
    #get timestamp, round it, make it string and encode it to bytes
    message=str(round(time.time()))+ public_key + to + amount
    bmessage = message.encode()
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
    signature = base64.b64encode(sk.sign(bmessage))
    return signature,message

def initialize_miner():
    if database.get_block(block_id=0)[0] == 1:
        return True
    else:
        return False

def validate_transactions(transactions):

    flawed = False
    network_checked = False
    valid_transactions = []
    for transaction in transactions:
        if transaction['from'] == 'network' and float(transaction['amount']) == 1:
            if network_checked:
                print('FLAWED!!! ' +str(transaction['from']) + ' ' + transaction['to'] + ' ' + transaction['amount'] )
                print('network is trying to pay off more coins than it is normally set up\n')
                flawed = True
            network_checked = True
        elif transaction['from'] == 'reward_center':
            if validate_signature(transaction['from_address'], transaction['signature'], transaction['message']) == True:
                valid_transactions.append(transaction)
                print(f'Transaction from {transaction["from"]} for {transaction["amount"]} was successfull')
        elif transaction['from_address'] != 'network':
            if validate_signature(transaction['from_address'], transaction['signature'], transaction['message']) == True:
                wallet_balance = get_wallet_balance(transaction['from'])
                if float(wallet_balance) >= float(transaction['amount']):
                    valid_transactions.append(transaction)
                    print(f'Transaction from {transaction["from_address"]} for {transaction["amount"]} was successfull')
    if flawed == True:
        return []
    else:
        return transactions

    # for transaction in transactions:
    #     flawed = False
    #     f = open('ledger.txt')
    #     filedata = []
    #     for line in f:
    #         if line != '\n':
    #             filedata.append(line)
    #     f.close()
    #
    #     # Checking of the network reward
    #     if transaction['from'] == 'network' and float(transaction['amount']) == 1:
    #         if network_checked:
    #             print('FLAWED!!! ' +str(transaction['from']) + ' ' + transaction['to'] + ' ' + transaction['amount'] )
    #             print('network is trying to pay off more coins than it is normally set up\n')
    #             flawed = True
    #             continue
    #         network_checked = True
    #
    #     # Checking of the users spending amounts
    #     transaction_from_found = False
    #     counter = 0
    #     length_of_filedata = len(filedata)
    #
    #     if transaction['from'] != 'network':
    #         while counter < length_of_filedata and not flawed:
    #             data = filedata[counter].split(':')
    #             if data[0] == transaction['from']:
    #                 transaction_from_found = True
    #                 if float(data[1]) < float(transaction['amount']):
    #                     print('FLAWED!!! ' +str(transaction['from']) + ' ' + transaction['to'] + ' ' + transaction['amount'] )
    #                     print('transferred amount is more than expected')
    #                     flawed = True
    #                     break
    #                 amount = float(data[1])
    #                 amount -= float(transaction['amount'])
    #                 data[1] = amount
    #                 filedata[counter] = str(data[0]) + ':' +str(float(data[1]))
    #             counter += 1
    #         if not transaction_from_found:
    #             print('address has not been found')
    #             flawed = True
    #             continue
    #
    #     if flawed:
    #         continue
    #     # Checking of the users income amounts
    #     transaction_to_found = False
    #     counter = 0
    #     length_of_filedata = len(filedata)
    #
    #     if length_of_filedata > 0:
    #         while counter < length_of_filedata:
    #             data = filedata[counter].split(':')
    #             if transaction['to'] == data[0]:
    #                 transaction_to_found = True
    #                 amount = float(data[1])
    #                 amount += float(transaction['amount'])
    #                 data[1] = amount
    #                 filedata[counter] = str(data[0]) + ':' +str(float(data[1]))
    #             counter += 1
    #
    #     if transaction_to_found == False:
    #         filedata.append(str(transaction['to'])+':'+str(float(transaction['amount'])))
    #
    #     f = open('ledger.txt', 'w')
    #     line_counter = 0
    #     length_of_filedata = len(filedata)
    #
    #     for line in filedata:
    #         if line != '\n':
    #             if line[-1] != '\n':
    #                 f.write(line + '\n')
    #             else:
    #                 f.write(line)
    #
    #     f.close()
    #
    #     valid_transactions.append(transaction)
    #
    # return valid_transactions

def get_complexity(sharetime, user_complexity):
    num = int((2-(sharetime/int(database.get_config_data(expected_sharetime=1))))*user_complexity)
    if num < 1:
        return num * -1
    elif num == 0:
        return int(database.get_config_data(complexity=1))
    else:
        return num

def toFixed(numObj, digits=0):
    return f"{numObj:.{digits}f}"

def get_complexity_reward(user_complexity):
    return toFixed(float((user_complexity/50**len(str(user_complexity)))), 10)

def check_stats():
    if int(time.strftime("%H")) - int(database.get_config_data(start_hour=1)) >= 1:
        database.update_stats_coin(str(0.0))

def add_balance(user_iden, reward):
    data = {}
    data['from'] = "reward_center"
    data['from_address'] = database.get_config_data(REWARD_CENTER_NODE_PUBLIC_KEY=1)
    data['to'] = user_iden
    data['amount'] = reward
    signature, message = sign_ECDSA_msg(database.get_config_data(REWARD_CENTER_NODE_PRIVATE_KEY=1),
                                        database.get_config_data(REWARD_CENTER_NODE_PUBLIC_KEY=1), user_iden, str(reward))
    data['signature'] = signature
    data['message'] = message
    database.add_pending_transaction(data)
    database.update_stats_coin(float(database.get_stat_new_coins())+float(reward))

def get_random_float():
    randoms = [1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]
    return randoms[random.randint(0, len(randoms)-1)]

def proof_of_work(last_proof):
  # Create a variable that we will use to find our next proof of work
  incrementor = random.randrange(0, 500000000)
  i = 0
  found = False
  start_time = time.time()
  timefound = 0
  time_printed = False
  # Keep incrementing the incrementor until it's equal to a number divisible by 9
  # and the proof of work of the previous block in the chain
  #while not (incrementor % 7919 == 0 and incrementor % last_proof == 0):
  while not found:
      incrementor += 1
      i += 1
      sha = hasher.sha256()
      sha.update((str(database.get_last_block()[5]) + str(incrementor)).encode('utf-8'))
      digest = str(sha.hexdigest())

      if (timefound != int((time.time()-start_time))):
          timefound = int((time.time()-start_time))
          time_printed = False

      if (time_printed == False and timefound != 0 and timefound % 60 == 0):
          print('speed - '+str(int(i/timefound)/1000)+' KH\s' + ', blockchain\'s length is ' + str(int(database.get_last_block()[0])+1) +'\n')
          time_printed = True

      if (digest[:len(database.get_config_data(target=1))] == database.get_config_data(target=1)):
          found = True
          print("")
          print(digest + ' - ' +str(i) +' FOUND!!!')
          timefound = int((time.time()-start_time))

      # # Check if any node found the solution every 60 seconds
      # if (int(i%200000)==0):
      #     # If any other node got the proof, stop searching
      #     new_blockchain = consensus(blockchain)
      #     if new_blockchain != False:
      #         #(False:another node got proof first, new blockchain)
      #         return (False,new_blockchain)
  # Once that number is found, we can return it as a proof of our work
  return incrementor