"""
Adaptations of the database that are called up from the (list)views in the SEEKER app.
"""

from django.db import transaction
from django.db.models import Q
import re
import os
import json
import csv

# ======= imports from my own application ======
from collbank.basic.utils import ErrHandle
from collbank.settings import MEDIA_DIR
from collbank.basic.models import Information
from collbank.collection.models import FieldChoice, Collection, Resource, \
    Media, Annotation, TotalSize, Modality, RecordingEnvironment, Channel, RecordingCondition, \
    SocialContext, PlanningType, Interactivity, Involvement, Audience, City, GeographicProvenance, \
    TotalSize, Genre, Title, Owner, TotalCollectionSize, Provenance, CollectionLanguage, \
    LanguageDisorder, Relation, Domain, PID, ResourceCreator, Project, ProjectFunder, \
    Linguality, LingualityType, LingualityNativeness, LingualityAgeGroup, LingualityStatus, \
    LingualityVariant, MultilingualityType, MediaFormat, Organization, Person, \
    LanguageIso, LanguageName, Language, CountryIso


adaptation_list = {
    "collection_list": ["resource_empty", "language_renew", "langname_add", "country_renew"] #, "country_add"]
    }

def listview_adaptations(lv):
    """Perform adaptations specific for this listview"""

    oErr = ErrHandle()
    try:
        if lv in adaptation_list:
            for adapt in adaptation_list.get(lv):
                sh_done  = Information.get_kvalue(adapt)
                # sh_done = False
                if sh_done == None or sh_done != "done":
                    # Do the adaptation, depending on what it is
                    method_to_call = "adapt_{}".format(adapt)
                    bResult, msg = globals()[method_to_call]()
                    if bResult:
                        # Success
                        Information.set_kvalue(adapt, "done")
                        # pass
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

def adapt_language_renew():
    """Read languages into [LanguageIso] and [LanguageName]"""
    oErr = ErrHandle()
    bResult = True
    msg = ""

    try:
        # Determine what file to take
        code_file = os.path.abspath(os.path.join(MEDIA_DIR, "collbank", "newcodes.csv"))
        if os.path.exists(code_file):
            # Read the CSV
            with open(code_file, "r", encoding="utf-8") as f:
                csvreader = csv.reader(f, delimiter="\t")
                line = 0
                for row in csvreader:
                    line += 1
                    if line > 1:
                        code = row[0]
                        lngname = row[1]
                        url = row[2]
                        # Show where we are
                        oErr.Status("{}: {} ({})".format(line, code, lngname))
                        # See if we can process the code
                        iso = LanguageIso.objects.filter(code=code).first()
                        if iso is None:
                            iso = LanguageIso.objects.create(code=code, url=url)
                        # Do we already have the language name?
                        obj = LanguageName.objects.filter(iso=iso, name=lngname).first()
                        if obj is None:
                            # Add the name
                            obj = LanguageName.objects.create(iso=iso, name=lngname)
        
    except:
        bResult = False
        msg = oErr.get_error_message()
        oErr.DoError("adapt_language_renew")
    return bResult, msg

def adapt_country_renew():
    """Read countries into [CountryIso] """

    oErr = ErrHandle()
    bResult = True
    msg = ""

    try:
        # Determine what file to take
        code_file = os.path.abspath(os.path.join(MEDIA_DIR, "collbank", "CountryCodes.json"))
        if os.path.exists(code_file):
            # Read the JSON into a list
            with open(code_file, "r", encoding="utf-8") as f:
                lst_country = json.load(f)

            # Process all the countries
            for oCountry in lst_country:
                # Get the parameters
                alpha2 = oCountry.get("alpha2Code")
                alpha3 = oCountry.get("alpha3Code")
                numeric = oCountry.get("numeric")
                english = oCountry.get("englishShortName")
                french = oCountry.get("frenchShortName")

                # Create a record if the alpha2 is not yet there
                obj = CountryIso.objects.filter(alpha2=alpha2).first()
                if obj is None:
                    obj = CountryIso.objects.create(alpha2=alpha2, alpha3=alpha3, numeric=numeric, english=english, french=french)
        
    except:
        bResult = False
        msg = oErr.get_error_message()
        oErr.DoError("adapt_country_renew")
    return bResult, msg

def adapt_langname_add():
    """Add the [langname] field contents to table [Language]"""

    oErr = ErrHandle()
    bResult = True
    msg = ""
    ptr_dict = {}

    try:
        qs = Language.objects.filter(langname__isnull=True)
        for obj in qs:
            # Figure out what the Language pointer is
            language_ptr = obj.name
            if not language_ptr in ptr_dict:
                # Find this entry in FieldChoice
                fchoice = FieldChoice.objects.filter(field="language.name", machine_value=language_ptr).first()
                if fchoice is None:
                    # Going wrong
                    oErr.Status("adapt_langname_add: cannot find machine_value {} for Language id {}".format(
                        language_ptr, obj.id))
                    bResult = False
                else:
                    # Get the value of the language
                    english_name = fchoice.english_name
                    if "Flemish" in english_name:
                        english_name = "Flemish"
                    elif "official aramaic" in english_name.lower():
                        english_name = "Official Aramaic (700-300 BCE)"
                    # Look for this language in [LanguageName]
                    langname = LanguageName.objects.filter(name__iexact=english_name).first()
                    if langname is None:
                        # Problem
                        oErr.Status("adapt_langname_add: cannot find language called [{}] for Language id {}".format(
                            english_name, obj.id))
                        bResult = False
                    else:
                        ptr_dict[language_ptr] = langname
        for obj in qs:
            language_ptr = obj.name
            if language_ptr in ptr_dict:
                obj.langname = ptr_dict[language_ptr] 
                obj.save()
        
    except:
        bResult = False
        msg = oErr.get_error_message()
        oErr.DoError("adapt_langname_add")
    return bResult, msg

#def adapt_country_add():
#    """Determine the [countryiso] field of [GeographicProvenance]"""

#    oErr = ErrHandle()
#    bResult = True
#    msg = ""
#    country_dict = {22: "BE", 76: "FR", 83: "DE", 111: "IT", 152: "MA", 158: "NL",
#                    185: "RU", 214: "SR", 217: "SE", 222: "TZ", 230: "TR", 237: "GB"}

#    try:
#        qs = GeographicProvenance.objects.filter(countryiso__isnull=True, country__isnull=False)
#        for obj in qs:
#            # Figure out what the machine_value is of the [country] field
#            cnt = obj.country
#            cnt = int(cnt)

#            # Figure out what the alpha2 code is
#            alpha2 = country_dict[cnt]

#            # Figure out what the countryIso object is
#            countryiso = CountryIso.get_byalpha2(alpha2)

#            # Set this feature
#            obj.countryiso = countryiso
#            obj.save()
        
#    except:
#        bResult = False
#        msg = oErr.get_error_message()
#        oErr.DoError("adapt_country_add")
#    return bResult, msg


