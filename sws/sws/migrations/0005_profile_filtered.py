# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-03-08 10:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sws', '0004_auto_20170307_1529'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='filtered',
            field=models.CharField(default=b'U', max_length=8),
        ),
    ]