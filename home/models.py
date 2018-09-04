from __future__ import absolute_import, unicode_literals

from os import urandom
from base64 import urlsafe_b64encode
from collections import Counter
import datetime
from email.headerregistry import Address
import random
import os.path

from django.contrib.auth.models import User
from django.core import validators
from django.db import models
from django.forms import ValidationError
from django.shortcuts import redirect
from django.urls import reverse
from itertools import chain, groupby
from urllib.parse import urlsplit

from ckeditor.fields import RichTextField as CKEditorField

from modelcluster.fields import ParentalKey

from languages.fields import LanguageField

from timezone_field.fields import TimeZoneField

from wagtail.wagtailcore.models import Orderable
from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailadmin.edit_handlers import InlinePanel
from wagtail.wagtailcore import blocks
from wagtail.wagtailadmin.edit_handlers import StreamFieldPanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailimages.blocks import ImageChooserBlock
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.contrib.wagtailroutablepage.models import RoutablePageMixin, route
from wagtail.wagtailembeds.blocks import EmbedBlock

from . import email
from .feeds import WagtailFeed

class HomePage(Page):
    body = StreamField([
        ('heading', blocks.CharBlock(template="home/blocks/heading.html")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('logo', ImageChooserBlock(template="home/blocks/logo.html")),
        ('date', blocks.DateBlock()),
        ('table', TableBlock(template="home/blocks/table.html")),
        ('quote', blocks.RichTextBlock(template="home/blocks/quote.html")),
    ])
    content_panels = Page.content_panels + [
        StreamFieldPanel('body', classname="full"),
    ]

class RichTextOnly(Page):
    body = RichTextField(blank=True)
    content_panels = Page.content_panels + [
        FieldPanel('body', classname="full"),
    ]

class RoundsIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full")
    ]

class DonatePage(Page):
    intro = RichTextField(blank=True, default='<p>Individual donations can be made via PayPal, check, or wire. Donations are tax deductible, and are handled by our 501(c)(3) non-profit parent organization, Software Freedom Conservancy. Individual donations are directed to the Outreachy general fund, unless otherwise specified.</p>')
    paypal_text = RichTextField(blank=True, default='<p><strong>PayPal</strong> To donate through PayPal, please click on the "Donate" button below.</p>')
    check_text = RichTextField(blank=True, default='<p><strong>Check</strong> We can accept check donations drawn in USD from banks in the USA. Please make the check payable to "Software Freedom Conservancy, Inc." and put "Directed donation: Outreachy" in the memo field. Please mail the check to: <br/><span class="offset1">Software Freedom Conservancy, Inc.</span><br/><span class="offset1">137 Montague ST Ste 380</span><br/><span class="offset1">Brooklyn, NY 11201</span><br/><span class="offset1">USA</span></p>')
    wire_text = RichTextField(blank=True, default='<p><strong>Wire</strong> Please write to <a href="mailto:accounting@sfconservancy.org">accounting@sfconservancy.org</a> and include the country of origin of your wire transfer and the native currency of your donation to receive instructions for a donation via wire.</p>')
    outro = RichTextField(blank=True, default='<p>If you are a corporation seeking to sponsor Outreachy, please see <a href="https://www.outreachy.org/sponsor/">our sponsor page.</a></p>')

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full"),
        FieldPanel('paypal_text', classname="full"),
        FieldPanel('check_text', classname="full"),
        FieldPanel('wire_text', classname="full"),
        FieldPanel('outro', classname="full"),
    ]

class StatsRoundFifteen(Page):
    unused = RichTextField(blank=True)
    content_panels = Page.content_panels + [
        FieldPanel('unused', classname="full"),
    ]

class BlogIndex(RoutablePageMixin, Page):
    feed_generator = WagtailFeed()

    @route(r'^feed/$')
    def feed(self, request):
        return self.feed_generator(request, self)

# All dates in RoundPage below, if an exact time matters, actually represent
# the given date at 4PM UTC.
DEADLINE_TIME = datetime.time(hour=16, tzinfo=datetime.timezone.utc)

def has_deadline_passed(deadline_date):
    if not deadline_date:
        return False
    deadline = datetime.datetime.combine(deadline_date, DEADLINE_TIME)
    now = datetime.datetime.now(deadline.tzinfo)
    return deadline < now

class RoundPage(Page):
    roundnumber = models.IntegerField()
    pingnew = models.DateField("Date to start pinging new orgs", blank=True, default='2017-08-01')
    pingold = models.DateField("Date to start pinging past orgs", blank=True, default='2017-08-07')
    orgreminder = models.DateField("Date to remind orgs to submit their home pages", blank=True, default='2017-08-14')
    landingdue = models.DateField("Date community landing pages are due", blank=True, default='2017-08-28')
    appsopen = models.DateField("Date applications open", default='2017-09-07')
    lateorgs = models.DateField("Last date to add community landing pages", blank=True, default='2017-10-02')
    appsclose = models.DateField("Date applications are due", blank=True, default='2017-10-23')
    appslate = models.DateField("Date extended applications are due", blank=True, default='2017-10-30')
    internapproval = models.DateField("Date interns are approved by the Outreachy organizers", default='2017-11-05')
    internannounce = models.DateField("Date interns are announced", default='2017-11-09')
    internstarts = models.DateField("Date internships start", default='2017-12-05')
    initialfeedback = models.DateField("Date initial feedback is due", blank=True, default='2017-12-20')
    initialpayment = models.IntegerField(default=1000)
    midfeedback = models.DateField("Date mid-point feedback is due", blank=True, default='2018-01-31')
    midpayment = models.IntegerField(default=2000)
    internends = models.DateField("Date internships end", default='2018-03-05')
    finalfeedback = models.DateField("Date final feedback is due", blank=True, default='2018-03-12')
    finalpayment = models.IntegerField(default=2500)
    sponsordetails = RichTextField(default='<p>Outreachy is hosted by the <a href="https://sfconservancy.org/">Software Freedom Conservancy</a> with special support from Red Hat, GNOME, and <a href="http://otter.technology">Otter Tech</a>. We invite companies and free and open source communities to sponsor internships in the next round.</p>')

    content_panels = Page.content_panels + [
        FieldPanel('roundnumber'),
        FieldPanel('pingnew'),
        FieldPanel('pingold'),
        FieldPanel('orgreminder'),
        FieldPanel('landingdue'),
        FieldPanel('appsopen'),
        FieldPanel('lateorgs'),
        FieldPanel('appsclose'),
        FieldPanel('appslate'),
        FieldPanel('internannounce'),
        FieldPanel('internstarts'),
        FieldPanel('midfeedback'),
        FieldPanel('internends'),
        FieldPanel('finalfeedback'),
        FieldPanel('sponsordetails', classname="full"),
    ]

    def official_name(self):
        return(self.internstarts.strftime("%B %Y") + " to " + self.internends.strftime("%B %Y") + " Outreachy internships")

    def regular_deadline_reminder(self):
        return(self.appsclose - datetime.timedelta(days=7))

    def regular_deadline_second_reminder(self):
        return(self.appsclose - datetime.timedelta(days=1))

    def late_deadline_reminder(self):
        return(self.appslate - datetime.timedelta(days=1))

    def ProjectsDeadline(self):
        return(self.appsclose - datetime.timedelta(days=14))

    def has_project_submission_and_approval_deadline_passed(self):
        return has_deadline_passed(self.ProjectsDeadline())

    def LateApplicationsDeadline(self):
        return(self.appsclose + datetime.timedelta(days=7))
    
    def InternSelectionDeadline(self):
        return(self.appslate + datetime.timedelta(days=6))

    def coordinator_funding_deadline(self):
        return(self.appslate + datetime.timedelta(days=10))

    def intern_agreement_deadline(self):
        return(self.internannounce + datetime.timedelta(days=7))

    def intern_not_started_deadline(self):
        return(self.initialfeedback - datetime.timedelta(days=1))

    def intern_sfc_initial_payment_notification_deadline(self):
        return(self.initialfeedback)
    
    def initial_stipend_payment_deadline(self):
        return self.initialfeedback + datetime.timedelta(days=30)

    def midpoint_stipend_payment_deadline(self):
        return self.midfeedback + datetime.timedelta(days=30)

    def final_stipend_payment_deadline(self):
        return self.finalfeedback + datetime.timedelta(days=30)

    # There is a concern about paying interns who are in a country
    # where they are not eligible to work in (usually due to visa restrictions).
    # We need to ask interns whether they will be traveling after their internship
    # when they would normally be paid. Internships may be extended by up to five weeks.
    # Payment isn't instantaneous, but this is a little better than just saying
    # "Are you eligible to work in all the countries you are residing in
    # during the internship period?"
    def sfc_payment_last_date(self):
        return self.internends + datetime.timedelta(days=7*5)

    def has_application_period_started(self):
        return has_deadline_passed(self.appsopen)

    # Interns get a five week extension at most.
    def has_internship_ended(self):
        return has_deadline_passed(self.internends + datetime.timedelta(days=7*5))

    def has_ontime_application_deadline_passed(self):
        return has_deadline_passed(self.appsclose)

    def has_late_application_deadline_passed(self):
        return has_deadline_passed(self.appslate)

    # Is there an approved project with a late deadline, or are all projects on time?
    def has_application_deadline_passed(self):
        participations = self.participation_set.all().approved()
        for p in participations:
            projects = p.project_set.approved()
            for project in projects:
                if project.deadline == Project.LATE:
                    return has_deadline_passed(self.appslate)
        return has_deadline_passed(self.appsclose)

    def has_intern_announcement_deadline_passed(self):
        return has_deadline_passed(self.internannounce)

    def gsoc_round(self):
        # The internships would start before August
        # for rounds aligned with GSoC
        # GSoC traditionally starts either in May or June
        return(self.internstarts.month < 8)

    def get_approved_communities(self):
        approved_participations = Participation.objects.filter(participating_round=self, approval_status=Participation.APPROVED).order_by('community__name')
        return [p.community for p in approved_participations]

    def is_mentor(self, user):
        return MentorApproval.objects.filter(
                mentor__account=user,
                project__project_round__participating_round=self,
                project__project_round__approval_status=ApprovalStatus.APPROVED,
                project__approval_status=ApprovalStatus.APPROVED,
                approval_status=ApprovalStatus.APPROVED).exists()

    def get_intern_selections(self):
        return InternSelection.objects.filter(
                project__project_round__participating_round=self,
                project__approval_status=Project.APPROVED,
                project__project_round__approval_status=Participation.APPROVED).exclude(
                        funding_source=InternSelection.NOT_FUNDED).order_by('project__project_round__community__name', 'project__short_title')

    def get_general_funding_intern_selections(self):
        return self.get_intern_selections().filter(
                funding_source=InternSelection.GENERAL_FUNDED)

    def get_pending_intern_selections(self):
        return self.get_intern_selections().filter(
                organizer_approved=None)

    def get_approved_intern_selections(self):
        return self.get_intern_selections().filter(
                organizer_approved=True)

    def get_rejected_intern_selections(self):
        return self.get_intern_selections().filter(
                organizer_approved=False)

    def get_approved_interns_with_unsigned_contracts(self):
        return self.get_approved_intern_selections().filter(
                intern_contract=None)

    def get_in_good_standing_intern_selections(self):
        return self.get_approved_intern_selections().filter(
                in_good_standing=True)

    def get_communities_with_unused_funding(self):
        participations = Participation.objects.filter(
                participating_round=self,
                approval_status=Participation.APPROVED)
        communities = []
        for p in participations:
            funded = p.interns_funded()
            if funded < 1:
                continue
            intern_count = InternSelection.objects.filter(
                    project__project_round=p,
                    project__approval_status=Project.APPROVED,
                    funding_source=InternSelection.ORG_FUNDED).count()
            if intern_count < funded:
                communities.append((p.community, intern_count, funded))
        communities.sort(key=lambda x: x[0].name)
        return communities

    def travel_stipend_starts(self):
        return self.internannounce

    def travel_stipend_ends(self):
        return self.internstarts + datetime.timedelta(days=365)

    # Interns have up to 90 days to submit their travel stipend request
    def has_travel_stipend_ended(self):
        return has_deadline_passed(self.travel_stipend_ends() + datetime.timedelta(days=90))

    # Travel stipends are good for travel starting the day the internship is announced
    # Until one year after their internship begins.
    def is_travel_stipend_valid(self):
        return not has_deadline_passed(self.internstarts + datetime.timedelta(days=365))

    def get_common_skills_counter(self):
        approved_projects = Project.objects.filter(project_round__participating_round=self, approval_status=Project.APPROVED)
        skills = []
        for p in approved_projects:
            for s in p.projectskill_set.all():
                if 'python' in s.skill.lower():
                    skills.append('Python')
                elif 'javascript' in s.skill.lower() or 'JS' in s.skill:
                    skills.append('JavaScript')
                elif 'html' in s.skill.lower() or 'css' in s.skill.lower():
                    skills.append('HTML/CSS')
                elif 'java' in s.skill.lower():
                    skills.append('Java')
                elif 'django' in s.skill.lower():
                    skills.append('Django')
                elif 'c program' in s.skill.lower() or 'c language' in s.skill.lower() or 'c code' in s.skill.lower() or 'programming in c' in s.skill.lower() or s.skill == 'C':
                    skills.append('C programming')
                elif 'c++' in s.skill.lower():
                    skills.append('C++')
                elif 'rust' in s.skill.lower():
                    skills.append('Rust')
                elif 'ruby on rails' in s.skill.lower():
                    skills.append('Ruby on Rails')
                elif 'ruby' in s.skill.lower():
                    skills.append('Ruby')
                elif 'operating systems' in s.skill.lower() or 'kernel' in s.skill.lower():
                    skills.append('Operating Systems knowledge')
                elif 'linux' in s.skill.lower():
                    skills.append('Linux')
                elif 'web development' in s.skill.lower():
                    skills.append('Web development')
                elif 'gtk' in s.skill.lower() or 'gobject' in s.skill.lower():
                    skills.append('GTK programming')
                elif 'git' in s.skill.lower():
                    skills.append('Git')
                elif 'writing' in s.skill.lower() or 'documentation' in s.skill.lower():
                    skills.append('Documentation')
                else:
                    skills.append(s.skill)

                # A lot of projects list Android in conjunction with another skill
                if 'android' in s.skill.lower():
                    skills.append('Android')
                # Some projects list both Git or mercurial
                if 'mercurial' in s.skill.lower():
                    skills.append('Mercurial')
                # Some projects list both JavaScipt and node.js
                if 'node.js' in s.skill.lower():
                    skills.append('node.js')
        return Counter(skills)

    # Statistics functions
    def get_common_skills(self):
        skill_counter = self.get_common_skills_counter()
        return skill_counter.most_common(20)

    def get_statistics_on_eligibility_check(self):
        count_all = ApplicantApproval.objects.filter(
                application_round=self).count()
        count_approved = ApplicantApproval.objects.filter(
                approval_status=ApplicantApproval.APPROVED,
                application_round=self).count()
        count_rejected_all = ApplicantApproval.objects.filter(
                approval_status=ApplicantApproval.REJECTED,
                application_round=self).count()
        count_rejected_demographics = ApplicantApproval.objects.filter(
                approval_status=ApplicantApproval.REJECTED,
                reason_denied="DEMOGRAPHICS",
                application_round=self).count()
        count_rejected_time = ApplicantApproval.objects.filter(
                approval_status=ApplicantApproval.REJECTED,
                reason_denied="TIME",
                application_round=self).count()
        count_rejected_general = ApplicantApproval.objects.filter(
                approval_status=ApplicantApproval.REJECTED,
                reason_denied="GENERAL",
                application_round=self).count()
        if count_rejected_all == 0:
            return (count_all, count_approved, 0, 0, 0)
        return (count_all, count_approved, count_rejected_demographics * 100 / count_rejected_all, count_rejected_time * 100 / count_rejected_all, count_rejected_general * 100 / count_rejected_all)

    def get_countries_stats(self):
        all_apps = ApplicantApproval.objects.filter(
                application_round=self,
                approval_status=ApplicantApproval.APPROVED)
        countries = []
        cities = []
        timezone_regions = []
        for a in all_apps:
            us_state_abbrevs = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'AS', 'DC', 'FM', 'GU', 'MH', 'MP', 'PW', 'PR', 'VI', ]
            us_states = [ 'alabama', 'alaska', 'arizona', 'arkansas', 'california', 'colorado', 'connecticut', 'delaware', 'florida', 'georgia', 'hawaii', 'idaho', 'illinois', 'indiana', 'iowa', 'kansas', 'kentucky', 'louisiana', 'maine', 'maryland', 'massachusetts', 'michigan', 'minnesota', 'mississippi', 'missouri', 'montana', 'nebraska', 'nevada', 'new hampshire', 'new jersey', 'new mexico', 'new york', 'north carolina', 'north dakota', 'ohiooH', 'oklahoma', 'oregon', 'pennsylvania', 'rhode island', 'south carolina', 'south dakota', 'tennessee', 'texas', 'utah', 'vermont', 'virginia', 'washington', 'west virginia', 'wisconsin', 'wyoming', 'american samoa', 'district of columbia', 'federated states of micronesia', 'guam', 'marshall islands', 'northern mariana islands', 'palau', 'puerto rico', 'virgin islands', ]

            us_cities = [
                    'boston',
                    'los angeles',
                    'san francisco',
                    'new york city',
                    'united states',
                    'philadelphia',
                    'madison',
                    ]
            us_timezones = [
                    'America/Los_Angeles',
                    'America/Chicago',
                    'America/New_York',
                    'US/Eastern',
                    'US/Central',
                    'US/Pacific',
                    ]

            indian_cities = [
                    'india',
                    'india.',
                    'new delhi',
                    'hyderabad',
                    'bangalore',
                    'delhi',
                    'mumbai',
                    'hyderabad',
                    'chennai',
                    'noida',
                    'kerala',
                    'pune',
                    'jaipur',
                    'maharashtra',
                    'new delhi india',
                    'bengaluru',
                    ]
            location = a.applicant.location.split(',')
            if location == '':
                city = ''
            else:
                city = location[0].strip().lower()

            country = ''
            if len(location) >= 3:
                country = location[-1].strip().lower()
            elif len(location) == 2:
                country = location[-1].strip().lower()
                if country.upper() in us_state_abbrevs or country in us_states:
                    country = 'usa'

            scrubbed_city = ''
            if country:
                if country == 'usa' or country == 'united states' or country == 'united states of america' or country == 'us' or country in us_states:
                    country = 'usa'
                if country == 'india.' or country == 'delhi and india':
                    country = 'india'
            elif city == 'buenos aires' or city.startswith('argentina'):
                country = 'argentina'
            # Brazilians like to use dashes instead of commas??
            elif city.startswith('são paulo') or city.startswith('curitiba') or city == 'brazil' or city == 'brasil':
                country = 'brazil'
            # There's a Vancouver, WA, but it's more likely to be Canada
            elif city == 'vancouver' or city == 'canada':
                country = 'canada'
            elif city == 'egypt':
                country = 'egypt'
            elif city == 'berlin':
                country = 'germany'
            elif city in indian_cities:
                country = 'india'
            elif city == 'israel':
                country = 'israel'
            elif city == 'mombasa' or city == 'nairobi' or city == 'kenya':
                country = 'kenya'
            elif city == 'mexico city' or city == 'mexico':
                country = 'mexico'
            elif city.startswith('lagos') or city == 'port harcourt' or city == 'ibadan' or city == 'nigeria':
                country = 'nigeria'
            # technically there's a saint petersberg FL, but it's more likely to be Russia
            elif city == 'moscow' or city == 'saint petersburg' or city == 'saint-petersburg' or city == 'russia':
                country = 'russia'
            elif city == 'istanbul' or city == 'turkey':
                country = 'turkey'
            elif city == 'kazakhstan' or city == 'united arab emirates':
                country = 'united arab emirates'
            elif city in us_cities or city in us_states:
                country = 'usa'
            else:
                if not a.applicant.timezone:
                    continue
                timezone = a.applicant.timezone.zone
                if timezone == 'America/Argentina/Buenos_Aires':
                    country = 'argentina'
                if 'Australia' in timezone:
                    country = 'australia'
                elif timezone == 'America/Sao_Paulo':
                    country = 'brazil'
                elif timezone.startswith('Canada') or timezone == 'America/Toronto':
                    country = 'canada'
                elif timezone == 'Africa/Cairo':
                    country = 'egypt'
                elif timezone == 'Europe/Berlin':
                    country = 'germany'
                elif timezone == 'Africa/Nairobi' or timezone == 'Africa/Lagos':
                    country = 'kenya'
                elif timezone == 'Asia/Kolkata' or timezone == 'Indian/Mayotte':
                    country = 'india'
                elif timezone == 'Europe/Rome':
                    country = 'italy'
                elif timezone == 'Europe/Dublin':
                    country = 'ireland'
                elif timezone == 'Indian/Antananarivo':
                    country = 'madagascar'
                elif timezone == 'Europe/Bucharest':
                    country = 'romania'
                elif timezone == 'Europe/Moscow':
                    country = 'russia'
                elif timezone == 'Europe/London':
                    country = 'uk'
                elif timezone == 'Europe/Kiev':
                    country = 'ukraine'
                elif timezone in us_timezones:
                    country = 'usa'
                else:
                    scrubbed_city = city
                    if len(timezone) > 1:
                        timezone_regions.append(timezone)

            if scrubbed_city != '':
                cities.append(scrubbed_city)
            if country != '':
                countries.append(country)

        return Counter(countries).most_common(25)

    def get_contributor_demographics(self):
        applicants = ApplicantApproval.objects.filter(
                application_round=self,
                approval_status=ApprovalStatus.APPROVED,
                contribution__isnull=False).distinct().count()

        us_apps = ApplicantApproval.objects.filter(
                models.Q(us_national_or_permanent_resident=True) | models.Q(living_in_us=True),
                application_round=self,
                approval_status=ApprovalStatus.APPROVED,
                contribution__isnull=False).distinct().count()

        us_people_of_color_apps = ApplicantApproval.objects.filter(
                us_resident_demographics=True,
                application_round=self,
                approval_status=ApprovalStatus.APPROVED,
                contribution__isnull=False).distinct().count()
        if us_apps == 0:
            return (applicants, 0, 0)

        return (applicants, (us_apps - us_people_of_color_apps) * 100 / us_apps, us_people_of_color_apps * 100 / us_apps)

    def get_contributor_gender_stats(self):
        all_apps = ApplicantApproval.objects.filter(
                application_round=self,
                approval_status=ApprovalStatus.APPROVED,
                contribution__isnull=False).distinct().count()

        cis_apps = ApplicantGenderIdentity.objects.filter(
                transgender=False,
                genderqueer=False,
                demi_boy=False,
                demi_girl=False,
                trans_masculine=False,
                trans_feminine=False,
                non_binary=False,
                demi_non_binary=False,
                genderflux=False,
                genderfluid=False,
                demi_genderfluid=False,
                demi_gender=False,
                bi_gender=False,
                tri_gender=False,
                multigender=False,
                pangender=False,
                maxigender=False,
                aporagender=False,
                intergender=False,
                mavrique=False,
                gender_confusion=False,
                gender_indifferent=False,
                graygender=False,
                agender=False,
                genderless=False,
                gender_neutral=False,
                neutrois=False,
                androgynous=False,
                androgyne=False,
                applicant__application_round=self,
                applicant__approval_status=ApprovalStatus.APPROVED,
                applicant__contribution__isnull=False).distinct().count()

        trans_folks_apps = ApplicantGenderIdentity.objects.filter(
                transgender=True,
                applicant__application_round=self,
                applicant__approval_status=ApprovalStatus.APPROVED,
                applicant__contribution__isnull=False).distinct().count()

        genderqueer_folks_apps = ApplicantGenderIdentity.objects.filter(
                genderqueer=True,
                applicant__application_round=self,
                applicant__approval_status=ApprovalStatus.APPROVED,
                applicant__contribution__isnull=False).distinct().count()

        return (cis_apps * 100 / all_apps, trans_folks_apps * 100 / all_apps, genderqueer_folks_apps * 100 / all_apps)

    def get_contributor_applicant_funding_status(self):
        eligible = ApplicantApproval.objects.filter(
                approval_status=ApplicantApproval.APPROVED,
                application_round=self).count()

        contributed = ApplicantApproval.objects.filter(
                application_round=self,
                approval_status=ApprovalStatus.APPROVED,
                contribution__isnull=False).distinct().count()

        applied = ApplicantApproval.objects.filter(
                application_round=self,
                approval_status=ApprovalStatus.APPROVED,
                finalapplication__isnull=False).distinct().count()

        funded = 0
        participations = Participation.objects.filter(
                approval_status=Participation.APPROVED,
                participating_round=self)
        for p in participations:
            funded = funded + p.interns_funded()

        return (eligible, contributed, applied, funded)

    def serve(self, request, *args, **kwargs):
        # Only show this page if newer rounds exist.
        if RoundPage.objects.filter(internstarts__gt=self.internstarts).exists():
            return super(RoundPage, self).serve(request, *args, **kwargs)
        # Otherwise, this is the newest, so temporary-redirect to project selection view.
        return redirect('project-selection')

