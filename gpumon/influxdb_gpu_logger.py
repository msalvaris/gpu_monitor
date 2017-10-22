from influxdb import InfluxDBClient
import logging

from .nvidia_dmon import nvidia_run_dmon_poll
from .influxdb_interface import create_influxdb_writer

logger = logging.getLogger(__name__)


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