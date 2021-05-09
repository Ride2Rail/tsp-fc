#!/bin/bash

# Start tsp-fc service
docker-compose up -d

# Check if everything is up and running
sleep 5
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://127.0.0.1:5002/test)" != "200" ]]; do
	sleep 2
done

# Stop tsp-fc
#docker-compose down
