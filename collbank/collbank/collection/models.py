"""Models for the collection records.

A collection is a bundle of resources belonging together.
The collection has a number of characteristics.
Each resource in the collection is characterised by its own annotations.

"""
from django.apps import apps
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.db.models.fields import Field
import requests
from requests.auth import HTTPBasicAuth

import copy  # (1) use python copy
import json
import sys
import os, time

from collbank.settings import REGISTRY_URL, REGISTRY_DIR, PUBLISH_DIR
from collbank.basic.utils import ErrHandle
from collbank.basic.views import get_current_datetime


MAX_IDENTIFIER_LEN = 30
MAX_NAME_LEN = 50
MAX_STRING_LEN = 255

PIDSERVICE_NAME = "gwdg"
INTERNAL_LANDINGPAGE = "internal.landingpage"
INTERNAL_SEARCHPAGE = "internal.searchpage"

RESOURCE_TYPE = "resource.type"
RESOURCE_DCTYPE = "resource.DCtype"
RESOURCE_SUBTYPE = "resource.subtype"
RESOURCE_MODALITY = "resource.modality"
GENRE_NAME = "genre.name"
MEDIA_FORMAT = "resource.media.format"
PROVENANCE_TEMPORALPROVENANCE = 'provenance.temporalprovenance'
PROVENANCE_GEOGRAPHICPROVENANCE = 'provenance.geographicprovenance'
PROVENANCE_GEOGRAPHIC_COUNTRY = 'country.name'  # 'provenance.geographic.country'
PROVENANCE_GEOGRAPHIC_PLACE = 'provenance.geographic.place'
RELATION_NAME = 'relation.name'
RELATION_TYPE = 'relation.type'
DOMAIN_NAME = "domain.name"
CHARACTERENCODING = "writtencorpus.characterencoding.name"
SPEECHCORPUS_RECORDINGENVIRONMENT = "speechcorpus.recordingenvironment"
SPEECHCORPUS_CHANNEL = "speechcorpus.channel"
SPEECHCORPUS_CONVERSATIONALTYPE = "speechcorpus.conversationaltype"
WRITTENCORPUS_AUTHORNUMBER = "writtencorpus.author.number"
WRITTENCORPUS_AUTHORDEMOGRAPHICS = "writtencorpus.author.demographics"

ACCESS_AVAILABILITY = "access.availability"
ACCESS_MEDIUM = "access.medium.format"
ACCESS_NONCOMMERCIAL = "access.nonCommercialUsageOnly"
ACCESS_LICENSE_NAME = "access.license.name"
ACCESS_LICENSE_URL = "access.license.url"
SIZEUNIT = "totalSize.sizeUnit"
DOCUMENTATION_TYPE = "documentation.type"
VALIDATION_TYPE = "validation.type"
VALIDATION_METHOD = "validation.method"
ANNOTATION_TYPE = "resource.annotation.type"
ANNOTATION_MODE = "resource.annotation.mode"
ANNOTATION_FORMAT = "resource.annotation.format"
SPEECHCORPUS_SOCIALCONTEXT = "speechcorpus.socialcontext.name"
SPEECHCORPUS_PLANNINGTYPE = "speechcorpus.planningtype.name"
SPEECHCORPUS_AUDIENCE = "speechcorpus.audience.type"
SPEECHCORPUS_INTERACTIVITY = "speechcorpus.interactivity.name"
SPEECHCORPUS_INVOLVEMENT = "speechcorpus.involvement.name"
AUDIOFORMAT_SPEECHCODING = "audioformat.speechcoding"
LINGUALITY_TYPE = "linguality.lingualitytype"
LINGUALITY_NATIVENESS = "linguality.lingualitynativeness"
LINGUALITY_AGEGROUP = "linguality.lingualityagegroup"
LINGUALITY_STATUS = "linguality.lingualitystatus"
LINGUALITY_VARIANT = "linguality.lingualityvariant"
LINGUALITY_MULTI = "linguality.multilingualitytype"
CLARIN_CENTRE = "clarincentre.name"

# ============================ HELPER FUNCTIONS ===========================

def build_choice_list(field, position=None, subcat=None):
    """Create a list of choice-tuples"""

    choice_list = [];
    unique_list = [];   # Check for uniqueness

    try:
        # check if there are any options at all
        if FieldChoice.objects == None:
            # Take a default list
            choice_list = [('0','-'),('1','N/A')]
        else:
            ## Force a real choice to be made
            #choice_list = [('-1','-')]
            for choice in FieldChoice.objects.filter(field__iexact=field):
                # Default
                sEngName = ""
                # Any special position??
                if position==None:
                    sEngName = choice.english_name
                elif position=='before':
                    # We only need to take into account anything before a ":" sign
                    sEngName = choice.english_name.split(':',1)[0]
                elif position=='after':
                    if subcat!=None:
                        arName = choice.english_name.partition(':')
                        if len(arName)>1 and arName[0]==subcat:
                            sEngName = arName[2]

                # Sanity check
                if sEngName != "" and not sEngName in unique_list:
                    # Add it to the REAL list
                    choice_list.append((str(choice.machine_value),sEngName));
                    # Add it to the list that checks for uniqueness
                    unique_list.append(sEngName)

            choice_list = sorted(choice_list,key=lambda x: x[1]);
    except:
        print("Unexpected error:", sys.exc_info()[0])
        choice_list = [('0','-'),('1','N/A')];

    # Signbank returns: [('0','-'),('1','N/A')] + choice_list
    # We do not use defaults
    return choice_list;

def choice_english(field, num):
    """Get the english name of the field with the indicated machine_number"""

    try:
        result_list = FieldChoice.objects.filter(field__iexact=field).filter(machine_value=num)
        if (result_list == None):
            return "(No results for "+field+" with number="+num
        return result_list[0].english_name
    except:
        return "(empty)"

def choice_value(field, term):
    """Get the numerical value of the field with the indicated English name"""

    try:
        result_list = FieldChoice.objects.filter(field__iexact=field).filter(english_name__iexact=term)
        if result_list == None or result_list.count() == 0:
            # Try looking at abbreviation
            result_list = FieldChoice.objects.filter(field__iexact=field).filter(abbr__iexact=term)
        if result_list == None:
            return -1
        else:
            return result_list[0].machine_value
    except:
        return -1

def choice_abbreviation(field, num):
    """Get the abbreviation of the field with the indicated machine_number"""

    try:
        result_list = FieldChoice.objects.filter(field__iexact=field).filter(machine_value=num)
        if (result_list == None):
            return "{}_{}".format(field, num)
        return result_list[0].abbr
    except:
        return "-"

def m2m_combi(items):
    try:
        if items == None:
            sBack = ''
        else:
            qs = items.all()
            sBack = '-'.join([str(thing) for thing in qs])
        return sBack
    except:
        return "(exception: {})".format(sys.exc_info()[0])

def m2m_namelist(items):
    if items == None:
        sBack = ''
    else:
        qs = items.all()
        sBack = ' || '.join([thing.name for thing in qs])
    return sBack

def m2m_identifier(items):
    if items == None:
        sBack = ''
    else:
        qs = items.all()
        sBack = "-".join([thing.identifier for thing in qs])
    return sBack

def get_instance_copy(item):
    new_copy = copy.copy(item)
    new_copy.id = None          # Reset the id
    new_copy.save()             # Save it preliminarily
    return new_copy

def copy_m2m(inst_src, inst_dst, field, lst_m2m = None):
    # Copy M2M relationship: conversationalType    
    for item in getattr(inst_src, field).all():
        # newItem = get_instance_copy(item)
        newItem = item.get_copy()
        # Possibly copy more m2m
        if lst_m2m != None:
            for deeper in lst_m2m:
                copy_m2m(item, newItem, deeper)
        getattr(inst_dst, field).add(newItem)

def copy_fk(inst_src, inst_dst, field):
    # Copy foreign-key relationship
    instSource = getattr(inst_src, field)
    if instSource != None:
        # instCopy = get_instance_copy(instSource)
        instCopy = instSource.get_copy()
        setattr(inst_dst, field, instCopy)

def get_ident(qs):
    if qs == None:
        idt = ""
    else:
        lst = qs.all()
        if len(lst) == 0:
            idt = "(empty)"
        else:
            qs = lst[0].collection_set
            idt = m2m_identifier(qs)
    return idt

def get_tuple_value(lstTuples, iId):
    if lstTuples == None:
        sBack = ""
    else:
        lstFound = [item for item in lstTuples if item[0] == iId]
        if len(lstFound) == 0:
            sBack = ""
        else:
            sBack = lstFound[0][1]
    return sBack

def get_tuple_index(lstTuples, sValue):
    if lstTuples == None:
        iBack = -1
    else:
        lstFound = [item for item in lstTuples if item[1] == sValue]
        if len(lstFound) == 0:
            iBack = -1
        else:
            iBack = lstFound[0][0]
    return iBack
  
def get_help(field):
    """Create the 'help_text' for this element"""

    # find the correct instance in the database
    help_text = ""
    try:
        entry_list = HelpChoice.objects.filter(field__iexact=field)
        entry = entry_list[0]
        # Note: only take the first actual instance!!
        help_text = entry.Text()
    except:
        help_text = "Sorry, no help available for " + field

    return help_text


# ========================= HELPER MODELS ==============================

class PidService(models.Model):
    name = models.CharField("The name of this ePIC service", max_length=MAX_NAME_LEN)
    url = models.CharField("The service URL with prefix", max_length=MAX_STRING_LEN)
    user = models.CharField("The user name", max_length=MAX_NAME_LEN)
    passwd = models.CharField("The password", max_length=MAX_STRING_LEN)

    def authenticate(self):
        """Authenticate with the ePIC API"""

        # Default reply
        oBack = {'status': 'error', 'msg': ''}
        # Issue the request
        r = requests.get(self.url, auth=(self.user,self.passwd))
        # Check the reply we got
        if r.status_code == 200:
            # Authentication worked
            oBack['status'] = 'ok'
        else:
            # Authentication did not work
            oBack['msg'] = "The authentication request returned code {}".format(r.status_code)
        return oBack

    def getdomain(self):
        """Get the domain of the url"""

        arUrl = self.url.split("/")
        if len(arUrl) > 0:
            if arUrl[-1] == "" and len(arUrl)> 1:
                sDomain = arUrl[-2]
            else:
                sDomain = arUrl[-1]
        else:
            sDomain = ""
        return sDomain

    def getpid(self, collection):
        """Get (and possibly create) a persistant identifier for this collection"""

        # Get the name that should have been used
        sName = collection.get_xmlfilename()
        # Try to find a persistent identifier for this collection:
        #   the real URL of this collection should end with / + sName
        basic_url = self.url
        if basic_url[-1] == "/":
            basic_url = basic_url[0:-1]
        sUrl = "{}/?URL=*/{}".format(basic_url, sName)
        headers = {'Accept': 'application/json'}
        # Issue the request
        r = requests.get(sUrl, auth=(self.user, self.passwd), headers=headers, timeout=10)
        if r.status_code == 200:
            # Got it: process the response
            if r.text == "":
                # Response is empty, so not found
                return "-"
            lResponse = json.loads(r.text)
            # Check how many responses we get
            if len(lResponse) == 1:
                # There is exactly one unique response
                sPid = lResponse[0]
                return sPid
            elif len(lResponse) == 0:
                # There is no response, so it does not exist
                return "-"
            else:
                # This is a real problem: there are more responses, while it should have been unique
                # TODO: remove multiple responses and leave only the FIRST entry
                #       (or the last one?)
                return ""
        elif r.status_code == 404:
            # It does not exist
            return "-"
        else:
            # Not authorized
            return ""

    def geturl(self, collection):
        """Given a stored PID, recover the URL it has"""

        sBack = ""
        # Try to use the PID stored in [collection]
        sPid = collection.pidname
        sUrl = "{}{}".format(self.url,sPid)
        headers = {'Content-type': 'application/json'}
        # sUrl = "{}?prefix=COLL".format(self.url)
        r = requests.get(sUrl,auth=(self.user, self.passwd), headers={'Content-type': 'application/json'})
        if r.status_code >= 100 and r.status_code < 300:
            lResponse = json.loads(r.text)
            # Find the element that has type URL
            for item in lResponse:
                if item['type'] == "URL":
                    # Found it
                    sBack = item['parsed_data']
                    break
        # we are fine here
        return sBack

    def createpid(self, collection):
        """Create a PID for this collection's id"""

        # First try to find it
        sAttempt = self.getpid(collection)
        if sAttempt == "":
            # Could be 'not authorized' or multiple responses
            return {'status': 'error', 'msg': 'not authorized?'}
        elif sAttempt != "-":
            return {'status': 'ok', 'pid': collection.pidname}
        # Getting here means that no PID has yet been made

        # Create the URL through which this collection bank entry can be reached
        sSearch = "{}{}".format(REGISTRY_URL, collection.get_xmlfilename())
        oData = [{'type': 'URL', 'parsed_data': sSearch}]
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        sUrl = "{}?prefix=COLL".format(self.url)
        r = requests.post(sUrl,auth=(self.user, self.passwd), json=oData, headers=headers)
        if r.status_code >= 100 and r.status_code < 300:
            # Positive reply -- get the pid
            oResponse = json.loads(r.text)
            sFullPid = oResponse['epic-pid']
            return {'status': 'ok', 'pid': sFullPid}
        else:
            # There has been a problem -- return empty
            return {'status': 'error', 'msg': 'code {}'.format(r.status_code)}

    def checkandupdatepid(self, collection):
        """Check and possibly PID for this collection """

        # Prepare our return
        oBack = {'status':"ok", 'msg': "no problem"}
        # Get the current URL
        sCurrentUrl = self.geturl(collection)
        # Compare with the stored url
        if sCurrentUrl != collection.url:
            # We need to update the stored url

            # Create the URL through which this collection bank entry can be updated
            oData = [{'type': 'URL', 'parsed_data': collection.url}]
            headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
            sUrl = "{}{}".format(self.url, collection.pidname)

            # For updating: use the PUT method
            r = requests.put(sUrl,auth=(self.user, self.passwd), json=oData, headers=headers)
            if r.status_code < 200 or r.status_code >= 300:
                # There has been a problem -- return empty
                oBack['status'] = "error"
                oBack['msg'] = 'code {}'.format(r.status_code)
            else:
                # Just in case: return the URL and the PID combination (r has no contents)
                oBack['url'] = collection.url
                oBack['pid'] = collection.pidname
        # Return the back object
        return oBack


