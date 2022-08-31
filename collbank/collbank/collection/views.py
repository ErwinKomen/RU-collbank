"""
Definition of views.
"""

from django.contrib.admin.templatetags.admin_list import result_headers
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.db.models.functions import Lower
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.template import RequestContext, loader
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.views.generic import ListView
from wsgiref import util
from wsgiref.util import FileWrapper
import json
from datetime import datetime
from xml.dom import minidom
import xml.etree.ElementTree as ET
import lxml
from lxml import etree
import os
import tarfile
import zipfile
import tempfile
import io
from requests import request

from collbank.collection.models import *
from collbank.settings import APP_PREFIX, WSGI_FILE, STATIC_ROOT, WRITABLE_DIR, COUNTRY_CODES # , LANGUAGE_CODE_LIST
# Not used anymore: OUTPUT_XML
from collbank.collection.admin import CollectionAdmin
from collbank.collection.forms import *
from collbank.collection.adaptations import listview_adaptations

# Local variables
XSI_CMD = "http://www.clarin.eu/cmd/"
# Initial version in Radboud-TSG (now extinct)
# XSD_ID = "clarin.eu:cr1:p_1459844210473"
# Draft publication version:
XSD_ID = "clarin.eu:cr1:p_1493735943947"
XSI_XSD = "https://catalog.clarin.eu/ds/ComponentRegistry/rest/registry/1.1/profiles/" + XSD_ID + "/xsd/"

app_user = "RegistryUser"
app_editor = "RegistryEditor"
bDebug = False

