"""Models for the collection records.

A collection is a bundle of resources belonging together.
The collection has a number of characteristics.
Each resource in the collection is characterised by its own annotations.

"""
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
# from collbank.settings import COUNTRY_CODES, LANGUAGE_CODE_LIST

import copy  # (1) use python copy
import sys

MAX_IDENTIFIER_LEN = 10

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

#settings_choices = [
#    {'name': "language.name",
#     'list': LANGUAGE_CODE_LIST,
#     'colCode': 0,
#     'colText': 2 },
#    {'name': "country.name",
#     'list': COUNTRY_CODES,
#     'colCode': 0,
#     'colText': 1 }
#    ]


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


#def build_choice_settings(field):
#    """Create a list of choice-tuples using settings_choices."""

#    choice_list = [];
#    unique_list = [];   # Check for uniqueness

#    try:
#        # Try find [field] in [settings_choices]
#        idx = next((obj for obj in settings_choices if object.name == field), -1)
#        # Are we positive?
#        if idx >=0:
#            # Get all elements
#            lstSettings = settings_choices[idx]['list']
#            colCode = settings_choices[idx]['colCode']
#            colText = settings_choices[idx]['colText']
#            # More validation
#            if lstSettings != None:
#                # Copy all elements
#                for choice in lstSettings:
#                    # Copy this choice
#                    choice_list.append(lstSettings[colCode], lstSettings[colText])
#                # Sort the result
#                choice_list = sorted(choice_list,key=lambda x: x[1]);
#        else:
#            # Take a default list
#            choice_list = [('0','-'),('1','N/A')]

#    except:
#        print("Unexpected error:", sys.exc_info()[0])
#        choice_list = [('0','-'),('1','N/A')];

#    # Signbank returns: [('0','-'),('1','N/A')] + choice_list
#    # We do not use defaults
#    return choice_list;

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

def m2m_combi(items):
    if items == None:
        sBack = ''
    else:
        qs = items.all()
        sBack = '-'.join([str(thing) for thing in qs])
    return sBack

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
        newItem = get_instance_copy(item)
        # Possibly copy more m2m
        if lst_m2m != None:
            for deeper in lst_m2m:
                copy_m2m(item, newItem, deeper)
        getattr(inst_dst, field).add(newItem)

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

#def one_time_startup():
#    """Execute things that only need to be done once on startup"""
#    iChanges = 0

#    try:
#        # Make a list of all DCtype values
#        arTypeChoices = Resource._meta.get_field('type').choices
#        arDCtypeChoices = Resource._meta.get_field('DCtype').choices
#        # Walk all existing 'Resource' objects
#        for resThis in Resource.objects.all():
#            # Check if the Type needs updating
#            if resThis.DCtype == '' or resThis.DCtype == '0':
#                # The type needs updating
#                sType = get_tuple_value(arTypeChoices, resThis.type)
#                # (1) Get the correct value
#                arType = sType.partition(':')
#                if len(arType) == 1:
#                    resThis.DCtype = get_tuple_index(arTypeChoices, sType)
#                    resThis.subtype = ''
#                else:
#                    resThis.DCtype = get_tuple_index(arDCtypeChoices, arType[0])
#                    resThis.subtype = get_tuple_index(arTypeChoices, sType)
#                iChanges += 1
#                resThis.save()

#        if iChanges > 0:
#            # Note the changes
#            print('OneTimeStartup Changes: ' + str(iChanges) + '\n',file=sys.stderr)
#    except:
#        print("OneTimeStartup Unexpected error:", sys.exc_info()[0],file=sys.stderr)

  

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


class Title(models.Model):
    """Title of this collection"""

    # [1; f]
    name = models.TextField("Title used for the collection as a whole", help_text=get_help('title'))
    # [1]     Each collection can have [1-n] titles
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, related_name="collection12m_title")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        return "[{}] {}".format(idt,self.name[:50])

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Return the new copy
        return new_copy


class Owner(models.Model):
    """The legal owner"""

    # [1; f]
    name = models.TextField("One of the collection or resource owners", help_text=get_help('owner'))
    # [1]     Each collection can have [0-n] owvers
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, related_name="collection12m_owner")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        return "[{}] {}".format(idt,self.name[:50])


class Media(models.Model):
    """Medium on which this resource exists"""

    class Meta:
        verbose_name_plural = "Media's"

    # format (0-n; c)
    # format = models.ManyToManyField("MediaFormat", blank=True, related_name="mediam2m_mediaformat")
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="media_items")

    def __str__(self):
        sFormats = m2m_combi(self.mediaformat12m_media)
        # return m2m_combi(self.format)
        return sFormats


