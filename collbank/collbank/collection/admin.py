from django.contrib import admin
from django.db.models import Q
from django import forms
from django.forms import Textarea
from collbank.collection.models import *
from functools import partial
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

class TitleInline(admin.TabularInline):
    model = Collection.title.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class OwnerInline(admin.TabularInline):
    model = Collection.owner.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class ResourceInline(admin.TabularInline):
    model = Collection.resource.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class GenreInline(admin.TabularInline):
    model = Collection.genre.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class ProvenanceInline(admin.TabularInline):
    model = Collection.provenance.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class LanguageInline(admin.TabularInline):
    model = Collection.language.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class LanguageDisorderInline(admin.TabularInline):
    model = Collection.languageDisorder.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class RelationInline(admin.TabularInline):
    model = Collection.relation.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class CollectionDomainInline(admin.TabularInline):
    model = Collection.domain.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class TotalSizeInline(admin.TabularInline):
    model = Collection.totalSize.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class PidInline(admin.TabularInline):
    model = Collection.pid.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class ResourceCreatorInline(admin.TabularInline):
    model = Collection.resourceCreator.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class ProjectInline(admin.TabularInline):
    model = Collection.project.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class CollectionAdmin(admin.ModelAdmin):
#    inlines = (TitleInline,)
    inlines = [TitleInline, OwnerInline, ResourceInline, GenreInline, ProvenanceInline,
               LanguageInline, LanguageDisorderInline, RelationInline, CollectionDomainInline,
               TotalSizeInline, PidInline, ResourceCreatorInline]
    # exclude = ('title', 'owner', 'resource', 'genre', 'provenance', 'language', 'languageDisorder', 'relation', 'domain', 'totalSize', 'pid', 'resourceCreator', 'project',)
    # filter_horizontal = ('title', 'owner', 'resource', 'genre', 'provenance', 'language', 'languageDisorder', 'relation', 'domain', 'totalSize', 'pid', 'resourceCreator', 'project',)
    # fieldsets = ( ('Searchable', {'fields': ('title', 'identifier', 'resource', 'provenance', 'linguality','language', 'languageDisorder', 'relation', 'speechCorpus',)}),
    #               ('Other',      {'fields': ('description', 'owner', 'genre', 'domain', 'clarinCentre', 'access', 'totalSize', 'pid', 'version', 'resourceCreator', 'documentation', 'validation', 'project', 'writtenCorpus',)}),
    #             )
    fieldsets = ( ('Searchable', {'fields': ('identifier', 'linguality',  'speechCorpus',)}),
                  ('Other',      {'fields': ('description', 'clarinCentre', 'access', 'version', 'documentation', 'validation', 'writtenCorpus',)}),
                )
    actions = ['export_xml']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }

    def get_form(self, request, obj=None, **kwargs):
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(CollectionAdmin, self).get_form(request, obj, **kwargs)
        bDelField = False
        bKeepIdentifier = True
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

        if bDelField and not bKeepIdentifier:
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

    def formfield_for_dbfield(self, db_field, **kwargs):
      collThis = kwargs.pop('obj', None)
      formfield = super(CollectionAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "title" and collThis:
          formfield.queryset = Title.objects.filter(collection=collThis.pk)
      elif db_field.name == "owner" and collThis:
          formfield.queryset = Owner.objects.filter(collection=collThis.pk)
      elif db_field.name == "resource" and collThis:
          formfield.queryset = Resource.objects.filter(collection=collThis.pk)
      elif db_field.name == "genre" and collThis:
          formfield.queryset = Genre.objects.filter(collection=collThis.pk)
      elif db_field.name == "provenance" and collThis:
          formfield.queryset = Provenance.objects.filter(collection=collThis.pk)
      elif db_field.name == "language" and collThis:
          formfield.queryset = Language.objects.filter(collection=collThis.pk)
      elif db_field.name == "languageDisorder" and collThis:
          formfield.queryset = LanguageDisorder.objects.filter(collection=collThis.pk)
      elif db_field.name == "relation" and collThis:
          formfield.queryset = Relation.objects.filter(collection=collThis.pk)
      elif db_field.name == "domain" and collThis:
          formfield.queryset = Domain.objects.filter(collection=collThis.pk)
      elif db_field.name == "totalSize" and collThis:
          formfield.queryset = TotalSize.objects.filter(collection=collThis.pk)
      elif db_field.name == "pid" and collThis:
          formfield.queryset = PID.objects.filter(collection=collThis.pk)
      elif db_field.name == "resourceCreator" and collThis:
          formfield.queryset = ResourceCreator.objects.filter(collection=collThis.pk)
      elif db_field.name == "project" and collThis:
          formfield.queryset = Project.objects.filter(collection=collThis.pk)
      elif db_field.name == "linguality" and collThis:                                  # ForeignKey
          formfield.queryset = Linguality.objects.filter(collection=collThis.pk)
      elif db_field.name == "access" and collThis:                                      # ForeignKey
          formfield.queryset = Access.objects.filter(collection=collThis.pk)
      elif db_field.name == "documentation" and collThis:                               # ForeignKey
          formfield.queryset = Documentation.objects.filter(collection=collThis.pk)
      elif db_field.name == "validation" and collThis:                                  # ForeignKey
          formfield.queryset = Validation.objects.filter(collection=collThis.pk)
      elif db_field.name == "writtenCorpus" and collThis:                               # ForeignKey
          formfield.queryset = WrittenCorpus.objects.filter(collection=collThis.pk)
      elif db_field.name == "speechCorpus" and collThis:                                # ForeignKey
          formfield.queryset = SpeechCorpus.objects.filter(collection=collThis.pk)
      return formfield

 




class GeographicProvenanceInline(admin.TabularInline):
    model = Provenance.geographicProvenance.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class ProvenanceAdmin(admin.ModelAdmin):
    inlines = [GeographicProvenanceInline]
    fieldsets = ( ('Searchable', {'fields': ('temporalProvenance',)}),
                  ('Other',      {'fields': ()}),
                )

    def get_form(self, request, obj=None, **kwargs):
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(ProvenanceAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(ProvenanceAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "geographicProvenance" and itemThis:
          formfield.queryset = GeographicProvenance.objects.filter(provenance=itemThis.pk)
      elif db_field.name == "temporalProvenance" and itemThis:                                  # ForeignKey
          formfield.queryset = TemporalProvenance.objects.filter(provenance=itemThis.pk)
      return formfield


class TemporalProvenanceAdmin(admin.ModelAdmin):
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('startYear', 'endYear',)}),
                )


