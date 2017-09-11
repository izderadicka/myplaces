#!/bin/sh
python setup.py build_ext --inplace
python manage.py migrate
python manage.py loaddata myplaces/fixtures/default_groups.json
python manage.py createsuperuser
