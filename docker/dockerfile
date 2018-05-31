FROM nvidia/cuda:9.0-base

ENV CONDA_DIR /opt/conda
ENV PATH $CONDA_DIR/bin:$PATH

RUN mkdir -p $CONDA_DIR && \
    echo export PATH=$CONDA_DIR/bin:'$PATH' > /etc/profile.d/conda.sh && \
    apt-get update && \
    apt-get install -y wget git g++ bzip2 && \
    wget --quiet https://repo.continuum.io/miniconda/Miniconda3-4.2.12-Linux-x86_64.sh && \
    echo "c59b3dd3cad550ac7596e0d599b91e75d88826db132e4146030ef471bb434e9a *Miniconda3-4.2.12-Linux-x86_64.sh" | sha256sum -c - && \
    /bin/bash /Miniconda3-4.2.12-Linux-x86_64.sh -f -b -p $CONDA_DIR && \
    rm Miniconda3-4.2.12-Linux-x86_64.sh

# Python
ARG python_version=3.6

ENV PATH /opt/conda/envs/py$PYTHON_VERSION/bin:$PATH

RUN mkdir -p /src

WORKDIR /src

RUN conda install -y python=${python_version} && \
    pip install --upgrade pip && \
	git clone https://github.com/msalvaris/gpu_monitor.git && \
	pip install -r gpu_monitor/requirements.txt && \
	pip install --no-deps -e gpu_monitor && \
    conda clean -yt

