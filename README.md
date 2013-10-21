MyPlaces is a platform for presenting geographical information (initially mainly places) on maps.
It's based on django, geo-django, postgis and uses OpenStreetMap data and services.


Install:
========
 # debian/ubuntu 
 sudo apt-get build-essential
 sudo apt-get install python-pip
 sudo apt-get install libevent-dev
 sudo pip -r requirements.pip
 #numpy and matplotlib would be quicker from distro packages
 sudo apt-get install python-numpy python-matplotlib

 #assure you have libzmq >= 3.2.3, may install it from source (ubuntu 13.04 has 2.2) - http://zeromq.org/intro:get-the-software
 
Versions History:
=================

0.1 - Initial version - under construction - use at your own risk 

License:
=========
[BSD license](http://opensource.org/licenses/BSD-3-Clause) (same as Django)
