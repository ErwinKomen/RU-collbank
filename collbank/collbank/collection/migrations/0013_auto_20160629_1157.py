# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-29 09:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0012_auto_20160629_1130'),
    ]

    operations = [
        migrations.CreateModel(
            name='DomainDescription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(default='0', help_text="See: <a href='http://hdl.handle.net/11459/CCR_C-2467_f4e7331f-b930-fc42-eeea-05e383cfaa78'>Domain</a>", verbose_name='Domain')),
            ],
        ),
        migrations.RemoveField(
            model_name='domain',
            name='name',
        ),
        migrations.AddField(
            model_name='domain',
            name='name',
            field=models.ManyToManyField(blank=True, to='collection.DomainDescription'),
        ),
    ]