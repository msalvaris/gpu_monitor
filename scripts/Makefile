.ONESHELL:
SHELL := /bin/bash

define PROJECT_HELP_MSG
Usage:
	make help                           show this message
	make run							start influx container and grafana container
	make stop							stop all containers
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

clean: remove
	grafana=$(dotenv get GRAFANA_DATA_LOCATION| cut -d '=' -f 2)
	influxdb=$(dotenv get INFLUXDB_DATA_LOCATION| cut -d '=' -f 2)
	echo grafana

.PHONY: help run stop remove delete
