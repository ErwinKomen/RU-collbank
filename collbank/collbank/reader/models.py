"""Models for the READER app.

"""
from typing import ByteString
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.db import models, transaction
from django.utils import timezone
from datetime import datetime
from pathlib import Path
import xmltodict
import lxml.etree as ET
import os
import json


from collbank.basic.models import LONG_STRING
from collbank.basic.utils import ErrHandle
from collbank.collection.models import PidService, PIDSERVICE_NAME, MAX_STRING_LEN, MAX_NAME_LEN, Resource
from collbank.settings import MEDIA_ROOT, REGISTRY_URL, REGISTRY_DIR, PUBLISH_DIR

def get_current_datetime():
    """Get the current time"""
    return timezone.now()

def vloitem_path(instance, filename):
    """Upload file to the right place,and remove old file if existing"""

    oErr = ErrHandle()
    sBack = ""
    try:
        sBack = os.path.join("collbank", filename)
        sAbsPath = os.path.abspath(os.path.join(MEDIA_ROOT, "collbank", filename))
        if os.path.exists(sAbsPath):
            # Remove it
            os.remove(sAbsPath)
    except:
        msg = oErr.get_error_message()
        oErr.DoError("vloitem_path")
    return sBack


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
    abbr = models.CharField("Abbreviation", null=True, blank=True, max_length=LONG_STRING, default="oh")
    # [0-1] File that was used for uploading
    file = models.FileField("File", null=True, blank=True, upload_to=vloitem_path)  # upload_to="collbank/")

    # [0-1] A VloItem should have a title - this can be changed by the user
    title = models.CharField("Title", null=True, blank=True, max_length=LONG_STRING)

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
    handledomain = models.CharField("Domain of the Handle system", max_length=MAX_NAME_LEN, default='')

    # Internal-only: last saved
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    # [1] Obligatory time of extraction
    created = models.DateTimeField(default=get_current_datetime)

    restype_abbr = {
        "landingpage": "lp", "searchpage": "sp", "resource": "res"
    }
    restype_full = {
        "landingpage": "LandingPage", "searchpage": "SearchPage", "resource": "Resource"
    }

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

    def get_pidfull(self):
        """Return the complete handle as a clickable item"""

        sBack = "-"
        oErr = ErrHandle()
        try:
            if self.pidname != None and self.get_status() in ["published", "stale"]:
                sBack = "http://hdl.handle.net/21.11114/{}".format(self.pidname)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/get_pidfull")
        return sBack

    def get_pidname(self, pidservice = None, viewonly = False):
        """Get the persistent identifier and create it if it is not there"""
        bNeedSaving = False

        sBack = ""
        oErr = ErrHandle()
        try:
            sPidName = self.pidname

            if viewonly:
                if sPidName is None or sPidName == "":
                    sBack = "-"
                else:
                    sBack = sPidName
            else:

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

    def get_publisfilename(self, sType=""):
        sPublish = "-"
        oErr = ErrHandle()
        try:
            # Get the correct pidname
            sFileName = self.get_xmlfilename()
            # THink of a filename
            if sType == "joai":
                sPublish = os.path.abspath(os.path.join(PUBLISH_DIR, sFileName)) + ".cmdi.xml"
            else:
                sPublish = os.path.abspath(os.path.join(REGISTRY_DIR, sFileName))
        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/get_publisfilename")
        return sPublish

    def publishdate(self):

        sDate = "-"
        oErr = ErrHandle()
        try:
            sPublishPath = self.get_publisfilename()
            if os.path.isfile(sPublishPath):
                fDate = os.path.getmtime(sPublishPath)
                oDate = datetime.fromtimestamp( fDate)
                sDate = oDate.strftime("%d/%b/%Y %H:%M:%S")
            else:
                sDate = 'unpublished'
        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/publishdate")
        return sDate

    def get_selflink(self):
        """Get a handle to myself"""

        sBack = ""
        oErr = ErrHandle()
        try:
    
            # If published: add the self link
            if self.pidname != None:
                # The selflink is the persistent identifier, preceded by 'hdl:'
                sBack = "hdl:{}/{}".format(self.handledomain, self.pidname)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/get_selflink")
        return sBack

    def get_status(self):
        """Get the status of this colletion: has it been published or not?"""

        sStatus = "-"
        oErr = ErrHandle()
        try:
            sPublishPath = self.get_publisfilename()
            sStatusP = 'p' if os.path.isfile(sPublishPath) else 'u'
            # If it is published, get its publication date and compare it to 
            sStatusD = 'n'
            # Has it been published?
            if sStatusP == 'p':
                if self.updated_at == None:
                    # If it is published, but no 'updated_at' yet, it is 'up to date'
                    sStatusD = 'd' 
                else:
                    # It is published: get the file date
                    saved_at = os.path.getmtime(sPublishPath)
                    updated_at = datetime.timestamp( self.updated_at)
                    sStatusD = 's' if saved_at < updated_at else 'd'
            # Combine states
            if sStatusP == 'u':
                sStatus = 'not-published'
            else:
                if sStatusD == 'n':
                    sStatus = 'unknown'
                elif sStatusD == 'd':
                    sStatus = 'published'
                else:
                    sStatus = 'stale' 
        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/get_status")
        # Return the combined status
        return sStatus

    def get_title(self):
        """If title has been filled in, get the title"""

        sBack = "-"
        if not self.title is None:
            sBack = self.title
        return sBack

    def get_targeturl(self):
        """Get the URL where the XML data should be made available"""
        sUrl = "{}{}".format(REGISTRY_URL,self.get_xmlfilename())
        return sUrl

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

    def get_xmlfilename(self):
        """Create the filename for the XML file for this item"""

        oErr = ErrHandle()
        sBack = ""
        try:
            sBack = "{0}_vlometadata_{1:05d}".format(self.abbr, self.id)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/get_xmlfilename")
        return sBack

    def may_register(self):
        # Check if we are allowed to register

        bMay = (not self.abbr is None and self.abbr != "" and \
           not self.vloname is None and self.vloname != "" and \
          not self.xmlcontent is None and self.xmlcontent != "")
        return bMay

    def publish(self):
        """Publish the XML"""

        oErr = ErrHandle()
        sContent = ""
        try:
            instance = self
            sXmlText = instance.xmlcontent
            if not sXmlText is None and sXmlText != "":
                # Get the full path to the registry file
                fPublish = instance.get_publisfilename()
                # Write it to a file in the XML directory
                with open(fPublish, encoding="utf-8", mode="w") as f:  
                    f.write(sXmlText)

                # Publish the .cmdi.xml
                fPublish = instance.get_publisfilename("joai")
                # Write it to a file in the XML directory
                with open(fPublish, encoding="utf-8", mode="w") as f:  
                    f.write(sXmlText)
                sContent = sXmlText
        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/publish")
        return sContent

    def repair_xml(self, sContent, selflink = None):
        """Read the XML from file/string, repair it, and return it as string again
        
        This uses the [lxml] approach, which is stricter than [xmltodict]
        """

        def get_first(elStart, sFind, NS):
            items = elStart.findall(sFind, NS)
            if len(items) == 0:
                item = None
            else:
                item = items[0]
            return item

        def get_first_node_value(elStart, sFind, NS):
            items = elStart.findall(sFind, NS)
            if len(items) == 0:
                sBack = ""
            else:
                sBack = items[0].text
            return sBack

        oErr = ErrHandle()
        CMD_VERSION = "1.1"

        try:
            # We use 'instance' in this method, but it actually is 'self'
            instance = self

            NS_find = {None: 'http://www.clarin.eu/cmd/'}
            NS_xpath = {'a': 'http://www.clarin.eu/cmd/'}

            # NOTE: the difference of working with .findall versus .xpath
            #   cmd_item = root.findall("./child::Header", {None: 'http://www.clarin.eu/cmd/'})
            #   cmd_item = root.xpath("./a:Header", namespaces={'a': 'http://www.clarin.eu/cmd/'})


            # This either reads a string or file and parses it
            parser = ET.ETCompatXMLParser()
            root = None
            if isinstance(sContent,bytes):
                root = ET.fromstring(sContent.decode("utf-8"), parser)
            elif isinstance(sContent,str):
                root = ET.fromstring(sContent, parser)
            else:
                xmldoc = ET.parse(sContent, parser)
                # Get to the root (which is the <CMD> element)
                root = xmldoc.getroot()
            
            # Get to the <CMD> element
            if not root is None:
                # Check for attribute CMDVersion
                sCmdVersion = root.attrib.get("CMDVersion", "")
                if sCmdVersion == "":
                    root.attrib['CMDVersion'] = CMD_VERSION

                # get the header 
                header = get_first(root, "Header", NS_find)

                # Check the header's selflink information
                if not selflink is None:
                    currentlink = get_first_node_value(header, "MdSelfLink", NS_find)
                    if selflink != currentlink:
                        # Add this node as child
                        newlink = ET.Element("MdSelfLink", nsmap = NS_find)
                        newlink.text = selflink
                        header.append(newlink)

                # Get the title from Components OralHistoryInterviewCRF
                title_xml = ""
                components = get_first(root, "Components", NS_find)
                if not components is None:
                    crf = get_first(components, "OralHistoryInterviewCRF", NS_find)
                    csd = get_first(components, "CorpusCollection_CSD", NS_find)
                    if not crf is None:
                        ID_element = get_first(crf, "ID", NS_find)
                        title_xml = crf.attrib.get("Title", "")
                        title_self = "" if instance.title is None else instance.title

                        # See what needs to happen
                        if title_self == "" and title_xml != "":
                            # Copy the title from XML to the object
                            print("VloItemRegister: copied <title> from XML to database")
                            instance.title = title_xml
                            instance.save()
                        elif title_self != "" and title_xml == "":
                            # Copy the title from Self to XML
                            print("VloItemRegister: copied <title> from database to XML")
                            title_xml = title_self
                            # The Title must be the first element
                            newtitle = ET.Element("Title", nsmap = NS_find)
                            newtitle.text = title_self

                            if ID_element is None:
                                # Insert it as the first child of CRF
                                crf.insert(0, newtitle)
                            else:
                                # Insert it as the second child of CRF, after the ID field
                                crf.insert(1, newtitle)
                    elif not csd is None:
                        # This is probably a <CorpusCollection_CSD>: get the title
                        title_element = get_first(csd, "title", NS_find)
                        if not title_element is None:
                            title_xml = title_element.text
                            title_self = "" if instance.title is None else instance.title
                            # See what needs to happen
                            if title_self == "" and title_xml != "":
                                # Copy the title from XML to the object
                                print("VloItemRegister: copied <title> from XML to database")
                                instance.title = title_xml
                                instance.save()

                # Returning to the header, get the <Resources> over there
                resources = get_first(root, "Resources", NS_find)
                if not resources is None:
                    # If there are any resources, process them
                    resourceProxyList = get_first(resources, "ResourceProxyList", NS_find)
                    if not resourceProxyList is None:
                        lst_proxy = resourceProxyList.findall("ResourceProxy", NS_find)

                        # Some initalisations
                        bNeedUpdate = False
                        lst_proxy_update = []

                        # Figure out landing page or resource reference
                        for oResourceProxy in lst_proxy:
                            oResType = get_first(oResourceProxy, "ResourceType", NS_find)
                            # NOTE: do *NOT* turn this into lower case
                            resource_type = oResType.text
                            resource_mtype = oResType.attrib.get("mimetype", "")
                            if resource_mtype == "":
                                resource_mtype = "application/x-http"
                                # Indicate that we need to replace the updated
                                bNeedUpdate = True
                            resource_ref = get_first(oResourceProxy, "ResourceRef", NS_find)

                            # Calculate the ID for this ResourceProxy
                            rtype = VloItem.restype_abbr.get(resource_type.lower(), "oth")
                            res_proxy_id = "{}_{}metadata_{:05d}".format(rtype, instance.abbr, instance.id)

                            sResProxyId = oResourceProxy.attrib.get("id", "")
                            if sResProxyId == "" or sResProxyId != res_proxy_id:
                                oResourceProxy.attrib['id'] = res_proxy_id

                            # Make sure the resource type is in the right case
                            if resource_type != VloItem.restype_full.get(resource_type.lower()):
                                resource_type = VloItem.restype_full.get(resource_type.lower(), "Other")
                                # Indicate that we need to replace the updated
                                bNeedUpdate = True

                            # Keep track of the resource proxy definitions
                            lst_proxy_update.append(dict(
                                mimetype=resource_mtype, 
                                resourcetype=resource_type, 
                                resourceref=resource_ref,
                                id=res_proxy_id))

                        # Do we need to update the existing list of proxies?
                        if bNeedUpdate:
                            # Update the existing list
                            for idx, oResourceProxy in enumerate(lst_proxy):
                                res_type = get_first(oResourceProxy, "ResourceType", NS_find)
                                res_type.attrib['mimetype'] = lst_proxy_update[idx]['mimetype']
                                res_type.text = lst_proxy_update[idx]['resourcetype']

                # See if we 

            # Get the contents as text
            sContent = ET.tostring(root, pretty_print=True).decode("utf-8")
        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/repair_xml")
        return sContent

    def repair_xml_dict(self, sContent, selflink = None):
        """Read the XML from file/string, repair it, and return it as string again
        
        This uses the [xmltodict] approach, which has a limitation in ordering
        """

        oErr = ErrHandle()
        CMD_VERSION = "1.1"

        try:
            # We use 'instance' in this method, but it actually is 'self'
            instance = self

            # This either reads a string or file and parses it
            doc = xmltodict.parse(sContent)
            # Now we can treat it as a JSON object
            oContent = doc.get("CMD")
            if not oContent is None:
                # For debugging: get a string of the object
                sCMD = json.dumps(oContent, indent=2)

                # Check for attribute CMDVersion
                sCmdVersion = oContent.get('@CMDVersion', '')
                if sCmdVersion == "":
                    oContent['@CMDVersion'] = CMD_VERSION

                # get the header 
                oHeader = oContent.get('Header')

                # Check the header's selflink information
                if not selflink is None:
                    currentlink = oHeader.get("MdSelfLink", "")
                    if selflink != currentlink:
                        oHeader['MdSelfLink'] = selflink

                # Check the header's <title> information
                # OLD: title_xml = oHeader.get("Title", "")
                # Get the title from Components OralHistoryInterviewCRF
                title_xml = ""
                oComponents = oContent.get("Components")
                if not oComponents is None:
                    oCRF = oComponents.get("OralHistoryInterviewCRF")
                    if not oCRF is None:
                        title_xml = oCRF.get("Title", "")
                title_self = "" if instance.title is None else instance.title
                if title_self == "" and title_xml != "":
                    # Copy the title from XML to the object
                    print("VloItemRegister: copied <title> from XML to database")
                    instance.title = title_xml
                    instance.save()
                elif title_self != "" and title_xml == "":
                    # Copy the title from Self to XML
                    print("VloItemRegister: copied <title> from database to XML")
                    title_xml = title_self
                    # OLD: oHeader['Title'] = title_xml
                    oCRF['Title'] = title_self

                # Also check if `ResourceProxy` has mimetype not empty
                oResources = oContent.get('Resources')
                if not oResources is None:
                    # If there are any resources, process them
                    oResourceProxyList = oResources.get("ResourceProxyList")
                    if not oResourceProxyList is None:
                        lst_proxy = []
                        lResourceProxy = oResourceProxyList.get("ResourceProxy")
                        if isinstance(lResourceProxy, list):
                            lst_proxy = lResourceProxy
                        else:
                            lst_proxy.append(lResourceProxy)

                        # Some initalisations
                        bNeedUpdate = False
                        lst_proxy_update = []

                        # Figure out landing page or resource reference
                        for oResourceProxy in lst_proxy:
                            oResType = oResourceProxy.get("ResourceType")
                            if isinstance(oResType, str):
                                resource_type = oResType
                                resource_mtype = "application/x-http"
                                # Indicate that we need to replace the updated
                                bNeedUpdate = True
                            else:
                                # NOTE: do *NOT* turn this into lower case
                                resource_type = oResType.get("#text")
                                resource_mtype = oResType.get("@mimetype")
                                if resource_mtype is None or resource_mtype == "":
                                    resource_mtype = "application/x-http"
                                    # Indicate that we need to replace the updated
                                    bNeedUpdate = True
                            resource_ref = oResourceProxy.get("ResourceRef")
                            # Calculate the ID for this ResourceProxy
                            rtype = VloItem.restype_abbr.get(resource_type.lower(), "oth")
                            res_proxy_id = "{}_{}metadata_{:05d}".format(rtype, instance.abbr, instance.id)

                            sResProxyId = oResourceProxy.get("@id", "")
                            if sResProxyId == "" or sResProxyId != res_proxy_id:
                                oResourceProxy['@id'] = res_proxy_id

                            # Make sure the resource type is in the right case
                            if resource_type != VloItem.restype_full.get(resource_type.lower()):
                                resource_type = VloItem.restype_full.get(resource_type.lower(), "Other")
                                # Indicate that we need to replace the updated
                                bNeedUpdate = True

                            # Keep track of the resource proxy definitions
                            lst_proxy_update.append(dict(
                                mimetype=resource_mtype, 
                                resourcetype=resource_type, 
                                resourceref=resource_ref,
                                id=res_proxy_id))

                        # Do we need to update the existing list of proxies?
                        if bNeedUpdate:
                            # Update the existing list
                            for idx, oResourceProxy in enumerate(lst_proxy):
                                oUpdated = {}
                                oUpdated['@mimetype'] = lst_proxy_update[idx]['mimetype']
                                oUpdated['#text'] = lst_proxy_update[idx]['resourcetype']
                                oResourceProxy['ResourceType'] = oUpdated

            # Get the contents as text
            sContent = xmltodict.unparse(doc, pretty=True)
        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/repair_xml_dict")
        return sContent

    def read_xml(self):
        """Re-read the XML from where it is stored (if it is stored)"""

        oErr = ErrHandle()
        sContent = ""
        try:
            # Get the file and read it
            data_file = self.file

            # Check if it exists
            if not data_file is None and data_file != "":

                # Use XmlToDict to parse (from XML to objects) and unparse (from objects to XML)
                sContent = self.repair_xml(data_file)
                # Store the contents into the VloItem 
                self.xmlcontent = sContent
                # And save it
                self.save()
        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/read_xml")
        return sContent

    def register(self):
        """Re-register the XML"""

        oErr = ErrHandle()
        sContent = ""
        CMD_VERSION = "1.1"

        try:
            instance = self

            # Now that we have a pidname, we can fill in the handle 
            selflink = instance.get_selflink()
            if selflink != "":
                # Yes, we have a selflink: process this internally
                sContent = self.repair_xml(instance.xmlcontent, selflink)
                # Store the contents into the VloItem 
                instance.xmlcontent = sContent
                # And save it
                instance.save()

        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/register")
        return sContent

    def register_pid(self):
        """Make sure this record has a registered persistant identifier
        
        Additionally: set the .pidname field (if needed) and set the .url field (if needed)
        """

        oErr = ErrHandle()
        bResult = True
        try:
            # Get the correct service
            pidservice = PidService.objects.filter(name=PIDSERVICE_NAME).first()
            if pidservice == None:
                # Make sure the caller understands something is wrong
                return False
            # Look for a record with this name in the PID service
            sResponse = pidservice.getpid(self)
            if sResponse == "":
                # There was some kind of error
                return False
            elif sResponse == "-":
                # There is no registration yet: create one
                oResponse = pidservice.createpid(self)
                if oResponse != None and 'status' in oResponse and oResponse['status'] == "ok":
                    sPidName = oResponse['pid']
                    # Adapt the PID if it contains a /
                    if "/" in sPidName:
                        # Make sure we only store the part *after* the slash
                        sPidName = sPidName.split("/")[-1]
                else:
                    # Something somewhere went wrong
                    oErr.DoError("VloItem/register_pid - something went wrong")
                    return False
            else:
                sPidName = sResponse

            # Check stuff
            if not self.check_pid(pidservice, sPidName):
                # Some error
                oErr.DoError("VloItem/register_pid doesn't get the pidservice:")
                bResult = False
        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/register_pid")
            bResult = False

        # Return positively
        return bResult

    def save(self, **kwargs):
        oErr = ErrHandle()
        try:
            # Check if a .vloname has been specified, when a .file is known
            if not self.file is None and not self.file.name is None and self.file != "":
                # Get what should be the VLONAME
                vloname = Path(self.file.path).stem
                if self.vloname is None or self.vloname != vloname:
                    self.vloname = vloname
            result = super(VloItem,self).save(**kwargs)
            return result
        except:
            msg = oErr.get_error_message()
            oErr.DoError("VloItem/save")
            return None


# ========= End ==============================




