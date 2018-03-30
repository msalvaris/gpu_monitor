# GPU Monitor
This is a library and script for monitoring GPUs on a single machine and across a cluster. You can use it to record various GPU measurements during a specific period using the context based logger or continuously. The context logger can either record to a file which can be read back into a dataframe or to an influxdb database. The influxdb database can then be accessed using the python influxdb client or can be viewed in realtime using dashboards such as Grafana


## Installation

To install simply clone the repository

```bash
git clone https://github.com/msalvaris/gpu_monitor.git
```

Then install it:
```bash
pip install -e /path/to/repo
```

For now I recommend the -e flag since it is in active development and 
will be easy to update by pulling the latest changes from the repo.

## Usage
Example of running gpu monitor in Jupyter notebook
```python
from gpumon import log_context
from bokeh.io import output_notebook, show

output_notebook()# Without this the plot won't show in Jupyter notebook

with log_context('log.txt') as log:
    # GPU code
    
show(log.plot())# Will plot the utilisation during the context

log()# Will return dataframe with all the logged properties
```
