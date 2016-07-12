"""
Definition of views.
"""

from django.views.generic.detail import DetailView
from django.shortcuts import get_object_or_404, render
from django.http import HttpRequest, HttpResponse
from django.template import RequestContext, loader
from datetime import datetime
from xml.dom import minidom
import xml.etree.ElementTree as ET
from collbank.collection.models import *
from collbank.settings import OUTPUT_XML, APP_PREFIX

# General help functions
def add_element(optionality, col_this, el_name, crp, **kwargs):
    """Add element [el_name] from collection [col_this] under the XML element [crp]"""

    foreign = ""
    if "foreign" in kwargs: foreign = kwargs["foreign"]
    field_choice = ""
    if "fieldchoice" in kwargs: field_choice = kwargs["fieldchoice"]
    col_this_el = getattr(col_this, el_name)
    sub_name = el_name
    if "subname" in kwargs: sub_name = kwargs["subname"]
    if optionality == "0-1" or optionality == "1":
        col_value = col_this_el
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


def overview(request):
    """Give an overview of the collections that have been entered"""

    overview_list = Collection.objects.order_by('identifier')
    template = loader.get_template('collection/overview.html')
    context = {
        'overview_list': overview_list,
        'app_prefix': APP_PREFIX,
    }
    return HttpResponse(template.render(context, request))

