#!/bin/bash
mkdir data
chmod 777 data
sysctl -w vm.max_map_count=262144
docker-compose up
