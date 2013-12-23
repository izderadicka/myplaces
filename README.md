MyPlaces is a platform for presenting geographical information (initially mainly places) on maps.
It's based on django, geo-django, postgis and uses OpenStreetMap data and services.


Prerequisities
==============
Scrips below are for ubuntu 12.04+/Debian - do not forget to upgrade your install to latest version - apt-get update; apt-get dist-upgrade

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
 apt-get install -y libevent-dev libxml2-dev libxslt1-dev
 
 #numpy and matplotlib would be quicker from distro packages
 apt-get install -y python-numpy python-matplotlib
 #postgres database 9.1+ recommended, python driver, postgis
 apt-get install -y postgresql python-psycopg2 postgis

 apt-get install -y git

 #create user to run python backend
 adduser ivan
 usermod -G postgres,www-data -a ivan

 #assure you have libzmq >= 3.2.3, may install it from source (ubuntu 13.04 has 2.2) - http://zeromq.org/intro:get-the-software
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
 # debian/ubuntu 
 sudo pip -r requirements.pip
 


 
Versions History:
=================

0.1 - Initial version - under construction - use at your own risk 

License:
=========
[BSD license](http://opensource.org/licenses/BSD-3-Clause) (same as Django)
