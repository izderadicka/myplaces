'''
Created on Nov 16, 2013

@author: ivan
'''

from django.conf.urls import patterns
from django.conf.urls import include
from django.conf.urls import url
from django.views.generic.base import TemplateView

from registration.backends.default.views import ActivationView
from registration.backends.default.views import RegistrationView
from registration.forms import RegistrationFormUniqueEmail

from django.dispatch import receiver
from registration.signals import user_activated
from django.contrib.auth.models import  Group
from captcha.fields import CaptchaField, CaptchaTextInput
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm,\
    AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django import forms
from django.contrib.auth.models import User
from django.views.generic.edit import UpdateView
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from lockout.exceptions import LockedOut
from django.contrib.admin.sites import AdminSite
import urlparse

@receiver(user_activated)
def on_user_activated(sender, **kwargs):
    user=kwargs.get('user')
    if not user:
        return
    group=Group.objects.get(name='Full Users')
    user.groups.add(group)
    
class PwdPolicy(object):
    MIN_LENGTH=0
    MAX_LENGTH=0
    REQUIRED_CLASSES={} #TODO:  Implement required char classes and regexp
    
    def __init__(self, policy):
        if policy:
            self.MIN_LENGTH=self._get(policy, 'PASSWORD_MIN_LENGTH') or PwdPolicy.MIN_LENGTH
            self.MAX_LENGTH=self._get(policy, 'PASSWORD_MAX_LENGTH') or PwdPolicy.MAX_LENGTH
    errors={'too_short': _('Password must be at at least %d characters long'),
            'too_long':_('Password must be shorter then  %d characters'),}
    
    def _get(self, object, key):
        if hasattr(object, key):
            return getattr(object,key)
        elif hasattr(object,'get'):
            return object.get(key)
        else:
            self._get(object, key.lower())
        
    def validate(self, pwd):
        if self.MIN_LENGTH and len(pwd)<self.MIN_LENGTH:
            raise ValidationError(self.errors['too_short']% self.MIN_LENGTH)
        if self.MAX_LENGTH and len(pwd)>self.MAX_LENGTH:
            raise ValidationError(self.errors['too_long']% self.MAX_LENGTH)
            
pwdPolicy=PwdPolicy(settings)            
    
class CaptchaWidget(CaptchaTextInput):
    
    def __init__(self,*args,**kwargs):
        audio=kwargs.pop('enable_audio', False) and settings.CAPTCHA_FLITE_PATH
        if audio:
            kwargs['output_format']= u'<div class="captcha">%(image)s  <div class="small_btn reload_captcha"></div>' +\
            u' %(hidden_field)s %(text_field)s<div class="small_btn audio_captcha"></div></div>'        
        else:
            kwargs['output_format']= u'<div class="captcha">%(image)s  <div class="small_btn reload_captcha"></div>' +\
            u' %(hidden_field)s %(text_field)s</div>'
        super(CaptchaWidget, self).__init__(*args, **kwargs)
        
    class Media:
        js=('mp/js/adv-forms.js',)
        css={'all': ('mp/css/adv-forms.css',)}
        
class LabelCssMixin(object):
    required_css_class='required'
    error_css_class = 'error'

class CaptchaForm(RegistrationFormUniqueEmail, LabelCssMixin): 
        
    captcha = CaptchaField(widget=CaptchaWidget( enable_audio=True))
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        pwdPolicy.validate(password1)
        return password1
    
    
        

class PwdChangeForm(PasswordChangeForm, LabelCssMixin):
    
    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        pwdPolicy.validate(password1)
        return password1
    
class PwdResetForm(PasswordResetForm, LabelCssMixin):   
    
    captcha = CaptchaField(widget=CaptchaWidget( enable_audio=True))
    
class PwdSetForm(SetPasswordForm, LabelCssMixin):
   
    
    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        pwdPolicy.validate(password1)
        return password1
    