# General help functions
def add_collection_xml(col_this, crp):
    """Add the collection information from [col_this] to XML element [crp]"""

    # title (1-n)
    add_element("1-n", col_this, "title", crp, field_name="collection12m_title", foreign="name")
    # description (0-1)
    add_element("0-1", col_this, "description", crp)
    # owner (0-n)
    add_element("0-n", col_this, "owner", crp, field_name="collection12m_owner", foreign="name")
    # genre (0-n)
    add_element("0-n", col_this, "genre", crp, field_name="collection12m_genre", foreign="name", fieldchoice=GENRE_NAME)
    # languageDisorder(0-n)
    add_element("0-n", col_this, "languageDisorder", crp, field_name="collection12m_languagedisorder", foreign="name")
    # domain (0-n)
    if col_this.collection12m_domain.count() > 0:
        # Add the domains here
        add_element("0-n", col_this, "name", crp, field_name="collection12m_domain", foreign="name", subname="domain")
    # clarinCentre (0-1)
    add_element("0-1", col_this, "clarinCentre", crp)
    # PID (0-n)
    add_element("0-n", col_this, "pid", crp, field_name="collection12m_pid", foreign="code", subname="PID")
    # version (0-1)
    add_element("0-1", col_this, "version", crp)
    # resource (1-n)
    for res_this in col_this.collection12m_resource.all():      # col_this.resource.all():
        # Add the resource top-element
        res = ET.SubElement(crp, "resource")
        # description (0-1)
        add_element("0-1", res_this, "description", res)

        # type (1) -- THIS MAY DISAPPEAR
        # add_element("1", res_this, "type", res, fieldchoice =RESOURCE_TYPE)
        # TODO: possibly divide this into DCtype and (optional) subtype
        # DCtype (1)
        add_element("1", res_this, "DCtype", res, fieldchoice =RESOURCE_TYPE, part=1)
        # subtype (0-1)
        add_element("0-1", res_this, "subtype", res, fieldchoice =RESOURCE_TYPE, part=2)

        # modality (1-n)
        add_element("1-n", res_this, "modality", res, field_name="modalities", foreign="name", fieldchoice=RESOURCE_MODALITY )
        # recording Environment (0-n)
        add_element("0-n", res_this, "recordingEnvironment", res, field_name="recordingenvironments", foreign="name", fieldchoice=SPEECHCORPUS_RECORDINGENVIRONMENT)
        # Recording conditions (0-n)
        add_element("0-n", res_this, "recordingConditions", res, field_name="recordingconditions", foreign="name")
        # channel (0-n)
        add_element("0-n", res_this, "channel", res, field_name="channels", foreign="name", fieldchoice=SPEECHCORPUS_CHANNEL)
        # socialContext (0-n)
        add_element("0-n", res_this, "socialContext", res, field_name="socialcontexts", foreign="name", fieldchoice=SPEECHCORPUS_SOCIALCONTEXT)
        # planningType (0-n)
        add_element("0-n", res_this, "planningType", res, field_name="planningtypes", foreign="name", fieldchoice=SPEECHCORPUS_PLANNINGTYPE)
        # interactivity (0-n)
        add_element("0-n", res_this, "interactivity", res, field_name="interactivities", foreign="name", fieldchoice=SPEECHCORPUS_INTERACTIVITY)
        # involvement (0-n)
        add_element("0-n", res_this, "involvement", res, field_name="involvements", foreign="name", fieldchoice=SPEECHCORPUS_INVOLVEMENT)
        # audience (0-n)
        add_element("0-n", res_this, "audience", res, field_name="audiences", foreign="name", fieldchoice=SPEECHCORPUS_AUDIENCE)
        # speechCorpus (0-1)
        speech_this = res_this.speechCorpus
        if speech_this != None:
            # Set the sub-element
            speech = ET.SubElement(res, "speechCorpus")
            # Process the elements of the speech corpus            
            add_element("0-n", speech_this, "conversationalType", speech, field_name="conversationaltypes", foreign="name", fieldchoice=SPEECHCORPUS_CONVERSATIONALTYPE)            
            add_element("0-1", speech_this, "durationOfEffectiveSpeech", speech, foreign="name")
            add_element("0-1", speech_this, "durationOfFullDatabase", speech, foreign="name")
            add_element("0-1", speech_this, "numberOfSpeakers", speech, foreign="name")
            add_element("0-1", speech_this, "speakerDemographics", speech, foreign="name")
            # audioFormat (0-n)
            for af_this in speech_this.audioformats.all():    # speech_this.audioFormat.all():
                # Set the sub-element
                af = ET.SubElement(speech, "audioFormat")
                # speechCoding (0-1)
                add_element("0-1", af_this, "speechCoding", af)
                # samplingFrequency (0-1)
                add_element("0-1", af_this, "samplingFrequency", af)
                # compression (0-1)
                add_element("0-1", af_this, "compression", af)
                # bitResolution (0-1)
                add_element("0-1", af_this, "bitResolution", af)
        # writtenCorpus (0-1)
        writ_this = res_this.writtenCorpus
        if writ_this != None:
            # Set the sub-element
            writ = ET.SubElement(res, "writtenCorpus")
            # Process the validation elements
            add_element("0-n", writ_this, "characterEncoding", writ, field_name="charenc_writtencorpora", foreign="name", fieldchoice=CHARACTERENCODING)
            # numberOfAuthors (0-1)
            add_element("0-1", writ_this, "numberOfAuthors", writ)
            # authorDemographics (0-1
            add_element("0-1", writ_this, "authorDemographics", writ)
        # totalSize (0-n)
        for size_this in res_this.totalsize12m_resource.all():    #  res_this.totalSize.all():
            # Start adding this sub-element
            tot = ET.SubElement(res, "totalSize")
            # Add the size part
            add_element("1", size_this, "size", tot)
            # Add the sizeUnit part
            add_element("1", size_this, "sizeUnit", tot)
        # annotation (0-n)
        for ann_this in res_this.annotations.all():   #  res_this.annotation.all():
            # Add this annotation element
            ann = ET.SubElement(res, "annotation")
            # type (1)
            add_element("1", ann_this, "type", ann, fieldchoice=ANNOTATION_TYPE, alternative = 'othertype')
            # mode (1)
            add_element("1", ann_this, "mode", ann, fieldchoice=ANNOTATION_MODE)
            # annotation_formats (1-n)
            add_element("1-n", ann_this, "format", ann, field_name="annotation_formats", foreign="name", fieldchoice=ANNOTATION_FORMAT)
        # media (0-n)
        for med_this in res_this.media_items.all():   # res_this.medias.all():
            # Add the media sub-element
            med = ET.SubElement(res, "media")
            # format (0-n)
            add_element("0-n", med_this, "format", med, field_name="mediaformat12m_media", foreign="name", fieldchoice=MEDIA_FORMAT)
    # provenance (0-n)
    for prov_this in col_this.collection12m_provenance.all():   # col_this.provenance.all():
        # Set the provenance sub-element
        prov = ET.SubElement(crp, "provenance")
        # temporal provenance (0-1)
        if prov_this.temporalProvenance != None:
            # Create a sub-element
            temp = ET.SubElement(prov, "temporalProvenance")
            # Fetch this element
            temp_this = prov_this.temporalProvenance
            # Start year and end-year
            add_element("1", temp_this, "startYear", temp)
            add_element("1", temp_this, "endYear", temp)
        # Walk the geographic provenance
        for geo_this in prov_this.g_provenances.all():    #  prov_this.geographicProvenance.all():
            # Create sub-element
            geo = ET.SubElement(prov, "geographicProvenance")
            # place (0-n)
            add_element("0-n", geo_this, "place", geo, field_name="cities", foreign="name")
            # country (0-1)
            cntry = geo_this.countryiso
            # Use the new method with CountryIso
            sEnglish = cntry.english
            sAlpha2 = cntry.alpha2
            # Set the values 
            cntMain = ET.SubElement(geo, "Country")
            cntMainName = ET.SubElement(cntMain, "CountryName")
            cntMainCoding = ET.SubElement(cntMain, "CountryCoding")
            cntMainName.text = sEnglish
            cntMainCoding.text = sAlpha2
    # linguality (0-1)
    linguality_this = col_this.linguality
    if linguality_this != None:
        # Set the linguality sub-element
        ling = ET.SubElement(crp, "linguality")
        # Process the linguality elements
        add_element("0-n", linguality_this, "lingualityType", ling, field_name="linguality_types", foreign="name", fieldchoice=LINGUALITY_TYPE)
        add_element("0-n", linguality_this, "lingualityNativeness", ling, field_name="linguality_nativenesses", foreign="name", fieldchoice=LINGUALITY_NATIVENESS)
        add_element("0-n", linguality_this, "lingualityAgeGroup", ling, field_name="linguality_agegroups",foreign="name", fieldchoice=LINGUALITY_AGEGROUP)
        add_element("0-n", linguality_this, "lingualityStatus", ling, field_name="linguality_statuses", foreign="name", fieldchoice=LINGUALITY_STATUS)
        add_element("0-n", linguality_this, "lingualityVariant", ling, field_name="linguality_variants", foreign="name", fieldchoice=LINGUALITY_VARIANT)
        add_element("0-n", linguality_this, "multilingualityType", ling, field_name="multilinguality_types", foreign="name", fieldchoice=LINGUALITY_MULTI)
    # language (1-n)
    for lng_this in col_this.coll_languages.all():    #  col_this.language.all():
        # (sLngName, sLngCode) = get_language(lng_this.name)
        (sLngName, sLngCode) = get_language_code_name(lng_this)
        # Validation
        if sLngCode == "" or sLngCode is None:
            bStop = True
        else:
            lngMain = ET.SubElement(crp, "Language")
            lngMainName = ET.SubElement(lngMain, "LanguageName")
            lngMainName.text = sLngName
            lngMainCode = ET.SubElement(lngMain, "ISO639")
            lngMainCodeVal = ET.SubElement(lngMainCode, "iso-639-3-code")
            lngMainCodeVal.text = sLngCode
    # relation (0-n)
    # add_element("0-n", col_this, "relation", crp, foreign="name", fieldchoice=RELATION_NAME, subname="dc-relation")
    for rel_this in col_this.collection12m_relation.all():    #  col_this.relation.all():
        # sRelName = choice_english(RELATION_NAME, rel_this.name)
        relMain = ET.SubElement(crp, "dc-relation")
        relMainVal = ET.SubElement(relMain, "relation")
        relMainVal.text = rel_this.name
    # access (0-1)
    access_this = col_this.access
    if access_this != None:
        # Set the access sub-element
        acc = ET.SubElement(crp, "access")
        # Process the access elements
        # add_element("1", access_this, "name", acc)
        add_element("0-n", access_this, "availability", acc, field_name="acc_availabilities", foreign="name", fieldchoice=ACCESS_AVAILABILITY)
        add_element("0-n", access_this, "licenseName", acc, field_name="acc_licnames", foreign="name")
        add_element("0-n", access_this, "licenseUrl", acc, field_name="acc_licurls", foreign="name", subname="licenseURL")
        add_element("0-1", access_this, "nonCommercialUsageOnly", acc, foreign="name", fieldchoice=ACCESS_NONCOMMERCIAL)
        add_element("0-n", access_this, "website", acc, field_name="acc_websites", foreign="name")
        add_element("0-1", access_this, "ISBN", acc, foreign="name")
        add_element("0-1", access_this, "ISLRN", acc, foreign="name")
        add_element("0-n", access_this, "medium", acc, field_name="acc_mediums", foreign="format", fieldchoice=ACCESS_MEDIUM)
        # contact (0-n)
        for contact_this in access_this.acc_contacts.all():   #  access_this.contact.all():
            # Add this contact
            cnt = ET.SubElement(acc, "contact")
            add_element("1", contact_this, "person", cnt)
            add_element("1", contact_this, "address", cnt)
            add_element("1", contact_this, "email", cnt)
    # totalSize (0-n) -- NOTE: this is on the COLLECTION level; there also is totalsize on the RESOURCE level
    if  col_this.collection12m_totalsize.count() > 0:   # col_this.totalSize != None:
        for size_this in col_this.collection12m_totalsize.all():    #  col_this.totalSize.all():
            # Start adding this sub-element (under CRP)
            tot = ET.SubElement(crp, "totalSize")
            # Add the size part
            add_element("1", size_this, "size", tot)
            # Add the sizeUnit part
            add_element("1", size_this, "sizeUnit", tot)
    # resourceCreator (0-n)
    for rescrea_this in col_this.collection12m_resourcecreator.all():   #  col_this.resourceCreator.all():
        # Add sub element
        res = ET.SubElement(crp, "resourceCreator")
        # Add the resource elements
        add_element("0-n", rescrea_this, "organization", res, field_name="organizations", foreign="name")
        add_element("0-n", rescrea_this, "person", res, field_name="persons", foreign="name")
    # documentation (0-1)
    doc_this = col_this.documentation
    if doc_this != None:
        # Set the sub-element
        doc = ET.SubElement(crp, "documentation")
        # Process the documentation elements
        add_element("0-n", doc_this, "documentationType", doc, field_name="doc_types", foreign="format", fieldchoice=DOCUMENTATION_TYPE)
        add_element("0-n", doc_this, "fileName", doc, field_name="doc_files", foreign="name")
        add_element("0-n", doc_this, "url", doc, field_name="doc_urls", foreign="name")
        # add_element("1-n", doc_this, "language", doc, foreign="name", fieldchoice="language.name")
        for lng_this in doc_this.doc_languages.all():   #  doc_this.language.all():
            # (sLngName, sLngCode) = get_language(lng_this.name)
            (sLngName, sLngCode) = get_language_code_name(lng_this)
            # Validation
            if sLngCode == "" or sLngCode is None:
                bStop = True
            else:
                lngMain = ET.SubElement(doc, "Language")
                lngMainName = ET.SubElement(lngMain, "LanguageName")
                lngMainName.text = sLngName
                lngMainCode = ET.SubElement(lngMain, "ISO639")
                lngMainCodeVal = ET.SubElement(lngMainCode, "iso-639-3-code")
                lngMainCodeVal.text = sLngCode
    # validation (0-1)
    val_this = col_this.validation
    if val_this != None:
        # Set the sub-element
        val = ET.SubElement(crp, "validation")
        # Process the validation elements
        add_element("0-1", val_this, "type", val, foreign="name", fieldchoice=VALIDATION_TYPE)
        add_element("0-n", val_this, "method", val, field_name="validationmethods", foreign="name", fieldchoice=VALIDATION_METHOD)
    # project (0-n)
    for proj_this in col_this.collection12m_project.all():    #  col_this.project.all():
        # Set the sub element
        proj = ET.SubElement(crp, "project")
        # Process the project properties
        add_element("0-1", proj_this, "title", proj)
        add_element("0-n", proj_this, "funder", proj, field_name="funders", foreign="name")
        add_element("0-1", proj_this, "URL", proj, foreign="name", subname="url")
    # There's no return value -- all has been added to [crp]
    return None

