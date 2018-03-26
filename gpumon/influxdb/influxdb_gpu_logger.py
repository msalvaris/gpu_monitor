import logging
import subprocess
from contextlib import contextmanager
from itertools import chain

from gpu_interface import start_record_gpu_to
from influxdb import InfluxDBClient, DataFrameClient
from toolz import curry, compose

# from gpumon.influxdb.influxdb_interface import create_influxdb_writer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Logger(object):
    def __init__(self,
                 ip_or_url,
                 port,
                 username,
                 password,
                 database,
                 series_name):
        self._client = DataFrameClient(ip_or_url, port, username, password, database)
        self._series_name = series_name

    def __call__(self):
        return self._client.query("select * from {}".format(self._series_name))[self._series_name]


@contextmanager
def log_context(ip_or_url,
                port,
                username,
                password,
                database,
                series_name,
                debug=False,
                nvidia_polling_interval=5,
                polling_timeout=1,
                polling_pause=1,
                **tags):
    logger.info('Logging GPU to Database {}'.format(ip_or_url))
    process_args = ["influxdb_gpu_logger.py",
                    ip_or_url,
                    port,
                    username,
                    password,
                    database,
                    series_name,
                    "--debug={}".format(debug),
                    "--nvidia_polling_interval={}".format(nvidia_polling_interval),
                    "--polling_timeout={}".format(polling_timeout),
                    "--polling_pause={}".format(polling_pause)]

    if tags:
        process_args.extend(('--{}={}'.format(k,v) for k,v in tags.items()))

    logger.info(process_args)
    with subprocess.Popen(process_args, stdout=subprocess.PIPE) as proc:
        yield Logger(ip_or_url, port, username, password, database, series_name)
        proc.terminate()


def _create_database(influxdb_client, database_name):
    dbs = influxdb_client.get_list_database()
    if database_name in [db['name'] for db in dbs]:
        logger.info('Database {} exists'.format(database_name))
        influxdb_client.switch_database(database_name)
    else:
        # TODO: Need to wait for database to be ready before continuing
        influxdb_client.create_database(database_name)


def _transform_gpu(gpu_num, gpu_dict, series_name, tags):
    tags['GPU']=gpu_num
    measurements_generator = ((gpu_dict, gpu_dict[key]) for key in set(gpu_dict.keys()) - set(['timestamp']))
    print(list(measurements_generator))
    identifiers_generator = (("measurement", series_name),
                             # ("tags", tags),
                             ("time", gpu_dict['timestamp']))
    return dict(chain(measurements_generator, identifiers_generator))


@curry
def _gpu_to_influxdb_format(series_name, tags, gpu_dict):
    return [_transform_gpu(gpu, gpu_dict[gpu], series_name, tags) for gpu in gpu_dict]


def create_influxdb_writer(influxdb_client):
    """ Returns function which writes to influxdb

    Parameters
    ----------
    influxdb_client:
    series_name: (str)
    tags: Extra tags to be added to the measurements
    """

    # def to_influxdf(data_list):
    #     logger.debug(data_list)
    #     if influxdb_client.write_points(data_list):
    #         logger.debug("Success")
    #     else:
    #         logger.info("FAIL")

    def to_influxdf(data_list):
        logger.info(data_list)

    return to_influxdf


def main(ip_or_url,
         port,
         username,
         password,
         database,
         series_name='gpu_measurements',
         debug=False,
         nvidia_polling_interval=5,
         polling_timeout=1,
         polling_pause=1,
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
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug('Debug logging | ON')

    try:
        logger.info('Trying to connect to {} on port {} with {}:{}'.format(ip_or_url, port, username, password))
        client = InfluxDBClient(ip_or_url, port, username, password)
        logger.info('Connected')


        _create_database(client, database)

        to_db = compose(create_influxdb_writer(client),
                        _gpu_to_influxdb_format(series_name, tags))
        logger.info('Starting logging...')
        start_record_gpu_to(to_db, polling_interval=nvidia_polling_interval)
    except KeyboardInterrupt:
        logger.info('Exiting')


def test_main():
    try:
        # logger.info('Trying to connect to {} on port {} with {}:{}'.format(ip_or_url, port, username, password))
        # client = InfluxDBClient(ip_or_url, port, username, password)
        logger.info('Connected')


        # _create_database(client, database)
        client=None
        series_name="gpu_measures"
        tags={
            'host':'test'
        }
        nvidia_polling_interval=1
        to_db = compose(create_influxdb_writer(client),
                        _gpu_to_influxdb_format(series_name, tags))
        logger.info('Starting logging...')
        start_record_gpu_to(to_db, polling_interval=nvidia_polling_interval)
    except KeyboardInterrupt:
        logger.info('Exiting')


if __name__=="__main__":
    # fire.Fire(main)
    test_main()
