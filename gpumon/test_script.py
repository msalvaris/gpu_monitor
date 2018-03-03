import pynvml
from datetime import datetime
from toolz.functoolz import compose
import time
import asyncio


def nativestr(s):
    if isinstance(s, str):
        return s
    return s.decode('utf-8', 'replace')

def device_name_for(device_handle):
    """Get GPU device name"""
    try:
        return nativestr(pynvml.nvmlDeviceGetName(device_handle))
    except pynvml.NVMlError:
        return "NVIDIA"


def mem_for(device_handle):
    """Get GPU device memory consumption in percent"""
    try:
        memory_info = pynvml.nvmlDeviceGetMemoryInfo(device_handle)
        return memory_info.used * 100.0 / memory_info.total
    except pynvml.NVMLError:
        return None


def utilization_for(device_handle):
    """Get GPU device consumption in percent"""
    try:
        return pynvml.nvmlDeviceGetUtilizationRates(device_handle).gpu
    except pynvml.NVMLError:
        return None


def mem_utilization_for(device_handle):
    try:
        return pynvml.nvmlDeviceGetUtilizationRates(device_handle).memory
    except pynvml.NVMLError:
        return None


def power_for(device_handle):
    try:
        return pynvml.nvmlDeviceGetPowerUsage(device_handle)
    except pynvml.NVMLError:
        return None


def temperature_for(device_handle):
    try:
        return pynvml.nvmlDeviceGetTemperature(device_handle, 0)
    except pynvml.NVMLError:
        return None


_MEASUREMENTS_FUNCS ={
    "Name": device_name_for,
    "Memory": mem_for,
    "Utilization": utilization_for,
    "Memory Utilization": mem_utilization_for,
    "Power": power_for,
    "Temperature": temperature_for,
}

def measurements_for(gpu_handle):
    mes_dict = {k: func(gpu_handle) for k, func in _MEASUREMENTS_FUNCS.items()}
    mes_dict['timestamp'] = str(datetime.now())
    return mes_dict

async def aggregate_measurements(device_count):
    measures_for_device = compose(measurements_for,
                                  pynvml.nvmlDeviceGetHandleByIndex)
    return {i:measures_for_device(i) for i in range(device_count)}


async def display_measurements(deviceCount, polling_interval=1):
    while True:
        print(await aggregate_measurements(deviceCount))
        await asyncio.sleep(polling_interval)

def main():
    pynvml.nvmlInit()
    print("Driver Version: {}".format(nativestr(pynvml.nvmlSystemGetDriverVersion())))
    deviceCount = pynvml.nvmlDeviceGetCount()
    polling_interval=1
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(display_measurements(deviceCount))
    except KeyboardInterrupt:
        loop.close()
        pynvml.nvmlShutdown()

if __name__=="__main__":
    main()