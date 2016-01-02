FROM python:2.7
ENV PYTHONUNBUFFERED 1
RUN apt-get update
RUN apt-get install -y libproj-dev gdal-bin
RUN mkdir /opt/maps
WORKDIR /opt/maps
ADD ./requirements.txt /opt/maps/
RUN pip install -r requirements.txt
