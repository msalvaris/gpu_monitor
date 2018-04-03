# GPU Monitor
This is a library and script for monitoring GPUs on a single machine and across a cluster. You can use it to record various GPU measurements during a specific period using the context based logger or continuously using the gpumon command. The context logger can either record to a file which can be read back into a dataframe or to an influxdb database. Data from the influxdb database can then be accessed using the python influxdb client or can be viewed in realtime using dashboards such as Grafana. Examples created in Juypyter notebooks can be found [here](examples/notebooks)


Below is an example dashboard using the InfluxDB log context and a Grafana dashboard

<p align="center">
  <img src="static/gpu_dashboard.gif" alt="Grafana GPU Dashboard"/>
</p>


## Installation

To install simply either clone the repository

```bash
git clone https://github.com/msalvaris/gpu_monitor.git
```

Then install it:
```bash
pip install -e /path/to/repo
```
For now I recommend the -e flag since it is in active development and 
will be easy to update by pulling the latest changes from the repo.


Or just install using pip

```bash
pip install git+https://github.com/msalvaris/gpu_monitor.git
```

## Usage
### Running gpu monitor in Jupyter notebook with file based log context
```python
from gpumon.file import log_context
from bokeh.io import output_notebook, show

output_notebook()# Without this the plot won't show in Jupyter notebook

with log_context('log.txt') as log:
    # GPU code
    
show(log.plot())# Will plot the utilisation during the context

log()# Will return dataframe with all the logged properties
```
[Click here to see the example notebook]()

### Running gpu monitor in Jupyter notebook with InfluxDB based log context
To do this you need to set up and [install InfluxDB](https://docs.influxdata.com/influxdb/v1.5/introduction/installation/) and [Grafana](http://docs.grafana.org/installation/). 
There are many ways to install and run InfluxDB and Grafana in this example we will be using Docker containers and docker-compose.

If you haven't got docker-compose installed run look [here](https://docs.docker.com/compose/install/)

You must be also be able to execute the docker commands without the requirement of sudo. To do this in Ubuntu execute the following
```bash
sudo groupadd docker
sudo usermod -aG docker $USER
```

If you haven't downloaded the whole repo then download the [scripts directory](scripts). In there should be three files  
The file *example.env* contains the following variables:  
INFLUXDB_DB=gpudb  
INFLUXDB_USER=admin  
INFLUXDB_USER_PASSWORD=password  
INFLUXDB_ADMIN_ENABLED=true  
GF_SECURITY_ADMIN_PASSWORD=password  
GRAFANA_DATA_LOCATION=/tmp/grafana  
INFLUXDB_DATA_LOCATION=/tmp/influxdb  

Please change them to appropriate values. The data location entries will tell Grafana and InfluxDB where to store their data so that when the containers are destroyed the data remains.  
Once you have edited it rename *example.env* to *.env* 

Now inside the folder that contains the file you can run the command below and it will give you the various commands you can execute.
```bash
make
```

To start InfluxDB and Grafana you run  
```bash
make run
```

Now in your Jupyter notebook simply add these lines
```python
from gpumon.influxdb import log_context

with log_context('localhost', 'admin', 'password', 'gpudb', 'gpuseries'):
	# GPU Code

```
Make sure you replace the values in the call to the log_context with the appropriate values.
*gpudata* is the name of the database and *gpuseries* is the name we have given to our series feel free to replace these.
If the database name given in the context isn't the same as the one supplied in the .env file a new database will be created.  
Have a look at [this notebook](examples/notebooks/InfluxDBLoggerExample.ipynb) for a full example.  


If you want to use the CLI version run the following command:
```bash
gpumon localhost admin password gpudb --series_name=gpuseries
```

The above command will connect to the influxdb database running on localhost with   
user=admin
password=password
database=gpudb
series_name=gpuseries

Now GPU information should be flowing to your database. You will also need to set up your Grafana dashboard.  
To do that log in to Grafana by pointing a browser to the IP of your VM or computer on port 3000. *If you are executing on a VM make sure that port is open*.  
Once there log in with the credentials you specified in your .env file.

You will need to set up the data source. Below is an example screen-shot of the datasource config

<p align="center">
  <img src="static/influxdb_config.png" alt="Datasource config"/>
</p>

Once that is set up you will need to also set up your dashboard. The dashboard shown in the gif above can be found [here](dashboards/GPUDashboard.json)