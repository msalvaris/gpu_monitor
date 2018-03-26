import asyncio
import logging
import time
from concurrent.futures import CancelledError
from datetime import datetime
from threading import Thread

import pynvml
from toolz.functoolz import compose

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.setLevel(logging.DEBUG)


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


async def record_measurements(async_reporting_func, polling_interval=1):
    try:
        deviceCount = pynvml.nvmlDeviceGetCount()
        while True:
            measurement = await aggregate_measurements(deviceCount)
            await async_reporting_func(measurement)
            await asyncio.sleep(polling_interval)
    except CancelledError:  # TODO: Better control for aync loop
        logger.info("Logging cancelled")


def async_function_from(output_function):
    async def async_output_function(measurement):
        output_function(measurement)
    return async_output_function


def record_gpu_to(output_function, async_loop, deviceCount=1, polling_interval=1):
    asyncio.set_event_loop(async_loop)
    pynvml.nvmlInit()
    logger.info("Driver Version: {}".format(nativestr(pynvml.nvmlSystemGetDriverVersion())))
    async_loop.run_until_complete(output_function)
    logger.info("Shutting down driver")
    pynvml.nvmlShutdown()


def start_record_gpu_to(output_function):
    new_loop = asyncio.new_event_loop()
    task = new_loop.create_task(record_measurements(async_function_from(output_function), polling_interval=1))
    t = Thread(target=record_gpu_to, args=(task, new_loop))
    t.start()
    return task


def main():

    try:
        t, loop, task_task = start_record_gpu_to(print)
        time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Cancelling")
        task_task.cancel()
    # loop.stop()
    # loop.close()
    # finally:
    #     print("Closing")
    #     loop.stop()
    #     loop.close()


if __name__=="__main__":
    main()