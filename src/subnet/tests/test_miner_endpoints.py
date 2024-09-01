import unittest
import time  # dont remove this import
from dotenv import load_dotenv
from src.subnet.miner._config import MinerSettings
from src.subnet.miner.miner import Miner
from src.subnet.protocol.llm_engine import LlmMessageList, LlmMessage
from src.subnet.validator.database import db_manager
from src.subnet.validator.nodes.factory import NodeFactory


def load_environment():
    load_dotenv(dotenv_path='../../../env/.env.tests.testnet')


class BitcoinLmmQueryTestCase(unittest.IsolatedAsyncioTestCase):

        async def asyncSetUp(self):
            load_environment()
            self.settings = MinerSettings()
            self.miner = Miner(settings=self.settings)
            self.node = NodeFactory.create_node('bitcoin')
            db_manager.init(self.settings.DATABASE_URL)

        async def test_bitcoin_lmm_query(self):
            llm_message_list = LlmMessageList(messages=[LlmMessage(type=0, content="1CGpXZ9LLYwi1baonweGfZDMsyA35sZXCW this is my wallet in bitcoin. what is my last transaction")])
            result = await self.miner.llm_query(llm_message_list.model_dump())
            self.assertEqual(len(result.outputs), 2)


class BitcoinChallengesTestCase(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        load_environment()
        self.settings = MinerSettings()
        self.miner = Miner(settings=self.settings)
        self.node = NodeFactory.create_node('bitcoin')
        db_manager.init(self.settings.DATABASE_URL)

    async def test_bitcoin_funds_flow_challenge(self):
        funds_flow_challenge, tx_id = self.node.create_funds_flow_challenge(0, 500)
        result = await self.miner.challenge(funds_flow_challenge.model_dump())
        self.assertEqual(result.output['tx_id'], tx_id)

    async def test_bitcoin_balance_tracking_challenge(self):
        balance_tracking_challenge, balance_tracking_expected_response = self.node.create_balance_tracking_challenge(500)
        result = await self.miner.challenge(balance_tracking_challenge.model_dump())
        self.assertEqual(result.output['balance'], balance_tracking_expected_response)


class MinerDiscoveryTestCase(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        load_environment()
        self.settings = MinerSettings()
        self.miner = Miner(settings=self.settings)

    async def test_bitcoin_discovery_challenge(self):
        result = await self.miner.discovery()
        self.assertEqual(result['network'], self.settings.NETWORK)

if __name__ == '__main__':
    unittest.main()
