import logging
from contextlib import contextmanager
from functools import partial
from multiprocessing import Process
from time import sleep

from dotenv import find_dotenv, dotenv_values
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from requests.exceptions import ConnectionError
from toolz import curry, compose

from gpumon.influxdb.gpu_interface import start_pushing_measurements_to

MEASUREMENTS_RETENTION_DURATION = '1d'


def _logger():
    return logging.getLogger(__name__)


def _switch_to_database(influxdb_client, database_name):
    dbs = influxdb_client.get_list_database()
    if database_name in [db['name'] for db in dbs]:
        _logger().info('Database {} exists'.format(database_name))
    else:
        _logger().info('Creating Database {}'.format(database_name))
        influxdb_client.create_database(database_name)
    influxdb_client.switch_database(database_name)


def _compose_measurement_dict(gpu_num, gpu_dict, series_name):
    return {"measurement": series_name,
            "tags": {'GPU': gpu_num},
            "time": gpu_dict['timestamp'],
            "fields": gpu_dict}


@curry
def _gpu_to_influxdb_format(series_name, gpu_dict):
    return [_compose_measurement_dict(gpu, gpu_dict[gpu], series_name) for gpu in gpu_dict]


def _create_influxdb_writer(influxdb_client, tags):
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
                if influxdb_client.write_points(data_list, tags=tags):
                    logger.debug("Success")
                    break
                else:
                    sleep(pause)
            except InfluxDBClientError:
                logger.debug('Failed {} out of {}'.format(i, retries))
        else:
            logger.warning("Failed to write to Database")

    return to_influxdf


def _set_retention_policy(influxdb_client, database, retention_duration, policy_name='standard'):
    retention_policies = influxdb_client.get_list_retention_policies(database=database)

    for policy in retention_policies:
        if policy['name'] == policy_name:
            _logger().debug('Found policy {}:{}'.format(policy_name, str(policy)))
            influxdb_client.alter_retention_policy(policy_name,
                                                   database=database,
                                                   duration=retention_duration,
                                                   default=True)
            break
    else:
        _logger().debug('Creating policy {}'.format(policy_name))
        influxdb_client.create_retention_policy(policy_name,
                                                retention_duration,
                                                1,
                                                database=database,
                                                default=True)


class MetricsRecordingFailed(Exception):
    pass


def start_logger(ip_or_url,
                 username,
                 password,
                 database,
                 port=8086,
                 series_name='gpu_measurements',
                 polling_interval=1,
                 retention_duration=MEASUREMENTS_RETENTION_DURATION,
                 **tags):
    """ Starts GPU logger

    Logs GPU measurements to an influxdb database

    Parameters
    ----------
    ip_or_url: ip or url of influxdb
    username: Username to log into influxdb database
    password: Password to log into influxdb database
    database: Name of database to log data to. It will create the database if one doesn't exist
    port: A number indicating the port on which influxdb is listening
    series_name: Name of series/table to log data to
    polling_interval: polling interval for measurements in seconds [default:1]
    retention_duration: the duration to retain the measurements for valid values are 1h, 90m, 12h, 7d, and 4w. default:1d
    tags: One or more tags to apply to the data. These can then be used to group or select timeseries
          Example: --machine my_machine --cluster kerb01

    """

    logger = _logger()
    logger.info('Trying to connect to {} on port {} as {}'.format(ip_or_url, port, username))
    try:
        client = InfluxDBClient(ip_or_url, port, username, password)
        response = client.ping()
    except ConnectionError:
        logger.warning('Could not connect to InfluxDB. GPU metrics NOT being recorded')
        raise MetricsRecordingFailed()

    logger.info('Connected | version {}'.format(response))
    _switch_to_database(client, database)

    logger.info('Measurement retention duration {}'.format(retention_duration))
    _set_retention_policy(client, database, retention_duration)

    to_db = compose(_create_influxdb_writer(client, tags=tags),
                    _gpu_to_influxdb_format(series_name))
    logger.info('Starting logging...')
    return start_pushing_measurements_to(to_db, polling_interval=polling_interval)


def _start_logger_process(ip_or_url,
                          port,
                          username,
                          password,
                          database,
                          series_name='gpu_measurements',
                          polling_interval=1,
                          retention_duration=MEASUREMENTS_RETENTION_DURATION,
                          **tags):
    try:
        t, stop_logging = start_logger(ip_or_url,
                                       username,
                                       password,
                                       database,
                                       port=port,
                                       series_name=series_name,
                                       polling_interval=polling_interval,
                                       retention_duration=retention_duration,
                                       **tags)
        t.join()
    except MetricsRecordingFailed:
        return None


@contextmanager
def _log_process(ip_or_url,
                 username,
                 password,
                 database,
                 series_name,
                 port=8086,
                 polling_interval=1,
                 retention_duration=MEASUREMENTS_RETENTION_DURATION,
                 **tags):
    """ GPU logging context

    Logs GPU measurements to an influxdb database

    Parameters
    ----------
    ip_or_url: ip or url of influxdb
    username: Username to log into influxdb database
    password: Password to log into influxdb database
    database: Name of database to log data to. It will create the database if one doesn't exist
    series_name: Name of series/table to log data to
    port: A number indicating the port on which influxdb is listening
    polling_interval: polling interval for measurements in seconds [default:1]
    retention_duration: the duration to retain the measurements for valid values are 1h, 90m, 12h, 7d, and 4w. default:1d
    tags: One or more tags to apply to the data. These can then be used to group or select timeseries
          Example: machine=my_machine cluster=kerb01
    """
    logger = _logger()
    logger.info('Logging GPU to Database {}'.format(ip_or_url))

    kwargs = {'series_name': series_name,
              'polling_interval': polling_interval,
              'retention_duration': retention_duration}
    kwargs.update(tags)
    p = Process(target=_start_logger_process,
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


def _generate_log_context():
    logger = _logger()
    try:
        dotenv_path = find_dotenv(raise_error_if_not_found=True)
        logger.info('Found .evn, loading variables')
        env_dict = dotenv_values(dotenv_path=dotenv_path)
        return partial(_log_process, **env_dict)
    except IOError:
        logger.info('Didn\'t find .env')
        return _log_process


log_context = _generate_log_context()


