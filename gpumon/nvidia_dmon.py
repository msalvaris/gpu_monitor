import select
import subprocess
import time
from contextlib import contextmanager
from datetime import datetime

try:
    from itertools import filterfalse
except ImportError:
    from itertools import ifilterfalse as filterfalse

import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.palettes import Paired
from bokeh.plotting import figure
from toolz import curry, pipe
import logging


logger = logging.getLogger(__name__)


def nvidia_run_dmon(interval_seconds=1):
    return subprocess.run(["nvidia-smi", "dmon", "-d", str(interval_seconds), "-o", "DT"],
                          stdout=subprocess.PIPE).stdout


def nvidia_run_dmon_poll(output_func, interval_seconds=1, polling_timeout=1, polling_interval=0.2):
    proc = subprocess.Popen(["nvidia-smi", "dmon", "-d", str(interval_seconds), "-o", "DT"], stdout=subprocess.PIPE)

    poller = select.poll()
    poller.register(proc.stdout, select.POLLIN)

    while True:
        if poller.poll(polling_timeout):
            output_func(proc.stdout.readline().decode('utf-8'))
        else:
            time.sleep(polling_interval)


convert_datetime = lambda x: datetime.strptime(x, '%Y%m%d')
convert_time = lambda x: datetime.strptime(x, '%H:%M:%S').time()
conversion_funcs = convert_datetime, convert_time, int, int, int, int, int, int, int, int, int
gpu_headers = 'timestamp', 'gpu', 'pwr', 'temp', 'sm', 'mem', 'enc', 'dec', 'mclk', 'pclk'
header_dict = dict(zip(range(len(gpu_headers)), gpu_headers))


def parse_line(line_string):
    parsed_list = list((func(val) for func, val in zip(conversion_funcs, line_string.split())))
    logger.info(parsed_list)
    return [datetime.combine(*parsed_list[:2])] + parsed_list[2:]


def convert_to_df(msg_list):
    return (pd.DataFrame(msg_list)
            .rename(columns=header_dict)
            .dropna(how='any'))


def parse_lines(msg_list):
    msg_list = filterfalse(lambda x: '#' in x, msg_list)
    new_list = []
    for line in msg_list:
        try:
            new_list.append(parse_line(line))
        except (ValueError, TypeError):
            logger.debug('Error parsing {}'.format(line))
    return convert_to_df(new_list)


def parse_log(filename):
    with open(filename) as f:
        return parse_lines(list(f))


@curry
def extract(gpu_property, df):
    return (df.groupby(['timestamp', 'gpu'])[gpu_property]
              .first()
              .unstack(level=1)
              .ffill()
              .bfill()
              .rename(columns={i:'gpu {}'.format(i) for i in range(4)}))


def plot(df, num_gpus=1, plot_width=600, plot_height=400, y_range=(0, 110)):
    """
    """
    data = ColumnDataSource(data=df)
    p = figure(plot_width=plot_width, plot_height=plot_height, y_range=y_range, x_axis_type="datetime")
    for gpu, color in zip(range(num_gpus), Paired[12]):
        p.line('timestamp',
               'gpu {}'.format(gpu),
               line_width=4,
               source=data,
               color=color,
               legend="GPU {}".format(gpu))
    return p


class Logger(object):
    def __init__(self, log_file):
        self._log_file = log_file

    def __call__(self):
        return parse_log(self._log_file)

    def plot(self, gpu_property='sm', num_gpus=1, plot_width=600, plot_height=400, y_range=(0, 110)):
        df = pipe(self._log_file,
                  parse_log,
                  extract(gpu_property))
        return plot(df,
                    num_gpus=num_gpus,
                    plot_width=plot_width,
                    plot_height=plot_height,
                    y_range=y_range)


@contextmanager
def log_context(log_file, interval_seconds=1):
    logger.info('Logging GPU in {}'.format(log_file))
    process_args = ["nvidia-smi",
                    "dmon",
                    "-d", str(interval_seconds),
                    "-o", "DT",
                    "-f", log_file]

    with subprocess.Popen(process_args, stdout=subprocess.PIPE) as proc:
        yield Logger(log_file)
        proc.terminate()

