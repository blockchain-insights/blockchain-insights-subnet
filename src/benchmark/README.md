### How to Run Locust

1. **Navigate to the `src/benchmark` directory:**
   ```sh
   cd src/benchmark
   ```

2. **Install the required dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Run Locust with the specified parameters:**
   ```sh
   locust -f locustfile.py --blockchain bitcoin --db-type neo4j --test-case test_case_get_block_750000_850000
   ```

### Explanation of Parameters

- `--blockchain`: Specifies the blockchain type (e.g., `bitcoin` or `commune`).
- `--db-type`: Specifies the database type (e.g., `neo4j` or `memgraph`).
- `--test-case`: Manually selects a test case to run (e.g., `test_case_get_block_750000_850000`).

### Example Command

To run a test case for the Bitcoin blockchain using Neo4j and querying blocks between heights 750,000 and 850,000, use the following command:
```sh
locust -f locustfile.py --blockchain bitcoin --db-type neo4j --test-case test_case_get_block_750000_850000
```