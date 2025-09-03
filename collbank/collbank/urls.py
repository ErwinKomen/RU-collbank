"""
Definition of urls for collbank.
"""

from django.conf import settings
from django.conf.urls import include                # , url
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy, re_path
from django.views.generic.base import RedirectView
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
import django.contrib.auth.views

import nested_admin
from datetime import datetime

# Import from COLLBANK as a whole
from collbank.settings import APP_PREFIX, STATIC_ROOT, STATIC_URL

# Import specific to COLLBANK parts
import collbank.collection.forms
import collbank.collection.views
import collbank.reader.views
from collbank.collection.views import *
from collbank.reader.views import *

admin.autodiscover()

# set admin site names
admin.site.site_header = 'Collection Bank Admin'
admin.site.site_title = 'Collection Bank Site Admin'

urlpatterns = [
    # Examples:
    re_path(r'^$',        collbank.collection.views.home,    name='home'),
    re_path(r'^contact$', collbank.collection.views.contact, name='contact'),
    re_path(r'^about',    collbank.collection.views.about,   name='about'),
    re_path(r'^nlogin',   collbank.collection.views.nlogin,  name='nlogin'),

    re_path(r'^reindex',  collbank.collection.views.oai_reset,  name='reindex'),

    re_path(r'^definitions$', RedirectView.as_view(url='/'+APP_PREFIX+'admin/'), name='definitions'),

    # ------------ Corpus collection handling and viewing --------------------------------------------
    re_path(r'^collection/add', RedirectView.as_view(url='/'+APP_PREFIX+'admin/collection/collection/add'), name='coll_add'),
    re_path(r'^collection/view/(?P<pk>\d+)$', CollectionDetailView.as_view(), name='coll_details'),
    re_path(r'^collection/export/(?P<pk>\d+)$', CollectionDetailView.as_view(),  {'type': 'output'}, name='output'),
    re_path(r'^collection/handle/(?P<pk>\d+)$', CollectionDetailView.as_view(),  {'type': 'handle'}, name='handle'),
    re_path(r'^collection/publish/(?P<pk>\d+)$', CollectionDetailView.as_view(),  {'type': 'publish'}, name='publish'),
    re_path(r'^collection/evaluate/(?P<pk>\d+)$', CollectionDetailView.as_view(),  {'type': 'evaluate'}, name='evaluate'),
    re_path(r'^overview/$', CollectionListView.as_view(), name='overview'),
    re_path(r'^admin/collection/collection/$', RedirectView.as_view(pattern_name='overview'), name='collectionlist'),

    # ------------ Basic app collection views --------------------------------------------------------
    re_path(r'^pid/list', PidList.as_view(), name='pid_list'),
    re_path(r'^pid/details(?:/(?P<pk>\d+))?/$', PidDetails.as_view(), name='pid_details'),
    re_path(r'^pid/edit(?:/(?P<pk>\d+))?/$', PidEdit.as_view(), name='pid_edit'),


    # -------------- Additional calls supporting the above -------------------------------------------
    re_path(r'^external/list', RedirectView.as_view(url='/'+APP_PREFIX+'admin/collection/extcoll'), name='extcoll_list'),
    re_path(r'^external/add', RedirectView.as_view(url='/'+APP_PREFIX+'admin/collection/extcoll/add'), name='extcoll_add'),
    re_path(r'^registry/(?P<slug>[-_\.\w]+)$', CollectionDetailView.as_view(),  {'type': 'registry'}, name='registry'),
    re_path(r'^reload_collbank/$', collbank.collection.views.reload_collbank, name='reload'),
    re_path(r'^admin/copy/$', collbank.collection.admin.copy_item, name='copyadmin'),
    re_path(r'^subtype_choices/', collbank.collection.views.subtype_choices),

    # ------------- Uploading XML definitions and viewing those uploads -------------------------------
    re_path(r'^source/list', SourceInfoList.as_view(), name='sourceinfo_list'),
    re_path(r'^source/details(?:/(?P<pk>\d+))?/$', SourceInfoDetails.as_view(), name='sourceinfo_details'),
    re_path(r'^source/edit(?:/(?P<pk>\d+))?/$', SourceInfoEdit.as_view(), name='sourceinfo_edit'),
    re_path(r'^source/load(?:/(?P<pk>\d+))?/$', SourceInfoLoadXml.as_view(), name='sourceinfo_load'),

    # ------------- Uploading VLO XML definitions and viewing those uploads -------------------------------
    re_path(r'^vloitem/list', VloItemList.as_view(), name='vloitem_list'),
    re_path(r'^vloitem/details(?:/(?P<pk>\d+))?/$', VloItemDetails.as_view(), name='vloitem_details'),
    re_path(r'^vloitem/edit(?:/(?P<pk>\d+))?/$', VloItemEdit.as_view(), name='vloitem_edit'),
    re_path(r'^vloitem/load(?:/(?P<pk>\d+))?/$', VloItemLoadXml.as_view(), name='vloitem_load'),
    re_path(r'^vloitem/register(?:/(?P<pk>\d+))?/$', VloItemRegister.as_view(), name='vloitem_register'),
    re_path(r'^vloitem/publish(?:/(?P<pk>\d+))?/$', VloItemPublish.as_view(), name='vloitem_publish'),

    # ------------- Authorization stuff ---------------------------------------------------------------
    re_path(r'^signup/$', collbank.collection.views.signup, name='signup'),

    re_path(r'^login/user/(?P<user_id>\w[\w\d_]+)$', collbank.collection.views.login_as_user, name='login_as'),

    re_path(r'^login/$', LoginView.as_view
        (
            template_name= 'collection/login.html',
            authentication_form= collbank.collection.forms.BootstrapAuthenticationForm,
            extra_context= {'title': 'Log in','year': datetime.now().year,}
        ),
        name='login'),
    re_path(r'^logout$',  LogoutView.as_view(next_page=reverse_lazy('home')), name='logout'),

    # ------------- Select2 ---------------------------------------------------------------------------
    re_path(r"^select2/", include("django_select2.urls")),

    # Uncomment the admin/doc line below to enable admin documentation:
    # re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    re_path(r'^admin/', admin.site.urls, name='admin_base'),
    re_path(r'^_nested_admin/', include('nested_admin.urls')),
]

