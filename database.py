import time
import json
import sqlite3
from miner_config import database_file

def add_block(block_data):
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO blocks (id, timestamp, data, previous_hash, prover, hash) VALUES (?, ?, ?, ?, ?, ?)",
                    (block_data['index'], block_data['timestamp'], json.dumps(block_data['data']),
                     block_data['previous_hash'], block_data['prover'], block_data['hash']))
        conn.commit()
        conn.close()
        return 1
    except:
        conn.close()
        return -1

def add_block_another_node(block_data):
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO blocks_wait (id, timestamp, data, previous_hash, prover, hash) VALUES (?, ?, ?, ?, ?, ?)",
                    (block_data['index'], block_data['timestamp'], json.dumps(block_data['data']),
                     block_data['previous_hash'], block_data['prover'], block_data['hash']))
        conn.commit()
        conn.close()
        return 1
    except:
        conn.close()
        return -1

def add_pending_transaction(transaction_data):
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO pending_transactions (from_type, from_transaction, to_transaction, amount_transaction, "
                    "signature_transaction, sig_message, message_transaction, timestamp_transaction) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (str(transaction_data['from']), str(transaction_data['from_address']), str(transaction_data['to_address']),
                     str(transaction_data['amount']), str(transaction_data['signature']), str(transaction_data['sig_message']),
                     str(transaction_data['message']), str(transaction_data['datetime']),))
        conn.commit()
        conn.close()
        return 1
    except:
        conn.close()
        return -1

