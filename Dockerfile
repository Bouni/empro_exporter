FROM python:slim

ENV PYTHONUNBUFFERED=1

RUN mkdir /app
WORKDIR /app

RUN apt-get update \
&& apt-get install gcc -y \
&& apt-get clean

COPY requirements.txt ./
COPY empro.py ./
COPY registers.py ./

RUN pip install --no-cache-dir -r requirements.txt