class PlaceInline(admin.TabularInline):
    model = GeographicProvenance.place.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class GeographicProvenanceAdmin(admin.ModelAdmin):
    inlines = [PlaceInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('country', )}),
                )

    def get_form(self, request, obj=None, **kwargs):
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(GeographicProvenanceAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(GeographicProvenanceAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "geographicProvenance" and itemThis:
          formfield.queryset = City.objects.filter(gegraphicprovenance=itemThis.pk)
      return formfield


class AnnotationInline(admin.TabularInline):
    model = Resource.annotation.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class ResourceSizeInline(admin.TabularInline):
    model = Resource.totalSize.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class ResourceAdmin(admin.ModelAdmin):
    # filter_horizontal = ('annotation','totalSize',)
    inlines = [AnnotationInline, ResourceSizeInline]
    fieldsets = ( ('Searchable', {'fields': ('type', 'media',)}),
                  ('Other',      {'fields': ('description', )}),
                )

    def get_form(self, request, obj=None, **kwargs):
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(ResourceAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(ResourceAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "annotation" and itemThis:
          formfield.queryset = Annotation.objects.filter(resource=itemThis.pk)
      elif db_field.name == "totalSize" and itemThis:
          formfield.queryset = TotalSize.objects.filter(resource=itemThis.pk)
      elif db_field.name == "media" and itemThis:                                   # ForeignKey
          formfield.queryset = Media.objects.filter(resource=itemThis.pk)
      return formfield


class AnnotationFormatInline(admin.TabularInline):
    model = Annotation.formatAnn.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class AnnotationAdmin(admin.ModelAdmin):
    inlines = [AnnotationFormatInline]
    fieldsets = ( ('Searchable', {'fields': ('type',) }),
                  ('Other',      {'fields': ('mode', )}),
                )
    # readonly_fields = ('format',)

    def __init__(self, *args, **kwargs):
        super(AnnotationAdmin, self).__init__(*args, **kwargs)
        if (self.fields != None):
            self.fields['name'].choices = build_choice_list("access.nonCommercialUsageOnly")

    def get_form(self, request, obj=None, **kwargs):
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(AnnotationAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(AnnotationAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "formatAnn" and itemThis:
          # Check if this needs to be populated
          if itemThis.formatAnn.count() == 0:
              # This needs populating
              formatNew = AnnotationFormat.objects.create(name = itemThis.format)
              # Add it to this model
              itemThis.formatAnn.add(formatNew)
          # Now show it
          formfield.queryset = AnnotationFormat.objects.filter(annotation=itemThis.pk)
      elif db_field.name == "type" and itemThis and itemThis.formatAnn.count() == 0:
          # Create a new format object
          formatNew = AnnotationFormat.objects.create(name = itemThis.format)
          # Add it to this model
          itemThis.formatAnn.add(formatNew)
      return formfield



class FormatInline(admin.TabularInline):
    model = Media.format.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class MediaAdmin(admin.ModelAdmin):
    # filter_horizontal = ('format',)
    inlines = [FormatInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ()}),
                )

    def get_form(self, request, obj=None, **kwargs):
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(MediaAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(MediaAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "format" and itemThis:
          formfield.queryset = MediaFormat.objects.filter(media=itemThis.pk)
      return formfield


class LanguageForm(forms.ModelForm):

    class Meta:
        model = Language
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(LanguageForm, self).__init__(*args, **kwargs)
        if (self.fields != None):
            self.fields['name'].choices = build_choice_list("language.name")


class LanguageAdmin(admin.ModelAdmin):
    form = LanguageForm


class AccessAvailabilityForm(forms.ModelForm):

    class Meta:
        model = AccessAvailability
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(AccessAvailabilityForm, self).__init__(*args, **kwargs)
        if (self.fields != None):
            self.fields['name'].choices = build_choice_list("access.availability")


class AccessAvailabilityAdmin(admin.ModelAdmin):
    form = AccessAvailabilityForm


class AccessMediumForm(forms.ModelForm):

    class Meta:
        model = AccessMedium
        fields = ['format']

    def __init__(self, *args, **kwargs):
        super(AccessMediumForm, self).__init__(*args, **kwargs)
        if (self.fields != None):
            self.fields['format'].choices = build_choice_list("access.medium.format")


class AccessMediumAdmin(admin.ModelAdmin):
    form = AccessMediumForm



class NonCommercialUsageOnlyForm(forms.ModelForm):

    class Meta:
        model = NonCommercialUsageOnly
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(NonCommercialUsageOnlyForm, self).__init__(*args, **kwargs)
        if (self.fields != None):
            self.fields['name'].choices = build_choice_list("access.nonCommercialUsageOnly")


class NonCommercialUsageOnlyAdmin(admin.ModelAdmin):
    form = NonCommercialUsageOnlyForm



class DocumentationTypeForm(forms.ModelForm):

    class Meta:
        model = DocumentationType
        fields = ['format']

    def __init__(self, *args, **kwargs):
        super(DocumentationTypeForm, self).__init__(*args, **kwargs)
        if (self.fields != None):
            self.fields['format'].choices = build_choice_list("documentation.type")


class DocumentationTypeAdmin(admin.ModelAdmin):
    form = DocumentationTypeForm


class AudioFormatForm(forms.ModelForm):

    class Meta:
        model = AudioFormat
        fields = ['speechCoding', 'samplingFrequency', 'compression', 'bitResolution']

    def __init__(self, *args, **kwargs):
        super(AudioFormatForm, self).__init__(*args, **kwargs)
        if (self.fields != None):
            self.fields['speechCoding'].choices = build_choice_list("audioformat.speechcoding")


class AudioFormatAdmin(admin.ModelAdmin):
    form = AudioFormatForm


class DomainInline(admin.TabularInline):
    model = Domain.name.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class DomainAdmin(admin.ModelAdmin):
    # filter_horizontal = ('name',)
    inlines = [DomainInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ()}),
                )

    def get_form(self, request, obj=None, **kwargs):
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(DomainAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(DomainAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "name" and itemThis:
          formfield.queryset = DomainDescription.objects.filter(domain=itemThis.pk)
      return formfield


class LingualityTypeInline(admin.TabularInline):
    model = Linguality.lingualityType.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class LingualityNativenessInline(admin.TabularInline):
    model = Linguality.lingualityNativeness.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class LingualityAgeGroupInline(admin.TabularInline):
    model = Linguality.lingualityAgeGroup.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class LingualityStatusInline(admin.TabularInline):
    model = Linguality.lingualityStatus.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class LingualityVariantInline(admin.TabularInline):
    model = Linguality.lingualityVariant.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class MultiLingualityTypeInline(admin.TabularInline):
    model = Linguality.multilingualityType.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class LingualityAdmin(admin.ModelAdmin):
    # filter_horizontal = ('lingualityType', 'lingualityNativeness', 'lingualityAgeGroup', 'lingualityStatus', 'lingualityVariant', 'multilingualityType', )
    inlines = [LingualityTypeInline, LingualityNativenessInline, 
               LingualityAgeGroupInline, LingualityStatusInline,
               LingualityVariantInline, MultiLingualityTypeInline]
    fieldsets = ( ('Searchable', {'fields': () }),
                  ('Other',      {'fields': ()}),
                )

    def get_form(self, request, obj=None, **kwargs):
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(LingualityAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(LingualityAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "lingualityType" and itemThis:
          formfield.queryset = LingualityType.objects.filter(linguality=itemThis.pk)
      elif db_field.name == "lingualityNativeness" and itemThis:
          formfield.queryset = LingualityNativeness.objects.filter(linguality=itemThis.pk)
      elif db_field.name == "lingualityAgeGroup" and itemThis:
          formfield.queryset = LingualityAgeGroup.objects.filter(linguality=itemThis.pk)
      elif db_field.name == "lingualityStatus" and itemThis:
          formfield.queryset = LingualityStatus.objects.filter(linguality=itemThis.pk)
      elif db_field.name == "lingualityVariant" and itemThis:
          formfield.queryset = LingualityVariant.objects.filter(linguality=itemThis.pk)
      elif db_field.name == "multilingualityType" and itemThis:
          formfield.queryset = MultilingualityType.objects.filter(linguality=itemThis.pk)
      return formfield


class AccessAvailabilityInline(admin.TabularInline):
    model = Access.availability.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class AccessLicenseNameInline(admin.TabularInline):
    model = Access.licenseName.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class AccessLicenseUrlInline(admin.TabularInline):
    model = Access.licenseUrl.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class AccessContactInline(admin.TabularInline):
    model = Access.contact.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class AccessWebsiteInline(admin.TabularInline):
    model = Access.website.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class AccessMediumInline(admin.TabularInline):
    model = Access.medium.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class AccessAdmin(admin.ModelAdmin):
    # filter_horizontal = ('availability', 'licenseName', 'licenseUrl', 'contact', 'website', 'medium',)
    inlines = [AccessAvailabilityInline, AccessLicenseNameInline,
               AccessLicenseUrlInline, AccessContactInline,
               AccessWebsiteInline, AccessMediumInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
#                 ('Other',      {'fields': ('name', 'availability', 'licenseName', 'licenseUrl', 'nonCommercialUsageOnly', 'contact', 'website', 'ISBN', 'ISLRN', 'medium',)}),
                  ('Other',      {'fields': ('name', 'nonCommercialUsageOnly', 'ISBN', 'ISLRN', )}),
                )
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }

    def get_form(self, request, obj=None, **kwargs):
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(AccessAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(AccessAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "availability" and itemThis:
          formfield.queryset = AccessAvailability.objects.filter(access=itemThis.pk)
      elif db_field.name == "licenseName" and itemThis:
          formfield.queryset = LicenseName.objects.filter(access=itemThis.pk)
      elif db_field.name == "licenseUrl" and itemThis:
          formfield.queryset = LicenseUrl.objects.filter(access=itemThis.pk)
      elif db_field.name == "contact" and itemThis:
          formfield.queryset = AccessContact.objects.filter(access=itemThis.pk)
      elif db_field.name == "website" and itemThis:
          formfield.queryset = AccessWebsite.objects.filter(access=itemThis.pk)
      elif db_field.name == "medium" and itemThis:
          formfield.queryset = AccessMedium.objects.filter(access=itemThis.pk)
      elif db_field.name == "nonCommercialUsageOnly" and itemThis:                  # ForeignKey
          formfield.queryset = NonCommercialUsageOnly.objects.filter(access=itemThis.pk)
      return formfield


class TotalSizeAdmin(admin.ModelAdmin):
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('size', 'sizeUnit',)}),
                )


class ResourceOrganizationInline(admin.TabularInline):
    model = ResourceCreator.organization.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class ResourcePersonInline(admin.TabularInline):
    model = ResourceCreator.person.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class ResourceCreatorAdmin(admin.ModelAdmin):
    # filter_horizontal = ('organization', 'person',)
    inlines = [ResourceOrganizationInline, ResourcePersonInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ()}),
                )
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }

    def get_form(self, request, obj=None, **kwargs):
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(ResourceCreatorAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(ResourceCreatorAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "organization" and itemThis:
          formfield.queryset = Organization.objects.filter(resourcecreator=itemThis.pk)
      elif db_field.name == "person" and itemThis:
          formfield.queryset = Person.objects.filter(resourcecreator=itemThis.pk)
      return formfield


class DocumentationTypeInline(admin.TabularInline):
    model = Documentation.documentationType.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class DocumentationFileInline(admin.TabularInline):
    model = Documentation.fileName.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class DocumentationUrlInline(admin.TabularInline):
    model = Documentation.url.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class DocumentationLanguageInline(admin.TabularInline):
    model = Documentation.language.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class DocumentationAdmin(admin.ModelAdmin):
    # filter_horizontal = ('documentationType', 'fileName', 'url', 'language',)
    inlines = [DocumentationTypeInline, DocumentationFileInline,
               DocumentationUrlInline, DocumentationLanguageInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ()}),
                )

    def get_form(self, request, obj=None, **kwargs):
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(DocumentationAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(DocumentationAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "documentationType" and itemThis:
          formfield.queryset = DocumentationType.objects.filter(documentationadmin=itemThis.pk)
      elif db_field.name == "fileName" and itemThis:
          formfield.queryset = DocumentationFile.objects.filter(documentationadmin=itemThis.pk)
      elif db_field.name == "url" and itemThis:
          formfield.queryset = DocumentationUrl.objects.filter(documentationadmin=itemThis.pk)
      elif db_field.name == "language" and itemThis:
          formfield.queryset = Language.objects.filter(documentationadmin=itemThis.pk)
      return formfield


class ValidationMethodInline(admin.TabularInline):
    model = Validation.method.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class ValidationAdmin(admin.ModelAdmin):
    # filter_horizontal = ('method',)
    inlines = [ValidationMethodInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('type', )}),
                )

    def get_form(self, request, obj=None, **kwargs):
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(ValidationAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(ValidationAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "method" and itemThis:
          formfield.queryset = ValidationMethod.objects.filter(validation=itemThis.pk)
      elif db_field.name == "type" and itemThis:                                                # ForeignKey
          formfield.queryset = ValidationType.objects.filter(validation=itemThis.pk)
      return formfield


class ProjectFunderInline(admin.TabularInline):
    model = Project.funder.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class ProjectAdmin(admin.ModelAdmin):
    # filter_horizontal = ('funder',)
    inlines = [ProjectFunderInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('title', 'URL',)}),
                )
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }

    def get_form(self, request, obj=None, **kwargs):
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(ValidationAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(ValidationAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "method" and itemThis:
          formfield.queryset = ValidationMethod.objects.filter(validation=itemThis.pk)
      elif db_field.name == "URL" and itemThis:                                                     # ForeignKey
          formfield.queryset = ProjectUrl.objects.filter(validation=itemThis.pk)
      return formfield


class SpeechCorpusRecEnvInline(admin.TabularInline):
    model = SpeechCorpus.recordingEnvironment.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class SpeechCorpusChannelInline(admin.TabularInline):
    model = SpeechCorpus.channel.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class SpeechCorpusConvTypeInline(admin.TabularInline):
    model = SpeechCorpus.conversationalType.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class SpeechCorpusRecCondInline(admin.TabularInline):
    model = SpeechCorpus.recordingConditions.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class SpeechCorpusSocContextInline(admin.TabularInline):
    model = SpeechCorpus.socialContext.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class SpeechCorpusPlanTypeInline(admin.TabularInline):
    model = SpeechCorpus.planningType.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class SpeechCorpusInteractivityInline(admin.TabularInline):
    model = SpeechCorpus.interactivity.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class SpeechCorpusInvolvementInline(admin.TabularInline):
    model = SpeechCorpus.involvement.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class SpeechCorpusAudienceInline(admin.TabularInline):
    model = SpeechCorpus.audience.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class SpeechCorpusAudioFormatInline(admin.TabularInline):
    model = SpeechCorpus.audioFormat.through

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class SpeechCorpusAdmin(admin.ModelAdmin):
    # filter_horizontal = ('recordingEnvironment', 'channel', 'conversationalType', 'recordingConditions', 
    #                      'socialContext', 'planningType', 'interactivity', 'involvement', 'audience', 'audioFormat')
    inlines = [SpeechCorpusRecEnvInline, SpeechCorpusChannelInline, SpeechCorpusConvTypeInline,
               SpeechCorpusRecCondInline, SpeechCorpusSocContextInline, SpeechCorpusPlanTypeInline,
               SpeechCorpusInteractivityInline, SpeechCorpusInvolvementInline,
               SpeechCorpusAudienceInline, SpeechCorpusAudioFormatInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('durationOfEffectiveSpeech', 'durationOfFullDatabase', 'numberOfSpeakers', 
                                             'speakerDemographics')}),
                )
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }

    def get_form(self, request, obj=None, **kwargs):
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(SpeechCorpusAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(SpeechCorpusAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "recordingEnvironment" and itemThis:
          formfield.queryset = RecordingEnvironment.objects.filter(speechcorpus=itemThis.pk)
      elif db_field.name == "channel" and itemThis:
          formfield.queryset = Channel.objects.filter(speechcorpus=itemThis.pk)
      elif db_field.name == "conversationalType" and itemThis:
          formfield.queryset = ConversationalType.objects.filter(speechcorpus=itemThis.pk)
      elif db_field.name == "recordingConditions" and itemThis:
          formfield.queryset = RecordingCondition.objects.filter(speechcorpus=itemThis.pk)
      elif db_field.name == "socialContext" and itemThis:
          formfield.queryset = SocialContext.objects.filter(speechcorpus=itemThis.pk)
      elif db_field.name == "planningType" and itemThis:
          formfield.queryset = PlanningType.objects.filter(speechcorpus=itemThis.pk)
      elif db_field.name == "interactivity" and itemThis:
          formfield.queryset = Interactivity.objects.filter(speechcorpus=itemThis.pk)
      elif db_field.name == "involvement" and itemThis:
          formfield.queryset = Involvement.objects.filter(speechcorpus=itemThis.pk)
      elif db_field.name == "audience" and itemThis:
          formfield.queryset = Audience.objects.filter(speechcorpus=itemThis.pk)
      elif db_field.name == "audioFormat" and itemThis:
          formfield.queryset = AudioFormat.objects.filter(speechcorpus=itemThis.pk)
      return formfield

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
admin.site.register(Language, LanguageAdmin)
# -- languageDisorder
admin.site.register(LanguageDisorder)
# -- relation
admin.site.register(Relation)
# -- domain
admin.site.register(DomainDescription)
admin.site.register(Domain, DomainAdmin)
# -- access
admin.site.register(AccessAvailability, AccessAvailabilityAdmin)
admin.site.register(LicenseName)
admin.site.register(LicenseUrl)
admin.site.register(NonCommercialUsageOnly, NonCommercialUsageOnlyAdmin)
admin.site.register(AccessContact)
admin.site.register(AccessWebsite)
admin.site.register(AccessMedium, AccessMediumAdmin)
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
admin.site.register(DocumentationType, DocumentationTypeAdmin)
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
admin.site.register(AudioFormat, AudioFormatAdmin)
admin.site.register(SpeechCorpus, SpeechCorpusAdmin)

# -- collection as a whole
admin.site.register(Collection, CollectionAdmin)
