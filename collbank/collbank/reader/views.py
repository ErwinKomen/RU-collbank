"""
Definition of views for the READER app.
"""

from django.apps import apps
from django.contrib import admin
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import Group, User
from django.db.models.fields.related import OneToOneField
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Q, Prefetch, Count, F
from django.db.models.functions import Lower
from django.db.models.query import QuerySet 
from django.forms import formset_factory, modelformset_factory, inlineformset_factory, ValidationError
from django.forms.models import model_to_dict
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.template import Context
from django.views.generic.detail import DetailView
from django.views.generic.base import RedirectView
from django.views.generic import ListView, View
from django.views.decorators.csrf import csrf_exempt

# General imports
from datetime import datetime
import operator 
from operator import itemgetter
from functools import reduce
from time import sleep 
import fnmatch
import sys, os
import base64
import json
import csv, re
import requests
import openpyxl
import xmltodict
from openpyxl.utils.cell import get_column_letter
from io import StringIO
from itertools import chain

# Imports needed for working with XML and other file formats
from xml.dom import minidom
# See: http://effbot.org/zone/celementtree.htm
import xml.etree.ElementTree as ElementTree
 
# ======= imports from my own application ======
from collbank.settings import APP_PREFIX, MEDIA_DIR, WRITABLE_DIR
from collbank.basic.utils import ErrHandle
from collbank.basic.views import BasicDetails, BasicList, BasicPart
from collbank.basic.models import get_crpp_date
from collbank.reader.forms import UploadFileForm, UploadFilesForm, SourceInfoForm
from collbank.reader.models import get_current_datetime, SourceInfo
from collbank.collection.models import Collection, Title, Genre, Owner, Resource, Linguality

# =================== This is imported by seeker/views.py ===============
reader_uploads = [
    ]
# Global debugging 
bDebug = False


# =============== Helper functions ======================================

def getText(nodeStart):
    # Iterate all Nodes aggregate TEXT_NODE
    rc = []
    for node in nodeStart.childNodes:
        if node.nodeType == node.TEXT_NODE:
            sText = node.data.strip(' \t\n')
            if sText != "":
                rc.append(sText)
        else:
            # Recursive
            rc.append(getText(node))
    return ' '.join(rc)

def get_xml_child_text(nodeStart, childName):
    nodeChild = nodeStart.find("./{}".format(childName))
    sBack = ""
    if nodeChild != None and nodeChild != "":
        sBack = nodeChild.text
    return sBack

def get_xml_children(nodeStart, lst_name, oDict):
    for name in lst_name:
        nodeChild = nodeStart.find("./{}".format(name))
        sResult = ""
        if nodeChild != None and nodeChild != "":
            sBack = nodeChild.text
        oDict[name] = sBack
    return True

def download_file(url):
    """Download a file from the indicated URL"""

    bResult = True
    sResult = ""
    errHandle = ErrHandle()
    # Get the filename from the url
    name = url.split("/")[-1]
    # Set the output directory
    outdir = os.path.abspath(os.path.join(MEDIA_DIR, "e-codices"))
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    # Create a filename where we can store it
    filename = os.path.abspath(os.path.join(outdir, name))
    try:
        r = requests.get(url)
    except:
        sMsg = errHandle.get_error_message()
        errHandle.DoError("Request problem")
        return False, sMsg
    if r.status_code == 200:
        # Read the response
        sText = r.text
        # Write away
        with open(filename, "w", encoding="utf-8") as f:
            f.write(sText)
        sResult = filename
    else:
        bResult = False
        sResult = "download_file received status {} for {}".format(r.status_code, url)
    # Return the result
    return bResult, sResult

def user_is_ingroup(request, sGroup):
    # Is this user part of the indicated group?
    username = request.user.username
    user = User.objects.filter(username=username).first()
    # glist = user.groups.values_list('name', flat=True)

    # Only look at group if the user is known
    if user == None:
        glist = []
    else:
        glist = [x.name for x in user.groups.all()]

        # Only needed for debugging
        if bDebug:
            ErrHandle().Status("User [{}] is in groups: {}".format(user, glist))
    # Evaluate the list
    bIsInGroup = (sGroup in glist)
    return bIsInGroup

def get_user_object(username):
        # Sanity check
        if username == "":
            # Rebuild the stack
            return None
        # Get the user
        user = User.objects.filter(username=username).first()
        return user

# ======================== READING ACTUAL XML ===============================



# ======================== REQUIRED CLASSES =================================

