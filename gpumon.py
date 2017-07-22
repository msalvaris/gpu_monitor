import json
from xml_parser import xml2json
from toolz import pipe
import subprocess


def read_data():
    """ Reads data from nvidia-smi
    """
    return


def extract_gpu(gpu_dict):
    return {'temperature': gpu_dict['temperature'],
            'utilization': gpu_dict['utilization']}


def extract_fields(json_dict):
    return {'gpu':[extract_gpu(gpu) for gpu in json_dict['nvidia_smi_log']['gpu']]}


def print_out(gpu_dict):
    print(json.dumps(gpu_dict))


def nvidia_run():
    return subprocess.run(["nvidia-smi", "-x", "-q"], stdout=subprocess.PIPE)


def extract_and_print(xml_data):
    pipe(xml_data,
         xml2json,
         extract_fields,
         print_out)


def run_continuously(processing_func):
    while True:
        pipe(nvidia_run, processing_func)


def main():
    run_continuously(extract_and_print)
    # jd = json.loads(xml2json(test_data, None))

# jd['nvidia_smi_log'].keys()
#
# jd['nvidia_smi_log']['gpu'][0]
#
# jd['nvidia_smi_log']['gpu'][0]['temperature']
#
# jd['nvidia_smi_log']['gpu'][0]['utilization']