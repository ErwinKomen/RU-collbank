"""
Definition of urls for collbank.
"""

from datetime import datetime
from django.conf.urls import url
# from django.core import urlresolvers
import django.contrib.auth.views

import collbank.collection.forms
from collbank.collection.views import *

# Uncomment the next lines to enable the admin:
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.base import RedirectView
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView

import nested_admin
from collbank.settings import APP_PREFIX, STATIC_ROOT, STATIC_URL
admin.autodiscover()

# set admin site names
admin.site.site_header = 'Collection Bank Admin'
admin.site.site_title = 'Collection Bank Site Admin'

urlpatterns = [
    # Examples:
    url(r'^$', collbank.collection.views.home, name='home'),
    url(r'^contact$', collbank.collection.views.contact, name='contact'),
    url(r'^about', collbank.collection.views.about, name='about'),
    url(r'^definitions$', RedirectView.as_view(url='/'+APP_PREFIX+'admin/'), name='definitions'),
    url(r'^collection/add', RedirectView.as_view(url='/'+APP_PREFIX+'admin/collection/collection/add'), name='add'),
    url(r'^collection/view/(?P<pk>\d+)$', CollectionDetailView.as_view(), name='coll_detail'),
    url(r'^collection/export/(?P<pk>\d+)$', CollectionDetailView.as_view(),  {'type': 'output'}, name='output'),
    url(r'^collection/handle/(?P<pk>\d+)$', CollectionDetailView.as_view(),  {'type': 'handle'}, name='handle'),
    url(r'^collection/publish/(?P<pk>\d+)$', CollectionDetailView.as_view(),  {'type': 'publish'}, name='publish'),
    url(r'^collection/evaluate/(?P<pk>\d+)$', CollectionDetailView.as_view(),  {'type': 'evaluate'}, name='evaluate'),
    # url(r'^collection/import/xml/$', CollectionUploadXml.as_view(), name='collection_upload_xml'),
    url(r'^external/list', RedirectView.as_view(url='/'+APP_PREFIX+'admin/collection/extcoll'), name='extcoll_list'),
    url(r'^external/add', RedirectView.as_view(url='/'+APP_PREFIX+'admin/collection/extcoll/add'), name='extcoll_add'),
    url(r'^registry/(?P<slug>[-_\.\w]+)$', CollectionDetailView.as_view(),  {'type': 'registry'}, name='registry'),
    url(r'^reload_collbank/$', collbank.collection.views.reload_collbank, name='reload'),
    url(r'^overview/$', CollectionListView.as_view(), name='overview'),
    url(r'^admin/collection/collection/$', RedirectView.as_view(pattern_name='overview'), name='collectionlist'),
    url(r'^admin/copy/$', collbank.collection.admin.copy_item, name='copyadmin'),
    url(r'^subtype_choices/', collbank.collection.views.subtype_choices),
    url(r'^signup/$', collbank.collection.views.signup, name='signup'),

    url(r'^login/user/(?P<user_id>\w[\w\d_]+)$', collbank.collection.views.login_as_user, name='login_as'),

    url(r'^login/$', LoginView.as_view
        (
            template_name= 'collection/login.html',
            authentication_form= collbank.collection.forms.BootstrapAuthenticationForm,
            extra_context= {'title': 'Log in','year': datetime.now().year,}
        ),
        name='login'),
    url(r'^logout$',  LogoutView.as_view(next_page=reverse_lazy('home')), name='logout'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', admin.site.urls, name='admin_base'),
    url(r'^_nested_admin/', include('nested_admin.urls')),
]

