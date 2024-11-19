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
            return result.single()[0]


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

    def _execute_task(self, query, test_name):
        """Executes the specified query."""
        try:
            result = self.user.db_client.execute_query(query)
            print(f"{test_name} Result: {result}")
        except Exception as e:
            print(f"{test_name} Failed: {e}")

    @task
    def test_case_return_1(self):
        """Executes RETURN 1."""
        if self.selected_task == "test_case_return_1":
            self._execute_task("RETURN 1", "Test Case: RETURN 1")

    @task
    def test_case_node_count(self):
        """Executes MATCH (n) RETURN COUNT(n)."""
        if self.selected_task == "test_case_node_count":
            self._execute_task("MATCH (n) RETURN COUNT(n)", "Test Case: Node Count")

    @task
    def test_case_relationship_count(self):
        """Executes MATCH (n)-[r]->(m) RETURN COUNT(r)."""
        if self.selected_task == "test_case_relationship_count":
            self._execute_task("MATCH (n)-[r]->(m) RETURN COUNT(r)", "Test Case: Relationship Count")


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
        help="Manually select a test case to run (e.g., test_case_return_1)"
    )


@events.init_command_line_parser.add_listener
def on_locust_init_parser(parser):
    """Attach custom argument parser to Locust's command-line parser."""
    add_custom_arguments(parser)
