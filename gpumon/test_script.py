from pynvml import *


def main():
    nvmlInit()
    print("Driver Version: {}".format(nvmlSystemGetDriverVersion()))
    deviceCount = nvmlDeviceGetCount()
    for i in range(deviceCount):
        handle = nvmlDeviceGetHandleByIndex(i)
        print("Device {} : {}".format(i, nvmlDeviceGetName(handle)))

    nvmlShutdown()

if __name__=="__main__":
    main()