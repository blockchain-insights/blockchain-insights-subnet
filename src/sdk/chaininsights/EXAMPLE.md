Here’s a properly formatted Markdown file with clear code block formatting for the examples:

---

### `sdk/examples/examples.md`

```markdown
# SDK Usage Examples

## Installation
```bash
pip install requests pydantic
```

## Configuration
```python
from sdk.config import Config

config = Config(base_url="https://api.example.com", api_key="your-api-key")
```

## Funds Flow API
### Example: Get Block
```python
from sdk.api.funds_flow import FundsFlowAPI

api = FundsFlowAPI(config)
block_data = api.get_block("mainnet", block_height=123456)
print(block_data)
```

### Example: Get Transaction by Tx ID
```python
transaction_data = api.get_transaction_by_tx_id("mainnet", tx_id="0x123abc")
print(transaction_data)
```

### Example: Get Address Transactions
```python
address_transactions = api.get_address_transactions("mainnet", address="0x123abc")
print(address_transactions)
```

## Balance Tracking API
### Example: Get Balance Deltas
```python
from sdk.api.balance_tracking import BalanceTrackingAPI

api = BalanceTrackingAPI(config)
deltas = api.get_balance_deltas("mainnet", addresses=["address1", "address2"], page=1, page_size=50)
print(deltas)
```

### Example: Get Balances
```python
balances = api.get_balances("mainnet", addresses=["address1", "address2"])
print(balances)
```

### Example: Get Timestamps
```python
timestamps = api.get_timestamps("mainnet", start_date="2024-01-01", end_date="2024-01-31")
print(timestamps)
```

## Miners API
### Example: Get Metadata
```python
from sdk.api.miners import MinersAPI

api = MinersAPI(config)
metadata = api.get_metadata("mainnet")
print(metadata)
```

### Example: Get Receipts
```python
receipts = api.get_receipts(miner_key="miner_key_123", page=1, page_size=10)
print(receipts)
```

### Example: Sync Receipts
```python
sync_data = api.sync_receipts(
    validator_key="validator_key_123",
    validator_signature="signature_abc",
    timestamp="2024-01-01T00:00:00Z",
    page=1,
    page_size=50
)
print(sync_data)
```
```

The file is now fully formatted for Markdown with proper code block usage and readability.

Hotkeys:  
- 📄 **Z**: Export as files  
- 📘 **S**: Explain step-by-step  