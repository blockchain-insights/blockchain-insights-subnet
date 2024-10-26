import pytest
from src.subnet.validator.nodes.random_block import select_block


@pytest.mark.parametrize("start, end", [(0, 850000)])
def test_select_block_range(start, end):
    for i in range(10):
        block = select_block(start, end)
        print(f"Selected block range: {block}")
