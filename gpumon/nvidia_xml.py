import json
import subprocess
from itertools import count

from bokeh.io import push_notebook
from bokeh.models import ColumnDataSource
from bokeh.palettes import Paired
from bokeh.plotting import figure
from toolz import pipe

from .xml_parser import xml2json


def extract_gpu(gpu_dict):
    return {'temperature': gpu_dict['temperature'],
            'utilization': gpu_dict['utilization']}


def extract_fields(json_dict):
    return {'gpu': [extract_gpu(gpu) for gpu in json_dict['nvidia_smi_log']['gpu']]}


def print_out(gpu_dict):
    print(json.dumps(gpu_dict))


def nvidia_run_xml():
    return subprocess.run(["nvidia-smi", "-x", "-q"], stdout=subprocess.PIPE).stdout


def extract(xml_data):
    return pipe(xml_data,
                xml2json,
                extract_fields)


def extract_and_print(xml_data):
    pipe(xml_data,
         extract,
         print_out)


def run_continuously(processing_func):
    while True:
        pipe(nvidia_run_xml, processing_func)


def gpu_plot(data, num_gpus=4, plot_width=600, plot_height=400, y_range=(0, 110)):
    """
    """
    p = figure(plot_width=plot_width, plot_height=plot_height, y_range=y_range)
    for gpu, color in zip(range(num_gpus), Paired[12]):
        p.line('index',
               'gpu {}'.format(gpu),
               line_width=4,
               source=data,
               color=color,
               legend="GPU {}".format(gpu))
    return p


def _extract_number_from(t_string):
    return int(t_string.split()[0])


def _create_property_extraction_func(property_string, secondary_property):
    def extract_(msg):
        return {'gpu {}'.format(i): [_extract_number_from(gpu[property_string][secondary_property])] for gpu, i in
                zip(msg['gpu'], count())}


_PROPERTY_DICT = {
    'temperature': _create_property_extraction_func('temperature', 'gpu_temp'),
    'utilization': _create_property_extraction_func('temperature', 'gpu_util'),
}


def create_running_func(data, gpu_property_func):
    def start(plot_handle):
        try:
            num_gen = count()
            while True:
                new_data = pipe(nvidia_run_xml(), extract, gpu_property_func)
                new_data['index'] = [next(num_gen)]
                data.stream(new_data, rollover=None, setter=None)
                push_notebook(handle=plot_handle)
        except KeyboardInterrupt:
            print('Exiting plotting')

    return start


def monitor(gpu_property_string, num_gpus=4):
    """"
    Parameters
    ----------
    gpu_property_string: temperature or utilization
    """
    data_dict = {'gpu {}'.format(gpu): [] for gpu in range(num_gpus)}
    data_dict['index'] = []
    data = ColumnDataSource(data=data_dict)
    p = gpu_plot(data, num_gpus=4, plot_width=600, plot_height=400, y_range=(0, 110))
    return p, create_running_func(data, _PROPERTY_DICT[gpu_property_string])