class CollectionDetailView(DetailView):
    """Details of a selected collection"""

    model = Collection
    export_xml = True
    context_object_name = 'collection'

    def render_to_response(self, context, **response_kwargs):
        if self.export_xml:
            return self.render_to_xml(context)
        else:
            return super(CollectionDetailView, self).render_to_response(context, **response_kwargs)


    def render_to_xml(self, context):

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
        crp = ET.SubElement(cmp, "CorpusCollection")

        # Access this particular collection
        col_this = context['collection']

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
            # type (1)
            add_element("1", res_this, "type", res, fieldchoice =RESOURCE_TYPE)
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
            # media (0-1)
            if res_this.media != None:
                # Set the media sub-element
                med = ET.SubElement(res, "media")
                # Get the media element
                med_this = res_this.media
                # format (0-n)
                add_element("0-n", med_this, "format", med, foreign="name", fieldchoice=MEDIA_FORMAT)
            # totalSize (0-n)
            for size_this in res_this.totalSize.all():
                # Start adding this sub-element
                tot = ET.SubElement(res, "totalSize")
                # Add the size part
                add_element("1", size_this, "size", tot)
                # Add the sizeUnit part
                add_element("1", size_this, "sizeUnit", tot)
        # genre (0-n)
        add_element("0-n", col_this, "genre", crp, foreign="name", fieldchoice=GENRE_NAME)
        # provenance (0-1)
        if col_this.provenance != None:
            # Set the provenance sub-element
            prov = ET.SubElement(crp, "provenance")
            # Get the provenance element
            prov_this = col_this.provenance
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
            add_element("0-n", linguality_this, "lingualityType", ling, foreign="name", fieldchoice=LINGUALITY_TYPE)
            add_element("0-n", linguality_this, "lingualityNativeness", ling, foreign="name", fieldchoice=LINGUALITY_NATIVENESS)
            add_element("0-n", linguality_this, "lingualityAgeGroup", ling, foreign="name", fieldchoice=LINGUALITY_AGEGROUP)
            add_element("0-n", linguality_this, "lingualityStatus", ling, foreign="name", fieldchoice=LINGUALITY_STATUS)
            add_element("0-n", linguality_this, "lingualityVariant", ling, foreign="name", fieldchoice=LINGUALITY_VARIANT)
            add_element("0-n", linguality_this, "multilingualityType", ling, foreign="name", fieldchoice=LINGUALITY_MULTI)
        # language (1-n)
        add_element("1-n", col_this, "language", crp, foreign="name", fieldchoice="language.name")
        # languageDisorder(0-n)
        add_element("0-n", col_this, "languageDisorder", crp, foreign="name")
        # relation (0-n)
        add_element("0-n", col_this, "relation", crp, foreign="name", fieldchoice=RELATION_NAME)
        # domain (0-n)
        for domain_this in col_this.domain.all():
            # Add the domains
            add_element("0-n", domain_this, "name", crp, foreign="name", subname="domain")
        # clarinCentre (0-1)
        add_element("0-1", col_this, "clarinCentre", crp)
        # access (0-1)
        access_this = col_this.access
        if access_this != None:
            # Set the access sub-element
            acc = ET.SubElement(crp, "access")
            # Process the access elements
            add_element("1", access_this, "name", acc)
            add_element("0-n", access_this, "availability", acc, foreign="name", fieldchoice=ACCESS_AVAILABILITY)
            add_element("0-n", access_this, "licenseName", acc, foreign="name")
            add_element("0-n", access_this, "licenseUrl", acc, foreign="name")
            add_element("0-1", access_this, "nonCommercialUsageOnly", acc, foreign="name", fieldchoice=ACCESS_NONCOMMERCIAL)
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
            add_element("1-n", doc_this, "language", doc, foreign="name", fieldchoice="language.name")
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
            add_element("0-1", proj_this, "URL", proj, foreign="name")
        # writtenCorpus (0-1)
        writ_this = col_this.writtenCorpus
        if writ_this != None:
            # Set the sub-element
            writ = ET.SubElement(crp, "writtenCorpus")
            # Process the validation elements
            add_element("0-n", writ_this, "characterEncoding", writ, foreign="name", fieldchoice=CHARACTERENCODING)
        # speechCorpus (0-1)
        speech_this = col_this.speechCorpus
        if speech_this != None:
            # Set the sub-element
            speech = ET.SubElement(crp, "speechCorpus")
            # Process the elements of the speech corpus
            add_element("0-n", speech_this, "recordingEnvironment", speech, foreign="name", fieldchoice=SPEECHCORPUS_RECORDINGENVIRONMENT)
            add_element("0-n", speech_this, "channel", speech, foreign="name", fieldchoice=SPEECHCORPUS_CHANNEL)
            add_element("0-n", speech_this, "conversationalType", speech, foreign="name", fieldchoice=SPEECHCORPUS_CONVERSATIONALTYPE)
            add_element("0-n", speech_this, "recordingConditions", speech, foreign="name")
            add_element("0-1", speech_this, "durationOfEffectiveSpeech", speech)
            add_element("0-1", speech_this, "durationOfFullDatabase", speech)
            add_element("0-1", speech_this, "numberOfSpeakers", speech)
            add_element("0-1", speech_this, "speakerDemographics", speech)
            add_element("0-n", speech_this, "socialContext", speech, foreign="name", fieldchoice=SPEECHCORPUS_SOCIALCONTEXT)
            add_element("0-n", speech_this, "planningType", speech, foreign="name", fieldchoice=SPEECHCORPUS_PLANNINGTYPE)
            add_element("0-n", speech_this, "interactivity", speech, foreign="name", fieldchoice=SPEECHCORPUS_INTERACTIVITY)
            add_element("0-n", speech_this, "involvement", speech, foreign="name", fieldchoice=SPEECHCORPUS_INVOLVEMENT)
            add_element("0-n", speech_this, "audience", speech, foreign="name", fieldchoice=SPEECHCORPUS_AUDIENCE)


        # Export this object to XML
        # xmlstr = minidom.parseString(ET.tostring(top,'utf-8')).toprettyxml(indent="  ")
        xmlstr = minidom.parseString(ET.tostring(top,encoding='utf-8')).toprettyxml(indent="  ")
        sFullPath = ""
        with open(OUTPUT_XML, encoding="utf-8", mode="w+") as f:
            sFullPath = f.name
            f.write(xmlstr)


        # TODO: make the file available for download and provide a link to it
        return HttpResponse(open(sFullPath, encoding="utf-8").read(), content_type='text/xml')
