import time
from random import random, randint

from locust import HttpUser, TaskSet, task, between, events
from neo4j import GraphDatabase
import configparser


def read_config(filename: str) -> configparser.ConfigParser:
    """Reads the database configuration from the provided filename."""
    config = configparser.ConfigParser()
    config.read(filename)
    return config


class GraphDatabaseClient:
    """Handles Neo4j/Memgraph connections and query execution."""

    def __init__(self, config: configparser.ConfigParser, blockchain: str, db_type: str):
        section = f"{blockchain}.{db_type}"
        self.blockchain = blockchain
        self.db_type = db_type
        self.url = config.get(section, 'GRAPH_DATABASE_URL')
        self.user = config.get(section, 'GRAPH_DATABASE_USER')
        self.password = config.get(section, 'GRAPH_DATABASE_PASSWORD')

        self.driver = GraphDatabase.driver(
            self.url,
            auth=(self.user, self.password),
            connection_timeout=60,
            max_connection_lifetime=60,
            max_connection_pool_size=10,
            encrypted=False
        )

    def execute_query(self, query: str):
        """Executes a Cypher query and returns the result."""
        with self.driver.session() as session:
            result = session.run(query)
            record = result.single()  # Get the first record, or None if no results
            if not record:
                print("No results found")


class UserBehavior(TaskSet):
    """Defines tasks and handles manual task selection."""

    def on_start(self):
        """Initialize database client."""
        if not hasattr(self.user, "db_client"):
            config = read_config('config.ini')
            blockchain = self.user.environment.parsed_options.blockchain
            db_type = self.user.environment.parsed_options.db_type
            self.user.db_client = GraphDatabaseClient(config, blockchain, db_type)

        # Determine which task to run based on --test-case argument
        self.selected_task = self.user.environment.parsed_options.test_case

    def _execute_task(self, query, test_name, *args):

        start_time = time.time()
        try:
            print(f"Executing test-case: {test_name} {args}")
            result = self.user.db_client.execute_query(query)
            response_time = (time.time() - start_time) * 1000
            print(f"Response time: {response_time}")
            events.request.fire(
                request_type="cypher",
                name=test_name,
                response_time=response_time,
                response_length=len(result) if result else 0,
                context=self.user,
                exception=None,
            )
        except Exception as e:
            print(f"Failed to execute cypher query: {e}")
            response_time = (time.time() - start_time) * 1000
            events.request.fire(
                request_type="cypher",
                name=test_name,
                response_time=response_time,
                response_length=0,
                context=self.user,
                exception=e,
            )

    @task
    def test_case(self):

        if self.selected_task == "test_case_get_block_750000_850000":
            block_height = randint(750000, 850000)
            query = """MATCH (t1:Transaction {block_height:%d})-[s1:SENT]->(a1:Address)
            OPTIONAL MATCH (t0)-[s0:SENT]->(a0:Address)-[s2:SENT]->(t1)
            OPTIONAL MATCH (t1)-[s3:SENT]->(a2:Address)-[s4:SENT]->(t2)
            WITH DISTINCT t1, s1, a1, t0, s0, a0, s2, s3, a2, s4, t2 
            RETURN *""" % block_height
            self._execute_task(query, self.selected_task, block_height)

        if self.selected_task == "test_case_get_block_500000_750000":
            block_height = randint(500000, 750000)
            query = """MATCH (t1:Transaction {block_height:%d})-[s1:SENT]->(a1:Address)
                   OPTIONAL MATCH (t0)-[s0:SENT]->(a0:Address)-[s2:SENT]->(t1)
                   OPTIONAL MATCH (t1)-[s3:SENT]->(a2:Address)-[s4:SENT]->(t2)
                   WITH DISTINCT t1, s1, a1, t0, s0, a0, s2, s3, a2, s4, t2 
                   RETURN *""" % block_height
            self._execute_task(query, self.selected_task, block_height)

class GraphUser(HttpUser):
    """Defines user behavior and test setup."""
    tasks = [UserBehavior]
    wait_time = between(1, 5)
    host = "http://localhost"  # Dummy host to satisfy Locust


def add_custom_arguments(parser):
    """Adds custom command-line arguments to the parser."""
    parser.add_argument(
        '--blockchain',
        type=str,
        required=True,
        help="Blockchain type (e.g., bitcoin or commune)"
    )
    parser.add_argument(
        '--db-type',
        type=str,
        required=True,
        help="Database type (e.g., neo4j or memgraph)"
    )
    parser.add_argument(
        '--test-case',
        type=str,
        default=None,
        help="Manually select a test case to run"
    )


@events.init_command_line_parser.add_listener
def on_locust_init_parser(parser):
    """Attach custom argument parser to Locust's command-line parser."""
    add_custom_arguments(parser)