class CohortPage(Page):
    round_start = models.DateField("Round start date")
    round_end = models.DateField("Round end date")
    content_panels = Page.content_panels + [
            FieldPanel('round_start'),
            FieldPanel('round_end'),
            InlinePanel('participant', label="Intern or alumns information", help_text="Please add information about the alumn or intern"),
    ]

class AlumInfo(Orderable):
    page = ParentalKey(CohortPage, related_name='participant')
    name = models.CharField(max_length=255, verbose_name="Name")
    email = models.EmailField(verbose_name="Email")
    picture = models.ForeignKey(
            'wagtailimages.Image',
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name='+'
            )
    gravitar = models.BooleanField(max_length=255, verbose_name="Use gravitar image associated with email?")
    location = models.CharField(max_length=255, blank=True, verbose_name="Location (optional)")
    nick = models.CharField(max_length=255, blank=True, verbose_name="Chat/Forum/IRC username (optional)")
    blog = models.URLField(blank=True, verbose_name="Blog URL (optional)")
    rss = models.URLField(blank=True, verbose_name="RSS URL (optional)")
    community = models.CharField(max_length=255, verbose_name="Community name")
    project = models.CharField(max_length=255, verbose_name="Project description")
    mentors = models.CharField(max_length=255, verbose_name="Mentor name(s)")
    survey_opt_out = models.BooleanField(default=False)
    panels = [
            FieldPanel('name'),
            FieldPanel('email'),
            ImageChooserPanel('picture'),
            FieldPanel('gravitar'),
            FieldPanel('location'),
            FieldPanel('nick'),
            FieldPanel('blog'),
            FieldPanel('rss'),
            FieldPanel('community'),
            FieldPanel('project'),
            FieldPanel('mentors'),
            FieldPanel('survey_opt_out'),
    ]

    def round_string(self):
        return '{start:%b %Y} to {end:%b %Y}'.format(
                start=self.page.round_start,
                end=self.page.round_end)

    def __str__(self):
        return '{start:%b %Y} to {end:%b %Y}: {name}'.format(
                start=self.page.round_start,
                end=self.page.round_end,
                name=self.name)

# We can't remove this old function because the default value
# for the token field used mentor_id and so an old migration
# refers to mentor_id
# FIXME - squash migrations after applied to server
def mentor_id():
    # should be a multiple of three
    return urlsafe_b64encode(urandom(9))

# There are several project descriptions on the last round page
# that are far too long. This feels about right.
SENTENCE_LENGTH=100
# Current maximum description paragraph on round 15 page is 684.
PARAGRAPH_LENGTH=800
THREE_PARAGRAPH_LENGTH=3000
EIGHT_PARAGRAPH_LENGTH=8000
# Longest application last round was 28,949 characters
TIMELINE_LENGTH=30000
LONG_LEGAL_NAME=800
SHORT_NAME=100

def make_comrade_photo_filename(instance, original_name):
    # Use the underlying User object's primary key rather than any
    # human-readable name, because if the person changes any of their
    # names, we don't want to be revealing their old names in these
    # URLs. It's usually considered bad style to include database IDs in
    # URLs, for a variety of good reasons, but it seems like the best we
    # can do here.
    base = instance.account.id
    # Incorporate a pseudo-random number to make it harder to guess the
    # URL to somebody's old photo once they've replaced it.
    randbase = 100000000
    unique = random.randrange(randbase, 10 * randbase)
    # Preserve the original filename's extension as that usually signals
    # the file's type.
    extension = os.path.splitext(original_name)[1]
    return "comrade/{pk}/{unique}{ext}".format(pk=base, unique=unique, ext=extension)

