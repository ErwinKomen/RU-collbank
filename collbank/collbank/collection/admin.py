from django.contrib import admin
import nested_admin
from django.db.models import Q
from django import forms
from django.core.urlresolvers import resolve
from django.forms import Textarea
from django.shortcuts import redirect
from collbank.collection.models import *
from collbank.settings import APP_PREFIX
from functools import partial
from django.core import serializers
from django.contrib.contenttypes.models import ContentType
import copy  # (1) use python copy
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

def init_choices(obj, sFieldName, sSet):
    if (obj.fields != None and sFieldName in obj.fields):
        obj.fields[sFieldName].choices = build_choice_list(sSet)
        obj.fields[sFieldName].help_text = get_help(sSet)

def get_formfield_qs(modelThis, instanceThis, parentName, bNoEmpty = False):
    """Get the queryset for [modelThis]
    
    Restrict it to the field named [parentName] equalling [instanceThis]
    If [bNoEmpty] is FALSE and the filtered result is empty, then get a list of all
    instances from the [modelThis] that are not bound to [parentName] """

    # Perform the initial filtering of modelThis
    qs = modelThis.objects.filter(**{parentName: instanceThis})
    # Check if the filtered result is empty
    if not bNoEmpty and len(qs) == 0:
        # Get all the instances of [modelThis] that are not bound to [parentName]
        qs = modelThis.objects.filter(**{parentName: None})
    else:
        # Combine the filtered result with all unbound instances of [modelThis]
        # Note: this makes sure that NEWLY created instances are available
        qs = qs | modelThis.objects.filter(**{parentName: None})
    # Return the queryset that we have created
    return qs.select_related()

def copy_item(request=None):
    # Get the parameters from the request object
    sCurrent = request.GET['current']
    sModel = request.GET['model']
    original_pk = request.GET['id']

    # Determine what the model must be
    model = None
    if sModel == "resource":
        # Get the object
        original_obj = Resource.objects.get(id=original_pk)

        # Make a copy of this object and save it
        copy_obj = original_obj.get_copy()
        copy_obj.save()

        # Get the OWNER of the original object
        original_owner = Collection.objects.get(resource__id=original_pk)
        # Add the new Resource to this new owner
        original_owner.resource.add(copy_obj)

    elif sModel == "title":
        # Get the object
        original_obj = Title.objects.get(id=original_pk)

        # Make a copy of this object and save it
        copy_obj = original_obj.get_copy()
        copy_obj.save()

        # Get the OWNER of the original object
        original_owner = Collection.objects.get(title__id=original_pk)
        # Add the new Title to this new owner
        original_owner.title.add(copy_obj)

    elif sModel == "speechcorpus":
        # Get the object
        original_obj = SpeechCorpus.objects.get(id=original_pk)

        # Make a copy of this object and save it
        copy_obj = original_obj.get_copy()
        copy_obj.save()

        # Get the OWNER of the original object
        original_owner = Resource.objects.get(title__id=original_pk)
        # Add the new Title to this new owner
        original_owner.speechCorpus.add(copy_obj)

    elif sModel == "writtencorpus":
        # Get the object
        original_obj = WrittenCorpus.objects.get(id=original_pk)

        # Make a copy of this object and save it
        copy_obj = original_obj.get_copy()
        copy_obj.save()

        # Get the OWNER of the original object
        original_owner = Resource.objects.get(title__id=original_pk)
        # Add the new Title to this new owner
        original_owner.writtenCorpus.add(copy_obj)


    # Now redirect to the 'current' URL
    return redirect(sCurrent)


class TitleAdminForm(forms.ModelForm):
    
    class Meta:
        model = Title
        fields = '__all__'
        widgets = {
            'name': forms.Textarea(attrs={'rows': 1, 'cols': 80})
        }


class TitleInline(nested_admin.NestedTabularInline):
    model = Title # Collection.title.through
    form = TitleAdminForm
    verbose_name = "Collection - title"
    verbose_name_plural = "Collection - titles"
    extra = 0


class OwnerAdminForm(forms.ModelForm):
    
    class Meta:
        model = Owner
        fields = '__all__'
        widgets = {
            'name': forms.Textarea(attrs={'rows': 1, 'cols': 80})
        }


class OwnerInline(nested_admin.NestedTabularInline):
    model = Owner # Collection.owner.through
    form = OwnerAdminForm
    verbose_name = "Collection - owner"
    verbose_name_plural = "Collection - owners"
    extra = 0


