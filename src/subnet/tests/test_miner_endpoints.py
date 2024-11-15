import pytest
import time  # don't remove this import

from substrateinterface import Keypair

from src.subnet import VERSION
from src.subnet.miner._config import MinerSettings
from src.subnet.miner.miner import Miner
from src.subnet.validator.database import db_manager
from src.subnet.validator.nodes.factory import NodeFactory


@pytest.fixture
async def setup_miner():
    settings = MinerSettings(
        NET_UID=1,
        MINER_KEY="test_miner_key",
        MINER_NAME="Test Miner",
        NETWORK="testnet",
        DATABASE_URL="sqlite:///:memory:",
        GRAPH_DATABASE_USER="test_user",
        GRAPH_DATABASE_PASSWORD="test_password",
        GRAPH_DATABASE_URL="bolt://localhost:7687"
    )
    miner = Miner(settings=settings)
    return miner, settings


@pytest.fixture
async def setup_miner_with_node():
    settings = MinerSettings(
        NET_UID=1,
        MINER_KEY="test_miner_key",
        MINER_NAME="Test Miner",
        NETWORK="testnet",
        DATABASE_URL="sqlite:///:memory:",
        GRAPH_DATABASE_USER="test_user",
        GRAPH_DATABASE_PASSWORD="test_password",
        GRAPH_DATABASE_URL="bolt://localhost:7687"
    )
    keypair = Keypair.create_from_mnemonic(Keypair.generate_mnemonic())
    miner = Miner(keypair=keypair, settings=settings)
    node = NodeFactory.create_node('bitcoin')
    await db_manager.init(settings.DATABASE_URL)
    return miner, node, settings


@pytest.mark.asyncio
async def test_bitcoin_discovery_challenge(setup_miner):
    miner, settings = await setup_miner  # Await the fixture
    result = await miner.discovery(validator_version=VERSION, validator_key="test_validator_key")
    assert result['network'] == settings.NETWORK
