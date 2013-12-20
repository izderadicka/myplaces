'''
Created on May 29, 2013

@author: ivan
'''



from django import forms
from models import  PlacesGroup, Place, Address
from django.utils.translation import ugettext_lazy as _
import os
import format as fmt


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
        
    file_format=forms.ChoiceField(label=_('File Format'), choices=fmt.index())
    csv_file=forms.FileField(label=_('File To Import'), required=True)
    call_id=forms.CharField(required=True, widget=forms.HiddenInput(), label='')
    description=forms.CharField(widget=forms.Textarea, required=False)
    def clean(self):
        fname=self.cleaned_data.get('csv_file')
        fname= fname.name if fname else ''
        ext=os.path.splitext(fname)[1]
        allowed_exts=fmt.get_fmt_descriptor(self.cleaned_data['file_format']).extensions
        
        if ext and allowed_exts:
            ext=ext[1:]
            if allowed_exts:
                ext=ext.lower()
                if not ext in allowed_exts:
                    raise forms.ValidationError(_('Invalid file extension for %s format')%
                                                self.cleaned_data['file_format'])
            else:
                raise forms.ValidationError(_('Missing file extension for %s format')%
                                                self.cleaned_data['file_format'])
                
            
            
        return self.cleaned_data
    
    def clean_name(self):
        name=self.cleaned_data['name']
        existing=PlacesGroup.objects.filter(name=name, private=False).exclude(created_by=self.user)
        if len(existing)>0:
            raise forms.ValidationError(_('Collection with same name is already created by someone else'))
        
        return self.cleaned_data['name']
    
        
