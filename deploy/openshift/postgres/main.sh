#!/bin/bash
set -ex
BIN_DIR="/usr/lib/postgresql/9.3/bin"
DATA_DIR="/var/lib/postgresql/9.3/main"
TEST_FILE="$DATA_DIR/.init_done"
DB_PROCESS="$BIN_DIR/postgres -D $DATA_DIR -c config_file=/etc/postgresql/9.3/main/postgresql.conf"

# set current user as postgres
if ! whoami &> /dev/null; then
  if [ -w /etc/passwd ]; then
    grep -v ^postgres /etc/passwd > "/tmp/passwd"
    echo "postgres:x:$(id -u):0:postgres user:${HOME}:/sbin/nologin" >> /tmp/passwd
    echo "" > /etc/passwd
    cat /tmp/passwd >> /etc/passwd
    rm /tmp/passwd
  fi
fi

whoami

mkdir /tmp/postgresql
mkdir /tmp/postgresql/9.3-main.pg_stat_tmp


init() {
  echo "Initializing"
  if [[ -z "${MAPS_DB_PASSWORD}" ]]; then
    echo "Empty db password"
    exit 1
  fi
  # Create a PostgreSQL role named ``maps``  and
  # then create a database `maps` owned by the ``maps`` role.
  
  mkdir -p $DATA_DIR
  LANG=en_US.UTF-8 $BIN_DIR/initdb -D $DATA_DIR
  
  $DB_PROCESS &
  DB_PID=$!
  sleep 1
  psql --command "CREATE USER maps WITH SUPERUSER PASSWORD '${MAPS_DB_PASSWORD}';"
  createdb -O maps maps
  psql -a -c "CREATE EXTENSION unaccent;"   maps
  psql -a -c "CREATE EXTENSION postgis;"   maps
  kill -INT $DB_PID
  wait
  touch $TEST_FILE
  }


if [[ ! -f $TEST_FILE ]]; then
  echo "DB Need initialization"
  init
else
  echo "DB Already initiallized"
fi

#main entry point
exec $DB_PROCESS