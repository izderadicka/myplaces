'''
Created on May 28, 2013

@author: ivan
'''

from django.contrib.gis import admin
from models import *

class PlaceAdmin(admin.OSMGeoAdmin):  
    search_fields=('name',)
    
class GroupAdmin(admin.ModelAdmin):
    search_fields=('name',)
   
class AddressAdmin(admin.ModelAdmin):
    search_fields=('street', 'city', 'unformatted')
    
admin.site.register(Place, PlaceAdmin)
admin.site.register(PlacesGroup, GroupAdmin)
admin.site.register(Address, AddressAdmin)    