class ReaderImport(View):
    # Initialisations
    arErr = []
    error_list = []
    transactions = []
    data = {'status': 'ok', 'html': ''}
    template_name = 'reader/import_manuscripts.html'
    obj = None
    oStatus = None
    data_file = ""
    bClean = False
    import_type = "undefined"
    sourceinfo_url = "undefined"
    username = ""
    mForm = UploadFilesForm
    
    def post(self, request, pk=None):
        # A POST request means we are trying to SAVE something
        self.initializations(request, pk)

        # Explicitly set the status to OK
        self.data['status'] = "ok"

        username = request.user.username
        self.username = username

        if self.checkAuthentication(request):
            # Remove previous status object for this user
            Status.objects.filter(user=username).delete()
            # Create a status object
            oStatus = Status(user=username, type=self.import_type, status="preparing")
            oStatus.save()
            # Make sure the status is available
            self.oStatus = oStatus

            form = self.mForm(request.POST, request.FILES)
            lResults = []
            if form.is_valid():
                # NOTE: from here a breakpoint may be inserted!
                print('import_{}: valid form'.format(self.import_type))
                oErr = ErrHandle()
                try:
                    # The list of headers to be shown
                    lHeader = ['status', 'msg', 'name', 'yearstart', 'yearfinish', 'library', 'idno', 'filename', 'url']

                    # Get user
                    user = User.models.filter(username=username).first() 
                    
                    # Create a SourceInfo object for this extraction
                    source = SourceInfo.objects.create(url=self.sourceinfo_url, collector=username, user=user)

                    # Process the request
                    bOkay, code = self.process_files(request, source, lResults, lHeader)

                    if bOkay:
                        # Adapt the 'source' to tell what we did 
                        source.code = code
                        oErr.Status(code)
                        source.save()
                        # Indicate we are ready
                        oStatus.set("readyclose")
                        # Get a list of errors
                        error_list = [str(item) for item in self.arErr]

                        statuscode = "error" if len(error_list) > 0 else "completed"

                        # Create the context
                        context = dict(
                            statuscode=statuscode,
                            results=lResults,
                            error_list=error_list
                            )
                    else:
                        self.arErr.append(code)

                    if len(self.arErr) == 0:
                        # Get the HTML response
                        self.data['html'] = render_to_string(self.template_name, context, request)
                    else:
                        lHtml = []
                        for item in self.arErr:
                            lHtml.append(item)
                        self.data['html'] = "There are errors: {}".format("\n".join(lHtml))
                except:
                    msg = oErr.get_error_message()
                    oErr.DoError("import_{}".format(self.import_type))
                    self.data['html'] = msg
                    self.data['status'] = "error"

            else:
                self.data['html'] = 'invalid form: {}'.format(form.errors)
                self.data['status'] = "error"
        
            # NOTE: do ***not*** add a breakpoint until *AFTER* form.is_valid
        else:
            self.data['html'] = "Please log in before continuing"

        # Return the information
        return JsonResponse(self.data)

    def initializations(self, request, object_id):
        # Clear errors
        self.arErr = []
        # COpy the request
        self.request = request

        # Get the parameters
        if request.POST:
            self.qd = request.POST
        else:
            self.qd = request.GET
        # ALWAYS: perform some custom initialisations
        self.custom_init()

    def custom_init(self):
        pass    

    def checkAuthentication(self,request):
        # first check for authentication
        if not request.user.is_authenticated:
            # Provide error message
            self.data['html'] = "Please log in to work on this project"
            return False
        elif not user_is_ingroup(request, 'lila_uploader'):
            # Provide error message
            self.data['html'] = "Sorry, you do not have the rights to upload anything"
            return False
        else:
            return True

    def process_files(self, request, source, lResults, lHeader):
        bOkay = True
        code = ""
        return bOkay, code


class SourceInfoList(BasicList):
    """List all source info objects"""

    model = SourceInfo
    listform = SourceInfoForm
    prefix = "srci"
    order_cols = ['user__username', 'code', 'created']
    order_default = order_cols
    order_heads = [
        {'name': 'User',    'order': 'o=1', 'type': 'str', 'custom': 'user', 'linkdetails': True},
        {'name': 'Code',    'order': 'o=2', 'type': 'str', 'custom': 'code', 'linkdetails': True, 'main': True},
        {'name': 'Created', 'order': 'o=3', 'type': 'str', 'custom': 'created', 'linkdetails': True},
    ]

    def get_field_value(self, instance, custom):
        sBack = ""
        sTitle = ""
        if custom == "code":
            sBack = instance.get_code_html()
        elif custom == "user":
            sBack = instance.get_username()
        elif custom == "created":
            sBack = instance.get_created()
        return sBack, sTitle


class SourceInfoEdit(BasicDetails):
    """The details of one SourceInfo object"""

    model = SourceInfo
    mForm = SourceInfoForm
    prefix = 'srci'
    mainitems = []

    def add_to_context(self, context, instance):
        """Add to the existing context"""

        oErr = ErrHandle()
        try:
            # Define the main items to show and edit
            context['mainitems'] = [
                # ============== HIDDEN ==========
                {'type': 'plain', 'label': "User ID",       'value': instance.user.id,         'field_key': "user", 'empty': 'idonly'},
                # ================================
                {'type': 'safe',  'label': "Code:",         'value': instance.get_code_html(), 'field_key': "code" },
                {'type': 'plain', 'label': "URL:",          'value': instance.get_url(),       'field_key': "url" },
                {'type': 'plain', 'label': "File:",         'value': instance.get_file(),      'field_key': "file"},
                {'type': 'plain', 'label': "User name:",    'value': instance.get_username(),   },
                {'type': 'plain', 'label': "Created:",      'value': instance.get_created()},
                ]
            # If there is a file, we can add a button to upload it
            if not instance.file is None:
                lhtml = []
                # Add an upload button
                lhtml.append(render_to_string("reader/upload_file.html", context, self.request))

                # Store the after_details in the context
                context['after_details'] = "\n".join(lhtml)


        except:
            msg = oErr.get_error_message()
            oErr.DoError("SourceInfoEdit/add_to_context")

        # Return the context we have made
        return context

    def before_save(self, form, instance):
        bStatus = True
        msg = ""
        if not instance is None:
            # Check if a user is supplied
            if instance.user is None:
                form.instance.user = self.request.user
                # This will now get saved correctly
        return bStatus, msg
    

