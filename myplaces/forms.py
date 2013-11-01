'''
Created on May 29, 2013

@author: ivan
'''



from django import forms
from models import  PlacesGroup, Place, Address
from django.utils.translation import ugettext_lazy as _
import os


class AuditableModelForm(forms.ModelForm):
    
    def save(self, commit=True, user=None):
        """
        Saves this ``form``'s cleaned_data into model instance
        ``self.instance``.

        If commit=True, then the changes to ``instance`` will be saved to the
        database. Returns ``instance``.
        """
        if self.instance.pk is None:
            fail_message = 'created'
        else:
            fail_message = 'changed'
            
        self.instance.update_user(user)
        return forms.models.save_instance(self, self.instance, self._meta.fields,
                             fail_message, commit, construct=False)

    save.alters_data = True

class Group(AuditableModelForm):
    class Meta():
        fields=('name', 'description', 'private')
        model= PlacesGroup
        
class Place(AuditableModelForm):
    class Meta():
        model=Place
        fields=('group', 'name', 'description', 'url', 'address', 'position' )
        
class Address(AuditableModelForm):
    class Meta():
        model=Address
        
        
        
class ImportForm(Group):
    error_css_class = 'error'
    required_css_class = 'required'
    
    def __init__(self, *args, **kwargs):
        if kwargs.has_key('user'):
            self.user=kwargs.pop('user')
        super(ImportForm,self).__init__(*args,**kwargs)
        

    csv_file=forms.FileField(label=_('CSV File'), required=True)
    call_id=forms.CharField(required=True, widget=forms.HiddenInput(), label='')
    description=forms.CharField(widget=forms.Textarea, required=False)
    def clean_csv_file(self):
        ext=os.path.splitext(self.cleaned_data['csv_file'].name)[1]
        if ext.lower()!='.csv':
            raise forms.ValidationError(_('Only .csv files can be imported'))
        return self.cleaned_data['csv_file']
    
    def clean_name(self):
        name=self.cleaned_data['name']
        existing=PlacesGroup.objects.filter(name=name, private=False).exclude(created_by=self.user)
        if len(existing)>0:
            raise forms.ValidationError(_('Collection with same name is already created by someone else'))
        
        return self.cleaned_data['name']
    
        
