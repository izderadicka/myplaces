#!/bin/bash
set -ex

DB_PASSWORD=${MAPS_DB_PASSWORD:-maps}
DB_USER=${MAPS_DB_USER:-maps}
DB_NAME=${MAPS_DB_NAME:-maps}
DB_HOST=${MAPS_DB_HOST:-localhost}
DB_PORT=${MAPS_DB_PORT:-5432}

#TEST CONNECTION
ADMIN_EXISTS=$(python manage.py shell<<EOF
from django.contrib.auth.models import User
User.objects.get(username='admin'); print 'ADMIN_EXISTS'
EOF
)

init() {
  echo "Initializing"
  
  # Create a PostgreSQL role named ``maps``  and
  # then create a database `maps` owned by the ``maps`` role.
  python manage.py migrate
  python manage.py loaddata myplaces/fixtures/default_groups.json
  python manage.py shell <<EOF
from django.contrib.auth.models import User
User.objects.create_superuser('admin', 'admin@example.com', '${MAPS_ADMIN_PASSWORD:-admin}')
EOF
}

if [[ ! -f myplaces/voronoi.so ]]; then 
  python setup.py build_ext --inplace
fi

if echo $ADMIN_EXISTS|grep ADMIN_EXISTS; then
  echo "App Already initiallized"
  
else
  echo "App Need initialization"
  init
fi

#main entry point
python manage.py process_server &
python runsocketio.py 0.0.0.0:8008
 
