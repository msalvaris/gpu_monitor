from pynvml import *


def nativestr(s):
    if isinstance(s, text_type):
        return s
    return s.decode('utf-8', 'replace')

def main():
    nvmlInit()
    print("Driver Version: {}".format(nativestr(nvmlSystemGetDriverVersion())))
    deviceCount = nvmlDeviceGetCount()
    for i in range(deviceCount):
        handle = nvmlDeviceGetHandleByIndex(i)
        print("Device {} : {}".format(i, nativestr(nvmlDeviceGetName(handle))))

    nvmlShutdown()

if __name__=="__main__":
    main()