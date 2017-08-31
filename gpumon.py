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
        pipe(nvidia_run, processing_func)

        
def gpu_plot(data, num_gpus=4, plot_width=600, plot_height=400, y_range=(0, 110)):
    """
    """
    p = figure(plot_width=plot_width, plot_height=plot_height, y_range=y_range)
    for gpu, color in zip(range(num_gpus), Paired[12]) :
        p.line('index', 
               'gpu {}'.format(gpu), 
               line_width=4, 
               source=data, 
               color=color, 
               legend="GPU {}".format(gpu))
    return p
        
def monitor(gpu_property):
    
    


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