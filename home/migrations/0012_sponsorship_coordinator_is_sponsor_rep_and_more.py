# Generated by Django 4.2.15 on 2025-01-30 06:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0011_participation_number_interns_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sponsorship',
            name='coordinator_is_sponsor_rep',
            field=models.BooleanField(default=False, verbose_name='Are you a representative of the sponsoring organization?'),
        ),
        migrations.AddField(
            model_name='sponsorship',
            name='legal_info',
            field=models.TextField(blank=True, max_length=800),
        ),
        migrations.AlterField(
            model_name='sponsorship',
            name='donation_for_any_outreachy_internship',
            field=models.PositiveIntegerField(default=0, verbose_name='Donation amount ($ USD) for all Outreachy internships'),
        ),
        migrations.AlterField(
            model_name='sponsorship',
            name='due_date',
            field=models.DateField(blank=True, help_text='Due date to provide an invoice to the sponsoring organization', null=True),
        ),
        migrations.AlterField(
            model_name='sponsorship',
            name='due_date_info',
            field=models.TextField(blank=True, help_text='Please provide any additional information about due dates for this sponsorship', max_length=800, verbose_name='Information about due dates'),
        ),
        migrations.AlterField(
            model_name='sponsorship',
            name='funding_decision_date',
            field=models.DateField(blank=True, help_text='Date by which you will know if this funding is confirmed.', null=True),
        ),
        migrations.AlterField(
            model_name='sponsorship',
            name='sponsor_contact',
            field=models.TextField(blank=True, max_length=800),
        ),
        migrations.AlterField(
            model_name='sponsorship',
            name='sponsor_relationship',
            field=models.TextField(blank=True, max_length=800),
        ),
    ]
