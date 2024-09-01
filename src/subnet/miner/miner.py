import signal
import traceback
from communex._common import get_node_url
from communex.client import CommuneClient
from communex.module import Module, endpoint
from communex.module._rate_limiters.limiters import IpLimiterMiddleware, IpLimiterParams
from keylimiter import TokenBucketLimiter
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from src.subnet.miner._config import MinerSettings, load_environment
from src.subnet.miner.blockchain import GraphSearchFactory
from src.subnet.miner.blockchain import BalanceSearchFactory
from src.subnet.miner.blockchain import GraphSummaryTransformerFactory
from src.subnet.miner.blockchain import GraphTransformerFactory, ChartTransformerFactory, TabularTransformerFactory
from src.subnet.miner.llm.factory import LLMFactory
from src.subnet.protocol.llm_engine import LLM_UNKNOWN_ERROR, LLM_ERROR_MESSAGES, \
    LLM_ERROR_MODIFICATION_NOT_ALLOWED, LLM_ERROR_INVALID_SEARCH_PROMPT, MODEL_TYPE_FUNDS_FLOW, \
    MODEL_TYPE_BALANCE_TRACKING, Challenge, LlmMessage, LlmMessageList, LlmMessageOutputList, \
    LlmMessageOutput
from src.subnet.validator.database import db_manager
import time

