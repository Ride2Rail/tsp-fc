FROM python:3.8

COPY tsp.py /home/tsp-fc/tsp.py

COPY ./requirements.txt /home/tsp/requirements.txt
RUN pip install -r /home/tsp/requirements.txt

ENTRYPOINT ['tsp.py']