class GenreForm(forms.ModelForm):

    class Meta:
        model = Genre
        fields = '__all__' # ['name']

    def __init__(self, *args, **kwargs):
        super(GenreForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', GENRE_NAME)


class GenreAdmin(admin.ModelAdmin):
    form = GenreForm


class GenreInline(nested_admin.NestedTabularInline):
    model = Genre   # Collection.genre.through
    form = GenreForm
    verbose_name = "Collection - genre"
    verbose_name_plural = "Collection - genres"
    extra = 0


class PlaceInline(nested_admin.NestedTabularInline):
    model = City        # GeographicProvenance.place.through
    # form = 
    verbose_name = "Geographic provenance: city"
    verbose_name_plural = "Geographic provenance: cities"
    extra = 0

    #def get_formset(self, request, obj = None, **kwargs):
    #    # Get the currently selected Collection object's identifier
    #    self.instance = obj
    #    return super(PlaceInline, self).get_formset(request, obj, **kwargs)

    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #    formfield = super(PlaceInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #    # Look for the field's name as it is used in the Collection model
    #    if db_field.name == "place":
    #        formfield.queryset = get_formfield_qs(City, self.instance, "geographicprovenance")
    #    return formfield


class GeographicProvenanceForm(forms.ModelForm):

    class Meta:
        model = GeographicProvenance
        # fields = "__all__"  # ['country', 'place']
        fields = ['country']

    def __init__(self, *args, **kwargs):
        super(GeographicProvenanceForm, self).__init__(*args, **kwargs)
        init_choices(self, 'country', PROVENANCE_GEOGRAPHIC_COUNTRY)


class GeographicProvenanceInline(nested_admin.NestedTabularInline):
    model = GeographicProvenance        # Provenance.geographicProvenance.through
    form = GeographicProvenanceForm
    verbose_name = "Provenance: geographic provenance"
    verbose_name_plural = "Provenance: geographic provenances"
    inlines = [PlaceInline]
    extra = 0

    #def get_formset(self, request, obj = None, **kwargs):
    #    # Get the currently selected Collection object's identifier
    #    self.instance = obj
    #    return super(GeographicProvenanceInline, self).get_formset(request, obj, **kwargs)

    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #    formfield = super(GeographicProvenanceInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #    # Look for the field's name as it is used in the Collection model
    #    if db_field.name == "geographicprovenance":
    #       formfield.queryset = get_formfield_qs(GeographicProvenance, self.instance, "provenance")
    #    return formfield


class ProvenanceForm(forms.ModelForm):

    class Meta:
        model = Provenance
        fields = "__all__"


class ProvenanceInline(nested_admin.NestedTabularInline):
    model = Provenance    #  Collection.provenance.through
    form = ProvenanceForm
    verbose_name = "Collection - provenance"
    verbose_name_plural = "Collection - provenances"
    inlines = [GeographicProvenanceInline]
    extra = 0


class CollectionLanguageInline(nested_admin.NestedTabularInline):
    model = CollectionLanguage
    extra = 0

class LanguageInline(nested_admin.NestedTabularInline):
    model = Collection.language.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        return super(LanguageInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super(LanguageInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "language":
            formfield.queryset = get_formfield_qs(Language, self.instance, "collection")
        return formfield


class LanguageDisorderForm(forms.ModelForm):

    class Meta:
        model = LanguageDisorder
        fields = "__all__"


class LanguageDisorderInline(nested_admin.NestedTabularInline):
    model = LanguageDisorder    # Collection.languageDisorder.through
    form = LanguageDisorderForm
    verbose_name = "Collection - language disorder"
    verbose_name_plural = "Collection - language disorders"
    extra = 0


class RelationInline(nested_admin.NestedTabularInline):
    model = Relation    # Collection.relation.through
    verbose_name = "Collection - relation"
    verbose_name_plural = "Collection - relations"
    extra = 0


class DomainForm(forms.ModelForm):
    
    class Meta:
        model = Domain
        fields = '__all__'
        widgets = {
            'name': forms.Textarea(attrs={'rows': 1, 'cols': 80})
        }


class CollectionDomainInline(nested_admin.NestedTabularInline):
    model = Domain  # Collection.domain.through
    form = DomainForm
    verbose_name = "Collection - domain"
    verbose_name_plural = "Collection - domains"
    extra = 0


class TotalCollectionSizeInline(nested_admin.NestedTabularInline):
    model = TotalCollectionSize
    verbose_name = "Collection - total size"
    verbose_name_plural = "Collection - total sizes"
    extra = 0


class PidAdminForm(forms.ModelForm):
    
    class Meta:
        model = PID
        fields = '__all__'
        widgets = {
            'code': forms.Textarea(attrs={'rows': 1})
        }


class PidInline(nested_admin.NestedTabularInline):
    model = PID   # Collection.pid.through
    form = PidAdminForm
    verbose_name = "Collection - PID"
    verbose_name_plural = "Collection - PIDs"
    extra = 0


class OrganizationForm(forms.ModelForm):

    class Meta:
        model = Organization
        fields = '__all__'
        widgets = {
            'name': forms.Textarea(attrs={'rows': 1, 'cols': 80})
        }


class ResourceOrganizationInline(nested_admin.NestedTabularInline):
    model = Organization        # ResourceCreator.organization.through
    form = OrganizationForm
    verbose_name = "Resource creator: organization"
    verbose_name_plural = "Resource creator: organizations"
    extra = 0

class PersonForm(forms.ModelForm):

    class Meta:
        model = Person
        fields = '__all__'
        widgets = {
            'name': forms.Textarea(attrs={'rows': 1, 'cols': 80})
        }


class ResourcePersonInline(nested_admin.NestedTabularInline):
    model = Person  # ResourceCreator.person.through
    form = PersonForm
    verbose_name = "Resource creator: person"
    verbose_name_plural = "Resource creator: persons"
    extra = 0


class ResourceCreatorForm(forms.ModelForm):

    class Meta:
        model = ResourceCreator
        fields = [] # '__all__'


class ResourceCreatorInline(nested_admin.NestedTabularInline):
    model = ResourceCreator   #  Collection.resourceCreator.through
    form = ResourceCreatorForm
    verbose_name = "Collection - resource creator"
    verbose_name_plural = "Collection - resource creators"
    inlines = [ResourceOrganizationInline, ResourcePersonInline]
    extra = 0


class ProjectFunderForm(forms.ModelForm):
    
    class Meta:
        model = ProjectFunder
        fields = '__all__'
        widgets = {
            'name': forms.Textarea(attrs={'rows': 1, 'cols': 100})
        }


class ProjectFunderInline(nested_admin.NestedTabularInline):
    model = ProjectFunder
    form = ProjectFunderForm
    verbose_name = "Project: funder"
    verbose_name_plural = "Project: funders"
    extra = 0


class ProjectAdminForm(forms.ModelForm):
    
    class Meta:
        model = Project
        fields = ['title', 'URL']   # '__all__'
        widgets = {
            'title': forms.Textarea(attrs={'rows': 1})
        }


class ProjectInline(nested_admin.NestedStackedInline):
    model = Project   # Collection.project.through
    form = ProjectAdminForm
    inlines = [ProjectFunderInline]
    verbose_name = "Collection - project"
    verbose_name_plural = "Collection - projects"
    extra = 0


class ModalityForm(forms.ModelForm):

    class Meta:
        model = Modality
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ModalityForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', RESOURCE_MODALITY)

            
class ModalityAdmin(admin.ModelAdmin):
    form = ModalityForm


# class ModalityInline(admin.TabularInline):
class ModalityInline(nested_admin.NestedTabularInline):
    model = Modality #   Resource.modality.through
    form = ModalityForm
    extra = 0


class RecordingEnvironmentForm(forms.ModelForm):

    class Meta:
        model = RecordingEnvironment
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(RecordingEnvironmentForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', SPEECHCORPUS_RECORDINGENVIRONMENT)

class RecordingEnvironmentAdmin(admin.ModelAdmin):
    form = RecordingEnvironmentForm


class ResourceRecEnvInline(nested_admin.NestedTabularInline):
    model = RecordingEnvironment # Resource.recordingEnvironment.through
    form = RecordingEnvironmentForm
    extra = 0


class ProvenanceAdmin(admin.ModelAdmin):
    inlines = [GeographicProvenanceInline]
    fieldsets = ( ('Searchable', {'fields': ('temporalProvenance',)}),
                  ('Other',      {'fields': ()}),
                )

    def get_form(self, request, obj=None, **kwargs):
        # Get the currently selected Collection object's identifier
        self.instance = obj
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(ProvenanceAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(ProvenanceAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "temporalProvenance":                                  # ForeignKey
          formfield.queryset = get_formfield_qs(TemporalProvenance, self.instance, "provenance")
      return formfield


class TemporalProvenanceAdmin(nested_admin.NestedModelAdmin):
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('startYear', 'endYear',)}),
                )


#class PlaceInline(nested_admin.NestedTabularInline):
#    model = GeographicProvenance.place.through
#    extra = 0

#    def get_formset(self, request, obj = None, **kwargs):
#        # Get the currently selected Collection object's identifier
#        self.instance = obj
#        return super(PlaceInline, self).get_formset(request, obj, **kwargs)

#    def formfield_for_foreignkey(self, db_field, request, **kwargs):
#        formfield = super(PlaceInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
#        # Look for the field's name as it is used in the Collection model
#        if db_field.name == "place":
#            formfield.queryset = get_formfield_qs(City, self.instance, "geographicprovenance")
#        return formfield


#class GeographicProvenanceForm(forms.ModelForm):

#    class Meta:
#        model = GeographicProvenance
#        fields = ['country', 'place']

#    def __init__(self, *args, **kwargs):
#        super(GeographicProvenanceForm, self).__init__(*args, **kwargs)
#        init_choices(self, 'country', PROVENANCE_GEOGRAPHIC_COUNTRY)


class GeographicProvenanceAdmin(admin.ModelAdmin):
    inlines = [PlaceInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('country', )}),
                )
    form = GeographicProvenanceForm


class AnnotationFormatInline(nested_admin.NestedTabularInline):
    model = Annotation.formatAnn.through
    extra = 0

    def get_formset(self, request, obj = None, **kwargs):
        # Get the currently selected Annotation object's identifier
        self.instance = obj
        return super(AnnotationFormatInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super(AnnotationFormatInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
        # Look for the field's name as it is used in the Collection model
        if db_field.name == "annotationformat":
            formfield.queryset = get_formfield_qs(AnnotationFormat, self.instance, "annotation")
        return formfield


class AnnotationFormatForm(forms.ModelForm):
    model = AnnotationFormat
    fields = ['name']

    def __init__(self, *args, **kwargs):
        super(AnnotationFormatForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', ANNOTATION_FORMAT)


class AnnotationFormatAdmin(admin.ModelAdmin):
    form = AnnotationFormatForm


class AnnotationForm(forms.ModelForm):

    class Meta:
        model = Annotation
        fields = ['type', 'mode', 'format']
        widgets = {
            'type': forms.Select(attrs={'width': 30}),
            'mode': forms.Select(attrs={'width': 30}),
            'format': forms.Select(attrs={'width': 30})
        }

    def __init__(self, *args, **kwargs):
        super(AnnotationForm, self).__init__(*args, **kwargs)
        init_choices(self, 'type', ANNOTATION_TYPE)
        init_choices(self, 'mode', ANNOTATION_MODE)


class AnnotationAdmin(admin.ModelAdmin):
    inlines = [AnnotationFormatInline]
    fieldsets = ( ('Searchable', {'fields': ('type',) }),
                  ('Other',      {'fields': ('mode', )}),
                )
    form = AnnotationForm

    def get_form(self, request, obj=None, **kwargs):
        # Get the currently selected Annotation object's identifier
        self.instance = obj
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
          formfield.queryset = AnnotationFormat.objects.filter(annotation=itemThis.pk).select_related()
      elif db_field.name == "type" and itemThis and itemThis.formatAnn.count() == 0:
          # Create a new format object
          formatNew = AnnotationFormat.objects.create(name = itemThis.format)
          # Add it to this model
          itemThis.formatAnn.add(formatNew)
      return formfield


class AnnotationInline(nested_admin.NestedTabularInline):
    model = Annotation      #  Resource.annotation.through
    form = AnnotationForm
    extra = 0

    #def get_formset(self, request, obj = None, **kwargs):
    #    # Get the currently selected Collection object's identifier
    #    self.instance = obj
    #    return super(AnnotationInline, self).get_formset(request, obj, **kwargs)

    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #    formfield = super(AnnotationInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #    # Look for the field's name as it is used in the Collection model
    #    if db_field.name == "annotation":
    #        formfield.queryset = get_formfield_qs(Annotation, self.instance, "resource")
    #    return formfield



class CharacterEncodingForm(forms.ModelForm):

    class Meta:
        model = CharacterEncoding
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(CharacterEncodingForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', CHARACTERENCODING)


class CharacterEncodingAdmin(admin.ModelAdmin):
    form = CharacterEncodingForm


class LingualityTypeForm(forms.ModelForm):

    class Meta:
        model = LingualityType
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(LingualityTypeForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', LINGUALITY_TYPE)


class LingualityTypeAdmin(admin.ModelAdmin):
    form = LingualityTypeForm


class LingualityNativenessForm(forms.ModelForm):

    class Meta:
        model = LingualityNativeness
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(LingualityNativenessForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', LINGUALITY_NATIVENESS)


class LingualityNativenessAdmin(admin.ModelAdmin):
    form = LingualityNativenessForm


class LingualityAgeGroupForm(forms.ModelForm):

    class Meta:
        model = LingualityAgeGroup
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(LingualityAgeGroupForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', LINGUALITY_AGEGROUP)


class LingualityAgeGroupAdmin(admin.ModelAdmin):
    form = LingualityAgeGroupForm


class LingualityStatusForm(forms.ModelForm):

    class Meta:
        model = LingualityStatus
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(LingualityStatusForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', LINGUALITY_STATUS)


class LingualityStatusAdmin(admin.ModelAdmin):
    form = LingualityStatusForm


class LingualityVariantForm(forms.ModelForm):

    class Meta:
        model = LingualityVariant
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(LingualityVariantForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', LINGUALITY_VARIANT)


class LingualityVariantAdmin(admin.ModelAdmin):
    form = LingualityVariantForm


class MultilingualityTypeForm(forms.ModelForm):

    class Meta:
        model = MultilingualityType
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(MultilingualityTypeForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', LINGUALITY_MULTI)


class MultilingualityTypeAdmin(admin.ModelAdmin):
    form = MultilingualityTypeForm


class TotalSizeForm(forms.ModelForm):

    class Meta:
        model = TotalSize
        fields = '__all__'
        widgets = {
            'size': forms. TextInput (attrs={'width': 30}),
            'sizeUnit': forms. TextInput (attrs={'width': 30})
        }


class ResourceSizeInline(nested_admin.NestedTabularInline):
    model = TotalSize   # Resource.totalSize.through
    form = TotalSizeForm
    extra = 0

    #def get_formset(self, request, obj = None, **kwargs):
    #    # Get the currently selected Collection object's identifier
    #    self.instance = obj
    #    return super(ResourceSizeInline, self).get_formset(request, obj, **kwargs)

    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #    formfield = super(ResourceSizeInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #    # Look for the field's name as it is used in the Collection model
    #    if db_field.name == "totalsize":
    #        formfield.queryset = get_formfield_qs(TotalSize, self.instance, "resource")
    #    return formfield


class MediaFormatInline(nested_admin.NestedTabularInline):
    model = MediaFormat
    extra = 0


class MediaForm(forms.ModelForm):

    class Meta:
        model = Media
        fields = "__all__"
        widgets = {
            'name': forms. TextInput (attrs={'width': 30})
        }


class MediaInline(nested_admin.NestedTabularInline):
    model = Media       # Resource.medias.through
    form = MediaForm
    inlines = [MediaFormatInline]
    extra = 0

    #def get_formset(self, request, obj = None, **kwargs):
    #    # Get the currently selected Collection object's identifier
    #    self.instance = obj
    #    return super(MediaInline, self).get_formset(request, obj, **kwargs)

    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #    formfield = super(MediaInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #    # Look for the field's name as it is used in the Collection model
    #    if db_field.name == "medias":
    #        formfield.queryset = get_formfield_qs(Media, self.instance, "resource")
    #    return formfield


class ResourceForm(forms.ModelForm):
    # model = Resource
    current_dctype = ''
    chosen_type = '0'

    def __init__(self, *args, **kwargs):
        super(ResourceForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Resource
        fields = ['type', 'DCtype', 'subtype', 'description']
        # fields = ['type', 'DCtype', 'subtype', 'modality', 'medias', 'description']
        # NOT NEEDED: widgets = { 'subtype': forms.Select }

    def save(self, *args, **kwargs):
        """Override the default saving"""
        # Set the value of 'type'
        self.instance.type = self.chosen_type
        # Perform the actual saving
        return super(ResourceForm, self).save(*args, **kwargs)



class AudienceForm(forms.ModelForm):

    class Meta:
        model = Audience
        fields = ['name']
        widgets = {
            'name': forms.Select(attrs={'width': 30})
        }

    def __init__(self, *args, **kwargs):
        super(AudienceForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', SPEECHCORPUS_AUDIENCE)


class AudienceAdmin(admin.ModelAdmin):
    form = AudienceForm


class ChannelForm(forms.ModelForm):

    class Meta:
        model = Channel
        fields = ['name']
        widgets = {
            'name': forms.Select(attrs={'width': 30})
        }

    def __init__(self, *args, **kwargs):
        super(ChannelForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', SPEECHCORPUS_CHANNEL)


class ChannelAdmin(admin.ModelAdmin):
    form = ChannelForm

class ResourceChannelInline(nested_admin.NestedTabularInline):
    model = Channel     # Resource.channel.through
    form = ChannelForm
    extra = 0

    #def get_formset(self, request, obj = None, **kwargs):
    #    # Get the currently selected SpeechCorpus object's identifier
    #    self.instance = obj
    #    return super(ResourceChannelInline, self).get_formset(request, obj, **kwargs)

    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #    formfield = super(ResourceChannelInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #    # Look for the field's name as it is used in the SpeechCorpus model
    #    if db_field.name == "channel":
    #        formfield.queryset = get_formfield_qs(Channel, self.instance, "resource")
    #    return formfield


class RecordingConditionForm(forms.ModelForm):

    class Meta:
        model = RecordingCondition
        fields = ['name']
        widgets = {
            'name': forms.Textarea(attrs={'rows': 1, 'cols': 80})
            # 'name': forms. TextInput (attrs={'width': 30})
        }


class ResourceRecCondInline(nested_admin.NestedTabularInline):
    model = RecordingCondition  # Resource.recordingConditions.through
    form = RecordingConditionForm
    extra = 0

    #def get_formset(self, request, obj = None, **kwargs):
    #    # Get the currently selected SpeechCorpus object's identifier
    #    self.instance = obj
    #    return super(ResourceRecCondInline, self).get_formset(request, obj, **kwargs)

    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #    formfield = super(ResourceRecCondInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #    # Look for the field's name as it is used in the SpeechCorpus model
    #    if db_field.name == "recordingcondition":
    #        formfield.queryset = get_formfield_qs(RecordingCondition, self.instance, "resource")
    #    return formfield


class SocialContextForm(forms.ModelForm):

    class Meta:
        model = SocialContext
        fields = ['name']
        widgets = {
            'name': forms.Select(attrs={'width': 30})
        }

    def __init__(self, *args, **kwargs):
        super(SocialContextForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', SPEECHCORPUS_SOCIALCONTEXT)


class SocialContextAdmin(admin.ModelAdmin):
    form = SocialContextForm


class ResourceSocContextInline(nested_admin.NestedTabularInline):
    model = SocialContext   # Resource.socialContext.through
    form = SocialContextForm
    extra = 0

    #def get_formset(self, request, obj = None, **kwargs):
    #    # Get the currently selected SpeechCorpus object's identifier
    #    self.instance = obj
    #    return super(ResourceSocContextInline, self).get_formset(request, obj, **kwargs)

    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #    formfield = super(ResourceSocContextInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #    # Look for the field's name as it is used in the SpeechCorpus model
    #    if db_field.name == "socialcontext":
    #        formfield.queryset = get_formfield_qs(SocialContext, self.instance, "resource")
    #    return formfield


class PlanningTypeForm(forms.ModelForm):

    class Meta:
        model = PlanningType
        fields = ['name']
        widgets = {
            'name': forms.Select(attrs={'width': 30})
        }

    def __init__(self, *args, **kwargs):
        super(PlanningTypeForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', SPEECHCORPUS_PLANNINGTYPE)


class PlanningTypeAdmin(admin.ModelAdmin):
    form = PlanningTypeForm


class ResourcePlanTypeInline(nested_admin.NestedTabularInline):
    model = PlanningType        # Resource.planningType.through
    form = PlanningTypeForm
    extra = 0

    #def get_formset(self, request, obj = None, **kwargs):
    #    # Get the currently selected SpeechCorpus object's identifier
    #    self.instance = obj
    #    return super(ResourcePlanTypeInline, self).get_formset(request, obj, **kwargs)

    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #    formfield = super(ResourcePlanTypeInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #    # Look for the field's name as it is used in the SpeechCorpus model
    #    if db_field.name == "planningtype":
    #        formfield.queryset = get_formfield_qs(PlanningType, self.instance, "resource")
    #    return formfield


class InteractivityForm(forms.ModelForm):

    class Meta:
        model = Interactivity
        fields = ['name']
        widgets = {
            'name': forms.Select(attrs={'width': 30})
        }

    def __init__(self, *args, **kwargs):
        super(InteractivityForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', SPEECHCORPUS_INTERACTIVITY)


class InteractivityAdmin(admin.ModelAdmin):
    form = InteractivityForm


class ResourceInteractivityInline(nested_admin.NestedTabularInline):
    model = Interactivity       # Resource.interactivity.through
    form = InteractivityForm
    extra = 0

    #def get_formset(self, request, obj = None, **kwargs):
    #    # Get the currently selected SpeechCorpus object's identifier
    #    self.instance = obj
    #    return super(ResourceInteractivityInline, self).get_formset(request, obj, **kwargs)

    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #    formfield = super(ResourceInteractivityInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #    # Look for the field's name as it is used in the SpeechCorpus model
    #    if db_field.name == "interactivity":
    #        formfield.queryset = get_formfield_qs(Interactivity, self.instance, "resource")
    #    return formfield


class InvolvementForm(forms.ModelForm):

    class Meta:
        model = Involvement
        fields = ['name']
        widgets = {
            'name': forms.Select(attrs={'width': 30})
        }

    def __init__(self, *args, **kwargs):
        super(InvolvementForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', SPEECHCORPUS_INVOLVEMENT)


class InvolvementAdmin(admin.ModelAdmin):
    form = InvolvementForm


class ResourceInvolvementInline(nested_admin.NestedTabularInline):
    model = Involvement     # Resource.involvement.through
    form = InvolvementForm
    extra = 0

    #def get_formset(self, request, obj = None, **kwargs):
    #    # Get the currently selected SpeechCorpus object's identifier
    #    self.instance = obj
    #    return super(ResourceInvolvementInline, self).get_formset(request, obj, **kwargs)

    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #    formfield = super(ResourceInvolvementInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #    # Look for the field's name as it is used in the SpeechCorpus model
    #    if db_field.name == "involvement":
    #        formfield.queryset = get_formfield_qs(Involvement, self.instance, "resource")
    #    return formfield


class ResourceAudienceInline(nested_admin.NestedTabularInline):
    model = Audience        #  Resource.audience.through
    form = AudienceForm
    extra = 0

    #def get_formset(self, request, obj = None, **kwargs):
    #    # Get the currently selected Resource object's identifier
    #    self.instance = obj
    #    return super(ResourceAudienceInline, self).get_formset(request, obj, **kwargs)

    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #    formfield = super(ResourceAudienceInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #    # Look for the field's name as it is used in the SpeechCorpus model
    #    if db_field.name == "audience":
    #        formfield.queryset = get_formfield_qs(Audience, self.instance, "resource")
    #    return formfield


class ResourceAdminForm(forms.ModelForm):

    class Meta:
        model = Resource
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 1})
        }


class ResourceInline(nested_admin.NestedStackedInline):
    model = Resource
    form = ResourceAdminForm
    exclude = ['type', 'recordingEnvironment']
    inlines = [ModalityInline, ResourceRecEnvInline, ResourceRecCondInline,
               ResourceChannelInline, ResourceSocContextInline, ResourcePlanTypeInline,
               ResourceInteractivityInline, ResourceInvolvementInline,
               ResourceAudienceInline, ResourceSizeInline, AnnotationInline,
               MediaInline]
    fieldsets = ( ('Searchable', {'fields': ('DCtype', 'subtype', 'speechCorpus',)}),
                  ('Other',      {'fields': ('description', 'writtenCorpus',)}),
                )
    extra = 0


class ResourceAdmin(admin.ModelAdmin):
    form = ResourceForm
    save_on_top = True      # Also allow the save buttons on top

    # filter_horizontal = ('annotation','totalSize',)
    inlines = [MediaInline, AnnotationInline, ResourceSizeInline, ModalityInline,
               ResourceRecEnvInline, ResourceChannelInline, ResourceRecCondInline, 
               ResourceSocContextInline, ResourcePlanTypeInline,
               ResourceInteractivityInline, ResourceInvolvementInline,
               ResourceAudienceInline ]
    fieldsets = ( ('Searchable', {'fields': ('DCtype', 'subtype', 'speechCorpus',)}),
                  ('Other',      {'fields': ('description', 'writtenCorpus',)}),
                )
    #formfield_overrides = {
    #    models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols':30})},
    #    }
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 2})},
        }
    current_dctype = ''

    class Media:
        js = ('/'+APP_PREFIX+'static/collection/scripts/collbank.js',)


    def get_form(self, request, obj=None, **kwargs):
        # Get the instance before the form gets generated
        self.instance = obj
        self.coll = Collection.objects.filter(resource=obj).select_related()
        self.chosen_type = ''
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(ResourceAdmin, self).get_form(request, obj, **kwargs)

        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
        arBack = None
        if "request" in kwargs:
            arBack = kwargs["request"].POST
        itemThis = kwargs.pop('obj', None)
        formfield = super(ResourceAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        # Adapt the queryset
        if db_field.name == "medias":
            formfield.queryset = get_formfield_qs(Media, self.instance, "resource")
        elif db_field.name == "type":
            formfield.initial = self.form.chosen_type
        elif db_field.name == "DCtype":
            # Get the DCtype list
            arDCtype = db_field.choices
            # Take note of the selected DC type
            if "DCtype" in arBack:
                # Get the selected element from the item
                sDCtype = get_tuple_value(arDCtype, arBack["DCtype"])
                self.current_dctype = sDCtype
                self.form.current_dctype = sDCtype
                # self.form.base_fields["type"] = arBack["DCtype"]
                self.form.chosen_type = arBack["DCtype"]
                formfield.initial = arBack["DCtype"]
            elif itemThis != None and itemThis.DCtype != None and  itemThis.DCtype != '' and itemThis.DCtype != '-':
                # Get the element from this list
                sDCtype = get_tuple_value(arDCtype, itemThis.DCtype)
                self.current_dctype = sDCtype
                self.form.current_dctype = sDCtype
        elif db_field.name == "subtype":
            arChoices = db_field.choices
            if "subtype" in arBack:
                # Note which DCtype was selected
                # ERWIN db_field.choices = build_choice_list(RESOURCE_TYPE, 'after', self.current_dctype)
                formfield.initial = arBack["subtype"]
                self.form.chosen_type = arBack["subtype"]
            elif itemThis != None and itemThis.subtype != '' and itemThis.subtype != '-':
                # Note which DCtype was selected
                # ERWIN db_field.choices = build_choice_list(RESOURCE_TYPE, 'after', self.current_dctype)
                formfield.initial = formfield.initial
        elif db_field.name == "modality" :                         # M2M
            formfield.queryset = get_formfield_qs(Modality, self.instance, "resource")
        elif db_field.name == "annotation" :                       # M2M
            formfield.queryset = get_formfield_qs(Annotation, self.instance, "resource")
        elif db_field.name == "totalSize" :                        # M2M
            formfield.queryset = get_formfield_qs(TotalSize, self.instance, "resource")
        return formfield

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super(ResourceAdmin, self).formfield_for_foreignkey(db_field, **kwargs)
        if db_field.name == "speechCorpus":                            # ForeignKey
          qs = get_formfield_qs(SpeechCorpus, self.instance, "resource", True)
          qs2 = get_formfield_qs(SpeechCorpus, self.coll, "collection", True)
          qsCombi = SpeechCorpus.objects.filter(Q(id__in=qs) | Q(id__in=qs2)).distinct().select_related()
          formfield.queryset = qsCombi
        elif db_field.name == "writtenCorpus":                         # ForeignKey
          qs = get_formfield_qs(WrittenCorpus, self.instance, "resource", True)
          qs2 = get_formfield_qs(WrittenCorpus, self.coll, "collection", True)
          qsCombi = WrittenCorpus.objects.filter(Q(id__in=qs) | Q(id__in=qs2)).distinct().select_related()
          formfield.queryset = qsCombi
        return formfield


class MediaFormatForm(forms.ModelForm):

    class Meta:
        model = MediaFormat
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(MediaFormatForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', MEDIA_FORMAT)


class FormatInline(nested_admin.NestedTabularInline):
    model = MediaFormat   #  Media.format.through
    form = MediaFormatForm
    extra = 0

    #def get_formset(self, request, obj = None, **kwargs):
    #    # Get the currently selected Collection object's identifier
    #    self.instance = obj
    #    return super(FormatInline, self).get_formset(request, obj, **kwargs)

    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #    formfield = super(FormatInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #    # Look for the field's name as it is used in the Collection model
    #    if db_field.name == "mediaformat":
    #        formfield.queryset = get_formfield_qs(MediaFormat, self.instance, "media")
    #    return formfield


class MediaFormatAdmin(nested_admin.NestedModelAdmin):
    form = MediaFormatForm


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
        init_choices(self, 'name', "language.name")


class LanguageAdmin(admin.ModelAdmin):
    form = LanguageForm
    

class AccessAvailabilityForm(forms.ModelForm):

    class Meta:
        model = AccessAvailability
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(AccessAvailabilityForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', "access.availability")


class AccessAvailabilityAdmin(admin.ModelAdmin):
    form = AccessAvailabilityForm


class AccessMediumForm(forms.ModelForm):

    class Meta:
        model = AccessMedium
        fields = ['format']

    def __init__(self, *args, **kwargs):
        super(AccessMediumForm, self).__init__(*args, **kwargs)
        init_choices(self, 'format', "access.medium.format")


class AccessMediumAdmin(admin.ModelAdmin):
    form = AccessMediumForm


class NonCommercialUsageOnlyForm(forms.ModelForm):

    class Meta:
        model = NonCommercialUsageOnly
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(NonCommercialUsageOnlyForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', "access.nonCommercialUsageOnly")


class NonCommercialUsageOnlyAdmin(admin.ModelAdmin):
    form = NonCommercialUsageOnlyForm
    

class DocumentationTypeForm(forms.ModelForm):

    class Meta:
        model = DocumentationType
        fields = ['format']

    def __init__(self, *args, **kwargs):
        super(DocumentationTypeForm, self).__init__(*args, **kwargs)
        init_choices(self, 'format', "documentation.type")


class DocumentationTypeAdmin(admin.ModelAdmin):
    form = DocumentationTypeForm


class AudioFormatForm(forms.ModelForm):

    class Meta:
        model = AudioFormat
        fields = ['speechCoding', 'samplingFrequency', 'compression', 'bitResolution']
        widgets = {
            'speechCoding': forms. TextInput (attrs={'width': 30}),
            'samplingFrequency': forms. TextInput (attrs={'width': 30}),
            'compression': forms. TextInput (attrs={'width': 30}),
            'bitResolution': forms. TextInput (attrs={'width': 30})
        }

    def __init__(self, *args, **kwargs):
        super(AudioFormatForm, self).__init__(*args, **kwargs)
        init_choices(self, 'speechCoding', "audioformat.speechcoding")


class AudioFormatAdmin(admin.ModelAdmin):
    form = AudioFormatForm


class DomainInline(nested_admin.NestedTabularInline):
    model = Domain   #  Domain.name.through
    extra = 0


class DomainAdmin(admin.ModelAdmin):
    # filter_horizontal = ('name',)
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ()}),
                )


class LingualityTypeInline(nested_admin.NestedTabularInline):
    model = LingualityType
    extra = 0


class LingualityNativenessInline(nested_admin.NestedTabularInline):
    model = LingualityNativeness
    extra = 0


class LingualityAgeGroupInline(nested_admin.NestedTabularInline):
    model = LingualityAgeGroup
    extra = 0


class LingualityStatusInline(nested_admin.NestedTabularInline):
    model = LingualityStatus
    extra = 0


class LingualityVariantInline(nested_admin.NestedTabularInline):
    model = LingualityVariant
    extra = 0


class MultiLingualityTypeInline(nested_admin.NestedTabularInline):
    model = MultilingualityType
    extra = 0


class LingualityAdmin(nested_admin.NestedModelAdmin):
    # filter_horizontal = ('lingualityType', 'lingualityNativeness', 'lingualityAgeGroup', 'lingualityStatus', 'lingualityVariant', 'multilingualityType', )
    inlines = [LingualityTypeInline, LingualityNativenessInline, 
               LingualityAgeGroupInline, LingualityStatusInline,
               LingualityVariantInline, MultiLingualityTypeInline]
    
    # list_display = ['id', 'linguality_types']
    fieldsets = ( ('Searchable', {'fields': () }),
                  ('Other',      {'fields': () }),
                )

    def get_form(self, request, obj=None, **kwargs):
        self.instance = obj
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(LingualityAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
        itemThis = kwargs.pop('obj', None)
        formfield = super(LingualityAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        # Adapt the queryset
        if db_field.name == "lingualityType":
            formfield.queryset = get_formfield_qs(LingualityType, self.instance, "linguality")
        elif db_field.name == "lingualityNativeness":
            formfield.queryset = get_formfield_qs(LingualityNativeness, self.instance, "linguality")
        elif db_field.name == "lingualityAgeGroup":
            formfield.queryset = get_formfield_qs(LingualityAgeGroup, self.instance, "linguality")
        elif db_field.name == "lingualityStatus":
            formfield.queryset = get_formfield_qs(LingualityStatus, self.instance, "linguality")
        elif db_field.name == "lingualityVariant":
            formfield.queryset = get_formfield_qs(LingualityVariant, self.instance, "linguality")
        elif db_field.name == "multilingualityType":
            formfield.queryset = get_formfield_qs(MultilingualityType, self.instance, "linguality")
        return formfield

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super(LingualityAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
        itemThis = kwargs.pop('obj', None)
        # Look for the field's name as it is used in the Linguality model
        if db_field.name == "lingualityType":
            # formfield.queryset = MultilingualityType.objects.filter(linguality__exact=self.instance)
            formfield.queryset = get_formfield_qs(LingualityType, self.instance, "linguality")
        return formfield
    

class AccessAvailabilityInline(nested_admin.NestedTabularInline):
    model = AccessAvailability
    form = AccessAvailabilityForm
    extra = 0


class LicenseNameForm(forms.ModelForm):

    class Meta:
        model = LicenseName
        fields = ['name']
        widgets = {
            'name': forms.Textarea(attrs={'rows': 1, 'cols': 100})
        }


class AccessLicenseNameInline(nested_admin.NestedTabularInline):
    model = LicenseName
    form = LicenseNameForm
    extra = 0


class LicenseUrlForm(forms.ModelForm):

    class Meta:
        model = LicenseUrl
        fields = ['name']


class AccessLicenseUrlInline(nested_admin.NestedTabularInline):
    model = LicenseUrl
    form = LicenseUrlForm
    extra = 0


class AccessContactForm(forms.ModelForm):

    class Meta:
        model = AccessContact
        fields = ['person', 'address', 'email']
        widgets = {
            'person': forms.TextInput(attrs={'size': 25}),
            'address': forms.TextInput(attrs={'size': 60})
        }


class AccessContactInline(nested_admin.NestedTabularInline):
    model = AccessContact
    form = AccessContactForm
    extra = 0


class AccessWebsiteForm(forms.ModelForm):

    class Meta:
        model = AccessWebsite
        fields = ['name']


class AccessWebsiteInline(nested_admin.NestedTabularInline):
    model = AccessWebsite
    form = AccessWebsiteForm
    extra = 0


class AccessMediumInline(nested_admin.NestedTabularInline):
    model = AccessMedium
    form = AccessMediumForm
    extra = 0


class AccessAdmin(nested_admin.NestedModelAdmin):
    # filter_horizontal = ('availability', 'licenseName', 'licenseUrl', 'contact', 'website', 'medium',)
    inlines = [AccessAvailabilityInline, AccessLicenseNameInline,
               AccessLicenseUrlInline, AccessContactInline,
               AccessWebsiteInline, AccessMediumInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
#                 ('Other',      {'fields': ('name', 'availability', 'licenseName', 'licenseUrl', 'nonCommercialUsageOnly', 'contact', 'website', 'ISBN', 'ISLRN', 'medium',)}),
                  ('Other',      {'fields': ('name', 'nonCommercialUsageOnly', 'ISBN', 'ISLRN', )}),
                )

    list_display = ['id', 'name', 'nonCommercialUsageOnly', 'ISBN', 'ISLRN']
    search_fields = ['name']

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'cols':30})},
        }

    def get_form(self, request, obj=None, **kwargs):
        self.instance = obj
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(AccessAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(AccessAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "nonCommercialUsageOnly":                 # ForeignKey
          formfield.queryset = get_formfield_qs(NonCommercialUsageOnly, self.instance, "access")
      return formfield


class TotalSizeAdmin(admin.ModelAdmin):
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('size', 'sizeUnit',)}),
                )




class ResourceCreatorAdmin(admin.ModelAdmin):
    # filter_horizontal = ('organization', 'person',)
    inlines = [ResourceOrganizationInline, ResourcePersonInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ()}),
                )
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'cols':30})},
        }


class DocumentationTypeInline(nested_admin.NestedTabularInline):
    model = DocumentationType
    form = DocumentationTypeForm
    extra = 0


class DocumentationFileForm(forms.ModelForm):

    class Meta:
        model = DocumentationFile
        fields = ['name']
        widgets = {
            'name': forms.Textarea(attrs={'rows': 1, 'cols': 100})
        }


class DocumentationFileInline(nested_admin.NestedTabularInline):
    model = DocumentationFile
    form = DocumentationFileForm
    extra = 0


class DocumentationUrlForm(forms.ModelForm):

    class Meta:
        model = DocumentationUrl
        fields = ['name']
        #widgets = {
        #    'name': forms.Textarea(attrs={'rows': 1})
        #}


class DocumentationUrlInline(nested_admin.NestedTabularInline):
    model = DocumentationUrl
    form = DocumentationUrlForm
    extra = 0


class DocumentationLanguageInline(nested_admin.NestedTabularInline):
    model = DocumentationLanguage   # Documentation.language.through
    extra = 0

    #def get_formset(self, request, obj = None, **kwargs):
    #    # Get the currently selected Documentation object's identifier
    #    self.instance = obj
    #    return super(DocumentationLanguageInline, self).get_formset(request, obj, **kwargs)

    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #    formfield = super(DocumentationLanguageInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #    # Look for the field's name as it is used in the Documentation model
    #    if db_field.name== "language":
    #        formfield.queryset = get_formfield_qs(Language, self.instance, "documentation")
    #    return formfield


class DocumentationAdmin(nested_admin.NestedModelAdmin):
    # filter_horizontal = ('documentationType', 'fileName', 'url', 'language',)
    inlines = [DocumentationTypeInline, DocumentationFileInline,
               DocumentationUrlInline, DocumentationLanguageInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ()}),
                )

 
class ValidationMethodInline(nested_admin.NestedTabularInline):
    model = ValidationMethod
    extra = 0


class ValidationAdmin(nested_admin.NestedModelAdmin):
    # filter_horizontal = ('method',)
    inlines = [ValidationMethodInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('type', )}),
                )

    def get_form(self, request, obj=None, **kwargs):
        self.instance = obj
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(ValidationAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
      itemThis = kwargs.pop('obj', None)
      formfield = super(ValidationAdmin, self).formfield_for_dbfield(db_field, **kwargs)
      # Adapt the queryset
      if db_field.name == "type":                                                # ForeignKey
          formfield.queryset = get_formfield_qs(ValidationType, self.instance, "validation")
      return formfield


class ProjectAdmin(admin.ModelAdmin):
    # filter_horizontal = ('funder',)
    inlines = [ProjectFunderInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('title', 'URL',)}),
                )
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'cols':30})},
        }

    def get_form(self, request, obj=None, **kwargs):
        self.instance = obj
        # Use one line to explicitly pass on the current object in [obj]
        kwargs['formfield_callback'] = partial(self.formfield_for_dbfield, request=request, obj=obj)
        # Standard processing from here
        form = super(ProjectAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_dbfield(self, db_field, **kwargs):
        itemThis = kwargs.pop('obj', None)
        formfield = super(ProjectAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        # Adapt the queryset
        if (db_field.name == "URL" ):                                                     # ForeignKey
            formfield.queryset = get_formfield_qs(ProjectUrl, self.instance, "project")
        return formfield




class SpeechCorpusConvTypeInline(nested_admin.NestedTabularInline):
    model = ConversationalType
    extra = 0


class ConversationalTypeForm(forms.ModelForm):

    class Meta:
        model = ConversationalType
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(ConversationalTypeForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', SPEECHCORPUS_CONVERSATIONALTYPE)


class ConversationalTypeAdmin(admin.ModelAdmin):
    form = ConversationalTypeForm


class SpeechCorpusAudioFormatInline(nested_admin.NestedTabularInline):
    model = AudioFormat
    form = AudioFormatForm
    extra = 0


class SpeechCorpusAdmin(nested_admin.NestedModelAdmin):
    # filter_horizontal = ('recordingEnvironment', 'channel', 'conversationalType', 'recordingConditions', 
    #                      'socialContext', 'planningType', 'interactivity', 'involvement', 'audience', 'audioFormat')

    inlines = [SpeechCorpusConvTypeInline, SpeechCorpusAudioFormatInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('durationOfEffectiveSpeech', 'durationOfFullDatabase', 'numberOfSpeakers', 
                                             'speakerDemographics')}),
                )
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'cols':30})},
        }


