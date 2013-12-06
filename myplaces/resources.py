'''
Created on Aug 19, 2013

@author: ivan
'''
import re
from models import Place, PlacesGroup, Address, MaxObjectsLimitReached
from rest_framework import serializers, viewsets, permissions, exceptions,\
    fields, status
from rest_framework.views import APIView
from rest_framework.response import Response
    
import django_filters
from django.contrib.gis.measure import Distance
from django.contrib.gis.geos import  Point
from rest2backbone.resources import ModelSerializer, ViewSetWithIndex
import rest_framework
from django.utils.translation import ugettext_lazy as _
import itertools
from django.forms import widgets
from django.core.exceptions import ValidationError
import widgets as custom_widgets
from rest2backbone import widgets as r2b_widgets
from django.db.models.query_utils import Q
from myplaces.models import MaxObjectsLimitReached


class FilterError(exceptions.APIException):
    status_code=400
    detail="Invalid filter expression"

class CreatedOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:            
            return True
        if not obj.created_by:
            return True
        else:
            return obj.created_by== request.user

class UserMixin():
    def pre_save(self, obj):
        if hasattr(self.request, 'user'):
            obj.update_user(self.request.user)
            
    permission_classes=(CreatedOrReadOnly,permissions.DjangoModelPermissionsOrAnonReadOnly)
    
class LimitCreateMixin(object):
    """
    Limits number of created objects per user
    """
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)

        if serializer.is_valid():
            self.pre_save(serializer.object)
            try:
                self.object = serializer.save(force_insert=True, user=request.user)
            except MaxObjectsLimitReached:
                return Response({'':[_('Reached maximum number of records per user')]}, status=status.HTTP_400_BAD_REQUEST)
            self.post_save(self.object, created=True)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HLSerializer(serializers.HyperlinkedModelSerializer):
    url_field_name='instance_url'
    def get_default_fields(self):
        fields = super(serializers.HyperlinkedModelSerializer, self).get_default_fields()

        if self.opts.view_name is None:
            self.opts.view_name = self._get_default_view_name(self.opts.model)

        if self.url_field_name not in fields:
            url_field = serializers.HyperlinkedIdentityField(
                view_name=self.opts.view_name,
                lookup_field=self.opts.lookup_field
            )
            ret = self._dict_class()
            ret[self.url_field_name] = url_field
            ret.update(fields)
            fields = ret

        return fields
    
    def get_identity(self, data):
        """
        This hook is required for bulk update.
        We need to override the default, to use the url as the identity.
        """
        try:
            return data.get(self.url_field_name, None)
        except AttributeError:
            return None    


class OwnerField(rest_framework.fields.Field):
    def to_native(self, value):
        if not self.context.get('request'):
            return False
        return value==self.context['request'].user
    
class CountField(rest_framework.fields.Field):
    def to_native(self, value):
        return value.all().count()
    
class LocationField(rest_framework.fields.CharField):
    def to_native(self,value):
#         return ','.join(map(lambda v:str(v), [value[1],value[0]]))
        return map(lambda x: round(x,7), [value[1],value[0]])
    
    def from_native(self, coords):
        if isinstance(coords, (list,tuple)) and len(coords)==2:
            return Point(coords[1], coords[0], srid=4326)
        raise ValidationError(_('Invalid location value'))
            
    
    
    
class BaseSerializer(ModelSerializer):
    is_mine=OwnerField(source='created_by')
    
class AddressesSerializer(BaseSerializer):
    class Meta:
        model=Address
        fields=('id', 'street', 'city', 'postal_code', 'county', 'state', 'country', 'email', 
                'phone', 'unformatted', 'is_mine' )
        #read_only_fields = ('unformatted',)
        
        
class AddressesViewSet(UserMixin, LimitCreateMixin, ViewSetWithIndex):
    queryset=Address.objects.all()
    serializer_class=AddressesSerializer
    
class PlacesFilter(django_filters.FilterSet):
    name=django_filters.CharFilter(lookup_type='icontains')
    description=django_filters.CharFilter(lookup_type='icontains')
    class Meta:
        model=Place
        fields=('name', 'description', 'group')
        
class PlacesSerializer(BaseSerializer):
    position=LocationField(label=_('Location'), widget=custom_widgets.LocationWidget)
    address=rest_framework.relations.PrimaryKeyRelatedField(label=_('Address'), 
                widget=r2b_widgets.DynamicEditor(options={'deferredSave':True}),
                required=False)
    address_string=rest_framework.relations.RelatedField(source='address')
    description=fields.CharField(widget=widgets.Textarea, label=_('Description'), max_length=200, required=False)
    group= rest_framework.relations.PrimaryKeyRelatedField(widget=widgets.HiddenInput)
    def validate_name(self, attrs, source):
        if not attrs.has_key(source):
            return attrs
        name=attrs[source]
        group=attrs.get('group')
        if not group and self.object:
            group=self.object.group
            
        if group:
            existing=Place.objects.filter(name=name, group=group)
            if self.object and self.object.pk:
                existing=existing.exclude(pk=self.object.pk)
            if len(existing)>0:
                raise rest_framework.serializers.ValidationError(_('Place with same name  already exists in this collection'))
        return attrs
    class Meta:
        model= Place
        fields=['id',  'name', 'position', 'address', 'address_string', 'url', 'description', 'group', 'is_mine']
        