# From Wordnik:
# comrade: A person who shares one's interests or activities; a friend or companion.
# user: One who uses addictive drugs.
class Comrade(models.Model):
    account = models.OneToOneField(User, primary_key=True)
    public_name = models.CharField(max_length=LONG_LEGAL_NAME, verbose_name="Name (public)", help_text="Your full name, which will be publicly displayed on the Outreachy website. This is typically your given name, followed by your family name. You may use a pseudonym or abbreviate your given or family names if you have concerns about privacy.")

    nick_name = models.CharField(max_length=SHORT_NAME, verbose_name="Nick name (internal)", help_text="The short name used in emails to you. You would use this name when introducing yourself to a new person, such as 'Hi, I'm (nick name)'. Emails will be addressed 'Hi (nick name)'. This name will be shown to organizers, coordinators, mentors, and volunteers.")

    legal_name = models.CharField(max_length=LONG_LEGAL_NAME, verbose_name="Legal name (private)", help_text="Your name on your government identification. This is the name that you would use to sign a legal document. This will be used only by Outreachy organizers on any private legal contracts. Other applicants, coordinators, mentors, and volunteers will not see this name.")

    photo = models.ImageField(blank=True, upload_to=make_comrade_photo_filename,
            help_text="File limit size is 1MB. For best display, use a square photo at least 200x200 pixels.")

    # Reference: https://uwm.edu/lgbtrc/support/gender-pronouns/
    PRONOUN_RAW = (
            ['she', 'her', 'her', 'hers', 'herself', 'http://pronoun.is/she'],
            ['he', 'him', 'his', 'his', 'himself', 'http://pronoun.is/he'],
            ['they', 'them', 'their', 'theirs', 'themself', 'http://pronoun.is/they'],
            ['fae', 'faer', 'faer', 'faers', 'faerself', 'http://pronoun.is/fae'],
            ['ey', 'em', 'eir', 'eirs', 'eirself', 'http://pronoun.is/ey'],
            ['per', 'per', 'pers', 'pers', 'perself', 'http://pronoun.is/per'],
            ['ve', 'ver', 'vis', 'vis', 'verself', 'http://pronoun.is/ve'],
            ['xe', 'xem', 'xyr', 'xyrs', 'xemself', 'http://pronoun.is/xe'],
            ['ze', 'hir', 'hir', 'hirs', 'hirself', 'http://pronoun.is/ze'],
            )
    PRONOUN_CHOICES = [
            (raw[0], '{subject}/{Object}/{possessive_pronoun}'.format(subject=raw[0], Object=raw[1], possessive_pronoun=raw[3]))
            for raw in PRONOUN_RAW
            ]
    pronouns = models.CharField(
            max_length=4,
            choices=PRONOUN_CHOICES,
            default='they',
            help_text="Your preferred pronoun. This will be used in emails from Outreachy organizers directly to you. The format is subject/object/possessive pronoun. Example: '__(subject)__ interned with Outreachy. The mentor liked working with __(object)__. The opportunity was __(possessive pronoun)__ to grab.",
            )

    pronouns_to_participants = models.BooleanField(
            verbose_name = "Share pronouns with Outreachy participants",
            help_text = "If this box is checked, applicant pronouns will be shared with coordinators, mentors and volunteers. If the box is checked, coordinator and mentor pronouns will be shared with applicants.<br>If the box is unchecked, no pronouns will be displayed.<br>If you don't want to share your pronouns, all Outreachy organizer email that Cc's another participant will use they/them/their pronouns for you.",
            default=True,
            )

    pronouns_public = models.BooleanField(
            verbose_name = "Share pronouns publicly",
            help_text = "Mentor, coordinator, and accepted interns' pronouns will be displayed publicly on the Outreachy website to anyone who is not logged in. Sharing pronouns can be a way for people to proudly display their gender identity and connect with other Outreachy participants, but other people may prefer to keep their pronouns private.<br>If this box is unchecked, Outreachy participants will be instructed to use they/them pronouns on public community channels. They will still know what your pronouns are if you check the previous box.",
            default=False,
            )

    timezone = TimeZoneField(blank=True, verbose_name="(Optional) Your timezone", help_text="The timezone in your current location. Shared with other Outreachy participants to help facilitate communication.")

    location = models.CharField(
            max_length=SENTENCE_LENGTH,
            blank=True,
            help_text="(Optional) Location - city, state/province, and country.<br>This field is unused for mentors and coordinators. Applicant's location will be shared with their mentors. If selected as an intern, this location will be publicly displayed on the Outreachy website.<br>If you are concerned about keeping your location private, you can share less information, such as just the country, or a larger town nearby.")

    nick = models.CharField(
            max_length=SENTENCE_LENGTH,
            blank=True,
            verbose_name="Forum, chat, or IRC username",
            help_text="(Optional) The username or 'nick' you typically use when communicating on professional channels. If you don't have one yet, leave this blank and update it later.<br>For mentors and coordinators, this will be displayed to applicants. Applicants' username/nick will be shared with their mentors and coordinators. Accepted interns' username/nick will be displayed on the Outreachy website.")

    github_url = models.URLField(blank=True,
            verbose_name="GitHub profile URL",
            help_text="(Optional) The full URL to your profile on GitHub.<br>For mentors and coordinators, this will be displayed to applicants. Applicants' GitHub URLs will be shared with their mentors and coordinators. Accepted interns' GitHub URLs will be displayed on the Outreachy website.")

    gitlab_url = models.URLField(blank=True,
            verbose_name="GitLab profile URL",
            help_text="(Optional) The full URL to your profile on GitLab.<br>For mentors and coordinators, this will be displayed to applicants. Applicants' GitLab URLs will be shared with their mentors and coordinators. Accepted interns' GitLab URLs will be displayed on the Outreachy website.")

    blog_url = models.URLField(blank=True,
            verbose_name="Blog URL",
            help_text="(Optional) The full URL to your blog.<br>For mentors and coordinators, this will be displayed to applicants. Applicants' blog URLs will be shared with their mentors and coordinators. Accepted interns' blog URLs will be displayed on the Outreachy website.")

    blog_rss_url = models.URLField(blank=True,
            verbose_name="Blog RSS URL",
            help_text="(Optional) The full URL to the RSS or ATOM feed for your blog.<br>For mentors and coordinators, this is unused. Applicants' blog RSS URLs will be unused. Accepted interns' blog RSS URLs will be used to create an aggregated feed of all Outreachy intern blogs, which will be displayed on the Outreachy website or Outreachy planetaria.")

    twitter_url = models.URLField(blank=True,
            verbose_name="Twitter profile URL",
            help_text="(Optional) The full URL to your Twitter profile.<br>For mentors and coordinators, this will be displayed to applicants, who may try to contact you via Twitter. Applicants' Twitter URLs will be shared with their mentors and coordinators. Accepted interns' Twitter URLs will be used to create an Outreachy Twitter list for accepted interns for that round. Accepted interns' Twitter URLs will not be displayed on the Outreachy website.")

    primary_language = LanguageField(blank=True, verbose_name="(Optional) Primary language", help_text="The spoken/written language you are most comfortable using. Shared with other Outreachy participants to help facilitate communication. Many Outreachy participants have English as a second language, and we want them to find others who speak their native language.")
    second_language = LanguageField(blank=True, verbose_name="(Optional) Second language", help_text="The second language you are most fluent in.")
    third_language = LanguageField(blank=True, verbose_name="(Optional) Third language", help_text="The next language you are most fluent in.")
    fourth_language = LanguageField(blank=True, verbose_name="(Optional) Fourth language", help_text="The next language you are most fluent in.")

    agreed_to_code_of_conduct = models.CharField(
            max_length=LONG_LEGAL_NAME,
            verbose_name = "Type your legal name to indicate you agree to the Code of Conduct")

    def __str__(self):
        return self.public_name + ' <' + self.account.email + '> (' + self.legal_name + ')'

    def email_address(self):
        return Address(self.public_name, addr_spec=self.account.email)

    def get_pronouns_html(self):
        return "<a href=http://pronoun.is/{short_name}>{pronouns}</a>".format(
                short_name=self.pronouns,
                pronouns=self.get_pronouns_display(),
                )

    def get_local_application_deadline(self):
        current_round = RoundPage.objects.latest('internstarts')
        utc = datetime.datetime.combine(current_round.appsclose, DEADLINE_TIME)
        if not self.timezone:
            return utc
        return utc.astimezone(self.timezone)

    def get_local_late_application_deadline(self):
        current_round = RoundPage.objects.latest('internstarts')
        utc = datetime.datetime.combine(current_round.appslate, DEADLINE_TIME)
        if not self.timezone:
            return utc
        return utc.astimezone(self.timezone)

    def has_application(self, **filters):
        # Does this Comrade have an ApplicantApproval for this round?
        current_round = RoundPage.objects.latest('internstarts')
        applications = ApplicantApproval.objects.filter(
                applicant=self, application_round=current_round, 
                **filters)
        return applications.exists()


    # We want to prompt the Comrade to fill out an ApplicantApproval
    # if they haven't already.
    # Don't advertise this for mentors or coordinators (pending or approved) in this current round
    def needs_application(self):
        if self.has_application():
            return False

        # Is this Comrade an approved mentor or coordinator?
        if self.approved_mentor_or_coordinator():
            return False
        return True


    def ineligible_application(self):
        return self.has_application(approval_status=ApprovalStatus.REJECTED)

    def pending_application(self):
        return self.has_application(approval_status=ApprovalStatus.PENDING)

    def eligible_application(self):
        return self.has_application(approval_status=ApprovalStatus.APPROVED)

    def alum_in_good_standing(self):
        # Search all rounds for an intern selection
        rounds = RoundPage.objects.all()
        for r in rounds:
            intern_selection = r.get_in_good_standing_intern_selections().filter(
                    applicant__applicant=self)
            if intern_selection:
                return True
        return False

    def approved_mentor_or_coordinator(self):
        if self.account.is_staff:
            return True

        current_round = RoundPage.objects.latest('internstarts')
        mentors = MentorApproval.objects.filter(
                mentor=self,
                approval_status=ApprovalStatus.APPROVED,
                project__approval_status=ApprovalStatus.APPROVED,
                project__project_round__approval_status=ApprovalStatus.APPROVED,
                project__project_round__participating_round=current_round,
                )
        if mentors.exists():
            return True

        coordinators = CoordinatorApproval.objects.filter(
                coordinator=self,
                approval_status=ApprovalStatus.APPROVED,
                community__participation__approval_status=ApprovalStatus.APPROVED,
                community__participation__participating_round=current_round,
                )
        if coordinators.exists():
            return True

        return False

    def get_approved_mentored_projects(self):
        current_round = RoundPage.objects.latest('internstarts')
        # Get all projects where they're an approved mentor
        # where the project is approved,
        # and the community is approved to participate in the current round.
        mentor_approvals = MentorApproval.objects.filter(mentor = self,
                approval_status = ApprovalStatus.APPROVED,
                project__approval_status = ApprovalStatus.APPROVED,
                project__project_round__participating_round = current_round,
                project__project_round__approval_status = ApprovalStatus.APPROVED,
                )
        return [m.project for m in mentor_approvals]

    def get_pending_mentored_projects(self):
        current_round = RoundPage.objects.latest('internstarts')
        # Get all projects where they're an approved mentor
        # where the project is pending,
        # and the community is approved or pending for the current round.
        # Don't count withdrawn or rejected communities.
        mentor_approvals = MentorApproval.objects.filter(mentor = self,
                approval_status = ApprovalStatus.APPROVED,
                project__approval_status = ApprovalStatus.PENDING,
                project__project_round__participating_round = current_round,
                ).exclude(
                        project__project_round__approval_status = ApprovalStatus.WITHDRAWN
                        ).exclude(
                                project__project_round__approval_status = ApprovalStatus.REJECTED
                        )
        if not mentor_approvals:
            return None

        return [m.project for m in mentor_approvals]

    def get_editable_mentored_projects(self):
        current_round = RoundPage.objects.latest('internstarts')
        # Get all projects where they're an approved mentor
        # where the project is pending,
        # and the community is approved or pending for the current round.
        # Don't count withdrawn or rejected communities.
        mentor_approvals = MentorApproval.objects.filter(
                mentor = self,
                approval_status = ApprovalStatus.APPROVED,
                project__project_round__participating_round = current_round,
                ).exclude(
                        project__project_round__approval_status = ApprovalStatus.WITHDRAWN
                        ).exclude(
                                project__project_round__approval_status = ApprovalStatus.REJECTED
                        )
        if not mentor_approvals:
            return None

        return [m.project for m in mentor_approvals]

    def get_all_mentored_projects(self):
        current_round = RoundPage.objects.latest('internstarts')
        # Get all projects where they're a mentor
        # Don't count withdrawn or rejected communities.
        mentor_approvals = MentorApproval.objects.filter(
                mentor = self,
                project__project_round__participating_round = current_round,
                ).exclude(
                        project__project_round__approval_status = ApprovalStatus.WITHDRAWN
                        ).exclude(
                                project__project_round__approval_status = ApprovalStatus.REJECTED
                        )
        if not mentor_approvals:
            return None

        return [m.project for m in mentor_approvals]

    def get_approved_coordinator_communities(self):
        current_round = RoundPage.objects.latest('internstarts')
        # Get all communities where they're an approved community
        # and the community is approved to participate in the current round.
        return Community.objects.filter(
                participation__participating_round = current_round,
                participation__approval_status = ApprovalStatus.APPROVED,
                coordinatorapproval__coordinator = self,
                coordinatorapproval__approval_status = ApprovalStatus.APPROVED,
                )

    def get_projects_contributed_to(self):
        current_round = RoundPage.objects.latest('internstarts')
        try:
            applicant = ApplicantApproval.objects.get(applicant = self,
                    application_round = current_round)
        except ApplicantApproval.DoesNotExist:
            return None
        contributions = Contribution.objects.filter(applicant=applicant).order_by('-project__deadline').order_by('project__community__name').order_by('project__short_title')
        projects = []
        for c in contributions:
            if not c.project in projects:
                projects.append(c.project)
        return projects

    def project_applied_to_for_sort(self, project):
        try:
            finalapplication = FinalApplication.objects.get(
                    applicant__applicant=self,
                    project=project)
        except FinalApplication.DoesNotExist:
            return 0
        return 1

    def get_projects_with_upcoming_and_passed_deadlines(self):
        current_round = RoundPage.objects.latest('internstarts')
        all_projects = self.get_projects_contributed_to()

        upcoming_deadlines = []
        passed_deadlines = []
        ontime_deadline = current_round.appsclose
        late_deadline = current_round.appslate
        for project in all_projects:
            if not has_deadline_passed(ontime_deadline) and (project.deadline == Project.ONTIME or project.deadline == Project.CLOSED):
                upcoming_deadlines.append(project)
            elif not has_deadline_passed(late_deadline) and project.deadline == Project.LATE:
                upcoming_deadlines.append(project)
            else:
                passed_deadlines.append(project)
        upcoming_deadlines.sort(key=lambda x: x.deadline, reverse=True)
        passed_deadlines.sort(key=lambda x: x.deadline, reverse=True)
        passed_deadlines.sort(key=lambda x: self.project_applied_to_for_sort(x), reverse=True)
        return upcoming_deadlines, passed_deadlines

    def get_projects_with_upcoming_deadlines(self):
        upcoming, passed = self.get_projects_with_upcoming_and_passed_deadlines()
        return upcoming

    def get_projects_with_passed_deadlines(self):
        upcoming, passed = self.get_projects_with_upcoming_and_passed_deadlines()
        return passed

    def get_projects_applied_to(self):
        current_round = RoundPage.objects.latest('internstarts')
        try:
            applicant = ApplicantApproval.objects.get(applicant = self,
                    application_round = current_round)
        except ApplicantApproval.DoesNotExist:
            return None
        applications = FinalApplication.objects.filter(applicant=applicant)
        projects = []
        for a in applications:
            if not a.project in projects:
                if a.approval_status == ApprovalStatus.WITHDRAWN:
                    a.project.withdrawn = True
                else:
                    a.project.withdrawn = False
                projects.append(a.project)
        return projects

    def get_intern_selection(self):
        try:
            return InternSelection.objects.get(
                applicant__applicant=self,
                funding_source__in=(InternSelection.ORG_FUNDED, InternSelection.GENERAL_FUNDED),
                organizer_approved=True)
        except ApplicantApproval.DoesNotExist:
            return None

class ApprovalStatusQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(approval_status=ApprovalStatus.APPROVED)
    def pending(self):
        return self.filter(approval_status=ApprovalStatus.PENDING)

class ApprovalStatus(models.Model):
    PENDING = 'P'
    APPROVED = 'A'
    WITHDRAWN = 'W'
    REJECTED = 'R'
    APPROVAL_STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (WITHDRAWN, 'Withdrawn'),
        (REJECTED, 'Rejected'),
    )
    approval_status = models.CharField(
            max_length=1,
            choices=APPROVAL_STATUS_CHOICES,
            default=WITHDRAWN)

    reason_denied = models.CharField(
            max_length=THREE_PARAGRAPH_LENGTH,
            blank=True,
            help_text="""
            Please explain why you are withdrawing this request. This
            explanation will only be shown to Outreachy organizers and
            approved people within this community.
            """)

    objects = ApprovalStatusQuerySet.as_manager()

    class Meta:
        abstract = True

    def submission_and_approval_deadline(self):
        """
        Override in subclasses to return a date if people ought not to be
        editing or approving this request because a deadline has passed.
        Calling code should use the has_deadline_passed helper above.
        """
        return None

    def is_approver(self, user):
        """
        Override in subclasses to return True if the given user has
        permission to approve or reject this request, False otherwise.
        """
        raise NotImplementedError

    def is_submitter(self, user):
        """
        Override in subclasses to return True if the given user has
        permission to withdraw or re-submit this request, False
        otherwise.
        """
        raise NotImplementedError

    @classmethod
    def objects_for_dashboard(cls, user):
        """
        Override in subclasses to return all instances of this model for
        which the given user is either an approver or a submitter.
        """
        raise NotImplementedError

    def get_action_url(self, action, **kwargs):
        """
        Override in subclasses to return the URL for the view which
        performs the specified action. In some subclasses, there may be
        optional extra parameters which control how the URL is
        constructed.
        """
        raise NotImplementedError

    def get_submit_url(self, **kwargs):
        return self.get_action_url('submit', **kwargs)

    def get_withdraw_url(self, **kwargs):
        return self.get_action_url('withdraw', **kwargs)

    def get_approve_url(self, **kwargs):
        return self.get_action_url('approve', **kwargs)

    def get_reject_url(self, **kwargs):
        return self.get_action_url('reject', **kwargs)

class Community(models.Model):
    name = models.CharField(
            max_length=50, verbose_name="Community name")
    slug = models.SlugField(
            max_length=50,
            unique=True,
            help_text="Community URL slug: https://www.outreachy.org/communities/SLUG/")

    description = models.CharField(
            max_length=PARAGRAPH_LENGTH,
            verbose_name="Short description of community",
            help_text="This should be three sentences for someone who has never heard of your community or the technologies involved. Do not put any links in the short description (use the long description instead).")

    long_description = CKEditorField(
            blank=True,
            verbose_name="(Optional) Longer description of community.",
            help_text="Please avoid adding educational requirements for interns to your community description. Outreachy interns come from a variety of educational backgrounds. Schools around the world may not teach the same topics. If interns need to have specific skills, your mentors need to add application tasks to test those skills.")

    website = models.URLField(
            blank=True,
            verbose_name="(Optional) Please provide the URL for your FOSS community's website")

    tutorial = CKEditorField(
            blank=True,
            verbose_name="(Optional) Description of your first time contribution tutorial",
            help_text="If your applicants need to complete a tutorial before working on contributions with mentors, please provide a description and the URL for the tutorial. For example, the Linux kernel asks applicants to complete a tutorial for compiling and installing a custom kernel, and sending in a simple whitespace change patch. Once applicants complete this tutorial, they can start to work with mentors on more complex contributions.")

    rounds = models.ManyToManyField(RoundPage, through='Participation')

    class Meta:
        verbose_name_plural = "communities"

    def __str__(self):
        return self.name

    def get_preview_url(self):
        return reverse('community-read-only', kwargs={'community_slug': self.slug})

    def is_coordinator(self, user):
        return self.coordinatorapproval_set.approved().filter(
                coordinator__account=user).exists()

    def get_coordinator_email_list(self):
        return [ca.coordinator.email_address()
                for ca in self.coordinatorapproval_set.approved()]

    def get_coordinator_names(self):
        return [ca.coordinator.public_name
                for ca in self.coordinatorapproval_set.approved()]

    def get_number_of_funded_interns(self):
        current_round = RoundPage.objects.latest('internstarts')
        return Participation.objects.get(
                participating_round=current_round,
                community=self).interns_funded()

class Notification(models.Model):
    community = models.ForeignKey(Community)
    comrade = models.ForeignKey(Comrade)
    # Ok, look, this is silly, and we don't actually need the date,
    # but I don't know what view to use to modify a through field on a model.
    date_of_signup = models.DateField("Date user signed up for notifications", auto_now_add=True)
    class Meta:
        unique_together = (
                ('community', 'comrade'),
                )

