MyPlaces is a platform for presenting geographical information (initially mainly places) on maps.
It's based on django, geo-django, postgis and uses OpenStreetMap data and services.


Prerequisities
==============
Scrips below are for ubuntu 12.04+/Debian - do not forget to upgrade your install to latest version - apt-get update; apt-get dist-upgrade
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
 apt-get install -y python-dev
 add-apt-repository ppa:nginx/stable
 apt-get update
 apt-get install -y nginx-light
 /etc/init.d/nginx start
 #you can test not via browser
 apt-get install -y build-essential
 apt-get install -y python-pip
 #headers to compile some python packages
 apt-get install -y libevent-dev libxml2-dev libxslt1-dev libjpeg-dev libfreetype6-dev zlib1g-dev
 ln -s /usr/lib/`uname -i`-linux-gnu/libfreetype.so /usr/lib/
 ln -s /usr/lib/`uname -i`-linux-gnu/libjpeg.so /usr/lib/
 ln -s /usr/lib/`uname -i`-linux-gnu/libz.so /usr/lib/
 
 #numpy and matplotlib would be quicker from distro packages
 apt-get install -y python-numpy python-matplotlib
 #postgres database 9.1+ recommended, python driver, postgis
 apt-get install -y postgresql python-psycopg2 postgresql-9.1-postgis postgresql-contrib-9.1

 apt-get install -y git

 apt-get install gdal-bin

 #create user to run python backend
 adduser ivan
 usermod -G postgres,www-data -a ivan

 #assure you have libzmq >= 3.2.3, may install it from source (ubuntu 13.04 has 2.2) - http://zeromq.org/intro:get-the-software
 #may not be needed
 apt-get install -y  libtool  autoconf  automake
 apt-get install -y  uuid-dev
 wget http://download.zeromq.org/zeromq-3.2.4.tar.gz
 tar xvzf zeromq-3.2.4.tar.gz 
 cd zeromq-3.2.4/
 ./configure
 make
 make install
 ldconfig

Install:
========
```
Creating DB - switch to postgres user
 su postgres
 createuser -PRSd maps
 createdb -O maps -e maps
 psql -a -c "CREATE EXTENSION unaccent;"   maps
 psql -d maps -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql
 psql -d maps -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql
 psql -d maps -f /usr/share/postgresql/9.1/contrib/postgis_comments.sql
 #template_postgis is only needed for running tests
 createdb -T maps template_postgis
 psql -c "UPDATE pg_database SET datistemplate = TRUE WHERE datname = 'template_postgis';"
 exit

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
 pip -r requirements.pip


 #log as user, who will run backend servers
 su ivan
 #optionally run tests
 ./manage.py test myplaces

 #create db, admin account and load initial groups
 ./manage.py syncdb
 ./manage.py loaddata myplaces/fixtures/default_groups.json

 #collect static data
 ./manage.py collectstatic

edit settings.py
- change DEBUG to False !!!
- set log location (file log handled in LOGGING)
- plus modify any other settings as appropriate (email address etc.)

test server:
 ./manage.py runserver_socketio  #  now should be able to see something in browser
 exit
 
prepare script for running backend server and start them
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

License:
=========
[BSD license](http://opensource.org/licenses/BSD-3-Clause) (same as Django)