class CharacterEncodingInline(nested_admin.NestedTabularInline):
    model = CharacterEncoding       # WrittenCorpus.characterEncoding.through
    form = CharacterEncodingForm
    extra = 0


class WrittenCorpusAdmin(nested_admin.NestedModelAdmin):
    inlines = [CharacterEncodingInline]
    fieldsets = ( ('Searchable', {'fields': ()}),
                  ('Other',      {'fields': ('numberOfAuthors', 'authorDemographics')}),
                )
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'cols':30})},
        }


class ValidationMethodForm(forms.ModelForm):

    class Meta:
        model = ValidationMethod
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(ValidationMethodForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', VALIDATION_METHOD)


class ValidationMethodAdmin(admin.ModelAdmin):
    form = ValidationMethodForm


class ValidationTypeForm(forms.ModelForm):

    class Meta:
        model = ValidationType
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super(ValidationTypeForm, self).__init__(*args, **kwargs)
        init_choices(self, 'name', VALIDATION_TYPE)


class ValidationTypeAdmin(admin.ModelAdmin):
    form = ValidationTypeForm


class CollectionAdmin(nested_admin.NestedModelAdmin):
    fieldsets = ( ('Searchable', {'fields': ('identifier', 'linguality',  )}),
                  ('Other',      {'fields': ('description', 'clarinCentre', 'access', 'version', 'documentation', 'validation', )}),
                )

    list_display = ['id', 'do_identifier', 'get_title', 'description']
    search_fields = ['identifier', 'title__name', 'description']

    inlines = [TitleInline, OwnerInline, ResourceInline, GenreInline, ProvenanceInline,
               CollectionLanguageInline, LanguageDisorderInline, RelationInline, CollectionDomainInline,
               TotalCollectionSizeInline, PidInline, ResourceCreatorInline, ProjectInline]

    actions = ['export_xml']
    formfield_overrides = {
        # models.TextField: {'widget': Textarea(attrs={'rows': 1, 'cols':30})},
        models.TextField: {'widget': Textarea(attrs={'rows': 1, 'cols': 80})},
        }

    def get_ordering_field_columns():
        return self.ordering

    def get_object(self, request, object_id, from_field=None):
        """Get a copy of the selected object and its related values"""

        # create a query
        lstQ = []
        lstQ.append(Q(id=object_id))

        # Get the correct queryset
        qs = Collection.objects.filter(*lstQ).select_related()
        if qs.count() == 0:
            obj = None
        else:
            obj = qs[0]
        return obj

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
        formfield = super(CollectionAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
        # Restrict the queryset where needed
        if db_field.name == "linguality":                                    # ForeignKey
            formfield.queryset = get_formfield_qs(Linguality, collThis, "collection")
        elif db_field.name == "access":                                      # ForeignKey
            formfield.queryset = get_formfield_qs(Access, collThis, "collection")
        elif db_field.name == "documentation":                               # ForeignKey
            formfield.queryset = get_formfield_qs(Documentation, collThis, "collection")
        elif db_field.name == "validation":                                  # ForeignKey
            formfield.queryset = get_formfield_qs(Validation, collThis, "collection")
        elif db_field.name == "writtenCorpus":                               # ForeignKey
            formfield.queryset = get_formfield_qs(WrittenCorpus, collThis, "collection")
        elif db_field.name == "speechCorpus":                                # ForeignKey
            formfield.queryset = get_formfield_qs(SpeechCorpus, collThis, "collection")
        return formfield


class FieldChoiceAdmin(admin.ModelAdmin):
    readonly_fields=['machine_value']
    list_display = ['english_name','dutch_name','machine_value','field']
    list_filter = ['field']

    def save_model(self, request, obj, form, change):

        if obj.machine_value == None:
            # Check out the query-set and make sure that it exists
            qs = FieldChoice.objectss.filter(field=obj.field)
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
admin.site.register(MediaFormat, MediaFormatAdmin)
admin.site.register(Media, MediaAdmin)
admin.site.register(Modality, ModalityAdmin)
# -- Genre
admin.site.register(Genre, GenreAdmin)
# -- provenance
admin.site.register(Provenance, ProvenanceAdmin)
admin.site.register(TemporalProvenance, TemporalProvenanceAdmin)
admin.site.register(GeographicProvenance, GeographicProvenanceAdmin)
admin.site.register(City)

# -- linguality
admin.site.register(LingualityType, LingualityTypeAdmin)
admin.site.register(LingualityNativeness, LingualityNativenessAdmin)
admin.site.register(LingualityAgeGroup, LingualityAgeGroupAdmin)
admin.site.register(LingualityStatus, LingualityStatusAdmin)
admin.site.register(LingualityVariant, LingualityVariantAdmin)
admin.site.register(MultilingualityType, MultilingualityTypeAdmin)
admin.site.register(Linguality, LingualityAdmin)
# -- language
admin.site.register(Language, LanguageAdmin)
# -- languageDisorder
admin.site.register(LanguageDisorder)
# -- relation
admin.site.register(Relation)
# -- domain
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
admin.site.register(ValidationType, ValidationTypeAdmin)
admin.site.register(ValidationMethod, ValidationMethodAdmin)
admin.site.register(Validation, ValidationAdmin)
# -- project
admin.site.register(ProjectFunder)
admin.site.register(ProjectUrl)
admin.site.register(Project, ProjectAdmin)

# -- writtencorpus
admin.site.register(CharacterEncoding, CharacterEncodingAdmin)
admin.site.register(WrittenCorpus, WrittenCorpusAdmin)
# -- speechcorpus
admin.site.register(RecordingEnvironment, RecordingEnvironmentAdmin)
admin.site.register(Channel, ChannelAdmin)
admin.site.register(ConversationalType, ConversationalTypeAdmin)
admin.site.register(RecordingCondition)
admin.site.register(SocialContext, SocialContextAdmin)
admin.site.register(PlanningType, PlanningTypeAdmin)
admin.site.register(Interactivity, InteractivityAdmin)
admin.site.register(Involvement, InvolvementAdmin)
admin.site.register(Audience, AudienceAdmin)
admin.site.register(AudioFormat, AudioFormatAdmin)
admin.site.register(SpeechCorpus, SpeechCorpusAdmin)

# -- collection as a whole
admin.site.register(Collection, CollectionAdmin)