class PlacesViewSet(UserMixin, LimitCreateMixin, ViewSetWithIndex):
    
    queryset=Place.objects.all()
    serializer_class=PlacesSerializer
    filter_class=PlacesFilter
    
    _allowed_units=('m','km','mi', 'ft')
    _dist_re=re.compile('^(\d+\.?\d*)(\w{1,3})?$', re.IGNORECASE)
    _dist_q_re=re.compile(r'^within\s+(\d+\.?\d*\w{1,3})?\s+from\s+(\d+\.?\d*,\s*\d+\.?\d*)$')
    def get_queryset(self):
        
        within=self.request.QUERY_PARAMS.get('within')
        from_loc=self.request.QUERY_PARAMS.get('from')
        q=self.request.QUERY_PARAMS.get('q')
        qs=self.queryset._clone()
        m=self._dist_q_re.match(q) if q else None
        if m:
            within=m.group(1)
            from_loc=m.group(2)
            q=None
        if q:
            qs=lookup(q,qs)
        if within and from_loc:
            
            m=self._dist_re.match(within)
            try:
                if not m:
                    raise ValueError('within parameter is not distance literal')
                unit=m.group(2) or 'm'
                unit=unit.lower()
                if unit not in self._allowed_units:
                    raise ValueError('invalid unit of distance')
                within=float(m.group(1))
                dist={}
                dist[unit]=within
                lat,lng= map(lambda p: float(p.strip()), from_loc.split(','))
            except ValueError, e:
                raise FilterError(str(e))
            qs=qs.filter(position__distance_lte=(Point(lng,lat, srid=4326), Distance(**dist)))
        return qs
            
            
    
class GroupsFilter(django_filters.FilterSet):
    name=django_filters.CharFilter(lookup_type='icontains')
    description=django_filters.CharFilter(lookup_type='icontains')
    class Meta:
        model=PlacesGroup
        fields=('name', 'description')
            
class GroupsSerializer(BaseSerializer):
    count=CountField(source='places', label=_('Count of Places'))
    description=fields.CharField(widget=widgets.Textarea, label=_('Description'), max_length=200, required=False)
    def validate_name(self, attrs, source):
        if not attrs.has_key(source):
            return attrs
        name=attrs[source]
        existing=PlacesGroup.objects.filter(name=name, private=False).exclude(created_by=self.context['request'].user)
        if self.object and self.object.pk:
                existing=existing.exclude(pk=self.object.pk)
        if len(existing)>0:
            raise rest_framework.serializers.ValidationError(_('Collection with same name is already created by someone else'))
        return attrs
    class Meta:
        model=PlacesGroup
        fields=['id', 'name', 'description', 'private', 'is_mine', 'count']
        
class GroupsViewSet(UserMixin, LimitCreateMixin, ViewSetWithIndex):
    queryset=PlacesGroup.objects.all()
    serializer_class=GroupsSerializer
    filter_class=GroupsFilter
    def get_queryset(self):
        q=self.request.QUERY_PARAMS.get('q')
        query=Q(private=False)
        if self.request.user.is_authenticated():
            query|=Q(private=True, created_by=self.request.user)
        qs=self.queryset.filter(query)
        if q:
            qs=lookup(q,qs)
        return qs


def lookup(lookup, q):  
    terms=lookup.split()
    expression=["(unaccent(name) ilike unaccent(%s) or unaccent(description) ilike unaccent(%s))"]*len(terms)
    params=[['%'+t+'%']*2 for t in terms]
    params=list(itertools.chain(*params))
    return q.extra(where=expression, params=params)


class LocationSerializer(serializers.Serializer):
    position=LocationField()

class GeocodePermission(permissions.BasePermission):    
    def has_permission(self, request, view):
        return request.user.has_perm('myplaces.geocode_place')

import geocode
class GeocodeReverse(APIView):
    permission_classes=(GeocodePermission,)
    def post(self, request, format=None):
        s=LocationSerializer(data=request.DATA)
        if not s.is_valid():
            return Response({'error':'Invalid request data'}, status=status.HTTP_400_BAD_REQUEST)
        data=s.object
        try:
            address, place=geocode.get_address_remote(data.get('position'))
            s=AddressesSerializer(address)
            address=s.data
        except geocode.NotFound:
            address=None
        
        return Response({'address':address})
    
    
class Geocode(APIView):
    permission_classes=(GeocodePermission,)
    def post(self, request, format=None):
        s=AddressesSerializer(data=request.DATA.get('address'))
        if not s.is_valid():
            return Response({'error':'Invalid request data'}, status=status.HTTP_400_BAD_REQUEST)
        address=s.object
        try:
            new_address, place=geocode.get_coordinates_remote(address)
            s=LocationSerializer({'position':place})
            data=s.data
        except geocode.NotFound:
            data={'position':None}
        
        return Response(data)
    
        
    
    
        
