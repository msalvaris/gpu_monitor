from contextlib import contextmanager

import subprocess
from influxdb import InfluxDBClient
import logging

from .nvidia_dmon import nvidia_run_dmon_poll
from .influxdb_interface import create_influxdb_writer

logger = logging.getLogger(__name__)


class Logger(object):
    def __init__(self, ip_or_url, port, username, password, database, series_name):
        self._client = InfluxDBClient(ip_or_url, port, username, password, database)# TODO:Change to DF client
        self._series_name = series_name

    def __call__(self):
        return self._client.select_all()#TODO:Fix


@contextmanager
def log_context(ip_or_url, port, username, password, database, series_name, **tags):
    logger.info('Logging GPU to Database {}'.format(ip_or_url))
    process_args = ["python",
                    "influxdb_gpu_logger.py",
                    ip_or_url,
                    port,
                    username,
                    password,
                    database,
                    series_name]

    if tags:
        process_args.extend(tags.to_list()) # TODO:Check

    with subprocess.Popen(process_args, stdout=subprocess.PIPE) as proc:
        yield Logger(ip_or_url, port, username, password, database, series_name)
        proc.terminate()


def _create_database(influxdb_client, database_name):
    dbs = influxdb_client.get_list_database()
    if database_name in [db['name'] for db in dbs]:
        logger.info('Database {} exists')
        influxdb_client.switch_database(database_name)
    else:
        influxdb_client.create_database(database_name)


def main(ip_or_url, port, username, password, database, series_name='gpu_measurements', **tags):
    try:
        logger.info('Trying to connect to {} on port {} with {}:{}'.format(ip_or_url, port, username, password))
        client = InfluxDBClient(ip_or_url, port, username, password)
        logger.info('Connected')

        #TODO Check database exists if it doesn't create it
        _create_database(client, database)

        to_db = create_influxdb_writer(client, series_name=series_name, **tags)
        logger.info('Starting logging...')
        nvidia_run_dmon_poll(to_db)
    except KeyboardInterrupt:
        logger.info('Exiting')


if __name__=="__main__":
    #TODO: Adds Fire interface
    main(ip_or_url, port, username, password, database)