class NewCommunity(Community):
    community = models.OneToOneField(Community, primary_key=True, parent_link=True)

    SMOL = '3'
    TINY = '5'
    MEDIUM = '10'
    SIZABLE = '20'
    BIG = '50'
    LARGER = '100'
    GINORMOUS = '999'
    COMMUNITY_SIZE_CHOICES = (
        (SMOL, '1-2 people'),
        (TINY, '3-5 people'),
        (MEDIUM, '6-10 people'),
        (SIZABLE, '11-20 people'),
        (BIG, '21-50 people'),
        (LARGER, '50-100 people'),
        (GINORMOUS, 'More than 100 people'),
    )
    community_size = models.CharField(
        max_length=3,
        choices=COMMUNITY_SIZE_CHOICES,
        default=SMOL,
        verbose_name="How many people are contributing to this FOSS community regularly?",
    )

    THREE_MONTHS = '3M'
    SIX_MONTHS = '6M'
    ONE_YEAR = '1Y'
    TWO_YEARS = '2Y'
    OLD_YEARS = 'OL'
    LONGEVITY_CHOICES = (
        (THREE_MONTHS, '0-2 months'),
        (SIX_MONTHS, '3-5 months'),
        (ONE_YEAR, '6-11 months'),
        (TWO_YEARS, '1-2 years'),
        (OLD_YEARS, 'More than 2 years'),
    )
    longevity = models.CharField(
        max_length=2,
        choices=LONGEVITY_CHOICES,
        default=THREE_MONTHS,
        verbose_name="How long has this FOSS community accepted public contributions?",
    )

    participating_orgs = models.CharField(max_length=THREE_PARAGRAPH_LENGTH,
            verbose_name="What different organizations and companies participate in this FOSS community?",
            help_text="If there are many organizations, list the top five organizations who make large contributions.")

    approved_license = models.BooleanField(
            default=False,
            help_text='I assert that all Outreachy internship projects under my community will be released under either an <a href="https://opensource.org/licenses/alphabetical">OSI-approved open source license</a> that is also identified by the FSF as a <a href="https://www.gnu.org/licenses/license-list.html">free software license</a>, OR a <a href="https://creativecommons.org/share-your-work/public-domain/freeworks/">Creative Commons license approved for free cultural works</a>')
    unapproved_license_description = CKEditorField(
            blank=True,
            help_text="(Optional) If your FOSS community uses a license that is not an OSI-approved and FSF-approved license OR a Creative Commons license, please provide a description and links to the non-free licenses.")

    no_proprietary_software = models.BooleanField(help_text='I assert all Outreachy internship projects under my community will forward the interests of free and open source software, not proprietary software.')
    proprietary_software_description = CKEditorField(
            blank=True,
            help_text="(Optional) If any internship project under your community furthers the interests of proprietary software, please explain.")

    approved_advertising = models.BooleanField(
            default=False,
            help_text='I assert that my community resources do not advertise the services of only one company. Community resources are where users and developers seek help for your FOSS project. Community resources can include the community website, mailing lists, forums, documentation, or community introduction emails. It is fine to advertise the services of multiple companies or to identify sponsor companies generally.')
    unapproved_advertising_description = CKEditorField(
            blank=True,
            help_text="(Optional) If your community resources advertise the services of only one community, please explain.")

    goverance = models.URLField(blank=True, verbose_name="(Optional) Please provide the URL for a description of your community's governance model")
    code_of_conduct = models.URLField(blank=True, verbose_name="(Optional) Please provide the URL for to your community's Code of Conduct")
    cla = models.URLField(blank=True, verbose_name="(Optional) Please provide the URL for your community's Contributor License Agreement (CLA)")
    dco = models.URLField(blank=True, verbose_name="(Optional) Please provide the URL for your community's Developer Certificate of Origin (DCO) agreement")

    class Meta:
        verbose_name_plural = 'new communities'

class Participation(ApprovalStatus):
    community = models.ForeignKey(Community)
    participating_round = models.ForeignKey(RoundPage)

    def __str__(self):
        return '{start:%Y %B} to {end:%Y %B} round - {community}'.format(
                community = self.community.name,
                start = self.participating_round.internstarts,
                end = self.participating_round.internends,
                )

    def interns_funded(self):
        total_funding = self.sponsorship_set.aggregate(total=models.Sum('amount'))['total'] or 0
        # Use integer division so it rounds down.
        return total_funding // 6500

    # Plain text string to use in email to Outreachy organizers
    # to confirm this community's participation in the round
    def intern_funding_details(self):
        details = ''
        for sponsor in self.sponsorship_set.all():
            if sponsor.funding_secured:
                secured = ' (confirmed)'
            else:
                secured = ' (unconfirmed, will know by ' + str(sponsor.funding_decision_date) + ')'
            details = details + '\n' + sponsor.name + ' $' + str(sponsor.amount) + secured
        return details

    def get_absolute_url(self):
        return reverse('community-landing', kwargs={'round_slug': self.participating_round.slug, 'slug': self.community.slug})

    def get_preview_url(self):
        return self.community.get_preview_url()

    def get_action_url(self, action):
        return reverse('participation-action', kwargs={
            'community_slug': self.community.slug,
            'action': action,
            })

    def is_approver(self, user):
        return user.is_staff

    def get_approver_email_list(self):
        return [email.organizers]

    def is_submitter(self, user):
        return self.community.is_coordinator(user)

    def is_approved_coordinator(self, comrade):
        coordinators = CoordinatorApproval.objects.filter(
                coordinator=comrade,
                approval_status=ApprovalStatus.APPROVED,
                community__participation=self,
                )
        if coordinators.exists():
            return True
        return False

    # This function should only be used before applications are open
    # There are a few people who should be approved to see
    # all the details of all projects for a community
    # before the applications open:
    def approved_to_see_all_project_details(self, comrade):
        # - staff
        if comrade.account.is_staff:
            return True
        # - an approved coordinator for any approved community
        # - an approved mentor with an approved project for a different approved community
        if comrade.approved_mentor_or_coordinator():
            return True
        # - an approved mentor with an approved project for this community (pending or approved)
        mentors = MentorApproval.objects.filter(
                mentor=comrade,
                approval_status=ApprovalStatus.APPROVED,
                project__project_round=self,
                project__approval_status=ApprovalStatus.APPROVED,
                )
        if mentors.exists():
            return True
        # - an approved coordinator for this pending community
        return self.is_approved_coordinator(comrade)

    # This function should only be used before applications are open
    # If a mentor has submitted a project, but it's not approved,
    # They should be able to see all their project details
    # And have the link to edit the project
    def mentors_pending_projects(self, comrade):
        current_round = RoundPage.objects.latest('internstarts')
        # Get all projects where they're an approved mentor.
        # It's ok if the community is pending and the project isn't approved.
        mentor_approvals = MentorApproval.objects.filter(
                mentor = comrade,
                approval_status = ApprovalStatus.APPROVED,
                project__project_round__participating_round = current_round,
                project__project_round = self,
                )
        return [m.project for m in mentor_approvals]

    def is_pending_co_mentor(self, comrade):
        mentors = MentorApproval.objects.filter(
                mentor=comrade,
                approval_status=ApprovalStatus.PENDING,
                project__project_round=self,
                )
        if mentors.exists():
            return True

    # Note that is is more than just the submitter!
    # We want to notify mentors as well as coordinators
    def get_submitter_email_list(self):
        emails = self.community.get_coordinator_email_list()
        mentors = Comrade.objects.filter(
                mentorapproval__project__project_round=self,
                mentorapproval__project__approval_status=ApprovalStatus.APPROVED,
                mentorapproval__approval_status=ApprovalStatus.APPROVED).distinct()
        for m in mentors:
            emails.append(m.email_address())
        # Coordinators might get duplicate emails if they're mentors,
        # but Address isn't hashable, so we can't make a set and then a list.
        return emails

    @classmethod
    def objects_for_dashboard(cls, user):
        if user.is_staff:
            return cls.objects.all()
        return cls.objects.filter(
                community__coordinatorapproval__approval_status=ApprovalStatus.APPROVED,
                community__coordinatorapproval__coordinator__account=user,
                )

    def is_mentor(self, user):
        return MentorApproval.objects.filter(
                mentor__account=user,
                project__project_round=self,
                project__approval_status=ApprovalStatus.APPROVED,
                approval_status=ApprovalStatus.APPROVED).exists()

class Sponsorship(models.Model):
    participation = models.ForeignKey(Participation, on_delete=models.CASCADE)

    coordinator_can_update = models.BooleanField(
            help_text="""
            Can a community coordinator update this information, or is
            it provided by the Outreachy organizers?
            """)

    name = models.CharField(
            max_length=SENTENCE_LENGTH,
            verbose_name='Organization or company full legal name',
            help_text='The full sponsor name to be used on invoices.')

    amount = models.PositiveIntegerField(
            verbose_name="Sponsorship amount",
            help_text="Sponsorship for each intern is $6,500.")

    funding_secured = models.BooleanField(
            default=False,
            help_text="""
            Check this box if funding has been confirmed by the sponsoring organization.
            <br>Leave the box unchecked if the funding is tentative.
            """)

    funding_decision_date = models.DateField(
            default=datetime.date.today,
            help_text='Date by which you will know if this funding is confirmed.')

    additional_information = CKEditorField(
            blank=True,
            help_text="""
            Anything else the Outreachy organizers should know about
            this sponsorship.
            """)

    def __str__(self):
        return "{name} sponsorship for {community}".format(
                name=self.name,
                community=self.participation.community)

class Project(ApprovalStatus):
    project_round = models.ForeignKey(Participation, verbose_name="Outreachy round and community")
    mentors = models.ManyToManyField(Comrade, through='MentorApproval')

    THREE_MONTHS = '3M'
    SIX_MONTHS = '6M'
    ONE_YEAR = '1Y'
    TWO_YEARS = '2Y'
    OLD_YEARS = 'OL'
    LONGEVITY_CHOICES = (
        (THREE_MONTHS, '0-2 months'),
        (SIX_MONTHS, '3-5 months'),
        (ONE_YEAR, '6-11 months'),
        (TWO_YEARS, '1-2 years'),
        (OLD_YEARS, 'More than 2 years'),
    )
    longevity = models.CharField(
        max_length=2,
        choices=LONGEVITY_CHOICES,
        default=THREE_MONTHS,
        verbose_name="How long has your team been accepting publicly submitted contributions?",
        help_text="A community can be comprised of many different teams that each work on separate subsystems, modules, applications, libraries, tools, documentation, user experience, graphical design, and more. Typically each Outreachy project involves working with a particular team in the community. If the Outreachy intern would work with the whole community rather than a particular team, consider the community to be a team for these questions.<br><br>How long has your team been accepting publicly submitted contributions?",
    )

    SMOL = '3'
    TINY = '5'
    MEDIUM = '10'
    SIZABLE = '20'
    BIG = '50'
    LARGER = '100'
    GINORMOUS = '999'
    COMMUNITY_SIZE_CHOICES = (
        (SMOL, '1-2 people'),
        (TINY, '3-5 people'),
        (MEDIUM, '6-10 people'),
        (SIZABLE, '11-20 people'),
        (BIG, '21-50 people'),
        (LARGER, '50-100 people'),
        (GINORMOUS, 'More than 100 people'),
    )
    community_size = models.CharField(
        max_length=3,
        choices=COMMUNITY_SIZE_CHOICES,
        default=SMOL,
        verbose_name="How many regular contributors does your team have?",
    )

    intern_tasks = CKEditorField(
            max_length=THREE_PARAGRAPH_LENGTH,
            blank=True,
            help_text='(Optional) Description of possible internship tasks. What smaller tasks will they start on? What is the main task or tasks for the internship? Do you have any optional stretch goals?')

    intern_benefits = CKEditorField(
            max_length=PARAGRAPH_LENGTH,
            blank=True,
            help_text="(Optional) How will the intern benefit from working with your team on this project? Imagine you're pitching this internship to a promising candidate. What would you say to convince them to apply? For example, what technical and non-technical skills will they learn from working on this project? How will this help them further their career in open source?")

    community_benefits = CKEditorField(
            blank=True,
            max_length=PARAGRAPH_LENGTH,
            help_text='(Optional) How will this internship project benefit the FOSS community that is funding it?')

    approved_license = models.BooleanField(
            default=False,
            help_text='I assert that this Outreachy internship project will released under either an <a href="https://opensource.org/licenses/alphabetical">OSI-approved open source license</a> that is also identified by the FSF as a <a href="https://www.gnu.org/licenses/license-list.html">free software license</a>, OR a <a href="https://creativecommons.org/share-your-work/public-domain/freeworks/">Creative Commons license approved for free cultural works</a>')
    unapproved_license_description = CKEditorField(
            blank=True,
            help_text="(Optional) If this Outreachy internship project will be released under a license that is not an OSI-approved and FSF-approved license OR a Creative Commons license, please provide a description and links to the non-free licenses.")

    no_proprietary_software = models.BooleanField(
            default=False,
            help_text='I assert that this Outreachy internship project will forward the interests of free and open source software, not proprietary software.')
    proprietary_software_description = CKEditorField(
            blank=True,
            help_text="(Optional) If this internship project furthers the interests of proprietary software, please explain.")

    short_title = models.CharField(
            max_length=SENTENCE_LENGTH,
            verbose_name="Project short title",
            help_text='Short title for this internship project proposal. This should be 100 characters or less, starting with a verb like "Create", "Improve", "Extend", "Survey", "Document", etc. Assume the applicant has never heard of your technology before and keep it simple. The short title will be used in your project page URL, so keep it short.')
    slug = models.SlugField(
            max_length=50,
            verbose_name="Project URL slug")
    long_description = CKEditorField(
            blank=True,
            help_text='Description of the internship project.<br><br>Please do not place educational restrictions (such as needing a degree) on this project. Outreachy applicants are judged on their demonstrated skills, not on their educational background. If your project requires knowledge that would normally be learned during a degree, your project contribution tasks should test applicants for that knowledge.<br><br>You should exclude applicant skills and communication channels. Those will be added in the next step.<br><br>You should also exclude discussion of internship tasks, internship benefits, repository URLs, issue tracker URLs, newcomer tags, or application period contribution tasks. Those are collected in the optional fields below.')

    repository = models.URLField(blank=True, help_text="(Optional) URL for your team's repository or contribution mechanism")
    issue_tracker = models.URLField(blank=True, help_text="(Optional) URL for your team's issue tracker")
    newcomer_issue_tag = models.CharField(
            blank=True,
            max_length=SENTENCE_LENGTH,
            help_text="(Optional) What tag is used for newcomer-friendly issues for your team or for this internship project? Please use a tag and not a URL.")

    contribution_tasks = CKEditorField(
            verbose_name="How can applicants make a contribution to your project?",
            help_text='Instructions for how applicants can make contributions during the Outreachy application period.<br><br>Make sure to include links to getting started tutorials or documentation, how applicants can find contribution tasks on your project website or issue tracker, who they should ask for tasks, and everything they need to know to get started.')

    CLOSED = 'NOW'
    ONTIME = 'REG'
    LATE = 'LAT'
    DEADLINE_CHOICES = (
            (CLOSED, 'Immediately close this project to new applicants'),
            (ONTIME, 'Open applications until the application period ends'),
            (LATE, 'Extend applications through the late application deadline'),
            )
    deadline = models.CharField(
            max_length=3,
            choices=DEADLINE_CHOICES,
            verbose_name="Project deadline",
            help_text="If you have too many applicants, and your most promising applicants have recorded both a contribution and a final application, you may want to close your project to new applicants.<br>If you have too few applicants, you may want to extend your project's application deadline by one week.",
            )

    needs_more_applicants = models.BooleanField(
            default=False,
            verbose_name="Does your project need more applicants?",
            help_text='Check this box to advertise this project as needing more applicants. This is typically used by projects without a lot of strong applicants two weeks before the application deadline.<br><br>You should uncheck this box if you already have many strong applicants who have filled out a final application.')

    class Meta:
        unique_together = (
                ('slug', 'project_round'),
                )
        ordering = ['slug']

    def __str__(self):
        return '{start:%Y %B} to {end:%Y %B} round - {community} - {title}'.format(
                start = self.project_round.participating_round.internstarts,
                end = self.project_round.participating_round.internends,
                community = self.project_round.community,
                title = self.short_title,
                )

    def get_preview_url(self):
        return reverse('project-read-only', kwargs={'community_slug': self.project_round.community.slug, 'project_slug': self.slug})

    def get_landing_url(self):
        return reverse('community-landing', kwargs={'round_slug': self.project_round.participating_round.slug, 'slug': self.project_round.community.slug}) + '#' + self.slug

    def get_contributions_url(self):
        return reverse('contributions', kwargs={'round_slug': self.project_round.participating_round.slug, 'community_slug': self.project_round.community.slug, 'project_slug': self.slug})

    def get_applicants_url(self):
        return reverse('project-applicants', kwargs={'round_slug': self.project_round.participating_round.slug, 'community_slug': self.project_round.community.slug, 'project_slug': self.slug})

    def get_action_url(self, action):
        return reverse('project-action', kwargs={
            'community_slug': self.project_round.community.slug,
            'project_slug': self.slug,
            'action': action,
            })

    def submission_and_approval_deadline(self):
        return self.project_round.participating_round.ProjectsDeadline()

    def has_application_deadline_passed(self):
        return has_deadline_passed(self.application_deadline())

    def application_deadline(self):
        if self.deadline == Project.LATE:
            return self.project_round.participating_round.appslate
        return self.project_round.participating_round.appsclose

    def has_intern_announcement_deadline_passed(self):
        return has_deadline_passed(self.project_round.participating_round.internannounce)

    def is_approver(self, user):
        return self.project_round.community.is_coordinator(user)

    def get_approver_email_list(self):
        return self.project_round.community.get_coordinator_email_list()

    def is_submitter(self, user):
        # Everyone is allowed to propose new projects.
        if self.id is None:
            return True
        # XXX: Should coordinators also be allowed to edit projects?
        return self.mentorapproval_set.approved().filter(
                mentor__account=user).exists()

    def get_submitter_email_list(self):
        return [ma.mentor.email_address()
                for ma in self.mentorapproval_set.approved()]

    def required_skills(self):
        return ProjectSkill.objects.filter(project=self, required=ProjectSkill.STRONG)

    def preferred_skills(self):
        return ProjectSkill.objects.filter(project=self, required=ProjectSkill.OPTIONAL)

    def bonus_skills(self):
        return ProjectSkill.objects.filter(project=self, required=ProjectSkill.BONUS)

    def get_applicants_and_contributions_list(self):
        applicants = ApplicantApproval.objects.filter(
                contribution__project = self,
                approval_status=ApprovalStatus.APPROVED).annotate(
                        number_contributions=models.Count('contribution'))

        for a in applicants:
            try:
                fa = a.finalapplication_set.get(project=self)
                a.submitted_application = True
                if fa.rating == fa.UNRATED:
                    a.rating = "Unrated"
                else:
                    a.rating = fa.rating
                a.rating_tip = fa.get_rating_display()
                if a.finalapplication_set.filter(project=self, approval_status = ApprovalStatus.WITHDRAWN):
                    a.withdrew_application = True
                else:
                    a.withdrew_application = False

                if a.finalapplication_set.filter(project=self).exclude(applying_to_gsoc=""):
                    a.applying_to_gsoc = True
                else:
                    a.applying_to_gsoc = False
            except:
                a.submitted_application = False

        return applicants

    def get_applications(self):
        return FinalApplication.objects.filter(project = self, applicant__approval_status=ApprovalStatus.APPROVED)

    def get_sorted_applications(self):
        return FinalApplication.objects.filter(project = self, applicant__approval_status=ApprovalStatus.APPROVED).order_by("-rating")

    def get_gsoc_applications(self):
        return FinalApplication.objects.filter(project = self, applicant__approval_status=ApprovalStatus.APPROVED).exclude(applying_to_gsoc="")

    def get_withdrawn_applications(self):
        return FinalApplication.objects.filter(project = self, approval_status=ApprovalStatus.WITHDRAWN)

    def get_interns(self):
        return InternSelection.objects.filter(project = self).all()

    def get_approved_mentors(self):
        return self.mentorapproval_set.filter(approval_status=ApprovalStatus.APPROVED)

    def get_mentor_email_list(self):
        emails = []
        mentors = Comrade.objects.filter(
                mentorapproval__project=self,
                mentorapproval__approval_status=ApprovalStatus.APPROVED).distinct()
        for m in mentors:
            emails.append(m.email_address())
        # Coordinators might get duplicate emails if they're mentors,
        # but Address isn't hashable, so we can't make a set and then a list.
        return emails

    def get_mentor_names(self):
        return " and ".join([m.public_name for m in self.mentors.all()])


    @classmethod
    def objects_for_dashboard(cls, user):
        return cls.objects.filter(
                models.Q(
                    project_round__community__coordinatorapproval__approval_status=ApprovalStatus.APPROVED,
                    project_round__community__coordinatorapproval__coordinator__account=user,
                    )
                | models.Q(
                    mentorapproval__approval_status=ApprovalStatus.APPROVED,
                    mentorapproval__mentor__account=user,
                    )
                )