class Miner(Module):

    def __init__(self, settings: MinerSettings):
        super().__init__()
        self.settings = settings
        self.llm = LLMFactory().create_llm(self.settings)
        self.graph_transformer_factory = GraphTransformerFactory()
        self.chart_transformer_factory = ChartTransformerFactory()
        self.tabular_transformer_factory = TabularTransformerFactory()
        self.graph_search_factory = GraphSearchFactory()
        self.balance_search_factory = BalanceSearchFactory()
        self.graph_summary_transformer_factory = GraphSummaryTransformerFactory()

    @endpoint
    async def discovery(self) -> dict:
        """
        Returns the network of the miner
        Returns:
            dict: The network of the miner
            {
                "network": "bitcoin"
            }
        """

        return {
            "network": self.settings.NETWORK
        }

    @endpoint
    async def challenge(self, challenge: Challenge) -> Challenge:
        """
        Solves the challenge and returns the output
        Args:
            challenge: {
                "kind": "funds_flow",
                "in_total_amount": 0.0,
                "out_total_amount": 0.0,
                "tx_id_last_6_chars": "string",
                "checksum": "string",
                "block_height": 0
            }

        Returns:
            dict: The output of the challenge
            {
                "output": "tx_id|sum"
            }

        """

        challenge = Challenge(**challenge)

        if challenge.kind == MODEL_TYPE_FUNDS_FLOW:
            search = GraphSearchFactory().create_graph_search(self.settings)
            tx_id = search.solve_challenge(
                in_total_amount=challenge.in_total_amount,
                out_total_amount=challenge.out_total_amount,
                tx_id_last_6_chars=challenge.tx_id_last_6_chars
            )

            challenge.output = {'tx_id': tx_id}
            return challenge
        else:
            search = BalanceSearchFactory().create_balance_search(self.settings.NETWORK)
            challenge.output = {
                'balance': await search.solve_challenge([challenge.block_height])
            }
            return challenge

    @endpoint
    def cross_check_query(self, request: dict) -> dict:
        return {
            "error": "Not implemented"
        }

    @endpoint
    async def llm_query(self, llm_messages_list: LlmMessageList) -> LlmMessageOutputList:
        """
        Args:
            llm_messages_list:
            {
                "llm_messages": [
                    {
                        "type": 0,
                        "content": "string"
                    }
                ]
            }

        Returns:
            {
                "output": [
                    {
                        "type": "graph",
                        "result": [
                            {
                                "type": "node",
                                "label": "string",
                                "properties": {
                                    "key": "value"
                                }
                            }
                        ]
                    },
                    {
                        "type": "text",
                        "result": "string"
                    }
                ],

        """

        llm_messages_list = LlmMessageList(**llm_messages_list)
        logger.debug(f"Received miner llm query: {llm_messages_list}")
        start_time = time.time()

        try:
            model_type = self.llm.determine_model_type(llm_messages_list.messages, self.settings.NETWORK)
            logger.debug(f"Determined model type: {model_type}")

            if model_type == 'funds_flow':
                output = await self._handle_funds_flow_query(llm_messages_list)
            elif model_type == 'balance_tracking':
                output = await self._handle_balance_tracking_query(llm_messages_list)
            else:
                output = LlmMessageOutputList(outputs=[LlmMessageOutput(error='Unsupported model type')])

        except Exception as e:
            logger.error(traceback.format_exc())
            error_code = e.args[0] if len(e.args) > 0 and isinstance(e.args[0], int) else LLM_UNKNOWN_ERROR
            output = LlmMessageOutputList(outputs=[LlmMessageOutput(error=error_code, result=LLM_ERROR_MESSAGES.get(error_code, 'An error occurred'))])

        logger.debug(f"Serving miner llm query output: {output} (Total time taken: {time.time() - start_time} seconds)")

        return output

    async def _handle_funds_flow_query(self, llm_messages_list: LlmMessageList) -> LlmMessageOutputList:
        try:
            graph_search = self.graph_search_factory.create_graph_search(self.settings)
            query_start_time = time.time()

            query = self.llm.build_cypher_query_from_messages(llm_messages_list.messages, self.settings.NETWORK)
            query = query.strip('`')
            logger.debug(f"Generated Cypher query: {query} (Time taken: {time.time() - query_start_time} seconds)")

            if query == 'modification_error':
                error_code = LLM_ERROR_MODIFICATION_NOT_ALLOWED
                error_message = LLM_ERROR_MESSAGES[error_code]
                logger.error(f"Error {error_code}: {error_message}")
                return LlmMessageOutputList(outputs=[LlmMessageOutput(type="error", error=error_code, result=error_message)])

            if query == 'invalid_prompt_error':
                error_code = LLM_ERROR_INVALID_SEARCH_PROMPT
                error_message = LLM_ERROR_MESSAGES[error_code]
                logger.error(f"Error {error_code}: {error_message}")
                return LlmMessageOutputList(outputs=[LlmMessageOutput(type="error", error=error_code, result=error_message)])

            execute_query_start_time = time.time()
            result = graph_search.execute_query(query)
            graph_search.close()

            logger.info(f"Query execution time: {time.time() - execute_query_start_time} seconds")
            logger.info(f"Result: {result}")

            # Use transformer for graph result
            graph_transformer = self.graph_transformer_factory.create_graph_transformer(self.settings.NETWORK)
            graph_summary_transformer = self.graph_summary_transformer_factory.create_graph_summary_transformer(self.settings.NETWORK)
            graph_transformed_result = graph_transformer.transform_result(result)
            graph_summary_result = graph_summary_transformer.transform_result(result)
            logger.info(f"Summary Result: {graph_summary_result}")

            # Use transformer for chart result
            chart_transformer = self.chart_transformer_factory.create_chart_transformer(self.settings.NETWORK)
            chart_transformed_result = None
            if chart_transformer.is_chart_applicable(result):
                chart_transformed_result = chart_transformer.convert_funds_flow_to_chart(result)

            interpret_result_start_time = time.time()
            interpreted_result = self.llm.interpret_result_funds_flow(
                llm_messages=llm_messages_list.messages,
                result=graph_summary_result,
                network=self.settings.NETWORK
            )

            logger.info(f"Result interpretation time: {time.time() - interpret_result_start_time} seconds")
            output = LlmMessageOutputList(outputs=[
                LlmMessageOutput(type="graph", result=graph_transformed_result),
                LlmMessageOutput(type="text", result=[interpreted_result])
            ])
            return output

        except Exception as e:
            logger.error(traceback.format_exc())
            error_code = e.args[0] if len(e.args) > 0 and isinstance(e.args[0], int) else LLM_UNKNOWN_ERROR
            error_message = LLM_ERROR_MESSAGES.get(error_code, 'An unknown error occurred')
            output = LlmMessageOutputList(outputs=[LlmMessageOutput(type="error", error=error_code, result=error_message)])
            return output

    async def _handle_balance_tracking_query(self, llm_messages: LlmMessageList) -> LlmMessageOutputList:
        try:
            query_start_time = time.time()
            query = self.llm.build_query_from_messages_balance_tracker(llm_messages.messages, settings.NETWORK)
            logger.info(f"extracted query: {query} (Time taken: {time.time() - query_start_time} seconds)")

            if query in ['modification_error', 'invalid_prompt_error']:
                error_code = LLM_ERROR_MODIFICATION_NOT_ALLOWED if query == 'modification_error' else LLM_ERROR_INVALID_SEARCH_PROMPT
                error_message = LLM_ERROR_MESSAGES.get(error_code)
                logger.error(f"Error {error_code}: {error_message}")
                output = LlmMessageOutputList(outputs=[LlmMessageOutput(type="error", error=error_code, result=error_message)])
                return output

            execute_query_start_time = time.time()
            balance_search = self.balance_search_factory.create_balance_search(self.settings.NETWORK)
            result = await balance_search.execute_query(query)

            logger.info(f"Query execution time: {time.time() - execute_query_start_time} seconds")

            # Use transformer for tabular result
            tabular_transformer = self.tabular_transformer_factory.create_tabular_transformer(self.settings.NETWORK)
            tabular_transformed_result = tabular_transformer.transform_result_set(result)

            chart_transformer = self.chart_transformer_factory.create_chart_transformer(self.settings.NETWORK)
            chart_transformed_result = None
            if chart_transformer.is_chart_applicable(result):
                chart_transformed_result = chart_transformer.convert_balance_tracking_to_chart(result)

            interpret_result_start_time = time.time()
            interpreted_result = self.llm.interpret_result_balance_tracker(
                llm_messages=llm_messages.messages,
                result=tabular_transformed_result,
                network=self.settings.NETWORK
            )

            logger.info(f"Result interpretation time: {time.time() - interpret_result_start_time} seconds")
            output = LlmMessageOutputList(outputs=[
                LlmMessageOutput(type="table", result=tabular_transformed_result),
                LlmMessageOutput(type="text", result=[interpreted_result])])

            return output

        except Exception as e:
            logger.error(traceback.format_exc())
            error_code = e.args[0] if len(e.args) > 0 and isinstance(e.args[0], int) else LLM_UNKNOWN_ERROR
            error_message = LLM_ERROR_MESSAGES.get(error_code, 'An error occurred')
            output = LlmMessageOutputList(outputs=[LlmMessageOutput(type="error", error=error_code, result=error_message)])
            return output


