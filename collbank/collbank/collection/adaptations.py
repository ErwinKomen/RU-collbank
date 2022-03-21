"""
Adaptations of the database that are called up from the (list)views in the SEEKER app.
"""

from django.db import transaction
from django.db.models import Q
import re
import json

# ======= imports from my own application ======
from collbank.basic.utils import ErrHandle
from collbank.collection.models import Collection, Resource, \
    Media, Annotation, TotalSize, Modality, RecordingEnvironment, Channel, RecordingCondition, \
    SocialContext, PlanningType, Interactivity, Involvement, Audience, City, GeographicProvenance, \
    TotalSize, Genre, Title, Owner, TotalCollectionSize, Provenance, CollectionLanguage, \
    LanguageDisorder, Relation, Domain, PID, ResourceCreator, Project, ProjectFunder, \
    Linguality, LingualityType, LingualityNativeness, LingualityAgeGroup, LingualityStatus, \
    LingualityVariant, MultilingualityType, MediaFormat, Organization, Person


adaptation_list = {
    "collection_list": ["resource_empty"]
    }

def listview_adaptations(lv):
    """Perform adaptations specific for this listview"""

    oErr = ErrHandle()
    try:
        if lv in adaptation_list:
            for adapt in adaptation_list.get(lv):
                # sh_done  = Information.get_kvalue(adapt)
                sh_done = False
                if sh_done == None or sh_done != "done":
                    # Do the adaptation, depending on what it is
                    method_to_call = "adapt_{}".format(adapt)
                    bResult, msg = globals()[method_to_call]()
                    if bResult:
                        # Success
                        # Information.set_kvalue(adapt, "done")
                        pass
    except:
        msg = oErr.get_error_message()
        oErr.DoError("listview_adaptations")

# =========== Part of manuscript_list ==================

def adapt_resource_empty():
    oErr = ErrHandle()
    bResult = True
    msg = ""
    lst_resource = [Media, Annotation, TotalSize, Modality, RecordingEnvironment, Channel, 
               RecordingCondition, SocialContext, PlanningType, Interactivity, Involvement, Audience]
    lst_geoprov = [City]
    lst_coll = [Genre, Title, Owner, TotalCollectionSize, Provenance, CollectionLanguage,
                LanguageDisorder, Relation, Domain, PID, ResourceCreator, Project]
    lst_prov = [GeographicProvenance]
    lst_ling = [LingualityType, LingualityNativeness, LingualityAgeGroup, LingualityStatus, 
                LingualityVariant, MultilingualityType]
    lst_medi = [MediaFormat]
    lst_rescrea = [Organization, Person]
    lst_proj = [ProjectFunder]

    def delete_empty(cls, res_id, fk_field, fk_other=None):
        oErr = ErrHandle()
        try:
            qs = cls.objects.exclude(Q(**{"{}__id__in".format(fk_field): res_id}))
            count = qs.count()
            if count > 0:
                oErr.Status("delete_empty: class {} deletes {}".format(cls.__name__, count))
                qs.delete()
            if not fk_other is None and hasattr(cls, fk_other):
                qs = cls.objects.exclude(Q(**{"{}__id__in".format(fk_other): res_id}))
                count = qs.count()
                if count > 0:
                    oErr.Status("delete_empty: class {} deletes {}".format(cls.__name__, count))
                    qs.delete()
        except:
            msg = oErr.get_error_message()
            oErr.DoError("delete_empty")
    
    try:
        # Check all models that have 'resource' as FK
        resource_ids = [x.id for x in Resource.objects.all()]
        for cls in lst_resource:
            delete_empty(cls, resource_ids, "resource")

        # Check all models that have 'resource' as FK
        geoprov_ids = [x.id for x in GeographicProvenance.objects.all()]
        for cls in lst_geoprov:
            delete_empty(cls, geoprov_ids, "geographicProvenance")

        # Adapt totalsize-collection connections
        qs = Collection.totalSize.through.objects.all()
        lst_m2m = qs.values("id", "totalsize_id")
        ts_id = []
        for item in lst_m2m:
            if TotalSize.objects.filter(id=item['totalsize_id']).count() == 0:
                ts_id.append(item['id'])
        Collection.totalSize.through.objects.filter(id__in=ts_id).delete()

        # Check all models that have 'collection' as FK
        coll_ids = [x.id for x in Collection.objects.all()]
        for cls in lst_coll:
            delete_empty(cls, coll_ids, "collection", "related")

        # Check all models that have 'provenance' as FK
        prov_ids = [x.id for x in Provenance.objects.all()]
        for cls in lst_prov:
            delete_empty(cls, prov_ids, "provenance")

        # Check all models that have 'linguality' as FK
        ling_ids = [x.id for x in Linguality.objects.all()]
        for cls in lst_ling:
            delete_empty(cls, ling_ids, "linguality")

        # Check all models that have 'media' as FK
        medi_ids = [x.id for x in Media.objects.all()]
        for cls in lst_medi:
            delete_empty(cls, medi_ids, "media")

        # Check all models that have 'resourceCreator' as FK
        resc_ids = [x.id for x in ResourceCreator.objects.all()]
        for cls in lst_rescrea:
            delete_empty(cls, resc_ids, "resourceCreator")

        # Check all models that have 'project' as FK
        proj_ids = [x.id for x in Project.objects.all()]
        for cls in lst_proj:
            delete_empty(cls, proj_ids, "project")

    except:
        bResult = False
        msg = oErr.get_error_message()
        oErr.DoError("adapt_resource_empty")
    return bResult, msg


