"""
Definition of views.
"""

from django.views.generic.detail import DetailView
from django.views.generic import ListView
from django.shortcuts import get_object_or_404, render
from django.http import HttpRequest, HttpResponse
from django.template import RequestContext, loader
from django.contrib.admin.templatetags.admin_list import result_headers
from django.db.models.functions import Lower
import json
from datetime import datetime
from xml.dom import minidom
import xml.etree.ElementTree as ET
from lxml import etree
import os
from collbank.collection.models import *
from collbank.settings import OUTPUT_XML, APP_PREFIX, WSGI_FILE, STATIC_ROOT, WRITABLE_DIR, COUNTRY_CODES, LANGUAGE_CODE_LIST
from collbank.collection.admin import CollectionAdmin

# Local variables
XSI_CMD = "http://www.clarin.eu/cmd/"
XSD_ID = "clarin.eu:cr1:p_1459844210473"
XSI_XSD = "https://catalog.clarin.eu/ds/ComponentRegistry/rest/registry/1.1/profiles/" + XSD_ID + "/xsd/"

# General help functions
def add_element(optionality, col_this, el_name, crp, **kwargs):
    """Add element [el_name] from collection [col_this] under the XML element [crp]
    
    Note: make use of the options defined in [kwargs]
    """

    foreign = ""
    if "foreign" in kwargs: foreign = kwargs["foreign"]
    field_choice = ""
    if "fieldchoice" in kwargs: field_choice = kwargs["fieldchoice"]
    col_this_el = getattr(col_this, el_name)
    sub_name = el_name
    if "subname" in kwargs: sub_name = kwargs["subname"]
    if optionality == "0-1" or optionality == "1":
        col_value = col_this_el
        if optionality == "1" or col_value != None:
            if foreign != "" and not isinstance(col_this_el, str):
                col_value = getattr(col_this_el, foreign)
            if field_choice != "": col_value = choice_english(field_choice, col_value)
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
            if field_choice != "": col_value = choice_english(field_choice, col_value)
            # Make sure the value is a string
            col_value = str(col_value)
            if col_value == "(empty)": 
                col_value = "unknown"
            else:
                title_element = ET.SubElement(crp, sub_name)
                title_element.text = col_value
    # Return positively
    return True
    
def make_collection_top():
    """Create the top-level elements for a collection"""

    # Define the top-level of the xml output
    topattributes = {'xmlns': "http://www.clarin.eu/cmd/" ,
                     'xmlns:xsd':"http://www.w3.org/2001/XMLSchema/",
                     'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance/",
                     'xsi:schemaLocation': XSI_CMD + " " + XSI_XSD,
                     'CMDVersion':'1.1'}
    # topattributes = {'CMDVersion':'1.1'}
    top = ET.Element('CMD', topattributes)

    # Add a header
    hdr = ET.SubElement(top, "Header", {})
    mdSelf = ET.SubElement(hdr, "MdSelfLink")
    mdProf = ET.SubElement(hdr, "MdProfile")
    mdProf.text = XSD_ID
    # Add obligatory Resources
    rsc = ET.SubElement(top, "Resources", {})
    lproxy = ET.SubElement(rsc, "ResourceProxyList")
    # TODO: add resource proxy's under [lproxy]

    ET.SubElement(rsc, "JournalFileProxyList")
    ET.SubElement(rsc, "ResourceRelationList")
    # Return the resulting top-level element
    return top
        
            