def add_new_work_user(user_iden, miner_name, miner_type, complexity):
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO works (user_iden, level, success_works, time_start, num, salt, hash, complexity, "
                    "minerName, minerType, bad_works, hashrate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (str(user_iden), 1, 0, time.time(), -1, -1, -1, complexity, miner_name, miner_type, 0, 0,))
        conn.commit()
        conn.close()
        return 1
    except:
        conn.close()
        return -1

def get_config_data(PEER_NODES = -1, expected_sharetime = -1, complexity = -1, max_coins = -1,
                    REWARD_CENTER_NODE_PRIVATE_KEY = -1, REWARD_CENTER_NODE_PUBLIC_KEY = -1, start_hour = -1,
                    target = -1, new_block = -1):
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        if PEER_NODES != -1:
            cur.execute("SELECT data FROM config WHERE name = ?", ('PEER_NODES',))
            row = cur.fetchone()
        if expected_sharetime != -1:
            cur.execute("SELECT data FROM config WHERE name = ?", ('expected_sharetime',))
            row = cur.fetchone()
        if complexity != -1:
            cur.execute("SELECT data FROM config WHERE name = ?", ('complexity',))
            row = cur.fetchone()
        if max_coins != -1:
            cur.execute("SELECT data FROM config WHERE name = ?", ('max_coins',))
            row = cur.fetchone()
        if REWARD_CENTER_NODE_PRIVATE_KEY != -1:
            cur.execute("SELECT data FROM config WHERE name = ?", ('REWARD_CENTER_NODE_PRIVATE_KEY',))
            row = cur.fetchone()
        if REWARD_CENTER_NODE_PUBLIC_KEY != -1:
            cur.execute("SELECT data FROM config WHERE name = ?", ('REWARD_CENTER_NODE_PUBLIC_KEY',))
            row = cur.fetchone()
        if start_hour != -1:
            cur.execute("SELECT data FROM config WHERE name = ?", ('start_hour',))
            row = cur.fetchone()
        if target != -1:
            cur.execute("SELECT data FROM config WHERE name = ?", ('target',))
            row = cur.fetchone()
        if new_block != -1:
            cur.execute("SELECT data FROM config WHERE name = ?", ('new_block',))
            row = cur.fetchone()
        try:
            if row:
                conn.close()
                return row[0]
            else:
                conn.close()
                return 0
        except:
            return 0
    except:
        conn.close()
        return -1

def get_block(block_id=-1, block_hash=-1):
    conn = sqlite3.connect(database_file)
    if block_id != -1:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM blocks WHERE id = ?", (block_id,))
            row = cur.fetchone()
            if row:
                if row[0] == block_id:
                    conn.close()
                    return 1, row
            else:
                conn.close()
                return 0, 0
        except:
            conn.close()
            return -1
    elif block_hash !=-1:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM blocks WHERE hash = ?", (block_hash,))
            row = cur.fetchone()
            if row:
                if row[5] == block_hash:
                    conn.close()
                    return 1, row
            else:
                conn.close()
                return 0, 0
        except:
            conn.close()
            return -1

def get_block_another_node(block_id=-3):
    conn = sqlite3.connect(database_file)
    if block_id > 0:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM blocks_wait WHERE id = ?", (block_id,))
            row = cur.fetchone()
            if row:
                if row[0] == block_id:
                    conn.close()
                    return 1, row
            else:
                conn.close()
                return 0, 0
        except:
            conn.close()
            return -1
    elif block_id == -1:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM blocks_wait", (block_id,))
            row = cur.fetchone()
            if row:
                if row[0] == block_id:
                    conn.close()
                    return 1, row
            else:
                conn.close()
                return 0, 0
        except:
            conn.close()
            return -1
    elif block_id == -2:
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM blocks_wait ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            if row:
                if row[0] == block_id:
                    conn.close()
                    return 1, row
            else:
                conn.close()
                return 0, 0
        except:
            conn.close()
            return -1

def get_last_block():
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM blocks ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            conn.close()
            return row
        else:
            conn.close()
            return 0
    except:
        conn.close()
        return -1

def get_pending_transaction():
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM pending_transactions DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            conn.close()
            return row
        else:
            conn.close()
            return 0
    except:
        conn.close()
        return -1

def get_blockchain_len():
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM blocks ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            conn.close()
            return row[0]
        else:
            conn.close()
            return 0
    except:
        conn.close()
        return -1

def get_work_user_data(user_iden, miner_name):
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM works WHERE user_iden = ? and minerName = ?", (str(user_iden), str(miner_name),))
        row = cur.fetchone()
        if row:
            conn.close()
            return row
        else:
            conn.close()
            return 0
    except:
        conn.close()
        return -1

def get_stat_new_coins():
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        cur.execute("SELECT data FROM stats WHERE name = 'new_coins'")
        row = cur.fetchone()
        if row:
            conn.close()
            return row[0]
        else:
            conn.close()
            return 0
    except:
        conn.close()
        return -1

def get_user_miners(user_iden):
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM works WHERE user_iden = ?", (str(user_iden),))
        rows = cur.fetchall()
        if rows:
            conn.close()
            return rows
        else:
            conn.close()
            return 0
    except:
        conn.close()
        return -1

def update_work_user_data(user_iden, miner_name, level=-2, success_works=-2, time_start=-2, num=-2, salt=-2, hash=-2, complexity=-2, bad_works=-2, hashrate=-2):
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        if level != -2:
            cur.execute("UPDATE works SET level = ? WHERE user_iden = ? and minerName = ?", (level, str(user_iden), str(miner_name),))
        if success_works != -2:
            cur.execute("UPDATE works SET success_works = ? WHERE user_iden = ? and minerName = ?", (success_works, str(user_iden), str(miner_name),))
        if time_start != -2:
            cur.execute("UPDATE works SET time_start = ? WHERE user_iden = ? and minerName = ?", (time_start, str(user_iden), str(miner_name),))
        if num != -2:
            cur.execute("UPDATE works SET num = ? WHERE user_iden = ? and minerName = ?", (num, str(user_iden), str(miner_name),))
        if salt != -2:
            cur.execute("UPDATE works SET salt = ? WHERE user_iden = ? and minerName = ?", (salt, str(user_iden), str(miner_name),))
        if hash != -2:
            cur.execute("UPDATE works SET hash = ? WHERE user_iden = ? and minerName = ?", (hash, str(user_iden), str(miner_name),))
        if complexity != -2:
            cur.execute("UPDATE works SET complexity = ? WHERE user_iden = ? and minerName = ?", (complexity, str(user_iden), str(miner_name),))
        if bad_works != -2:
            cur.execute("UPDATE works SET bad_works = ? WHERE user_iden = ? and minerName = ?", (bad_works, str(user_iden), str(miner_name),))
        if hashrate != -2:
            cur.execute("UPDATE works SET hashrate = ? WHERE user_iden = ? and minerName = ?", (hashrate, str(user_iden), str(miner_name),))
        conn.commit()
        conn.close()
        return 1
    except:
        conn.close()
        return -1

def update_config_data(PEER_NODES = -1, expected_sharetime = -1, complexity = -1, max_coins = -1,
                    REWARD_CENTER_NODE_PRIVATE_KEY = -1, REWARD_CENTER_NODE_PUBLIC_KEY = -1, start_hour = -1,
                    target = -1, new_block = -1):
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        if PEER_NODES != -1:
            cur.execute("UPDATE config SET data = ? WHERE name = ?", (str(PEER_NODES), 'PEER_NODES',))
        if expected_sharetime != -1:
            cur.execute("UPDATE config SET data = ? WHERE name = ?", (str(expected_sharetime), 'expected_sharetime',))
        if complexity != -1:
            cur.execute("UPDATE config SET data = ? WHERE name = ?", (str(complexity), 'complexity',))
        if max_coins != -1:
            cur.execute("UPDATE config SET data = ? WHERE name = ?", (str(max_coins), 'max_coins',))
        if REWARD_CENTER_NODE_PRIVATE_KEY != -1:
            cur.execute("UPDATE config SET data = ? WHERE name = ?", (str(REWARD_CENTER_NODE_PRIVATE_KEY), 'REWARD_CENTER_NODE_PRIVATE_KEY',))
        if REWARD_CENTER_NODE_PUBLIC_KEY != -1:
            cur.execute("UPDATE config SET data = ? WHERE name = ?", (str(REWARD_CENTER_NODE_PUBLIC_KEY), 'REWARD_CENTER_NODE_PUBLIC_KEY',))
        if start_hour != -1:
            cur.execute("UPDATE config SET data = ? WHERE name = ?", (str(start_hour), 'start_hour',))
        if target != -1:
            cur.execute("UPDATE config SET data = ? WHERE name = ?", (str(target), 'target',))
        if new_block != -1:
            cur.execute("UPDATE config SET data = ? WHERE name = ?", (str(new_block), 'new_block',))
        conn.commit()
        conn.close()
        return 1
    except:
        conn.close()
        return -1

def update_stats_coin(new_stat):
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        cur.execute("UPDATE stats SET data = ? WHERE name = 'new_coins'", (str(new_stat),))
        conn.commit()
        conn.close()
        return 1
    except:
        conn.close()
        return -1

def del_pending_block(block_id):
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM blocks_wait WHERE id = ?", (block_id,))
        conn.commit()
        conn.close()
        return 1
    except:
        conn.close()
        return -1

def del_pending_transaction(transaction_time):
    conn = sqlite3.connect(database_file)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM pending_transactions WHERE timestamp_transaction = ?", (transaction_time,))
        conn.commit()
        conn.close()
        return 1
    except:
        conn.close()
        return -1