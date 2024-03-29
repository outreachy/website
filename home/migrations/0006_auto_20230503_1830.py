# Generated by Django 3.2.16 on 2023-05-03 18:30

import ckeditor.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0005_auto_20230405_2114'),
    ]

    operations = [
        migrations.AddField(
            model_name='sponsorship',
            name='organizer_notes',
            field=ckeditor.fields.RichTextField(blank=True, help_text='Private Outreachy organizer notes, shared with Software Freedom Conservancy, and not community coordinators'),
        ),
        migrations.AddField(
            model_name='sponsorship',
            name='status',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='sponsorship',
            name='ticket_number',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
