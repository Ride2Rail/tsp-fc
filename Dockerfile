FROM python:3.8

ENV APP_NAME=tsp.py
COPY /code/"$APP_NAME" /code/"$APP_NAME"
COPY /code/tsp.conf /code/tsp.conf

WORKDIR /code

ENV FLASK_APP="$APP_NAME"
ENV FLASK_RUN_HOST=0.0.0.0

RUN pip3 install --no-cache-dir --upgrade pip

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 5002

CMD ["flask", "run"]
