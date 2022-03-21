"""Models for the READER app.

"""
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.db import models, transaction
from django.utils import timezone

from collbank.basic.models import LONG_STRING

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
    file = models.FileField("File", null=True, blank=True)
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


