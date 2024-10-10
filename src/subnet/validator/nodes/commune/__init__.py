from threading import Event

from Crypto.Hash import SHA256
from loguru import logger
from substrateinterface import SubstrateInterface
from src.subnet.protocol import Challenge, MODEL_KIND_FUNDS_FLOW, MODEL_KIND_BALANCE_TRACKING
from src.subnet.validator._config import ValidatorSettings
from src.subnet.validator.nodes.abstract_node import Node
from src.subnet.validator.nodes.random_block import select_block


def extract_receiver(extrinsic):
    call_module = extrinsic['call']['call_module']
    call_function = extrinsic['call']['call_function']
    call_args = extrinsic.get('call_args', [])
    if call_module == "Balances" and call_function == "transfer":
        for arg in call_args:
            if arg['name'] == 'dest':
                return arg['value']
    elif call_module == "SubspaceModule" and call_function == "set_weights":
        return ""
    return ""


def calculate_checksum(tx_hash, block_hash, sender, receiver):
    binary_address = tx_hash + block_hash + sender + receiver
    encoded_address = binary_address.encode('utf-8')
    sha256_hash = SHA256.new(encoded_address).hexdigest()
    return sha256_hash


class CommuneNode(Node):
    def __init__(self, settings: ValidatorSettings):
        super().__init__()
        self.setting = settings
        self.substrate = SubstrateInterface(
            url=settings.COMMUNE_NODE_RPC,
            ss58_format=0,
        )

    def get_current_block_height(self):
        header = self.substrate.get_block_header()
        return header['header']['number']

    def get_block_by_height(self, block_height):
        try:
            block = self.substrate.get_block(block_number=block_height)
            return block
        except Exception as e:
            logger.error(f"Error fetching block at height {block_height}: {e}", block_height=block_height, error=e)
            return None

    def create_funds_flow_challenge(self, end_block: int, terminate_event: Event):
        if terminate_event.is_set():
            return None, None

        block_number = select_block(0, end_block)
        block = self.substrate.get_block(block_number=block_number)

        block_hash = block['header']['hash']

        for idx, extrinsic in enumerate(block['extrinsics']):
            extrinsic_data = extrinsic.value
            is_inherent = 'address' not in extrinsic_data
            if is_inherent:
                continue
            tx_hash = extrinsic_data.get('extrinsic_hash', 'Unknown Hash')
            sender = extrinsic_data.get('address', "None")
            receiver = extract_receiver(extrinsic_data)
            checksum = calculate_checksum(tx_hash, block_hash, sender, receiver)

            challenge = Challenge(
                model_kind=MODEL_KIND_FUNDS_FLOW,
                in_total_amount=None,
                out_total_amount=None,
                tx_id_last_6_chars=tx_hash[-6:],
                checksum=checksum,
                block_height=block_number,
                output=None
            )
            return challenge, tx_hash

        return None, None

    def create_balance_tracking_challenge(self, block_height: int, terminate_event: Event):
        if terminate_event.is_set():
            return None, None

        logger.info("Creating balance tracking challenge", block_height=block_height)

        block = self.get_block_by_height(block_height)
        if not block:
            logger.error(f"Failed to retrieve block at height {block_height}", block_height=block_height)
            return None, 0

        extrinsics = block['extrinsics']

        balance_changes_by_address = {}
        changed_addresses = []

        for extrinsic in extrinsics:
            extrinsic_data = extrinsic.value
            is_inherent = 'address' not in extrinsic_data
            if is_inherent:
                continue

            sender = extrinsic_data.get('address', "None")
            receiver = extract_receiver(extrinsic_data)

            if not sender or not receiver:
                continue

            if sender not in balance_changes_by_address:
                balance_changes_by_address[sender] = 0
                changed_addresses.append(sender)
            if receiver not in balance_changes_by_address:
                balance_changes_by_address[receiver] = 0
                changed_addresses.append(receiver)

            call_args = extrinsic_data.get('call_args', [])
            amount = 0
            for arg in call_args:
                if arg['name'] == 'value' or arg['name'] == 'amount':
                    amount = int(arg['value'])
                    break

            balance_changes_by_address[sender] -= amount
            balance_changes_by_address[receiver] += amount

        total_balance_change = sum(balance_changes_by_address.values())

        challenge = Challenge(
            model_kind=MODEL_KIND_BALANCE_TRACKING,
            in_total_amount=None,
            out_total_amount=None,
            tx_id_last_6_chars=None,
            checksum=None,
            block_height=block_height,
            output=balance_changes_by_address  # Assuming you want to store the changes
        )

        return challenge, total_balance_change
