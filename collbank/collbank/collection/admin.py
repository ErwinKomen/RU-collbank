from django.contrib import admin
from collbank.collection.models import *

#class TitleInline(admin.TabularInline):
#    model = Collection.title.through
#    extra = 1

class CollectionAdmin(admin.ModelAdmin):
#    inlines = (TitleInline,)
    filter_horizontal = ('title', 'owner', 'resource', 'genre', 'language', 'languageDisorder', 'relation', 'domain',)
    fieldsets = ( ('Searchable', {'fields': ('title', 'resource', 'provenance', 'linguality','language', 'languageDisorder', 'relation', 'speechCorpus',)}),
                  ('Other',      {'fields': ('description', 'owner', 'genre', 'domain', 'clarinCentre', 'access', 'totalSize', 'pid', 'version', 'resourceCreator', 'documentation', 'validation', 'project', 'writtenCorpus',)}),
                )


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
    filter_horizontal = ('annotation',)
    fieldsets = ( ('Searchable', {'fields': ('type', 'annotation', 'media',)}),
                  ('Other',      {'fields': ()}),
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


# Models that serve others
admin.site.register(FieldChoice)
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