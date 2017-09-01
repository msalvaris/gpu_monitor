import select
import subprocess
import time
from contextlib import contextmanager
from datetime import datetime
from itertools import filterfalse

import pandas as pd


def nvidia_run_dmon(interval_seconds=1):
    return subprocess.run(["nvidia-smi", "dmon", "-d", str(interval_seconds), "-o", "DT"],
                          stdout=subprocess.PIPE).stdout

def nvidia_run_dmon_poll(output_func, interval_seconds=1, polling_timeout=1, polling_interval=0.2):
    proc = subprocess.Popen(["nvidia-smi", "dmon", "-d", str(interval_seconds), "-o", "DT"], stdout=subprocess.PIPE)

    poller = select.poll()
    poller.register(proc.stdout, select.POLLIN)

    while True:
        if poller.poll(polling_timeout):
            output_func(proc.stdout.readline())
        else:
            time.sleep(polling_interval)


convert_datetime = lambda x: datetime.strptime(x, '%Y%m%d')
convert_time = lambda x: datetime.strptime(x, '%H:%M:%S').time()
conversion_funcs = convert_datetime, convert_time, int, int, int, int, int, int, int, int, int
gpu_headers = 'timestamp', 'gpu','pwr','temp','sm','mem','enc','dec','mclk','pclk'
header_dict = dict(zip(range(2, len(gpu_headers)+2),gpu_headers[1:]))


def parse_line(line_string):
    parsed_list = list((func(val) for func, val in zip(conversion_funcs, line_string.split())))
    return [datetime.combine(*parsed_list[:2])]+parsed_list[2:]


def convert_to_df(msg_list):
    return (pd.DataFrame([line.split() for line in msg_list])
              .pipe(lambda x: x.assign(timestamp=pd.to_datetime(x[0] + ' ' + x[1])))
              .rename(columns=header_dict)
              .drop([0, 1], axis=1))


def parse_lines(msg_list):
    return convert_to_df(filterfalse(lambda x: x.startswith('#'), msg_list))


def parse_log(filename):
    with open(filename) as f:
        return parse_lines(list(f))


@contextmanager
def log_context(log_file, interval_seconds=1):
    print('Logging GPU in {}'.format(log_file))
    proc = subprocess.Popen(["nvidia-smi",
                             "dmon",
                             "-d", str(interval_seconds),
                             "-o", "DT",
                             "-f", log_file], stdout=subprocess.PIPE)
    yield lambda: parse_log(log_file)
    proc.terminate()