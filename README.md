# GPU Monitor
## Install

To install simply clone the repository

```bash
git clone https://github.com/msalvaris/gpu_monitor.git
```

Then install it:
```bash
pip install -e /path/to/repo
```

For now I recommend the -e flag since it is in active developement and 
will be easy to update by pulling the latest changes from the repo

If you get any errors try the following:
```bash
pip install -e /path/to/repo
```

## Usage
Example of running gpu monitor in Jupyter notebook
```python
from gpumon import file_log_context
from bokeh.io import output_notebook, show

output_notebook()# Without this the plot won't show in Jupyter notebook

with file_log_context('log.txt') as log:
    # GPU code
    
show(log.plot())# Will plot the utilisation during the context

log()# Will return dataframe with all the logged properties
```