def add_collection_xml(col_this, crp):
    """Add the collection information from [col_this] to XML element [crp]"""

    # title (1-n)
    add_element("1-n", col_this, "title", crp, foreign="name")
    # description (0-1)
    add_element("0-1", col_this, "description", crp)
    # owner (0-n)
    add_element("0-n", col_this, "owner", crp, foreign="name")
    # genre (0-n)
    add_element("0-n", col_this, "genre", crp, foreign="name", fieldchoice=GENRE_NAME)
    # languageDisorder(0-n)
    add_element("0-n", col_this, "languageDisorder", crp, foreign="name")
    # domain (0-n)
    for domain_this in col_this.domain.all():
        # Add the domains
        add_element("0-n", domain_this, "name", crp, foreign="name", subname="domain")
    # clarinCentre (0-1)
    add_element("0-1", col_this, "clarinCentre", crp)
    # PID (0-n)
    add_element("0-n", col_this, "pid", crp, foreign="code", subname="PID")
    # version (0-1)
    add_element("0-1", col_this, "version", crp)
    # resource (1-n)
    for res_this in col_this.resource.all():
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
        add_element("1-n", res_this, "modality", res, foreign="name", fieldchoice=RESOURCE_MODALITY )
        # recording Environment (0-n)
        add_element("0-n", res_this, "recordingEnvironment", res, foreign="name", fieldchoice=SPEECHCORPUS_RECORDINGENVIRONMENT)
        # Recording conditions (0-n)
        add_element("0-n", res_this, "recordingConditions", res, foreign="name")
        # channel (0-n)
        add_element("0-n", res_this, "channel", res, foreign="name", fieldchoice=SPEECHCORPUS_CHANNEL)
        # socialContext (0-n)
        add_element("0-n", res_this, "socialContext", res, foreign="name", fieldchoice=SPEECHCORPUS_SOCIALCONTEXT)
        # planningType (0-n)
        add_element("0-n", res_this, "planningType", res, foreign="name", fieldchoice=SPEECHCORPUS_PLANNINGTYPE)
        # interactivity (0-n)
        add_element("0-n", res_this, "interactivity", res, foreign="name", fieldchoice=SPEECHCORPUS_INTERACTIVITY)
        # involvement (0-n)
        add_element("0-n", res_this, "involvement", res, foreign="name", fieldchoice=SPEECHCORPUS_INVOLVEMENT)
        # audience (0-n)
        add_element("0-n", res_this, "audience", res, foreign="name", fieldchoice=SPEECHCORPUS_AUDIENCE)
        # speechCorpus (0-1)
        speech_this = col_this.speechCorpus
        if speech_this != None:
            # Set the sub-element
            speech = ET.SubElement(res, "speechCorpus")
            # Process the elements of the speech corpus            
            add_element("0-n", speech_this, "conversationalType", speech, foreign="name", fieldchoice=SPEECHCORPUS_CONVERSATIONALTYPE)            
            add_element("0-1", speech_this, "durationOfEffectiveSpeech", speech, foreign="name")
            add_element("0-1", speech_this, "durationOfFullDatabase", speech, foreign="name")
            add_element("0-1", speech_this, "numberOfSpeakers", speech, foreign="name")
            add_element("0-1", speech_this, "speakerDemographics", speech, foreign="name")
            # audioFormat (0-n)
            for af_this in speech_this.audioFormat.all():
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
        writ_this = col_this.writtenCorpus
        if writ_this != None:
            # Set the sub-element
            writ = ET.SubElement(res, "writtenCorpus")
            # Process the validation elements
            add_element("0-n", writ_this, "characterEncoding", writ, foreign="name", fieldchoice=CHARACTERENCODING)
            # numberOfAuthors (0-1)
            add_element("0-1", writ_this, "numberOfAuthors", writ)
            # authorDemographics (0-1
            add_element("0-1", writ_this, "authorDemographics", writ)
        # totalSize (0-n)
        for size_this in res_this.totalSize.all():
            # Start adding this sub-element
            tot = ET.SubElement(res, "totalSize")
            # Add the size part
            add_element("1", size_this, "size", tot)
            # Add the sizeUnit part
            add_element("1", size_this, "sizeUnit", tot)
        # annotation (0-n)
        for ann_this in res_this.annotation.all():
            # Add this annotation element
            ann = ET.SubElement(res, "annotation")
            # type (1)
            add_element("1", ann_this, "type", ann, fieldchoice=ANNOTATION_TYPE)
            # mode (1)
            add_element("1", ann_this, "mode", ann, fieldchoice=ANNOTATION_MODE)
            # format (1)
            # add_element("1", ann_this, "format", ann, fieldchoice=ANNOTATION_FORMAT)
            # formatAnn (1-n)
            add_element("1-n", ann_this, "formatAnn", ann, foreign="name", subname="format", fieldchoice=ANNOTATION_FORMAT)
        # media (0-n)
        for med_this in res_this.medias.all():
            # Add the media sub-element
            med = ET.SubElement(res, "media")
            # format (0-n)
            add_element("0-n", med_this, "format", med, foreign="name", fieldchoice=MEDIA_FORMAT)
    # provenance (0-n)
    for prov_this in col_this.provenance.all():
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
        for geo_this in prov_this.geographicProvenance.all():
            # Create sub-element
            geo = ET.SubElement(prov, "geographicProvenance")
            # place (0-n)
            add_element("0-n", geo_this, "place", geo, foreign="name")
            # country (0-1)
            cntry = geo_this.country
            if cntry != None:
                # Look up the country in the list
                (sEnglish, sAlpha2) = get_country(cntry)
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
        add_element("0-n", linguality_this, "lingualityType", ling, foreign="name", fieldchoice=LINGUALITY_TYPE)
        add_element("0-n", linguality_this, "lingualityNativeness", ling, foreign="name", fieldchoice=LINGUALITY_NATIVENESS)
        add_element("0-n", linguality_this, "lingualityAgeGroup", ling, foreign="name", fieldchoice=LINGUALITY_AGEGROUP)
        add_element("0-n", linguality_this, "lingualityStatus", ling, foreign="name", fieldchoice=LINGUALITY_STATUS)
        add_element("0-n", linguality_this, "lingualityVariant", ling, foreign="name", fieldchoice=LINGUALITY_VARIANT)
        add_element("0-n", linguality_this, "multilingualityType", ling, foreign="name", fieldchoice=LINGUALITY_MULTI)
    # language (1-n)
    # add_element("1-n", col_this, "language", crp, foreign="name", fieldchoice="language.name")
    for lng_this in col_this.language.all():
        (sLngName, sLngCode) = get_language(lng_this.name)
        # Validation
        if sLngCode == "" or sLngCode == None:
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
    for rel_this in col_this.relation.all():
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
        add_element("0-n", access_this, "availability", acc, foreign="name", fieldchoice=ACCESS_AVAILABILITY)
        add_element("0-n", access_this, "licenseName", acc, foreign="name")
        add_element("0-n", access_this, "licenseUrl", acc, foreign="name", subname="licenseURL")
        add_element("0-1", access_this, "nonCommercialUsageOnly", acc, foreign="name", fieldchoice=ACCESS_NONCOMMERCIAL)
        add_element("0-n", access_this, "website", acc, foreign="name")
        add_element("0-1", access_this, "ISBN", acc, foreign="name")
        add_element("0-1", access_this, "ISLRN", acc, foreign="name")
        add_element("0-n", access_this, "medium", acc, foreign="format", fieldchoice=ACCESS_MEDIUM)
        # contact (0-n)
        for contact_this in access_this.contact.all():
            # Add this contact
            cnt = ET.SubElement(acc, "contact")
            add_element("1", contact_this, "person", cnt)
            add_element("1", contact_this, "address", cnt)
            add_element("1", contact_this, "email", cnt)
    # totalSize (0-n) -- NOTE: this is on the COLLECTION level; there also is totalsize on the RESOURCE level
    if col_this.totalSize != None:
        for size_this in col_this.totalSize.all():
            # Start adding this sub-element (under CRP)
            tot = ET.SubElement(crp, "totalSize")
            # Add the size part
            add_element("1", size_this, "size", tot)
            # Add the sizeUnit part
            add_element("1", size_this, "sizeUnit", tot)
    # resourceCreator (0-n)
    for rescrea_this in col_this.resourceCreator.all():
        # Add sub element
        res = ET.SubElement(crp, "resourceCreator")
        # Add the resource elements
        add_element("0-n", rescrea_this, "organization", res, foreign="name")
        add_element("0-n", rescrea_this, "person", res, foreign="name")
    # documentation (0-1)
    doc_this = col_this.documentation
    if doc_this != None:
        # Set the sub-element
        doc = ET.SubElement(crp, "documentation")
        # Process the documentation elements
        add_element("0-n", doc_this, "documentationType", doc, foreign="format", fieldchoice=DOCUMENTATION_TYPE)
        add_element("0-n", doc_this, "fileName", doc, foreign="name")
        add_element("0-n", doc_this, "url", doc, foreign="name")
        # add_element("1-n", doc_this, "language", doc, foreign="name", fieldchoice="language.name")
        for lng_this in doc_this.language.all():
            (sLngName, sLngCode) = get_language(lng_this.name)
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
        add_element("0-n", val_this, "method", val, foreign="name", fieldchoice=VALIDATION_METHOD)
    # project (0-n)
    for proj_this in col_this.project.all():
        # Set the sub element
        proj = ET.SubElement(crp, "project")
        # Process the project properties
        add_element("0-1", proj_this, "title", proj)
        add_element("0-n", proj_this, "funder", proj, foreign="name")
        add_element("0-1", proj_this, "URL", proj, foreign="name", subname="url")
    # There's no return value -- all has been added to [crp]

