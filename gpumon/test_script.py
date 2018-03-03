import pynvml
from datetime import datetime

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
        return pynvml.nvmlDeviceGetUtilizationRates(device_handle).mem
    except pynvml.NVMLError:
        return None


def power_for(device_handle):
    try:
        return pynvml.nvmlDeviceGetPowerUsage(device_handle)
    except pynvml.NVMLError:
        return None


def temperature_for(device_handle):
    try:
        return pynvml.nvmlDeviceGetTemperature(device_handle)
    except pynvml.NVMLError:
        return None


def main():
    pynvml.nvmlInit()
    print("Driver Version: {}".format(nativestr(pynvml.nvmlSystemGetDriverVersion())))
    deviceCount = pynvml.nvmlDeviceGetCount()
    try:
        for cc in range(100):
            print(str(datetime.now())),
            for i in range(deviceCount):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                print([func(handle) for func in (device_name_for, mem_for, utilization_for, mem_utilization_for, power_for, temperature_for)])
                # print("Device {} : {}".format(i, nativestr(nvmlDeviceGetName(handle))))
    except KeyboardInterrupt:
        pynvml.nvmlShutdown()

if __name__=="__main__":
    main()