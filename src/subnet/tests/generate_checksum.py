from substrateinterface import SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException
from Crypto.Hash import SHA256

def calculate_checksum(tx_hash, block_hash, sender, receiver):
    """
    Calculate the SHA256 checksum based on the transaction details.
    """
    # Concatenate the required fields
    binary_address = tx_hash + block_hash + sender + receiver
    # Encode the concatenated string to UTF-8
    encoded_address = binary_address.encode('utf-8')
    # Compute SHA256 hash
    sha256_hash = SHA256.new(encoded_address).hexdigest()
    return sha256_hash

def extract_receiver(extrinsic):
    """
    Extract the 'to' address from the extrinsic based on its type.
    If not applicable, return "Not Applicable".
    """
    call_module = extrinsic['call']['call_module']
    call_function = extrinsic['call']['call_function']
    call_args = extrinsic.get('call_args', [])

    # Example for handling Balances.transfer
    if call_module == "Balances" and call_function == "transfer":
        for arg in call_args:
            if arg['name'] == 'dest':
                return arg['value']
    elif call_module == "SubspaceModule" and call_function == "set_weights":
        # Assuming 'set_weights' doesn't have a direct 'to' address
        return ""
    # Add more conditions here for different extrinsic types as needed

    return ""

def get_block_transactions_checksum(substrate, block_number):
    """
    Retrieve a specific block and calculate checksum for each transaction.
    """
    try:
        # Fetch block by number
        block = substrate.get_block(block_number=block_number)
    except SubstrateRequestException as e:
        print(f"Error fetching block {block_number}: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return

    # Access the block hash directly as a string
    block_hash = block['header']['hash']

    print(f"Processing Block #{block_number} with Hash: {block_hash}\n")

    # Iterate through extrinsics (transactions) in the block
    for idx, extrinsic in enumerate(block['extrinsics']):
        extrinsic_data = extrinsic.value  # Access the underlying dictionary

        # Determine if the extrinsic is inherent (like timestamp updates)
        # Inherent extrinsics typically do not have an 'address' or 'signature'
        is_inherent = 'address' not in extrinsic_data

        if is_inherent:
            # Skip inherent extrinsics
            continue

        tx_hash = extrinsic_data.get('extrinsic_hash', 'Unknown Hash')
        sender = extrinsic_data.get('address', "None")

        # Extract 'to' using the helper function
        receiver = extract_receiver(extrinsic_data)

        checksum = calculate_checksum(tx_hash, block_hash, sender, receiver)

        print(f"Transaction {idx + 1}:")
        print(f"  Hash       : {tx_hash}")
        print(f"  Block Hash : {block_hash}")
        print(f"  From       : {sender}")
        print(f"  To         : {receiver}")
        print(f"  Checksum   : {checksum}\n")

def main():
    try:
        # Connect to the Commune AI node
        substrate = SubstrateInterface(
            url="wss://comai.chain-insights.io",  # Commune AI RPC endpoint
            ss58_format=0,  # Replace with Commune AI's SS58 format if different
            #type_registry_preset='polkadot'  # Replace with Commune AI's preset if available
        )
        print("Successfully connected to Commune AI node.")
    except SubstrateRequestException as e:
        print(f"Error connecting to the node: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred while connecting: {e}")
        return

    # Specify the block number you want to retrieve
    block_number = 1234567  # Replace with your target block number

    get_block_transactions_checksum(substrate, block_number)

if __name__ == "__main__":
    main()
