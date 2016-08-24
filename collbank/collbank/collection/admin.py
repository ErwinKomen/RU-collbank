from django.contrib import admin
from collbank.collection.models import *
from django.core import serializers
from django.contrib.contenttypes.models import ContentType
import logging
# from lxml.etree import ElementTree, Element, SubElement

#class TitleInline(admin.TabularInline):
#    model = Collection.title.through
#    extra = 1

MAX_IDENTIFIER_LEN = 10
logger = logging.getLogger(__name__)

def remove_from_fieldsets(fieldsets, fields):
    for fieldset in fieldsets:
        for field in fields:
            if field in fieldset[1]['fields']:
                logging.debug("'%s' field found in %s, hiding." % (field, fieldset[1]['fields']))
                newfields = []
                for myfield in fieldset[1]['fields']:
                    if not myfield in fields:
                        newfields.append(myfield)

                fieldset[1]['fields'] = tuple(newfields)
                logger.debug('Setting newfields to: %s' % newfields)

                break

class CollectionAdmin(admin.ModelAdmin):
#    inlines = (TitleInline,)
    filter_horizontal = ('title', 'identifier', 'owner', 'resource', 'genre', 'language', 'languageDisorder', 'relation', 'domain', 'totalSize', 'pid', 'resourceCreator', 'project',)
    fieldsets = ( ('Searchable', {'fields': ('title', 'identifier', 'resource', 'provenance', 'linguality','language', 'languageDisorder', 'relation', 'speechCorpus',)}),
                  ('Other',      {'fields': ('description', 'owner', 'genre', 'domain', 'clarinCentre', 'access', 'totalSize', 'pid', 'version', 'resourceCreator', 'documentation', 'validation', 'project', 'writtenCorpus',)}),
                )
    actions = ['export_xml']

    def get_form(self, request, obj=None, **kwargs):
        form = super(CollectionAdmin, self).get_form(request, obj, **kwargs)
        bDelField = False
        # Check if the 'identifier' field has been defined
        if obj != None:
            # Try to get the value of this instance
            sValue = obj.identifier
            # Check this value
            if sValue == "" or sValue == "-":
                # Try to create a better value: get the shortest title
                if obj.title != None:
                    # Sort all the many-to-many titles for this object
                    oTitles = obj.title.extra(select={'length': 'Length(name)'}).order_by('length')
                    # get the shortest title
                    smallest = oTitles.first().name
                    # check if the length is okay
                    if smallest != "" and smallest != "-" and len(smallest) <= MAX_IDENTIFIER_LEN:
                        # The identifier is large enough
                        bDelField = True
                        # Make sure that the 'identifier' field is set
                        obj.identifier = smallest
                        # And make sure it is written to the database
                        obj.save()
            else:
                # the [sValue] is not empty, so the field is not needed in this instance
                bDelField = True

        if bDelField:
            # Delete the field
            # del form.base_fields['identifier']
            # Remove it from the fieldsets
            remove_from_fieldsets(self.fieldsets, ('identifier',))
            

        # return the form
        return form

    def export_xml(self, request, queryset):
        # Export this object to XML
        oSerializer = serializers.get_serializer("xml")
        xml_serializer = oSerializer()
        with open("collbank-file.xml", "w") as out:
            sFullPath = out.name
            xml_serializer.serialize(queryset, stream=out)
        # TODO: make the file available for download and provide a link to it
    export_xml.short_description = "Export in XML format"




class ProvenanceAdmin(admin.ModelAdmin):
    filter_horizontal = ('geographicProvenance',)
    fieldsets = ( ('Searchable', {'fields': ('temporalProvenance', 'geographicProvenance',)}),
                  ('Other',      {'fields': ()}),
                )


class TemporalProvenanceAdmin(admin.ModelAdmin):
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('startYear', 'endYear',)}),
                )


class GeographicProvenanceAdmin(admin.ModelAdmin):
    filter_horizontal = ('place',)
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('country', 'place',)}),
                )


class ResourceAdmin(admin.ModelAdmin):
    filter_horizontal = ('annotation','totalSize',)
    fieldsets = ( ('Searchable', {'fields': ('type', 'annotation', 'media',)}),
                  ('Other',      {'fields': ('description', 'totalSize',)}),
                )


class AnnotationAdmin(admin.ModelAdmin):
    fieldsets = ( ('Searchable', {'fields': ('type',) }),
                  ('Other',      {'fields': ('mode', 'format',)}),
                )


class MediaAdmin(admin.ModelAdmin):
    filter_horizontal = ('format',)
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('format',)}),
                )


class DomainAdmin(admin.ModelAdmin):
    filter_horizontal = ('name',)
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('name',)}),
                )


class LingualityAdmin(admin.ModelAdmin):
    filter_horizontal = ('lingualityType', 'lingualityNativeness', 'lingualityAgeGroup', 'lingualityStatus', 'lingualityVariant', 'multilingualityType', )
    fieldsets = ( ('Searchable', {'fields': ('lingualityType', 'lingualityNativeness', 'lingualityAgeGroup', 'lingualityStatus', 'lingualityVariant', 'multilingualityType',) }),
                  ('Other',      {'fields': ()}),
                )


class AccessAdmin(admin.ModelAdmin):
    filter_horizontal = ('availability', 'licenseName', 'licenseUrl', 'contact', 'website', 'medium',)
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('name', 'availability', 'licenseName', 'licenseUrl', 'nonCommercialUsageOnly', 'contact', 'website', 'ISBN', 'ISLRN', 'medium',)}),
                )