class MediaFormat(models.Model):
    """Format of a medium"""

    name = models.CharField("Format of a medium", choices=build_choice_list(MEDIA_FORMAT), max_length=5, help_text=get_help(MEDIA_FORMAT), default='0')
    # [1]     Each [Media] object can have [0-n] MediaFormat items
    media = models.ForeignKey(Media, blank=False, null=False, default=1, related_name="mediaformat12m_media")

    def __str__(self):
        return choice_english(MEDIA_FORMAT, self.name)


class AnnotationFormat(models.Model):
    """Format of an annotation"""

    name = models.CharField("Annotation format", choices=build_choice_list(ANNOTATION_FORMAT), max_length=5, help_text=get_help(ANNOTATION_FORMAT), default='0')

    def __str__(self):
        return choice_english(ANNOTATION_FORMAT, self.name)


class Annotation(models.Model):
    """Description of one annotation layer in a resource"""

    type = models.CharField("Kind of annotation", choices=build_choice_list(ANNOTATION_TYPE), max_length=5, help_text=get_help(ANNOTATION_TYPE), default='0')
    mode = models.CharField("Annotation mode", choices=build_choice_list(ANNOTATION_MODE), max_length=5, help_text=get_help(ANNOTATION_MODE), default='0')
    # The [format] field was used initially, but is now overridden by the [formatAnn] field
    format = models.CharField("Annotation format", choices=build_choice_list(ANNOTATION_FORMAT), max_length=5, help_text=get_help(ANNOTATION_FORMAT), default='0')
    # The [formatAnn] field is the m2m field that should now be used
    formatAnn = models.ManyToManyField(AnnotationFormat)
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="annotations")

    def __str__(self):
        if self.resource.collection_id > 0:
            idt = self.resource.collection.identifier
        else:
            idt = "EMPTY"
        return "[{}] {}: {}, {}".format(
            idt,
            choice_english(ANNOTATION_TYPE, self.type), 
            choice_english(ANNOTATION_MODE,self.mode), 
            m2m_combi(self.formatAnn))

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Copy the m2m field
        copy_m2m(self, new_copy, "formatAnn")
        # Return the new copy
        return new_copy


class TotalSize(models.Model):
    """Total size of the resource"""

    # size = models.IntegerField("Size of the collection", default=0)
    size = models.CharField("Size of the collection", default="unknown", max_length=80)
    sizeUnit = models.CharField("Units", help_text=get_help(SIZEUNIT), max_length=50, default='MB')
    # [1]     Each resource can have [0-n] total-sizes
    resource = models.ForeignKey("Resource", blank=False, null=False, default=1, related_name="totalsize12m_resource")

    def __str__(self):
        if self.resource.collection_id >0:
            idt = self.resource.collection.identifier
        else:
            idt = "EMPTY"
        return "[{}] {} {}".format(idt,self.size,self.sizeUnit)


class TotalCollectionSize(models.Model):
    """Total size of the collection"""

    # [1]
    size = models.CharField("Size of the collection", default="unknown", max_length=80)
    # [1]
    sizeUnit = models.CharField("Units", help_text=get_help(SIZEUNIT), max_length=50, default='MB')
    # [1]     Each collection can have [0-n] total-sizes
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, related_name="collection12m_totalsize")

    def __str__(self):
        return "[{}] {} {}".format(self.collection.identifier,self.size,self.sizeUnit)



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


class City(models.Model):
    """Name of a city"""

    class Meta:
        verbose_name_plural = "Cities"

    name = models.CharField("Place (city)", max_length=80, help_text=get_help(PROVENANCE_GEOGRAPHIC_PLACE))
    # [1]     Each Provenance can have [0-n] geographic provenances
    geographicProvenance = models.ForeignKey("GeographicProvenance", blank=False, null=False, default=-1, related_name="cities")

    def __str__(self):
        return self.name



class GeographicProvenance(models.Model):
    """Geographic coverage of the collection"""

    # == country (0-1;c) (name+ISO-3166 code)
    country = models.CharField("Country included in this geographic coverage", choices=build_choice_list(PROVENANCE_GEOGRAPHIC_COUNTRY), max_length=5, help_text=get_help(PROVENANCE_GEOGRAPHIC_COUNTRY), default='0')
    # == place (0-n;f)
    # place = models.ManyToManyField(City, blank=True, related_name="place_geoprovenances")
    # [1]     Each Provenance can have [0-n] geographic provenances
    provenance = models.ForeignKey("Provenance", blank=False, null=False, default=-1, related_name="g_provenances")

    def __str__(self):
        cnt = choice_english(PROVENANCE_GEOGRAPHIC_COUNTRY, self.country)
        cts = m2m_combi(self.cities)
        return "{}: {}".format(cnt, cts)