class ProjectSkill(models.Model):
    project = models.ForeignKey(Project, verbose_name="Project")

    skill = models.CharField(max_length=SENTENCE_LENGTH, verbose_name="Skill description", help_text="What is one skill an the applicant needs to have in order to contribute to this internship project, or what skill will they need to be willing to learn?")

    TEACH_YOU = 'WTU'
    CONCEPTS = 'CON'
    EXPERIMENTATION = 'EXP'
    FAMILIAR = 'FAM'
    CHALLENGE = 'CHA'
    EXPERIENCE_CHOICES = (
            (TEACH_YOU, 'Mentors are willing to teach this skill to applicants with no experience at all'),
            (CONCEPTS, 'Applicants should have read about the skill'),
            (EXPERIMENTATION, 'Applicants should have used this skill in class or personal projects'),
            (FAMILIAR, 'Applicants should be able to expand on their skills with the help of mentors'),
            (CHALLENGE, 'Applicants who are experienced in this skill will have the chance to expand it further'),
            )
    experience_level = models.CharField(
            max_length=3,
            choices=EXPERIENCE_CHOICES,
            default=TEACH_YOU,
            verbose_name="Expected skill experience level",
            help_text="Choose this carefully! Many Outreachy applicants choose not to apply for an internship project unless they meet 100% of the project skill criteria.",
            )

    BONUS = 'BON'
    OPTIONAL = 'OPT'
    STRONG = 'STR'
    REQUIRED_CHOICES = (
            (BONUS, "It would be nice if applicants had this skill, but it will not impact intern selection"),
            (OPTIONAL, "Mentors will prefer applicants who have this skill"),
            (STRONG, "Mentors will only accept applicants who have this skill as an intern"),
            )
    required = models.CharField(
            max_length=3,
            choices=REQUIRED_CHOICES,
            default=BONUS,
            verbose_name="Skill impact on intern selection",
            help_text="Is this skill a hard requirement, a preference, or an optional bonus? Choose this carefully! Many Outreachy applicants choose not to apply for an internship project unless they meet 100% of the project skill criteria.",
            )

    def get_skill_level_display(self):
        if self.experience_level == self.TEACH_YOU:
            return "1"
        if self.experience_level == self.CONCEPTS:
            return "2"
        if self.experience_level == self.EXPERIMENTATION:
            return "3"
        if self.experience_level == self.FAMILIAR:
            return "4"
        if self.experience_level == self.CHALLENGE:
            return "5"

    def __str__(self):
        return '{start:%Y %B} to {end:%Y %B} round - {community} - {title} - {skill}'.format(
                start = self.project.project_round.participating_round.internstarts,
                end = self.project.project_round.participating_round.internends,
                community = self.project.project_round.community,
                title = self.project.short_title,
                skill = self.skill,
                )

def mentor_read_instructions(value):
    if value is False:
        raise ValidationError('Please read this to understand your duties as mentor.')

def mentor_read_contract(value):
    if value is False:
        raise ValidationError('Please read the mentor contract to ensure you will be comfortable signing this legal document.')

# This through table records whether a mentor is approved for this project.
# If a mentor creates a project, we set them as approved. The coordinator then reviews the Project.
# If a co-mentor signs up to join a project, we set them as unapproved.
# We want the coordinator to review any co-mentors to ensure
# we don't have a random person signing up who can now see project applications.
class MentorApproval(ApprovalStatus):
    # If a Project or a Comrade gets deleted, delete this through table.
    mentor = models.ForeignKey(Comrade, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    # TODO
    # Add information about how to contact the mentor for this project
    # e.g. I'm <username> on IRC
    # This will require a new MentorApprovalUpdate view and permissions
    # FIXME add a validator for this field that requires it to be checked
    instructions_read = models.BooleanField(
            default=False,
            validators=[mentor_read_instructions],
            verbose_name="Understands mentor instructions",
            help_text='I have read the <a href="/mentor/#mentor">mentor duties</a> and <a href="/mentor/mentor-faq/">mentor FAQ</a>.')

    understands_intern_time_commitment = models.BooleanField(
            default=False,
            validators=[mentor_read_instructions],
            help_text='I understand that Outreachy mentors are required to spend a minimum of 5 hours a week mentoring their intern during the three month internship period')

    understands_applicant_time_commitment = models.BooleanField(
            default=False,
            validators=[mentor_read_instructions],
            help_text='I understand that Outreachy mentors often spend 5-10 hours a week helping applicants during the six week application period')

    understands_mentor_contract = models.BooleanField(
            default=False,
            validators=[mentor_read_contract],
            help_text='I understand that Outreachy mentors will need to sign a <a href="/generic-mentor-contract-export/">mentor contract</a> after they accept an applicant as an intern')

    THREE_MONTHS = '3M'
    SIX_MONTHS = '6M'
    ONE_YEAR = '1Y'
    TWO_YEARS = '2Y'
    OLD_YEARS = 'OL'
    LONGEVITY_CHOICES = (
        (THREE_MONTHS, '0-2 months'),
        (SIX_MONTHS, '3-5 months'),
        (ONE_YEAR, '6-11 months'),
        (TWO_YEARS, '1-2 years'),
        (OLD_YEARS, 'More than 2 years'),
    )
    longevity = models.CharField(
        max_length=2,
        choices=LONGEVITY_CHOICES,
        default=THREE_MONTHS,
        verbose_name="How long have you been a contributor on this team?",
        help_text="A community can be comprised of many different teams that each work on separate subsystems, modules, applications, libraries, tools, documentation, user experience, graphical design, and more. Typically each Outreachy project involves working with a particular team in the community. If the Outreachy intern would work with the whole community rather than a particular team, consider the community to be a team for these questions.<br><br>How long have you been a contributor on this team?",
    )

    mentor_foss_contributions = models.CharField(
        max_length=PARAGRAPH_LENGTH,
        verbose_name="What contributions have you made to this team and this community?",
        help_text="If none, what contributions have you made to other FOSS communities?",
    )

    communication_channel_username = models.CharField(
        max_length=SENTENCE_LENGTH,
        blank=True,
        verbose_name="What is your username on the team communication channel?",
        help_text="What is your username on the team communication channel? (This information will be shared with applicants.)",
    )
    OUTREACHY = 'OUT'
    GOOGLE_SUMMER_OF_CODE = 'GSOC'
    RAILS_GIRLS = 'RAILS'
    OTHER_MENTOR_PROGRAM = 'UNK'
    NOT_MENTORED = 'NOT'
    MENTOR_CHOICES = (
        (OUTREACHY, 'Yes, I have mentored in a past Outreachy round'),
        (GOOGLE_SUMMER_OF_CODE, 'No, but I have mentored for Google Summer of Code or Google Code In'),
        (RAILS_GIRLS, 'No, but I have mentored for Rails Girls Summer of Code'),
        (OTHER_MENTOR_PROGRAM, 'No, but I have mentored with another mentorship program'),
        (NOT_MENTORED, 'No, I have never mentored before'),
    )
    mentored_before = models.CharField(
        max_length=5,
        choices=MENTOR_CHOICES,
        default=NOT_MENTORED,
        verbose_name="Have you been a mentor for Outreachy before?",
        help_text="Outreachy welcomes first time mentors, but this information allows the coordinator and other mentors to provide extra help to new mentors.",
    )

    mentorship_style = models.CharField(
        max_length=PARAGRAPH_LENGTH,
        verbose_name="What is your mentorship style?",
        help_text="Do you prefer short daily standups, longer weekly reports, or informal progress reports? Are you willing to try pair programming when your intern gets stuck? Do you like talking over video chat or answering questions via email? Give the applicants a sense of what it will be like to work with you during the internship.",
    )

    def __str__(self):
        return '{mentor} - {start:%Y %B} to {end:%Y %B} round - {community} - {title}'.format(
                mentor = self.mentor.public_name,
                start = self.project.project_round.participating_round.internstarts,
                end = self.project.project_round.participating_round.internends,
                community = self.project.project_round.community,
                title = self.project.short_title,
                )

    def get_preview_url(self):
        return reverse('mentorapproval-preview', kwargs={
            'community_slug': self.project.project_round.community.slug,
            'project_slug': self.project.slug,
            'username': self.mentor.account.username,
            })

    def get_action_url(self, action, current_user=None):
        kwargs = {
                'community_slug': self.project.project_round.community.slug,
                'project_slug': self.project.slug,
                'action': action,
                }
        if self.mentor.account != current_user:
            kwargs['username'] = self.mentor.account.username
        return reverse('mentorapproval-action', kwargs=kwargs)

    def is_approver(self, user):
        return self.project.project_round.community.is_coordinator(user)

    def get_approver_email_list(self):
        return self.project.project_round.community.get_coordinator_email_list()

    def is_submitter(self, user):
        return self.mentor.account_id == user.id

    def get_submitter_email_list(self):
        return [self.mentor.email_address()]

    @classmethod
    def objects_for_dashboard(cls, user):
        return cls.objects.filter(
                models.Q(
                    project__project_round__community__coordinatorapproval__approval_status=ApprovalStatus.APPROVED,
                    project__project_round__community__coordinatorapproval__coordinator__account=user,
                    )
                | models.Q(mentor__account=user)
                )

class CommunicationChannel(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    tool_name = models.CharField(
            max_length=SENTENCE_LENGTH,
            verbose_name="Communication tool name",
            help_text='The name of the communication tool your project uses. E.g. "a mailing list", "IRC", "Zulip", "Mattermost", or "Discourse"')

    url = models.CharField(
            max_length=200,
            validators=[validators.URLValidator(schemes=['http', 'https', 'irc'])],
            verbose_name="Communication channel URL",
            help_text='URL for the communication channel applicants will use to reach mentors and ask questions about this internship project. IRC URLs should be in the form irc://&lt;host&gt;[:port]/[channel]. Since many applicants have issues with IRC port blocking at their universities, IRC communication links will use <a href="https://kiwiirc.com/">Kiwi IRC</a> to direct applicants to a web-based IRC client. If this is a mailing list, the URL should be the mailing list subscription page.')

    instructions = CKEditorField(
            blank=True,
            verbose_name="Instructions on joining",
            help_text='(Optional) After following the communication channel link, are there any special instructions? For example: "Join the #outreachy channel and make sure to introduce yourself.')

    norms = CKEditorField(
            blank=True,
            verbose_name="Community norms",
            help_text="(Optional) What communication norms would a newcomer need to know about this communication channel? Example: newcomers to open source don't know they should Cc their mentor or the software maintainer when asking a question to a large mailing list. Think about what a newcomer would find surprising when communicating on this channel.")

    communication_help = models.URLField(
            blank=True,
            verbose_name="Communication tool documentation URL",
            help_text='(Optional) URL for the documentation for your communication tool. This should be user-focused documentation that explains the basic mechanisms of logging in and features. Suggestions: IRC - https://wiki.gnome.org/Outreachy/IRC; Zulip - https://chat.zulip.org/help/; Mattersmost - https://docs.mattermost.com/guides/user.html')

    def url_parsed(self):
        return urlsplit(self.url)


# This through table records whether a coordinator is approved for this community.
# Both the current coordinators and organizers (staff) can approve new coordinators.
class CoordinatorApproval(ApprovalStatus):
    # If a Project or a Comrade gets deleted, delete this through table.
    coordinator = models.ForeignKey(Comrade, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)

    def __str__(self):
        return '{coordinator} for {community}'.format(
                coordinator = self.coordinator.public_name,
                community = self.community,
                )

    def get_preview_url(self):
        return reverse('coordinatorapproval-preview', kwargs={
            'community_slug': self.community.slug,
            'username': self.coordinator.account.username,
            })

    def get_action_url(self, action, current_user=None):
        kwargs = {
                'community_slug': self.community.slug,
                'action': action,
                }
        if self.coordinator.account != current_user:
            kwargs['username'] = self.coordinator.account.username
        return reverse('coordinatorapproval-action', kwargs=kwargs)

    def is_approver(self, user):
        return user.is_staff or self.community.is_coordinator(user)

    def get_approver_email_list(self):
        return self.community.get_coordinator_email_list() + [email.organizers]

    def is_submitter(self, user):
        return self.coordinator.account_id == user.id

    def get_submitter_email_list(self):
        return [self.coordinator.email_address()]

    @classmethod
    def objects_for_dashboard(cls, user):
        if user.is_staff:
            return cls.objects.all()
        return cls.objects.filter(
                models.Q(
                    community__coordinatorapproval__approval_status=ApprovalStatus.APPROVED,
                    community__coordinatorapproval__coordinator__account=user,
                    )
                | models.Q(coordinator__account=user)
                )

def create_time_commitment_calendar(tcs, application_round):
    application_period_length = (application_round.internends - application_round.internstarts).days + 1
    calendar = [0]*(application_period_length)
    for tc in tcs:
        date = application_round.internstarts
        for i in range(application_period_length):
            if date >= tc['start_date'] and date <= tc['end_date']:
                calendar[i] = calendar[i] + tc['hours']
            date = date + datetime.timedelta(days=1)
    return calendar

# This class stores information about whether an applicant is eligible to
# participate in this round Automated checking will set the applicant to
# Approved or Rejected, but the Outreachy organizers can move the applicant to
# either state manually.  They start out in the Withdrawn state. We can set
# them to 'Pending' if they need to send us an email (say because of being a
# citizen of a U.S. export-regulated countries).
# Once the tool sets them to rejected, they won't be able to edit the information,
# which is fine.
class ApplicantApproval(ApprovalStatus):
    applicant = models.ForeignKey(Comrade, on_delete=models.CASCADE)
    application_round = models.ForeignKey(RoundPage, on_delete=models.CASCADE)
    project_contributions = models.ManyToManyField(Project, through='Contribution')

    gsoc_or_outreachy_internship = models.NullBooleanField(
            verbose_name='Previous Google Summer of Code or Outreachy internship?',
            help_text='Have you been accepted as a Google Summer of Code intern or an Outreachy intern before? Please say yes even if you did not complete the internship.')

    # Race/Ethnicity Information
    us_resident_demographics = models.NullBooleanField(
            verbose_name='Are you Black/African American, Hispanic/Latin@, Native American, Alaska Native, Native Hawaiian, or Pacific Islander?')

    def is_approver(self, user):
        return user.is_staff

    def get_approver_email_list(self):
        return [email.organizers]

    def submission_and_editing_deadline(self):
        return self.application_round.appslate

    def time_commitment_from_model(self, tc, hours):
        return {
                'start_date': tc.start_date,
                'end_date': tc.end_date,
                'hours': hours,
                }

    def get_time_commitments(self):
        current_round = RoundPage.objects.latest('internstarts')
        noncollege_school_time_commitments = NonCollegeSchoolTimeCommitment.objects.filter(applicant=self)
        school_time_commitments = SchoolTimeCommitment.objects.filter(applicant=self)
        volunteer_time_commitments = VolunteerTimeCommitment.objects.filter(applicant=self)
        employment_time_commitments = EmploymentTimeCommitment.objects.filter(applicant=self)
        tcs = [ self.time_commitment_from_model(d, d.hours_per_week)
                for d in volunteer_time_commitments or []
                if d ]
        ctcs = [ self.time_commitment_from_model(d, d.hours_per_week)
                for d in noncollege_school_time_commitments or []
                if d ]

        etcs = [ self.time_commitment_from_model(d, 0 if d.quit_on_acceptance else d.hours_per_week)
                for d in employment_time_commitments or []
                if d ]

        stcs = [ self.time_commitment_from_model(d, 40 * ((d.registered_credits - d.outreachy_credits - d.thesis_credits) / d.typical_credits))
                for d in school_time_commitments or []
                if d ]
        calendar = create_time_commitment_calendar(chain(tcs, ctcs, etcs, stcs), current_round)

        longest_period_free = 0
        free_period_start_day = 0
        counter = 0
        for key, group in groupby(calendar, lambda hours: hours <= 20):
            group_len = len(list(group))
            if key is True and group_len > longest_period_free:
                longest_period_free = group_len
                free_period_start_day = counter
            counter = counter + group_len
        # Catch the case where the person is never free during the internship period
        if longest_period_free == 0 and free_period_start_day == 0 and counter != 0:
            longest_period_free = None
            free_period_start_date = None
            free_period_end_date = None
        else:
            free_period_start_date = current_round.internstarts + datetime.timedelta(days=free_period_start_day)
            free_period_end_date = current_round.internstarts + datetime.timedelta(days=free_period_start_day + longest_period_free - 1)
        internship_total_days = current_round.internends - current_round.internstarts

        return {
                'longest_period_free': longest_period_free,
                'free_period_start_date': free_period_start_date,
                'free_period_end_date': free_period_end_date,
                'internship_total_days': internship_total_days,
                'school_time_commitments': school_time_commitments,
                'noncollege_school_time_commitments': noncollege_school_time_commitments,
                'volunteer_time_commitments': volunteer_time_commitments,
                'employment_time_commitments': employment_time_commitments,
                }

    def __str__(self):
        return "{name} <{email}> - {status}".format(
                name=self.applicant.public_name,
                email=self.applicant.account.email,
                status=self.get_approval_status_display())

    class Meta:
        unique_together = (
                ('applicant', 'application_round'),
                )

class WorkEligibility(models.Model):
    applicant = models.OneToOneField(ApplicantApproval, on_delete=models.CASCADE, primary_key=True)

    over_18 = models.BooleanField(
            verbose_name='Will you be 18 years or older when the Outreachy internship starts?')

    eligible_to_work = models.BooleanField(
            verbose_name='Are you eligible to work for 40 hours a week in ALL the countries you will be living in for the entire internship period, and five weeks after the internship period ends?',
            help_text='<p><b>Student visas</b>: Please note that in some countries, students studying abroad on a student visa may not be eligible to work full-time (40 hours a week). If you are on a student visa, please double check with your school counselors before applying.</p><p><b>Spouse visas</b>: In some countries, spousal visas may not allow spouses to work. Please contact your immigration officer if you have any questions about whether your visa allows you to work full-time (40 hours a week).</p><p><b>International Travel</b>: Outreachy interns are not required to work while they are traveling internationally. If you travel for more than 1 week, you may need to extend your internship. Internships can be extended for up to five weeks.</p>')

    under_export_control = models.BooleanField(
            verbose_name='Are you a person or entity restricted by United States of America export controls or sanctions programs?',
            help_text='See the <a href="https://www.treasury.gov/resource-center/sanctions/Programs/Pages/Programs.aspx">US export control and sanctions list</a> for more information')

    us_sanctioned_country = models.BooleanField(
            verbose_name='Are you a citizen, resident, or national of Crimea, Cuba, Iran, North Korea, or Syria?',
            help_text="Outreachy's fiscal parent, Software Freedom Conservancy, is a 501(c)(3) U.S. non-profit. As a U.S. non-profit, Conservancy must ensure that funds are not sent to countries under U.S. sanctions programs, such as Cuba, Iran, North Korea, or Syria. If you have citizenship with Cuba, Iran, North Korea, or Syria, please answer yes, even if you are not currently living in those countries. We will follow up with additional questions.")


class PaymentEligibility(models.Model):
    applicant = models.OneToOneField(ApplicantApproval, on_delete=models.CASCADE, primary_key=True)
    us_national_or_permanent_resident = models.BooleanField(
            verbose_name='Are you a national or permanent resident of the United States of America?',
            help_text='Outreachy is open to applicants around the world. This question is only to determine which tax form you will need to fill out.')

    living_in_us = models.BooleanField(
            verbose_name='Will you be living in the United States of America during the Outreachy internship period, or for up to five weeks after the internship period ends?',
            help_text='Please answer yes even if you are a citizen of a country other than the USA.')

class ApplicantGenderIdentity(models.Model):
    applicant = models.OneToOneField(ApplicantApproval, on_delete=models.CASCADE, primary_key=True)

    transgender = models.BooleanField(
            verbose_name='Do you identify as transgender?',
            help_text='If you are questioning whether you are transgender, please say yes.')

    genderqueer = models.BooleanField(
            verbose_name='Do you identify as genderqueer?',
            help_text='Do you identify as genderqueer, gender non-conforming, gender diverse, gender varient, or gender expansive? If you are questioning whether you identify with any of those terms, please say yes.')

    man = models.BooleanField()

    woman = models.BooleanField()

    demi_boy = models.BooleanField()

    demi_girl = models.BooleanField()

    trans_masculine = models.BooleanField()

    trans_feminine = models.BooleanField()

    non_binary = models.BooleanField()

    demi_non_binary = models.BooleanField()

    genderflux = models.BooleanField()

    genderfluid = models.BooleanField()

    demi_genderfluid = models.BooleanField()

    demi_gender = models.BooleanField()

    bi_gender = models.BooleanField()

    tri_gender = models.BooleanField()

    multigender = models.BooleanField()

    pangender = models.BooleanField()

    maxigender = models.BooleanField()

    aporagender = models.BooleanField()

    intergender = models.BooleanField()

    mavrique = models.BooleanField()

    gender_confusion = models.BooleanField()

    gender_indifferent = models.BooleanField()

    graygender = models.BooleanField()

    agender = models.BooleanField()

    genderless = models.BooleanField()

    gender_neutral = models.BooleanField()

    neutrois = models.BooleanField()

    androgynous = models.BooleanField()

    androgyne = models.BooleanField()

    prefer_not_to_say = models.BooleanField()

    self_identify = models.CharField(max_length=SENTENCE_LENGTH,
            blank=True,
            help_text="If your gender identity is NOT listed above, what is your gender identity? Please note that 'gender identity' is NOT your name. Gender identity is your gender.")

    # FIXME: iterate over the fields in self
    # if they're true, return a comma separated list of gender identities,
    # e.g. 'non-binary, agender, and that you self-identify as gender fuck'
    # Need to take into account 'prefer not to say' also marked with other genders?
    def __str__(self):
        return self.self_identify

class TimeCommitmentSummary(models.Model):
    applicant = models.OneToOneField(ApplicantApproval, on_delete=models.CASCADE, primary_key=True)

    enrolled_as_student = models.BooleanField(
            verbose_name='Are you (or will you be) a university or college student during the internship period?',
            help_text='Will you be enrolled in a university or college during the Outreachy internship period? University and college students will be asked questions about the number of credits they are taking. Please state yes even if only a few days overlap with the internship period.')

    enrolled_as_noncollege_student = models.BooleanField(
            verbose_name='Are you enrolled in a coding school or self-paced online courses?',
            help_text='Will you be enrolled in a coding school or self-paced online classes during the Outreachy internship period? If you are taking classes without receiving credits, select this option.')

    employed = models.BooleanField(
            help_text='Will you be an employee (for any number of hours) during the Outreachy internship period?')

    contractor = models.BooleanField(
            help_text='Will you be a contractor during the Outreachy internship period?')

    volunteer_time_commitments = models.BooleanField(
            help_text='Will you have any volunteer positions (such as volunteering with a non-profit or community center, participating in a community band, or volunteering to organize an event) that require more than 10 hours a week during the Outreachy internship period? Do not count your Outreachy internship time as a volunteer position.')

    # FIXME: this field was never used in a view??
    other_time_commitments = models.TextField(
            max_length=THREE_PARAGRAPH_LENGTH,
            blank=True,
            help_text="(Optional) If you have other time commitments outside of school, work, or volunteer hours, please use this field to let your mentor know. Examples of other time commitments include vacation that lasts longer than a week, coding school time commitments, community or online classes, etc.")

class VolunteerTimeCommitment(models.Model):
    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)
    start_date = models.DateField(help_text="Date your volunteer time commitments start. Use YYYY-MM-DD format.")
    end_date = models.DateField(help_text="Date your volunteer time commitments end. Use YYYY-MM-DD format.")
    hours_per_week = models.IntegerField(
            help_text="Maximum hours per week spent volunteering.",
            validators=[validators.MinValueValidator(1)],
            )
    description = models.TextField(
            max_length=THREE_PARAGRAPH_LENGTH,
            blank=True,
            help_text="Please describe what kind of volunteer position and duties you have.")

class EmploymentTimeCommitment(models.Model):
    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)
    start_date = models.DateField(help_text="Start date of employment period. Use YYYY-MM-DD format.")
    end_date = models.DateField(help_text="End date of employment period. Use YYYY-MM-DD format.")
    hours_per_week = models.IntegerField(
            help_text="Number of hours per week required by your employment contract",
            validators=[validators.MinValueValidator(1)],
            )
    quit_on_acceptance = models.BooleanField(
            help_text="I will quit this job or contract if I am accepted as an Outreachy intern.")

