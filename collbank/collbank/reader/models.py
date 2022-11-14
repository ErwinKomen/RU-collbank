"""Models for the READER app.

"""
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.db import models, transaction
from django.utils import timezone

from collbank.basic.models import LONG_STRING
from collbank.basic.utils import ErrHandle
from collbank.collection.models import PidService, PIDSERVICE_NAME

def get_current_datetime():
    """Get the current time"""
    return timezone.now()



# Create your models here.

class SourceInfo(models.Model):
    """Details of the source from which we get information"""

    # [0-1] Code used to collect information
    code = models.TextField("Code", null=True, blank=True)
    # [0-1] URL that was used
    url = models.URLField("URL", null=True, blank=True)
    # [0-1] File that was used for uploading
    file = models.FileField("File", null=True, blank=True, upload_to="collbank/")
    # [1] The person who was in charge of extracting the information
    collector = models.CharField("Collected by", max_length=LONG_STRING)
    # [0-1] Link to the actual user
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="user_sourceinfos")

    # [1] Obligatory time of extraction
    created = models.DateTimeField(default=get_current_datetime)

    def init_user():
        coll_set = {}
        qs = SourceInfo.objects.filter(user__isnull=True)
        # Derive from string in [collector]
        with transaction.atomic():
            for obj in qs:
                if obj.collector != "" and obj.collector not in coll_set:
                    coll_set[obj.collector] = User.models.filter(username=obj.collector).first()
                obj.user = coll_set[obj.collector]
                obj.save()

        result = True

    def get_created(self):
        sBack = self.created.strftime("%d/%b/%Y %H:%M")
        return sBack

    def get_code_html(self):
        sCode = "-" if self.code == None else self.code
        if len(sCode) > 80:
            button_code = "<a class='btn btn-xs jumbo-1' data-toggle='collapse' data-target='#source_code'>...</a>"
            sBack = "<pre>{}{}<span id='source_code' class='collapse'>{}</span></pre>".format(sCode[:80], button_code, sCode[80:])
        else:
            sBack = "<pre>{}</pre>".format(sCode)
        return sBack

    def get_file(self):
        """If file has been filled in, get the file name"""

        sBack = "-"
        if not self.file is None:
            sBack = self.file
        return sBack

    def get_url(self):
        """If URL has been filled in, get the URL"""

        sBack = "-"
        if not self.url is None:
            sBack = self.url
        return sBack

    def get_username(self):
        sBack = "(unknown)"
        if self.user != None:
            sBack = self.user.username
        return sBack

    def get_manu_html(self):
        """Get the HTML display of the manuscript[s] to which I am attached"""

        sBack = "Make sure to connect this source to a manuscript and save it. Otherwise it will be automatically deleted"
        qs = self.sourcemanuscripts.all()
        if qs.count() > 0:
            html = ["Linked to {} manuscript[s]:".format(qs.count())]
            for idx, manu in enumerate(qs):
                url = reverse('manuscript_details', kwargs={'pk': manu.id})
                sManu = "<span class='source-number'>{}.</span><span class='signature ot'><a href='{}'>{}</a></span>".format(
                    idx+1, url, manu.get_full_name())
                html.append(sManu)
            sBack = "<br />".join(html)
        return sBack
    