class Provenance(models.Model):
    """Temporal and/or geographic provenance of the collection"""

    # temporalProvenance (0-1) 
    temporalProvenance = models.ForeignKey(TemporalProvenance, blank=True, null=True)
    # geographicProvenance (0-n) 
    # geographicProvenance = models.ManyToManyField(GeographicProvenance, blank=True, related_name="geoprov_provenances")
    # [1]     Each collection can have [0-n] provenances
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, related_name="collection12m_provenance")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        tmp = self.temporalProvenance
        geo = m2m_combi(self.g_provenances)
        return "[{}] temp:{}, geo:{}".format(idt, tmp, geo)


class Genre(models.Model):
    """Genre of collection as a whole"""

    # (0-n; c)
    name = models.CharField("Collection genre", choices=build_choice_list(GENRE_NAME), max_length=5, help_text=get_help(GENRE_NAME), default='0')
    # [1]     Each collection can have [1-n] genres
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, related_name="collection12m_genre")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        return "[{}] {}".format(idt,choice_english(GENRE_NAME, self.name))


class LingualityType(models.Model):
    """Type of linguality"""

    name = models.CharField("Type of linguality", choices=build_choice_list(LINGUALITY_TYPE), max_length=5, help_text=get_help(LINGUALITY_TYPE), default='0')
    # [1]     Each Linguality instance can have [0-n] linguality types
    linguality = models.ForeignKey("Linguality", blank=False, null=False, default=1, related_name="linguality_types")

    def __str__(self):
        return choice_english(LINGUALITY_TYPE, self.name)


class LingualityNativeness(models.Model):
    """Nativeness type of linguality"""

    class Meta:
        verbose_name_plural = "Linguality Nativeness Types"

    name = models.CharField("Nativeness type of linguality", choices=build_choice_list(LINGUALITY_NATIVENESS), max_length=5, help_text=get_help(LINGUALITY_NATIVENESS), default='0')
    # [1]     Each Linguality instance can have [0-n] linguality nativenesses
    linguality = models.ForeignKey("Linguality", blank=False, null=False, default=1, related_name="linguality_nativenesses")

    def __str__(self):
        return choice_english(LINGUALITY_NATIVENESS, self.name)


class LingualityAgeGroup(models.Model):
    """Age group of linguality"""

    name = models.CharField("Age group of linguality", choices=build_choice_list(LINGUALITY_AGEGROUP), max_length=5, help_text=get_help(LINGUALITY_AGEGROUP), default='0')
    # [1]     Each Linguality instance can have [0-n] linguality age groups
    linguality = models.ForeignKey("Linguality", blank=False, null=False, default=1, related_name="linguality_agegroups")

    def __str__(self):
        return choice_english(LINGUALITY_AGEGROUP, self.name)


class LingualityStatus(models.Model):
    """Status of linguality"""

    class Meta:
        verbose_name_plural = "Linguality statuses"

    name = models.CharField("Status of linguality", choices=build_choice_list(LINGUALITY_STATUS), max_length=5, help_text=get_help(LINGUALITY_STATUS), default='0')
    # [1]     Each Linguality instance can have [0-n] linguality statuses
    linguality = models.ForeignKey("Linguality", blank=False, null=False, default=1, related_name="linguality_statuses")

    def __str__(self):
        return choice_english(LINGUALITY_STATUS, self.name)


class LingualityVariant(models.Model):
    """Variant of linguality"""

    name = models.CharField("Variant of linguality", choices=build_choice_list(LINGUALITY_VARIANT), max_length=5, help_text=get_help(LINGUALITY_VARIANT), default='0')
    # [1]     Each Linguality instance can have [0-n] linguality variants
    linguality = models.ForeignKey("Linguality", blank=False, null=False, default=1, related_name="linguality_variants")

    def __str__(self):
        return choice_english(LINGUALITY_VARIANT, self.name)


class MultilingualityType(models.Model):
    """Type of multi-linguality"""

    name = models.CharField("Type of multi-linguality", choices=build_choice_list(LINGUALITY_MULTI), max_length=5, help_text=get_help(LINGUALITY_MULTI), default='0')
    # [1]     Each Linguality instance can have [0-n] multilinguality types
    linguality = models.ForeignKey("Linguality", blank=False, null=False, default=1, related_name="multilinguality_types")

    def __str__(self):
        return choice_english(LINGUALITY_MULTI, self.name)


class Linguality(models.Model):
    """Linguality information on this collection"""

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


class Language(models.Model):
    """Language that is used in this collection"""

    name = models.CharField("Language in collection", choices=build_choice_list("language.name"), max_length=5, help_text=get_help("language.name"), default='0')

    def __str__(self):
        idt = m2m_identifier(self.collection_set)
        # idt = m2m_identifier(self.collectionm2m_resource)
        if idt == "" or idt == "-":
            sBack = "[DOC] " + choice_english("language.name", self.name)
        else:
            sBack = "[{}] {}".format(idt,choice_english("language.name", self.name))
        return sBack