class TotalSizeAdmin(admin.ModelAdmin):
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('size', 'sizeUnit',)}),
                )


class ResourceCreatorAdmin(admin.ModelAdmin):
    filter_horizontal = ('organization', 'person',)
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('organization', 'person',)}),
                )


class DocumentationAdmin(admin.ModelAdmin):
    filter_horizontal = ('documentationType', 'fileName', 'url', 'language',)
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('documentationType', 'fileName', 'url', 'language',)}),
                )


class ValidationAdmin(admin.ModelAdmin):
    filter_horizontal = ('method',)
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('type', 'method',)}),
                )


class ProjectAdmin(admin.ModelAdmin):
    filter_horizontal = ('funder',)
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('title', 'funder', 'URL',)}),
                )


class SpeechCorpusAdmin(admin.ModelAdmin):
    filter_horizontal = ('recordingEnvironment', 'channel', 'conversationalType', 'recordingConditions', 'socialContext', 'planningType', 'interactivity', 'involvement', 'audience',)
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('recordingEnvironment', 'channel', 'conversationalType', 'recordingConditions', 'durationOfEffectiveSpeech', 'durationOfFullDatabase', 'numberOfSpeakers', 'speakerDemographics', 'socialContext', 'planningType', 'interactivity', 'involvement', 'audience',)}),
                )

class FieldChoiceAdmin(admin.ModelAdmin):
    readonly_fields=['machine_value']
    list_display = ['english_name','dutch_name','machine_value','field']
    list_filter = ['field']

    def save_model(self, request, obj, form, change):

        if obj.machine_value == None:
            # Check out the query-set and make sure that it exists
            qs = FieldChoice.objects.filter(field=obj.field)
            if len(qs) == 0:
                # The field does not yet occur within FieldChoice
                # Future: ask user if that is what he wants (don't know how...)
                # For now: assume user wants to add a new field (e.g: wordClass)
                # NOTE: start with '0'
                obj.machine_value = 0
            else:
                # Calculate highest currently occurring value
                highest_machine_value = max([field_choice.machine_value for field_choice in qs])
                # The automatic machine value we calculate is 1 higher
                obj.machine_value= highest_machine_value+1

        obj.save()


# Models that serve others
admin.site.register(FieldChoice, FieldChoiceAdmin)
admin.site.register(HelpChoice)

# Models for the collection record
admin.site.register(Title)
admin.site.register(Owner)
# -- Resource
admin.site.register(Resource, ResourceAdmin)
admin.site.register(Annotation, AnnotationAdmin)
admin.site.register(MediaFormat)
admin.site.register(Media, MediaAdmin)
# -- Genre
admin.site.register(Genre)
# -- provenance
admin.site.register(Provenance, ProvenanceAdmin)
admin.site.register(TemporalProvenance, TemporalProvenanceAdmin)
admin.site.register(GeographicProvenance, GeographicProvenanceAdmin)
admin.site.register(City)
# -- linguality
admin.site.register(LingualityType)
admin.site.register(LingualityNativeness)
admin.site.register(LingualityAgeGroup)
admin.site.register(LingualityStatus)
admin.site.register(LingualityVariant)
admin.site.register(MultilingualityType)
admin.site.register(Linguality, LingualityAdmin)
# -- language
admin.site.register(Language)
# -- languageDisorder
admin.site.register(LanguageDisorder)
# -- relation
admin.site.register(Relation)
# -- domain
admin.site.register(DomainDescription)
admin.site.register(Domain, DomainAdmin)
# -- access
admin.site.register(AccessAvailability)
admin.site.register(LicenseName)
admin.site.register(LicenseUrl)
admin.site.register(NonCommercialUsageOnly)
admin.site.register(AccessContact)
admin.site.register(AccessWebsite)
admin.site.register(AccessMedium)
admin.site.register(Access, AccessAdmin)
# -- totalSize
admin.site.register(TotalSize, TotalSizeAdmin)
# -- PID
admin.site.register(PID)
# -- resourceCreator
admin.site.register(Organization)
admin.site.register(Person)
admin.site.register(ResourceCreator, ResourceCreatorAdmin)
# -- documentation
admin.site.register(DocumentationFile)
admin.site.register(DocumentationType)
admin.site.register(DocumentationUrl)
admin.site.register(Documentation, DocumentationAdmin)
# -- validation
admin.site.register(ValidationType)
admin.site.register(ValidationMethod)
admin.site.register(Validation, ValidationAdmin)
# -- project
admin.site.register(ProjectFunder)
admin.site.register(ProjectUrl)
admin.site.register(Project, ProjectAdmin)

# -- writtencorpus
admin.site.register(CharacterEncoding)
admin.site.register(WrittenCorpus)
# -- speechcorpus
admin.site.register(RecordingEnvironment)
admin.site.register(Channel)
admin.site.register(ConversationalType)
admin.site.register(RecordingCondition)
admin.site.register(SocialContext)
admin.site.register(PlanningType)
admin.site.register(Interactivity)
admin.site.register(Involvement)
admin.site.register(Audience)
admin.site.register(SpeechCorpus, SpeechCorpusAdmin)

# -- collection as a whole
admin.site.register(Collection, CollectionAdmin)
