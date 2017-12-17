from toolz import compose, merge, curry
import logging

from gpumon.nvidia_dmon import parse_line

logger = logging.getLogger(__name__)


def _to_json_dict(gpu_prop_list):
    return { "time": gpu_prop_list[0].strftime('%Y-%m-%dT%H:%M:%S%z'),
            "tags": {
                "gpu": gpu_prop_list[1],
            },
             "fields": {
                "pwr": gpu_prop_list[2],
                "temp": gpu_prop_list[3],
                "sm": gpu_prop_list[4],
                "mem": gpu_prop_list[5],
                "enc": gpu_prop_list[6],
                "dec": gpu_prop_list[7],
                "mclk": gpu_prop_list[8],
                "pclk": gpu_prop_list[9],
             }
           }


def _influxdb_writer_for(influxdb_client, measurement):
    mes_dict = {"measurement": measurement}
    def to_influxdf(*data_dicts):
        merged_dicts = merge(mes_dict, *data_dicts)
        logger.debug(merged_dicts)
        if influxdb_client.write_points([merged_dicts]):
            logger.debug("Success")
        else:
            logger.info("FAIL")
    return to_influxdf


@curry
def _call_when(write_func, predicate_func, line):
    if predicate_func(line):
        write_func(line)

@curry
def _add_tags(tags, json_dict):
    json_dict['tags'] = merge(json_dict['tags'], tags)
    return json_dict


def create_influxdb_writer(influxdb_client, series_name="gpu_measurements", **tags):
    """ Returns function which writes to influxdb

    Parameters
    ----------
    influxdb_client:
    series_name: (str)
    tags: Extra tags to be added to the measurements
    """
    to_influxdb = _influxdb_writer_for(influxdb_client, series_name)

    if tags:
        logger.debug('Creating writer with tags')
        write_to_db = compose(to_influxdb,
                              _add_tags(tags),
                              _to_json_dict,
                              parse_line)
    else:
        logger.debug('Creating writer')
        write_to_db = compose(to_influxdb,
                              _to_json_dict,
                              parse_line)

    return _call_when(write_to_db, lambda x: x is not None and '#' not in x)
