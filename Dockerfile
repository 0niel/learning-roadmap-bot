FROM python:3.9-slim-buster AS builder
RUN mkdir /app

WORKDIR /app

COPY requirements.txt .

ADD plans.db /app/plans.db

RUN apt-get update

# Need to curriculum-parser
RUN apt-get install -y libsm6 libxext6 libgl1-mesa-dev
RUN apt-get install -y libglib2.0-0

RUN pip install --upgrade pip \
  && pip install --upgrade setuptools \
  && pip install -r requirements.txt

COPY bot /app/bot

CMD python -m bot
