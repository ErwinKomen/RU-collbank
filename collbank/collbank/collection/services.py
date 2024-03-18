"""
Remote services for the CollBank application
This is mainly aimed at questioning the OAI interface
"""

import requests
import os
import json
import lxml
import requests
import sys
import time
from lxml import etree

# From own application
from collbank.basic.views import ErrHandle

OAI_HOME = 'http://localhost:8080/oai'

def get_oai_status():
    """Mimic reading the OAI interface, asking for a list of available metadata records"""

    oErr = ErrHandle()
    # Default reply
    oBack = {}
    try:
        # Figure out what the URL is going to be 
        url = OAI_HOME + "/provider?verb=ListIdentifiers&metadataPrefix=cmdi"
        r = None
        try:
            r = requests.get(url, timeout=2)
        except:
            # Getting an exception here probably means that the back-end is not reachable (down)
            oBack['status'] = 'error'
            oBack['msg'] = "get_oai_status(): The back-end server (oai) cannot be reached. Is it running? {}".format(
                oErr.get_error_message())
        else:
            if r.status_code == 200:
                # Success
                reply = r.text.replace("\t", " ")
                # Try to interpret this as an XML
                docroot = etree.XML(reply.encode('utf-8'))

                # Clean up the namespace
                for elem in docroot.getiterator():
                    if not (isinstance(elem, etree._Comment) or isinstance(elem, etree._ProcessingInstruction)):
                        elem.tag = etree.QName(elem).localname
                etree.cleanup_namespaces(docroot)

                # Get all the <identifier> elements under <ListIdentifiers>
                identifiers = docroot.xpath("//ListIdentifiers/header/identifier")
                msg = "{} identifiers found".format(len(identifiers))
                oBack['msg'] = msg

    except:
        msg = oErr.get_error_message()
        oErr.DoError("get_oai_status")
        oBack['status'] = "error"
        oBack['msg'] = msg

    # Return the correct object
    return oBack

    