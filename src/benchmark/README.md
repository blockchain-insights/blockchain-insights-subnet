cd src/benchmark
pip install -r requirements.txt
locust -f locustfile.py --blockchain bitcoin --db-type neo4j --test-case test_case_get_block_750000_850000
