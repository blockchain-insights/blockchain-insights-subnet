from abc import ABC, abstractmethod


class Node(ABC):
    def __init__(self):
        ...

    @abstractmethod
    def get_current_block_height(self):
        ...
