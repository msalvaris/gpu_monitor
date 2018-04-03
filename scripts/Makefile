.ONESHELL:
SHELL := /bin/bash

define PROJECT_HELP_MSG
Usage:
	make help                           show this message
	make run                            start influx container and grafana container
	make stop                           stop all containers
	make remove                         remove all containers
	make clean                          delete grafana and influxdb data
endef
export PROJECT_HELP_MSG

help:
	@echo "$$PROJECT_HELP_MSG" | less

run:
	@echo "Starting InfluxDB and Grafana"
	docker-compose up -d

stop:
	docker-compose down

remove:
	docker-compose down --rmi all

clean:
	$(eval grafana:=$(shell dotenv get GRAFANA_DATA_LOCATION| cut -d '=' -f 2))
	$(eval influxdb:=$(shell dotenv get INFLUXDB_DATA_LOCATION| cut -d '=' -f 2))
	@echo "Deleting $(grafana)"
	@rm -rf $(grafana)
	@echo "Deleting $(influxdb)"
	@rm -rf $(influxdb)

.PHONY: help run stop remove clean