class FieldChoice(models.Model):

    field = models.CharField(max_length=50)
    english_name = models.CharField(max_length=100)
    dutch_name = models.CharField(max_length=100)
    machine_value = models.IntegerField(help_text="The actual numeric value stored in the database. Created automatically.")

    def __str__(self):
        return "{}: {}, {} ({})".format(
            self.field, self.english_name, self.dutch_name, str(self.machine_value))

    class Meta:
        ordering = ['field','machine_value']


class HelpChoice(models.Model):
    """Define the URL to link to for the help-text"""
    
    field = models.CharField(max_length=200)        # The 'path' to and including the actual field
    searchable = models.BooleanField(default=False) # Whether this field is searchable or not
    display_name = models.CharField(max_length=50)  # Name between the <a></a> tags
    help_url = models.URLField(default='')          # THe actual help url (if any)

    def __str__(self):
        return "[{}]: {}".format(
            self.field, self.display_name)

    def Text(self):
        help_text = ''
        # is anything available??
        if (self.help_url != ''):
            if self.help_url[:4] == 'http':
                help_text = "See: <a href='{}'>{}</a>".format(
                    self.help_url, self.display_name)
            else:
                help_text = "{} ({})".format(
                    self.display_name, self.help_url)
        return help_text


class CollbankModel(object):
    """This is the regular [models.Model], but then with processing functions"""

    specification = []

    def custom_add(self, oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = self
        bOverwriting = False
        bSkip = False
        app_name = "collection"
        params = {}
        lst_msg = []

        # ============= DEBUGGING ===========
        bAllowOverwriting = True

        try:
            user = kwargs.get("user")
            username = kwargs.get("username")
            bOverwriting = kwargs.get("overwriting", bOverwriting)
            keyfield = kwargs.get("keyfield", "path")

            if not bOverwriting or bAllowOverwriting and bOverwriting:
                # Yes, we may continue! Process all fields in the specification
                for oField in self.specification:
                    # Get the parameters of this entry
                    field_org = oField.get(keyfield)
                    field = field_org.lower()
                    if keyfield == "path" and oField.get("type") == "fk_id":
                        field = "{}_id".format(field)
                    value = oItem.get(field) if field in oItem else oItem.get(field_org)
                    readonly = oField.get('readonly', False)

                    # Can we process this entry?
                    if value != None and value != "" and not readonly:
                        # Get some more parameters of the entry, which are for processing
                        path = oField.get("path")
                        type = oField.get("type")

                        # ======= DEBUGGING ===========
                        if path.lower() == "resource":
                            iStop = 1
                        # =============================

                        # If this is fieldchoice, we need to change the [value] appropriately
                        fieldchoice = oField.get("fieldchoice")
                        if not fieldchoice is None:
                            if isinstance(value, list):
                                vlist = []
                                for onevalue in value:
                                    vlist.append(choice_value(fieldchoice, onevalue))
                                value = vlist
                            else:
                                iBack = choice_value(fieldchoice, value)
                                # But what if we end up not knowing this value??
                                if iBack < 0:
                                    # The value is not known - do we have an alternative field??
                                    alternative = oField.get("alternative")
                                    if not alternative is None:
                                        # Set the alternative field
                                        setattr(obj, alternative, value)
                                        # Make sure that we set the fieldchoice field to 'other'
                                        value = choice_value(fieldchoice, "other")
                                else:
                                    value = iBack

                        # Processing depends on the [type]
                        if type == "field":
                            # See if this is accidentily a list
                            if isinstance(value, list):
                                # Get the value
                                if len(value) == 0:
                                    value = None
                                else:
                                    value = value[0]
                            # Note overwriting
                            old_value = getattr(obj, path)
                            if value != old_value:
                                # Set the correct field's value
                                setattr(obj, path, value)
                        elif type == "fk" or type == "fkc":
                            fkfield = oField.get("fkfield")
                            model = oField.get("model")
                            vfield = oField.get("vfield")
                            if fkfield != None and model != None:
                                # Find an item with the name for the particular model
                                cls = apps.app_configs[app_name].get_model(model)

                                if type == "fk":
                                    if vfield is None:
                                        # Find this particular instance
                                        instance = cls.objects.filter(**{"{}".format(fkfield): value}).first()
                                    else:
                                        # Find this particular instance
                                        instance = cls.objects.filter(**{"{}".format(vfield): value}).first()
                                    if instance is None:
                                        # There is no such instance (yet): NOW WHAT??
                                        pass
                                    else:
                                        old_value = getattr(obj,path)
                                        if instance != old_value:
                                            setattr(obj, path, instance)
                                elif type == "fkc":
                                    # Need to create an item
                                    if vfield is None:
                                        # Find this particular instance
                                        oErr.Status("custom_add: [fkc] has no [vfield] specified")
                                        pass
                                    else:
                                        # Create an instance appropriately
                                        instance = cls.objects.create(**{'{}'.format(fkfield): obj, '{}'.format(vfield): value})
                                        # Set the FK appropriately
                                        setattr(obj, path, instance)
                        elif type == "fkob":
                            if not value is None:
                                model = oField.get("model")
                                # Find an item with the name for the particular model
                                cls = apps.app_configs[app_name].get_model(model)

                                # Use the custom_set of that model
                                fkob = cls.get_instance(value, params, **kwargs)
                                # fkob.custom_add(value, params, **kwargs)

                                # Make sure this is added to collection
                                setattr(obj, path, fkob)

                        elif type == "m2o":
                            fkfield = oField.get("fkfield")
                            model = oField.get("model")
                            vfield = oField.get("vfield")
                            if not fkfield is None and not model is None:
                                # Find an item with the name for the particular model
                                cls = apps.app_configs[app_name].get_model(model)
                                if vfield is None:
                                    if False:
                                        # Divide the values
                                        lst_val = [ value ] if isinstance(value, str) or isinstance(value, int) else value
                                        for oneval in lst_val:
                                            # Create a new instance
                                            instance = cls.get_instance(oneval, params, **kwargs)

                                            # Make sure the FK is set correctly
                                            setattr(instance, fkfield, obj)
                                    else:
                                        # Create a new instance
                                        params[fkfield] = obj
                                        if isinstance(value, list):
                                            for onevalue in value:
                                                instance = cls.get_instance(onevalue, params, **kwargs)
                                        else:
                                            instance = cls.get_instance(value, params, **kwargs)
                                else:
                                    # A vfield has been specified
                                    if isinstance(value, list):
                                        for onevalue in value:
                                            instance = cls.objects.create(**{'{}'.format(fkfield): obj, '{}'.format(vfield): onevalue})
                                    else:
                                        instance = cls.objects.create(**{'{}'.format(fkfield): obj, '{}'.format(vfield): value})

                        elif type == "func":
                            # Set the KV in a special way
                            obj.custom_set(path, value, **kwargs)

                # Make sure to save changes
                obj.save()

        except:
            msg = oErr.get_error_message()
            oErr.DoError("CollbankModel/custom_add")
        return obj



# ========================= COLLECTION MODELS ==========================

class Title(models.Model):
    """Title of this collection"""

    # [1; f]
    name = models.TextField("Title used for the collection as a whole", help_text=get_help('title'))
    # [1]     Each collection can have [1-n] titles
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="collection12m_title")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        return "[{}] {}".format(idt,self.name[:50])

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.name


class Owner(models.Model):
    """The legal owner"""

    # [1; f]
    name = models.TextField("One of the collection or resource owners", help_text=get_help('owner'))
    # [1]     Each collection can have [0-n] owvers
    collection = models.ForeignKey("Collection", blank=False, null=False, on_delete=models.CASCADE, default=1, related_name="collection12m_owner")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        return "[{}] {}".format(idt,self.name[:50])

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.name


class Media(CollbankModel, models.Model):
    """Medium on which this resource exists"""

    class Meta:
        verbose_name_plural = "Media's"

    # format (0-n; c)
    # format = models.ManyToManyField("MediaFormat", blank=True, related_name="mediam2m_mediaformat")
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="media_items")

    # Scheme for downloading and uploading
    specification = [
        {'name': 'Format',  'type': 'm2o',  'path': 'format',   'fkfield': 'media', 'model': 'MediaFormat',  
         'vfield': 'name', 'fieldchoice': MEDIA_FORMAT},
        ]

    def __str__(self):
        sFormats = m2m_combi(self.mediaformat12m_media)
        # return m2m_combi(self.format)
        return sFormats

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Copy the 12m fields
        copy_m2m(self, new_copy, "mediaformat12m_media")
        # Return the new copy
        return new_copy

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            # We should create a new instance
            resource = oParams.get("resource")
            obj = Media.objects.create(resource=resource)

            # And now call the standard custom_add() method
            oParams['media'] = obj
            obj.custom_add(oItem, oParams, **kwargs)

        except:
            msg = oErr.get_error_message()
            oErr.DoError("Media/get_instance")
        return obj


class MediaFormat(models.Model):
    """Format of a medium"""

    name = models.CharField("Format of a medium", choices=build_choice_list(MEDIA_FORMAT), max_length=5, help_text=get_help(MEDIA_FORMAT), default='0')
    # [1]     Each [Media] object can have [0-n] MediaFormat items
    media = models.ForeignKey(Media, blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="mediaformat12m_media")

    def __str__(self):
        return choice_english(MEDIA_FORMAT, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class AnnotationFormat(models.Model):
    """Format of an annotation"""

    name = models.CharField("Annotation format", choices=build_choice_list(ANNOTATION_FORMAT), max_length=5, help_text=get_help(ANNOTATION_FORMAT), default='0')
    # [1] link to the parent Annotation (many-to-one relation)
    annotation = models.ForeignKey("Annotation", blank=False, null=False, default=-1, on_delete=models.CASCADE, related_name = "annotation_formats")

    def __str__(self):
        return choice_english(ANNOTATION_FORMAT, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class Annotation(CollbankModel, models.Model):
    """Description of one annotation layer in a resource"""

    # [1] Obligatory type, but it can be '0'
    type = models.CharField("Kind of annotation", choices=build_choice_list(ANNOTATION_TYPE), 
                            max_length=5, help_text=get_help(ANNOTATION_TYPE), default='0')
    # [0-1] Optional other type in a string
    othertype = models.CharField("kind of 'other' annotation", blank=True, null=True, max_length=MAX_STRING_LEN)
    # [0-1] Optional mode (it can be '0'
    mode = models.CharField("Annotation mode", choices=build_choice_list(ANNOTATION_MODE), 
                            max_length=5, help_text=get_help(ANNOTATION_MODE), default='0')

    # [1] Annotation belongs to a resource
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , 
                                 on_delete=models.CASCADE, related_name="annotations")

    # Scheme for downloading and uploading
    specification = [
        {'name': 'Type',    'type': 'field', 'path': 'type',        'fieldchoice': ANNOTATION_TYPE, 'alternative': 'othertype'},
        {'name': 'Other',   'type': 'field', 'path': 'othertype'},
        {'name': 'Mode',    'type': 'field', 'path': 'mode',        'fieldchoice': ANNOTATION_MODE},

        {'name': 'Format',  'type': 'm2o',   'path': 'format',      'fkfield': 'annotation', 
         'model': 'AnnotationFormat',  'vfield': 'name',            'fieldchoice': ANNOTATION_FORMAT},
    ]

    def __str__(self):
        try:
            if self.resource.collection_id > 0:
                idt = self.resource.collection.identifier
            else:
                idt = "EMPTY"
            #return "[{}] {}: {}, {}".format(
            #    idt,
            #    choice_english(ANNOTATION_TYPE, self.type), 
            #    choice_english(ANNOTATION_MODE,self.mode), 
            #    m2m_combi(self.formatAnn))
            return "[{}] {}: {}".format(
                idt, choice_english(ANNOTATION_TYPE, self.type),  choice_english(ANNOTATION_MODE,self.mode))
        except:
            return "(exception)"

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Copy the 12m field
        copy_m2m(self, new_copy, "annotation_formats")
        # Return the new copy
        return new_copy

    def get_instance(oItem, oParams, **kwargs):
        """Get a new instance based on the parameters"""

        obj = None
        oErr = ErrHandle()
        try:
            # Must have the resource
            resource = oParams.get("resource")

            # We should create a new Annotation instance
            obj = Annotation.objects.create(resource=resource)

            oParams['annotation'] = obj

            # And now call the standard custom_add() method
            obj.custom_add(oItem, oParams, **kwargs)

            # Quick fix
            if obj.mode == '0':
                obj.mode = '1'

        except:
            msg = oErr.get_error_message()
            oErr.DoError("Annotation/get_instance")
        return obj

    def get_view(self):
        """Present the current annotation format"""
        sFmts = m2m_combi(self.annotation_formats)
        annotationtype = self.get_type_display()
        annotationmode = self.get_mode_display()
        if annotationtype == "other":
            # Check if [othertype] has been specified
            if not self.othertype is None and self.othertype != "":
                annotationtype = "{}: {}".format(annotationtype, self.othertype)
        sBack = "[{}] [{}] [{}]".format(annotationtype, annotationmode, sFmts)
        return sBack


class TotalSize(CollbankModel, models.Model):
    """Total size of the resource"""

    # size = models.IntegerField("Size of the collection", default=0)
    size = models.CharField("Size of the collection", default="unknown", max_length=80)
    sizeUnit = models.CharField("Units", help_text=get_help(SIZEUNIT), max_length=50, default='MB')
    # [1]     Each resource can have [0-n] total-sizes
    resource = models.ForeignKey("Resource", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="totalsize12m_resource")

    # Scheme for downloading and uploading
    specification = [
        {'name': 'Size',        'type': 'field', 'path': 'size'},
        {'name': 'SizeUnit',    'type': 'field', 'path': 'sizeUnit'},
    ]

    def __str__(self):
        if self.resource.collection_id >0:
            idt = self.resource.collection.identifier
        else:
            idt = "EMPTY"
        return "[{}] {} {}".format(idt,self.size,self.sizeUnit)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_instance(oItem, oParams, **kwargs):
        """Get a new instance based on the parameters"""

        obj = None
        oErr = ErrHandle()
        try:
            # Must have the resource
            resource = oParams.get("resource")

            if resource is None:
                # Cannot process this
                pass
            else:
                # Create a new instance
                obj = TotalSize.objects.create(resource=resource)

                # And now call the standard custom_add() method
                obj.custom_add(oItem, oParams, **kwargs)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("TotalSize/get_instance")
        return obj
    

class TotalCollectionSize(CollbankModel, models.Model):
    """Total size of the collection"""

    # [1]
    size = models.CharField("Size of the collection", default="unknown", max_length=80)
    # [1]
    sizeUnit = models.CharField("Units", help_text=get_help(SIZEUNIT), max_length=50, default='MB')
    # [1]     Each collection can have [0-n] total-sizes
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="collection12m_totalsize")

    # Scheme for downloading and uploading
    specification = [
        {'name': 'Size',        'type': 'field', 'path': 'size'},
        {'name': 'SizeUnit',    'type': 'field', 'path': 'sizeUnit'},
    ]

    def __str__(self):
        return "[{}] {} {}".format(self.collection.identifier,self.size,self.sizeUnit)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_instance(oItem, oParams, **kwargs):
        """Get a new instance based on the parameters"""

        obj = None
        oErr = ErrHandle()
        try:
            # Must have the collection
            collection = oParams.get("collection")

            if collection is None:
                # Cannot process this
                pass
            else:
                # Create a new instance
                obj = TotalCollectionSize.objects.create(collection=collection)

                # And now call the standard custom_add() method
                obj.custom_add(oItem, oParams, **kwargs)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("TotalCollectionSize/get_instance")
        return obj

    def get_view(self):
        return "{} {}".format(self.size, self.sizeUnit)


