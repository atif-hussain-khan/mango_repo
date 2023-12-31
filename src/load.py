import logging
import pg8000
import numpy as np
from utils.utils import get_secret
from utils.load_utils import (
    get_id_col, get_table_data,
    insert_data_format, build_insert_sql,
    insert_table_data, get_job_list,
    build_update_sql, update_data_format,
    rename_lastjob)

logger = logging.getLogger('LoadLogger')
logger.setLevel(logging.INFO)


def load_lambda_handler(event, context):
    """
    Entry point for Load Lambda, triggered by CloudWatch scheduled event.
    Retrieves warehouse credentials, and list of table names, from
    AWS Secrets, as well as a list of timestamps from 'lastjob.csv'
    file in processed s3 bucket.

    Then establishes connection with warehouse before iterating through
    list of table names. With each iteration, function iterates through
    list of timestamps, reading data from processed s3 bucket as pandas
    dataframe:

        - For dim_tables: peforms neccessary data transformations
        before comparing each row id to warehouse, discerning inserts from
        updates, building queries and configuring row structure,
        before updating warehouse.

        - For fact tables; queries are built and
        data formatted before updating warehouse.

        - Logging progress to CloudWatch.

    Connection to warehouse is then closed and lastjob.csv is renamed with
    timestamp to keep record and indicate successful load.

    Args:
        event (dict):
            event data containing info about triggered S3 object.

        context (LambdaContext):
            runtime information about the lambda function.

    Returns:
        None.

    Raises:
        Exception:
            Raised if an unforseen errors arrise during execution.

    Note:
        This function relies on, and utilises, the following utility functions:
            get_id_col, get_table_data,
            insert_data_format, build_insert_sql,
            insert_table_data, get_job_list,
            build_update_sql, update_data_format,
            rename_lastjob, get_secret.
    """
    PROCESSED_BUCKET_NAME = 'processed-va-052023'
    WAREHOUSE_DB_NAME = 'warehouse'
    WAREHOUSE_TABLE_NAMES = 'warehouse_table_names'

    new_jobs = get_job_list(PROCESSED_BUCKET_NAME)
    rename_lastjob(PROCESSED_BUCKET_NAME)
    db_creds = get_secret(WAREHOUSE_DB_NAME)
    table_names = list(get_secret(WAREHOUSE_TABLE_NAMES).keys())

    try:
        connection = pg8000.connect(
            host=db_creds['host'],
            port=db_creds['port'],
            database=db_creds['dbname'],
            user=db_creds['username'],
            password=db_creds['password']
        )
        logger.info('successfully connected to database')

        for table_name in table_names:

            for ts_dir in new_jobs:

                logger.info(f'looping over {table_name} in directory {ts_dir}')

                table_df = get_table_data(
                    table_name, PROCESSED_BUCKET_NAME, ts_dir)
                logger.info(f'successfully retrieved {table_name} dataframe')

                if table_name == 'dim_transaction':
                    table_df.replace({np.nan: -1}, inplace=True)
                    table_df = table_df.astype(
                        {"sales_order_id": 'int', "purchase_order_id": 'int'})
                    table_df.replace({-1: None}, inplace=True)

                if len(table_df) > 0:
                    if table_name.startswith('dim'):
                        lst_wh_id = get_id_col(
                            connection, table_name, table_df)
                        for row in table_df.values.tolist():
                            if row[0] in lst_wh_id:
                                query = build_update_sql(table_name, table_df)
                                data = [tuple(update_data_format(row))]
                            else:
                                query = build_insert_sql(table_name, table_df)
                                data = [
                                    tuple(row)]
                            insert_table_data(connection, query, data)
                    else:
                        query = build_insert_sql(table_name, table_df)
                        data = insert_data_format(table_df)
                        insert_table_data(connection, query, data)

                    logger.info(
                        f'successfully loaded {table_name} to the warehouse')
                else:
                    logger.info(f'SKIPPING: {table_name} - no data to add')

        connection.close()

    except Exception as error:
        logger.error("main function error")
        raise error