class VloItem(models.Model):
    """XML item for direct output into the VLO (virtual language observatory)"""

    # [0-1] Abbreviation to be used for the metadata file naming
    abbr = models.CharField("Abbreviation", null=True, blank=True, max_length=LONG_STRING)
    # [0-1] File that was used for uploading
    file = models.FileField("File", null=True, blank=True, upload_to="collbank/")
    # [0-1] Link to the actual user
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="user_vloitems")

    # [0-1] The name that has been assigned to this item for the VLO
    vloname = models.CharField("Name in the VLO", null=True, blank=True, max_length=LONG_STRING)

    # [0-1] The contents of the file in XML form
    xmlcontent = models.TextField("Contents in XML", null=True, blank=True)

    # the persistent identifier name by which this descriptor is going to be recognized
    #  The PID in CLARIN should be a handle. In our case it is the *last part* of the handle URL
    #  So a user can get to this collection description by typing:
    #  http://hdl.handle.net/21.11114/COLL-[this-pidname]
    pidname = models.CharField("Registry identifier", max_length=MAX_STRING_LEN, default="empty")
    # the 'URL' is the local (Radboud University) link where the XML and the HTML output of
    #           this collection should be found
    # Note: this field is *calculated* by the program and should *not* be entered by a user
    #       it is calculated upon publication
    url = models.URLField("URL of the metadata file", default='')

    # [1] Obligatory time of extraction
    created = models.DateTimeField(default=get_current_datetime)

    def __str__(self) -> str:
        sBack = "-"
        if self.file is None:
            sBack = "vloitem_{}".format(self.id)
        else:
            sBack = self.file
        return sBack

    def check_pid(self, pidservice, sPidName):
        """Check the PID against [sPidName] and brush up .url and .handledomain too"""

        oErr = ErrHandle()
        bResult = True
        try:
            # Validate
            if pidservice == None or sPidName == "": 
                return False
            bNeedSaving = False
            # Check if the handle domain is there 
            sHandleDomain = pidservice.getdomain()
            if self.handledomain != sHandleDomain:
                self.handledomain = sHandleDomain
                bNeedSaving = True
            # Check if the PID name is already there
            if self.pidname != sPidName:
                # Set the PID name
                self.pidname = sPidName
                bNeedSaving = True
            # Possibly set the url
            sUrl = self.get_targeturl()
            if self.url != sUrl:
                self.url = sUrl
                bNeedSaving = True
            # Possibly adapt the URL
            oResponse = pidservice.checkandupdatepid(self)
            if oResponse == None or oResponse['status'] != 'ok':
                print("VloItem/check_pid returns: " + oResponse['msg'])
                return False
            # Need saving?
            if bNeedSaving:
                self.save()
        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/check_pid")
            bResult = False
        # Return positively
        return bResult

    def get_abbr(self):
        sBack = "-"
        if not self.abbr is None:
            sBack = self.abbr
        return sBack

    def get_created(self):
        sBack = self.created.strftime("%d/%b/%Y %H:%M")
        return sBack

    def get_file(self):
        """If file has been filled in, get the file name"""

        sBack = "-"
        if not self.file is None:
            sBack = self.file
        return sBack

    def get_pidname(self, pidservice = None):
        """Get the persistent identifier and create it if it is not there"""
        bNeedSaving = False

        sBack = ""
        oErr = ErrHandle()
        try:
            sPidName = self.pidname
            if sPidName == "" or sPidName.startswith("empty") or sPidName.startswith("vlometadata"):
                # register the PID
                self.register_pid()
                sPidName = self.pidname
            # Return the PID name we have
            # (should be 21.11114/COLL-0000-000x-yyyy-z)

            # Check stuff
            if pidservice == None:
                pidservice = PidService.objects.filter(name=PIDSERVICE_NAME).first()
            if not self.check_pid(pidservice, sPidName):
                # Some error
                print("get_pidname doesn't get the pidservice:", sys.exc_info()[0])
                return ""
            # Return whatever the PID is now
            sBack = self.pidname
        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/get_pidname")
            sBack = ""
        return sBack

    def get_username(self):
        sBack = "(unknown)"
        if self.user != None:
            sBack = self.user.username
        return sBack

    def get_vloname(self):
        sBack = "-"
        if not self.vloname is None:
            sBack = self.vloname
        return sBack

    def get_selflink(self):
        """Get a handle to myself"""

        sBack = None
        oErr = ErrHandle()
        try:

    
            # If published: add the self link
            if colThis.pidname != None:
                # The selflink is the persistent identifier, preceded by 'hdl:'
                mdSelf.text = "hdl:{}/{}".format(colThis.handledomain, colThis.pidname)
            pass
        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/get_selflink")
        return sBack




