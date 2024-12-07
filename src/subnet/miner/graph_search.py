from loguru import logger
from neo4j import GraphDatabase, READ_ACCESS
from neo4j.exceptions import Neo4jError


class GraphSearch:

    def __init__(self, graph_database_url: str,  graph_database_user: str, graph_database_password: str):
        self.driver = GraphDatabase.driver(
            graph_database_url,
            auth=(graph_database_user, graph_database_password),
            connection_timeout=60,
            max_connection_lifetime=60,
            max_connection_pool_size=128,
            fetch_size=1000,
            encrypted=False,
        )

    def execute_query(self, query: str):
        with self.driver.session(default_access_mode=READ_ACCESS) as session:
            try:
                result = session.run(query)

                # If no results are found, return an empty list
                if not result:
                    return []

                results_data = []

                # Iterate through the query result
                for record in result:
                    processed_record = {}

                    # Iterate over the key-value pairs in each record
                    for key in record.keys():
                        value = record[key]

                        if value is None:
                            # Handle null values gracefully
                            processed_record[key] = None

                        # Process nodes
                        elif hasattr(value, "id") and hasattr(value, "labels"):
                            processed_record[key] = {
                                "id": value.id,
                                "labels": list(value.labels),
                                "properties": dict(value),
                            }

                        # Process relationships
                        elif hasattr(value, "id") and hasattr(value, "type"):
                            processed_record[key] = {
                                "id": value.id,
                                "start": value.start_node.id,
                                "end": value.end_node.id,
                                "label": value.type,
                                "properties": dict(value),
                            }

                        # Handle primitive or other values
                        else:
                            processed_record[key] = value

                    results_data.append(processed_record)

                return results_data

            except Neo4jError as e:
                logger.error("Failed to execute query", error=e, query=query)
                raise ValueError("Failed to execute query") from e