class Modality(models.Model):
    """Modality of a resource"""

    class Meta:
        verbose_name_plural = "Modalities"

    name = models.CharField("Resource modality", choices=build_choice_list(RESOURCE_MODALITY), max_length=5, 
                            help_text=get_help(RESOURCE_MODALITY), default='0')
    # [1] Link to the parent Resource instance
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1, on_delete=models.CASCADE, related_name="modalities")

    def __str__(self):
        if self.resource_id >0 and self.resource.collection_id >0:
            idt = self.resource.collection.identifier
        else:
            idt = "EMPTY"
        return "[{}] {}".format(idt,choice_english(RESOURCE_MODALITY, self.name))

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class TemporalProvenance(models.Model):
    """Temporal coverage of the collection"""

    # == Start year: yyyy
    # startYear = models.IntegerField("First year covered by the collection", default=datetime.now().year)
    startYear = models.CharField("First year covered by the collection", max_length=20, default=str(datetime.now().year))
    # == End year: yyyy
    # endYear = models.IntegerField("Last year covered by the collection", default=datetime.now().year)
    endYear = models.CharField("Last year covered by the collection", max_length=20, default=str(datetime.now().year))

    def __str__(self):
        return "{}-{}".format(self.startYear, self.endYear)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            if not oItem is None:
                startYear = oItem.get("startYear", "")
                endYear = oItem.get("endYear", "")

                if endYear is None or endYear == "":
                    endYear = startYear
                # Create an instance
                obj = TemporalProvenance.objects.create(startYear=startYear, endYear=endYear)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("TemporalProvenance/get_instance")
        return obj

    def get_view(self):
        return "{}-{}".format(self.startYear, self.endYear)


class CountryIso(models.Model):
    """Country according to the ISO-3166 codes"""

    # [1] Two-letter code
    alpha2 = models.CharField("Two letter code", max_length=2)
    # [1] Three-letter code
    alpha3 = models.CharField("Three letter code", max_length=3)
    # [1] Numerical code
    numeric = models.IntegerField("Numeric code")
    # [1] Short name English
    english = models.CharField("English short name", max_length=MAX_STRING_LEN)
    # [1] Short name French
    french = models.CharField("French short name", max_length=MAX_STRING_LEN)

    def __str__(self) -> str:
        sBack = "[{}] {}".format(self.alpha2, self.english)
        return sBack

    def get_byalpha2(alpha2):
        """Get country via the Alpha2"""

        oErr = ErrHandle()
        obj = None
        try:
            obj = CountryIso.objects.filter(alpha2__iexact=alpha2).first()
        except:
            msg = oErr.get_error_message()
            oErr.DoError("get_byalpha2")
        return obj


class City(models.Model):
    """Name of a city"""

    class Meta:
        verbose_name_plural = "Cities"

    name = models.CharField("Place (city)", max_length=80, help_text=get_help(PROVENANCE_GEOGRAPHIC_PLACE))
    # [1]     Each geographic provenance can have [0-n] cities
    geographicProvenance = models.ForeignKey("GeographicProvenance", blank=False, null=False, default=-1, on_delete=models.CASCADE, related_name="cities")

    def __str__(self):
        return self.name

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.name


class GeographicProvenance(models.Model):
    """Geographic coverage of the collection"""

    # [0-1] New link to CountryIso (0-1;c) (name+ISO-3166 code)
    countryiso = models.ForeignKey(CountryIso, null=True, on_delete=models.SET_NULL, related_name="countryiso_gprovenances")
    # [1]     Each Provenance can have [0-n] geographic provenances
    provenance = models.ForeignKey("Provenance", blank=False, null=False, default=-1, on_delete=models.CASCADE, related_name="g_provenances")

    def __str__(self):
        cnt = self.countryiso.alpha2
        cts = m2m_combi(self.cities)
        return "{}: {}".format(cnt, cts)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Copy 1-to-m fields
        copy_m2m(self, new_copy, "cities")
        # Return the new copy
        return new_copy

    def get_countryiso(oGeoProv):
        """Retrieve the [countryiso] from a geographic provenance specification"""

        oErr = ErrHandle()
        obj = None
        try:
            if not oGeoProv is None:
                oCountry = oGeoProv.get("Country")
                if not oCountry is None:
                    sCountryCoding = oCountry.get("CountryCoding")
                    if not sCountryCoding is None:
                        obj = CountryIso.objects.filter(alpha2__iexact=sCountryCoding).first()
        except:
            msg = oErr.get_error_message()
            oErr.DoError("get_countryiso")
        return obj

    def get_view(self):
        return self.__str__()


class Provenance(models.Model):
    """Temporal and/or geographic provenance of the collection"""

    # temporalProvenance (0-1) 
    temporalProvenance = models.ForeignKey(TemporalProvenance, blank=True, null=True, on_delete=models.SET_NULL)
    # geographicProvenance (0-n) 
    # [1]     Each collection can have [0-n] provenances
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="collection12m_provenance")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        tmp = self.temporalProvenance
        geo = m2m_combi(self.g_provenances)
        return "[{}] temp:{}, geo:{}".format(idt, tmp, geo)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Copy FK field
        copy_fk(self, new_copy, "temporalProvenance")
        # copy 1-to-m- fields
        copy_m2m(self, new_copy, "g_provenances")
        # Return the new copy
        return new_copy

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            # We should create a new instance
            collection = oParams.get("collection")
            if collection is None:
                # Cannot process this
                pass
            else:
                obj = Provenance.objects.create(collection=collection)

                prov_temp = oItem.get('temporalProvenance')
                if not prov_temp is None:
                    # Get the FK in a straight forward way
                    obj.temporalProvenance = TemporalProvenance.get_instance(prov_temp, oParams, **kwargs)
                    # Save this change
                    obj.save()

                # Create a geographicProvenance if this is needed
                countryiso = GeographicProvenance.get_countryiso( oItem.get("geographicProvenance"))
                if not countryiso is None:
                    obj_geo = GeographicProvenance.objects.create(provenance=obj, countryiso=countryiso)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("Provenance/get_instance")
        return obj


