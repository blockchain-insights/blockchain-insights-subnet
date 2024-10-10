from abc import ABC, abstractmethod
from threading import Event


class Node(ABC):
    def __init__(self):
       pass

    @abstractmethod
    def get_current_block_height(self):
        ...

    @abstractmethod
    def get_block_by_height(self, block_height):
        ...

    @abstractmethod
    def create_funds_flow_challenge(self, last_block_height, terminate_event: Event):
        ...

    @abstractmethod
    def create_balance_tracking_challenge(self, block_height, terminate_event: Event):
        ...
