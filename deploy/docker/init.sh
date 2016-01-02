#!/bin/sh

python manage.py migrate
python manage.py loaddata myplaces/fixtures/default_groups.json
python manage.py createsuperuser