def add_element(optionality, col_this, el_name, crp, **kwargs):
    """Add element [el_name] from collection [col_this] under the XML element [crp]
    
    Note: make use of the options defined in [kwargs]
    """

    foreign = ""
    if "foreign" in kwargs: foreign = kwargs["foreign"]
    field_choice = ""
    if "fieldchoice" in kwargs: field_choice = kwargs["fieldchoice"]
    field_name = el_name
    if "field_name" in kwargs: field_name = kwargs["field_name"]
    alternative = None
    if "alternative" in kwargs: alternative = kwargs["alternative"]

    col_this_el = getattr(col_this, field_name)
    sub_name = el_name
    if "subname" in kwargs: sub_name = kwargs["subname"]
    if optionality == "0-1" or optionality == "1":
        col_value = col_this_el
        if optionality == "1" or col_value != None:
            if foreign != "" and not isinstance(col_this_el, str):
                col_value = getattr(col_this_el, foreign)
            if field_choice != "": 
                sBack = choice_english(field_choice, col_value)
                if sBack == "other" and not alternative is None:
                    # Get the value from the alternative field
                    col_value = getattr(col_this, alternative)
                else:
                    col_value = sBack
            # Make sure the value is a string
            col_value = str(col_value)
            # Do we need to discern parts?
            if "part" in kwargs:
                arPart = col_value.split(":")
                iPart = kwargs["part"]
                if iPart == 1:
                    col_value = arPart[0]
                elif iPart == 2:
                    if len(arPart) == 2:
                        col_value = arPart[1]
                    else:
                        col_value = ""
            if col_value != "":
                descr_element = ET.SubElement(crp, sub_name)
                descr_element.text = col_value
    elif optionality == "1-n" or optionality == "0-n":
        # Test for obligatory foreign
        if foreign == "": return False
        for t in col_this_el.all():
            col_value = getattr(t, foreign)
            if field_choice != "": 
                sBack = choice_english(field_choice, col_value)
                if sBack == "other" and not alternative is None:
                    # Get the value from the alternative field
                    col_value = getattr(col_this, alternative)
                else:
                    col_value = sBack
            # Make sure the value is a string
            col_value = str(col_value)
            if col_value == "(empty)": 
                col_value = "unknown"
            else:
                title_element = ET.SubElement(crp, sub_name)
                title_element.text = col_value
    # Return positively
    return True
    
def create_collection_xml(collection_this, sUserName, sHomeUrl):
    """Convert the 'collection' object from the context to XML
    
    Note: this returns a TUPLE (boolean, string)
    """

    # Create a top-level element, including CMD, Header and Resources
    top = make_collection_top(collection_this, sUserName, sHomeUrl)

    # Start components and this collection component
    cmp = ET.SubElement(top, "Components")

    # Add a <OralHistoryInterview> root that contains a list of <collection> objects
    collroot = ET.SubElement(cmp, "CorpusCollection")

    # Add this collection to the xml
    add_collection_xml(collection_this, collroot )

    # Convert the XML to a string
    xmlstr = minidom.parseString(ET.tostring(top,encoding='utf-8')).toprettyxml(indent="  ")

    # Validate the XML against the XSD
    (bValid, oError) = validateXml(xmlstr)
    if not bValid:
        # Get error messages for all the errors
        return (False, xsd_error_list(oError, xmlstr))

    # Return this string
    return (True, xmlstr)

def get_application_context(request, context):
    context['is_app_user'] = user_is_ingroup(request, app_user)
    context['is_app_editor'] = user_is_ingroup(request, app_editor)
    return context

def get_country(cntryCode):
    """Get the country details according to the FieldChoice method (EXTINCT)"""

    # Get the country string according to field-choice
    sCountry = choice_english(PROVENANCE_GEOGRAPHIC_COUNTRY, cntryCode).strip()
    sCountryAlt = sCountry + " (the)"
    # Walk all country codes
    for tplCountry in COUNTRY_CODES:
        # Check for country name or alternative country name
        if sCountry == tplCountry[1] or sCountryAlt == tplCountry[1]:
            # REturn the correct country name and code
            return (tplCountry[1], tplCountry[0])
    # Empty
    return (None, None)

def get_language_code_name(lng_obj):
    """Given the LanguageName object, provide the 3-letter code and the name"""

    sLanguage = None
    code = None
    if not lng_obj is None:
        sLanguage = lng_obj.langname.name
        code = lng_obj.langname.iso.code
    return (sLanguage, code)

def getSchema():
    # Get the XSD file into an LXML structure
    # fSchema = os.path.abspath(os.path.join(STATIC_ROOT, "collection", "xsd", "CorpusCollection.xsd.txt"))
    fSchema = os.path.abspath(os.path.join(WRITABLE_DIR, "xsd", "CorpusCollection.xsd.txt"))
    with open(fSchema, encoding="utf-8", mode="r") as f:  
        sText = f.read()                        
        # doc = etree.parse(f)
        doc = etree.XML(sText)                                                    
    
    # Load the schema
    try:                                                                        
        schema = etree.XMLSchema(doc)       
        return schema
    except lxml.etree.XMLSchemaParseError as e:                                 
        print(e)                                                              
        return None

