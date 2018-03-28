import logging
logging.basicConfig(level=logging.INFO)

from time import sleep

import fire
from gpumon.influxdb.gpu_interface import start_record_gpu_to
from influxdb import InfluxDBClient
from toolz import curry, compose


def _logger():
    return logging.getLogger(__name__)


def _wait_for_database(influxdb_client, database_name):
    dbs = influxdb_client.get_list_database()
    logger = _logger()
    while database_name not in [db['name'] for db in dbs]:
        logger.info('Waiting for database {} to be created....')
        sleep(5)


def _create_database(influxdb_client, database_name):
    dbs = influxdb_client.get_list_database()
    if database_name in [db['name'] for db in dbs]:
        _logger().info('Database {} exists'.format(database_name))
        influxdb_client.switch_database(database_name)
    else:
        _logger().info('Creating Database {}'.format(database_name))
        influxdb_client.create_database(database_name)
        _wait_for_database(influxdb_client, database_name)


def _transform_gpu_measurement(gpu_num, gpu_dict, series_name, tags):
    tags['GPU'] = gpu_num
    return {"measurement": series_name,
            "tags": tags,
            "time": gpu_dict['timestamp'],
            "fields": gpu_dict}


@curry
def _gpu_to_influxdb_format(series_name, tags, gpu_dict):
    return [_transform_gpu_measurement(gpu, gpu_dict[gpu], series_name, tags) for gpu in gpu_dict]


def create_influxdb_writer(influxdb_client):
    """ Returns function which writes to influxdb

    Parameters
    ----------
    influxdb_client:
    series_name: (str)
    tags: Extra tags to be added to the measurements
    """

    def to_influxdf(data_list):
        logger=_logger()
        logger.debug(data_list)
        if influxdb_client.write_points(data_list):
            logger.debug("Success")
        else:
            logger.warning("FAIL")


    return to_influxdf


def main(ip_or_url,
         port,
         username,
         password,
         database,
         series_name='gpu_measurements',
         debug=False,
         polling_interval=1,
         **tags):
    """ Starts GPU logger

    Logs GPU measurements form nvidia-smi to an influxdb database


    Parameters
    ----------
    ip_or_url: ip or url of influxdb
    port: A number indicating the port on which influxdb is listening
    username: Username to log into influxdb database
    password: Password to log into influxdb database
    database: Name of database to log data to. It will create the database if one doesn't exist
    series_name: Name of series/table to log data to
    tags: One or more tags to apply to the data. These can then be used to group or select timeseries
          Example: --machine my_machine --cluster kerb01

    Example
    -------
    influxdb_gpu_logger.py localhost 8086 username password gpudata --machine=my_gpu_machine

    """

    if bool(debug):
        logging.basicConfig(level=logging.DEBUG)
        _logger().debug('Debug logging | ON')

    try:
        logger = _logger()
        logger.info('Trying to connect to {} on port {} with {}:{}'.format(ip_or_url, port, username, password))
        client = InfluxDBClient(ip_or_url, port, username, password)
        logger.info('Connected')

        _create_database(client, database)
        to_db = compose(create_influxdb_writer(client),
                        _gpu_to_influxdb_format(series_name, tags))
        logger.info('Starting logging...')
        start_record_gpu_to(to_db, polling_interval=polling_interval)
    except KeyboardInterrupt:
        logger.info('Exiting')


if __name__=="__main__":
    fire.Fire(main)
