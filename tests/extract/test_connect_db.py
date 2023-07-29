from src.extract.extract import connect_db, get_secret
from pg8000.native import Connection, InterfaceError
import pytest
import boto3
from unittest.mock import patch
import json
from moto import (
    mock_secretsmanager
    )


# @patch('src.extract.extract.Connection')
# def test_test(mock_connection):

#     mock_connection.return_value = Connection()
#     AWS_SECRET_DB_CREDENTIALS_NAME = "ingestion/db/credentials"
#     db_credentials_response = get_secret(AWS_SECRET_DB_CREDENTIALS_NAME)
#     db_credentials = json.loads(db_credentials_response["SecretString"])
#     connection = connect_db(db_credentials, db_name = "totesys")
#     print(type(connection))

#     assert True

def test_should_raise_exception_if_incorrect_credentials():
    test_db_credentials = {
        "username": "test_user",
        "password": "test_password",
        "engine": "test_engine",
        "host": "http://test.com",
        "port": "9090",
        "dbname": "test_dbname"
        }
    with pytest.raises(InterfaceError):
        connection = connect_db(test_db_credentials, db_name = "totesys")

def test_should_raise_exception_if_incorrect_input_type():
    test_db_credentials = {
        "username": "test_user",
        "password": "test_password",
        "engine": "test_engine",
        "host": "http://test.com",
        "port": "9090",
        "dbname": "test_dbname"
        }
    with pytest.raises(TypeError):
        connection = connect_db(test_db_credentials, db_name = 2)
    
    with pytest.raises(TypeError):
        connection = connect_db(["test"])

def test_should_raise_exception_if_incorrect_db_data():
    test_db_credentials = {
        "username": "test_user",
        "password": "test_password",
        "engine": "test_engine",
        "port": "9090",
        "dbname": "test_dbname"
        }
    with pytest.raises(KeyError):
        connection = connect_db(test_db_credentials)

    test_db_credentials = {
        "username": "test_user",
        "password": "test_password",
        "engine": "test_engine",
        "host": "http://test.com",
        "port": 9090,
        "dbname": "test_dbname"
        }

    with pytest.raises(ValueError):
        connection = connect_db(test_db_credentials)
