MyPlaces is a platform for presenting geographical information (initially mainly places) on maps.
It's based on django, geo-django, postgis and uses OpenStreetMap data and services.

Run in Docker
=============
Easy way how to test it is to start application in docker (install docker-engine and docker-compose as described here https://docs.docker.com/compose/install/):

```
cd deploy/docker
docker-compose build
docker-compose run --rm web deploy/docker/init.sh # if fails try second time
docker-compose up

```

Openshift
=========

Live demo version is available on Openshift PaaS service:
http://myplaces-ivanovo.rhcloud.com

Deployment on openshift requires custom python cartridge from here: https://github.com/gsterjov/openshift-advanced-python-cartridge

Plus couple of tweeks were needed:
- lxml installation is causing problems - better to install it manually from ssh app shell
- ssh shell is not running python, this helped:   
    `rhc env set LD_LIBRARY_PATH /opt/rh/python27/root/usr/lib64 -a myplaces`
- Have to set custom app server
	  `rhc env set OPENSHIFT_PYTHON_SERVER=custom -a myplaces`
- In ssh shell :
```
cd  /var/lib/openshift/569218b07628e1059100005b/advanced-python//usr/nginx/versions/1.4/conf
cp nginx.wsgiref.conf.erb nginx.custom.conf.erb
cd $OPENSHIFT_REPO_DIR 
python manage.py createsuperuser
python manage.py loaddata myplaces/fixtures/default_groups.json

```

Manual Install
==============
Application can be installed in blank linux (Debian/Ubuntu). 
There are 3 servers which should run:
- web -  this is Django application - can be deployed as usual (WSGI application), or manage.py runserver for testing purposes
- socketio server - ./runsocketio.py
- remote processes server - ./ manage.py process_server


Below are approximate steps to make it 
running.

It is bit outdated will need some updates.

Prerequisities
--------------
Scrips below are for ubuntu 14.04+/Debian - do not forget to upgrade your install to latest version - apt-get update; apt-get dist-upgrade
Scripts shall be run under root (if logged in under other user use sudo)
SMTP server to send email
You can start one (lightweight, send only) on your server as per instructions https://library.linode.com/email/exim/send-only-mta-ubuntu-12.04-precise-pangolin
 

 #Server will need only ssh, http and htts ports 
 #on ubuntu you can use ufw 
 ufw allow ssh
 ufw allow http
 ufw allow https
 ufw enable

 #nginx - we will need relativelly recent version for websocket support
 apt-get install -y python-software-properties
 add-apt-repository ppa:nginx/stable
 apt-get update
 apt-get install -y nginx-light
 /etc/init.d/nginx start
 #you can test not via browser
 
 
 apt-get install -y build-essential
 apt-get install -y python-pip
 #headers to compile some python packages
 apt-get install -y libevent-dev libxml2-dev libxslt1-dev libjpeg-dev libfreetype6-dev zlib1g-dev python-dev
 
 #postgres database 9.3+ recommended postis 2.1, python driver, postgis
 apt-get install -y postgresql python-psycopg2  postgresql-9.3-postgis-2.1  postgresql-contrib

 apt-get install -y git
 apt-get install -y gdal-bin  libproj-dev

 

Install:
-------
```
Creating DB - switch to postgres user
 su postgres
 createuser -PRSd maps
 #for running tests need superuser rights for postgis
 #createuser -Ps maps
 createdb -O maps -e maps
 psql -a -c "CREATE EXTENSION unaccent;"   maps
 psql -a -c "CREATE EXTENSION postgis;"   maps
 exit
 
#create user to run python backend
 adduser ivan
 usermod -G postgres,www-data -a ivan

Now can install the code
 #getcode from github
 cd /opt
 git clone https://github.com/izderadicka/myplaces.git maps
 cd maps

 #create directory for static data
 mkdir /var/www
 chown root:www-data /var/www
 ls -la /var
 chmod g+w /var/www
 
 #create ssl certificate and pk
 mkdir /etc/nginx/ssl
 # get certificate from startssl - guide is here http://www.lognormal.com/blog/2013/06/22/setting-up-ssl-on-nginx/
 
 #configure nginx
 mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf.old
 cp deploy/nginx/nginx.conf /etc/nginx/
 cp deploy/nginx/sites-available/* /etc/nginx/sites-available/
 /etc/init.d/nginx reload
 #tail /var/log/nginx/error.log

 #create dir for logs
 mkdir /var/log/myplace
 chown ivan:www-data /var/log/myplaces

 # install dependencies
 pip -r requirements.txt


#create db, admin account and load initial groups

 ./manage.py migrate
 ./manage.py loaddata myplaces/fixtures/default_groups.json

 #log as user, who will run backend servers
 su ivan
 
 #optionally run tests
 ./manage.py test myplaces


 #collect static data
 ./manage.py collectstatic
```


edit settings.py
- change DEBUG to False !!!
- set log location (file log handled in LOGGING)
- plus modify any other settings as appropriate (email address etc.)

test server:
 ./manage.py runserver 0.0.0.0:8000  #  now should be able to see something in browser http://host_name:8000
 # stop it Crtl-C
 
prepare script for running backend servers and start them
 cp deploy/mp-servers /usr/local/bin
 nano /usr/local/bin/mp-servers #edit base directory, python interpreter
 mp-servers start
 mp-servers status # should see two lines for two processes
 
start browser - go to site url

login to /admin - change site name and url  to appropriate values 
 
Versions History:
=================

0.1 Initial version
- provides collections of places, complete interface to manage and view
- imports/exports in CSV,GPX, GEOJSON formats
- voronoi diagram visualization
- now running live at http://my-places.eu

0.1.2 Updated for Django 1.8 and Docker environment

License:- "8000:8000"
=========
[BSD license](http://opensource.org/licenses/BSD-3-Clause) (same as Django)