class Genre(models.Model):
    """Genre of collection as a whole"""

    # (0-n; c)
    name = models.CharField("Collection genre", choices=build_choice_list(GENRE_NAME), max_length=5, help_text=get_help(GENRE_NAME), default='0')
    # [1]     Each collection can have [1-n] genres
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="collection12m_genre")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        return "[{}] {}".format(idt,choice_english(GENRE_NAME, self.name))

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class LingualityType(models.Model):
    """Type of linguality"""

    name = models.CharField("Type of linguality", choices=build_choice_list(LINGUALITY_TYPE), max_length=5, help_text=get_help(LINGUALITY_TYPE), default='0')
    # [1]     Each Linguality instance can have [0-n] linguality types
    linguality = models.ForeignKey("Linguality", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="linguality_types")

    def __str__(self):
        return choice_english(LINGUALITY_TYPE, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class LingualityNativeness(models.Model):
    """Nativeness type of linguality"""

    class Meta:
        verbose_name_plural = "Linguality Nativeness Types"

    name = models.CharField("Nativeness type of linguality", choices=build_choice_list(LINGUALITY_NATIVENESS), max_length=5, help_text=get_help(LINGUALITY_NATIVENESS), default='0')
    # [1]     Each Linguality instance can have [0-n] linguality nativenesses
    linguality = models.ForeignKey("Linguality", blank=False, null=False, on_delete=models.CASCADE, default=1, related_name="linguality_nativenesses")

    def __str__(self):
        return choice_english(LINGUALITY_NATIVENESS, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class LingualityAgeGroup(models.Model):
    """Age group of linguality"""

    name = models.CharField("Age group of linguality", choices=build_choice_list(LINGUALITY_AGEGROUP), max_length=5, help_text=get_help(LINGUALITY_AGEGROUP), default='0')
    # [1]     Each Linguality instance can have [0-n] linguality age groups
    linguality = models.ForeignKey("Linguality", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="linguality_agegroups")

    def __str__(self):
        return choice_english(LINGUALITY_AGEGROUP, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class LingualityStatus(models.Model):
    """Status of linguality"""

    class Meta:
        verbose_name_plural = "Linguality statuses"

    name = models.CharField("Status of linguality", choices=build_choice_list(LINGUALITY_STATUS), max_length=5, help_text=get_help(LINGUALITY_STATUS), default='0')
    # [1]     Each Linguality instance can have [0-n] linguality statuses
    linguality = models.ForeignKey("Linguality", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="linguality_statuses")

    def __str__(self):
        return choice_english(LINGUALITY_STATUS, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class LingualityVariant(models.Model):
    """Variant of linguality"""

    name = models.CharField("Variant of linguality", choices=build_choice_list(LINGUALITY_VARIANT), max_length=5, help_text=get_help(LINGUALITY_VARIANT), default='0')
    # [1]     Each Linguality instance can have [0-n] linguality variants
    linguality = models.ForeignKey("Linguality", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="linguality_variants")

    def __str__(self):
        return choice_english(LINGUALITY_VARIANT, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class MultilingualityType(models.Model):
    """Type of multi-linguality"""

    name = models.CharField("Type of multi-linguality", choices=build_choice_list(LINGUALITY_MULTI), max_length=5, help_text=get_help(LINGUALITY_MULTI), default='0')
    # [1]     Each Linguality instance can have [0-n] multilinguality types
    linguality = models.ForeignKey("Linguality", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="multilinguality_types")

    def __str__(self):
        return choice_english(LINGUALITY_MULTI, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class Linguality(CollbankModel, models.Model):
    """Linguality information on this collection"""


    # Scheme for downloading and uploading
    specification = [
        {'name': 'Type',        'type': 'm2o',  'path': 'lingualityType',       'fkfield': 'linguality', 'model': 'LingualityType',       
         'vfield': 'name', 'fieldchoice': LINGUALITY_TYPE},
        {'name': 'Nativeness',  'type': 'm2o',  'path': 'lingualityNativeness', 'fkfield': 'linguality', 'model': 'LingualityNativeness',      
         'vfield': 'name', 'fieldchoice': LINGUALITY_NATIVENESS},
        {'name': 'Age group',   'type': 'm2o',  'path': 'lingualityAgeGroup',   'fkfield': 'linguality', 'model': 'LingualityAgeGroup', 
         'vfield': 'name', 'fieldchoice': LINGUALITY_AGEGROUP},
        {'name': 'Status',      'type': 'm2o',  'path': 'lingualityStatus',     'fkfield': 'linguality', 'model': 'LingualityStatus',        
         'vfield': 'name', 'fieldchoice': LINGUALITY_STATUS},
        {'name': 'Variant',     'type': 'm2o',  'path': 'lingualityVariant',    'fkfield': 'linguality', 'model': 'LingualityVariant',         
         'vfield': 'name', 'fieldchoice': LINGUALITY_VARIANT},
        {'name': 'Multiple',    'type': 'm2o',  'path': 'multilingualityType',  'fkfield': 'linguality', 'model': 'MultilingualityType',         
         'vfield': 'name', 'fieldchoice': LINGUALITY_MULTI},

        ]

    class Meta:
        verbose_name_plural = "Lingualities"

    def __str__(self):
        fld_type = m2m_combi(self.linguality_types)
        fld_nati = m2m_combi(self.linguality_nativenesses)
        fld_ageg = m2m_combi(self.linguality_agegroups)
        fld_stat = m2m_combi(self.linguality_statuses)
        fld_vari = m2m_combi(self.linguality_variants)
        fld_mult = m2m_combi(self.multilinguality_types)
        return "t:{}, n:{}, a:{}, s:{}, v:{}, m:{}".format(fld_type, fld_nati, fld_ageg, fld_stat, fld_vari, fld_mult)

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            # We should create a new instance
            obj = Linguality.objects.create()

            # And now call the standard custom_add() method
            oParams['linguality'] = obj
            obj.custom_add(oItem, oParams, **kwargs)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("Linguality/get_instance")
        return obj

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # copy 1-to-m- fields
        copy_m2m(self, new_copy, "linguality_types")
        copy_m2m(self, new_copy, "linguality_nativenesses")
        copy_m2m(self, new_copy, "linguality_agegroups")
        copy_m2m(self, new_copy, "linguality_statuses")
        copy_m2m(self, new_copy, "linguality_variants")
        copy_m2m(self, new_copy, "multilinguality_types")
        # Return the new copy
        return new_copy


class LanguageIso(models.Model):
    """Language and ISO-639-3 letter code"""

    # [1] Three letter code
    code = models.CharField("Three letter code", max_length=3)
    # [0-1] URL to an ISO description of the 3-letter code
    url = models.URLField("Description", blank=True, null=True)

    # [1] Obligatory time of creation
    created = models.DateTimeField(default=get_current_datetime)

    def __str__(self):
        sBack = self.code
        return sBack

    def get_created(self):
        sBack = self.created.strftime("%d/%b/%Y %H:%M")
        return sBack

    def get_view(self):
        name = ""
        obj = self.code_languagenames.first()
        if not obj is None:
            name = obj.name
        sBack = "[{}] {}".format(self.code, name)
        return sBack


class LanguageName(models.Model):
    """Name of an ISO language"""

    # [1] Language name
    name = models.CharField("Full language name", blank=True, max_length=MAX_STRING_LEN)
    # [0-1] URL to a description of the language Name for the 3-letter code
    url = models.URLField("URL", blank=True, null=True)
    # [1] Obligatorily belongs to one particular ISO-code
    iso = models.ForeignKey(LanguageIso, on_delete=models.CASCADE, related_name="iso_languagenames")

    # [1] Obligatory time of creation
    created = models.DateTimeField(default=get_current_datetime)

    def __str__(self):
        sBack = "[{}] {}".format(self.iso.code, self.name)
        return sBack

    def get_created(self):
        sBack = self.created.strftime("%d/%b/%Y %H:%M")
        return sBack

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            sLngName = oItem.get("LanguageName")
            oIso = oItem.get("ISO639")
            if not oIso is None:
                # Try to get the language code
                sCode = oIso.get("iso-639-3-code")

                if sLngName is None or sLngName == "":
                    # Only search for the code
                    obj = LanguageName.objects.filter(iso__code=sCode).first()
                else:
                    # (1) Specific search: name + code
                    obj = LanguageName.objects.filter(name__iexact=sLngName, iso__code=sCode).first()

                    # (2) Less specific?
                    if obj is None:
                        obj = LanguageName.objects.filter(iso__code=sCode).first()

        except:
            msg = oErr.get_error_message()
            oErr.DoError("Language/get_instance")
        return obj
    

class Language(models.Model):
    """Language that is used in this collection"""

    # [1] Obligatory link to this language's entry inside the table FieldChoice
    name = models.CharField("Language in collection", choices=build_choice_list("language.name"),
                            max_length=5, help_text=get_help("language.name"), default='0')
    # [0-1] To be constructed: link to correct entry in [LanguageName]
    langname = models.ForeignKey(LanguageName, blank=True, null=True, on_delete=models.CASCADE, related_name = "langname_languages")
    
    # Scheme for downloading and uploading
    specification = [
        {'name': 'Language',    'type': 'fk', 'path': 'Language',
         'fkfield': 'langname', 'model': 'LanguageName'},
        ]

    def __str__(self):
        idt = m2m_identifier(self.collection_set)
        if idt == "" or idt == "-":
            # OLD:
            # sBack = "[DOC] " + choice_english("language.name", self.name)
            sBack = "[DOC] {}".format(self.langname)
        else:
            # OLD:
            # sBack = "[{}] {}".format(idt,choice_english("language.name", self.name))
            sBack = "[{}] {}".format(idt,self.langname)
        return sBack

    def get_view(self):
        html = []
        # Name of the language
        if self.langname is None:
            html.append(self.get_name_display())
            html.append("(no iso code)")
        else:
            html.append(self.langname.name)
            # Isocode
            html.append("[{}]".format(self.langname.iso.code))

        # Combine
        sBack = " ".join(html)
        return sBack


class DocumentationLanguage(CollbankModel, Language):

    # [1]     Each documentation object can have [0-n] languages associated with it
    documentationParent = models.ForeignKey("Documentation", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="doc_languages")
    
    # Scheme for downloading and uploading
    specification = [
        {'name': 'Language',    'type': 'fk', 'path': 'Language',
         'fkfield': 'langname', 'model': 'LanguageName'},
        ]

    def __str__(self):
        sBack = "[unclear]"
        # There is only ONE collection parent
        doc = self.documentationParent
        if doc != None:
            col = Collection.objects.filter(documentation=doc).first()
            if col is None:
                sBack = "[col?] {}".format(self.langname)
            else:
                idt = col.identifier
                sBack = "[{}] {}".format(idt,self.langname)

        return sBack

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            # We should create a new instance
            documentation = oParams.get("documentation")
            obj = DocumentationLanguage.objects.create(documentationParent=documentation)

            # Get the LanguageName instance
            obj.langname = LanguageName.get_instance(oItem, oParams, **kwargs)
            obj.save()

            sCheck = "{}".format(obj)

        except:
            msg = oErr.get_error_message()
            oErr.DoError("DocumentationLanguage/get_instance")
        return obj

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy


class CollectionLanguage(Language):

    # [1]     Each collection can have [0-n] languages associated with it
    collectionParent = models.ForeignKey("Collection", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="coll_languages")

    def __str__(self):
        idt = self.collectionParent.identifier
        # OLD: sBack = "[{}] {}".format(idt,choice_english("language.name", self.name))
        sBack = "[{}] {}".format(idt,self.langname)
        return sBack

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            # We should create a new instance
            collection = oParams.get("collection")
            obj = CollectionLanguage.objects.create(collectionParent=collection)

            # Get the LanguageName instance
            obj.langname = LanguageName.get_instance(oItem, oParams, **kwargs)
            obj.save()

            sCheck = "{}".format(obj)

        except:
            msg = oErr.get_error_message()
            oErr.DoError("CollectionLanguage/get_instance")
        return obj


class LanguageDisorder(models.Model):
    """Language that is used in this collection"""

    # [1]
    name = models.CharField("Language disorder", max_length=50, help_text=get_help("languagedisorder.name"), default='unknown')
    # [1]     Each collection can have [0-n] language disorders
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="collection12m_languagedisorder")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        sName = self.name
        return "[{}] {}".format(idt, sName)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.name


class Relation(CollbankModel, models.Model):
    """Language that is used in this collection"""

    # [1]
    name = models.CharField("Summary", max_length=80, help_text=get_help(RELATION_NAME ), default='-')
    # [0-1] Type of relation
    rtype = models.CharField(choices=build_choice_list(RELATION_TYPE), max_length=5, help_text=get_help(RELATION_TYPE), default='0', verbose_name="type of relation")
    # [0-1] The collection with which the relation holds
    related = models.ForeignKey("Collection", blank=True, null=True, on_delete=models.CASCADE, related_name="relatedcollection", verbose_name="with collection")
    # [0-1] The externalcollection with which the relation holds
    extrel = models.ForeignKey("ExtColl", blank=True, null=True, on_delete=models.CASCADE, related_name="relatedextcoll", verbose_name="with external collection")
    # [1]     Each collection can have [0-n] relations
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="collection12m_relation")

    # Scheme for downloading and uploading
    specification = [
        {'name': 'Name',            'type': 'field', 'path': 'name'},
        {'name': 'Relation type',   'type': 'field', 'path': 'rtype',   'fieldchoice': RELATION_TYPE},
        ]

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        if self.rtype != '0':
            type = choice_english(RELATION_TYPE, self.rtype)
        else:
            type = '(unspecified relation)'
        if self.related == None:
            if self.extrel == None:
                withcoll = "(unspecified collection)"
            else:
                withcoll = self.extrel.identifier
        else:
            withcoll = self.related.identifier
        return "[{}] {} [{}]".format(idt,type, withcoll)

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            # Make sure we have the right collection
            collection = oParams.get("collection")

            # We should create a new instance
            obj = Relation.objects.create(collection=collection)

            # And now call the standard custom_add() method
            obj.custom_add(oItem, oParams, **kwargs)

            # Possibly add 'related' and 'extrel'
            # NOTE: they are not used when importing...

        except:
            msg = oErr.get_error_message()
            oErr.DoError("Relation/get_instance")
        return obj

    def get_relation_fname(self):
        # Show that this is a tab-separated CSV
        sCsvFile = "cbrelation_{}_{}.tsv".format(self.collection.id, self.id)
        return sCsvFile

    def get_relation_path(self):
        """Get the full path to a registry file storing this relation"""

        sCsvFile = self.get_relation_fname()
        fPath = os.path.abspath(os.path.join(REGISTRY_DIR, sCsvFile))
        return fPath

    def get_relation_url(self):
        """Get the URL to this relation"""
        sCsvFile = self.get_relation_fname()
        return "{}{}".format(REGISTRY_URL, sCsvFile)

    def save_relation_file(self):
        # Transform the details of this relation into CSV
        related = ""
        if self.related != None and self.related.identifier != "":
            related = self.related.identifier
        elif self.extrel != None and self.extrel.identifier != "":
            related = self.extrel.identifier
        else:
            related= "(No relation specified)"
        # Start creating CSV lines
        lCsv = []
        lCsv.append("{}\t{}\t{}".format("Collection", "Type of relation", "Collection"))
        lCsv.append("{}\t{}\t{}".format(self.collection.identifier, self.get_rtype_display(), related))
        sCsv = "\n".join(lCsv)
        # Save the CSV to a text file
        fPath = self.get_relation_path()
        with open(fPath, encoding="utf-8", mode="w") as f:  
            f.write(sCsv)
        return fPath

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        """How this relation must be shown in the detail-view"""
        return self.__str__()


class Domain(models.Model):
    """Domain"""

    # Description of this domain (to be copied from [DomainDescription]
    name = models.TextField("Domain", help_text=get_help(DOMAIN_NAME), default='0')
    # [1]     Each collection can have [0-n] domains
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="collection12m_domain")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        if self.collection_id < 0:
            return "Empty"
        else:
            idt = self.collection.identifier
            sName = self.name
            return "[{}] {}".format(idt,sName)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.name
    

class AccessAvailability(models.Model):
    """Access availability"""

    class Meta:
        verbose_name_plural = "Access availabilities"

    name = models.CharField("Access availability", choices=build_choice_list(ACCESS_AVAILABILITY), max_length=5, help_text=get_help(ACCESS_AVAILABILITY), default='0')
    # [1]     Each access instance can have [0-n] availabilities
    access = models.ForeignKey("Access", blank=False, null=False, default=-1, on_delete=models.CASCADE, related_name="acc_availabilities")

    def __str__(self):
        return choice_english(ACCESS_AVAILABILITY, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()

    
class LicenseName(models.Model):
    """Name of the license"""

    name = models.TextField("Name of the license", help_text=get_help('access.licenseName'))
    # [1]     Each access instance can have [0-n] licence Names
    access = models.ForeignKey("Access", blank=False, null=False, default=-1, on_delete=models.CASCADE, related_name="acc_licnames")

    def __str__(self):
        return self.name[:50]

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.name


class LicenseUrl(models.Model):
    """URL of the license"""

    name = models.URLField("URL of the license", help_text=get_help('access.licenseURL'))
    # [1]     Each access instance can have [0-n] license URLs
    access = models.ForeignKey("Access", blank=False, null=False, default=-1, on_delete=models.CASCADE, related_name="acc_licurls")

    def __str__(self):
        return self.name

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.name


class NonCommercialUsageOnly(models.Model):
    """Whether access is restricted to non-commerical usage"""

    class Meta:
        verbose_name_plural = "Non-commercial usage only types"

    name = models.CharField("Non-commercial usage only access", choices=build_choice_list(ACCESS_NONCOMMERCIAL ), 
                            max_length=5, help_text=get_help(ACCESS_NONCOMMERCIAL ), default='0')

    def __str__(self):
        return choice_english(ACCESS_NONCOMMERCIAL, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class AccessContact(models.Model):
    """Contact details for access"""

    person = models.TextField("Access: person to contact", help_text=get_help('access.contact.person'))
    address = models.TextField("Access: address of contact", help_text=get_help('access.contact.address'))
    email = models.EmailField("Access: email of contact", help_text=get_help('access.contact.email'))
    # [1]     Each access instance can have [0-n] contacts
    access = models.ForeignKey("Access", blank=False, null=False, default=-1, on_delete=models.CASCADE, related_name="acc_contacts")

    def __str__(self):
        return "{}: {}, ({})".format(
            self.person, self.address[:30], self.email)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            # We should create a new instance
            person = oItem.get("person", "-")
            address = oItem.get("address", "-")
            email = oItem.get("email", "-")
            access = oParams.get("access")
            if access is None:
                oErr.Status("WARNING: AccessContact doesn't get a valid [access] FK")
            else:
                obj = AccessContact.objects.create(person=person, address=address, email=email, access=access)

        except:
            msg = oErr.get_error_message()
            oErr.DoError("AccessContact/get_instance")
        return obj

    def get_view(self):
        return self.__str__()


class AccessWebsite(models.Model):
    """Website to access the collection"""

    name = models.URLField("Website to access the collection", help_text=get_help('access.website'))
    # [1]     Each access instance can have [0-n] websites
    access = models.ForeignKey("Access", blank=False, null=False, default=-1, on_delete=models.CASCADE, related_name="acc_websites")

    def __str__(self):
        return self.name

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.name


class AccessMedium(models.Model):
    """Medium used to access a resource of the collection"""

    format = models.CharField("Resource medium", choices=build_choice_list(ACCESS_MEDIUM ), max_length=5, help_text=get_help(ACCESS_MEDIUM ), default='0')
    # [1]     Each access instance can have [0-n] mediums
    access = models.ForeignKey("Access", blank=False, null=False, default=-1, on_delete=models.CASCADE, related_name="acc_mediums")

    def __str__(self):
        return choice_english(ACCESS_MEDIUM, self.format)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_format_display()


class Access(CollbankModel, models.Model):
    """Access to the resources"""

    class Meta:
        verbose_name_plural = "Accesses"

    name = models.TextField("Name of this access type", default='-')
    # nonCommercialUsageOnly (0-1;c yes; no)
    nonCommercialUsageOnly = models.ForeignKey(NonCommercialUsageOnly, blank=True, null=True, on_delete=models.SET_NULL)
    # ISBN (0-1;f)
    ISBN = models.TextField("ISBN of collection", help_text=get_help('access.ISBN'), blank=True)
    # ISLRN (0-1;f)
    ISLRN = models.TextField("ISLRN of collection", help_text=get_help('access.ISLRN'), blank=True)

    # Scheme for downloading and uploading
    specification = [
        {'name': 'Collection ISBN',     'type': 'field', 'path': 'ISBN'},
        {'name': 'Collection ISLRN',    'type': 'field', 'path': 'ISLRN'},
        {'name': 'Non-commercial only', 'type': 'func',  'path': 'nonCommercialUsageOnly' },

        {'name': 'Medium types',        'type': 'm2o',   'path': 'medium',      'fkfield': 'access', 'model': 'AccessMedium',       
         'vfield': 'format', 'fieldchoice': ACCESS_MEDIUM},
        {'name': 'Websites',            'type': 'm2o',   'path': 'website',     'fkfield': 'access', 'model': 'AccessWebsite',      'vfield': 'name'},
        {'name': 'Availabilities',      'type': 'm2o',   'path': 'availability','fkfield': 'access', 'model': 'AccessAvailability', 
         'vfield': 'name', 'fieldchoice': ACCESS_AVAILABILITY},
        {'name': 'License names',       'type': 'm2o',   'path': 'licenseName', 'fkfield': 'access', 'model': 'LicenseName',        'vfield': 'name'},
        {'name': 'License URLs',        'type': 'm2o',   'path': 'licenseURL',  'fkfield': 'access', 'model': 'LicenseUrl',         'vfield': 'name'},
        {'name': 'Access contacts',     'type': 'm2o',   'path': 'contact',     'fkfield': 'access', 'model': 'AccessContact'},

        ]

        #append_item(coll_access, "Name", "1", "single", access.name)
        #
        #append_item(coll_access, "ISBN", "0-1", "single", access.ISBN)
        #append_item(coll_access, "ISLRN", "0-1", "single", access.ISLRN)
        #append_item(coll_access, "Non-commercial usage", "0-1", "single", access.nonCommercialUsageOnly)
        #
        #append_item(coll_access, "Medium(s)", "0-n", "list", access.acc_mediums.all())
        #append_item(coll_access, "Website(s)", "0-n", "list", access.acc_websites.all())
        #append_item(coll_access, "Availability", "0-n", "list", access.acc_availabilities.all())
        #append_item(coll_access, "License name(s)", "0-n", "list", access.acc_licnames.all())
        #append_item(coll_access, "Licence URL(s)", "0-n", "list", access.acc_licurls.all())
        #append_item(coll_access, "Contact(s)", "0-n", "list", access.acc_contacts.all())

    def __str__(self):
        sName = self.name
        return sName[:50]

    def custom_set(self, path, value, **kwargs):
        """Set related items"""

        bResult = True
        oErr = ErrHandle()
        try:
            profile = kwargs.get("profile")
            username = kwargs.get("username")
            team_group = kwargs.get("team_group")
            value_lst = []
            if isinstance(value, str) and value[0] != '[':
                value_lst = value.split(",")
                for idx, item in enumerate(value_lst):
                    value_lst[idx] = value_lst[idx].strip()
            elif isinstance(value, list):
                value_lst = value

            # See what this one is
            if path == "nonCommercialUsageOnly":
                # Find out what the index in FieldChoice is
                cvalue = choice_value(ACCESS_NONCOMMERCIAL, value)
                if cvalue < 0:
                    # Cannot find this FC
                    oErr.Status("Access nonCommercialUsageOnly: cannot find value [{}]".format(value))
                else:
                    # Create a unique object in [NonCommercialUsageOnly]
                    obj = NonCommercialUsageOnly.objects.create(name=cvalue)
                    # Set the FK to this unique object
                    self.nonCommercialUsageOnly = obj

        except:
            msg = oErr.get_error_message()
            oErr.DoError("Access/custom_set")
            bResult = False
        return bResult

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            # We should create a new instance
            name = oItem.get("name", "-")
            obj = Access.objects.create(name=name)

            # And now call the standard custom_add() method
            oParams['access'] = obj
            obj.custom_add(oItem, oParams, **kwargs)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("Access/get_instance")
        return obj

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Copy the 1-to-m stuff
        copy_m2m(self, new_copy, "acc_availabilities")
        copy_m2m(self, new_copy, "acc_licnames")
        copy_m2m(self, new_copy, "acc_licurls")
        copy_m2m(self, new_copy, "acc_contacts")
        copy_m2m(self, new_copy, "acc_websites")
        copy_m2m(self, new_copy, "acc_mediums")
        # Copy the FK stuff
        copy_fk(self, new_copy, "nonCommercialUsageOnly")
        # Return the new copy
        return new_copy


class PID(models.Model):
    """Persistent identifier"""

    class Meta:
        verbose_name_plural = "PIDs"

    # [1]
    code = models.TextField("Persistent identifier of the collection", help_text=get_help('PID'))
    # [1]     Each collection can have [0-n] PIDs
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="collection12m_pid")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        return "[{}] {}".format(idt,self.code[:50])

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.code


class Organization(models.Model):
    """Name of organization"""

    name = models.TextField("Name of organization", help_text=get_help('resourceCreator.organization'))
    # [1]     Each resourceCreator can have [0-n] organizations
    resourceCreator = models.ForeignKey("ResourceCreator", blank=False, null=False, default=-1, on_delete=models.CASCADE, related_name="organizations")

    def __str__(self):
        return self.name[:50]

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy


class Person(models.Model):
    """Name of person"""

    name = models.TextField("Name of person", help_text=get_help('resourceCreator.person'))
    # [1]     Each resourceCreator can have [0-n] persons
    resourceCreator = models.ForeignKey("ResourceCreator", blank=False, null=False, default=-1, on_delete=models.CASCADE, related_name="persons")

    def __str__(self):
        return self.name[:50]

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy


class ResourceCreator(CollbankModel, models.Model):
    """Creator of this resource"""

    # FKs pointing to ResourceCreator: 
    # - Organization
    # - Person

    # [1]     Each collection can have [0-n] resource creators
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="collection12m_resourcecreator")

    # ============= Old, legacy, do not use ================
    # [1] Organization that created the resource
    organization = models.ManyToManyField(Organization, blank=False, related_name="resourcecreatorm2m_organization")

    # Scheme for downloading and uploading
    specification = [
        {'name': 'Person',      'type': 'm2o',  'path': 'person',       'fkfield': 'resourceCreator', 'model': 'Person',        'vfield': 'name'},
        {'name': 'Organization','type': 'm2o',  'path': 'organization', 'fkfield': 'resourceCreator', 'model': 'Organization',  'vfield': 'name'},

        ]

    def __str__(self):
        # OLD: idt = self.collection.identifier
        orgs = m2m_combi(self.organizations)    # One or more organizations
        pers = m2m_combi(self.persons)          # M-to-1 link from Person to ResourceCreator
        sBack = "o:{} p:{}".format(orgs, pers)
        # OLD sBack = "[{}] o:{}|p:{}".format(idt,orgs,pers)
        return sBack

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Copy the 1-to-m stuff
        copy_m2m(self, new_copy, "organizations")
        copy_m2m(self, new_copy, "persons")
        # Return the new copy
        return new_copy

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            collection = oParams.get("collection")
            if collection is None:
                # Cannot process this
                pass
            else:
                # We should create a new instance, based on this collection
                obj = ResourceCreator.objects.create(collection=collection)

                # And now call the standard custom_add() method to add persons and organizations
                oParams['resourceCreator'] = obj
                obj.custom_add(oItem, oParams, **kwargs)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("ResourceCreator/get_instance")
        return obj

    def get_view(self):
        """The view for detail-view"""

        orgs = m2m_combi(self.organizations)    # One or more organizations
        pers = m2m_combi(self.persons)          # M-to-1 link from Person to ResourceCreator
        sBack = "{} ({})".format(pers, orgs)
        return sBack


class DocumentationType(models.Model):
    """Kind of documentation"""

    format = models.CharField("Kind of documentation", choices=build_choice_list(DOCUMENTATION_TYPE ), max_length=5, help_text=get_help(DOCUMENTATION_TYPE ), default='0')
    # [1]
    documentation = models.ForeignKey("Documentation", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="doc_types")

    def __str__(self):
        return choice_english(DOCUMENTATION_TYPE, self.format)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_format_display()


class DocumentationFile(models.Model):
    """File name for documentation"""

    name = models.TextField("File name for documentation", help_text=get_help('documentation.file'))
    # [1]
    documentation = models.ForeignKey("Documentation", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="doc_files")

    def __str__(self):
        return self.name[:50]

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.name


class DocumentationUrl(models.Model):
    """URL of documentation"""

    # [1] Obligatory name
    name = models.URLField("URL of documentation", help_text=get_help('documentation.url'))
    # [1]
    documentation = models.ForeignKey("Documentation", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="doc_urls")

    def __str__(self):
        return self.name

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.name


class Documentation(CollbankModel, models.Model):
    """Creator of this resource"""

    # Many-to-one relations:
    #   DocumentationType (0-n; c)
    #   DocumentationFile (0-n; f)
    #   DocumentationUrl (0-n; f)
    #   DocumentationLanguage (1-n; c)

    # Scheme for downloading and uploading
    specification = [
        {'name': 'Documentation type',      'type': 'm2o',  'path': 'documentationType','fkfield': 'documentation', 'model': 'DocumentationType',   'vfield': 'format'},
        {'name': 'Documentation File',      'type': 'm2o',  'path': 'fileName',         'fkfield': 'documentation', 'model': 'DocumentationFile',   'vfield': 'name'},
        {'name': 'Documentation URL',       'type': 'm2o',  'path': 'url',              'fkfield': 'documentation', 'model': 'DocumentationUrl',    'vfield': 'name'},
        {'name': 'Documentation language',  'type': 'm2o',  'path': 'Language',         'fkfield': 'documentation', 'model': 'DocumentationLanguage'},

        ]

    def __str__(self):
        fld_tp = m2m_combi(self.doc_types)
        fld_fl = m2m_combi(self.doc_files)
        fld_ur = m2m_combi(self.doc_urls)
        fld_ln = m2m_combi(self.doc_languages)
        lBack = []
        if fld_tp != "": lBack.append("t:{}".format(fld_tp))
        if fld_fl != "": lBack.append("f:{}".format(fld_fl))
        if fld_ur != "": lBack.append("u:{}".format(fld_ur))
        if fld_ln != "": lBack.append("l:{}".format(fld_ln))
        if len(lBack) > 0:
            sBack = " ".join(lBack)
        else:
            sBack = "(empty)"
        return sBack

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            # We should create a new instance
            obj = Documentation.objects.create()

            oParams['documentation'] = obj
            # And now call the standard custom_add() method
            obj.custom_add(oItem, oParams, **kwargs)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("Documentation/get_instance")
        return obj

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Copy the 1-to-m stuff
        copy_m2m(self, new_copy, "doc_languages")
        copy_m2m(self, new_copy, "doc_types")
        copy_m2m(self, new_copy, "doc_files")
        copy_m2m(self, new_copy, "doc_urls")
        # Return the new copy
        return new_copy


class ValidationType(models.Model):
    """Validation type"""

    name = models.CharField("Validation type", choices=build_choice_list(VALIDATION_TYPE), max_length=5, help_text=get_help(VALIDATION_TYPE), default='0')

    def __str__(self):
        return choice_english(VALIDATION_TYPE, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class ValidationMethod(models.Model):
    """Validation method"""

    name = models.CharField("Validation method", choices=build_choice_list(VALIDATION_METHOD), max_length=5, help_text=get_help(VALIDATION_METHOD), default='0')
    # [1]
    validation = models.ForeignKey("Validation", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="validationmethods")

    def __str__(self):
        return choice_english(VALIDATION_METHOD, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class Validation(CollbankModel, models.Model):
    """Validation"""

    # type (0-1; c)
    type = models.ForeignKey(ValidationType, blank=True, null=True, on_delete=models.SET_NULL)
    # Many-to-one relations:
    # ValidationMethod (0-n; c)

    # Scheme for downloading and uploading
    specification = [
        {'name': 'Validation type',   'type': 'fkc',    'path': 'type',  'fkfield': 'validation', 'model': 'ValidationType',    
         'vfield': 'name', 'fieldchoice': VALIDATION_TYPE},
        {'name': 'Validation method', 'type': 'm2o',    'path': 'method','fkfield': 'validation', 'model': 'ValidationMethod',  
         'vfield': 'name', 'fieldchoice': VALIDATION_METHOD},
        ]

    def __str__(self):
        return "{}:{}".format(
            self.type,
            m2m_combi(self.validationmethods))

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Copy the 1-to-m stuff
        copy_m2m(self, new_copy, "validationmethods")
        # Copy the FK stuff
        copy_fk(self, new_copy, "type")
        # Return the new copy
        return new_copy

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            # We should create a new instance
            obj = Validation.objects.create()

            ## Extract possible parameters
            #validation_type = oItem.get("type")
            #validation_method = oItem.get("method")

            ## Process type
            #if not validation_type is None:
            #    obj.type = ValidationType.objects.create(name=choice_value(VALIDATION_TYPE, validation_type))
            #    obj.save()

            ## Process method
            #if not validation_method is None:
            #    instance = ValidationMethod.objects.create(validation=obj, name=choice_value(VALIDATION_METHOD, validation_method))

            # And now call the standard custom_add() method
            oParams['validation'] = obj
            obj.custom_add(oItem, oParams, **kwargs)

        except:
            msg = oErr.get_error_message()
            oErr.DoError("Validation/get_instance")
        return obj
    

class ProjectFunder(models.Model):
    """Funder of project"""

    name = models.TextField("Funder of project", help_text=get_help('project.funder'))
    # [1]
    project = models.ForeignKey("Project", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="funders")

    def __str__(self):
        # OLD: sBack = self.name[:50]
        sBack = self.name
        return sBack

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy


class ProjectUrl(models.Model):
    """URL of project"""

    name = models.URLField("URL of project", help_text=get_help('project.url'))

    def __str__(self):
        return self.name

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy


class Project(CollbankModel, models.Model):
    """Project supporting a resource from the collection"""

    # title (0-1; f)
    title = models.TextField("Project title", help_text=get_help('project.title'))
    # url (0-1; f)
    URL = models.ForeignKey(ProjectUrl, blank=True, null=True, on_delete=models.SET_NULL)

    # [1]     Each collection can have [0-n] projects
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="collection12m_project")

    ## ================= Many to many (stale??) ============
    ## funder (0-n; f)
    #funder = models.ManyToManyField(ProjectFunder, blank=True, related_name="projectm2m_funder")

    # Scheme for downloading and uploading
    specification = [
        {'name': 'Title',   'type': 'field','path': 'title',    'vfield': 'name'},
        {'name': 'URL',     'type': 'fkc',  'path': 'URL',      'fkfield': 'project', 'model': 'ProjectUrl',     'vfield': 'name'},
        {'name': 'Funder',  'type': 'm2o',  'path': 'funder',   'fkfield': 'project', 'model': 'ProjectFunder',  'vfield': 'name'},
        ]

    def __str__(self):
        lHtml = []
        lHtml.append("[{}] ".format(self.collection.identifier))
        if not self.title is None and self.title != "":
            lHtml.append("{}".format(self.title[:50]))
        elif not self.URL is None:
            lHtml.append(self.URL.name)
        sBack = "".join(lHtml)
        return sBack

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Copy the 1-to-m stuff
        copy_m2m(self, new_copy, "funders")
        # Copy the FK stuff
        copy_fk(self, new_copy, "URL")
        # Return the new copy
        return new_copy

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            # We should create a new instance, based on this collection
            collection = oParams.get("collection")
            if collection is None:
                # Cannot process this
                pass
            else:
                obj = Project.objects.create(collection=collection)

                # And now call the standard custom_add() method to add persons and organizations
                oParams['project'] = obj
                obj.custom_add(oItem, oParams, **kwargs)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("Project/get_instance")
        return obj

    def get_view(self):
        """The view for detail-view"""
        sFunders = m2m_combi(self.funders)
        return "{} <a href=\"{}\">site</a> (Funder: <span class=\"coll-funder\">{}</span>)".format(self.title, self.URL, sFunders)


class CharacterEncoding(models.Model):
    """Type of character-encoding"""

    name = models.CharField("Character encoding", choices=build_choice_list(CHARACTERENCODING), max_length=5, help_text=get_help(CHARACTERENCODING), default='0')
    # [1]     Each written corpus can have [0-n] character encodings
    writtenCorpus = models.ForeignKey("WrittenCorpus", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="charenc_writtencorpora")

    def __str__(self):
        return choice_english(CHARACTERENCODING, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy


class WrittenCorpus(CollbankModel, models.Model):
    """Written Corpus"""

    class Meta:
        verbose_name_plural = "Written corpora"

    # numberOfAuthors:    (0-1;f)
    numberOfAuthors = models.CharField("Number of authors", blank=True, help_text=get_help(WRITTENCORPUS_AUTHORNUMBER), max_length=20, default="unknown")
    # authorDemographics: (0-1;f)
    authorDemographics = models.TextField("Author demographics", blank=True, help_text=get_help(WRITTENCORPUS_AUTHORDEMOGRAPHICS), default='-')

    # Scheme for downloading and uploading
    specification = [
        {'name': 'Number of authors',   'type': 'field', 'path': 'numberOfAuthors'},
        {'name': 'Author demographics', 'type': 'field', 'path': 'authorDemographics'},

        ]

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = "TODO"
        sEnc = m2m_combi(self.charenc_writtencorpora) # m2m_combi(self.characterEncoding)
        return "[{}]: {}".format(idt, sEnc)

    def custom_add(oColl, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        bOverwriting = False
        bSkip = False
        lst_msg = []
        try:
            profile = kwargs.get("profile")
            username = kwargs.get("username")
            team_group = kwargs.get("team_group")
            source = kwargs.get("source")
            keyfield = kwargs.get("keyfield", "name")

        except:
            msg = oErr.get_error_message()
            oErr.DoError("WrittenCorpus/custom_add")
        return obj

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Copy the 1-to-m stuff
        copy_m2m(self, new_copy, 'charenc_writtencorpora')
        # Return the new copy
        return new_copy

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            # We should create a new instance
            obj = WrittenCorpus.objects.create()

            # And now call the standard custom_add() method
            obj.custom_add(oItem, oParams, **kwargs)

        except:
            msg = oErr.get_error_message()
            oErr.DoError("WrittenCorpus/get_instance")
        return obj


class RecordingEnvironment(models.Model):
    """Environment for the recording"""

    # [1]
    name = models.CharField("Environment for the recording", choices=build_choice_list(SPEECHCORPUS_RECORDINGENVIRONMENT), max_length=5, help_text=get_help(SPEECHCORPUS_RECORDINGENVIRONMENT), default='0')
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="recordingenvironments")

    def __str__(self):
        return choice_english(SPEECHCORPUS_RECORDINGENVIRONMENT, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class Channel(models.Model):
    """Channel for the speech corpus"""

    name = models.CharField("Channel for the speech corpus", choices=build_choice_list(SPEECHCORPUS_CHANNEL), max_length=5, help_text=get_help(SPEECHCORPUS_CHANNEL), default='0')
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="channels")

    def __str__(self):
        return choice_english(SPEECHCORPUS_CHANNEL, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class ConversationalType(models.Model):
    """Type of conversation"""

    name = models.CharField("Type of conversation", choices=build_choice_list(SPEECHCORPUS_CONVERSATIONALTYPE), max_length=5, help_text=get_help(SPEECHCORPUS_CONVERSATIONALTYPE), default='0')
    # [1]     Each speech corpus can have [0-n] conversational types
    speechCorpus = models.ForeignKey("SpeechCorpus", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="conversationaltypes")

    def __str__(self):
        return choice_english(SPEECHCORPUS_CONVERSATIONALTYPE, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class RecordingCondition(models.Model):
    """Recording condition"""

    name = models.TextField("Recording condition", help_text=get_help('speechcorpus.recordingConditions'))
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="recordingconditions")

    def __str__(self):
        # Max 80 characters
        return self.name[:80]

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.name


class SocialContext(models.Model):
    """Social context"""

    name = models.CharField("Social context", choices=build_choice_list(SPEECHCORPUS_SOCIALCONTEXT), max_length=5, help_text=get_help(SPEECHCORPUS_SOCIALCONTEXT), default='0')
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="socialcontexts")

    def __str__(self):
        return choice_english(SPEECHCORPUS_SOCIALCONTEXT, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class PlanningType(models.Model):
    """Type of planning"""

    name = models.CharField("Type of planning", choices=build_choice_list(SPEECHCORPUS_PLANNINGTYPE), max_length=5, help_text=get_help(SPEECHCORPUS_PLANNINGTYPE), default='0')
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="planningtypes")

    def __str__(self):
        return choice_english(SPEECHCORPUS_PLANNINGTYPE, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class Interactivity(models.Model):
    """Interactivity"""

    class Meta:
        verbose_name_plural = "Interactivities"

    name = models.CharField("Interactivity", choices=build_choice_list(SPEECHCORPUS_INTERACTIVITY), max_length=5, help_text=get_help(SPEECHCORPUS_INTERACTIVITY), default='0')
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="interactivities")

    def __str__(self):
        return choice_english(SPEECHCORPUS_INTERACTIVITY, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class Involvement(models.Model):
    """Type of involvement"""

    name = models.CharField("Type of involvement", choices=build_choice_list(SPEECHCORPUS_INVOLVEMENT), max_length=5, help_text=get_help(SPEECHCORPUS_INVOLVEMENT), default='0')
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="involvements")

    def __str__(self):
        return choice_english(SPEECHCORPUS_INVOLVEMENT, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class Audience(models.Model):
    """Audience"""

    name = models.CharField("Audience", choices=build_choice_list(SPEECHCORPUS_AUDIENCE), max_length=5, help_text=get_help(SPEECHCORPUS_AUDIENCE), default='0')
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="audiences")

    def __str__(self):
        return choice_english(SPEECHCORPUS_AUDIENCE, self.name)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy

    def get_view(self):
        return self.get_name_display()


class AudioFormat(models.Model):
    """AudioFormat"""

    # speechCoding (0-1; f)
    speechCoding = models.CharField("Speech coding", blank=True, help_text=get_help(AUDIOFORMAT_SPEECHCODING), max_length=25, default='unknown')
    # samplingFrequency (0-1; f)
    samplingFrequency = models.CharField("Sampling frequency", blank=True, help_text=get_help('audioformat.samplingFrequency'), max_length=25, default='unknown')
    # compression  (0-1; f)
    compression = models.CharField("Compression", blank=True, help_text=get_help('audioformat.compression'), max_length=25, default='unknown')
    # bitResolution  (0-1; f)
    bitResolution = models.CharField("Bit resolution", blank=True, help_text=get_help('audioformat.bitResolution'), max_length=25, default='unknown')
    # [1]     Each speech corpus can have [0-n] AudioFormats
    speechCorpus = models.ForeignKey("SpeechCorpus", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="audioformats")

    def __str__(self):
        sc = self.speechCoding
        sf = self.samplingFrequency
        cmp = self.compression
        br = self.bitResolution
        sMsg = "sc:{}, sf:{}, cmp:{}, br:{}".format(sc, sf, cmp, br)
        return sMsg

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy


class SpeechCorpus(CollbankModel, models.Model):
    """Spoken corpus"""

    class Meta:
        verbose_name_plural = "Speech corpora"

    # durationOfEffectiveSpeech (0-1; f)
    durationOfEffectiveSpeech = models.TextField("Duration of effective speech",blank=True, help_text=get_help('speechcorpus.durationOfEffectiveSpeech'), default='0')
    # durationOfFullDatabase (0-1; f)
    durationOfFullDatabase = models.TextField("Duration of full database",blank=True, help_text=get_help('speechcorpus.durationOfFullDatabase'), default='0')
    # numberOfSpeakers (0-1; f)
    numberOfSpeakers = models.CharField("Number of speakers", blank=True, help_text=get_help('speechcorpus.numberOfSpeakers'), max_length=20, default='unknown')
    additional = models.IntegerField("Number of speakers", blank=True, help_text=get_help('speechcorpus.numberOfSpeakers'), default=0)
    # speakerDemographics (0-1; f)
    speakerDemographics = models.TextField("Speaker demographics",blank=True, help_text=get_help('speechcorpus.speakerDemographics'), default='-')

    # Scheme for downloading and uploading
    specification = [
        {'name': 'Duration eff. speech',    'type': 'field', 'path': 'durationOfEffectiveSpeech'},
        {'name': 'Duration full dbase',     'type': 'field', 'path': 'durationOfFullDatabase'},
        {'name': 'Number of speakers',      'type': 'field', 'path': 'numberOfSpeakers'},
        {'name': 'Number of speakers',      'type': 'field', 'path': 'additional'},
        {'name': 'Speaker demographics',    'type': 'field', 'path': 'speakerDemographics'},

        ]

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = "MOVED"
        sCnvType = m2m_combi(self.conversationaltypes)
        return "[{}] cnv:{}".format(idt, sCnvType)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Copy M2M relationship: conversationalType
        copy_m2m(self, new_copy, 'conversationaltypes')
        # Copy M2M relationship: audioFormat
        copy_m2m(self, new_copy, 'audioformats')
        # Return the new copy
        return new_copy

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            # We should create a new instance
            obj = SpeechCorpus.objects.create()

            # And now call the standard custom_add() method
            obj.custom_add(oItem, oParams, **kwargs)

        except:
            msg = oErr.get_error_message()
            oErr.DoError("SpeechCorpus/get_instance")
        return obj


class Resource(CollbankModel, models.Model):
    """A resource is part of a collection"""

    # (0-1)
    description = models.TextField("Description of this resource", blank=True)
    # (1;c)
    type = models.CharField("Type of this resource", choices=build_choice_list(RESOURCE_TYPE), max_length=5,
                            help_text=get_help(RESOURCE_TYPE))
    # NEW: type >> [DCtype] + [subtype]
    # (1;c) DCtype
    DCtype = models.CharField("DCtype of this resource", choices=build_choice_list(RESOURCE_TYPE, 'before'), max_length=5,
                            help_text=get_help(RESOURCE_DCTYPE), default='0')
    # (0-1) subtype
    subtype = models.CharField("Subtype of this resource (optional)", choices=build_choice_list(RESOURCE_TYPE), max_length=5,
                            help_text=get_help(RESOURCE_SUBTYPE), blank=True, null=True)

    # [1]     Each collection can have [1-n] resources
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, on_delete=models.CASCADE, related_name="collection12m_resource")

    # == writtenCorpus (0-1)
    writtenCorpus = models.ForeignKey(WrittenCorpus, blank=True, null=True, on_delete=models.SET_NULL)
    # speechCorpus (0-1)
    speechCorpus = models.ForeignKey(SpeechCorpus, blank=True, null=True, on_delete=models.SET_NULL)

    # Scheme for downloading and uploading
    specification = [
        {'name': 'Description',         'type': 'field', 'path': 'description'},
        # NOTE: type, DCtype and subtype need special treatment

        {'name': 'Modality',        'type': 'm2o',   'path': 'modality',        'fkfield': 'resource', 'model': 'Modality',  
         'vfield': 'name', 'fieldchoice': RESOURCE_MODALITY},
         # Recording environment
        {'name': 'Recording environment',   'type': 'm2o',    'path': 'recordingEnvironment', 'fkfield': 'resource', 
         'model': 'RecordingEnvironment',   'vfield': 'name', 'fieldchoice': SPEECHCORPUS_RECORDINGENVIRONMENT},
         # Recording conditions
        {'name': 'Recording condition',     'type': 'm2o',    'path': 'recordingConditions',  'fkfield': 'resource', 
         'model': 'RecordingCondition',     'vfield': 'name'},
         # Channel
        {'name': 'Channel',         'type': 'm2o',   'path': 'channel',         'fkfield': 'resource', 'model': 'Channel',   
         'vfield': 'name', 'fieldchoice': SPEECHCORPUS_CHANNEL},
         # SocialContext
        {'name': 'Social context',  'type': 'm2o',   'path': 'socialContext',   'fkfield': 'resource', 'model': 'SocialContext',   
         'vfield': 'name', 'fieldchoice': SPEECHCORPUS_SOCIALCONTEXT},
         # PlanningType
        {'name': 'Planning type',   'type': 'm2o',   'path': 'planningType',    'fkfield': 'resource', 'model': 'PlanningType',   
         'vfield': 'name', 'fieldchoice': SPEECHCORPUS_PLANNINGTYPE},
         # Interactivity
        {'name': 'Interactivity',   'type': 'm2o',   'path': 'interactivity',   'fkfield': 'resource', 'model': 'Interactivity',   
         'vfield': 'name', 'fieldchoice': SPEECHCORPUS_INTERACTIVITY},
         # Involvement
        {'name': 'Involvement',     'type': 'm2o',   'path': 'involvement',     'fkfield': 'resource', 'model': 'Involvement',   
         'vfield': 'name', 'fieldchoice': SPEECHCORPUS_INVOLVEMENT},
         # Audience
        {'name': 'Audience',        'type': 'm2o',   'path': 'audience',        'fkfield': 'resource', 'model': 'Audience',   
         'vfield': 'name', 'fieldchoice': SPEECHCORPUS_AUDIENCE },
         # Speech and Written corpus
        {'name': 'Speech corpus',   'type': 'fkob',  'path': 'speechCorpus',    'model': 'SpeechCorpus'},
        {'name': 'Written corpus',  'type': 'fkob',  'path': 'writtenCorpus',   'model': 'WrittenCorpus'},
        # Totalsize, annotation, media
        {'name': 'TotalSize',       'type': 'm2o',   'path': 'totalSize',       'fkfield': 'resource', 'model': 'TotalSize'},
        {'name': 'Annotation',      'type': 'm2o',   'path': 'annotation',      'fkfield': 'resource', 'model': 'Annotation'},
        {'name': 'Media',           'type': 'm2o',   'path': 'media',           'fkfield': 'resource', 'model': 'Media'},
        ]

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        if self.subtype == None:
            iType = self.DCtype
        else:
            iType = self.subtype
        sAnn = m2m_combi(self.annotations)
        return "[{}] {}: ann[{}]".format(
            idt,
            choice_english(RESOURCE_TYPE, iType),
            sAnn)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Copy the 12m fields
        copy_m2m(self, new_copy, "media_items")
        copy_m2m(self, new_copy, "annotations")
        copy_m2m(self, new_copy, "totalsize12m_resource")
        copy_m2m(self, new_copy, "modalities")
        copy_m2m(self, new_copy, "recordingenvironments")
        copy_m2m(self, new_copy, "channels")
        copy_m2m(self, new_copy, "socialcontexts")
        copy_m2m(self, new_copy, "planningtypes")
        copy_m2m(self, new_copy, "interactivities")
        copy_m2m(self, new_copy, "involvements")
        copy_m2m(self, new_copy, "audiences")
        # Check and copy FK fields
        copy_fk(self, new_copy, "writtenCorpus")
        copy_fk(self, new_copy, "speechCorpus")
        # Return the new copy
        return new_copy

    def get_instance(oItem, oParams, **kwargs):
        """Add an object according to the specifications provided"""

        oErr = ErrHandle()
        obj = None
        try:
            # We should create a new instance
            description = oItem.get("description", "-")
            collection = oParams.get("collection")
            obj = Resource.objects.create(collection=collection, description=description)

            # Treat the types
            iDCtype = Resource.xml_DCtype(oItem.get("DCtype"))
            if not iDCtype is None:
                obj.DCtype = iDCtype
                iSubType = Resource.xml_DCsubtype(oItem.get("DCtype"), oItem.get("subtype"))
                if not iSubType is None:
                    obj.subtype = iSubType
                    obj.type = iSubType
                else:
                    obj.type = iDCtype
                # Make sure to save any changes
                obj.save()

            # And now call the standard custom_add() method
            oParams['resource'] = obj
            obj.custom_add(oItem, oParams, **kwargs)

        except:
            msg = oErr.get_error_message()
            oErr.DoError("Resource/get_instance")
        return obj

    def subtype_only(self):
        """Display only the subtype text if it exists"""

        if self.subtype == None:
            return ""
        sTypeFull = self.get_subtype_display()
        arType = sTypeFull.split(":")
        if len(arType) > 1:
            sBack = arType[1]
        else:
            sBack = sTypeFull
        return sBack

    def xml_DCtype(sDCtype):
        """Determine the Fieldchoice mv for the DCtype"""

        oErr = ErrHandle()
        iBack = None
        try:
            # Validate
            if not sDCtype is None and sDCtype != "":
                # Look for the first one that has the english_name
                obj = FieldChoice.objects.filter(field=RESOURCE_TYPE, english_name__iexact=sDCtype).first()
                if obj is None:
                    # Look for the first one that has the name with colon
                    starting = "{}:".format(sDCtype)
                    obj = FieldChoice.objects.filter(field=RESOURCE_TYPE, english_name__istartswith=starting).first()
                # Do we have a match?
                if not obj is None:
                    # Get the mv
                    iBack = obj.machine_value
        except:
            msg = oErr.get_error_message()
            oErr.DoError("xml_DCtype")

        return iBack

    def xml_DCsubtype(sDCtype, sSubType):
        """Determine the Fieldchoice mv for the subtype (of DCtype)"""

        oErr = ErrHandle()
        iBack = None
        try:
            # If no subtype is specified, we return
            if not sDCtype is None and sDCtype != "" and not sSubType is None and sSubType != "":
                # Combine what we are looking for
                sSearch = ":".join([sDCtype, sSubType])
                obj = FieldChoice.objects.filter(field=RESOURCE_TYPE, english_name__iexact=sSearch).first()
                # Do we have a match?
                if not obj is None:
                    # Get the mv
                    iBack = obj.machine_value
        except:
            msg = oErr.get_error_message()
            oErr.DoError("xml_DCsubtype")

        return iBack
    

class ExtColl(models.Model):
    """External collection"""

    # identifier (1) MUST BE UNIQUE
    identifier = models.CharField("Unique short collection identifier (10 characters max)", unique=True, max_length=MAX_IDENTIFIER_LEN, default='-')
    # Full title [1; f]
    title = models.TextField("Full title for this collection", help_text=get_help('title'))
    # == description (0-1;f) 
    description = models.TextField("Description", blank=True, help_text=get_help('description'))

    def __str__(self):
        # We are known by our identifier
        return self.identifier


class Collection(models.Model, CollbankModel):
    """Characteristics of the collection as a whole"""

    # ============ INTERNAL FIELDS ================================
    # the persistent identifier name by which this descriptor is going to be recognized
    #  The PID in CLARIN should be a handle. In our case it is the *last part* of the handle URL
    #  So a user can get to this collection description by typing:
    #  http://hdl.handle.net/21.11114/COLL-[this-pidname]
    pidname = models.CharField("Registry identifier", max_length=MAX_STRING_LEN, default="empty")
    # the 'URL' is the local (Radboud University) link where the XML and the HTML output of
    #           this collection should be found
    # Note: this field is *calculated* by the program and should *not* be entered by a user
    #       it is calculated upon publication
    url = models.URLField("URL of the metadata file", default='')
    handledomain = models.CharField("Domain of the Handle system", max_length=MAX_NAME_LEN, default='')
    # identifier (1) MUST BE UNIQUE
    identifier = models.CharField("Unique short collection identifier (10 characters max)", unique=True, max_length=MAX_IDENTIFIER_LEN, default='-')
    # Landing Page (1)
    landingPage = models.URLField("URL of the landing page", help_text=get_help(INTERNAL_LANDINGPAGE), default='')
    # Search Page (0-1)
    searchPage = models.URLField("URL of the search page", help_text=get_help(INTERNAL_SEARCHPAGE), blank=True, null=True)
    # Internal-only: last saved
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)


    # ============ OTHER TEXT FIELDS ===================================================================================
    # == description (0-1;f) 
    description = models.TextField("Describes the collection as a whole", blank=True, help_text=get_help('description'))
    # == clarinCentre (0-1; f)
    clarinCentre = models.TextField("Clarin centre in charge", blank=True, help_text=get_help('clarincentre.name'))
    # == version (0-1; f)
    version = models.TextField("Version of the collection", blank=True, help_text=get_help('version'))

    # ============ OTHER FK FIELDS =====================================================================================
    # linguality (0-1)
    linguality = models.ForeignKey(Linguality, blank=True, null=True, on_delete=models.SET_NULL)   # , related_name="collectionm2m_linguality")
    # == access (0-1)
    access = models.ForeignKey(Access, blank=True, null=True, on_delete=models.SET_NULL)
    # == documentation (0-1)
    documentation = models.ForeignKey(Documentation, blank=True, null=True, on_delete=models.SET_NULL)
    # == validation (0-1)
    validation = models.ForeignKey(Validation, blank=True, null=True, on_delete=models.SET_NULL)

    # ============ TO BE DELETED: m2m fields that have been converted to Many-to-One fields ============================
    # title (1-n;f)             [many-to-one]
    title = models.ManyToManyField(Title, blank=False, related_name="collectionm2m_title")
    # == owner (0-n;f)          [many-to-one]
    owner = models.ManyToManyField( Owner, blank=True, related_name="collectionm2m_owner")
    # resource (1-n)            [many-to-one]
    resource = models.ManyToManyField(Resource, blank=False, related_name="collectionm2m_resource")
    # == genre (0-n; c:)        [many-to-one]
    genre = models.ManyToManyField(Genre, blank=True, related_name="collectionm2m_genre")
    # provenance (0-n)          [many-to-one]
    provenance = models.ManyToManyField(Provenance, blank=True, related_name="collectionm2m_provenance")
    # language (1-n; c)   Many-to-Many!!
    language = models.ManyToManyField(Language, blank=False)
    # languageDisorder (0-n;f)  [many-to-one]
    languageDisorder = models.ManyToManyField(LanguageDisorder, blank=True, related_name="collectionm2m_langdisorder")
    # relation (0-n;f)          [many-to-one]
    relation = models.ManyToManyField(Relation, blank=True, related_name="collectionm2m_relation")
    # == domain (0-n;f)         [many-to-one]
    domain = models.ManyToManyField(Domain, blank=True, related_name="collectionm2m_domain")
    # == totalSize (0-n)        [many-to-one] - verander in 'TotalCollectionSize'
    totalSize = models.ManyToManyField(TotalSize, blank=True, related_name="collectionm2m_totalsize")
    # == PID (0-n)              [many-to-one]
    pid = models.ManyToManyField(PID, blank=True, related_name="collectionm2m_pid")
    # == resourceCreator (0-n)  [many-to-one]
    resourceCreator = models.ManyToManyField(ResourceCreator, blank=True, related_name="collectionm2m_resourcecreator")
    # == project (0-n)          [many-to-one]
    project = models.ManyToManyField(Project, blank=True, related_name="collectionm2m_project")
    
    class Meta:
        # This defines (amongst others) the default ordering in the admin listview of Collections
        ordering = ['identifier']

    # Scheme for downloading and uploading
    specification = [
        {'name': 'Registry identifier', 'type': 'field', 'path': 'pidname',     'readonly': True},
        {'name': 'Url',                 'type': 'field', 'path': 'url',         'readonly': True},  # project/url
        {'name': 'Landing page',        'type': 'field', 'path': 'landingPage'},                    # ResourceProxy
        {'name': 'Search page',         'type': 'field', 'path': 'searchPage'},                     # ResourceProxy

        {'name': 'Description',         'type': 'field', 'path': 'description'},
        {'name': 'Clarin centre',       'type': 'field', 'path': 'clarinCentre'},
        {'name': 'Version',             'type': 'field', 'path': 'version'},

        # Tables that are linked to [collection] by a FK

        {'name': 'Access',              'type': 'fkob',  'path': 'access',          'model': 'Access'},
        {'name': 'Linguality',          'type': 'fkob',  'path': 'linguality',      'model': 'Linguality'},
        {'name': 'Documentation',       'type': 'fkob',  'path': 'documentation',   'model': 'Documentation'},
        {'name': 'Validation',          'type': 'fkob',  'path': 'validation',      'model': 'Validation'},

        # Tables that are actually [many-to-one] with an FK to [collection]:
        #   Title, Owner, Genre, LanguageDisorder, Domain, PID, 
        #   Resource, Provenance, Language, Relation, TotalSize, ResourceCreator, Project

        {'name': 'Titles',              'type': 'm2o',  'path': 'title',        'fkfield': 'collection', 'model': 'Title',  'vfield': 'name'},
        {'name': 'Owners',              'type': 'm2o',  'path': 'owner',        'fkfield': 'collection', 'model': 'Owner',  'vfield': 'name'},
        {'name': 'Genres',              'type': 'm2o',  'path': 'genre',        'fkfield': 'collection', 'model': 'Genre',  'vfield': 'name'},
        {'name': 'Domains',             'type': 'm2o',  'path': 'domain',       'fkfield': 'collection', 'model': 'Domain', 'vfield': 'name'},
        {'name': 'PIDs',                'type': 'm2o',  'path': 'PID',          'fkfield': 'collection', 'model': 'PID',    'vfield': 'code'},
        {'name': 'Language Disorder',   'type': 'm2o',  'path': 'languageDisorder','fkfield': 'collection', 'model': 'LanguageDisorder', 'vfield': 'name'},
        {'name': 'Provenance',          'type': 'm2o',  'path': 'provenance',      'fkfield': 'collection', 'model': 'Provenance'},
        {'name': 'Resource',            'type': 'm2o',  'path': 'resource',        'fkfield': 'collection', 'model': 'Resource'},
        {'name': 'Language',            'type': 'm2o',  'path': 'Language',        'fkfield': 'collection', 'model': 'CollectionLanguage'},
        {'name': 'Relation',            'type': 'm2o',  'path': 'dc-relation',     'fkfield': 'collection', 'model': 'Relation'},
        {'name': 'TotalSize',           'type': 'm2o',  'path': 'totalSize',       'fkfield': 'collection', 'model': 'TotalCollectionSize'},
        {'name': 'Resource Creator',    'type': 'm2o',  'path': 'resourceCreator', 'fkfield': 'collection', 'model': 'ResourceCreator'},
        {'name': 'Project',             'type': 'm2o',  'path': 'project',         'fkfield': 'collection', 'model': 'Project'},
        ]

    def __str__(self):
        # We are known by our identifier
        return self.identifier

    def check_pid(self, pidservice, sPidName):
        """Check the PID against [sPidName] and brush up .url and .handledomain too"""

        # Validate
        if pidservice == None or sPidName == "": 
            return False
        bNeedSaving = False
        # Check if the handle domain is there 
        sHandleDomain = pidservice.getdomain()
        if self.handledomain != sHandleDomain:
            self.handledomain = sHandleDomain
            bNeedSaving = True
        # Check if the PID name is already there
        if self.pidname != sPidName:
            # Set the PID name
            self.pidname = sPidName
            bNeedSaving = True
        # Possibly set the url
        sUrl = self.get_targeturl()
        if self.url != sUrl:
            self.url = sUrl
            bNeedSaving = True
        # Possibly adapt the URL
        oResponse = pidservice.checkandupdatepid(self)
        if oResponse == None or oResponse['status'] != 'ok':
            print("checkandupdatepid returns: " + oResponse['msg'])
            return False
        # Need saving?
        if bNeedSaving:
            self.save()
        # Return positively
        return True

    def do_identifier(self):
        # This function is used in [CollectionAdmin] in list_display
        return str(self.identifier)
    do_identifier.short_description = "Identifier"
    do_identifier.admin_order_field = 'identifier'

    def get_copy(self):
        # Make a clean copy
        # new_copy = get_instance_copy(self)
        new_copy = Collection(url=self.url, handledomain=self.handledomain, landingPage = self.landingPage,
                              searchPage = self.searchPage, description=self.description, clarinCentre=self.clarinCentre)
        new_copy.save()
        # Reset the PIDFIELD 
        new_copy.pidname = "empty_{0:05d}".format(self.id)
        # Create a unique identifier
        new_copy.identifier = "{}_{}".format(self.identifier[:25],new_copy.id)
        # Copy the one-to-many fields
        copy_m2m(self, new_copy, "collection12m_title")             # Title               +
        copy_m2m(self, new_copy, "collection12m_owner")             # Owner               +
        copy_m2m(self, new_copy, "collection12m_resource")          # Resource
        copy_m2m(self, new_copy, "collection12m_genre")             # Genre
        copy_m2m(self, new_copy, "collection12m_provenance")        # Provenance
        copy_m2m(self, new_copy, "coll_languages")                  # CollectionLanguage
        copy_m2m(self, new_copy, "collection12m_languagedisorder")  # LanguageDisorder
        copy_m2m(self, new_copy, "collection12m_relation")          # Relation
        copy_m2m(self, new_copy, "collection12m_domain")            # Domain
        copy_m2m(self, new_copy, "collection12m_totalsize")         # TotalCollectionSize
        copy_m2m(self, new_copy, "collection12m_pid")               # PID
        copy_m2m(self, new_copy, "collection12m_resourcecreator")   # ResourceCreator
        copy_m2m(self, new_copy, "collection12m_project")           # Project
        # Check and copy FK fields
        copy_fk(self, new_copy, "linguality")
        copy_fk(self, new_copy, "access")
        copy_fk(self, new_copy, "documentation")
        copy_fk(self, new_copy, "validation")
        # Return the new copy
        return new_copy

    def get_identifier(self):
        """Get a proper copy of the identifier as string"""
        return self.identifier.value_to_string()

    def get_instance(oItem):
        """kkk"""

        def get_shortest(lst_value):
            shortest = None
            for onevalue in lst_value:
                # Keep track of what the shortest is (for title)
                if shortest is None:
                    shortest = onevalue
                elif len(onevalue) < len(shortest):
                    shortest = onevalue
            return shortest

        bOverwriting = False
        instance = None
        oErr = ErrHandle()
        try:
            # Adapt the title, if need be
            titles = oItem.get("title")
            oItem['title'] = [ titles ] if isinstance(titles, str) else titles

            # Get to the identifier, which is the shortest title
            identifier = get_shortest(oItem.get("title"))
            if identifier is None or identifier == "":
                oErr.DoError("Collection/get_instance: no [identifier] provided")
            else:
                # Retrieve the object
                instance = Collection.objects.filter(identifier=identifier).first()
                if instance is None:
                    # This object doesn't yet exist: create it
                    instance = Collection.objects.create(identifier=identifier)
                else:
                    bOverwriting = True

        except:
            msg = oErr.get_error_message()
            oErr.DoError("Collection/get_instance")
        return bOverwriting, instance

    def get_pidname(self, pidservice = None):
        """Get the persistent identifier and create it if it is not there"""
        bNeedSaving = False

        try:
            sPidName = self.pidname
            if sPidName == "" or sPidName.startswith("empty") or sPidName.startswith("cbmetadata"):
                # register the PID
                self.register_pid()
                sPidName = self.pidname
            # Return the PID name we have
            # (should be 21.11114/COLL-0000-000x-yyyy-z)

            # Check stuff
            if pidservice == None:
                pidservice = PidService.objects.filter(name=PIDSERVICE_NAME).first()
            if not self.check_pid(pidservice, sPidName):
                # Some error
                print("get_pidname doesn't get the pidservice:", sys.exc_info()[0])
                return ""
            # Return whatever the PID is now
            return self.pidname
        except:
            print("get_pidname error:", sys.exc_info()[0])
            return ""

    def get_pidfull(self):
        sBack = ""
        if self.pidname != None:
            sBack = "http://hdl.handle.net/21.11114/{}".format(self.pidname)
        return sBack

    def get_publisfilename(self, sType=""):
        # Get the correct pidname
        sFileName = self.get_xmlfilename()
        # THink of a filename
        if sType == "joai":
            sPublish = os.path.abspath(os.path.join(PUBLISH_DIR, sFileName)) + ".cmdi.xml"
        else:
            sPublish = os.path.abspath(os.path.join(REGISTRY_DIR, sFileName))
        return sPublish

    def publishdate(self):

        sPublishPath = self.get_publisfilename()
        if os.path.isfile(sPublishPath):
            fDate = os.path.getmtime(sPublishPath)
            oDate = datetime.fromtimestamp( fDate)
            sDate = oDate.strftime("%d/%b/%Y %H:%M:%S")
        else:
            sDate = 'unpublished'
        return sDate

    def get_status(self):
        """Get the status of this colletion: has it been published or not?"""

        sPublishPath = self.get_publisfilename()
        sStatusP = 'p' if os.path.isfile(sPublishPath) else 'u'
        # If it is published, get its publication date and compare it to 
        sStatusD = 'n'
        # Has it been published?
        if sStatusP == 'p':
            if self.updated_at == None:
                # If it is published, but no 'updated_at' yet, it is 'up to date'
                sStatusD = 'd' 
            else:
                # It is published: get the file date
                saved_at = os.path.getmtime(sPublishPath)
                updated_at = datetime.timestamp( self.updated_at)
                sStatusD = 's' if saved_at < updated_at else 'd'
        # Combine states
        if sStatusP == 'u':
            sStatus = 'not-published'
        else:
            if sStatusD == 'n':
                sStatus = 'unknown'
            elif sStatusD == 'd':
                sStatus = 'published'
            else:
                sStatus = 'stale' 
        # Return the combined status
        return sStatus

    def get_targeturl(self):
        """Get the URL where the XML data should be made available"""
        sUrl = "{}{}".format(REGISTRY_URL,self.get_xmlfilename())
        return sUrl

    def get_title(self):
        return m2m_namelist(self.collection12m_title)
    get_title.short_description = 'Titles (not sortable)'
    # This works, but sorting on a non-f
    # get_title.admin_order_field = 'identifier'

    def get_xmlfilename(self):
        """Create the filename for the XML file for this item"""

        sFileName = "cbmetadata_{0:05d}".format(self.id)
        return sFileName

    def register_pid(self):
        """Make sure this record has a registered persistant identifier
        
        Additionally: set the .pidname field (if needed) and set the .url field (if needed)
        """

        # Get the correct service
        pidservice = PidService.objects.filter(name=PIDSERVICE_NAME).first()
        if pidservice == None:
            # Make sure the caller understands something is wrong
            return False
        # Look for a record with this name in the PID service
        sResponse = pidservice.getpid(self)
        if sResponse == "":
            # There was some kind of error
            return False
        elif sResponse == "-":
            # There is no registration yet: create one
            oResponse = pidservice.createpid(self)
            if oResponse != None and 'status' in oResponse and oResponse['status'] == "ok":
                sPidName = oResponse['pid']
                # Adapt the PID if it contains a /
                if "/" in sPidName:
                    # Make sure we only store the part *after* the slash
                    sPidName = sPidName.split("/")[-1]
            else:
                # Something somewhere went wrong
                return False
        else:
            sPidName = sResponse

        # Check stuff
        if not self.check_pid(pidservice, sPidName):
            # Some error
            print("register_pid doesn't get the pidservice:", sys.exc_info()[0])
            return ""

        # Return positively
        return True

    def save(self, **kwargs):
        oErr = ErrHandle()
        try:
            result = super(Collection,self).save(**kwargs)
            return result
        except:
            msg = oErr.get_error_message()
            oErr.DoError("Collection/save")
            return None

    def save_relations(self):
        """Look for all of my collection relations and store them in separate txt files"""

        iSaved = 0
        for rel_this in self.collection12m_relation.all():
            # Save this relation
            rel_this.save_relation_file()
            iSaved +=1
        # Return the number of relations saved
        return iSaved

