from loguru import logger
import os


def read_local_file(file_path):
    try:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        full_path = os.path.join(base_path, file_path)

        if not os.path.exists(full_path):
            logger.error(f"File not found: {full_path}")
            return None

        with open(full_path, 'r', encoding='utf-8') as file:
            content = file.read()

        return content
    except Exception as e:
        logger.error(f"Error reading local file: {e}")
        return None