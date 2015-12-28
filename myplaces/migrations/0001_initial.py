# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Modified')),
                ('updates', models.BigIntegerField(default=0, verbose_name='Updates', editable=False)),
                ('views', models.BigIntegerField(default=0, verbose_name='Views', editable=False)),
                ('street', models.CharField(max_length=80, null=True, verbose_name='Street', blank=True)),
                ('city', models.CharField(max_length=80, null=True, verbose_name='City', blank=True)),
                ('county', models.CharField(max_length=80, null=True, verbose_name='County', blank=True)),
                ('state', models.CharField(max_length=80, null=True, verbose_name='State', blank=True)),
                ('postal_code', models.CharField(max_length=10, null=True, verbose_name='Postal Code', blank=True)),
                ('country', models.CharField(max_length=40, null=True, verbose_name='Country', blank=True)),
                ('unformatted', models.CharField(max_length=200, null=True, verbose_name='Unformatted Address', blank=True)),
                ('email', models.EmailField(max_length=80, null=True, verbose_name='Email', blank=True)),
                ('phone', models.CharField(max_length=40, null=True, verbose_name='Phone Number', blank=True)),
                ('created_by', models.ForeignKey(related_name='address_created_set', blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Created by')),
                ('modified_by', models.ForeignKey(related_name='address_modified_set', blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Modified by')),
            ],
            options={
                'verbose_name': 'Address',
                'verbose_name_plural': 'Addresses',
                'permissions': (('higher_limit_address', 'Can create more address objects'),),
            },
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Modified')),
                ('updates', models.BigIntegerField(default=0, verbose_name='Updates', editable=False)),
                ('views', models.BigIntegerField(default=0, verbose_name='Views', editable=False)),
                ('name', models.CharField(max_length=80, verbose_name='Name')),
                ('description', models.CharField(max_length=200, null=True, verbose_name='Description', blank=True)),
                ('position', django.contrib.gis.db.models.fields.PointField(srid=4326, verbose_name='Coordinates')),
                ('url', models.URLField(null=True, verbose_name='WWW Link', blank=True)),
                ('address', models.OneToOneField(related_name='place', null=True, blank=True, to='myplaces.Address', verbose_name='Address')),
                ('created_by', models.ForeignKey(related_name='place_created_set', blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Created by')),
            ],
            options={
                'verbose_name': 'Place',
                'verbose_name_plural': 'Places',
                'permissions': (('geocode_place', 'Can use geocoding API'), ('higher_limit_place', 'Can create more place objects')),
            },
        ),
        migrations.CreateModel(
            name='PlacesGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Modified')),
                ('updates', models.BigIntegerField(default=0, verbose_name='Updates', editable=False)),
                ('views', models.BigIntegerField(default=0, verbose_name='Views', editable=False)),
                ('name', models.CharField(max_length=80, verbose_name='Name')),
                ('description', models.CharField(max_length=200, null=True, verbose_name='Description', blank=True)),
                ('private', models.BooleanField(default=False, verbose_name='Private')),
                ('created_by', models.ForeignKey(related_name='placesgroup_created_set', blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Created by')),
                ('modified_by', models.ForeignKey(related_name='placesgroup_modified_set', blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Modified by')),
            ],
            options={
                'verbose_name': 'Places Group',
                'verbose_name_plural': 'Places Groups',
                'permissions': (('import_placesgroup', 'Can import places data from CSV'), ('higher_limit_placesgroup', 'Can create more placesgroup objects')),
            },
        ),
        migrations.AddField(
            model_name='place',
            name='group',
            field=models.ForeignKey(related_name='places', verbose_name='Group', to='myplaces.PlacesGroup'),
        ),
        migrations.AddField(
            model_name='place',
            name='modified_by',
            field=models.ForeignKey(related_name='place_modified_set', blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Modified by'),
        ),
    ]