class DocumentationLanguage(Language):

    # [1]     Each documentation object can have [0-n] languages associated with it
    documentationParent = models.ForeignKey("Documentation", blank=False, null=False, default=1, related_name="doc_languages")
    
    def __str__(self):
        arColl = self.documentationParent.collection_set.all()
        # arColl = Collection.objects.filter(documentation=self.documentationParent)
        idt = arColl[0].identifier
        # idt = self.documentationParent.collection.identifier
        sBack = "[{}] {}".format(idt,choice_english("language.name", self.name))
        return sBack


class CollectionLanguage(Language):

    # [1]     Each collection can have [0-n] languages associated with it
    collectionParent = models.ForeignKey("Collection", blank=False, null=False, default=1, related_name="coll_languages")

    def __str__(self):
        idt = self.collectionParent.identifier
        sBack = "[{}] {}".format(idt,choice_english("language.name", self.name))
        return sBack


class LanguageDisorder(models.Model):
    """Language that is used in this collection"""

    # [1]
    name = models.CharField("Language disorder", max_length=50, help_text=get_help("languagedisorder.name"), default='unknown')
    # [1]     Each collection can have [0-n] language disorders
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, related_name="collection12m_languagedisorder")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        sName = self.name
        return "[{}] {}".format(idt, sName)


class Relation(models.Model):
    """Language that is used in this collection"""

    # [1]
    name = models.CharField("Relation with something else", max_length=80, help_text=get_help(RELATION_NAME ), default='-')
    # [1]     Each collection can have [0-n] relations
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, related_name="collection12m_relation")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        return "[{}] {}".format(idt,self.name)


class Domain(models.Model):
    """Domain"""

    # Description of this domain (to be copied from [DomainDescription]
    name = models.TextField("Domain", help_text=get_help(DOMAIN_NAME), default='0')
    # [1]     Each collection can have [0-n] domains
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, related_name="collection12m_domain")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        if self.collection_id < 0:
            return "Empty"
        else:
            idt = self.collection.identifier
            sName = self.name
            return "[{}] {}".format(idt,sName)


class AccessAvailability(models.Model):
    """Access availability"""

    class Meta:
        verbose_name_plural = "Access availabilities"

    name = models.CharField("Access availability", choices=build_choice_list(ACCESS_AVAILABILITY), max_length=5, help_text=get_help(ACCESS_AVAILABILITY), default='0')
    # [1]     Each access instance can have [0-n] availabilities
    access = models.ForeignKey("Access", blank=False, null=False, default=-1, related_name="acc_availabilities")

    def __str__(self):
        return choice_english(ACCESS_AVAILABILITY, self.name)


class LicenseName(models.Model):
    """Name of the license"""

    name = models.TextField("Name of the license", help_text=get_help('access.licenseName'))
    # [1]     Each access instance can have [0-n] licence Names
    access = models.ForeignKey("Access", blank=False, null=False, default=-1, related_name="acc_licnames")

    def __str__(self):
        return self.name[:50]


class LicenseUrl(models.Model):
    """URL of the license"""

    name = models.URLField("URL of the license", help_text=get_help('access.licenseURL'))
    # [1]     Each access instance can have [0-n] license URLs
    access = models.ForeignKey("Access", blank=False, null=False, default=-1, related_name="acc_licurls")

    def __str__(self):
        return self.name


class NonCommercialUsageOnly(models.Model):
    """Whether access is restricted to non-commerical usage"""

    class Meta:
        verbose_name_plural = "Non-commercial usage only types"

    name = models.CharField("Non-commercial usage only access", choices=build_choice_list(ACCESS_NONCOMMERCIAL ), max_length=5, help_text=get_help(ACCESS_NONCOMMERCIAL ), default='0')

    def __str__(self):
        return choice_english(ACCESS_NONCOMMERCIAL, self.name)


class AccessContact(models.Model):
    """Contact details for access"""

    person = models.TextField("Access: person to contact", help_text=get_help('access.contact.person'))
    address = models.TextField("Access: address of contact", help_text=get_help('access.contact.address'))
    email = models.EmailField("Access: email of contact", help_text=get_help('access.contact.email'))
    # [1]     Each access instance can have [0-n] contacts
    access = models.ForeignKey("Access", blank=False, null=False, default=-1, related_name="acc_contacts")

    def __str__(self):
        return "{}: {}, ({})".format(
            self.person, self.address[:30], self.email)


