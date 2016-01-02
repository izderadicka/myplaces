#!/bin/bash

cd $1
python runsocketio.py &
python manage.py process_server &
python manage.py runserver 0.0.0.0:8000

# kill running servers
pkill -f runsocketio.py
pkill -f process_server