class NonCollegeSchoolTimeCommitment(models.Model):
    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)
    start_date = models.DateField(help_text="Date your coding school or online course starts. Use YYYY-MM-DD format.")
    end_date = models.DateField(help_text="Date your coding school or online course ends. Use YYYY-MM-DD format.")
    hours_per_week = models.IntegerField(
            help_text="Maximum hours per week spent on coursework, exercises, homework, and studying for this course.",
            validators=[validators.MinValueValidator(1)],
            )
    description = models.TextField(
            max_length=THREE_PARAGRAPH_LENGTH,
            blank=True,
            help_text="Please describe the course. Include the name and a link to the website of your coding school or organization offering online courses. Add the course name and a short description of course work.")

class SchoolTimeCommitment(models.Model):
    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)

    term_name = models.CharField(
            max_length=SENTENCE_LENGTH,
            verbose_name="Term name or term number",
            help_text="If your university uses term names (e.g. Winter 2018 term of your Sophomore year), enter your current term name, year in college, and term year. If your university uses term numbers (e.g. 7th semester), enter the term number.")
    
    start_date = models.DateField(
            verbose_name="Date classes start. Use YYYY-MM-DD format.",
            help_text="What is the first possible day of classes for all students?<br>If you started this term late (or will start this term late), use the date that classes start for all students, not the late registration date.<br>If students who are in different school years or different semester numbers start classes on different dates, use the first possible date that students in your year or semester start classes.<br>If you do not know when the term will start, use the start date of that term from last year.")
    
    end_date = models.DateField(
            verbose_name="Date all exams end. Use YYYY-MM-DD format.",
            help_text="This is the date your university advertises for the last possible date of any exam for any student in your semester. Use the last possible exam date, even if your personal exams end sooner.")
    
    typical_credits = models.IntegerField(
            validators=[validators.MinValueValidator(1)],
            verbose_name="Number of credits for a typical student",
            help_text="How many credits does a typical student register for?<br> If your university has different credit requirements for each semester for students in your major, use the number of credits that are listed on your syllabus or class schedule.")

    registered_credits = models.IntegerField(
            validators=[validators.MinValueValidator(1)],
            verbose_name="Number of credits you're registered for",
            help_text="What is the total number of credits you are enrolled for this term?<br>If you aren't registered yet, please provide an approximate number of credits?")

    outreachy_credits = models.PositiveIntegerField(
            verbose_name="Number of internship or project credits for Outreachy",
            help_text="If you are going to seek university credit for your Outreachy internship, how many credits will you earn?")

    thesis_credits = models.PositiveIntegerField(
            verbose_name="Number of graduate thesis or research credits",
            help_text="If you are a graduate student, how many credits will you earn for working on your thesis or research (not including the credits earned for the Outreachy internship)?")

class SchoolInformation(models.Model):
    applicant = models.OneToOneField(ApplicantApproval, on_delete=models.CASCADE, primary_key=True)

    university_name = models.CharField(
            max_length=SENTENCE_LENGTH,
            help_text='University or college name')

    university_website = models.URLField(help_text="University or college website")

    degree_name = models.CharField(
            max_length=SENTENCE_LENGTH,
            help_text='What degree(s) are you pursuing?')

    def print_terms(school_info):
        print(school_info.applicant.get_approval_status_display(), " ", school_info.applicant.applicant.public_name, " <", school_info.applicant.applicant.account.email, ">")
        print(school_info.university_name)
        terms = SchoolTimeCommitment.objects.filter(applicant__applicant__account__email=school_info.applicant.applicant.account.email)
        for t in terms:
            print("Term: ", t.term_name, "; Start date: ", t.start_date, "; End date: ", t.end_date)
            print("Typical " + str(t.typical_credits) + "; registered " + str(t.registered_credits) + "; outreachy " + str(t.outreachy_credits) + "; thesis " + str(t.thesis_credits))

    def print_university_students(school_name):
        apps = SchoolInformation.objects.filter(university_name__icontains=school_name).orderby('applicant__approval_status')
        for a in apps.all():
            self.print_terms(a)
            print("")

    def print_country_university_students(country):
        apps = SchoolInformation.objects.filter(applicant__applicant__location__icontains=country).orderby('applicant__approval_status')
        for a in apps.all():
            self.print_terms(a)
            print("")

class ContractorInformation(models.Model):
    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)

    typical_hours = models.IntegerField(
            validators=[validators.MinValueValidator(1)],
            verbose_name="Average number of hours spent on contractor business",
            help_text="During the past three months, what is the average number of hours/week you have spent on contracted work and unpaid business development or business marketing? You will be able to enter your known contract hours for the Outreachy internship period on the next page.")

    continuing_contract_work = models.NullBooleanField(
            verbose_name="Will you be doing contract work during the Outreachy internship period?")

class Contribution(models.Model):
    applicant = models.ForeignKey(ApplicantApproval)
    project = models.ForeignKey(Project)

    date_started = models.DateField(verbose_name="Date contribution was started (in YYYY-MM-DD format)")
    date_merged = models.DateField(verbose_name="Date contribution was accepted or merged (in YYYY-MM-DD format)",
            help_text="If this contribution is still in progress, you can leave this field blank and edit it later.",
            blank=True,
            null=True)

    url = models.URLField(
            verbose_name="Contribution URL",
            help_text="A link to the publicly submitted contribution. The contribution can be work in progress. The URL could a link to a GitHub/GitLab issue or pull request, a link to the mailing list archives for a patch, a Gerrit pull request or issue, a contribution change log on a wiki, a review of graphical design work, a posted case study or user experience study, etc. If you're unsure what URL to put here, ask your mentor.")

    description = models.TextField(
            max_length=THREE_PARAGRAPH_LENGTH,
            help_text="Description of this contribution for review by the Outreachy coordinators and organizers during intern selection. If you used advanced tools to create this contribution, mention them here.")

    def get_application(self):
        try:
            return FinalApplication.objects.get(
                    project=self.project,
                    applicant=self.applicant)
        except FinalApplication.DoesNotExist:
            return None

    def get_submission_and_approval_deadline(self):
        return self.project.project_round.participating_round.internannounce

    def __str__(self):
        return '{applicant} contribution for {community} - {project}'.format(
                applicant = self.applicant.applicant.public_name,
                community = self.project.project_round.community,
                project = self.project.short_title,
                )