class AccessWebsite(models.Model):
    """Website to access the collection"""

    name = models.URLField("Website to access the collection", help_text=get_help('access.website'))
    # [1]     Each access instance can have [0-n] websites
    access = models.ForeignKey("Access", blank=False, null=False, default=-1, related_name="acc_websites")

    def __str__(self):
        return self.name


class AccessMedium(models.Model):
    """Medium used to access a resource of the collection"""

    format = models.CharField("Resource medium", choices=build_choice_list(ACCESS_MEDIUM ), max_length=5, help_text=get_help(ACCESS_MEDIUM ), default='0')
    # [1]     Each access instance can have [0-n] mediums
    access = models.ForeignKey("Access", blank=False, null=False, default=-1, related_name="acc_mediums")

    def __str__(self):
        return choice_english(ACCESS_MEDIUM, self.format)


class Access(models.Model):
    """Access to the resources"""

    class Meta:
        verbose_name_plural = "Accesses"

    name = models.TextField("Name of this access type", default='-')
    # availability (0-n;c ) 
    # availability = models.ManyToManyField(AccessAvailability, blank=True, related_name = "access_m2m_avail")
    # licenseName (0-n; f)
    # licenseName = models.ManyToManyField(LicenseName, blank=True, related_name = "access_m2m_licname")
    # licenseURL (0-n;f)
    # licenseUrl = models.ManyToManyField(LicenseUrl, blank=True, related_name = "access_m2m_licurl")
    # nonCommercialUsageOnly (0-1;c yes; no)
    nonCommercialUsageOnly = models.ForeignKey(NonCommercialUsageOnly, blank=True, null=True)
    # contact (0-n;f)
    # contact = models.ManyToManyField(AccessContact, blank=True, related_name = "access_m2m_contact")
    # website (0-n)
    # website = models.ManyToManyField(AccessWebsite, blank=True, related_name = "access_m2m_website")
    # ISBN (0-1;f)
    ISBN = models.TextField("ISBN of collection", help_text=get_help('access.ISBN'), blank=True)
    # ISLRN (0-1;f)
    ISLRN = models.TextField("ISLRN of collection", help_text=get_help('access.ISLRN'), blank=True)
    # medium (0-n; c)
    # medium = models.ManyToManyField(AccessMedium, blank=True, related_name = "access_m2m_medium")

    def __str__(self):
        sName = self.name
        return sName[:50]



class PID(models.Model):
    """Persistent identifier"""

    class Meta:
        verbose_name_plural = "PIDs"

    # [1]
    code = models.TextField("Persistent identifier of the collection", help_text=get_help('PID'))
    # [1]     Each collection can have [0-n] PIDs
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, related_name="collection12m_pid")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        return "[{}] {}".format(idt,self.code[:50])


class Organization(models.Model):
    """Name of organization"""

    name = models.TextField("Name of organization", help_text=get_help('resourceCreator.organization'))
    # [1]     Each resourceCreator can have [0-n] organizations
    resourceCreator = models.ForeignKey("ResourceCreator", blank=False, null=False, default=-1, related_name="organizations")

    def __str__(self):
        return self.name[:50]


class Person(models.Model):
    """Name of person"""

    name = models.TextField("Name of person", help_text=get_help('resourceCreator.person'))
    # [1]     Each resourceCreator can have [0-n] persons
    resourceCreator = models.ForeignKey("ResourceCreator", blank=False, null=False, default=-1, related_name="persons")

    def __str__(self):
        return self.name[:50]


class ResourceCreator(models.Model):
    """Creator of this resource"""

    # [1]
    organization = models.ManyToManyField(Organization, blank=False, related_name="resourcecreatorm2m_organization")
    # [1]
    person = models.ManyToManyField(Person, blank=False, related_name="resourcecreatorm2m_person")
    # [1]     Each collection can have [0-n] resource creators
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, related_name="collection12m_resourcecreator")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        orgs = m2m_combi(self.organizations)
        pers = m2m_combi(self.persons)
        return "[{}] o:{}|p:{}".format(idt,orgs,pers)


class DocumentationType(models.Model):
    """Kind of documentation"""

    format = models.CharField("Kind of documentation", choices=build_choice_list(DOCUMENTATION_TYPE ), max_length=5, help_text=get_help(DOCUMENTATION_TYPE ), default='0')
    # [1]
    documentation = models.ForeignKey("Documentation", blank=False, null=False, default=1, related_name="doc_types")

    def __str__(self):
        return choice_english(DOCUMENTATION_TYPE, self.format)


class DocumentationFile(models.Model):
    """File name for documentation"""

    name = models.TextField("File name for documentation", help_text=get_help('documentation.file'))
    # [1]
    documentation = models.ForeignKey("Documentation", blank=False, null=False, default=1, related_name="doc_files")

    def __str__(self):
        return self.name[:50]


