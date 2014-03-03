import types
from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
import json
from StringIO import StringIO
from utils import uni

class ModManager(models.Manager):
    def get_or_create_ns(self, **kwargs):
        try:
            obj=self.get(**kwargs)
            return obj,False
        except self.model.DoesNotExist:
            obj=self.model(**kwargs)
            return obj, True

class MaxObjectsLimitReached(Exception):
    pass

class Auditable (models.Model):
    created=models.DateTimeField(_('Created'), auto_now_add=True, editable=False)
    modified=models.DateTimeField(_('Modified'), auto_now=True, editable=False)
    created_by=models.ForeignKey(User, verbose_name=_('Created by'),
                                 null=True, blank=True, 
                                 related_name="%(class)s_created_set", 
                                 editable=False)
    modified_by=models.ForeignKey(User, verbose_name=_('Modified by'),
                                  null=True, blank=True, 
                                  related_name="%(class)s_modified_set", editable=False)
    updates=models.BigIntegerField(_('Updates'), null=False, default=0, editable=False)
    views=models.BigIntegerField(_('Views'), null=False, default=0, editable=False)
    
    def update_user(self, user):
        if user and not user.is_anonymous():
            if self.pk:
                self.modified_by=user
            else:
                self.modified_by=user
                self.created_by=user
    
    def save(self, *args, **kwargs):
        user=kwargs.pop('user', None)
        if isinstance(user, types.StringTypes):
            try:
                user=User.objects.get(username=user)
            except User.DoesNotExist:
                user=None
        self.update_user(user)
        if not self.pk and not self.is_within_limit(self.created_by):
            raise MaxObjectsLimitReached(_('Reached limit of maximum objects per user'))
        if self.pk:
            self.updates+=1
        super(Auditable,self).save(*args, **kwargs)
    objects=ModManager()
    
    def can_edit(self, user):
        # open for more more complex policy
        if not user:
            return False
        return user==self.created_by
    class Meta ():
        abstract=True;
        
        
    #limits maximum number of objects per user     
    max_objects=None
    max_objects_higher=None
    
    def get_count(self, user):
        return self.__class__.objects.filter(created_by=user).count()
        
    def get_limit(self, user):
        if user and user.has_perm('myplaces.higher_limit_'+ self._meta.module_name):
            return self.max_objects_higher
        return self.max_objects
        
    def is_within_limit(self, user):
        limit=self.get_limit(user)
        if not limit:
            return True
        if self.get_count(user)>=limit:
            return False
        return True
    


class PlacesGroup(Auditable):
    max_objects=29
    max_object_higher=99
    
    name=models.CharField(_('Name'), max_length=80, null=False, blank=False)
    description=models.CharField(_('Description'), max_length=200, null=True, blank=True)
    private=models.BooleanField(_('Private'), default=False)
    
    def __unicode__(self):
        return self.name
    
    def as_geojson(self,  places=None, details=False, user=None):
        str_file=StringIO()
        str_file.write('{"type":"FeatureCollection", "features":[')
        if not places:
            places=self.places.all().order_by('name')
        length=places.count()
        for pos,p in enumerate(places) :
            str_file.write(p.as_geojson(details,user))
            if pos < length-1:
                str_file.write(', ')
        str_file.write(']}')
        return str_file.getvalue()
        
    class Meta:
        verbose_name=_('Places Group')
        verbose_name_plural=_('Places Groups')
        permissions = (
            ("import_placesgroup", "Can import places data from CSV"),
            ("higher_limit_placesgroup", "Can create more placesgroup objects")
        )
    
class Address(Auditable):
    max_objects=29*199
    max_objects_higher=99*499
    
    street=models.CharField(_('Street'), max_length=80, null=True, blank=True)
    city=models.CharField(_('City'), max_length=80, null=True, blank=True)
    county=models.CharField(_('County'), max_length=80, null=True, blank=True)
    state=models.CharField(_('State'), max_length=80, null=True, blank=True)
    postal_code=models.CharField(_('Postal Code'), max_length=10, null=True, blank=True)
    country=models.CharField(_('Country'), max_length=40, null=True, blank=True)
    unformatted=models.CharField(_('Unformatted Address'), max_length=200, null=True, blank=True)
    email=models.EmailField(_('Email'), max_length=80, null=True, blank=True)
    phone=models.CharField(_('Phone Number'), max_length=40, null=True, blank=True)
    #-------------------------------------------------------------
    
    def __unicode__(self):
        
        addr=[]
        def append_if_exists(item):
            if item:
                addr.append(uni(item))
        append_if_exists(self.street)
        append_if_exists( u'%s %s'% (uni(self.postal_code), uni(self.city)) if self.postal_code else self.city)
        append_if_exists(self.county)
        append_if_exists(self.state)
        append_if_exists(self.country)
            
        if addr:
            return u', '.join(addr)
        else:
            return self.unformatted or ''
            
    class Meta:
        verbose_name=_('Address')
        verbose_name_plural=_('Addresses')
        permissions= (
                      ("higher_limit_address", "Can create more address objects"),
                      )
    
class Place(Auditable):
    max_objects=199
    max_objects_higher=499
    
    def get_count(self,user):
        return Place.objects.filter(created_by=user, group=self.group).count()
    
    
    name=models.CharField(_('Name'), max_length=80, null=False, blank=False)
    description=models.CharField(_('Description'), max_length=200, null=True, blank=True)
    group=models.ForeignKey(PlacesGroup, blank=False, null=False, related_name="places", 
                            verbose_name=_('Group'))
    position=models.PointField(_('Coordinates'), srid=4326, null=False, blank=False)
    #TODO: Change to OnetoOneFields - this will require chnange of test data
    address=models.OneToOneField(Address, related_name="place", verbose_name=_('Address'),null=True, blank=True)
    url=models.URLField(_('WWW Link'), max_length=200, null=True, blank=True )
    
    objects = models.GeoManager()
    
    def as_geojson(self, details=False, user=None):
        
        data={'type':'Feature',
              'id': self.id,
              'geometry': {'type':'Point', 'coordinates':[self.position.x, self.position.y]},
              'properties':{'name':self.name,}}
        if self.url:
                data['properties']['url']=self.url
        if self.can_edit(user) and not details:
            data['properties']['group']=self.group.id
        if self.description:
            if details:
                data['properties']['description']=self.description
            else:
                data['properties']['description'] =self.description if len(self.description)<=80 else \
                    self.description[:77]+'...'   
        if self.address:
            if details:
                adr={}
                for name in ['street', 'city', 'county', 'state', 'country', 'postal_code', 'phone', 'email']:
                    if getattr(self.address, name):
                        adr[name]=getattr(self.address,name)
            else:
                adr=self.address.__unicode__()
            data['properties']['address']=adr
        
        return json.dumps(data)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name=_('Place')
        verbose_name_plural=_('Places')
        permissions=(('geocode_place', 'Can use geocoding API'),
                     ("higher_limit_place", "Can create more place objects"),
                     )
    