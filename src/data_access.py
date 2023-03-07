import sys
from pymongo import MongoClient
from src.utils import read_config
from src.exception import FlipkartCustomException
from src.logging import CustomLogger

config = read_config()
logger = CustomLogger("data_access_logs")


class Database:
    def __init__(self):
        self.client = MongoClient(config["secrets"]["mongodb"])
        self.database = self.client["FlipkartStore"]

    def create_collection(self, collection_name, data):
        try:
            collection = self.database[collection_name]
            if response := collection.insert_many(data):
                return response.acknowledged
            else:
                return False

        except Exception as e:
            message = FlipkartCustomException(e, sys)
            logger.error(message.error_message)
            raise message.error_message from e

    def drop_collection(self, collection_name):
        try:
            collection = self.database[collection_name]
            collection.drop()
            return True

        except Exception as e:
            message = FlipkartCustomException(e, sys)
            logger.error(message.error_message)
            raise message.error_message from e

    def get_collection(self, collection_name):
        try:
            collection = self.database[collection_name]
            return list(collection.find())

        except Exception as e:
            message = FlipkartCustomException(e, sys)
            logger.error(message.error_message)
            raise Exception(message.error_message) from e
