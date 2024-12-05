from Crypto.Hash import SHA256, RIPEMD160
import base58
import binascii
from dataclasses import dataclass, field
from typing import List, Optional
from decimal import Decimal, getcontext


def pubkey_to_address(pubkey: str) -> str:
    if not all(c in '0123456789abcdefABCDEF' for c in pubkey):
        raise ValueError(f"Invalid pubkey: {pubkey}. Contains non-hexadecimal characters.")

    # Step 1: SHA-256 hashing on the public key
    sha256_result = SHA256.new(bytes.fromhex(pubkey)).digest()

    # Step 2: RIPEMD-160 hashing on the result of SHA-256 using PyCryptodome
    ripemd160 = RIPEMD160.new()
    ripemd160.update(sha256_result)
    ripemd160_result = ripemd160.digest()

    # Step 3: Add version byte (0x00 for Mainnet)
    versioned_payload = b"\x00" + ripemd160_result

    # Step 4 and 5: Calculate checksum and append to the payload
    checksum = SHA256.new(SHA256.new(versioned_payload).digest()).digest()[:4]
    binary_address = versioned_payload + checksum

    # Step 6: Encode the binary address in Base58
    bitcoin_address = base58.b58encode(binary_address).decode("utf-8")
    return bitcoin_address


def script_to_p2sh_address(script: str, mainnet=True) -> str:
    script_bytes = binascii.unhexlify(script)
    sha256 = SHA256.new(script_bytes).digest()
    ripemd160 = RIPEMD160.new(sha256).digest()
    version_byte = b"\x05" if mainnet else b"\xc4"
    payload = version_byte + ripemd160
    checksum = SHA256.new(SHA256.new(payload).digest()).digest()[:4]
    return base58.b58encode(payload + checksum).decode()


def script_to_p2pkh_address(script: str, mainnet=True) -> str:
    try:
        # Check if the script is unusually long
        if len(script) > 50:  # Normal P2PKH script is 50 characters
            # Extract only the relevant part of the script
            script = script[:50]

        if not script.startswith("76a914"):  # OP_DUP OP_HASH160
            raise ValueError(f"Script does not start with P2PKH pattern: {script[:10]}...")

        pubkey_hash = script[6:46]

        if len(pubkey_hash) != 40:  # 20 bytes in hex = 40 characters
            raise ValueError(f"Invalid pubkey hash length: {pubkey_hash}")

        version_byte = b"\x00" if mainnet else b"\x6f"
        payload = version_byte + binascii.unhexlify(pubkey_hash)
        checksum = SHA256.new(SHA256.new(payload).digest()).digest()[:4]
        return base58.b58encode(payload + checksum).decode()
    except Exception as e:
        print(f"Error in script_to_p2pkh_address: {e}")
        print(f"Script (truncated): {script[:50]}...")
        return f"INVALID_P2PKH_SCRIPT_{script[:10]}"


def derive_address(script_pub_key: dict, script_pub_key_asm: str) -> str:
    script_type = script_pub_key.get("type", "")

    if "address" in script_pub_key:
        return script_pub_key["address"]

    if "addresses" in script_pub_key and script_pub_key["addresses"]:
        return script_pub_key["addresses"][0]

    hex_script = script_pub_key.get("hex", "")

    try:
        if script_type == "nulldata":
            # Handle OP_RETURN (nulldata) scripts
            asm_parts = script_pub_key_asm.split()
            if asm_parts[0] == "OP_RETURN":
                data = " ".join(asm_parts[1:])
                return f"OP_RETURN_{data[:20]}..."  # Return first 20 chars of data

        if script_type == "pubkey":
            pubkey = script_pub_key_asm.split()[0]
            return pubkey_to_address(pubkey)

        if script_type == "pubkeyhash" or (script_type == "" and hex_script.startswith("76a914")):
            return script_to_p2pkh_address(hex_script)

        if script_type == "scripthash" or (script_type == "" and hex_script.startswith("a914")):
            return script_to_p2sh_address(hex_script)

        if script_type == "multisig":
            return script_to_p2sh_address(hex_script)

        if script_type == "witness_v0_keyhash":
            return script_pub_key.get("address", "")  # Bech32 address should be provided

        if script_type == "witness_v0_scripthash":
            return script_pub_key.get("address", "")  # Bech32 address should be provided

        # Handle "cosmic ray" transactions with long, repeating OP_CHECKSIG
        if script_pub_key_asm.count("OP_CHECKSIG") > 100:
            return f"UNKNOWN_{script_pub_key_asm[:30]}"

        if script_type == "nonstandard":
            return f"NONSTANDARD_{hex_script[:20]}..."

        # fallback
        if "OP_CHECKSIG" in script_pub_key_asm:
            asm_parts = script_pub_key_asm.split()
            if len(asm_parts) == 2 and asm_parts[1] == "OP_CHECKSIG":
                # This is likely a P2PK script
                pubkey = asm_parts[0]
                return pubkey_to_address(pubkey)
            elif "OP_DUP OP_HASH160" in script_pub_key_asm and "OP_EQUALVERIFY OP_CHECKSIG" in script_pub_key_asm:
                # This is likely a P2PKH script
                return script_to_p2pkh_address(hex_script)
        elif "OP_CHECKMULTISIG" in script_pub_key_asm:
            return script_to_p2sh_address(hex_script)

        # If we've reached this point, we couldn't derive an address
        raise ValueError(f"Unable to derive address for script type: {script_type}")

    except Exception as e:
        print(f"Error in derive_address: {e}")
        print(f"Script type: {script_type}")
        print(f"Script pub key: {script_pub_key}")
        print(f"Script pub key ASM: {script_pub_key_asm[:100]}...")  # Print only the first 100 characters
        return f"UNKNOWN_{script_pub_key_asm[:30]}"