class ProfileForm(forms.ModelForm, LabelCssMixin):
    
    email=forms.EmailField(label=_('Email'))
    class Meta:
        model=User
        fields=('email', 'first_name', 'last_name')
        
    def clean_email(self):
        email=self.cleaned_data.get('email')
        found=User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if len(found)>0:
            raise ValidationError(_('This email is already used, use other email'))
        return email
        
class ProfileView(UpdateView):
    template_name='registration/profile_form.html'
    model=User
    form_class=ProfileForm
    
    @property
    def success_url(self):
        return urlparse.urljoin('http://', self.request.META.get('HTTP_HOST', ''),  reverse('home'))

       
    
    def get_object(self):
        return self.request.user
    

class AuthenticationLockForm(AuthenticationForm, LabelCssMixin):
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username and password:
            try:
                self.user_cache = auth.authenticate(username=username,
                                           password=password)
            except LockedOut:
                raise ValidationError(_('Login is temporarily disabled due to high amount of unsuccessful attempts from your address - try again later'))
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login']% {'username': self.username_field.verbose_name})
            elif not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages['inactive'])
        return self.cleaned_data
    

        
    
urlpatterns = patterns('',
                       url(r'^activate/complete/$',
                           TemplateView.as_view(template_name='registration/activation_complete.html'),
                           name='registration_activation_complete'),
                       # Activation keys get matched by \w+ instead of the more specific
                       # [a-fA-F0-9]{40} because a bad activation key should still get to the view;
                       # that way it can return a sensible "invalid key" message instead of a
                       # confusing 404.
                       url(r'^activate/(?P<activation_key>\w+)/$',
                           ActivationView.as_view(),
                           name='registration_activate'),
                       url(r'^register/$',
                           RegistrationView.as_view(form_class=CaptchaForm),
                           name='registration_register'),
                       url(r'^register/complete/$',
                           TemplateView.as_view(template_name='registration/registration_complete.html'),
                           name='registration_complete'),
                       url(r'^register/closed/$',
                           TemplateView.as_view(template_name='registration/registration_closed.html'),
                           name='registration_disallowed'),
                       url(r'^profile/?$', 
                           login_required(ProfileView.as_view()),
                           name='profile_change'
                           ),
                       url(r'^login/$',
                           auth_views.login,
                           {'template_name': 'registration/login.html',
                            'authentication_form': AuthenticationLockForm},
                           name='auth_login'),
                       url(r'^logout/$',
                           auth_views.logout,
                           {'template_name': 'registration/logout.html'},
                           name='auth_logout'),
                       url(r'^password/change/$',
                           auth_views.password_change, {'template_name':'registration/pwd_change_form.html',
                                                        'password_change_form':PwdChangeForm,
                                                       },
                           name='auth_password_change'),
                       url(r'^password/change/done/$',
                           auth_views.password_change_done, {'template_name':'registration/pwd_change_done.html'},
                           name='auth_password_change_done'),
                       url(r'^password/reset/$',
                           auth_views.password_reset, {'template_name': 'registration/pwd_reset_form.html',
                                                       'password_reset_form':PwdResetForm,
                                                        'email_template_name':'registration/pwd_reset_email.txt',
                                                        'subject_template_name':'registration/pwd_reset_subject.txt'},
                           name='auth_password_reset'),
                       url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
                           auth_views.password_reset_confirm, 
                           {'template_name':'registration/pwd_reset_confirm.html',
                            'set_password_form': PwdSetForm},
                           name='auth_password_reset_confirm'),
                       url(r'^password/reset/complete/$',
                           auth_views.password_reset_complete,
                           {'template_name':'registration/pwd_reset_complete.html'},
                           name='auth_password_reset_complete'),
                       url(r'^password/reset/done/$',
                           auth_views.password_reset_done,
                           {'template_name':'registration/pwd_reset_done.html'},
                           name='auth_password_reset_done'), 
                       )
