import logging
from contextlib import contextmanager
from multiprocessing import Process
from time import sleep

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from toolz import curry, compose

from gpumon.influxdb.gpu_interface import start_pushing_measurements_to


def _logger():
    return logging.getLogger(__name__)


def _wait_for_database(influxdb_client, database_name):
    dbs = influxdb_client.get_list_database()
    logger = _logger()
    logger.debug(str(dbs))
    while database_name not in [db['name'] for db in dbs]:
        logger.info('Waiting for database {} to be created....')
        logger.debug(str(dbs))
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
        influxdb_client.switch_database(database_name)


def _transform_gpu_measurement(gpu_num, gpu_dict, series_name, tags):
    tags['GPU'] = gpu_num
    return {"measurement": series_name,
            "tags": tags,
            "time": gpu_dict['timestamp'],
            "fields": gpu_dict}


@curry
def _gpu_to_influxdb_format(series_name, tags, gpu_dict):
    return [_transform_gpu_measurement(gpu, gpu_dict[gpu], series_name, tags) for gpu in gpu_dict]


def _create_influxdb_writer(influxdb_client):
    """ Returns function which writes to influxdb

    Parameters
    ----------
    influxdb_client:
    """

    def to_influxdf(data_list, retries=5, pause=5):
        logger = _logger()
        logger.debug(data_list)
        for i in range(retries):
            try:
                if influxdb_client.write_points(data_list):
                    logger.debug("Success")
                    break
                else:
                    sleep(pause)
            except InfluxDBClientError:
                logger.debug('Failed {} out of {}'.format(i,retries))
        else:
            logger.warning("Failed to write to Database")

    return to_influxdf


def start_logger(ip_or_url,
                 port,
                 username,
                 password,
                 database,
                 series_name='gpu_measurements',
                 polling_interval=1,
                 **tags):
    """ Starts GPU logger

    Logs GPU measurements to an influxdb database

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

    """

    logger = _logger()
    logger.info('Trying to connect to {} on port {} as {}'.format(ip_or_url, port, username))
    client = InfluxDBClient(ip_or_url, port, username, password)
    logger.info('Connected')

    _create_database(client, database)
    to_db = compose(_create_influxdb_writer(client),
                    _gpu_to_influxdb_format(series_name, tags))
    logger.info('Starting logging...')
    return start_pushing_measurements_to(to_db, polling_interval=polling_interval)


@contextmanager
def log_context(ip_or_url,
                port,
                username,
                password,
                database,
                series_name,
                debug=False,
                polling_interval=5,
                **tags):
    logger = _logger()
    logger.info('Logging GPU to Database {}'.format(ip_or_url))

    kwargs = {'series_name': series_name,
              'debug': debug,
              'polling_interval': polling_interval}.update(tags)
    p = Process(target=start_logger,
                args=(ip_or_url,
                      port,
                      username,
                      password,
                      database),
                kwargs=kwargs)
    p.start()
    yield p
    p.terminate()
    p.join()
