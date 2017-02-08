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
import os
from collbank.collection.models import *
from collbank.settings import OUTPUT_XML, APP_PREFIX, WSGI_FILE
from collbank.collection.admin import CollectionAdmin

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
            if field_choice != "": col_value = choice_english(field_choice, col_value)
            # Make sure the value is a string
            col_value = str(col_value)
            if col_value != "":
                descr_element = ET.SubElement(crp, sub_name)
                descr_element.text = col_value
    elif optionality == "1-n" or optionality == "0-n":
        for t in col_this_el.all():
            title_element = ET.SubElement(crp, sub_name)
            col_value = getattr(t, foreign)
            if field_choice != "": col_value = choice_english(field_choice, col_value)
            # Make sure the value is a string
            col_value = str(col_value)
            title_element.text = col_value
            
def add_collection_xml(col_this, crp):
    """Add the collection information from [col_this] to XML element [crp]"""

    # title (1-n)
    add_element("1-n", col_this, "title", crp, foreign="name")
    # description (0-1)
    add_element("0-1", col_this, "description", crp)
    # owner (0-n)
    add_element("0-n", col_this, "owner", crp, foreign="name")
    # resource (1-n)
    for res_this in col_this.resource.all():
        # Add the resource top-element
        res = ET.SubElement(crp, "resource")
        # description (0-1)
        add_element("0-1", res_this, "description", res)
        # type (1) -- THIS MAY DISAPPEAR
        add_element("1", res_this, "type", res, fieldchoice =RESOURCE_TYPE)
        # TODO: possibly divide this into DCtype and (optional) subtype
        # DCtype (1)
        add_element("1", res_this, "DCtype", res, fieldchoice =RESOURCE_TYPE)
        # subtype (0-1)
        add_element("0-1", res_this, "subtype", res, fieldchoice =RESOURCE_TYPE)
        # modality (1-n)
        #for modality_this in res_this.modality.all():
            # add the modality sub-element under <resource>
            #modality = ET.SubElement(res, "modality")
            # name (1-n)
            #add_element("1-n", modality_this, "name", modality, fieldchoice=RESOURCE_MODALITY )
        add_element("1-n", res_this, "modality", modality, foreign="name", fieldchoice=RESOURCE_MODALITY )
        # recording Environment (0-n)
        add_element("0-n", res_this, "recordingEnvironment", res, fieldchoice=SPEECHCORPUS_RECORDINGENVIRONMENT)
        # Recording conditions (0-n)
        add_element("0-n", res_this, "recordingConditions", res, foreign="name")
        # channel (0-n)
        add_element("0-n", res_this, "channel", res, fieldchoice=SPEECHCORPUS_CHANNEL)
        # socialContext (0-n)
        add_element("0-n", res_this, "socialContext", res, fieldchoice=SPEECHCORPUS_SOCIALCONTEXT)
        # planningType (0-n)
        add_element("0-n", res_this, "planningType", res, fieldchoice=SPEECHCORPUS_PLANNINGTYPE)
        # interactivity (0-n)
        add_element("0-n", res_this, "interactivity", res, fieldchoice=SPEECHCORPUS_INTERACTIVITY)
        # involvement (0-n)
        add_element("0-n", res_this, "involvement", res, fieldchoice=SPEECHCORPUS_INVOLVEMENT)
        # audience (0-n)
        add_element("0-n", res_this, "audience", res, fieldchoice=SPEECHCORPUS_AUDIENCE)
        # speechCorpus (0-1)
        speech_this = col_this.speechCorpus
        if speech_this != None:
            # Set the sub-element
            speech = ET.SubElement(res, "speechCorpus")
            # Process the elements of the speech corpus            
            add_element("0-n", speech_this, "conversationalType", speech, fieldchoice=SPEECHCORPUS_CONVERSATIONALTYPE)            
            add_element("0-1", speech_this, "durationOfEffectiveSpeech", speech)
            add_element("0-1", speech_this, "durationOfFullDatabase", speech)
            add_element("0-1", speech_this, "numberOfSpeakers", speech)
            add_element("0-1", speech_this, "speakerDemographics", speech)
            # audioFormat (0-n)
            for af_this in speech_this.audioFormat.all():
                # Set the sub-element
                af = ET.SubElement(speech, "audioFormat")
                # speechCoding (0-1)
                add_element("0-1", af_this, "speechCoding", af)
                # samplingFrequency (0-1)
                add_element("0-1", af_this, "samplingFrequency")
                # compression (0-1)
                add_element("0-1", af_this, "compression", af)
                # bitResolution (0-1)
                add_element("0-1", af_this, "bitResolution", af)
        # writtenCorpus (0-1)
        writ_this = col_this.writtenCorpus
        if writ_this != None:
            # Set the sub-element
            writ = ET.SubElement(crp, "writtenCorpus")
            # Process the validation elements
            add_element("0-n", writ_this, "characterEncoding", writ, fieldchoice=CHARACTERENCODING)
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
            add_element("1", ann_this, "format", ann, fieldchoice=ANNOTATION_FORMAT)
        # media (0-n)
        for med_this in res_this.medias.all():
            # Add the media sub-element
            med = ET.SubElement(res, "media")
            # format (0-n)
            add_element("0-n", med_this, "format", med, fieldchoice=MEDIA_FORMAT)
    # genre (0-n)
    add_element("0-n", col_this, "genre", crp, fieldchoice=GENRE_NAME)
    # provenance (0-n)
    for prov_this in col_this.provenance.all():
    # if col_this.provenance != None:
        # Set the provenance sub-element
        prov = ET.SubElement(crp, "provenance")
        # Get the provenance element
        # prov_this = col_this.provenance
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
            # country (0-1)
            add_element("0-1", geo_this, "country", geo, fieldchoice=PROVENANCE_GEOGRAPHIC_COUNTRY)
            # place (0-n)
            add_element("0-n", geo_this, "place", geo, foreign="name")
    # linguality (0-1)
    linguality_this = col_this.linguality
    if linguality_this != None:
        # Set the linguality sub-element
        ling = ET.SubElement(crp, "linguality")
        # Process the linguality elements
        add_element("0-n", linguality_this, "lingualityType", ling, fieldchoice=LINGUALITY_TYPE)
        add_element("0-n", linguality_this, "lingualityNativeness", ling, fieldchoice=LINGUALITY_NATIVENESS)
        add_element("0-n", linguality_this, "lingualityAgeGroup", ling, fieldchoice=LINGUALITY_AGEGROUP)
        add_element("0-n", linguality_this, "lingualityStatus", ling, fieldchoice=LINGUALITY_STATUS)
        add_element("0-n", linguality_this, "lingualityVariant", ling, fieldchoice=LINGUALITY_VARIANT)
        add_element("0-n", linguality_this, "multilingualityType", ling, fieldchoice=LINGUALITY_MULTI)
    # language (1-n)
    add_element("1-n", col_this, "language", crp, fieldchoice="language.name")
    # languageDisorder(0-n)
    add_element("0-n", col_this, "languageDisorder", crp, foreign="name")
    # relation (0-n)
    add_element("0-n", col_this, "relation", crp, fieldchoice=RELATION_NAME)
    # domain (0-n)
    for domain_this in col_this.domain.all():
        # Add the domains
        add_element("0-n", domain_this, "name", crp, subname="domain")
    # clarinCentre (0-1)
    add_element("0-1", col_this, "clarinCentre", crp)
    # access (0-1)
    access_this = col_this.access
    if access_this != None:
        # Set the access sub-element
        acc = ET.SubElement(crp, "access")
        # Process the access elements
        add_element("1", access_this, "name", acc)
        add_element("0-n", access_this, "availability", acc, fieldchoice=ACCESS_AVAILABILITY)
        add_element("0-n", access_this, "licenseName", acc, foreign="name")
        add_element("0-n", access_this, "licenseUrl", acc, foreign="name")
        add_element("0-1", access_this, "nonCommercialUsageOnly", acc, fieldchoice=ACCESS_NONCOMMERCIAL)
        # contact (0-n)
        for contact_this in access_this.contact.all():
            # Add this contact
            cnt = ET.SubElement(acc, "contact")
            add_element("1", contact_this, "person", cnt)
            add_element("1", contact_this, "address", cnt)
            add_element("1", contact_this, "email", cnt)
        add_element("0-n", access_this, "website", acc, foreign="name")
        add_element("0-1", access_this, "ISBN", acc)
        add_element("0-1", access_this, "ISLRN", acc)
        add_element("0-n", access_this, "medium", acc, foreign="format", fieldchoice=ACCESS_MEDIUM)
    # totalSize (0-n) -- NOTE: this is on the COLLECTION level; there also is totalsize on the RESOURCE level
    if col_this.totalSize != None:
        for size_this in col_this.totalSize.all():
            # Start adding this sub-element
            tot = ET.SubElement(res, "totalSize")
            # Add the size part
            add_element("1", size_this, "size", tot)
            # Add the sizeUnit part
            add_element("1", size_this, "sizeUnit", tot)
    # PID (0-n)
    add_element("0-n", col_this, "pid", crp, foreign="code", subname="PID")
    # version (0-1)
    add_element("0-1", col_this, "version", crp)
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
        add_element("1-n", doc_this, "language", doc, fieldchoice="language.name")
    # validation (0-1)
    val_this = col_this.validation
    if val_this != None:
        # Set the sub-element
        val = ET.SubElement(crp, "validation")
        # Process the validation elements
        add_element("0-1", val_this, "type", val, fieldchoice=VALIDATION_TYPE)
        add_element("0-n", val_this, "method", val, fieldchoice=VALIDATION_METHOD)
    # project (0-n)
    for proj_this in col_this.project.all():
        # Set the sub element
        proj = ET.SubElement(crp, "project")
        # Process the project properties
        add_element("0-1", proj_this, "title", proj)
        add_element("0-n", proj_this, "funder", proj, foreign="name")
        add_element("0-1", proj_this, "URL", proj, foreign="name")

    # There's no return value -- all has been added to [crp]

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

        # Define the top-level of the xml output
        topattributes = {'xmlns:xsi':"http://www.w3.org/2001/XMLSchema-instance",
                         'xmlns:xsd':"http://www.w3.org/2001/XMLSchema",
                         'CMDIVersion':'1.1',
                         'xmlns':"http://www.clarin.eu/cmd/"}
        top = ET.Element('CMD', topattributes)

        # Add an empty header
        ET.SubElement(top, "Header", {})
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

        # Return this string
        return xmlstr
    
    def download_to_xml(self, context):
        """Make the XML representation of ALL collections downloadable"""

        # Construct a file name based on the identifier
        # NOT NEEDED HERE? sFileName = 'collection-{}'.format(getattr(context['collection'], 'identifier'))
        # Get the XML of this collection
        sXmlStr = self.convert_to_xml(context)
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(sXmlStr, content_type='text/xml')
        response['Content-Disposition'] = 'attachment; filename="collbank_all.xml"'

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

        # Define the top-level of the xml output
        topattributes = {'xmlns:xsi':"http://www.w3.org/2001/XMLSchema-instance",
                         'xmlns:xsd':"http://www.w3.org/2001/XMLSchema",
                         'CMDIVersion':'1.1',
                         'xmlns':"http://www.clarin.eu/cmd/"}
        top = ET.Element('CMD', topattributes)

        # Add an empty header
        ET.SubElement(top, "Header", {})
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

        # Return this string
        return xmlstr

    def render_to_xml(self, context):
        """Return the XML representation in the browser"""

        # Save the to a standard location
        sXmlStr = self.convert_to_xml(context)
        sFileName = OUTPUT_XML
        sFullPath = ""
        with open(sFileName, encoding="utf-8", mode="w+") as f:
            sFullPath = f.name
            f.write(sXmlStr)
        # Show result from that location
        return HttpResponse(open(sFullPath, encoding="utf-8").read(), content_type='text/xml')

    def download_to_xml(self, context):
        """Make the XML representation of this collection downloadable"""

        # Construct a file name based on the identifier
        sFileName = 'collection-{}'.format(getattr(context['collection'], 'identifier'))
        # Get the XML of this collection
        sXmlStr = self.convert_to_xml(context)
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(sXmlStr, content_type='text/xml')
        response['Content-Disposition'] = 'attachment; filename="'+sFileName+'.xml"'

        # Return the result
        return response