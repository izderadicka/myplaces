FROM python:2.7
MAINTAINER ivan@zderadicka.eu
ENV PYTHONUNBUFFERED 1
RUN apt-get update &&\
    apt-get install -y libproj-dev gdal-bin

ADD requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

RUN mkdir /opt/maps
ADD *.py /opt/maps/
ADD myplaces /opt/maps/myplaces/
ADD  socketio_app/ /opt/maps/socketio_app/
RUN adduser maps &&\
    chown -R maps:root /opt/maps &&\
    chmod -R g+w /opt/maps

WORKDIR /opt/maps


ADD deploy/openshift/app/main.sh /opt/maps

EXPOSE 8008
USER maps
CMD ./main.sh