def make_collection_top(colThis, sUserName, sHomeUrl):
    """Create the top-level elements for a collection"""

    # Define the top-level of the xml output
    topattributes = {'xmlns': "http://www.clarin.eu/cmd/" ,
                     'xmlns:xsd':"http://www.w3.org/2001/XMLSchema/",
                     'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
                     'xsi:schemaLocation': XSI_CMD + " " + XSI_XSD,
                     'CMDVersion':'1.1'}
    # topattributes = {'CMDVersion':'1.1'}
    top = ET.Element('CMD', topattributes)

    # Add a header
    hdr = ET.SubElement(top, "Header", {})
    mdCreator = ET.SubElement(hdr, "MdCreator")
    # mdCreator.text = request.user.username
    mdCreator.text = sUserName
    mdSelf = ET.SubElement(hdr, "MdSelfLink")

    # If published: add the self link
    if colThis.pidname != None:
        # The selflink is the persistent identifier, preceded by 'hdl:'
        mdSelf.text = "hdl:{}/{}".format(colThis.handledomain, colThis.pidname)
    mdProf = ET.SubElement(hdr, "MdProfile")
    mdProf.text = XSD_ID

    # Obligatory for Collbank: add a display-name
    mdDisplayName = ET.SubElement(hdr, "MdCollectionDisplayName")
    mdDisplayName.text = "CollBank"

    # Add obligatory Resources
    rsc = ET.SubElement(top, "Resources", {})
    lproxy = ET.SubElement(rsc, "ResourceProxyList")
    # TODO: add resource proxy's under [lproxy]

    # The Landing page is provided by the USER!!! take it over
    oProxy = ET.SubElement(lproxy, "ResourceProxy")
    sProxyId = "lp_{}".format(colThis.get_xmlfilename())
    oProxy.set('id', sProxyId)
    # Add resource type
    oSubItem = ET.SubElement(oProxy, "ResourceType")
    oSubItem.set("mimetype", "application/x-http")
    oSubItem.text = "LandingPage"
    # Add resource ref
    oSubItem = ET.SubElement(oProxy, "ResourceRef")
    #  "http://applejack.science.ru.nl/collbank"
    # OLD: oSubItem.text = sHomeUrl  + "registry/" + colThis.get_xmlfilename()
    # oSubItem.text = REGISTRY_URL + colThis.get_xmlfilename()
    oSubItem.text = colThis.landingPage

    # Produce links to RELATION txt files if needed
    for rel_this in colThis.collection12m_relation.all():
        oProxy = ET.SubElement(lproxy, "ResourceProxy")
        sProxyId = "rel_{}_{}".format(rel_this.get_rtype_display(), rel_this.id)
        oProxy.set('id', sProxyId)
        # Add resource type
        oSubItem = ET.SubElement(oProxy, "ResourceType")
        # Dieter: use mimetype [text/tab-separated-values] for this
        oSubItem.set("mimetype", "text/tab-separated-values")
        oSubItem.text = "Resource"
        # Add resource ref
        oSubItem = ET.SubElement(oProxy, "ResourceRef")
        oSubItem.text = rel_this.get_relation_url()


    # Produce a link to the resource: search page
    if colThis.searchPage != None and colThis.searchPage != "":
        oProxy = ET.SubElement(lproxy, "ResourceProxy")
        sProxyId = "sru_{}".format(colThis.get_xmlfilename())
        oProxy.set('id', sProxyId)
        # Add resource type
        oSubItem = ET.SubElement(oProxy, "ResourceType")
        oSubItem.set("mimetype", "application/x-http") # SearchService would have: "application/sru+xml"
        oSubItem.text = "SearchPage"    # N.B: "SearchService" is reserved for the federated xml content search link
        # Add resource ref
        oSubItem = ET.SubElement(oProxy, "ResourceRef")
        #  "http://applejack.science.ru.nl/collbank"
        # oSubItem.text = request.build_absolute_uri(reverse('home'))
        # oSubItem.text = sHomeUrl 
        oSubItem.text = colThis.searchPage

    ET.SubElement(rsc, "JournalFileProxyList")
    ET.SubElement(rsc, "ResourceRelationList")
    # Return the resulting top-level element
    return top     
            
def publish_collection(coll_this, sUserName, sHomeUrl):
    """Create the XML of this collection and put it in a publishing directory"""

    # Create an object to return
    oBack = {'status': 'ok', 'msg': ''}
    # Make sure this record has a registered PID
    coll_this.register_pid()
    # Save the relation files
    coll_this.save_relations()
    # Get the XML text of this object
    (bValid, sXmlText) = create_collection_xml(coll_this, sUserName, sHomeUrl)
    if bValid:
        # Get the full path to the registry file
        fPublish = coll_this.get_publisfilename()
        # Write it to a file in the XML directory
        with open(fPublish, encoding="utf-8", mode="w") as f:  
            f.write(sXmlText)

        # Publish the .cmdi.xml
        fPublish = coll_this.get_publisfilename("joai")
        # Write it to a file in the XML directory
        with open(fPublish, encoding="utf-8", mode="w") as f:  
            f.write(sXmlText)
    else:
        oBack['status'] = 'error'
        oBack['msg'] = sXmlText
        oBack['coll'] = coll_this
    return oBack

def treat_bom(sHtml):
    """REmove the BOM marker except at the beginning of the string"""

    # Check if it is in the beginning
    bStartsWithBom = sHtml.startswith(u'\ufeff')
    # Remove everywhere
    sHtml = sHtml.replace(u'\ufeff', '')
    # Return what we have
    return sHtml

def username_is_ingroup(user, sGroup):
    # glist = user.groups.values_list('name', flat=True)

    # Only look at group if the user is known
    if user == None:
        glist = []
    else:
        glist = [x.name for x in user.groups.all()]

        # Only needed for debugging
        if bDebug:
            print("User [{}] is in groups: {}".format(user, glist))
    # Evaluate the list
    bIsInGroup = (sGroup in glist)
    return bIsInGroup

def user_is_ingroup(request, sGroup):
    # Is this user part of the indicated group?
    user = User.objects.filter(username=request.user.username).first()
    response = username_is_ingroup(user, sGroup)
    return response

def user_is_superuser(request):
    bFound = False
    # Is this user part of the indicated group?
    username = request.user.username
    if username != "":
        user = User.objects.filter(username=username).first()
        if user != None:
            bFound = user.is_superuser
    return bFound

def validateXml(xmlstr):
    """Validate an XML string against an XSD schema
    
    The first argument is a string containing the XML.
    The XSD schema that is being used must be present in the static files section.
    """

    # Get the XSD definition
    schema = getSchema()
    if schema == None: return False

    # Load the XML string into a document
    xml = etree.XML(xmlstr)

    # Perform the validation
    validation = schema.validate(xml)
    # Return a tuple with the boolean validation and a possible error log
    return (validation, schema.error_log, )

def xsd_error_list(lError, sXmlStr):
    """Transform a list of XSD error objects into a list of strings"""

    lHtml = []
    # lHtml.append("<html><body><h3>Fouten in het XML bestand</h3><table>")
    lHtml.append("<h3>Fouten in het XML bestand</h3><table>")
    lHtml.append("<thead><th>line</th><th>column</th><th>level</th><th>domain</th><th>type</th><th>message</th></thead>")
    lHtml.append("<tbody>")
    for oError in lError:
        lHtml.append("<tr><td>" + str(oError.line) + "</td>" +
                     "<td>" +str(oError.column) + "</td>" +
                     "<td>" +oError.level_name + "</td>" + 
                     "<td>" +oError.domain_name + "</td>" + 
                     "<td>" +oError.type_name + "</td>" + 
                     "<td>" +oError.message + "</td>")
    lHtml.append("</tbody></table>")
    # Add the XML string
    lHtml.append("<h3>Het XML bestand:</h3>")
    lHtml.append("<div class='rawxml'><pre class='brush: xml;'>" + sXmlStr.replace("<", "&lt;").replace(">", "&gt;") + "</pre></div>")
    # Finish the HTML feedback
    # lHtml.append("</body></html>")
    return "\n".join(lHtml)

