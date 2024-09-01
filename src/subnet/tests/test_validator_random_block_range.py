import unittest
from src.subnet.validator.nodes.random_block import select_block


class MyTestCase(unittest.TestCase):
    def test_select_block_range(self):
        for i in range(10):
            block = select_block(0, 850000)
            print(f"Selected block range: {block}")


if __name__ == '__main__':
    unittest.main()