class FinalApplication(ApprovalStatus):
    applicant = models.ForeignKey(ApplicantApproval)
    project = models.ForeignKey(Project)

    experience = models.TextField(
            max_length=EIGHT_PARAGRAPH_LENGTH,
            verbose_name="Experience with this community",
            help_text="Please describe your experience with this free software community and project as a user and as a contributor.")

    foss_experience = models.TextField(
            max_length=EIGHT_PARAGRAPH_LENGTH,
            verbose_name="Experience with other communities",
            help_text="Please describe your experience with any other free software projects as a user and as a contributor.")

    relevant_projects = models.TextField(
            max_length=EIGHT_PARAGRAPH_LENGTH,
            verbose_name="Relevant Projects",
            help_text="Please describe any relevant projects (either personal, work, or school projects) that helped you gain skills you will use in this project. Talk about what knowledge you gained from working on them. Include links where possible.")

    applying_to_gsoc = models.TextField(
            max_length=EIGHT_PARAGRAPH_LENGTH,
            blank=True,
            verbose_name="(Optional) Please describe which Google Summer of Code communities and projects you are applying for, and provide mentor contact information",
            help_text='If you are a student at an accredited university or college, we highly encourage you to also apply to <a href="https://summerofcode.withgoogle.com/">Google Summer of Code</a> during the May to August internship round. Many Outreachy communities participate in both programs, and applying to Google Summer of Code increases your chances of being accepted as an intern. Please note that <a href="https://developers.google.com/open-source/gsoc/help/student-stipends">Google Summer of Code has stipend amounts that vary per country</a>.<br><br>Please keep the list of communities and projects you are applying to under Google Summer of Code up-to-date, since we often try to coordinate with Google Summer of Code mentors during the intern selection period.<br><br>If this application is for the December to March internship period, or you are not applying to Google Summer of Code, please leave this question blank.')

    community_specific_questions = models.TextField(
            max_length=EIGHT_PARAGRAPH_LENGTH,
            blank=True,
            verbose_name="(Optional) Community-specific Questions",
            help_text="Some communities or projects may want you to answer additional questions. Please check with your mentor and community coordinator to see if you need to provide any additional information after you save your project application.")

    timeline = models.TextField(
            max_length=EIGHT_PARAGRAPH_LENGTH,
            blank=True,
            verbose_name="Outreachy internship project timeline",
            help_text="Please work with your mentor to provide a timeline of the work you plan to accomplish on the project and what tasks you will finish at each step. Make sure take into account any time commitments you have during the Outreachy internship round. If you are still working on your contributions and need more time, you can leave this blank and edit your application later.")

    BIT = 'BIT'
    GIRLSWHOCODE = 'GWC'
    NAJOBS = 'NAJ'
    POCIT = 'POCIT'
    WOMENWHOCODE = 'WWC'
    HYPATIA = 'HYP'
    LATINASINTECH = 'LAIT'
    LGBTQ = 'LGBTQ'
    RECURSE = 'RC'
    H4CK = 'H4CK'
    WITCH = 'WITCH'
    WIL = 'WIL'
    TAPIA = 'TAPIA'
    CONFERENCE = 'CONF'
    PRESENTATION = 'PRES'
    ALUM = 'ALUM'
    MENTOR = 'MENT'
    TEACHER = 'TEACH'
    CLASSMATE = 'STUD'
    FRIEND = 'PAL'
    TWITTER = 'TWIT'
    SEARCH = 'SEAR'
    OTHER = 'OTH'
    HEARD_CHOICES = (
        (BIT, 'Job board - Blacks in Tech'),
        (GIRLSWHOCODE, 'Job board - Girls Who Code'),
        (NAJOBS, 'Job board - Native American Jobs'),
        (POCIT, 'Job board - People of Color in Tech'),
        (WOMENWHOCODE, 'Job board - Women Who Code'),
        (HYPATIA, 'Community - Hypatia Software'),
        (LATINASINTECH, 'Community - Latinas in Tech group'),
        (LGBTQ, 'Community - LGBTQ in Tech slack'),
        (RECURSE, 'Community - Recurse Center'),
        (H4CK, 'Community - Trans*H4CK'),
        (WITCH, 'Community - Women in Tech Chat slack'),
        (WIL, 'Community - Women in Linux group'),
        (TAPIA, 'Conference - Richard Tapia Conference'),
        (CONFERENCE, 'Conference - other'),
        (PRESENTATION, 'Presentation by an Outreachy organizer, mentor, or coordinator'),
        (ALUM, 'From a former Outreachy intern'),
        (MENTOR, 'From an Outreachy mentor'),
        (TEACHER, 'From a teacher'),
        (CLASSMATE, 'From a classmate'),
        (FRIEND, 'From a friend'),
        (TWITTER, 'From Twitter'),
        (SEARCH, 'Found Outreachy from a web search'),
        (OTHER, 'Other'),
    )
    spread_the_word = models.CharField(
            verbose_name="How did you find out about Outreachy? (This will only be displayed to Outreachy Organizers.)",
            max_length=5,
            choices=HEARD_CHOICES,
            default=OTHER)

    AMAZING = '5'
    STRONG = '4'
    GOOD = '3'
    UNLIKELY = '2'
    NOTGOOD = '1'
    UNRATED = '0'
    RATING_CHOICES = (
        (AMAZING, '5 - Amazing - multiple large, high-quality contributions'),
        (STRONG, '4 - Strong - at least one large, high-quality contribution'),
        (GOOD, '3 - Good - some smaller contributions of good quality'),
        (UNLIKELY, '2 - Inexperienced - smaller contributions that vary in quality'),
        (NOTGOOD, '1 - Struggling - applicant did not understand instructions or feedback'),
        (UNRATED, 'Not rated'),
    )
    rating = models.CharField(
            max_length=1,
            choices=RATING_CHOICES,
            default=UNRATED)

    def is_approver(self, user):
        approved_mentor = self.project.mentors_set.filter(approval_status=ApprovalStatus.APPROVED, mentor=user.comrade)
        if approved_mentor:
            return True
        return False

    def is_submitter(self, user):
        if user.comrade == self.applicant.applicant:
            return True
        return False

    # We have a separate view for mentors to see applicants
    def objects_for_dashboard(cls, user):
        return None

    def get_action_url(self, action, **kwargs):
        return reverse('application-action', kwargs={
            'round_slug': self.project.project_round.participating_round.slug,
            'community_slug': self.project.project_round.community.slug,
            'project_slug': self.project.slug,
            'username': self.applicant.applicant.account.username,
            'action': action,
            })

    def submission_and_approval_deadline(self):
        return self.project.application_deadline()

    def number_contributions(self):
        return Contribution.objects.filter(
                project=self.project,
                applicant=self.applicant).count()

    def get_intern_selection(self):
        try:
            return InternSelection.objects.get(
                    applicant=self.applicant,
                    project=self.project)
        except InternSelection.DoesNotExist:
            return None

    def get_intern_selection_conflicts(self):
        current_round = RoundPage.objects.latest('internstarts')
        return InternSelection.objects.filter(
                applicant=self.applicant,
                project__project_round__participating_round=current_round).exclude(
                        funding_source=InternSelection.NOT_FUNDED).exclude(
                                project=self.project)

    def __str__(self):
        return '{applicant} application for {community} - {project} - {id}'.format(
                applicant = self.applicant.applicant.public_name,
                community = self.project.project_round.community,
                project = self.project.short_title,
                id = self.pk,
                )
    class Meta:
        unique_together = (
                ('applicant', 'project'),
                )

class SignedContract(models.Model):
    text = models.TextField(max_length=100000, verbose_name="Contract text")
    legal_name = models.CharField(max_length=LONG_LEGAL_NAME,
            verbose_name="Legal name",
            help_text="Your name on your government identification. This is the name that you would use to sign a legal document.")
    ip_address = models.GenericIPAddressField(protocol="both")
    date_signed = models.DateField(verbose_name="Date contract was signed in YYYY-MM-DD format")

class InternSelection(models.Model):
    applicant = models.ForeignKey(ApplicantApproval)
    project = models.ForeignKey(Project)
    intern_contract = models.OneToOneField(SignedContract, null=True, blank=True, on_delete=models.SET_NULL)
    mentors = models.ManyToManyField(MentorApproval, through='MentorRelationship')

    GENERAL_FUNDED = 'GEN'
    ORG_FUNDED = 'ORG'
    NOT_FUNDED = 'NOT'
    UNDECIDED_FUNDING = 'UND'
    FUNDING_CHOICES = (
        (GENERAL_FUNDED, 'Funded by the Outreachy general fund'),
        (ORG_FUNDED, 'Funded by the community sponsors'),
        (NOT_FUNDED, 'Not funded (intern will not be selected for this round)'),
        (UNDECIDED_FUNDING, 'Funding source undecided'),
    )
    funding_source = models.CharField(
        max_length=3,
        choices=FUNDING_CHOICES,
        default=UNDECIDED_FUNDING,
        help_text="How will this intern be funded?",
    )
    # None = undecided, True = accepted, False = not accepted
    organizer_approved = models.NullBooleanField(
            help_text="Is this intern and funding information confirmed to be correct by the Outreachy organizers?",
            default=None)
    survey_opt_out = models.BooleanField(default=False)
    in_good_standing = models.BooleanField(default=True)

    class Meta:
        unique_together = (
                ('applicant', 'project'),
                )

    # Intern funding is decided by Outreachy coordinators
    # but Outreachy organizers have the final yes/no approval for interns.
    def is_approver(self, user):
        return user.is_staff

    def is_submitter(self, user):
        # Allow coordinators to withdraw an intern
        if self.project.project_round.community.is_coordinator(user):
            return True
        # Allow any approved mentor to withdraw an intern
        return self.mentorapproval_set.approved().filter(
                mentor__account=user).exists()

    def intern_name(self):
        return self.applicant.applicant.public_name

    def round(self):
        return self.project.project_round.participating_round

    def community_name(self):
        return self.project.project_round.community.name

    def project_name(self):
        return self.project.short_title

    def mentor_names(self):
        return " and ".join([m.mentor.public_name for m in self.mentors.all()])

    def mentor_emails(self):
        emails = []
        for m in self.mentors.all():
            emails.append(m.mentor.email_address())
        return emails

    def get_application(self):
        return FinalApplication.objects.get(
                project=self.project,
                applicant=self.applicant,
                )

    def get_intern_selection_conflicts(self):
        if self.funding_source == self.NOT_FUNDED:
            return []
        return InternSelection.objects.filter(
                project__project_round__participating_round=self.project.project_round.participating_round,
                applicant=self.applicant,
                ).exclude(funding_source=self.NOT_FUNDED).exclude(project=self.project).all()

    def get_mentor_agreement_url(self):
        return reverse('select-intern', kwargs={
            'round_slug': self.project.project_round.participating_round.slug,
            'community_slug': self.project.project_round.community.slug,
            'project_slug': self.project.slug,
            'applicant_username': self.applicant.applicant.account.username,
            })

    def __str__(self):
        return self.mentor_names() + ' mentoring ' + self.applicant.applicant.public_name

class MentorRelationship(models.Model):
    intern_selection = models.ForeignKey(InternSelection)
    mentor = models.ForeignKey(MentorApproval)
    contract = models.OneToOneField(SignedContract)

    def intern_name(self):
        return self.intern_selection.applicant.applicant.public_name

    def round(self):
        return self.intern_selection.project.project_round.participating_round

    def community_name(self):
        return self.intern_selection.project.project_round.community.name

    def project_name(self):
        return self.intern_selection.project.short_title

    def mentor_name(self):
        return self.mentor.mentor.public_name

    def __str__(self):
        return self.mentor.mentor.public_name + ' mentoring ' + self.intern_selection.applicant.applicant.public_name
    class Meta:
        unique_together = (
                ('intern_selection', 'mentor'),
                )

# Track each person we sent a survey to
class AlumSurveyTracker(models.Model):
    # Track the alums we sent a survey invitation to
    # This can either be a person who was an intern before we had the website up
    # (in which case they'll be listed using an AlumInfo object)
    # or someone who has an account and was selected as an intern through the website.
    alumni_info = models.ForeignKey(AlumInfo, null=True, on_delete=models.CASCADE)
    intern_info = models.ForeignKey(InternSelection, null=True, on_delete=models.CASCADE)

    # Track the initial date we sent the survey out
    survey_date = models.DateTimeField(null=True, blank=True)