class DocumentationUrl(models.Model):
    """URL of documentation"""

    name = models.URLField("URL of documentation", help_text=get_help('documentation.url'))
    # [1]
    documentation = models.ForeignKey("Documentation", blank=False, null=False, default=1, related_name="doc_urls")

    def __str__(self):
        return self.name


class Documentation(models.Model):
    """Creator of this resource"""

    # Many-to-one relations:
    #   DocumentationType (0-n; c)
    #   DocumentationFile (0-n; f)
    #   DocumentationUrl (0-n; f)
    #   DocumentationLanguage (1-n; c)

    def __str__(self):
        fld_tp = m2m_combi(self.doc_types)
        fld_fl = m2m_combi(self.doc_files)
        return "t:{}|f:{}".format(fld_tp, fld_fl)


class ValidationType(models.Model):
    """Validation type"""

    name = models.CharField("Validation type", choices=build_choice_list(VALIDATION_TYPE), max_length=5, help_text=get_help(VALIDATION_TYPE), default='0')

    def __str__(self):
        return choice_english(VALIDATION_TYPE, self.name)


class ValidationMethod(models.Model):
    """Validation method"""

    name = models.CharField("Validation method", choices=build_choice_list(VALIDATION_METHOD), max_length=5, help_text=get_help(VALIDATION_METHOD), default='0')
    # [1]
    validation = models.ForeignKey("Validation", blank=False, null=False, default=1, related_name="validationmethods")

    def __str__(self):
        return choice_english(VALIDATION_METHOD, self.name)


class Validation(models.Model):
    """Validation"""

    # type (0-1; c)
    type = models.ForeignKey(ValidationType, blank=True, null=True)
    # Many-to-one relations:
    # ValidationMethod (0-n; c)

    def __str__(self):
        return "{}:{}".format(
            self.type,
            m2m_combi(self.validationmethods))


class ProjectFunder(models.Model):
    """Funder of project"""

    name = models.TextField("Funder of project", help_text=get_help('project.funder'))
    # [1]
    project = models.ForeignKey("Project", blank=False, null=False, default=1, related_name="funders")

    def __str__(self):
        return self.name[:50]


class ProjectUrl(models.Model):
    """URL of project"""

    name = models.URLField("URL of project", help_text=get_help('project.url'))

    def __str__(self):
        return self.name


class Project(models.Model):
    """Project supporting a resource from the collection"""

    # title (0-1; f)
    title = models.TextField("Project title", help_text=get_help('project.title'))
    # funder (0-n; f)
    funder = models.ManyToManyField(ProjectFunder, blank=True, related_name="projectm2m_funder")
    # url (0-1; f)
    URL = models.ForeignKey(ProjectUrl, blank=True, null=True)
    # [1]     Each collection can have [0-n] projects
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, related_name="collection12m_project")

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = self.collection.identifier
        sName = self.title
        if sName == "": sName = self.URL
        return "[{}] {}".format(idt,sName[:50])


class CharacterEncoding(models.Model):
    """Type of character-encoding"""

    name = models.CharField("Character encoding", choices=build_choice_list(CHARACTERENCODING), max_length=5, help_text=get_help(CHARACTERENCODING), default='0')
    # [1]     Each written corpus can have [0-n] character encodings
    writtenCorpus = models.ForeignKey("WrittenCorpus", blank=False, null=False, default=1, related_name="charenc_writtencorpora")

    def __str__(self):
        return choice_english(CHARACTERENCODING, self.name)


class WrittenCorpus(models.Model):
    """Written Corpus"""

    class Meta:
        verbose_name_plural = "Written corpora"

    # numberOfAuthors:    (0-1;f)
    numberOfAuthors = models.CharField("Number of authors", blank=True, help_text=get_help(WRITTENCORPUS_AUTHORNUMBER), max_length=20, default="unknown")
    # authorDemographics: (0-1;f)
    authorDemographics = models.TextField("Author demographics", blank=True, help_text=get_help(WRITTENCORPUS_AUTHORDEMOGRAPHICS), default='-')

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = "TODO"
        sEnc = m2m_combi(self.charenc_writtencorpora) # m2m_combi(self.characterEncoding)
        return "[{}]: {}".format(idt, sEnc)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Copy M2M relationship: conversationalType
        # OLD: copy_m2m(self, new_copy, 'characterEncoding')
        # TODO: check this...
        copy_m2m(self, new_copy, 'charenc_writtencorpora')
        # Return the new copy
        return new_copy



