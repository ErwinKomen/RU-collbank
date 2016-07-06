# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-06 09:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0017_auto_20160706_1102'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='identifier',
            field=models.CharField(default='-', max_length=10, verbose_name='Unique short collection identifier (10 characters max)'),
        ),
    ]