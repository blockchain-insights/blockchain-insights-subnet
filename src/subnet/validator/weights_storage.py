import os
import pickle
from loguru import logger


class WeightsStorage:

    def __init__(self, weights_file_name):
        self.weights_file_name = weights_file_name

    def setup(self):
        if not os.path.exists(self.weights_file_name):
            with open(self.weights_file_name, 'wb') as file:
                pickle.dump({}, file)
            logger.debug(f"Created file: {self.weights_file_name}")

    def store(self, weighted_scores: dict[int, int]):
        with open(self.weights_file_name, 'wb') as file:
            pickle.dump(weighted_scores, file)
        logger.debug(f"Stored weights to {self.weights_file_name}")

    def read(self) -> dict[int, int]:
        if not os.path.exists(self.weights_file_name):
            logger.debug(f"File {self.weights_file_name} does not exist, returning empty dictionary")
            return {}
        with open(self.weights_file_name, 'rb') as file:
            data = pickle.load(file)
        logger.debug(f"Read weights from {self.weights_file_name}")
        return data