def xsd_error_as_simple_string(error):
    """
    Returns a string based on an XSD error object with the format
    LINE:COLUMN:LEVEL_NAME:DOMAIN_NAME:TYPE_NAME:MESSAGE.
    """
    parts = [
        error.line,
        error.column,
        error.level_name,
        error.domain_name,
        error.type_name,
        error.message
    ]
    return ':'.join([str(item) for item in parts])



# ============= Standard Views ==============================================

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    # Make the response
    context = dict(title="RU-CollBank",
                   year=datetime.now().year)
    context = get_application_context(request, context)
    response= render(request,'collection/index.html', context=context)

    # Return the response
    return response    

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    context = dict(title="Contact",
                   message='Henk van den Heuvel (Henk.vandenHeuvel@ru.nl)',
                   year=datetime.now().year)
    context = get_application_context(request, context)

    response = render(request, 'collection/contact.html', context)
    return response

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    context = dict(title="About",
                   message='Radboud University Collection Bank utility.',
                   year=datetime.now().year)
    context = get_application_context(request, context)

    response = render(request, 'collection/about.html', context)
    return response

def nlogin(request):
    """Renders the not-logged-in page."""
    assert isinstance(request, HttpRequest)
    context =  {    'title':'Not logged in', 
                    'message':'Radboud University Collbank utility.',
                    'year':datetime.now().year,}
    return render(request,'collection/nlogin.html', context)

def signup(request):
    """Provide basic sign up and validation of it """

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Save the form
            form.save()
            # Create the user
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            # also make sure that the user gets into the STAFF,
            #      otherwise he/she may not see the admin pages
            user = authenticate(username=username, 
                                password=raw_password,
                                is_staff=True)
            user.is_staff = True
            user.save()
            # Add user to the "RegistryUser" group
            g = Group.objects.get(name="RegistryUser")
            if g != None:
                g.user_set.add(user)
            # Log in as the user
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'collection/signup.html', {'form': form})

def login_as_user(request, user_id):
    assert isinstance(request, HttpRequest)

    # Find out who I am
    supername = request.user.username
    super = User.objects.filter(username__iexact=supername).first()
    if super == None:
        return nlogin(request)

    # Make sure that I am superuser
    if super.is_staff and super.is_superuser:
        user = User.objects.filter(username__iexact=user_id).first()
        if user != None:
            # Perform the login
            login(request, user)
            return HttpResponseRedirect(reverse("home"))

    return home(request)

def output(request, collection_id):
    """Provide XML-output for the specified collection"""

    selected_collection = get_object_or_404(Collection,pk=collection_id)
    file_name = Collection.make_xml(selected_collection)
    return HttpResponse(open(file_name).read(), content_type='text/xml')

def reload_collbank(request=None):
    """Clear the Apache cache by touching the WSGI file"""

    # Refresh the wsgi script
    os.utime(WSGI_FILE,None)

    # Use the obj.refresh_from_db() function (since Django 1.8)
    # NOTE: doesn't really seem to work.
    #       what does work: add __init__ function to the form that is shown
    #                       re-load "choices" in this __init__ function
    #for obj in Collection.objects.all():
    #    obj.refresh_from_db()
    #for obj in Language.objects.all():
    #    obj.refresh_from_db()
    #for obj in FieldChoice.objects.all():
    #    obj.refresh_from_db()
    #for obj in Genre.objects.all():
    #    obj.refresh_from_db()

    # If this is a HTTP request, give an appropriate response
    if request != None:
        from django.shortcuts import render_to_response
        return render_to_response('collection/index.html')

def subtype_choices(request):
    """Provide the list of subtypes valid for the chosen DCtype-number"""

    # Get the DCtype ID value that has been selected by the user (delivered by JavaScript)
    sDCtype_id = request.GET.get('dctype_type')
    # Get the 'choices' for the DCtype from which we need to find the selected DCtype
    arDCtype = Resource._meta.get_field('DCtype').choices
    arThis = [item for item in arDCtype if item[0] == sDCtype_id]
    # Sanity check
    if len(arThis) > 0:
        # get the STRING belonging to the first tuple that satisfies the ID condition
        sDCtype = arThis[0][1]
        # Get the choices of subtype for this DCtype
        choices = build_choice_list(RESOURCE_TYPE, 'after', sDCtype)
        sOut = json.dumps(list(choices))
    else:
        # rturn empty-handedly
        sOut = "{}"
    return HttpResponse(sOut)


# ============= Application specific Views ==================================

