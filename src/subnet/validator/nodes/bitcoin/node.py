from decimal import Decimal
from loguru import logger
from src.subnet.protocol.llm_engine import Challenge, MODEL_TYPE_FUNDS_FLOW, MODEL_TYPE_BALANCE_TRACKING
from .node_utils import initialize_tx_out_hash_table, get_tx_out_hash_table_sub_keys, construct_redeem_script, \
    hash_redeem_script, create_p2sh_address, pubkey_to_address, check_if_block_is_valid_for_challenge, parse_block_data, \
    Transaction, VIN, SATOSHI, VOUT
from bitcoinrpc.authproxy import AuthServiceProxy
import pickle
import time
import os
import random
from ..abstract_node import Node
from ..random_block import select_block


class BitcoinNode(Node):
    def __init__(self, node_rpc_url: str = None):
        self.tx_out_hash_table = initialize_tx_out_hash_table()
        pickle_files_env = os.environ.get("BITCOIN_V2_TX_OUT_HASHMAP_PICKLES")
        pickle_files = []
        if pickle_files_env:
            pickle_files = pickle_files_env.split(',')

        for pickle_file in pickle_files:
            if pickle_file:
                self.load_tx_out_hash_table(pickle_file)
                
        if node_rpc_url is None:
            self.node_rpc_url = (
                os.environ.get("BITCOIN_NODE_RPC_URL")
                or "http://bitcoinrpc:rpcpassword@127.0.0.1:8332"
            )
        else:
            self.node_rpc_url = node_rpc_url

    def load_tx_out_hash_table(self, pickle_path: str, reset: bool = False):
        logger.info(f"Loading tx_out hash table from pickle file", pickle_path=pickle_path)
        with open(pickle_path, 'rb') as file:
            start_time = time.time()
            hash_table = pickle.load(file)
            if reset:
                self.tx_out_hash_table = hash_table
            else:
                sub_keys = get_tx_out_hash_table_sub_keys()
                for sub_key in sub_keys:
                    self.tx_out_hash_table[sub_key].update(hash_table[sub_key])
            end_time = time.time()
            logger.info(f"Successfully loaded tx_out hash table from pickle file", pickle_path=pickle_path, time_taken=end_time - start_time)

    def get_current_block_height(self):
        rpc_connection = AuthServiceProxy(self.node_rpc_url)
        try:
            return rpc_connection.getblockcount()
        except Exception as e:
            logger.error(f"RPC Provider with Error")
        finally:
            rpc_connection._AuthServiceProxy__conn.close()  # Close the connection

    def get_block_by_height(self, block_height):
        rpc_connection = AuthServiceProxy(self.node_rpc_url)
        try:
            block_hash = rpc_connection.getblockhash(block_height)
            return rpc_connection.getblock(block_hash, 2)
        except Exception as e:
            logger.error(f"RPC Provider with Error")
        finally:
            rpc_connection._AuthServiceProxy__conn.close()  # Close the connection

    def get_transaction_by_hash(self, tx_hash):
        logger.error(f"get_transaction_by_hash not implemented for BitcoinNode")
        raise NotImplementedError()
    
    def get_address_and_amount_by_txn_id_and_vout_id(self, txn_id: str, vout_id: str):
        # call rpc if not in hash table
        if (txn_id, vout_id) not in self.tx_out_hash_table[txn_id[:3]]:
            # indexlogger.info(f"No entry is found in tx_out hash table: (tx_id, vout_id): ({txn_id}, {vout_id})")
            rpc_connection = AuthServiceProxy(self.node_rpc_url)
            try:
                txn_data = rpc_connection.getrawtransaction(str(txn_id), 1)
                vout = next((x for x in txn_data['vout'] if str(x['n']) == vout_id), None)
                amount = int(vout['value'] * 100000000)
                address = vout["scriptPubKey"].get("address", "")
                script_pub_key_asm = vout["scriptPubKey"].get("asm", "")
                if not address:
                    addresses = vout["scriptPubKey"].get("addresses", [])
                    if addresses:
                        address = addresses[0]
                    elif "OP_CHECKSIG" in script_pub_key_asm:
                        pubkey = script_pub_key_asm.split()[0]
                        address = pubkey_to_address(pubkey)
                    elif "OP_CHECKMULTISIG" in script_pub_key_asm:
                        pubkeys = script_pub_key_asm.split()[1:-2]
                        m = int(script_pub_key_asm.split()[0])
                        redeem_script = construct_redeem_script(pubkeys, m)
                        hashed_script = hash_redeem_script(redeem_script)
                        address = create_p2sh_address(hashed_script)
                    else:
                        address = f"unknown-{txn_id}"
                return address, amount
            except Exception as e:
                address = f"unknown-{txn_id}"
                return address, 0
            finally:
                rpc_connection._AuthServiceProxy__conn.close()  # Close the connection
        else: # get from hash table if exists
            address, amount = self.tx_out_hash_table[txn_id[:3]][(txn_id, vout_id)]
            return address, int(amount)

    def create_funds_flow_challenge(self, start_block_height, last_block_height):
        num_retries = 10 # to prevent infinite loop
        is_valid_block = False
        while num_retries and not is_valid_block:
            block_to_check = select_block(start_block_height, last_block_height)
            is_valid_block = check_if_block_is_valid_for_challenge(block_to_check)
            num_retries -= 1

        # if failed ot find valid block, return invalid response
        if not num_retries:
            raise Exception(
                f"Failed to create a valid challenge."
            )
        
        block_data = self.get_block_by_height(block_to_check)
        num_transactions = len(block_data["tx"])

        out_total_amount = 0
        while out_total_amount == 0:
            selected_txn = block_data["tx"][random.randint(0, num_transactions - 1)]
            txn_id = selected_txn.get('txid')
        
            txn_data = self.get_txn_data_by_id(txn_id)
            tx = self.create_in_memory_txn(txn_data)

            *_, in_total_amount, out_total_amount = self.process_in_memory_txn_for_indexing(tx)
            
        challenge = Challenge(kind=MODEL_TYPE_FUNDS_FLOW,
                              in_total_amount=in_total_amount,
                              out_total_amount=out_total_amount,
                              tx_id_last_6_chars=txn_id[-6:])
        return challenge, txn_id

    def validate_funds_flow_challenge_response_output(self, challenge: Challenge, response_output):
        if response_output[-6:] != challenge.tx_id_last_6_chars:
            return False
        
        txn_data = self.get_txn_data_by_id(response_output)
        if txn_data is None:
            return False
        
        tx = self.create_in_memory_txn(txn_data)

        *_, in_total_amount, out_total_amount = self.process_in_memory_txn_for_indexing(tx)
        return challenge.in_total_amount == in_total_amount and challenge.out_total_amount == out_total_amount

    def create_balance_tracking_challenge(self, block_height):

        logger.info(f"Creating balance tracking challenge", block_height=block_height)

        block = self.get_block_by_height(block_height)
        block_data = parse_block_data(block)
        transactions = block_data.transactions

        balance_changes_by_address = {}
        changed_addresses = []

        for tx in transactions:
            in_amount_by_address, out_amount_by_address, input_addresses, output_addresses, in_total_amount, out_total_amount = self.process_in_memory_txn_for_indexing(
                tx)

            for address in input_addresses:
                if not address in balance_changes_by_address:
                    balance_changes_by_address[address] = 0
                    changed_addresses.append(address)
                balance_changes_by_address[address] -= in_amount_by_address[address]

            for address in output_addresses:
                if not address in balance_changes_by_address:
                    balance_changes_by_address[address] = 0
                    changed_addresses.append(address)
                balance_changes_by_address[address] += out_amount_by_address[address]

        challenge = Challenge(kind=MODEL_TYPE_BALANCE_TRACKING, block_height=block_height)
        total_balance_change = sum(balance_changes_by_address.values())
        logger.info(f"Created balance tracking challenge", block_height=block_height)

        return challenge, total_balance_change


    def get_txn_data_by_id(self, txn_id: str):
        try:
            rpc_connection = AuthServiceProxy(self.node_rpc_url)
            return rpc_connection.getrawtransaction(txn_id, 1)
        except Exception as e:
            logger.error(f"Failed to get transaction data by id", error={'exception_type': e.__class__.__name__, 'exception_message': str(e), 'exception_args': e.args})
            return None

    def create_in_memory_txn(self, tx_data):
        tx = Transaction(
            tx_id=tx_data.get('txid'),
            block_height=0,
            timestamp=0,
            fee_satoshi=0
        )
        
        for vin_data in tx_data["vin"]:
            vin = VIN(
                tx_id=vin_data.get("txid", 0),
                vin_id=vin_data.get("sequence", 0),
                vout_id=vin_data.get("vout", 0),
                script_sig=vin_data.get("scriptSig", {}).get("asm", ""),
                sequence=vin_data.get("sequence", 0),
            )
            tx.vins.append(vin)
            tx.is_coinbase = "coinbase" in vin_data
            
        for vout_data in tx_data["vout"]:
            script_type = vout_data["scriptPubKey"].get("type", "")
            if "nonstandard" in script_type or script_type == "nulldata":
                continue

            value_satoshi = int(Decimal(vout_data["value"]) * SATOSHI)
            n = vout_data["n"]
            script_pub_key_asm = vout_data["scriptPubKey"].get("asm", "")

            address = vout_data["scriptPubKey"].get("address", "")
            if not address:
                addresses = vout_data["scriptPubKey"].get("addresses", [])
                if addresses:
                    address = addresses[0]
                elif "OP_CHECKSIG" in script_pub_key_asm:
                    pubkey = script_pub_key_asm.split()[0]
                    address = pubkey_to_address(pubkey)
                elif "OP_CHECKMULTISIG" in script_pub_key_asm:
                    pubkeys = script_pub_key_asm.split()[1:-2]
                    m = int(script_pub_key_asm.split()[0])
                    redeem_script = construct_redeem_script(pubkeys, m)
                    hashed_script = hash_redeem_script(redeem_script)
                    address = create_p2sh_address(hashed_script)
                else:
                    raise Exception(
                        f"Unknown address type: {vout_data['scriptPubKey']}"
                    )

            vout = VOUT(
                vout_id=n,
                value_satoshi=value_satoshi,
                script_pub_key=script_pub_key_asm,
                is_spent=False,
                address=address,
            )
            tx.vouts.append(vout)
            
        return tx
    
    def process_in_memory_txn_for_indexing(self, tx):
        input_amounts = {} # input amounts by address in satoshi
        output_amounts = {} # output amounts by address in satoshi

        for vin in tx.vins:
            if vin.tx_id == 0:
                continue
            address, amount = self.get_address_and_amount_by_txn_id_and_vout_id(vin.tx_id, str(vin.vout_id))
            input_amounts[address] = input_amounts.get(address, 0) + amount

        for vout in tx.vouts:
            amount = vout.value_satoshi
            address = vout.address or f"unknown-{tx.tx_id}"
            output_amounts[address] = output_amounts.get(address, 0) + amount


        for address in input_amounts:
            if address in output_amounts:
                diff = input_amounts[address] - output_amounts[address]
                if diff > 0:
                    input_amounts[address] = diff
                    output_amounts[address] = 0
                elif diff < 0:
                    output_amounts[address] = -diff
                    input_amounts[address] = 0
                else:
                    input_amounts[address] = 0
                    output_amounts[address] = 0

        input_addresses = [address for address, amount in input_amounts.items() if amount != 0]
        output_addresses = [address for address, amount in output_amounts.items() if amount != 0]
                    
        in_total_amount = sum(input_amounts.values())
        out_total_amount = sum(output_amounts.values())

        return input_amounts, output_amounts, input_addresses, output_addresses, in_total_amount, out_total_amount

    def get_random_vin_or_vout(self, block_height):
        logger.info(f"Fetching random vin or vout from block {block_height}")

        block_data = self.get_block_by_height(block_height)
        transactions = block_data.get('tx', [])

        if not transactions:
            raise Exception(f"No transactions found in block {block_height}")

        # Ensure that transactions are list items, not single integers
        if not isinstance(transactions, list):
            raise Exception(f"Expected a list of transactions but got {type(transactions)}")

        # Select a random transaction from the block
        selected_txn = random.choice(transactions)

        # Ensure the selected transaction has a 'txid' key
        if not isinstance(selected_txn, dict) or 'txid' not in selected_txn:
            raise Exception(f"Invalid transaction data: {selected_txn}")

        txn_data = self.get_txn_data_by_id(selected_txn['txid'])

        if txn_data is None:
            raise Exception(f"Transaction data not found for txid: {selected_txn['txid']}")

        tx = self.create_in_memory_txn(txn_data)

        # Collect all vins and vouts
        all_vins = getattr(tx, 'vins', [])
        all_vouts = getattr(tx, 'vouts', [])

        if not all_vins and not all_vouts:
            raise Exception(f"No vins or vouts found in transaction {selected_txn['txid']}")

        # Randomly select between vins and vouts, but prioritize VOUTs if VINs are problematic
        selected_item = None

        if all_vouts:
            selected_item = random.choice(all_vouts)
            return {"type": "vout", "address": selected_item.address, "block_data": block_data}
        elif all_vins:
            selected_item = random.choice(all_vins)
            try:
                # Attempt to retrieve the address from the previous VOUT
                prev_txn = self.get_txn_data_by_id(selected_item.tx_id)
                if prev_txn:
                    prev_vout = prev_txn['vout'][selected_item.vout_id]
                    address = prev_vout.get('scriptPubKey', {}).get('addresses', [None])[0]
                    if address:
                        return {"type": "vin", "address": address, "block_data": block_data}
                    else:
                        logger.warning(f"Address not found for VIN in transaction {selected_item.tx_id}")
                        raise Exception(f"Address not found for VIN in transaction {selected_item.tx_id}")
                else:
                    logger.warning(f"Previous transaction not found for VIN {selected_item.tx_id}")
                    raise Exception(f"Previous transaction not found for VIN {selected_item.tx_id}")
            except Exception as e:
                logger.error(f"Error retrieving address for VIN: {e}")
                raise
        else:
            raise Exception(f"No valid VIN or VOUT found for transaction {selected_txn['txid']}")