def get_country(cntryCode):
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

def get_language(lngCode):
    if str(lngCode) == "493": 
        x = 1
    # Get the language string according to the field choice
    sLanguage = choice_english("language.name", lngCode).lower()
    # Walk all language codes
    for tplLang in LANGUAGE_CODE_LIST:
        # Check in column #2 for the language name (must be complete match)
        if sLanguage == tplLang[2].lower():
            # Return the language code from column #0
            return (sLanguage, tplLang[0])
    # Empty
    return (None, None)


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

def xsd_error_list(lError, sXmlStr):
    """Transform a list of XSD error objects into a list of strings"""

    lHtml = []
    lHtml.append("<html><body><h3>Fouten in het XML bestand</h3><table>")
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
    lHtml.append("</body></html>")
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

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'collection/index.html',
        {
            'title':'RU-CollBank',
            'year':datetime.now().year,
        }
    )

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'collection/contact.html',
        {
            'title':'Contact',
            'message':'Henk van den Heuvel (H.vandenHeuvel@Let.ru.nl)',
            'year':datetime.now().year,
        }
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'collection/about.html',
        {
            'title':'About',
            'message':'Radboud University Collection Bank utility.',
            'year':datetime.now().year,
        }
    )

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

class CollectionListView(ListView):
    """Listview of collections"""

    model = Collection
    context_object_name='collection'
    template_name = 'collection/overview.html'
    order_cols = ['id', 'identifier']
    order_heads = [{'name': 'id', 'order': 'o=1', 'type': 'int'}, 
                   {'name': 'Identifier', 'order': 'o=2', 'type': 'str'}, 
                   {'name': 'Description', 'order': '', 'type': 'str'}]

    def render_to_response(self, context, **response_kwargs):
        """Check if downloading is needed or not"""
        sType = self.request.GET.get('submit_type', '')
        if sType == 'xml':
            return self.download_to_xml(context)
        else:
            return super(CollectionListView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        # Get the base implementation first of the context
        context = super(CollectionListView, self).get_context_data(**kwargs)
        # Add our own elements
        context['app_prefix'] = APP_PREFIX
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

    def convert_to_xml(self, context):
        """Convert all available collection objects to XML"""

        # Create a top-level element, including CMD, Header and Resources
        top = make_collection_top()

        # Start components and this collection component
        cmp     = ET.SubElement(top, "Components")
        # Add a <CorpusCollection> root that contains a list of <collection> objects
        colroot = ET.SubElement(cmp, "CorpusCollection")

        # Walk all the collections
        for col_this in Collection.objects.all():

            # Add a <collection> root for this collection
            crp = ET.SubElement(colroot, "collection")
            # Add the information in this collection to the xml
            add_collection_xml(col_this, crp)

        # Convert the XML to a string
        xmlstr = minidom.parseString(ET.tostring(top,encoding='utf-8')).toprettyxml(indent="  ")

        # Validate the XML against the XSD
        (bValid, oError) = validateXml(xmlstr)
        if not bValid:
            # Provide an error message
            return (False, xsd_error_list(oError, xmlstr))

        # Return this string
        return (True, xmlstr)
    
    def download_to_xml(self, context):
        """Make the XML representation of ALL collections downloadable"""

        # Construct a file name based on the identifier
        # NOT NEEDED HERE? sFileName = 'collection-{}'.format(getattr(context['collection'], 'identifier'))
        # Get the XML of this collection
        (bValid, sXmlStr) = self.convert_to_xml(context)
        if bValid:
            # Create the HttpResponse object with the appropriate CSV header.
            response = HttpResponse(sXmlStr, content_type='text/xml')
            response['Content-Disposition'] = 'attachment; filename="collbank_all.xml"'
        else:
            # Return the error response
            response = HttpResponse(sXmlStr)

        # Return the result
        return response


class CollectionDetailView(DetailView):
    """Details of a selected collection"""

    model = Collection
    export_xml = True
    context_object_name = 'collection'

    def render_to_response(self, context, **response_kwargs):
        """Check if downloading is needed or not"""
        sType = self.request.GET.get('submit_type', '')
        if sType == 'xml':
            return self.download_to_xml(context)
        elif self.export_xml:
            return self.render_to_xml(context)
        else:
            return super(CollectionDetailView, self).render_to_response(context, **response_kwargs)
        
    def convert_to_xml(self, context):
        """Convert the 'collection' object from the context to XML"""

        # Create a top-level element, including CMD, Header and Resources
        top = make_collection_top()

        # Start components and this collection component
        cmp = ET.SubElement(top, "Components")
        # Add a <CorpusCollection> root that contains a list of <collection> objects
        colroot = ET.SubElement(cmp, "CorpusCollection")
        # Add a <collection> root for this collection
        crp = ET.SubElement(colroot, "collection")

        # Access this particular collection
        col_this = context['collection']

        # Add this collection to the xml
        add_collection_xml(col_this, crp)

        # Convert the XML to a string
        xmlstr = minidom.parseString(ET.tostring(top,encoding='utf-8')).toprettyxml(indent="  ")

        # Validate the XML against the XSD
        (bValid, oError) = validateXml(xmlstr)
        if not bValid:
            # Get error messages for all the errors

            return (False, xsd_error_list(oError, xmlstr))

        # Return this string
        return (True, xmlstr)

    def download_to_xml(self, context):
        """Make the XML representation of this collection downloadable"""

        # Construct a file name based on the identifier
        sFileName = 'collection-{}'.format(getattr(context['collection'], 'identifier'))
        # Get the XML of this collection
        (bValid, sXmlStr) = self.convert_to_xml(context)
        if bValid:
            # Create the HttpResponse object with the appropriate CSV header.
            response = HttpResponse(sXmlStr, content_type='text/xml')
            response['Content-Disposition'] = 'attachment; filename="'+sFileName+'.xml"'
        else:
            # Return the error response
            response = HttpResponse(sXmlStr)

        # Return the result
        return response