if __name__ == "__main__":
    from communex.module.server import ModuleServer
    from communex.compat.key import classic_load_key
    import uvicorn
    import time
    import sys

    if len(sys.argv) != 2:
        logger.error("Usage: python -m subnet.cli <environment> ; where <environment> is 'testnet' or 'mainnet'")
        sys.exit(1)

    env = sys.argv[1]
    use_testnet = env == 'testnet'
    load_environment(env)

    logger.remove()
    logger.add(
        "../logs/miner.log",
        rotation="500 MB",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )

    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG"
    )

    settings = MinerSettings()
    keypair = classic_load_key(settings.MINER_KEY)
    c_client = CommuneClient(get_node_url(use_testnet=use_testnet))
    miner = Miner(settings=settings)
    refill_rate: float = 1 / 1000
    bucket = TokenBucketLimiter(
        refill_rate=refill_rate,
        bucket_size=1000,
        time_func=time.time,
    )
    limiter = IpLimiterParams()
    db_manager.init(settings.DATABASE_URL)

    server = ModuleServer(miner,
                          keypair,
                          subnets_whitelist=[settings.NET_UID],
                          use_testnet=use_testnet,
                          limiter=limiter)

    app = server.get_fastapi_app()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def shutdown_handler(signal, frame):
        uvicorn_server.should_exit = True
        uvicorn_server.force_exit = True

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    uvicorn_server = uvicorn.Server(config=uvicorn.Config(app, host="0.0.0.0", port=9962, workers=4))
    uvicorn_server.run()