class SourceInfoDetails(SourceInfoEdit):
    """Like SourceInfo Edit, but then html output"""
    rtype = "html"
    

class SourceInfoLoadXml(SourceInfoDetails):
    """Import an XML description of a collection"""

    initRedirect = True

    def initializations(self, request, pk):
        oErr = ErrHandle()
        try:

            # Get the parameters
            self.qd = request.POST
            self.object = None

            # The default redirectpage is just this manuscript
            self.redirectpage = reverse("sourceinfo_details", kwargs = {'pk': pk})

            # Get the object
            if not pk is None:
                instance = SourceInfo.objects.filter(id=pk).first()
                if not instance is None:
                    # Perform the actual uploading
                    oBack = self.read_xml(instance)

            # Getting here means all went well
        except:
            msg = oErr.get_error_message()
            oErr.DoError("SourceInfoLoadXml/initializations")
        return None

    def read_xml(self, instance):
        """Import an XML description of a collection and add it to the DB"""

        def get_shortest(lst_value):
            shortest = None
            for onevalue in lst_value:
                # Keep track of what the shortest is (for title)
                if shortest is None:
                    shortest = onevalue
                elif len(onevalue) < len(shortest):
                    shortest = onevalue
            return shortest

        def add_field_values(obj, value, sObl, cls, fk, sField):
            """"""
            if "-n" in sObl:
                # Potentially multiple values
                lst_value = [ value ] if isinstance(value, str) else value
                lst_current = [getattr(x, sField) for x in cls.objects.filter(**{"{}__id".format(fk): obj.id})]
                for oneval in lst_value:
                    if not oneval in lst_current:
                        oNew = {}
                        oNew[fk] = obj
                        oNew[sField] = oneval
                        cls.objects.create(**oNew)
            else:
                pass


        oErr = ErrHandle()
        oBack = dict(status="ok", msg="", filename="")
        iCollCount = 0
        # Overall keeping track of read collections
        lst_colls = []
        field_header = ['MdCreator', 'MdSelfLink', 'MdProfile', 'MdCollectionDisplayName']
        # field_coll = ['title', 'description', 'owner', 'genre', 'languageDisorder', 'domain', 'clarinCentre', 'version']
        field_coll = [
            {"name": "title",           "optionality": "1-n"},
            {"name": "description",     "optionality": "0-1"},
            {"name": "owner",           "optionality": "0-n"},
            {"name": "genre",           "optionality": "0-n"},
            {"name": "languageDisorder", "optionality": "0-n"},
            {"name": "domain",          "optionality": "0-n"},
            {"name": "clarinCentre",    "optionality": "0-1"},
            {"name": "version",         "optionality": "0-1"},
            ]

        try:
            # Get the file and read it
            data_file = instance.file

            # Convert the XML immediately into a dictionary
            doc = xmltodict.parse(data_file)
            oCollection = doc.get("CMD")
            if not oCollection is None:
                # get the header 
                oHeader = oCollection.get('Header')
                # Process the header information

                # Get the resources
                # NOTE: this is not used, since they will be generated by Collbank itself
                oResources = oCollection.get('Resources')

                # Get the components
                oComponents = oCollection.get("Components")

                coll_info = oComponents.get("CorpusCollection")
                # Get the titles and see if any of them match an existing identifier
                titles = coll_info.get("title")
                if not titles is None:
                    if isinstance(titles, str): titles = [ titles ]
                    # Walk all titles and see if there is any existing identifier
                    qs = Collection.objects.filter(identifier__in=titles)
                    if qs.count() == 0:
                        # We don't have this one yet: add it
                        identifier = get_shortest(titles)

                        # Process the necessary fields
                        for oField in field_coll:
                            fieldname = oField["name"]
                            fieldvalue = coll_info.get(fieldname)
                            optionality = oField['optionality']
                            if "-n" in optionality:
                                # Should get a list
                                if fieldvalue is None:
                                    lst_value = []
                                elif isinstance(fieldvalue,list):
                                    lst_value = fieldvalue
                                else:
                                    lst_value = [ fieldvalue ]
                                # Add the list of values
                                for onevalue in lst_value:
                                    pass

                        # Create the new collection
                        collection = Collection.objects.create(identifier=identifier)
                        # Add all fields appropriately
                        add_field_values(collection, titles, "1-n", Title, "collection", "name")
 

        except:
            msg = oErr.get_error_message()
            oBack['filename'] = filename
            oBack['status'] = 'error'
            oBack['msg'] = msg
    
        # Return the object that has been created
        return oBack