class RecordingEnvironment(models.Model):
    """Environment for the recording"""

    # [1]
    name = models.CharField("Environment for the recording", choices=build_choice_list(SPEECHCORPUS_RECORDINGENVIRONMENT), max_length=5, help_text=get_help(SPEECHCORPUS_RECORDINGENVIRONMENT), default='0')
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="recordingenvironments")

    def __str__(self):
        return choice_english(SPEECHCORPUS_RECORDINGENVIRONMENT, self.name)


class Channel(models.Model):
    """Channel for the speech corpus"""

    name = models.CharField("Channel for the speech corpus", choices=build_choice_list(SPEECHCORPUS_CHANNEL), max_length=5, help_text=get_help(SPEECHCORPUS_CHANNEL), default='0')
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="channels")

    def __str__(self):
        return choice_english(SPEECHCORPUS_CHANNEL, self.name)


class ConversationalType(models.Model):
    """Type of conversation"""

    name = models.CharField("Type of conversation", choices=build_choice_list(SPEECHCORPUS_CONVERSATIONALTYPE), max_length=5, help_text=get_help(SPEECHCORPUS_CONVERSATIONALTYPE), default='0')
    # [1]     Each speech corpus can have [0-n] conversational types
    speechCorpus = models.ForeignKey("SpeechCorpus", blank=False, null=False, default=1, related_name="conversationaltypes")

    def __str__(self):
        return choice_english(SPEECHCORPUS_CONVERSATIONALTYPE, self.name)


class RecordingCondition(models.Model):
    """Recording condition"""

    name = models.TextField("Recording condition", help_text=get_help('speechcorpus.recordingConditions'))
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="recordingconditions")

    def __str__(self):
        # Max 80 characters
        return self.name[:80]


class SocialContext(models.Model):
    """Social context"""

    name = models.CharField("Social context", choices=build_choice_list(SPEECHCORPUS_SOCIALCONTEXT), max_length=5, help_text=get_help(SPEECHCORPUS_SOCIALCONTEXT), default='0')
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="socialcontexts")

    def __str__(self):
        return choice_english(SPEECHCORPUS_SOCIALCONTEXT, self.name)


class PlanningType(models.Model):
    """Type of planning"""

    name = models.CharField("Type of planning", choices=build_choice_list(SPEECHCORPUS_PLANNINGTYPE), max_length=5, help_text=get_help(SPEECHCORPUS_PLANNINGTYPE), default='0')
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="planningtypes")

    def __str__(self):
        return choice_english(SPEECHCORPUS_PLANNINGTYPE, self.name)


class Interactivity(models.Model):
    """Interactivity"""

    class Meta:
        verbose_name_plural = "Interactivities"

    name = models.CharField("Interactivity", choices=build_choice_list(SPEECHCORPUS_INTERACTIVITY), max_length=5, help_text=get_help(SPEECHCORPUS_INTERACTIVITY), default='0')
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="interactivities")

    def __str__(self):
        return choice_english(SPEECHCORPUS_INTERACTIVITY, self.name)


class Involvement(models.Model):
    """Type of involvement"""

    name = models.CharField("Type of involvement", choices=build_choice_list(SPEECHCORPUS_INVOLVEMENT), max_length=5, help_text=get_help(SPEECHCORPUS_INVOLVEMENT), default='0')
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="involvements")

    def __str__(self):
        return choice_english(SPEECHCORPUS_INVOLVEMENT, self.name)


class Audience(models.Model):
    """Audience"""

    name = models.CharField("Audience", choices=build_choice_list(SPEECHCORPUS_AUDIENCE), max_length=5, help_text=get_help(SPEECHCORPUS_AUDIENCE), default='0')
    # [1]
    resource = models.ForeignKey("Resource", blank=False, null=False, default=-1 , on_delete=models.CASCADE, related_name="audiences")

    def __str__(self):
        return choice_english(SPEECHCORPUS_AUDIENCE, self.name)


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
    speechCorpus = models.ForeignKey("SpeechCorpus", blank=False, null=False, default=1, related_name="audioformats")

    def __str__(self):
        sc = self.speechCoding
        sf = self.samplingFrequency
        cmp = self.compression
        br = self.bitResolution
        sMsg = "sc:{}, sf:{}, cmp:{}, br:{}".format(sc, sf, cmp, br)
        return sMsg


class SpeechCorpus(models.Model):
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

    def __str__(self):
        # idt = m2m_identifier(self.collection_set)
        idt = "MOVED"
        sCnvType = m2m_combi(self.conversationaltypes)
        return "[{}] cnv:{}".format(idt, sCnvType)

    def get_copy(self):
        # Make a clean copy
        new_copy = get_instance_copy(self)
        # Copy M2M relationship: conversationalType
        copy_m2m(self, new_copy, 'conversationalType')
        # Copy M2M relationship: audioFormat
        copy_m2m(self, new_copy, 'audioFormat')
        # Return the new copy
        return new_copy



