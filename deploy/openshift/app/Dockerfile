FROM python:2.7
MAINTAINER ivan@zderadicka.eu
ENV PYTHONUNBUFFERED 1
RUN mkdir /opt/map
ADD myplaces socketio_app *.py requirements.tx 
RUN apt-get update &&\
    apt-get install -y libproj-dev gdal-bin
s

WORKDIR /opt/maps
RUN pip install -r requirements.txt