def construct_redeem_script(pubkeys, m):
    n = len(pubkeys)
    script = f"{m} " + " ".join(pubkeys) + f" {n} OP_CHECKMULTISIG"
    return script.encode("utf-8")


def hash_redeem_script(redeem_script):
    sha256 = SHA256.new(redeem_script).digest()
    ripemd160 = RIPEMD160.new(sha256).digest()
    return ripemd160


def create_p2sh_address(hashed_script, mainnet=True):
    version_byte = b"\x05" if mainnet else b"\xc4"
    payload = version_byte + hashed_script
    checksum = SHA256.new(SHA256.new(payload).digest()).digest()[:4]
    return base58.b58encode(payload + checksum).decode()


def get_tx_out_hash_table_sub_keys():
    hex_chars = "0123456789abcdef"
    return [h1 + h2 + h3 for h1 in hex_chars for h2 in hex_chars for h3 in hex_chars]


def initialize_tx_out_hash_table():
    hash_table = {}
    for sub_key in get_tx_out_hash_table_sub_keys():
        hash_table[sub_key] = {}
    return hash_table


@dataclass
class Block:
    block_height: int
    block_hash: str
    timestamp: int  # Using int to represent Unix epoch time
    previous_block_hash: str
    nonce: int
    difficulty: int
    transactions: List["Transaction"] = field(default_factory=list)


@dataclass
class Transaction:
    tx_id: str
    block_height: int
    timestamp: int  # Using int to represent Unix epoch time
    fee_satoshi: int
    vins: List["VIN"] = field(default_factory=list)
    vouts: List["VOUT"] = field(default_factory=list)
    is_coinbase: bool = False
    size: int = 0,
    vsize: int = 0,
    weight: int = 0


@dataclass
class VOUT:
    vout_id: int
    value_satoshi: int
    script_pub_key: Optional[str]
    is_spent: bool
    address: str


@dataclass
class VIN:
    tx_id: str
    vin_id: int
    vout_id: int
    script_sig: Optional[str]
    sequence: Optional[int]


getcontext().prec = 28
SATOSHI = Decimal("100000000")


def parse_block_data(block_data):
    block_height = block_data["height"]
    block_hash = block_data["hash"]
    block_previous_hash = block_data.get("previousblockhash", "")
    timestamp = int(block_data["time"])

    block = Block(
        block_height=block_height,
        block_hash=block_hash,
        timestamp=timestamp,
        previous_block_hash=block_previous_hash,
        nonce=block_data.get("nonce", 0),
        difficulty=block_data.get("difficulty", 0),
    )

    for tx_data in block_data["tx"]:
        try:
            tx_id = tx_data["txid"]
            fee = Decimal(tx_data.get("fee", 0))
            fee_satoshi = int(fee * SATOSHI)
            tx_timestamp = int(tx_data.get("time", timestamp))

            tx = Transaction(
                tx_id=tx_id,
                block_height=block_height,
                timestamp=tx_timestamp,
                fee_satoshi=fee_satoshi,
                size=tx_data.get("size", 0),
                vsize=tx_data.get("vsize", 0),
                weight=tx_data.get("weight", 0)
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
                script_pub_key = vout_data["scriptPubKey"]
                script_pub_key_asm = script_pub_key.get("asm", "")
                value_satoshi = int(Decimal(vout_data["value"]) * SATOSHI)

                address = derive_address(script_pub_key, script_pub_key_asm)

                vout = VOUT(
                    vout_id=vout_data["n"],
                    value_satoshi=value_satoshi,
                    script_pub_key=script_pub_key_asm,
                    is_spent=False,
                    address=address
                )
                tx.vouts.append(vout)

            block.transactions.append(tx)
        except Exception as e:
            print(f"Error processing transaction in block {block_height}: {e}")
            print(f"Transaction data: {tx_data}")

    return block


def check_if_block_is_valid_for_challenge(block_height: int) -> bool:
    blocks_to_avoid = [91722, 91880]
    return not block_height in blocks_to_avoid