class AlumSurvey(models.Model):
    # This can either be a person who was an intern before we had the website up
    # (in which case they'll be listed using an AlumInfo object)
    # or someone who has an account and was selected as an intern through the website.

    survey_date = models.DateTimeField(default=datetime.date.today)
    survey_tracker = models.ForeignKey(AlumSurveyTracker)

    RECOMMEND1 = '1'
    RECOMMEND2 = '2'
    RECOMMEND3 = '3'
    RECOMMEND4 = '4'
    RECOMMEND5 = '5'
    RECOMMEND6 = '6'
    RECOMMEND7 = '7'
    RECOMMEND8 = '8'
    RECOMMEND9 = '9'
    RECOMMEND10 = '10'
    RECOMMENDATION_CHOICES = (
        (RECOMMEND1, '1 - never'),
        (RECOMMEND2, '2'),
        (RECOMMEND3, '3'),
        (RECOMMEND4, '4'),
        (RECOMMEND5, '5 - maybe'),
        (RECOMMEND6, '6'),
        (RECOMMEND7, '7'),
        (RECOMMEND8, '8'),
        (RECOMMEND9, '9'),
        (RECOMMEND10, '10 - enthusiastically'),
    )
    IMPACT0 = '0'
    IMPACT1 = '1'
    IMPACT2 = '2'
    IMPACT3 = '3'
    IMPACT4 = '4'
    IMPACT5 = '5'
    IMPACT6 = '6'
    IMPACT7 = '7'
    IMPACT8 = '8'
    IMPACT9 = '9'
    IMPACT10 = '10'
    IMPACT_CHOICES = (
        (IMPACT0, 'Decline to answer'),
        (IMPACT1, '1 - very negative impact'),
        (IMPACT2, '2'),
        (IMPACT3, '3 - negative impact'),
        (IMPACT4, '4'),
        (IMPACT5, '5 - no impact'),
        (IMPACT6, '6'),
        (IMPACT7, '7 - positive impact'),
        (IMPACT8, '8'),
        (IMPACT9, '9'),
        (IMPACT10, '10 - very positive impact'),
    )
    recommend_outreachy = models.CharField(
            max_length=2,
            verbose_name='(Required) How likely would you be to recommend a friend apply to Outreachy?',
            choices=RECOMMENDATION_CHOICES,
            default=RECOMMEND5)

    # If a question has multiple check boxes, we implement them as a series of BooleanFields.
    # The question text is a BooleanField starting with 'question'.
    # It's a bit of a hack because it creates extra database fields,
    # but it allows us to write simpler templates without hard-coding question text,
    # and we expect to create less than 1,000 survey objects per year.
    # In the template, question fields will have field.label_tag starting with 'Question'
    # We can test for this using {% if field.label_tag|truncatechars:8 == 'Question' %}
    # In order to display the checkboxes below the question text, we can test
    # if the field name starts with multi using
    # {% if field.label_tag|truncatechars:5 == 'Multi' %}
    question_event = models.BooleanField(verbose_name='During or after your Outreachy internship, have you:')
    multi_event_full_presentation = models.BooleanField(verbose_name='presented on a FOSS topic in a full-session talk, panel, workshop or another session at a conference, event, or meetup')
    multi_event_short_presentation = models.BooleanField(verbose_name='presented lightning talk or other short talk on a FOSS topic at a conference, event, or meetup')
    multi_event_organizer = models.BooleanField(verbose_name='helped organize a FOSS conference, event, or meetup')
    multi_event_attendee = models.BooleanField(verbose_name='attended a FOSS conference, event, or meetup')

    community_contact = models.BooleanField(verbose_name='(Required) In the last year, have you been in contact with your mentor or other FOSS community members you met during your Outreachy internship?')

    question_contribution = models.BooleanField(verbose_name='In the last year, have you contributed to any FOSS community by:')
    multi_contribution_forums = models.BooleanField(verbose_name='participating in project forums, mailing lists, or chat')
    multi_contribution_moderator = models.BooleanField(verbose_name='moderating or managing community forums')
    multi_contribution_issue_reporter = models.BooleanField(verbose_name='reporting issues or bugs')
    multi_contribution_tester = models.BooleanField(verbose_name='testing or creating tests')
    multi_contribution_coder = models.BooleanField(verbose_name='contributing code')
    multi_contribution_docs = models.BooleanField(verbose_name='documenting')
    multi_contribution_translator = models.BooleanField(verbose_name='translating')
    multi_contribution_artist = models.BooleanField(verbose_name='designing graphics or illustrations')
    multi_contribution_ux = models.BooleanField(verbose_name='improving user experience')
    multi_contribution_survey = models.BooleanField(verbose_name='creating user surveys')
    multi_contribution_reviewer = models.BooleanField(verbose_name='reviewing contributions')
    multi_contribution_mentor = models.BooleanField(verbose_name='mentoring')
    multi_contribution_coordinator = models.BooleanField(verbose_name='coordinating or admining for a mentorship program')
    multi_contribution_events = models.BooleanField(verbose_name='planning or volunteering to help with events')
    multi_contribution_full_talk = models.BooleanField(verbose_name='presenting in a full-session talk, panel, workshop or another session at a conference, event, or meetup')
    multi_contribution_short_talk = models.BooleanField(verbose_name='presenting a lightning talk or other short talk at a conference, event, or meetup')
    multi_contribution_leader = models.BooleanField(verbose_name='leading a project with more than one contributor')
    multi_contribution_maintainer = models.BooleanField(verbose_name='maintaining a project with more than one contributor')
    multi_contribution_advisor = models.BooleanField(verbose_name='advising the project or being a board member')
    multi_contribution_fundraiser = models.BooleanField(verbose_name='fund raising for the project')
    multi_contribution_donor = models.BooleanField(verbose_name='contributing financially to the project')
    multi_contribution_marketer = models.BooleanField(verbose_name='spreading the word about the project or helping with marketing')

    other_contribution = models.CharField(max_length=THREE_PARAGRAPH_LENGTH,
            blank=True,
            verbose_name='If you contributed to any FOSS community in another way, please let us know how you contributed:')

    question_contribution_target = models.BooleanField(verbose_name='In the last year, have you:')
    multi_contribution_target_interned_community = models.BooleanField(verbose_name='contributed to the FOSS community you interned with')
    multi_contribution_target_other = models.BooleanField(verbose_name='contributed to another FOSS community')

    question_profession = models.BooleanField(verbose_name='What is your current job or student status?')
    multi_profession_student = models.BooleanField(verbose_name='Full or part time student at a university')
    multi_profession_unemployed = models.BooleanField(verbose_name='Unemployed or taking a break from employment')
    multi_profession_consultant = models.BooleanField(verbose_name='Consultant or self-employed')
    multi_profession_employee = models.BooleanField(verbose_name='Full or part time work')

    impact_foss_appreciation = models.CharField(
            max_length=2,
            verbose_name='How much did your Outreachy internship impact your appreciation of FOSS?',
            choices=IMPACT_CHOICES,
            default=IMPACT0)

    impact_career = models.CharField(
            max_length=2,
            verbose_name='How much did your Outreachy internship impact your career?',
            choices=IMPACT_CHOICES,
            default=IMPACT0)

    impact_career = models.CharField(
            max_length=2,
            verbose_name='How much did your Outreachy internship impact your communication skills with a mentor or manager?',
            choices=IMPACT_CHOICES,
            default=IMPACT0)

    impact_career = models.CharField(
            max_length=2,
            verbose_name='How much did your Outreachy internship impact your collaboration skills with an international community?',
            choices=IMPACT_CHOICES,
            default=IMPACT0)

    impact_career = models.CharField(
            max_length=2,
            verbose_name='How much did your Outreachy internship impact your technical skills?',
            choices=IMPACT_CHOICES,
            default=IMPACT0)

    impact_career = models.CharField(
            max_length=2,
            verbose_name='How much did your Outreachy internship impact your skills as a contributor to a FOSS community?',
            choices=IMPACT_CHOICES,
            default=IMPACT0)

    STEM_JOB0 = '0'
    STEM_JOB1 = '1'
    STEM_JOB2 = '2'
    STEM_JOB_CHOICES = (
        (STEM_JOB0, "I'm not employed right now"),
        (STEM_JOB1, "No, I don't use STEM in my job"),
        (STEM_JOB2, 'Yes, I use STEM in my job'),
    )
    job_stem = models.CharField(
            max_length=2,
            verbose_name='(Required) Does your job involve science, technology, engineering, or mathematics (STEM)?',
            choices=STEM_JOB_CHOICES,
            default=STEM_JOB0)

    FOSS_USER_JOB0 = '0'
    FOSS_USER_JOB1 = '1'
    FOSS_USER_JOB2 = '2'
    FOSS_USER_JOB_CHOICES = (
        (FOSS_USER_JOB0, "I'm not employed right now"),
        (FOSS_USER_JOB1, "No, I don't use FOSS in my job"),
        (FOSS_USER_JOB2, 'Yes, I use FOSS in my job'),
    )
    job_foss_user = models.CharField(
            max_length=2,
            verbose_name='(Required) Does your job involve working with Free and Open Source Software (FOSS)?',
            choices=FOSS_USER_JOB_CHOICES,
            default=FOSS_USER_JOB0)

    FOSS_CONTRIB_JOB0 = '0'
    FOSS_CONTRIB_JOB1 = '1'
    FOSS_CONTRIB_JOB2 = '2'
    FOSS_CONTRIB_JOB_CHOICES = (
        (FOSS_CONTRIB_JOB0, "I'm not employed right now"),
        (FOSS_CONTRIB_JOB1, "No, I don't contribute to FOSS as part of my job"),
        (FOSS_CONTRIB_JOB2, 'Yes, I contribute to FOSS as part of my job'),
    )
    job_foss_contributor = models.CharField(
            max_length=2,
            verbose_name='(Required) Does your job involve contributing to Free and Open Source Software (FOSS)?',
            choices=FOSS_CONTRIB_JOB_CHOICES,
            default=FOSS_CONTRIB_JOB0)

    question_past_employers = models.BooleanField(verbose_name='After your Outreachy internship, were you ever an employee, intern, or contractor of the following companies, foundations, or projects:')
    multi_past_employer_automattic = models.BooleanField(verbose_name='Automattic')
    multi_past_employer_bloomberg = models.BooleanField(verbose_name='Bloomberg')
    multi_past_employer_cadasta = models.BooleanField(verbose_name='Cadasta')
    multi_past_employer_discourse = models.BooleanField(verbose_name='Civilized Discourse Construction Kit, Inc.')
    multi_past_employer_cncf = models.BooleanField(verbose_name='Cloud Native Computing Foundation')
    multi_past_employer_codethink = models.BooleanField(verbose_name='Codethink')
    multi_past_employer_codeweavers = models.BooleanField(verbose_name='Codeweavers')
    multi_past_employer_collabora = models.BooleanField(verbose_name='Collabora')
    multi_past_employer_cloudera = models.BooleanField(verbose_name='Cloudera')
    multi_past_employer_debian = models.BooleanField(verbose_name='Debian')
    multi_past_employer_dial = models.BooleanField(verbose_name='Digital Impact Alliance, at the United Nations Foundation')
    multi_past_employer_digitalocean = models.BooleanField(verbose_name='DigitalOcean')
    multi_past_employer_endless = models.BooleanField(verbose_name='Endless')
    multi_past_employer_eff = models.BooleanField(verbose_name='Electronic Frontier Foundation (EFF)')
    multi_past_employer_elego = models.BooleanField(verbose_name='Elego')
    multi_past_employer_ffmpeg = models.BooleanField(verbose_name='FFmpeg')
    multi_past_employer_fsf = models.BooleanField(verbose_name='Free Software Foundation (FSF)')
    multi_past_employer_github = models.BooleanField(verbose_name='GitHub')
    multi_past_employer_google = models.BooleanField(verbose_name='Google')
    multi_past_employer_goldman_sachs = models.BooleanField(verbose_name='Goldman Sachs')
    multi_past_employer_gnome = models.BooleanField(verbose_name='GNOME Foundation')
    multi_past_employer_hpe = models.BooleanField(verbose_name='Hewlett-Packard or Hewlet-Packard Enterprise')
    multi_past_employer_ibm = models.BooleanField(verbose_name='International Business Machines Corp (IBM)')
    multi_past_employer_igalia = models.BooleanField(verbose_name='Igalia')
    multi_past_employer_indeed = models.BooleanField(verbose_name='Indeed')
    multi_past_employer_intel = models.BooleanField(verbose_name='Intel Corporation')
    multi_past_employer_joomla = models.BooleanField(verbose_name='Joomla')
    multi_past_employer_kandra_labs = models.BooleanField(verbose_name='Kandra Labs')
    multi_past_employer_kde = models.BooleanField(verbose_name='KDE Eingetragener Verein (KDE e.V.).')
    multi_past_employer_libav = models.BooleanField(verbose_name='Libav')
    multi_past_employer_lightbend = models.BooleanField(verbose_name='Lightbend')
    multi_past_employer_linaro = models.BooleanField(verbose_name='Linaro')
    multi_past_employer_linux_australia = models.BooleanField(verbose_name='Linux Australia')
    multi_past_employer_linux_foundation = models.BooleanField(verbose_name='Linux Foundation')
    multi_past_employer_mapbox = models.BooleanField(verbose_name='Mapbox')
    multi_past_employer_mapzen = models.BooleanField(verbose_name='Mapzen')
    multi_past_employer_measurement_lab = models.BooleanField(verbose_name='Measurement Lab')
    multi_past_employer_microsoft = models.BooleanField(verbose_name='Microsoft')
    multi_past_employer_mifos = models.BooleanField(verbose_name='Mifos')
    multi_past_employer_mozilla = models.BooleanField(verbose_name='Mozilla')
    multi_past_employer_nescent = models.BooleanField(verbose_name='NESCent')
    multi_past_employer_node_js_foundation = models.BooleanField(verbose_name='Node.js Foundation')
    multi_past_employer_opendaylight_project = models.BooleanField(verbose_name='OpenDaylight Project')
    multi_past_employer_open_humans_foundation = models.BooleanField(verbose_name='Open Humans Foundation')
    multi_past_employer_openmrs = models.BooleanField(verbose_name='OpenMRS')
    multi_past_employer_open_source_matters = models.BooleanField(verbose_name='Open Source Matters')
    multi_past_employer_open_robotics = models.BooleanField(verbose_name='Open Robotics')
    multi_past_employer_open_technology_institute = models.BooleanField(verbose_name='Open Technology Institute')
    multi_past_employer_openitp = models.BooleanField(verbose_name='OpenITP')
    multi_past_employer_openstack_foundation = models.BooleanField(verbose_name='OpenStack Foundation')
    multi_past_employer_o_reilly = models.BooleanField(verbose_name="O'Reilly")
    multi_past_employer_owncloud = models.BooleanField(verbose_name='ownCloud')
    multi_past_employer_perl_foundation = models.BooleanField(verbose_name='Perl Foundation')
    multi_past_employer_python_software_foundation = models.BooleanField(verbose_name='Python Software Foundation')
    multi_past_employer_rackspace = models.BooleanField(verbose_name='Rackspace')
    multi_past_employer_red_hat = models.BooleanField(verbose_name='Red Hat')
    multi_past_employer_samsung = models.BooleanField(verbose_name='Samsung')
    multi_past_employer_shopify = models.BooleanField(verbose_name='Shopify')
    multi_past_employer_spi = models.BooleanField(verbose_name='Software in the Public Interest')
    multi_past_employer_tidelift = models.BooleanField(verbose_name='Tidelift')
    multi_past_employer_tor_project = models.BooleanField(verbose_name='Tor Project')
    multi_past_employer_typesafe = models.BooleanField(verbose_name='Typesafe')
    multi_past_employer_twitter = models.BooleanField(verbose_name='Twitter')
    multi_past_employer_videolan = models.BooleanField(verbose_name='VideoLAN')
    multi_past_employer_wikimedia_foundation = models.BooleanField(verbose_name='Wikimedia Foundation')
    multi_past_employer_xen_project = models.BooleanField(verbose_name='Xen Project')
    multi_past_employer_yocto_project = models.BooleanField(verbose_name='Yocto Project')

    question_achievments = models.BooleanField(verbose_name='After your Outreachy internship, did you participate in any of the following programs?')
    multi_achievement_abi = models.BooleanField(verbose_name='<a href="http://anitaborg.org/awards-grants/pass-it-on-awards-program/">Anita Borg Pass-It-On awards</a>')
    multi_achievement_ascend = models.BooleanField(verbose_name='<a href="http://ascendproject.org/about/index.html">Ascend Project</a>')
    multi_achievement_automattic = models.BooleanField(verbose_name='<a href="https://vip.wordpress.com/internships/">Automattic internships</a>')
    multi_achievement_bithub = models.BooleanField(verbose_name='<a href="https://whispersystems.org/blog/bithub/">Bithub</a>')
    multi_achievement_center_open_science = models.BooleanField(verbose_name='<a href="https://cos.io/jobs/#devintern">Center for Open Science internships</a>')
    multi_achievement_code_for_america = models.BooleanField(verbose_name='<a href="http://codeforamerica.org/fellows/apply/">Code for America Fellowship</a>')
    multi_achievement_consumer_bureau = models.BooleanField(verbose_name='<a href="http://www.consumerfinance.gov/jobs/technology-innovation-fellows/">Consumer Financial Protection Bureau, Technology and Innovation Fellowship</a>')
    multi_achievement_dataone = models.BooleanField(verbose_name='<a href="http://www.dataone.org/internships">DataONE Internships</a>')
    multi_achievement_drupal = models.BooleanField(verbose_name='<a href="https://assoc.drupal.org/grants">Drupal Community Cultivation Grants</a>')
    multi_achievement_gsoc = models.BooleanField(verbose_name='<a href="https://developers.google.com/open-source/gsoc/">Google Summer of Code</a>')
    multi_achievement_hp = models.BooleanField(verbose_name='<a href="http://go.hpcloud.com/scholarship-registration">HP Helion OpenStack scholarship</a>')
    multi_achievement_igalia = models.BooleanField(verbose_name='<a href="http://www.igalia.com/nc/igalia-247/news/item/announcing-igalias-summer-intern-positions/">Igalia Internships</a>')
    multi_achievement_knight_mozilla = models.BooleanField(verbose_name='<a href="http://opennews.org/fellowships/">Knight-Mozilla Fellowship</a>')
    multi_achievement_nlnet = models.BooleanField(verbose_name='<a href="http://www.nlnet.nl/foundation/can_do.html">NLnet Funding</a>')
    multi_achievement_opengov = models.BooleanField(verbose_name='<a href="http://sunlightfoundation.com/about/grants/opengovgrants/">OpenGov Grants</a>')
    multi_achievement_openitp = models.BooleanField(verbose_name='<a href="https://openitp.org/grants.html">OpenITP Grants</a>')
    multi_achievement_open_society = models.BooleanField(verbose_name='<a href="http://www.opensocietyfoundations.org/grants/open-society-fellowship">Open Society Fellowship</a>')
    multi_achievement_open_robotics = models.BooleanField(verbose_name='<a href="http://osrfoundation.org/jobs/">Open Robotics internships</a>')
    multi_achievement_perl = models.BooleanField(verbose_name='<a href="http://www.perlfoundation.org/rules_of_operation">Perl Foundation Grants</a>')
    multi_achievement_rgsoc = models.BooleanField(verbose_name='<a href="http://railsgirlssummerofcode.org/">Rails Girls Summer of Code</a>')
    multi_achievement_recurse = models.BooleanField(verbose_name='<a href="https://www.recurse.com/">Recurse Center (formerly known as Hacker School)</a>')
    multi_achievement_red_hat = models.BooleanField(verbose_name='<a href="http://jobs.redhat.com/job-categories/internships/">Red Hat internships</a>')
    multi_achievement_stripe = models.BooleanField(verbose_name='<a href="https://stripe.com/blog/stripe-open-source-retreat">Stripe Open Source Retreat</a>')
    multi_achievement_socis = models.BooleanField(verbose_name='<a href="http://sophia.estec.esa.int/socis/">Summer of Code in Space (SOCIS)</a>')
    multi_achievement_xorg_evoc = models.BooleanField(verbose_name='<a href="http://www.x.org/wiki/XorgEVoC/">Xorg Endless Vacation of Code</a>')
    multi_achievement_wikimedia = models.BooleanField(verbose_name='<a href="https://meta.wikimedia.org/wiki/Grants:IEG">Wikimedia Individual Engagement Grants</a>')
    multi_achievement_other = models.BooleanField(verbose_name='Other internship, fellowship, or grant program that involved FOSS, Open Science, Open Government, or Open Data')

    question_mentor = models.BooleanField(verbose_name='After your Outreachy internship, did you mentor for any of the following programs?')
    multi_mentor_gsoc = models.BooleanField(verbose_name='<a href="https://developers.google.com/open-source/gsoc/">Google Summer of Code</a>')
    multi_mentor_outreachy = models.BooleanField(verbose_name='<a href="https://outreachy.org">Outreachy</a>')
    multi_mentor_rgsoc = models.BooleanField(verbose_name='<a href="http://railsgirlssummerofcode.org/">Rails Girls Summer of Code</a>')
    multi_mentor_other = models.BooleanField(verbose_name='Other FOSS internship, fellowship, or grant program')

    other_achievement = models.CharField(max_length=TIMELINE_LENGTH,
            blank=True,
            verbose_name='We understand that your accomplishments after your Outreachy internship may not be captured by all the questions above. Please tell us about any other experiences or accomplishments related to your participation in Outreachy or in FOSS that can help us understand the impact Outreachy has on alums.')

    address1 = models.CharField(max_length=PARAGRAPH_LENGTH, blank=True, verbose_name="Address Line 1")
    address2 = models.CharField(max_length=PARAGRAPH_LENGTH, blank=True, verbose_name="Address Line 2/District/Neighborhood")
    city = models.CharField(max_length=PARAGRAPH_LENGTH, blank=True, verbose_name="Town/City")
    region = models.CharField(max_length=PARAGRAPH_LENGTH, blank=True, verbose_name="State/Province/Region/County/Territory/Prefecture/Republic")
    postal_code = models.CharField(max_length=PARAGRAPH_LENGTH, blank=True, verbose_name="Zip/Postal Code")
    country = models.CharField(max_length=PARAGRAPH_LENGTH, blank=True, verbose_name="Country")

    def intern_name(self):
        if self.survey_tracker.intern_info != None:
            return self.survey_tracker.intern_info.applicant.applicant.public_name
        if self.survey_tracker.alumni_info != None:
            return self.survey_tracker.alumni_info.name
        return None

    def community(self):
        if self.survey_tracker.intern_info != None:
            return self.survey_tracker.intern_info.project.project_round.community.name
        if self.survey_tracker.alumni_info != None:
            return self.survey_tracker.alumni_info.community
        return None

# Please keep this at the end of this file; it has to come after the
# models it mentions, so just keep it after all other definitions.
DASHBOARD_MODELS = (
        CoordinatorApproval,
        Participation,
        Project,
        MentorApproval,
        )
