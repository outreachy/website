# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-10-31 21:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0114_roundpage_coordinator_funding_deadline'),
    ]

    operations = [
        migrations.AddField(
            model_name='roundpage',
            name='mentor_intern_selection_deadline',
            field=models.DateField(default='2017-11-02', verbose_name='Date mentors must select their intern by'),
        ),
    ]