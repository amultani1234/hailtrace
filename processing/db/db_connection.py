"""@class db_connection.py
For connecting to database and executing CRUD operations.
To use, call get_connection() and save in a variable. This
variable now holds a connection to the database hailtrace.
See PyMongo documentation for example usage, i.e. db.insert_one()

NOTE: Make sure to setup .env file in processing folder for this
to work, add connection string to variable MONGO_URI
"""
import logging
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

load_dotenv()


def get_connection():
    """Establish connection with database"""
    try:
        conn_str = os.getenv('MONGO_URI')
        client = MongoClient(conn_str)
    except ConnectionFailure as exception:
        logging.error("Failure to connect to db. {}".format(exception))
    else:
        logging.info("Database connection was successful")
    return client


def insert_files(docs, collection):
    """Pass in json objects in a list (even if just one)
    and the collection name"""
    try:
        conn = get_connection()
        if not isinstance(docs, list):
            raise ValueError("Param docs must be a list of json objects")
        if collection not in conn.hailtrace.list_collection_names():
            raise ValueError("Collection doesnt exist")
        for doc in docs:
            conn.hailtrace[collection].insert_one(doc)
    except ValueError as val_e:
        logging.error("{}".format(val_e))
    else:
        logging.info("Successfully inserted documents")
    finally:
        logging.info("Closing Connection")
        conn.close()