class CollectionListView(ListView):
    """Listview of collections"""

    model = Collection
    context_object_name='collection'
    template_name = 'collection/overview.html'
    order_cols = ['id', 'identifier']
    order_heads = [{'name': 'id', 'order': 'o=1', 'type': 'int'}, 
                   {'name': 'Identifier', 'order': 'o=2', 'type': 'str'}, 
                   {'name': 'Description', 'order': '', 'type': 'str'},
                   {'name': 'Status', 'order': '', 'type': 'str'}]

    def render_to_response(self, context, **response_kwargs):
        """Check if downloading is needed or not"""
        sType = self.request.GET.get('submit_type', '')
        if sType == 'tar':
            return self.download_to_tar(context)
        elif sType == 'zip':
            return self.download_to_zip(context)
        elif sType == 'publish':
            # Perform the publishing
            context['publish'] = self.publish_xml(context)
            if context['publish']['status'] == 'error':
                sHtml = context['publish']['html']
                return HttpResponse(sHtml)
            else:
                # Return a positive result
                return super(CollectionListView, self).render_to_response(context, **response_kwargs)
        else:
            return super(CollectionListView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        # Get the base implementation first of the context
        context = super(CollectionListView, self).get_context_data(**kwargs)

        # ======== One-time adaptations ==============
        listview_adaptations("collection_list")

        # Add permissions
        context = get_application_context(self.request, context)

        # Add our own elements
        context['app_prefix'] = APP_PREFIX
        # context['static_root'] = STATIC_ROOT
        # Figure out which ordering to take
        order = 'identifier'
        initial = self.request.GET
        bAscending = True
        sType = 'str'
        if 'o' in initial:
            iOrderCol = int(initial['o'])
            bAscending = (iOrderCol>0)
            iOrderCol = abs(iOrderCol)
            order = self.order_cols[iOrderCol-1]
            sType = self.order_heads[iOrderCol-1]['type']
            if bAscending:
                self.order_heads[iOrderCol-1]['order'] = 'o=-{}'.format(iOrderCol)
            else:
                # order = "-" + order
                self.order_heads[iOrderCol-1]['order'] = 'o={}'.format(iOrderCol)
        if sType == 'str':
            qs = Collection.objects.order_by(Lower(order))
        else:
            qs = Collection.objects.order_by(order)
        if not bAscending:
            qs = qs.reverse()
        context['overview_list'] = qs.select_related()
        context['order_heads'] = self.order_heads
        # Return the calculated context
        return context

    def download_to_tar(self, context):
        """Make the XML representation of ALL collections downloadable as a tar.gz"""

        # Get the overview list
        qs = context['overview_list']
        if qs != None and len(qs) > 0:
            out = io.BytesIO()
            # Combine the files
            with tarfile.open(fileobj=out, mode="w:gz") as tar:
                for coll_this in qs:
                    sHomeUrl = request.build_absolute_uri(reverse('home'))
                    sUserName = request.user.username
                    # Get the XML text of this object
                    (bValid, sXmlText) = create_collection_xml(coll_this, sUserName, sHomeUrl)
                    if bValid:
                        sEnc = sXmlText.encode('utf-8')
                        bData = io.BytesIO(sEnc)

                        info = tarfile.TarInfo(name=coll_this.identifier + ".xml")
                        info.size = len(sEnc)
                        tar.addfile(tarinfo=info, fileobj=bData)
                    else:
                        # Return the error response
                        response = HttpResponse(sXmlText)

            # Create the HttpResponse object with the appropriate header.
            response = HttpResponse(out.getvalue(), content_type='application/x-gzip')
            response['Content-Disposition'] = 'attachment; filename="collbank_all.tar.gz"'
        else:
            # Return the error response
            response = HttpResponse("<div>The overview list is empty</div><div><a href=\"/"+APP_PREFIX+"\">Back</a></div>")

        # Return the result
        return response

    def download_to_zip(self, context):
        """Make the XML representation of ALL collections downloadable as a .zip"""

        # Get the overview list
        qs = context['overview_list']
        if qs != None and len(qs) > 0:
            temp = tempfile.TemporaryFile()
            # Combine the files
            with zipfile.ZipFile(temp, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for coll_this in qs:
                    sHomeUrl = request.build_absolute_uri(reverse('home'))
                    sUserName = request.user.username
                    # Get the XML text of this object
                    (bValid, sXmlText) = create_collection_xml(coll_this, sUserName, sHomeUrl)
                    if bValid:
                        archive.writestr(coll_this.identifier + ".xml", sXmlText)
                    else:
                        # Return the error response
                        response = HttpResponse(sXmlText)
                # Do some checking
                x = 1
            # Get file information
            iLength = temp.tell()
            temp.seek(0)
            # Use a wrapper to chunk-send it
            wrapper = FileWrapper(temp)
            # Create the HttpResponse object with the appropriate header.
            response = HttpResponse(wrapper, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="collbank_all.zip"'
            response['Content-Length'] = iLength
        else:
            # Return the error response
            response = HttpResponse("<div>The overview list is empty</div><div><a href=\"/"+APP_PREFIX+"\">Back</a></div>")

        # Return the result
        return response

    def publish_xml(self, context):
        """Create XML of all collections, give them a PID and save them in the /database/xml directory"""

        # Get the overview list -- which is what I am able to publish myself anyway
        qs = context['overview_list']
        oBack = {'status': 'unknown', 'written': 0}
        iWritten = 0
        iErrors = 0
        if qs != None and len(qs) > 0:
            # Assuming all goes well
            oBack['status'] = 'published'
            coll_list = []
            sHomeUrl = self.request.build_absolute_uri(reverse('home'))
            sUserName = self.request.user.username
            # Walk all the descriptors in the queryset
            for coll_this in qs:
                oPublish = publish_collection(coll_this, sUserName, sHomeUrl)
                if oPublish['status'] == 'error':
                    iErrors += 1
                    coll_list.append(oPublish)
                else:
                    iWritten += 1
            # Adapt the status
            oBack['written'] = iWritten
            oBack['errors'] = iErrors
            oBack['coll_list'] = coll_list
        else:
            oBack['status'] = 'empty'

        # Return good status
        return oBack


class CollectionDetailView(DetailView):
    """Details of a selected collection"""

    model = Collection
    export_xml = True
    context_object_name = 'collection'
    template_name = 'collection/coll_detail.html'
    slug_field = 'pidname'
    slug_field = 'get_xmlfilename'
    
    def get(self, request, *args, **kwargs):
        context = {}
        self.template_name = 'collection/coll_detail.html'
        # If this is 'registry' then get the id
        if 'type' in kwargs and kwargs['type'] == 'registry':
            # Find out which instance this is
            sSlug = kwargs['slug']
            arSlug = sSlug.split("_")
            self.pk = int(arSlug[1])
            self.kwargs['pk'] = self.pk
        # Get the object in the standard way
        self.object = self.get_object()
        # Check what kind of output we need to give
        if 'type' in kwargs:
            # Check if this is a /handle request, which needs to be turned into a /registry one
            if kwargs['type'] == 'handle':
                # Get the View object in the standard way
                self.object = self.get_object()
                # Make sure the PID is registered
                self.instance.register_pid()
                # Get the correct slug name
                sSlug = self.instance.get_xmlfilename()
                return HttpResponseRedirect(reverse('registry', kwargs={'type': 'registry', 'slug': sSlug}))
            # We can come here directly or through /handle
            if kwargs['type'] == 'registry':
                # TODO: change this to download the file that is actually in the REGISTRY
                bValid = True
                bCsv = False
                sCsvText = "(empty)"
                try:
                    # Find out which instance this is
                    sSlug = kwargs['slug']
                    # This might be a text file
                    if sSlug.endswith(".txt"):
                        # We are assuming this is a collection-relation csv file
                        fCsvFile = os.path.abspath(os.path.join(REGISTRY_DIR, sSlug))
                        if os.path.isfile(fCsvFile):
                            with open(fCsvFile, encoding="utf-8", mode="r") as f:
                                sCsvText = f.read()
                        bCsv = True
                    else:
                        arSlug = sSlug.split("_")
                        id = int(arSlug[1])
                        self.instance = Collection.objects.filter(id=id).first()
                        if self.instance == None:
                            bValid = False
                            sXmlText = "Could not find the resource with slug {}".format(
                                sSlug)
                        else:
                            # Get the XML file and show it
                            sFileName = self.instance.get_xmlfilename() + ".xml"
                            # THink of a filename
                            fPublish = os.path.abspath(os.path.join(WRITABLE_DIR, "xml", sFileName))
                            # Write it to a file in the XML directory
                            with open(fPublish, encoding="utf-8", mode="r") as f:  
                                sXmlText = f.read()
                except:
                    bValid = False
                    sXmlText = "Could not fetch the resource with identifier {}".format(
                        self.instance.identifier)
                if bValid:
                    # Is this csv?
                    if bCsv:
                        response = HttpResponse(sCsvText, content_type='text/plain')
                    else:
                        # Create the HttpResponse object with the appropriate CSV header.
                        response = HttpResponse(sXmlText, content_type='text/xml')
                        # response['Content-Disposition'] = 'attachment; filename="'+sFileName+'.xml"'
                else:
                    # Return the error response
                    response = HttpResponse(sXmlText)

                # Return the result
                return response
            elif kwargs['type'] == 'publish':
                # Get an evaluation context
                context = self.get_context_data()
                # First perform validation
                evaluate = self.get_validation(context)
                # Action depends on the size of eval_list
                if len(evaluate['eval_list']) == 0:
                    # Publish it
                    self.publish()
                    # Return to the overview
                    return redirect(reverse('overview'))
                else:
                    # Make the evaluation available
                    context['evaluate'] = evaluate
                    # Show the list of errors to the user
                    return self.render_to_response(context)
            elif kwargs['type'] == 'output':
                # Publish it
                self.publish()
                return self.download_to_xml(context)
            elif kwargs['type'] == 'evaluate':
                # Get an evaluation context
                context = self.get_context_data()
                # Get an evaluation context
                evaluate = self.get_validation(context)
                # Make the evaluation available
                context['evaluate'] = evaluate
                # Evaluate this collection to see if all is okay
                return self.render_to_response(context)

        # This is where we get in all other cases (e.g. no 'type' in the kwargs)

        # For further processing we need to have the context
        context = self.get_context_data(object=self.object)

        # Visualize using the context
        return self.render_to_response(context)

    def get_validation(self, context):
        # Initialisation
        lZeroN = [{'list': 'coll_resources', 'name': 'Resource'},
                  {'list': 'coll_provenances', 'name': 'Provenance'}]
        lZeroOne = [{'list': 'coll_linguality', 'name': 'Linguality'},
                  {'list': 'coll_access', 'name': 'Access'},
                  {'list': 'coll_docu', 'name': 'Documentation'}]

        # Start evaluating
        evaluate = {}
        evaluate['status'] = 'This collection contains no errors'
        eval_list = []
        num_errors = 0
        # Check the main part
        coll_main = context['coll_main']
        for oMain in coll_main:
            if oMain['obl'].startswith('1'):
                # This is an obligatory one
                v = oMain['value']
                t = oMain['type']
                if (t == 'single' or t == 'code') and (v == None or v == ''):
                    eval_list.append({'field': oMain['name'], 
                                        'value': "Main field {} should occur {} time(s), but it is empty".format(
                                            oMain['name'], oMain['obl'])})
                    num_errors += 1
                elif (v == None or len(v) == 0):
                    eval_list.append({'field': oMain['name'], 
                                        'value': "Main field {} is a list that should occur {} time(s), but it is empty".format(
                                            oMain['name'], oMain['obl'])})
                    num_errors += 1

        # Check for all the lists that must occur at least once
        # That is only 1 list: resources
        if not 'coll_resources' in context or len(context['coll_resources']) == 0:
            eval_list.append({'field': 'resources', 'value': "No resources are defined, but each collection must have at least one"})
            num_errors += 1

        # Check all lists that occur 0-n
        for list_spec in lZeroN:
            list_this = context[list_spec['list']]
            list_name = list_spec['name']
            # Check each resource
            # for idx, res_spec in enumerate(context['coll_resources']):
            for idx, res_spec in enumerate(list_this):
                # resource = res_spec['resource']
                oRes = res_spec['info_list']
                for item in oRes:
                    if item['obl'].startswith('1'):
                        # This is an obligatory one
                        v = item['value']
                        t = item['type']
                        if (t == 'single' or t == 'code') and (v == None or v == ''):
                            eval_list.append({'field': item['name'], 
                                                'value': "{} {}: field {} should occur {} time(s), but it is empty".format(
                                                    list_name, idx+1, item['name'], item['obl'])})
                            num_errors += 1
                        elif (v == None or len(v) == 0):
                            eval_list.append({'field': item['name'], 
                                                'value': "{} {}: field {} is a list that should occur {} time(s), but it is empty".format(
                                                    list_name, idx+1, item['name'], item['obl'])})
                            num_errors += 1

        # Check for everything that occurs 0-1 times
        for list_spec in lZeroOne:
            list_this = context[list_spec['list']]
            list_name = list_spec['name']
            # Check all the items in the list
            for item in list_this:
                if item['obl'].startswith('1'):
                    # This is an obligatory one
                    v = item['value']
                    t = item['type']
                    if (t == 'single' or t == 'code') and (v == None or v == ''):
                        eval_list.append({'field': item['name'], 
                                            'value': "{} {}: field {} should occur {} time(s), but it is empty".format(
                                                list_name, idx+1, item['name'], item['obl'])})
                        num_errors += 1
                    elif (v == None or len(v) == 0):
                        eval_list.append({'field': item['name'], 
                                            'value': "{} {}: field {} is a list that should occur {} time(s), but it is empty".format(
                                                list_name, idx+1, item['name'], item['obl'])})
                        num_errors += 1

        # Define the status if there are errors
        if num_errors > 0:
            evaluate['status'] = "This collection contains at least {} error(s)".format(num_errors)

        # The following lists or elements need no further checking because they are either 0-1 or 0-n:
        # validation [0-1]

        evaluate['eval_list'] = eval_list
        # Return the evaluation
        return evaluate

    def get_object(self):
        obj = super(CollectionDetailView,self).get_object()
        self.instance = obj
        form = CollectionForm(instance=obj)
        return form

    def get_context_data(self, **kwargs):
        # Get the basic context
        context = super(CollectionDetailView, self).get_context_data(**kwargs)

        # Initialize
        coll_main = []

        # Preliminary own context information
        context['now'] = timezone.now()
        context['collection'] = self.instance
        # Make sure we know whether it was authenticated
        context['authenticated'] = self.request.user.is_authenticated

        # For ease of processing
        def append_item(coll_this, sName, sObl, sType, qs):
            if sType == "single" or sType == "code" or (qs != None and qs.count() > 0):
                oItem = {"name": sName, "obl": sObl, "type": sType, "value": qs}
                coll_this.append(oItem)
            elif (sType == "numbered" or sType == "list" ) and sObl.startswith("1") and (qs==None or qs.count() == 0):
                oItem = {"name": sName, "obl": sObl, "type": sType, "value": qs}
                coll_this.append(oItem)


        # Provide the main-level information for the fields
        append_item(coll_main, "LandingPage",              "1",   "single", self.instance.landingPage)
        append_item(coll_main, "Title(s)",                 "1-n", "numbered", self.instance.collection12m_title.all())
        append_item(coll_main, "Owner(s)",                 "0-n", "numbered", self.instance.collection12m_owner.all())
        append_item(coll_main, "Genre(s)",                 "0-n", "list", self.instance.collection12m_genre.all())
        append_item(coll_main, "Language disorder(s)",     "0-n", "numbered", self.instance.collection12m_languagedisorder.all())
        append_item(coll_main, "Domain(s)",                "0-n", "list", self.instance.collection12m_domain.all())
        append_item(coll_main, "Language(s)",              "1-n", "list", self.instance.coll_languages.all())
        append_item(coll_main, "CLARIN centre",            "0-1", "single", self.instance.clarinCentre)
        append_item(coll_main, "Persistent identifier(s)", "0-n", "list", self.instance.collection12m_pid.all())
        append_item(coll_main, "Version",                  "0-1", "code", self.instance.version)
        append_item(coll_main, "Size(s)",                  "0-n", "list", self.instance.collection12m_totalsize.all())
        append_item(coll_main, "Relation(s)",              "0-n", "numbered", self.instance.collection12m_relation.all())
        append_item(coll_main, "Creator(s)",               "0-n", "numbered", self.instance.collection12m_resourcecreator.all())
        append_item(coll_main, "Project(s)",               "0-n", "numbered", self.instance.collection12m_project.all())
        context['coll_main'] = coll_main
        # Get through all resources
        coll_resources = []
        for resource in self.instance.collection12m_resource.all():
            # Gather information
            sDCtype = "A <code>DCtype</code> must be specified" if resource.DCtype == None else resource.get_DCtype_display()
            sSubtype = "No DCtype available" if resource.DCtype == None else resource.subtype_only()
            # Create an item for this resource
            resource_items = []
            append_item(resource_items, "Dublin-Core Type",  "1", "single", sDCtype)
            append_item(resource_items, "subtype",           "0-1", "single", sSubtype)
            append_item(resource_items, "Modality",          "1-n", "list", resource.modalities.all())
            append_item(resource_items, "Recording environment", "0-n", "list", resource.recordingenvironments.all())
            append_item(resource_items, "Recording condition", "0-n", "list", resource.recordingconditions.all())
            append_item(resource_items, "Channel",           "0-n", "list", resource.channels.all())
            append_item(resource_items, "Social context",    "0-n", "list", resource.socialcontexts.all())
            append_item(resource_items, "Planning type",     "0-n", "list", resource.planningtypes.all())
            append_item(resource_items, "Interactivity",     "0-n", "list", resource.interactivities.all())
            append_item(resource_items, "Involvement",       "0-n", "list", resource.involvements.all())
            append_item(resource_items, "Audience",          "0-n", "list", resource.audiences.all())
            # speech corpus stuff
            if resource.speechCorpus:
                append_item(resource_items, "SC duration speech",   "0-1", "single", resource.speechCorpus.durationOfEffectiveSpeech)
                append_item(resource_items, "SC duration full",     "0-1", "single", resource.speechCorpus.durationOfFullDatabase)
                append_item(resource_items, "SC speakers",          "0-1", "single", resource.speechCorpus.numberOfSpeakers)
                append_item(resource_items, "SC sp. demogr",        "0-1", "single", resource.speechCorpus.speakerDemographics)
            # Written corpus stuff
            if resource.writtenCorpus:
                append_item(resource_items, "WC authors", "0-1", "single", resource.writtenCorpus.numberOfAuthors)
                append_item(resource_items, "WC auth. demogr", "0-1", "single", resource.writtenCorpus.authorDemographics)
            # Look at the sizes
            for item in resource.totalsize12m_resource.all():
                sSize = "{} {}".format(item.size, item.sizeUnit)
                append_item(resource_items, "Size", "0-n", "single", sSize)

            # Look at the annotations
            append_item(resource_items, "Annotation", "0-n", "numbered", resource.annotations.all())

            # Look at the media
            for item in resource.media_items.all():
                sFmts = ""
                for fmt in item.mediaformat12m_media.all():
                    if sFmts != "": 
                        sFmts += ", "
                    sFmts += fmt.get_name_display()
                append_item(resource_items, "Media", "0-n", "single", sFmts)
            # Combine
            resource_obj = {'resource': resource, 'info_list': resource_items}
            # Add to the list
            coll_resources.append(resource_obj)
        # Add the list of resources to the context
        context['coll_resources'] = coll_resources

        # Treat the provenances
        coll_provenances = []
        for provenance in self.instance.collection12m_provenance.all(): 
            prov_this = []
            # Look for temporal
            if provenance.temporalProvenance:
                append_item(prov_this, "Temporal", "0-1", "single", provenance.temporalProvenance.get_view())
            for geo in provenance.g_provenances.all():
                append_item(prov_this, "Cities", "0-n", "list", geo.cities.all())

                cntry = geo.countryiso
                # Use the NEW method with CountryIso
                sCountry = "{} {}".format(cntry.english, cntry.alpha2)
                append_item(prov_this, "Country", "0-1", "single", sCountry)
                    
            coll_provenances.append({'info_list': prov_this})
        # Add the list of povenances to the context
        context['coll_provenances'] = coll_provenances

        # Linguality
        linguality = self.instance.linguality
        coll_ling = []
        if linguality != None:
            append_item(coll_ling, "Type", "0-n", "list", linguality.linguality_types.all())
            append_item(coll_ling, "Nativeness", "0-n", "list", linguality.linguality_nativenesses.all())
            append_item(coll_ling, "AgeGroup", "0-n", "list", linguality.linguality_agegroups.all())
            append_item(coll_ling, "Status", "0-n", "list", linguality.linguality_statuses.all())
            append_item(coll_ling, "Variant", "0-n", "list", linguality.linguality_variants.all())
            append_item(coll_ling, "MultiType", "0-n", "list", linguality.multilinguality_types.all())
        context['coll_linguality'] = coll_ling

        # Accessibility
        access = self.instance.access
        coll_access = []
        if access != None:
            append_item(coll_access, "Name", "1", "single", access.name)
            append_item(coll_access, "Availability", "0-n", "list", access.acc_availabilities.all())
            append_item(coll_access, "License name(s)", "0-n", "list", access.acc_licnames.all())
            append_item(coll_access, "Licence URL(s)", "0-n", "list", access.acc_licurls.all())
            append_item(coll_access, "Non-commercial usage", "0-1", "single", access.nonCommercialUsageOnly)
            append_item(coll_access, "Website(s)", "0-n", "list", access.acc_websites.all())
            append_item(coll_access, "ISBN", "0-1", "single", access.ISBN)
            append_item(coll_access, "ISLRN", "0-1", "single", access.ISLRN)
            append_item(coll_access, "Contact(s)", "0-n", "list", access.acc_contacts.all())
            append_item(coll_access, "Medium(s)", "0-n", "list", access.acc_mediums.all())

        context['coll_access'] = coll_access

        # Documentation
        docu = self.instance.documentation
        coll_docu = []
        if docu != None:
            append_item(coll_docu, "Language(s)", "1-n", "list", docu.doc_languages.all())
            append_item(coll_docu, "Type(s)", "0-n", "list", docu.doc_types.all())
            append_item(coll_docu, "File(s)", "0-n", "list", docu.doc_files.all())
            append_item(coll_docu, "URL(s)", "0-n", "list", docu.doc_urls.all())
        context['coll_docu'] = coll_docu

        # Validation
        vali = self.instance.validation
        coll_vali = []
        if vali != None:
            append_item(coll_vali, "Type", "0-1", "single", vali.type)
            append_item(coll_vali, "Method(s)", "0-n", "list", vali.validationmethods.all())

        context['coll_vali'] = coll_vali

        # Return the whole context
        return context

    def publish(self):
        """Publish this collection"""

        sHomeUrl = self.request.build_absolute_uri(reverse('home'))
        sUserName = self.request.user.username
        oBack = publish_collection(self.instance, sUserName, sHomeUrl)
        if oBack['status'] == 'error':
            # TODO: Show the error??
            pass
        # Return True if status is okay
        return (oBack['status'] == 'ok')

    def download_to_xml(self, context):
        """Make the XML representation of this collection downloadable"""

        # Get to this collection instance
        itemThis = self.instance
        # Make sure the PID is registered
        if itemThis.register_pid():
            # Construct a file name based on the identifier
            sFileName = 'collection-{}'.format(getattr(itemThis, 'identifier'))
            sHomeUrl = self.request.build_absolute_uri(reverse('home'))
            sUserName = self.request.user.username
            # Get the XML of this collection
            (bValid, sXmlStr) = create_collection_xml(itemThis, sUserName, sHomeUrl)
            if bValid:
                # Create the HttpResponse object with the appropriate CSV header.
                response = HttpResponse(sXmlStr, content_type='text/xml')
                response['Content-Disposition'] = 'attachment; filename="'+sFileName+'.xml"'
            else:
                # Return the error response
                response = HttpResponse(sXmlStr)
        else:
            # Provide an error response
            sErrMsg = "Unable to register the PID"
            response = HttpResponse(sErrMsg)

        # Return the result
        return response