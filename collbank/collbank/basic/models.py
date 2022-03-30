"""Models for the BASIC app.

"""
from django.db import models, transaction
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.db.models.functions import Lower
from django.db.models.query import QuerySet 

import json
import pytz
from collbank.settings import TIME_ZONE

# provide error handling
from .utils import ErrHandle

LONG_STRING=255
MAX_TEXT_LEN = 200

def get_crpp_date(dtThis, readable=False):
    """Convert datetime to string"""

    if readable:
        # Convert the computer-stored timezone...
        dtThis = dtThis.astimezone(pytz.timezone(TIME_ZONE))
        # Model: yyyy-MM-dd'T'HH:mm:ss
        sDate = dtThis.strftime("%d/%B/%Y (%H:%M)")
    else:
        # Model: yyyy-MM-dd'T'HH:mm:ss
        sDate = dtThis.strftime("%Y-%m-%dT%H:%M:%S")
    return sDate



# =============== HELPER models ==================================
class Status(models.Model):
    """Intermediate loading of sync information and status of processing it"""

    # [1] Status of the process
    status = models.CharField("Status of synchronization", max_length=50)
    # [1] Counts (as stringified JSON object)
    count = models.TextField("Count details", default="{}")
    # [0-1] Synchronisation type
    type = models.CharField("Type", max_length=255, default="")
    # [0-1] User
    user = models.CharField("User", max_length=255, default="")
    # [0-1] Error message (if any)
    msg = models.TextField("Error message", blank=True, null=True)

    def __str__(self):
        # Refresh the DB connection
        self.refresh_from_db()
        # Only now provide the status
        return self.status

    def set(self, sStatus, oCount = None, msg = None):
        self.status = sStatus
        if oCount != None:
            self.count = json.dumps(oCount)
        if msg != None:
            self.msg = msg
        self.save()


class UserSearch(models.Model):
    """User's searches"""
    
    # [1] The listview where this search is being used
    view = models.CharField("Listview", max_length = LONG_STRING)
    # [1] The parameters used for this search
    params = models.TextField("Parameters", default="[]")    
    # [1] The number of times this search has been done
    count = models.IntegerField("Count", default=0)
    # [1] The usage history
    history = models.TextField("History", default="{}")    
    
    class Meta:
        verbose_name = "User search"
        verbose_name_plural = "User searches"

    def add_search(view, param_list, username):
        """Add or adapt search query based on the listview"""

        oErr = ErrHandle()
        obj = None
        try:
            # DOuble check
            if len(param_list) == 0:
                return obj

            params = json.dumps(sorted(param_list))
            if view[-1] == "/":
                view = view[:-1]
            history = {}
            obj = UserSearch.objects.filter(view=view, params=params).first()
            if obj == None:
                history['count'] = 1
                history['users'] = [dict(username=username, count=1)]
                obj = UserSearch.objects.create(view=view, params=params, history=json.dumps(history), count=1)
            else:
                # Get the current count
                count = obj.count
                # Adapt it
                count += 1
                obj.count = count
                # Get and adapt the history
                history = json.loads(obj.history)
                history['count'] = count
                # Make sure there are users
                if not 'users' in history:
                    history['users'] = []
                    oErr.Status("Usersearch/add_search: added 'users' to history: {}".format(json.dumps(history)))
                bFound = False
                for oUser in history['users']:
                    if oUser['username'] == username:
                        # This is the count for a particular user
                        oUser['count'] += 1
                        bFound = True
                        break
                if not bFound:
                    history['users'].append(dict(username=username, count=1))
                obj.history = json.dumps(history)
                obj.save()

        except:
            msg = oErr.get_error_message()
            oErr.DoError("UserSearch/add_search")
        # Return what we found
        return obj

    def load_parameters(search_id, qd):
        """Retrieve the parameters for the search with the indicated id"""

        oErr = ErrHandle()
        try:
            obj = UserSearch.objects.filter(id=search_id).first()
            if obj != None:
                param_list = json.loads(obj.params)
                for param_str in param_list:
                    arParam = param_str.split("=")
                    if len(arParam) == 2:
                        k = arParam[0]
                        v = arParam[1]
                        qd[k] = v
        except:
            msg = oErr.get_error_message()
            oErr.DoError("UserSearch/load_parameters")
        # Return what we found
        return qd


class Information(models.Model):
    """Specific information that needs to be kept in the database"""

    # [1] The key under which this piece of information resides
    name = models.CharField("Key name", max_length=255)
    # [0-1] The value for this piece of information
    kvalue = models.TextField("Key value", default = "", null=True, blank=True)

    class Meta:
        verbose_name_plural = "Information Items"

    def __str__(self):
        return self.name

    def get_kvalue(name):
        info = Information.objects.filter(name=name).first()
        if info == None:
            return ''
        else:
            return info.kvalue

    def set_kvalue(name, value):
        info = Information.objects.filter(name=name).first()
        if info == None:
            info = Information(name=name)
            info.save()
        info.kvalue = value
        info.save()
        return True



