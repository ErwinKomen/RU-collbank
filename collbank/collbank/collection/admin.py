from django.contrib import admin
from django.db.models import Q
from django import forms
from django.forms import Textarea
from collbank.collection.models import *
from collbank.settings import APP_PREFIX
from functools import partial
from django.core import serializers
from django.contrib.contenttypes.models import ContentType
import logging

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
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(TitleInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "title":
            kwargs['queryset'] = Title.objects.filter(collection__exact=self.instance)
        return super(TitleInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class OwnerInline(admin.TabularInline):
    model = Collection.owner.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(OwnerInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "owner":
            kwargs['queryset'] = Owner.objects.filter(collection__exact=self.instance)
        return super(OwnerInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class ResourceInline(admin.TabularInline):
    model = Collection.resource.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(ResourceInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "resource":
            kwargs['queryset'] = Resource.objects.filter(collection__exact=self.instance)
        return super(ResourceInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class GenreInline(admin.TabularInline):
    model = Collection.genre.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(GenreInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "genre":
            kwargs['queryset'] = Genre.objects.filter(collection__exact=self.instance)
        return super(GenreInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class ProvenanceInline(admin.TabularInline):
    model = Collection.provenance.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(ProvenanceInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "provenance":
            kwargs['queryset'] = Provenance.objects.filter(collection__exact=self.instance)
        return super(ProvenanceInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class LanguageInline(admin.TabularInline):
    model = Collection.language.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(LanguageInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "language":
            kwargs['queryset'] = Language.objects.filter(collection__exact=self.instance)
        return super(LanguageInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class LanguageDisorderInline(admin.TabularInline):
    model = Collection.languageDisorder.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(LanguageDisorderInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "languagedisorder":
            kwargs['queryset'] = LanguageDisorder.objects.filter(collection__exact=self.instance)
        return super(LanguageDisorderInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class RelationInline(admin.TabularInline):
    model = Collection.relation.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(RelationInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "relation":
            kwargs['queryset'] = Relation.objects.filter(collection__exact=self.instance)
        return super(RelationInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class CollectionDomainInline(admin.TabularInline):
    model = Collection.domain.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(CollectionDomainInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "domain":
            kwargs['queryset'] = Domain.objects.filter(collection__exact=self.instance)
        return super(CollectionDomainInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class TotalSizeInline(admin.TabularInline):
    model = Collection.totalSize.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(TotalSizeInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "totalsize":
            kwargs['queryset'] = TotalSize.objects.filter(collection__exact=self.instance)
        return super(TotalSizeInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class PidInline(admin.TabularInline):
    model = Collection.pid.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(PidInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "pid":
            kwargs['queryset'] = PID.objects.filter(collection__exact=self.instance)
        return super(PidInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class ResourceCreatorInline(admin.TabularInline):
    model = Collection.resourceCreator.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(ResourceCreatorInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "resourcecreator":
            kwargs['queryset'] = ResourceCreator.objects.filter(collection__exact=self.instance)
        return super(ResourceCreatorInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class ProjectInline(admin.TabularInline):
    model = Collection.project.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(ProjectInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "project":
            kwargs['queryset'] = Project.objects.filter(collection__exact=self.instance)
        return super(ProjectInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class CollectionAdmin(admin.ModelAdmin):
    inlines = [TitleInline, OwnerInline, ResourceInline, GenreInline, ProvenanceInline,
               LanguageInline, LanguageDisorderInline, RelationInline, CollectionDomainInline,
               TotalSizeInline, PidInline, ResourceCreatorInline, ProjectInline]
    fieldsets = ( ('Searchable', {'fields': ('identifier', 'linguality',  'speechCorpus',)}),
                  ('Other',      {'fields': ('description', 'clarinCentre', 'access', 'version', 'documentation', 'validation', 'writtenCorpus',)}),
                )
    actions = ['export_xml']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }

    def get_formset(self, request, obj = None, **kwargs):
        self.instance = obj
        return super(CollectionAdmin, self).get_formset(request, obj, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        # Get the instance before the form gets generated
        self.instance = obj

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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        collThis = self.instance
        formfield = super(CollectionAdmin, self).formfield_for_foreignkey(db_field, **kwargs)
        if db_field.name == "linguality" and collThis:                                    # ForeignKey
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
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(GeographicProvenanceInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "geographicprovenance":
            kwargs['queryset'] = GeographicProvenance.objects.filter(provenance__exact=self.instance)
        return super(GeographicProvenanceInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


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
      if db_field.name == "temporalProvenance" and itemThis:                                  # ForeignKey
          formfield.queryset = TemporalProvenance.objects.filter(provenance=itemThis.pk)
      return formfield


class TemporalProvenanceAdmin(admin.ModelAdmin):
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('startYear', 'endYear',)}),
                )


class PlaceInline(admin.TabularInline):
    model = GeographicProvenance.place.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(PlaceInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "place":
            kwargs['queryset'] = City.objects.filter(geographicprovenance__exact=self.instance)
        return super(PlaceInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class GeographicProvenanceAdmin(admin.ModelAdmin):
    inlines = [PlaceInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('country', )}),
                )


class AnnotationInline(admin.TabularInline):
    model = Resource.annotation.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(AnnotationInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "annotation":
            kwargs['queryset'] = Annotation.objects.filter(resource__exact=self.instance)
        return super(AnnotationInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class ModalityInline(admin.TabularInline):
    model = Resource.modality.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(ModalityInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "modality":
            kwargs['queryset'] = Modality.objects.filter(resource__exact=self.instance)
        return super(ModalityInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class ResourceSizeInline(admin.TabularInline):
    model = Resource.totalSize.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(ResourceSizeInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "totalsize":
            kwargs['queryset'] = TotalSize.objects.filter(resource__exact=self.instance)
        return super(ResourceSizeInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class ResourceForm(forms.ModelForm):
    # model = Resource
    current_dctype = ''

    def __init__(self, *args, **kwargs):
        super(ResourceForm, self).__init__(*args, **kwargs)
        if (self.fields != None):
            self.fields['subtype'].choices = build_choice_list(RESOURCE_TYPE, 'after', self.current_dctype)

    class Meta:
        model = Resource
        fields = ['type', 'DCtype', 'subtype', 'modality', 'media', 'description']
        widgets = { 'subtype': forms.Select }


class ResourceAdmin(admin.ModelAdmin):
    form = ResourceForm

    # filter_horizontal = ('annotation','totalSize',)
    inlines = [AnnotationInline, ResourceSizeInline, ModalityInline]
    fieldsets = ( ('Searchable', {'fields': ('DCtype', 'subtype', 'modality', 'media',)}),
                  ('Other',      {'fields': ('description', )}),
                )
    current_dctype = ''

    class Media:
        js = ['/'+APP_PREFIX+'static/collection/scripts/collbank.js']

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
      if db_field.name == "media" and itemThis:                                   # ForeignKey
          formfield.queryset = Media.objects.filter(resource=itemThis.pk)
      elif db_field.name == "DCtype":
          # Take note of the selected DC type
          # self.current_dctype = str(itemThis.DCtype)
          # Try to convert this into an integer index
          if itemThis.DCtype != '' and itemThis.DCtype != '-':
              # Get the DCtype list
              arDCtype = db_field.choices
              # Get the element from this list
              sDCtype = get_tuple_value(arDCtype, itemThis.DCtype)
              self.current_dctype = sDCtype
              self.form.current_dctype = sDCtype

      elif db_field.name == "subtype":
          if itemThis.subtype != '' and itemThis.subtype != '-':
              # Note which DCtype was selected
              db_field.choices = build_choice_list(RESOURCE_TYPE, 'after', self.current_dctype)
      return formfield


class AnnotationFormatInline(admin.TabularInline):
    model = Annotation.formatAnn.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Annotation object's identifier
        self.instance = obj
        return super(AnnotationFormatInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "annotationformat":
            kwargs['queryset'] = AnnotationFormat.objects.filter(annotation__exact=self.instance)
        return super(AnnotationFormatInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class AnnotationFormatForm(forms.ModelForm):
    model = AnnotationFormat
    fields = ['name']

    def __init__(self, *args, **kwargs):
        super(AnnotationFormatForm, self).__init__(*args, **kwargs)
        if (self.fields != None):
            self.fields['name'].choices = build_choice_list(ANNOTATION_FORMAT)


class AnnotationFormatAdmin(admin.ModelAdmin):
    form = AnnotationFormatForm


class AnnotationForm(forms.ModelForm):
    model = Annotation
    fields = ['type', 'mode', 'format']

    def __init__(self, *args, **kwargs):
        super(AnnotationForm, self).__init__(*args, **kwargs)
        if (self.fields != None):
            self.fields['type'].choices = build_choice_list(ANNOTATION_TYPE)
            self.fields['mode'].choices = build_choice_list(ANNOTATION_MODE)


class AnnotationAdmin(admin.ModelAdmin):
    inlines = [AnnotationFormatInline]
    fieldsets = ( ('Searchable', {'fields': ('type',) }),
                  ('Other',      {'fields': ('mode', )}),
                )
    form = AnnotationForm

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
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(FormatInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "mediaformat":
            kwargs['queryset'] = MediaFormat.objects.filter(media__exact=self.instance)
        return super(FormatInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class MediaAdmin(admin.ModelAdmin):
    # filter_horizontal = ('format',)
    inlines = [FormatInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ()}),
                )


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
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Domain object's identifier
        self.instance = obj
        return super(DomainInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "domaindescription":
            kwargs['queryset'] = DomainDescription.objects.filter(domain__exact=self.instance)
        return super(DomainInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class DomainAdmin(admin.ModelAdmin):
    # filter_horizontal = ('name',)
    inlines = [DomainInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ()}),
                )


class LingualityTypeInline(admin.TabularInline):
    model = Linguality.lingualityType.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Linguality object's identifier
        self.instance = obj
        return super(LingualityTypeInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Linguality model
        if db_field.name == "lingualitytype":
            kwargs['queryset'] = LingualityType.objects.filter(linguality__exact=self.instance)
        return super(LingualityTypeInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class LingualityNativenessInline(admin.TabularInline):
    model = Linguality.lingualityNativeness.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Linguality object's identifier
        self.instance = obj
        return super(LingualityNativenessInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Linguality model
        if db_field.name == "lingualitynativeness":
            kwargs['queryset'] = LingualityNativeness.objects.filter(linguality__exact=self.instance)
        return super(LingualityNativenessInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class LingualityAgeGroupInline(admin.TabularInline):
    model = Linguality.lingualityAgeGroup.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Linguality object's identifier
        self.instance = obj
        return super(LingualityAgeGroupInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Linguality model
        if db_field.name == "lingualityagegroup":
            kwargs['queryset'] = LingualityAgeGroup.objects.filter(linguality__exact=self.instance)
        return super(LingualityAgeGroupInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class LingualityStatusInline(admin.TabularInline):
    model = Linguality.lingualityStatus.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Linguality object's identifier
        self.instance = obj
        return super(LingualityStatusInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Linguality model
        if db_field.name == "lingualitystatus":
            kwargs['queryset'] = LingualityStatus.objects.filter(linguality__exact=self.instance)
        return super(LingualityStatusInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class LingualityVariantInline(admin.TabularInline):
    model = Linguality.lingualityVariant.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Linguality object's identifier
        self.instance = obj
        return super(LingualityVariantInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Linguality model
        if db_field.name == "lingualityvariant":
            kwargs['queryset'] = LingualityVariant.objects.filter(linguality__exact=self.instance)
        return super(LingualityVariantInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class MultiLingualityTypeInline(admin.TabularInline):
    model = Linguality.multilingualityType.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Linguality object's identifier
        self.instance = obj
        return super(MultiLingualityTypeInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Linguality model
        if db_field.name == "multilingualitytype":
            kwargs['queryset'] = MultilingualityType.objects.filter(linguality__exact=self.instance)
        return super(MultiLingualityTypeInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


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
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Access object's identifier
        self.instance = obj
        return super(AccessAvailabilityInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Access model
        if db_field.name == "accessavailability":
            kwargs['queryset'] = AccessAvailability.objects.filter(access__exact=self.instance)
        return super(AccessAvailabilityInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class AccessLicenseNameInline(admin.TabularInline):
    model = Access.licenseName.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Access object's identifier
        self.instance = obj
        return super(AccessLicenseNameInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Access model
        if db_field.name == "licensename":
            kwargs['queryset'] = LicenseName.objects.filter(access__exact=self.instance)
        return super(AccessLicenseNameInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class AccessLicenseUrlInline(admin.TabularInline):
    model = Access.licenseUrl.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Access object's identifier
        self.instance = obj
        return super(AccessLicenseUrlInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Access model
        if db_field.name == "licenseurl":
            kwargs['queryset'] = LicenseUrl.objects.filter(access__exact=self.instance)
        return super(AccessLicenseUrlInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class AccessContactInline(admin.TabularInline):
    model = Access.contact.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Access object's identifier
        self.instance = obj
        return super(AccessContactInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Access model
        if db_field.name == "accesscontact":
            kwargs['queryset'] = AccessContact.objects.filter(access__exact=self.instance)
        return super(AccessContactInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class AccessWebsiteInline(admin.TabularInline):
    model = Access.website.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Access object's identifier
        self.instance = obj
        return super(AccessWebsiteInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Access model
        if db_field.name == "accesswebsite":
            kwargs['queryset'] = AccessWebsite.objects.filter(access__exact=self.instance)
        return super(AccessWebsiteInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class AccessMediumInline(admin.TabularInline):
    model = Access.medium.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Access object's identifier
        self.instance = obj
        return super(AccessMediumInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Access model
        if db_field.name == "accessmedium":
            kwargs['queryset'] = AccessMedium.objects.filter(access__exact=self.instance)
        return super(AccessMediumInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


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
      if db_field.name == "nonCommercialUsageOnly" and itemThis:                  # ForeignKey
          formfield.queryset = NonCommercialUsageOnly.objects.filter(access=itemThis.pk)

      #if db_field.name == "availability" and itemThis:
      #    formfield.queryset = AccessAvailability.objects.filter(access=itemThis.pk)
      #elif db_field.name == "licenseName" and itemThis:
      #    formfield.queryset = LicenseName.objects.filter(access=itemThis.pk)
      #elif db_field.name == "licenseUrl" and itemThis:
      #    formfield.queryset = LicenseUrl.objects.filter(access=itemThis.pk)
      #elif db_field.name == "contact" and itemThis:
      #    formfield.queryset = AccessContact.objects.filter(access=itemThis.pk)
      #elif db_field.name == "website" and itemThis:
      #    formfield.queryset = AccessWebsite.objects.filter(access=itemThis.pk)
      #elif db_field.name == "medium" and itemThis:
      #    formfield.queryset = AccessMedium.objects.filter(access=itemThis.pk)
      #elif db_field.name == "nonCommercialUsageOnly" and itemThis:                  # ForeignKey
      #    formfield.queryset = NonCommercialUsageOnly.objects.filter(access=itemThis.pk)
      return formfield


class TotalSizeAdmin(admin.ModelAdmin):
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('size', 'sizeUnit',)}),
                )


class ResourceOrganizationInline(admin.TabularInline):
    model = ResourceCreator.organization.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected ResourceCreator object's identifier
        self.instance = obj
        return super(ResourceOrganizationInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the ResourceCreator model
        if db_field.name == "organization":
            kwargs['queryset'] = Organization.objects.filter(resourcecreator__exact=self.instance)
        return super(ResourceOrganizationInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class ResourcePersonInline(admin.TabularInline):
    model = ResourceCreator.person.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected ResourceCreator object's identifier
        self.instance = obj
        return super(ResourcePersonInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the ResourceCreator model
        if db_field.name == "person":
            kwargs['queryset'] = Person.objects.filter(resourcecreator__exact=self.instance)
        return super(ResourcePersonInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class ResourceCreatorAdmin(admin.ModelAdmin):
    # filter_horizontal = ('organization', 'person',)
    inlines = [ResourceOrganizationInline, ResourcePersonInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ()}),
                )
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1})},
        }


class DocumentationTypeInline(admin.TabularInline):
    model = Documentation.documentationType.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Documentation object's identifier
        self.instance = obj
        return super(DocumentationTypeInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Documentation model
        if db_field.name == "documentationtype" :
            kwargs['queryset'] = DocumentationType.objects.filter(documentation__exact=self.instance)
        return super(DocumentationTypeInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class DocumentationFileInline(admin.TabularInline):
    model = Documentation.fileName.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Documentation object's identifier
        self.instance = obj
        return super(DocumentationFileInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Documentation model
        if db_field.name == "documentationfile" :
            kwargs['queryset'] = DocumentationFile.objects.filter(documentation__exact=self.instance)
        return super(DocumentationFileInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class DocumentationUrlInline(admin.TabularInline):
    model = Documentation.url.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Documentation object's identifier
        self.instance = obj
        return super(DocumentationUrlInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Documentation model
        if db_field.name == "documentationurl":
            kwargs['queryset'] = DocumentationUrl.objects.filter(documentation__exact=self.instance)
        return super(DocumentationUrlInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class DocumentationLanguageInline(admin.TabularInline):
    model = Documentation.language.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Documentation object's identifier
        self.instance = obj
        return super(DocumentationLanguageInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Documentation model
        if db_field.name== "language":
            kwargs['queryset'] = Language.objects.filter(documentation__exact=self.instance)
        return super(DocumentationLanguageInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class DocumentationAdmin(admin.ModelAdmin):
    # filter_horizontal = ('documentationType', 'fileName', 'url', 'language',)
    inlines = [DocumentationTypeInline, DocumentationFileInline,
               DocumentationUrlInline, DocumentationLanguageInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ()}),
                )

 
class ValidationMethodInline(admin.TabularInline):
    model = Validation.method.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Validation object's identifier
        self.instance = obj
        return super(ValidationMethodInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Validation model
        if db_field.name == "validationmethod":
            kwargs['queryset'] = ValidationMethod.objects.filter(validation__exact=self.instance)
        return super(ValidationMethodInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


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
      if db_field.name == "type" and itemThis:                                                # ForeignKey
          formfield.queryset = ValidationType.objects.filter(validation=itemThis.pk)
      #if db_field.name == "method" and itemThis:
      #    formfield.queryset = ValidationMethod.objects.filter(validation=itemThis.pk)
      #elif db_field.name == "type" and itemThis:                                                # ForeignKey
      #    formfield.queryset = ValidationType.objects.filter(validation=itemThis.pk)
      return formfield


class ProjectFunderInline(admin.TabularInline):
    model = Project.funder.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Project object's identifier
        self.instance = obj
        return super(ProjectFunderInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the Project model
        if db_field.name == "projectfunder":
            kwargs['queryset'] = ProjectFunder.objects.filter(project__exact=self.instance)
        return super(ProjectFunderInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


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
        form = super(ProjectAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(ProjectAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if (db_field.name == "URL" ) and itemThis:                                                     # ForeignKey
          formfield.queryset = ProjectUrl.objects.filter(project=itemThis.pk)
      return formfield


class SpeechCorpusRecEnvInline(admin.TabularInline):
    model = SpeechCorpus.recordingEnvironment.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected SpeechCorpus object's identifier
        self.instance = obj
        return super(SpeechCorpusRecEnvInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the SpeechCorpus model
        if db_field.name == "recordingenvironment":
            kwargs['queryset'] = RecordingEnvironment.objects.filter(speechcorpus__exact=self.instance)
        return super(SpeechCorpusRecEnvInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class SpeechCorpusChannelInline(admin.TabularInline):
    model = SpeechCorpus.channel.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected SpeechCorpus object's identifier
        self.instance = obj
        return super(SpeechCorpusChannelInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the SpeechCorpus model
        if db_field.name == "channel":
            kwargs['queryset'] = Channel.objects.filter(speechcorpus__exact=self.instance)
        return super(SpeechCorpusChannelInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class SpeechCorpusConvTypeInline(admin.TabularInline):
    model = SpeechCorpus.conversationalType.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected SpeechCorpus object's identifier
        self.instance = obj
        return super(SpeechCorpusConvTypeInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the SpeechCorpus model
        if db_field.name == "conversationaltype":
            kwargs['queryset'] = ConversationalType.objects.filter(speechcorpus__exact=self.instance)
        return super(SpeechCorpusConvTypeInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class SpeechCorpusRecCondInline(admin.TabularInline):
    model = SpeechCorpus.recordingConditions.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected SpeechCorpus object's identifier
        self.instance = obj
        return super(SpeechCorpusRecCondInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the SpeechCorpus model
        if db_field.name == "recordingcondition":
            kwargs['queryset'] = RecordingCondition.objects.filter(speechcorpus__exact=self.instance)
        return super(SpeechCorpusRecCondInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class SpeechCorpusSocContextInline(admin.TabularInline):
    model = SpeechCorpus.socialContext.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected SpeechCorpus object's identifier
        self.instance = obj
        return super(SpeechCorpusSocContextInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the SpeechCorpus model
        if db_field.name == "socialcontext":
            kwargs['queryset'] = SocialContext.objects.filter(speechcorpus__exact=self.instance)
        return super(SpeechCorpusSocContextInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class SpeechCorpusPlanTypeInline(admin.TabularInline):
    model = SpeechCorpus.planningType.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected SpeechCorpus object's identifier
        self.instance = obj
        return super(SpeechCorpusPlanTypeInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the SpeechCorpus model
        if db_field.name == "planningtype":
            kwargs['queryset'] = PlanningType.objects.filter(speechcorpus__exact=self.instance)
        return super(SpeechCorpusPlanTypeInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class SpeechCorpusInteractivityInline(admin.TabularInline):
    model = SpeechCorpus.interactivity.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected SpeechCorpus object's identifier
        self.instance = obj
        return super(SpeechCorpusInteractivityInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the SpeechCorpus model
        if db_field.name == "interactivity":
            kwargs['queryset'] = Interactivity.objects.filter(speechcorpus__exact=self.instance)
        return super(SpeechCorpusInteractivityInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class SpeechCorpusInvolvementInline(admin.TabularInline):
    model = SpeechCorpus.involvement.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected SpeechCorpus object's identifier
        self.instance = obj
        return super(SpeechCorpusInvolvementInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the SpeechCorpus model
        if db_field.name == "involvement":
            kwargs['queryset'] = Involvement.objects.filter(speechcorpus__exact=self.instance)
        return super(SpeechCorpusInvolvementInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class SpeechCorpusAudienceInline(admin.TabularInline):
    model = SpeechCorpus.audience.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected SpeechCorpus object's identifier
        self.instance = obj
        return super(SpeechCorpusAudienceInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the SpeechCorpus model
        if db_field.name == "audience":
            kwargs['queryset'] = Audience.objects.filter(speechcorpus__exact=self.instance)
        return super(SpeechCorpusAudienceInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class SpeechCorpusAudioFormatInline(admin.TabularInline):
    model = SpeechCorpus.audioFormat.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected SpeechCorpus object's identifier
        self.instance = obj
        return super(SpeechCorpusAudioFormatInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Look for the field's name as it is used in the SpeechCorpus model
        if db_field.name == "audioformat":
            kwargs['queryset'] = AudioFormat.objects.filter(speechcorpus__exact=self.instance)
        return super(SpeechCorpusAudioFormatInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


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

    #def get_form(self, request, obj=None, **kwargs):
    #    # Use one line to explicitly pass on the current object in [obj]
    #    kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
    #    # Standard processing from here
    #    form = super(SpeechCorpusAdmin, self).get_form(request, obj, **kwargs)
    #    return form

    #def formfield_for_dbfield(self, db_field, **kwargs):
    #  itemThis = kwargs.pop('obj', None)
    #  formfield = super(SpeechCorpusAdmin, self).formfield_for_dbfield(db_field, **kwargs)
    #  # Adapt the queryset
    #  if db_field.name == "recordingEnvironment" and itemThis:
    #      formfield.queryset = RecordingEnvironment.objects.filter(speechcorpus=itemThis.pk)
    #  elif db_field.name == "channel" and itemThis:
    #      formfield.queryset = Channel.objects.filter(speechcorpus=itemThis.pk)
    #  elif db_field.name == "conversationalType" and itemThis:
    #      formfield.queryset = ConversationalType.objects.filter(speechcorpus=itemThis.pk)
    #  elif db_field.name == "recordingConditions" and itemThis:
    #      formfield.queryset = RecordingCondition.objects.filter(speechcorpus=itemThis.pk)
    #  elif db_field.name == "socialContext" and itemThis:
    #      formfield.queryset = SocialContext.objects.filter(speechcorpus=itemThis.pk)
    #  elif db_field.name == "planningType" and itemThis:
    #      formfield.queryset = PlanningType.objects.filter(speechcorpus=itemThis.pk)
    #  elif db_field.name == "interactivity" and itemThis:
    #      formfield.queryset = Interactivity.objects.filter(speechcorpus=itemThis.pk)
    #  elif db_field.name == "involvement" and itemThis:
    #      formfield.queryset = Involvement.objects.filter(speechcorpus=itemThis.pk)
    #  elif db_field.name == "audience" and itemThis:
    #      formfield.queryset = Audience.objects.filter(speechcorpus=itemThis.pk)
    #  elif db_field.name == "audioFormat" and itemThis:
    #      formfield.queryset = AudioFormat.objects.filter(speechcorpus=itemThis.pk)
    #  return formfield

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
admin.site.register(AnnotationFormat, AnnotationFormatAdmin)
admin.site.register(MediaFormat)
admin.site.register(Media, MediaAdmin)
admin.site.register(Modality)
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
