import requests
#from requests.auth import HTTPBasicAuth
#from collbank.collection.models import PidService

#PIDSERVICE_NAME = "gwdg"


#def epic_authenticate(oReq):
#    """Authenticate with the ePIC API"""

#    # Default reply
#    oBack = {'status': 'error', 'msg': ''}
#    # Get the correct service
#    pidservice = PidService.objects.filter(PIDSERVICE_NAME)
#    if pidservice == None:
#        oBack['msg'] = 'Could not find ePIC service'
#        return oBack
#    # We have the information to our disposal
#    url = pidservice.url
#    user = pidservice.user
#    ww = pidservice.passwd
#    # Issue the request
#    r = requests.get(url, auth=(user,ww))
#    # Check the reply we got
#    if r.status_code == 200:
#        # Authentication worked
#        oBack['status'] = 'ok'
#    else:
#        # Authentication did not work
#        oBack['msg'] = "The authentication request returned code {}".format(r.status_code)
#    return oBack


#PIDSERVICE_URL="THE_SERVICE_URL_WITH_PREFIX"
#PIDSERVICE_USER="YOURUSERNAME"
#PIDSERVICE_PASSWD="YOURPASSWORD"
#DATAURL=''
#URL_TO_OPEN=PIDSERVICE_URL

## create a password manager
#password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

## Add the username and password.
#password_mgr.add_password(None, PIDSERVICE_URL, PIDSERVICE_USER, PIDSERVICE_PASSWD)

#handler = urllib2.HTTPBasicAuthHandler(password_mgr)

## create "opener" (OpenerDirector instance)
#opener = urllib2.build_opener(handler)

## use the opener to fetch a URL
#opener.open(PIDSERVICE_URL)

## Install the opener.
## Now all calls to urllib2.urlopen use the created opener.
#urllib2.install_opener(opener)

#REQUESTDATA = urllib2.Request(URL_TO_OPEN)
#try:
#    DATAURL = urllib2.urlopen(REQUESTDATA)
#except urllib2.URLError, e:
#    if e.code == 401:
#         print("401-Authentication failed")

#if DATAURL:
#    # Getting the code
#    print("This gets the code: {}".format(DATAURL.code))