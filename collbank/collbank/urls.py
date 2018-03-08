"""
Definition of urls for collbank.
"""

from datetime import datetime
from django.conf.urls import url
from django.core import urlresolvers
import django.contrib.auth.views

import collbank.collection.forms
from collbank.collection.views import *

# Uncomment the next lines to enable the admin:
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic.base import RedirectView
from django.contrib import admin
import nested_admin
from collbank.settings import APP_PREFIX, STATIC_ROOT, STATIC_URL
# from collbank.collection.models import one_time_startup
admin.autodiscover()

# set admin site names
admin.site.site_header = 'Collection Bank Admin'
admin.site.site_title = 'Collection Bank Site Admin'

# define a site prefix: SET this for the production environment
# pfx = "ru/"
# SET this one for the development environment
# pfx = ""
# pfx = APP_PREFIX

urlpatterns = [
    # Examples:
    url(r'^$', collbank.collection.views.home, name='home'),
    url(r'^contact$', collbank.collection.views.contact, name='contact'),
    url(r'^about', collbank.collection.views.about, name='about'),
    url(r'^definitions$', RedirectView.as_view(url='/'+APP_PREFIX+'admin/'), name='definitions'),
    url(r'^collection/add', RedirectView.as_view(url='/admin/collection/collection/add'), name='add'),
    url(r'^collection/(?P<pk>\d+)$', CollectionDetailView.as_view(), name='coll_detail'),
    url(r'^collection/export/(?P<pk>\d+)$', CollectionDetailView.as_view(),  {'type': 'output'}, name='output'),
    url(r'^collection/handle/(?P<pk>\d+)$', CollectionDetailView.as_view(),  {'type': 'handle'}, name='handle'),
    url(r'^collection/publish/(?P<pk>\d+)$', CollectionDetailView.as_view(),  {'type': 'publish'}, name='publish'),
    url(r'^external/list', RedirectView.as_view(url='/admin/collection/extcoll'), name='extcoll_list'),
    url(r'^external/add', RedirectView.as_view(url='/admin/collection/extcoll/add'), name='extcoll_add'),
    url(r'^registry/(?P<slug>[-_\.\w]+)$', CollectionDetailView.as_view(),  {'type': 'registry'}, name='registry'),
    url(r'^reload_collbank/$', collbank.collection.views.reload_collbank, name='reload'),
    url(r'^overview/$', CollectionListView.as_view(), name='overview'),
    url(r'^admin/collection/collection/$', RedirectView.as_view(pattern_name='overview'), name='collectionlist'),
    url(r'^admin/copy/$', collbank.collection.admin.copy_item, name='copyadmin'),
    url(r'^subtype_choices/', collbank.collection.views.subtype_choices),
    url(r'^signup/$', collbank.collection.views.signup, name='signup'),

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
    url(r'^_nested_admin/', include('nested_admin.urls')),
]  # + static('/static/', document_root='/scratch2/www/collbank/live/repo/collbank/static/')
# ]  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# one_time_startup()
