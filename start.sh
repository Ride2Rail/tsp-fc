#!/bin/bash
app="tsp-fc"
docker build -t ${app} .
docker run -d -p 5002:5002 \
  --name=${app} \
  -v $PWD:/app ${app}