class Resource(models.Model):
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
    collection = models.ForeignKey("Collection", blank=False, null=False, default=1, related_name="collection12m_resource")

    # == writtenCorpus (0-1)
    writtenCorpus = models.ForeignKey(WrittenCorpus, blank=True, null=True)
    # speechCorpus (0-1)
    speechCorpus = models.ForeignKey(SpeechCorpus, blank=True, null=True)

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
        # Copy the m2m fields
        copy_m2m(self, new_copy, "modality")
        copy_m2m(self, new_copy, "annotation")
        copy_m2m(self, new_copy, "totalSize")
        # Copying Medias requires special attention...
        copy_m2m(self, new_copy, "medias", ["format"])
        # Check and copy FK fields
        if self.writtenCorpus != None:
            new_copy.writtenCorpus = self.writtenCorpus.get_copy()
        if self.speechCorpus != None:
            new_copy.speechCorpus = self.speechCorpus.get_copy()
        # Return the new copy
        return new_copy



class Collection(models.Model):
    """Characteristics of the collection as a whole"""

    # INTERNAL FIELD: identifier (1)
    identifier = models.CharField("Unique short collection identifier (10 characters max)", max_length=MAX_IDENTIFIER_LEN, default='-')
    # title (1-n;f)             [many-to-one]
    title = models.ManyToManyField(Title, blank=False, related_name="collectionm2m_title")
    # == description (0-1;f) 
    description = models.TextField("Describes the collection as a whole", blank=True, help_text=get_help('description'))
    # == owner (0-n;f)          [many-to-one]
    owner = models.ManyToManyField( Owner, blank=True, related_name="collectionm2m_owner")
    # resource (1-n)            [many-to-one]
    resource = models.ManyToManyField(Resource, blank=False, related_name="collectionm2m_resource")
    # == genre (0-n; c:)        [many-to-one]
    genre = models.ManyToManyField(Genre, blank=True, related_name="collectionm2m_genre")
    # provenance (0-n)          [many-to-one]
    provenance = models.ManyToManyField(Provenance, blank=True, related_name="collectionm2m_provenance")
    # linguality (0-1)
    linguality = models.ForeignKey(Linguality, blank=True, null=True)   # , related_name="collectionm2m_linguality")
    # language (1-n; c)   Many-to-Many!!
    language = models.ManyToManyField(Language, blank=False)
    # languageDisorder (0-n;f)  [many-to-one]
    languageDisorder = models.ManyToManyField(LanguageDisorder, blank=True, related_name="collectionm2m_langdisorder")
    # relation (0-n;f)          [many-to-one]
    relation = models.ManyToManyField(Relation, blank=True, related_name="collectionm2m_relation")
    # == domain (0-n;f)         [many-to-one]
    domain = models.ManyToManyField(Domain, blank=True, related_name="collectionm2m_domain")
    # == clarinCentre (0-1; f)
    clarinCentre = models.TextField("Clarin centre in charge", blank=True, help_text=get_help('clarincentre.name'))
    # == access (0-1)
    access = models.ForeignKey(Access, blank=True, null=True)
    # == totalSize (0-n)        [many-to-one] - verander in 'TotalCollectionSize'
    totalSize = models.ManyToManyField(TotalSize, blank=True, related_name="collectionm2m_totalsize")
    # == PID (0-n)              [many-to-one]
    pid = models.ManyToManyField(PID, blank=True, related_name="collectionm2m_pid")
    # == version (0-1; f)
    version = models.TextField("Version of the collection", blank=True, help_text=get_help('version'))
    # == resourceCreator (0-n)  [many-to-one]
    resourceCreator = models.ManyToManyField(ResourceCreator, blank=True, related_name="collectionm2m_resourcecreator")
    # == documentation (0-1)
    documentation = models.ForeignKey(Documentation, blank=True, null=True)
    # == validation (0-1)
    validation = models.ForeignKey(Validation, blank=True, null=True)
    # == project (0-n)          [many-to-one]
    project = models.ManyToManyField(Project, blank=True, related_name="collectionm2m_project")

    class Meta:
        # This defines (amongst others) the default ordering in the admin listview of Collections
        ordering = ['identifier']

    def get_identifier(self):
        return self.identifier.value_to_string()

    def do_identifier(self):
        # This function is used in [CollectionAdmin] in list_display
        return str(self.identifier)
    do_identifier.short_description = "Identifier"
    do_identifier.admin_order_field = 'identifier'

    def get_title(self):
        return m2m_namelist(self.title)
    get_title.short_description = 'Titles (not sortable)'
    # This works, but sorting on a non-f
    # get_title.admin_order_field = 'identifier'

    def __str__(self):
        # We are known by our identifier
        return self.identifier
