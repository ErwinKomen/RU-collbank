"""
Definition of urls for collbank.
"""

from datetime import datetime
from django.conf.urls import url
from django.core import urlresolvers
import django.contrib.auth.views

import collbank.collection.forms
import collbank.collection.views

# Uncomment the next lines to enable the admin:
from django.conf.urls import include
from django.shortcuts import redirect
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic.base import RedirectView
from django.contrib import admin
admin.autodiscover()

# set admin site names
admin.site.site_header = 'Collection Bank Admin'
admin.site.site_title = 'Collection Bank Site Admin'

# define a site prefix: SET this for the production environment
# pfx = "ru/"
# SET this one for the development environment
pfx = ""

urlpatterns = [
    # Examples:
    url(r'^$', collbank.collection.views.home, name='home'),
    url(r'^contact$', collbank.collection.views.contact, name='contact'),
    url(r'^about', collbank.collection.views.about, name='about'),
    url(r'^definitions$', RedirectView.as_view(url='/'+pfx+'admin/'), name='definitions'),
    url(r'^collections$', RedirectView.as_view(url='/'+pfx+'admin/collection/collection/'), name='collections'),

    url(r'^login/$',
        django.contrib.auth.views.login,
        {
            'template_name': 'collection/login.html',
            'authentication_form': collbank.collection.forms.BootstrapAuthenticationForm,
            'extra_context':
            {
                'title': 'Log in',
                'year': datetime.now().year,
            }
        },
        name='login'),
    url(r'^logout$',
        django.contrib.auth.views.logout,
        {
            'next_page': reverse_lazy('home'),
        },
        name='logout'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls), name='admin_base'),
]
