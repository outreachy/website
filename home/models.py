from __future__ import absolute_import, unicode_literals

from os import urandom
from base64 import urlsafe_b64encode
from collections import Counter
import datetime
from email.headerregistry import Address
import random
import os.path
import re
import math

from django.contrib.auth.models import User
from django.core import validators
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db import transaction
from django.forms import ValidationError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from itertools import chain, groupby
from urllib.parse import urlsplit, urlparse

from ckeditor.fields import RichTextField as CKEditorField

from modelcluster.fields import ParentalKey

from reversion.models import Version

from timezone_field.fields import TimeZoneField

from wagtail.core.models import Orderable
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.core.fields import StreamField
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.admin.edit_handlers import InlinePanel
from wagtail.core import blocks
from wagtail.admin.edit_handlers import StreamFieldPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.images.blocks import ImageChooserBlock
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.contrib.routable_page.models import RoutablePageMixin, route

from . import email
from .feeds import WagtailFeed

# These constants are used across several different models
# Please be cautious about shorting them,
# as it may mean stored objects are no longer valid.
# When in doubt, use a longer max character length or define a new constant.

SENTENCE_LENGTH=100
PARAGRAPH_LENGTH=800
THREE_PARAGRAPH_LENGTH=3000
EIGHT_PARAGRAPH_LENGTH=8000
TIMELINE_LENGTH=30000
LONG_LEGAL_NAME=800
SHORT_NAME=100

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

    def get_context(self, request, *args, **kwargs):
        context = super(BlogIndex, self).get_context(request, *args, **kwargs)
        context['feed'] = self.feed_generator.get_feed(self, request)
        return context

# All dates in RoundPage below, if an exact time matters, actually represent
# the given date at 4PM UTC.
DEADLINE_TIME = datetime.time(hour=16, tzinfo=datetime.timezone.utc)

def get_deadline_date_for(dt):
    """
    Takes a timezone-aware datetime and returns the date which is
    comparable to dates in RoundPage deadlines. If the datetime has
    not reached the deadline time of 4PM UTC, then this is the
    previous day's date.

    This is handy for comparing an arbitrary point in time against
    any of the deadlines in RoundPage, like the following example to
    find rounds where the intern announcement deadline has passed but
    the internship end deadline has not:

    >>> import datetime
    >>> now = datetime.datetime.now(datetime.timezone.utc)
    >>> today = get_deadline_date_for(now)
    >>> RoundPage.objects.filter(
    ...     internannounce__lte=today,
    ...     internends__gt=today,
    ... ) # doctest: +ELLIPSIS
    <PageQuerySet [...]>
    """
    if dt.timetz() < DEADLINE_TIME:
        return dt.date() - datetime.timedelta(days=1)
    return dt.date()


class Deadline(datetime.date):
    """
    An extension of datetime.date which adds extra methods that are useful when
    the date represents a deadline. This class also stores an extra ``today``
    value that's used to determine whether the deadline has already passed.
    """

    @classmethod
    def at(cls, base, today):
        """
        This is the only valid constructor for this type, because other methods
        won't set self._today.
        """
        new = cls(base.year, base.month, base.day)
        new._today = today
        return new

    def __add__(self, other):
        # In Python 3.7, date.__add__ always returns a date. In 3.8 it returns
        # the same type as self, e.g. Deadline, but without setting _today.
        # Either way, extracting the year/month/day and building a new Deadline
        # object produces the right result.
        new = super(Deadline, self).__add__(other)
        return Deadline.at(new, self._today)

    def __sub__(self, other):
        # Override to make sure that the above implementation of __add__ gets
        # used.
        if isinstance(other, datetime.timedelta):
            return self + -other
        return super(Deadline, self).__sub__(other)

    def deadline(self):
        """
        Returns this deadline with time and timezone set from
        ``DEADLINE_TIME``.
        """
        return datetime.datetime.combine(self, DEADLINE_TIME)

    def has_passed(self):
        """
        Returns whether this deadline is in the past.
        """
        return self <= self._today


class NoDeadline(object):
    """
    Like ``Deadline``, but for situations where there is no expiration date.
    This class can't act like a ``date`` or implement the ``deadline`` method.
    But it does work if the caller only needs to know whether the deadline has
    passed yet, because the answer is always: no, it hasn't.

    There's no need to construct instances of this class. Instead of using
    ``NoDeadline()``, just use ``NoDeadline``.
    """

    @staticmethod
    def has_passed():
        return False


class AugmentDeadlines(object):
    """
    Mixin to transparently make date fields return Deadline objects instead.
    """

    def __init__(self, *args, **kwargs):
        now = datetime.datetime.now(DEADLINE_TIME.tzinfo)
        self.today = get_deadline_date_for(now)
        super(AugmentDeadlines, self).__init__(*args, **kwargs)

    def __getattribute__(self, name):
        """
        Extend all fields that are plain dates to return an instance of
        Deadline instead, where the Deadline's idea of ``today`` is set from
        ``self.today``. For example:

        >>> rp = RoundPage(internstarts=datetime.date(2019, 1, 1))
        >>> rp.internstarts.deadline()
        datetime.datetime(2019, 1, 1, 16, 0, tzinfo=datetime.timezone.utc)
        >>> rp.today = datetime.date(2018, 12, 1)
        >>> rp.internstarts.has_passed()
        False
        >>> rp.today = datetime.date(2019, 1, 1)
        >>> rp.internstarts.has_passed()
        True

        Any Python class can override what ``obj.field`` means by implementing
        this method, which then gets called like
        ``obj.__getattribute__("field")``. See:

        https://docs.python.org/3/reference/datamodel.html#object.__getattribute__
        """
        # Call the default implementation first...
        value = super(AugmentDeadlines, self).__getattribute__(name)

        if name != "today" and type(value) is datetime.date:
            # This is a plain date; augment it with the Deadline extras. Note
            # that accessing ``self.today`` triggers a recursive call to this
            # function with name="today", so we have to be very careful: that
            # call must not reach this same statement or it will recurse
            # forever.
            return Deadline.at(value, self.today)

        # This was not a date, so return it as-is.
        return value


class RoundPage(AugmentDeadlines, Page):
    roundnumber = models.IntegerField()
    pingnew = models.DateField("Date to start pinging new orgs")
    pingold = models.DateField("Date to start pinging past orgs")
    orgreminder = models.DateField("Date to remind orgs to submit their home pages")
    landingdue = models.DateField("Date community landing pages are due")
    coupon_code = models.CharField(blank=True, max_length=255, verbose_name='Coupon code for the book "Forge Your Future with Open Source"')
    minimum_days_free_for_students = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=49,
            )
    minimum_days_free_for_non_students = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=49,
            )
    initial_applications_open = models.DateField("Date initial applications open")
    outreachy_chat = models.DateTimeField("Date and time of the Outreachy Twitter chat")
    outreachy_chat_timezone_url = models.URLField(blank=True, verbose_name="URL to display timezone conversions for the Outreachy Twitter chat time")
    initial_applications_close = models.DateField("Date initial applications close")
    pick_a_project_blog_url = models.URLField(blank=True, verbose_name="URL of the blog on how to pick a project")
    contributions_open = models.DateField("Date contributions open")
    contributions_close = models.DateField("Date contributions close")
    lateorgs = models.DateField("Last date to add community landing pages")
    lateprojects = models.DateField("Last date to add projects")
    mentor_intern_selection_deadline = models.DateField("Date mentors must select their intern by")
    coordinator_funding_deadline = models.DateField("Date coordinators must mark funding sources for interns by")
    internapproval = models.DateField("Date interns are approved by the Outreachy organizers")
    internannounce = models.DateField("Date interns are announced")
    internstarts = models.DateField("Date internships start")
    week_two_chat_text_date = models.DateTimeField("Date and time of outreachy week two chat (text only)")
    week_two_chat_text_url = models.URLField(blank=True, verbose_name="URL of the real-time text chat")
    week_four_chat_text_date = models.DateTimeField("Date and time of Outreachy week four chat about what we're stuck on")
    week_four_stuck_chat_url = models.URLField(blank=True, verbose_name="URL of the week four chat on what we're stuck on")
    week_six_chat_text_date = models.DateTimeField("Date and time of Outreachy week six chat to explain why your project passion to a newcomer")
    week_six_audience_chat_url = models.URLField(blank=True, verbose_name="URL of the week six chat to explain your project to a newcomer")
    week_eight_chat_text_date = models.DateTimeField("Date and time of Outreachy week eight chat to talk about difficulties scoping project tasks")
    week_eight_timeline_chat_url = models.URLField(blank=True, verbose_name="URL of the week eight chat to talk about project timeline modifications")
    week_ten_chat_text_date = models.DateTimeField("Date and time of Outreachy week ten chat to talk about career opportunities")
    week_ten_career_chat_url = models.URLField(blank=True, verbose_name="URL of the week ten chat to talk about career opportunities")
    week_twelve_chat_text_date = models.DateTimeField("Date and time of Outreachy week twelve chat on interviewing")
    week_twelve_interviewing_chat_url = models.URLField(blank=True, verbose_name="URL of the week twelve chat on interviewing")
    resume_reviewer_name = models.CharField(blank=True, max_length=255, verbose_name='Name of the person doing resume review during week 12')
    resume_reviewer_email = models.EmailField(blank=True, verbose_name='Email address of the person doing resume review during week 12')
    week_fourteen_chat_text_date = models.DateTimeField(verbose_name="Date and time of Outreachy week fourteen chat to wrap up the Outreachy internship")
    week_fourteen_wrapup_chat_url = models.URLField(blank=True, verbose_name="URL of the week fourteen chat to wrap up the Outreachy internship")
    tax_form_deadline = models.DateField("Date tax forms must be received by in order to have on-time initial payments")

    # Feedback 1 fields
    initialfeedback = models.DateField("Date initial feedback is due")
    initial_payment_date = models.DateField("Date initial payment will be received by")
    initialpayment = models.IntegerField(default=1000)

    # Feedback 2 fields
    midfeedback = models.DateField("Date mid-point feedback is due")
    midpoint_payment_date = models.DateField("Date mid-point payment will be received by")
    midpayment = models.IntegerField(default=2000)

    # Feedback 3 fields
    feedback3_due = models.DateField(blank=True, null=True, verbose_name="Date feedback #3 is due")
    final_payment_date = models.DateField("Date final payment will be received by")
    finalpayment = models.IntegerField(default=2500)

    internends = models.DateField("Date internships end")

    # Feedback 4 fields
    finalfeedback = models.DateField("Date final feedback is due")

    sponsordetails = RichTextField(default='<p>Outreachy is hosted by the <a href="https://sfconservancy.org/">Software Freedom Conservancy</a> with special support from Red Hat, GNOME, and <a href="http://otter.technology">Otter Tech</a>. We invite companies and free and open source communities to sponsor internships in the next round.</p>')

    content_panels = Page.content_panels + [
        FieldPanel('roundnumber'),
        FieldPanel('pingnew'),
        FieldPanel('pingold'),
        FieldPanel('orgreminder'),
        FieldPanel('landingdue'),
        FieldPanel('initial_applications_open'),
        FieldPanel('initial_applications_close'),
        FieldPanel('pick_a_project_blog_url'),
        FieldPanel('contributions_open'),
        FieldPanel('contributions_close'),
        FieldPanel('lateorgs'),
        FieldPanel('lateprojects'),
        FieldPanel('mentor_intern_selection_deadline'),
        FieldPanel('coordinator_funding_deadline'),
        FieldPanel('internapproval'),
        FieldPanel('internannounce'),
        FieldPanel('internstarts'),
        FieldPanel('initialfeedback'),
        FieldPanel('midfeedback'),
        FieldPanel('feedback3_due'),
        FieldPanel('internends'),
        FieldPanel('finalfeedback'),
        FieldPanel('sponsordetails', classname="full"),
        FieldPanel('initialpayment'),
        FieldPanel('midpayment'),
        FieldPanel('finalpayment'),
        FieldPanel('week_two_chat_text_date'),
        FieldPanel('week_two_chat_text_url'),
        FieldPanel('week_four_chat_text_date'),
        FieldPanel('week_four_stuck_chat_url'),
        FieldPanel('week_six_chat_text_date'),
        FieldPanel('week_six_audience_chat_url'),
        FieldPanel('week_eight_chat_text_date'),
        FieldPanel('week_eight_timeline_chat_url'),
        FieldPanel('week_ten_chat_text_date'),
        FieldPanel('week_ten_career_chat_url'),
        FieldPanel('week_twelve_chat_text_date'),
        FieldPanel('week_twelve_interviewing_chat_url'),
        FieldPanel('week_fourteen_chat_text_date'),
        FieldPanel('week_fourteen_wrapup_chat_url'),
    ]

    def official_name(self):
        return(self.internstarts.strftime("%B %Y") + " to " + self.internends.strftime("%B %Y") + " Outreachy internships")

    def project_soft_deadline(self):
        return self.lateprojects - datetime.timedelta(days=7)

    def internship_week_1_email_date(self):
        return(self.internstarts)

    def internship_week_3_email_date(self):
        return self.internstarts + datetime.timedelta(days=7*(3-1))

    def internship_week_5_email_date(self):
        return self.internstarts + datetime.timedelta(days=7*(5-1))

    def internship_week_7_email_date(self):
        return self.internstarts + datetime.timedelta(days=7*(7-1))

    def internship_week_9_email_date(self):
        return self.internstarts + datetime.timedelta(days=7*(9-1))

    def internship_week_11_email_date(self):
        return self.internstarts + datetime.timedelta(days=7*(11-1))

    def internship_week_13_email_date(self):
        return self.internstarts + datetime.timedelta(days=7*(13-1))

    def intern_agreement_deadline(self):
        return(self.internannounce + datetime.timedelta(days=5))

    def intern_initial_feedback_opens(self):
        return(self.initialfeedback - datetime.timedelta(days=4))

    def intern_midpoint_feedback_opens(self):
        return(self.midfeedback - datetime.timedelta(days=4))

    def intern_not_started_deadline(self):
        return(self.initialfeedback - datetime.timedelta(days=1))

    def intern_sfc_initial_payment_notification_deadline(self):
        return(self.initialfeedback)

    def initial_stipend_payment_deadline(self):
        return self.initial_payment_date

    def midpoint_stipend_payment_deadline(self):
        return self.midpoint_payment_date

    def final_stipend_payment_deadline(self):
        return self.final_payment_date

    # There is a concern about paying interns who are in a country
    # where they are not eligible to work in (usually due to visa restrictions).
    # We need to ask interns whether they will be traveling after their internship
    # when they would normally be paid. Internships may be extended by up to five weeks.
    # Payment isn't instantaneous, but this is a little better than just saying
    # "Are you eligible to work in all the countries you are residing in
    # during the internship period?"
    def sfc_payment_last_date(self):
        return self.internends + datetime.timedelta(days=7*5)

    # Interns get a five week extension at most.
    def has_internship_ended(self):
        return (self.internends + datetime.timedelta(days=7 * 5)).has_passed()

    # Outreachy internships can be extended for up to five weeks past the official end date.
    # In some cases, we've changed or added an intern after the official announcement date.
    # The very latest we could do that would be five weeks after the official start date.
    def has_last_day_to_add_intern_passed(self):
        return (self.internstarts + datetime.timedelta(days=5 * 7)).has_passed()

    def gsoc_round(self):
        # The internships would start before August
        # for rounds aligned with GSoC
        # GSoC traditionally starts either in May or June
        return(self.internstarts.month < 8)

    def number_approved_communities_with_projects(self):
        return self.participation_set.approved().filter(project__isnull=False).distinct().count()

    def number_approved_projects(self):
        return Project.objects.filter(project_round__participating_round=self,
                approval_status=ApprovalStatus.APPROVED,
                project_round__approval_status=ApprovalStatus.APPROVED).distinct().count()

    def get_new_projects(self):
        # Find all approved projects
        projects = Project.objects.filter(project_round__participating_round=self,
                approval_status=ApprovalStatus.APPROVED,
                project_round__approval_status=ApprovalStatus.APPROVED).order_by('project_round__community__name').distinct()

        new_projects = []
        now = datetime.datetime.now(datetime.timezone.utc)
        week_ago = now - datetime.timedelta(weeks=1)
        # Find all projects that were in the submitted state within the last week
        for p in projects:
            versions = Version.objects.get_for_object(p)
            for v in versions:
                if v.revision.date_created < week_ago:
                    break
                if v.field_dict['approval_status'] == ApprovalStatus.PENDING:
                    new_projects.append(p)
                    break
        return new_projects
    # for p in new_projects:
    #   print(p.project_round.community.name, '"' + p.short_title + '" - ', ', '.join([s.skill for s in p.projectskill_set.all()]))
    #   print("New @outreachy internship project:", p.project_round.community.name, '"' + p.short_title + '" - ', ', '.join([s.skill for s in p.projectskill_set.all()]), 'https://www.outreachy.org/apply/project-selection/#' + p.project_round.community.slug + '-' + p.slug)

    def number_funded_interns(self):
        participations = self.participation_set.approved().filter(project__isnull=False).distinct()
        funded = 0
        for p in participations:
            funded += p.interns_funded()
        return funded

    def is_coordinator(self, user):
        return CoordinatorApproval.objects.filter(
            coordinator__account=user,
            approval_status=ApprovalStatus.APPROVED,
            community__participation__approval_status=ApprovalStatus.APPROVED,
            community__participation__participating_round=self,
        ).exists()

    def is_mentor(self, user):
        try:
            return user.comrade.get_mentored_projects().approved().filter(
                project_round__participating_round=self,
                project_round__approval_status=ApprovalStatus.APPROVED,
            ).exists()
        except Comrade.DoesNotExist:
            return False

    def is_reviewer(self, user):
        return self.applicationreviewer_set.approved().filter(
            comrade__account=user,
        ).exists()

    def print_approved_project_list(self):
        projects = Project.objects.filter(project_round__participating_round=self, approval_status=ApprovalStatus.APPROVED, project_round__approval_status=ApprovalStatus.APPROVED).order_by('project_round__community__name').distinct()
        for p in projects:
            skills = p.required_skills() | p.preferred_skills()
            print("<p><a href='https://www.outreachy.org/{}'>{}</a>, ".format(p.get_landing_url(), p.short_title), end='')
            for s in skills:
                print("{} ({}), ".format(s.skill, s.get_requirement_short_code()), end='')
            print("</p>")

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

    def get_interns_with_open_initial_feedback(self):
        interns = []
        # interns may not give feedback, but we only want to send a reminder email
        # if their mentor hasn't given feedback yet.
        for i in self.get_in_good_standing_intern_selections():
            if i.is_initial_feedback_on_intern_open():
                interns.append(i)
        return interns

    def get_interns_with_open_midpoint_feedback(self):
        interns = []
        for i in self.get_in_good_standing_intern_selections():
            if i.is_feedback_2_form_open_to_mentor():
                interns.append(i)
        return interns

    def get_interns_with_open_feedback3(self):
        interns = []
        for i in self.get_in_good_standing_intern_selections():
            if i.is_feedback_3_form_open_to_mentor():
                interns.append(i)
        return interns

    def get_interns_with_open_final_feedback(self):
        interns = []
        for i in self.get_in_good_standing_intern_selections():
            if i.is_final_feedback_on_intern_open():
                interns.append(i)
        return interns

    def get_communities_with_unused_funding(self):
        participations = self.participation_set.approved()
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

    def number_accepted_initial_applications(self):
        return self.applicantapproval_set.approved().count()

    def number_contributors(self):
        return self.applicantapproval_set.approved().filter(
            contribution__isnull=False,
        ).distinct().count()

    def number_final_applicants(self):
        return self.applicantapproval_set.approved().filter(
            finalapplication__isnull=False,
        ).distinct().count()

    def get_statistics_on_eligibility_check(self):
        applicants = self.applicantapproval_set
        count_all = applicants.count()
        count_approved = applicants.approved().count()
        count_rejected_all = applicants.rejected().count()
        count_rejected_time = applicants.rejected().filter(reason_denied="TIME").count()
        count_rejected_general = applicants.rejected().filter(reason_denied="GENERAL").count()
        count_rejected_essay = applicants.rejected().filter(reason_denied__contains="ALIGNMENT").count()
        if count_rejected_all == 0:
            return (count_all, count_approved, 0, 0, 0)
        return (count_all, count_approved, count_rejected_essay * 100 / count_rejected_all, count_rejected_time * 100 / count_rejected_all, count_rejected_general * 100 / count_rejected_all)

    def get_countries_stats(self):
        all_apps = self.applicantapproval_set.approved()
        countries = []
        cities = []
        for a in all_apps:
            city, country = a.applicant.get_city_country()
            if city != '':
                cities.append(city)
            if country != '':
                countries.append(country)

        return Counter(countries).most_common(25)

    def get_contributor_demographics(self):
        contributors = self.applicantapproval_set.approved().filter(contribution__isnull=False).distinct()

        applicants = contributors.count()

        us_apps = contributors.filter(
            models.Q(
                paymenteligibility__us_national_or_permanent_resident=True
            ) | models.Q(
                paymenteligibility__living_in_us=True
            )
        ).count()

        us_people_of_color_apps = contributors.filter(
            applicantraceethnicityinformation__us_resident_demographics=True,
        ).count()
        if us_apps == 0:
            return (applicants, 0, 0)

        return (applicants, (us_apps - us_people_of_color_apps) * 100 / us_apps, us_people_of_color_apps * 100 / us_apps)

    def get_contributor_gender_stats(self):
        all_apps = self.applicantapproval_set.approved().filter(contribution__isnull=False).distinct().count()

        if all_apps == 0:
            return (0, 0, 0)

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
        eligible = self.applicantapproval_set.approved().count()

        contributed = self.applicantapproval_set.approved().filter(contribution__isnull=False).distinct().count()

        applied = self.applicantapproval_set.approved().filter(finalapplication__isnull=False).distinct().count()

        funded = 0
        participations = self.participation_set.approved()
        for p in participations:
            funded = funded + p.interns_funded()

        return (eligible, contributed, applied, funded)

    def serve(self, request, *args, **kwargs):
        # If the project selection page (views.current_round_page) would
        # consider this a current_round, redirect there.
        if self.pingnew.has_passed() and not self.internannounce.has_passed():
            return redirect('project-selection')

        # Only show this page if we shouldn't be showing the project selection page.
        return super(RoundPage, self).serve(request, *args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        context = super(RoundPage, self).get_context(request, *args, **kwargs)
        context['role'] = Role(request.user, self)
        return context

class StatisticTotalApplied(models.Model):
    internship_round = models.OneToOneField(RoundPage, on_delete=models.CASCADE, primary_key=True)
    total_applicants = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )
    total_approved = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )
    total_pending = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )
    total_rejected = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )
    total_withdrawn = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )

    def clean(self):
        if self.total_applicants != (self.total_approved + self.total_pending + self.total_rejected + self.total_withdrawn):
            error_string = 'Total applicants != approved + pending + rejected + withdrawn'
            raise ValidationError({'total_applicants': error_string})

class StatisticApplicantCountry(models.Model):
    internship_round = models.ForeignKey(RoundPage, on_delete=models.CASCADE)
    country_living_in_during_internship = models.CharField(
            verbose_name='Country interns are living in during the internship',
            max_length=PARAGRAPH_LENGTH,
            )

    country_living_in_during_internship_code = models.CharField(
            verbose_name='ISO 3166-1 alpha-2 country code',
            max_length=2,
            )

    total_applicants = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )

class StatisticAmericanDemographics(models.Model):
    internship_round = models.OneToOneField(RoundPage, on_delete=models.CASCADE, primary_key=True)

    # total accepted applicants who are U.S. nationals or permanent residents
    total_approved_american_applicants = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )

    # total accepted applicants who are U.S. nationals or permanent residents and
    # Black/African American, Hispanic/Latinx, Native American,
    # Alaska Native, Native Hawaiian, or Pacific Islander
    total_approved_american_bipoc = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )
    def total_approved_american_not_bipoc(self):
        return self.total_approved_american_applicants - self.total_approved_american_bipoc

    def percentage_americans_accepted_who_are_bipoc(self):
        return int(round(100 * (self.total_approved_american_bipoc / self.total_approved_american_applicants)))

    def percentage_americans_accepted_who_are_not_bipoc(self):
        return int(round(100 * (self.total_approved_american_not_bipoc() / self.total_approved_american_applicants)))

class StatisticGenderDemographics(models.Model):
    internship_round = models.OneToOneField(RoundPage, on_delete=models.CASCADE, primary_key=True)

    # Note: These could be overlapping gender identities
    # For example, someone could be a non-binary woman, or a trans masculine agender person.
    # In short, these totals will not add up to the total number of accepted applicants.

    # total accepted applicants who answered 'yes' to "Are you transgender?"
    total_transgender_people = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )

    # total accepted applicants who answered 'yes' to "Are you genderqueer?"
    total_genderqueer_people = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )

    # total accepted applicants checked the 'man' gender box
    total_men = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )

    # Note: Trans men are men!
    #
    # If an applicant identifies as a man, they would have checked the 'man' gender box.
    # However, some non-binary people may identify as trans masculine, but don't identify as men.
    #
    # Don't assume that trans masculine and trans feminine people are binary.

    # total accepted applicants checked the 'trans masculine' gender box
    total_trans_masculine_people = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )

    # total accepted applicants checked the 'woman' gender box
    total_women = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )

    # total accepted applicants checked the 'trans feminine' gender box
    total_trans_feminine_people = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )

    # total accepted applicants checked a gender identity other
    # than 'man', 'woman', 'trans masculine', or 'trans feminine'
    total_non_binary_people = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )

    # total accepted applicants who self identified their gender
    # We get a lot of people who self-identify as "girl" instead of "woman"
    # So self-identification is not an indication of whether they are non-binary
    total_who_self_identified_gender = models.IntegerField(
            validators=[validators.MinValueValidator(0)],
            default=0,
            )

    def percentage_accepted_who_are_women(self):
        return int(round(100 * (self.total_women / self.internship_round.statistictotalapplied.total_approved)))

    def percentage_accepted_who_are_men(self):
        return int(round(100 * (self.total_men / self.internship_round.statistictotalapplied.total_approved)))

    def percentage_accepted_who_are_transgender(self):
        return int(round(100 * (self.total_transgender_people / self.internship_round.statistictotalapplied.total_approved)))

    def percentage_accepted_who_are_non_binary(self):
        return int(round(100 * (self.total_non_binary_people / self.internship_round.statistictotalapplied.total_approved)))

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
    account = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    public_name = models.CharField(max_length=LONG_LEGAL_NAME, verbose_name="Name (public)", help_text="Your full name, which will be publicly displayed on the Outreachy website. This is typically your given name, followed by your family name. You may use a pseudonym or abbreviate your given or family names if you have concerns about privacy.")

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
            help_text="Common pronouns include she/her, he/him, or they/them. Neopronouns are also welcome! Your pronouns may be (optionally) displayed to Outreachy organizers, applicants, mentors, and (optionally) displayed on the public Outreachy alums page. See the pronoun privacy options below.",
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

    agreed_to_code_of_conduct = models.CharField(
            max_length=LONG_LEGAL_NAME,
            verbose_name = "Type your legal name to indicate you agree to the Code of Conduct")

    def __str__(self):
        return self.public_name + ' <' + self.account.email + '> (' + self.legal_name + ')'

    def email_address(self):
        if self.account.email:
            return Address(self.public_name, addr_spec=self.account.email)
        return ''

    def username(self):
        return self.account.username

    def get_pronouns_html(self):
        return "<a href=http://pronoun.is/{short_name}>{pronouns}</a>".format(
                short_name=self.pronouns,
                pronouns=self.get_pronouns_display(),
                )

    # Having a text location field was a disaster.
    def get_city_country(self):
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
        location = self.location.split(',')
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
        elif city == 'yaounde':
            country = 'cameroon'
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
        elif self.timezone:
            timezone = self.timezone.zone
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

        return (city.title(), country.title())

    def get_mentored_projects(self):
        """
        Returns all projects for which this person has ever been approved as a
        mentor, regardless of whether the project itself or its community were
        approved. You can apply additional filters to the return value if you
        want to be more specific.
        """
        return Project.objects.filter(
            mentorapproval__mentor=self,
            mentorapproval__approval_status=ApprovalStatus.APPROVED,
        )

    def get_intern_selection(self):
        try:
            return InternSelection.objects.get(
                applicant__applicant=self,
                funding_source__in=(InternSelection.ORG_FUNDED, InternSelection.GENERAL_FUNDED),
                organizer_approved=True)
        except InternSelection.DoesNotExist:
            return None

class ApprovalStatusQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(approval_status=ApprovalStatus.APPROVED)

    def pending(self):
        return self.filter(approval_status=ApprovalStatus.PENDING)

    def withdrawn(self):
        return self.filter(approval_status=ApprovalStatus.WITHDRAWN)

    def rejected(self):
        return self.filter(approval_status=ApprovalStatus.REJECTED)

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
        Override in subclasses to return a Deadline if people ought not to be
        editing or approving this request because a deadline has passed.
        """
        return NoDeadline

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

    def is_pending(self):
        return self.approval_status == self.PENDING

    def is_approved(self):
        return self.approval_status == self.APPROVED

    def is_withdrawn(self):
        return self.approval_status == self.WITHDRAWN

    def is_rejected(self):
        return self.approval_status == self.REJECTED

class Community(models.Model):
    name = models.CharField(
            max_length=50,
            verbose_name="Community name",
            help_text="The community name you provide will be used to generate unique identifier. The identifier will be used in Outreachy website URLs to reference your community. To ensure old links remain valid, modifying the community name later will not change the community's unique identifier.")

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
            verbose_name="(Optional) Community website URL")

    tutorial = CKEditorField(
            blank=True,
            verbose_name="(Optional) Description of your first time contribution tutorial",
            help_text="If your applicants need to complete a tutorial before working on contributions with mentors, please provide a description and the URL for the tutorial. For example, the Linux kernel asks applicants to complete a tutorial for compiling and installing a custom kernel, and sending in a simple whitespace change patch. Once applicants complete this tutorial, they can start to work with mentors on more complex contributions.")

    humanitarian_community = models.BooleanField(
            default=False,
            verbose_name='Is your community a humanitarian open source community?')

    general_funding_application = models.TextField(
            blank=True,
            max_length=THREE_PARAGRAPH_LENGTH,
            verbose_name="What humanitarian issues is your community addressing?",
            )

    open_science_community = models.BooleanField(
            default=False,
            verbose_name='Is your community an open science community?')

    open_science_funder_questions = models.TextField(
            blank=True,
            max_length=THREE_PARAGRAPH_LENGTH,
            )

    open_science_practices = models.TextField(
            blank=True,
            max_length=THREE_PARAGRAPH_LENGTH,
            verbose_name="How does your community implement reproducible research, open access, open data sets, open data science, open collaboration, citizen science, or open source software?",
            )

    inclusive_participation = models.TextField(
            blank=True,
            max_length=THREE_PARAGRAPH_LENGTH,
            verbose_name="How do people impacted by your work participate in your community?",
            )

    additional_sponsors = models.TextField(
            blank=True,
            max_length=THREE_PARAGRAPH_LENGTH,
            verbose_name="What other companies or organizations could Outreachy ask for additional sponsorship?",
            help_text="Outreachy needs to carefully allocate our funds. We want to try to find your community additional sponsors, so that we can fund more interns each round. Please let us know if there are organizations we could contact on your behalf for additional sponsorship.")

    rounds = models.ManyToManyField(RoundPage, through='Participation')

    class Meta:
        verbose_name_plural = "communities"

    def __str__(self):
        return self.name

    def reverse(self, view_name, **kwargs):
        kwargs['community_slug'] = self.slug
        return reverse(view_name, kwargs=kwargs)

    def get_coordinator_signup_url(self):
        return self.reverse('coordinatorapproval-action', action='submit')

    def get_preview_url(self):
        return self.reverse('community-read-only')

    def is_coordinator(self, user):
        return self.coordinatorapproval_set.approved().filter(
                coordinator__account=user).exists()

    def get_coordinator_email_list(self):
        return [ca.coordinator.email_address()
                for ca in self.coordinatorapproval_set.approved()]

    def get_coordinator_names(self):
        return [ca.coordinator.public_name
                for ca in self.coordinatorapproval_set.approved()]

class Notification(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    comrade = models.ForeignKey(Comrade, on_delete=models.CASCADE)
    # Ok, look, this is silly, and we don't actually need the date,
    # but I don't know what view to use to modify a through field on a model.
    date_of_signup = models.DateField("Date user signed up for notifications", auto_now_add=True)
    class Meta:
        unique_together = (
                ('community', 'comrade'),
                )

class NewCommunity(Community):
    community = models.OneToOneField(Community, primary_key=True, parent_link=True, on_delete=models.CASCADE)

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
    # deprecated
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
    # deprecated
    longevity = models.CharField(
        max_length=2,
        choices=LONGEVITY_CHOICES,
        default=THREE_MONTHS,
        verbose_name="How long has this FOSS community accepted public contributions?",
    )

    participating_orgs = models.CharField(max_length=THREE_PARAGRAPH_LENGTH,
            verbose_name="What different organizations and companies participate in this FOSS community?",
            help_text="If there are many organizations, list the top five organizations who make large contributions.")

    repositories = models.TextField(
            blank=True,
            max_length=THREE_PARAGRAPH_LENGTH,
            verbose_name="List of repositories",
            help_text="List the URLs of community repositories. Repositories can contain your open source community's code, documentation, and/or creative works. Repositories are usually hosted on GitHub, GitLab, or community web servers. If your community has multiple repositories, list the repositories which Outreachy applicants and interns will be likely to interact with.")

    licenses_used = models.TextField(
            blank=True,
            max_length=THREE_PARAGRAPH_LENGTH,
            verbose_name="List of open source licenses used",
            help_text="For each repository listed above, say which open source license they use.")

    approved_license = models.BooleanField(
            default=False,
            help_text='I assert that all Outreachy internship projects under my community will be released under either an <a href="https://opensource.org/licenses/alphabetical">OSI-approved open source license</a> that is also identified by the FSF as a <a href="https://www.gnu.org/licenses/license-list.html">free software license</a>, OR a <a href="https://creativecommons.org/share-your-work/public-domain/freeworks/">Creative Commons license approved for free cultural works</a>')
    unapproved_license_description = CKEditorField(
            blank=True,
            verbose_name="(Optional) Non-free software license details. If your FOSS community uses a license that is not an OSI-approved and FSF-approved license OR a Creative Commons license, please provide a description and links to the non-free licenses.")

    no_proprietary_software = models.BooleanField(help_text='I assert all Outreachy internship projects under my community will forward the interests of free and open source software, not proprietary software.')
    proprietary_software_description = CKEditorField(
            blank=True,
            verbose_name="(Optional) Proprietary software details. If any internship project under your community will further the interests of proprietary software, please explain.")

    approved_advertising = models.BooleanField(
            default=False,
            help_text='I assert that my community resources do not advertise the services of only one company. Community resources are where users and developers seek help for your FOSS project. Community resources can include the community website, mailing lists, forums, documentation, or community introduction emails. It is fine to advertise the services of multiple companies or to identify sponsor companies generally.')
    unapproved_advertising_description = CKEditorField(
            blank=True,
            verbose_name="(Optional) Company advertisements on community resources. If your community resources advertise the services of only one company or organization, please explain.")

    governance = models.URLField(blank=True, verbose_name="(Optional) Community governance model URL")
    participating_orgs_in_goverance = models.CharField(
            blank=True,
            max_length=THREE_PARAGRAPH_LENGTH,
            verbose_name="(Optional) What different organizations and companies participate in the governance of this FOSS community?",
            help_text="If there are many organizations, list the top five organizations.")

    code_of_conduct = models.URLField(blank=True, verbose_name="(Optional) Community's Code of Conduct URL")
    coc_committee = models.CharField(
            blank=True,
            max_length=THREE_PARAGRAPH_LENGTH,
            verbose_name="(Optional) What are the names of all Code of Conduct committee members?",
            help_text="If you do not have a formal Code of Conduct committee, please note this.")
    cla = models.URLField(blank=True, verbose_name="(Optional) Contributor License Agreement (CLA) URL")
    dco = models.URLField(blank=True, verbose_name="(Optional) Developer Certificate of Origin (DCO) agreement URL")

    mentorship_programs = models.TextField(
            default="None",
            max_length=THREE_PARAGRAPH_LENGTH,
            verbose_name="What other mentorship programs has your community participated in?",
            help_text="Note when your community participated in each program and how many interns the community worked with. Examples of mentoring programs include Rails Girls Summer of Code, Google Summer of Code, Google Code In, Google Season of Docs, Linux Foundation Community Bridge, and GitHub Major League Hacking internships.")

    reason_for_participation = models.TextField(
            blank=True,
            max_length=THREE_PARAGRAPH_LENGTH,
            verbose_name="(Optional) Why does your community want to work with Outreachy?")

    demographics = models.TextField(
            blank=True,
            max_length=THREE_PARAGRAPH_LENGTH,
            verbose_name="(Optional) What is the demographics of your community?",
            help_text="Most communities come to Outreachy to improve the diversity of their community. Please be honest about the demographic make up of your community")

    inclusive_practices = models.TextField(
            blank=True,
            max_length=THREE_PARAGRAPH_LENGTH,
            verbose_name="(Optional) How is your community working to become more inclusive?",
            help_text="Many communities come to Outreachy hoping to learn more inclusive practices. Please be honest about what steps your community has taken to become more inclusive. Please be clear on what steps you have completed vs. what you are planning to do.")

    class Meta:
        verbose_name_plural = 'new communities'

class Participation(ApprovalStatus):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    participating_round = models.ForeignKey(RoundPage, on_delete=models.CASCADE)

    class Meta:
        ordering = ('community__name',)

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

    def number_interns_approved(self):
        return InternSelection.objects.filter(project__project_round=self, organizer_approved=True).count()

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

    def reverse(self, view_name, **kwargs):
        return self.community.reverse(view_name, round_slug=self.participating_round.slug, **kwargs)

    def get_absolute_url(self):
        return self.reverse('community-landing')

    def get_preview_url(self):
        return self.community.get_preview_url()

    def get_action_url(self, action):
        return self.reverse('participation-action', action=action)

    # Outreachy organizers can approve participations until the contribution period closes
    # Other pages should hide the community participation submission button
    # after RoundPage.lateorgs
    def submission_and_approval_deadline(self):
        return self.participating_round.contributions_close

    def is_approver(self, user):
        return user.is_staff

    def get_approver_email_list(self):
        return [email.organizers]

    def is_submitter(self, user):
        return self.community.is_coordinator(user)

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
        try:
            return user.comrade.get_mentored_projects().approved().filter(
                project_round=self,
            ).exists()
        except Comrade.DoesNotExist:
            return False

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

    def number_interns(self):
        return self.amount / 6500

    def sponsorship_history(self):
        versions = Version.objects.get_for_object(self)
        history = []
        for v in versions:
            try:
                comrade = Comrade.objects.get(account=v.revision.user)
                email = "{} <{}>".format(comrade.public_name, comrade.account.email)
            except Comrade.DoesNotExist:
                email = ""
            history.append([
                v.revision.date_created,
                v.revision.user.username,
                email,
                v.field_dict['name'],
                v.field_dict['amount'],
                v.field_dict['funding_secured'],
                v.field_dict['funding_decision_date'],
                v.field_dict['additional_information'],
                ])
        return history

    def __str__(self):
        return "{name} sponsorship for {community}".format(
                name=self.name,
                community=self.participation.community)

class Project(ApprovalStatus):
    project_round = models.ForeignKey(Participation, verbose_name="Outreachy round and community", on_delete=models.CASCADE)
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

    minimum_system_requirements = CKEditorField(
            help_text="What are the minimum computer requirements to contribute to this project during the application period? Examples: Operating system, CPU, memory, and hard drive space. <br><br>Many Outreachy applicants have older laptops. Many of them are working with ten year old systems (e.g. 1.6 GHz dual core with 2 GB of RAM). Please evaluate whether your project could better support contributors with older systems.",
            default="<p>No system requirements provided.</p>")

    repository = models.URLField(blank=True, help_text="(Optional) URL for your team's repository or contribution mechanism")
    issue_tracker = models.URLField(blank=True, help_text="(Optional) URL for your team's issue tracker")
    newcomer_issue_tag = models.CharField(
            blank=True,
            max_length=SENTENCE_LENGTH,
            help_text="(Optional) What tag is used for newcomer-friendly issues for your team or for this internship project? Please use a tag and not a URL.")

    contribution_tasks = CKEditorField(
            verbose_name="How can applicants make a contribution to your project?",
            help_text='Instructions for how applicants can make contributions during the Outreachy application period.<br><br>Make sure to include links to getting started tutorials or documentation, how applicants can find contribution tasks on your project website or issue tracker, who they should ask for tasks, and everything they need to know to get started.')

    new_contributors_welcome = models.BooleanField(
        default=True,
        verbose_name="Is your project open to new contributors?",
        choices=(
            (True, "My project is open to new contributors"),
            (False, "My project already has many strong applicants"),
        ),
    )

    class Meta:
        unique_together = (
                ('slug', 'project_round'),
                )
        ordering = ['slug']

    def __str__(self):
        return '{start:%Y %B} to {end:%Y %B} round - {community} - {title}'.format(
            start=self.round().internstarts,
            end=self.round().internends,
            community=self.project_round.community,
            title=self.short_title,
        )

    def reverse(self, view_name, **kwargs):
        return self.project_round.reverse(view_name, project_slug=self.slug, **kwargs)

    def get_preview_url(self):
        return self.reverse('project-read-only')

    def get_project_selection_url(self):
        return reverse('project-selection') + '#' + self.project_round.community.slug + '-' + self.slug

    def get_landing_url(self):
        return self.project_round.get_absolute_url() + '#' + self.slug

    def get_contributions_url(self):
        return self.reverse('contributions')

    def get_applicants_url(self):
        return self.reverse('project-applicants')

    def get_apply_url(self):
        return self.reverse('final-application-action', action='submit')

    def get_mentor_signup_url(self):
        return self.reverse('mentorapproval-action', action='submit')

    def get_action_url(self, action):
        return self.reverse('project-action', action=action)

    def round(self):
        return self.project_round.participating_round

    def submission_and_approval_deadline(self):
        return self.round().lateprojects

    def is_approver(self, user):
        return self.project_round.community.is_coordinator(user)

    def get_approver_email_list(self):
        return self.project_round.community.get_coordinator_email_list()

    def is_submitter(self, user):
        # Everyone is allowed to propose new projects.
        if self.id is None:
            return True
        # XXX: Should coordinators also be allowed to edit projects?
        return self.is_mentor(user)

    def is_mentor(self, user):
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
        applicants = ApplicantApproval.objects.approved().filter(
            contribution__project=self,
        ).annotate(
            number_contributions=models.Count('contribution'),
        )

        for a in applicants:
            try:
                fa = a.finalapplication_set.get(project=self)
                a.submitted_application = True
                if fa.rating == fa.UNRATED:
                    a.rating = "Unrated"
                else:
                    a.rating = fa.rating
                a.rating_tip = fa.get_rating_display()
                if a.finalapplication_set.filter(project=self).withdrawn().exists():
                    a.withdrew_application = True
                else:
                    a.withdrew_application = False

                if a.finalapplication_set.filter(project=self).exclude(applying_to_gsoc="").exists():
                    a.applying_to_gsoc = True
                else:
                    a.applying_to_gsoc = False

                if a.finalapplication_set.filter(project=self).exclude(time_correct="True").exists():
                    a.incorrect_time_commitments = True
                elif a.finalapplication_set.filter(project=self).exclude(time_updates="").exists():
                    a.incorrect_time_commitments = True
                else:
                    a.incorrect_time_commitments = False
            except:
                a.submitted_application = False
                a.incorrect_time_commitments = False

        return applicants

    def get_applications(self):
        return self.finalapplication_set.filter(applicant__approval_status=ApprovalStatus.APPROVED)

    def get_sorted_applications(self):
        return self.get_applications().order_by("-rating")

    def get_gsoc_applications(self):
        return self.get_applications().exclude(applying_to_gsoc="")

    def get_applicants_with_time_commitment_updates(self):
        return self.get_applications().filter(
                models.Q(
                    time_correct=False
                ) | ~models.Q(
                    time_updates=''
                )
            )

    def get_withdrawn_applications(self):
        return self.finalapplication_set.filter(applicant__approval_status=ApprovalStatus.WITHDRAWN)

    def get_approved_mentors(self):
        return self.mentorapproval_set.approved()

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

def skill_is_valid(value):

    if ',' in value or '/' in value:
        raise ValidationError("Please list only one project skill")

    multiple = [
            'and',
            'or',
            'with',
            ]

    for w in multiple:
        if re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search(value):
            raise ValidationError("Please list only one project skill")

    desire = [
            'bonus',
            'optional',
            'optionally',
            'must',
            'preference',
            'preferred',
            'required',
            'should',
            ]

    for w in desire:
        if re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search(value):
            raise ValidationError("Please list requirements using drop down menus only")

    experience = [
            'basic',
            'basics',
            'comfortable',
            'experienced',
            'learn',
            'learning',
            'concepts',
            ]

    for w in experience:
        if re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search(value):
            raise ValidationError("Please list experience level using drop down menus only")

    # Allow defining acronyms
    #  - e.g. "Continuous Integration (CI)"
    #
    # Allow acronyms with no more than 1 consecutive lower case letter
    #
    # Prohibit asides
    #  - e.g. "Java (especially Java8)"
    #  - this should be two skills - Java required, Java8 preferred
    if re.compile(r'\(.*[a-z]{2}.*\)').search(value):
        raise ValidationError("Please use 1-3 words to describe the project skill, and don't use sentences with parenthesis")

    verbosity = [
            'able',
            'ability',
            'alternative',
            'alternatively',
            'applicant',
            'candidate',
            'especially',
            'etc',
            'interest',
            'interested',
            'familiar',
            'sense',
            'willing',
            'with',
            ]

    for w in verbosity:
        if re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search(value):
            raise ValidationError("Please use 1-3 words to describe the project skill, and don't use sentences")

class ProjectSkill(models.Model):
    project = models.ForeignKey(Project, verbose_name="Project", on_delete=models.CASCADE)

    skill = models.CharField(
            max_length=SENTENCE_LENGTH,
            verbose_name="Skill name",
            validators=[skill_is_valid],
            )

    TEACH_YOU = 'WTU'
    CONCEPTS = 'CON'
    EXPERIMENTATION = 'EXP'
    FAMILIAR = 'FAM'
    CHALLENGE = 'CHA'
    EXPERIENCE_CHOICES = (
            (TEACH_YOU, 'No knowledge required'),
            (CONCEPTS, 'Concepts'),
            (EXPERIMENTATION, 'Experimented'),
            (FAMILIAR, 'Comfortable'),
            (CHALLENGE, 'Challenge'),
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
            (BONUS, "Optional"),
            (OPTIONAL, "Preferred"),
            (STRONG, "Required"),
            )
    required = models.CharField(
            max_length=3,
            choices=REQUIRED_CHOICES,
            default=BONUS,
            verbose_name="Skill impact on intern selection",
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

    def get_skill_experience_level_display(self):
        if self.experience_level == self.TEACH_YOU:
            return "(No knowledge required) Mentors are willing to teach this skill to applicants with no experience at all"
        if self.experience_level == self.CONCEPTS:
            return "(Concepts) Applicants should have read about the skill"
        if self.experience_level == self.EXPERIMENTATION:
            return "(Experimented) Applicants should have used this skill in class or personal projects"
        if self.experience_level == self.FAMILIAR:
            return "(Comfortable) Applicants should be able to expand on their skills with the help of mentors"
        if self.experience_level == self.CHALLENGE:
            return "(Challenge) Applicants who are experienced in this skill will have the chance to expand it further"

    def get_requirement_short_code(self):
        if self.required == self.STRONG:
            return 'Required'
        if self.required == self.OPTIONAL:
            return 'Preferred'
        else:
            return 'Nice to have'

    def __str__(self):
        return '{start:%Y %B} to {end:%Y %B} round - {community} - {title} - {skill}'.format(
            start=self.project.round().internstarts,
            end=self.project.round().internends,
            community=self.project.project_round.community,
            title=self.project.short_title,
            skill=self.skill,
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
# we don't have a random person signing up who can now see
# final applications with applicant contact info, location, and pronouns.
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

    employer = models.CharField(
        max_length=SENTENCE_LENGTH,
        verbose_name="Employer",
    )

    def __str__(self):
        return '{mentor} - {start:%Y %B} to {end:%Y %B} round - {community} - {title}'.format(
            mentor=self.mentor.public_name,
            start=self.project.round().internstarts,
            end=self.project.round().internends,
            community=self.project.project_round.community,
            title=self.project.short_title,
        )

    def get_preview_url(self):
        return self.project.reverse('mentorapproval-preview', username=self.mentor.account.username)

    def get_action_url(self, action, current_user=None):
        kwargs = {}
        if self.mentor.account != current_user:
            kwargs['username'] = self.mentor.account.username
        return self.project.reverse('mentorapproval-action', action=action, **kwargs)

    def submission_and_approval_deadline(self):
        return self.project.round().internends + datetime.timedelta(days=7 * 5)

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
        return self.community.reverse('coordinatorapproval-preview', username=self.coordinator.account.username)

    def get_action_url(self, action, current_user=None):
        kwargs = {}
        if self.coordinator.account != current_user:
            kwargs['username'] = self.coordinator.account.username
        return self.community.reverse('coordinatorapproval-action', action=action, **kwargs)

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


# --------------------------------------------------------------------------- #
# initial application models
# --------------------------------------------------------------------------- #

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

class ApplicationReviewer(ApprovalStatus):
    comrade = models.ForeignKey(Comrade, on_delete=models.CASCADE)
    reviewing_round = models.ForeignKey(RoundPage, on_delete=models.CASCADE)

class EssayQuality(models.Model):
    category = models.CharField(
            max_length=SENTENCE_LENGTH,
            help_text='Which category list should this description be under?')
    description = models.CharField(
            max_length=SENTENCE_LENGTH,
            verbose_name='Essay quality description')
    help_text = models.CharField(
            max_length=SENTENCE_LENGTH,
            blank=True,
            help_text='Help text to further clarify the short essay quality description')

    def __str__(self):
        return '[' + self.category + '] ' + self.description

    class Meta:
        ordering = ('category', 'description')

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
    essay_qualities = models.ManyToManyField(EssayQuality, blank=True)
    submission_date = models.DateField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(protocol="both")
    review_owner = models.ForeignKey(ApplicationReviewer, blank=True, null=True, on_delete=models.SET_NULL)
    collected_statistics = models.BooleanField(default=False)

    # This information is saved to pass onto Software Freedom Conservancy accounting
    initial_application_country_living_in_during_internship = models.CharField(
            verbose_name='Country applicant will be living in during the internship - from initial application',
            max_length=PARAGRAPH_LENGTH,
            blank=True,
            )

    initial_application_country_living_in_during_internship_code = models.CharField(
            verbose_name='Country code from initial application - ISO 3166-1 alpha-2 country code',
            max_length=2,
            blank=True,
            )

    def get_essay_qualities(self):
        return [q.__str__ for q in self.essay_qualities.all()]

    def collect_statistics(self):
        if self.collected_statistics:
            return

        with transaction.atomic():
            # Collect statistics about approval and rejection rates
            try:
                stats = StatisticTotalApplied.objects.get(
                        internship_round = self.application_round,
                        )
            except StatisticTotalApplied.DoesNotExist:
                stats = StatisticTotalApplied(
                        internship_round = self.application_round,
                        )
            stats.total_applicants += 1
            if self.approval_status == ApprovalStatus.APPROVED:
                stats.total_approved += 1
            if self.approval_status == ApprovalStatus.PENDING:
                stats.total_pending += 1
            if self.approval_status == ApprovalStatus.REJECTED:
                stats.total_rejected += 1
            if self.approval_status == ApprovalStatus.WITHDRAWN:
                stats.total_withdrawn += 1
            stats.save()

            if self.approval_status != ApprovalStatus.APPROVED:
                self.collected_statistics = True
                self.save()
                return

            # Collect statistics about country living in during the internship
            # Skip applicants who just filled out the location in the Comrade,
            # not the question in the essay page about where they would be
            # living during the internship
            try:
                data = BarriersToParticipation.objects.get(
                        applicant=self,
                        )
                if data.country_living_in_during_internship != 'Unknown' and self.approval_status == ApprovalStatus.APPROVED:
                    try:
                        # Country names may change. Do the ISO codes change??
                        stats = StatisticApplicantCountry.objects.get(
                                internship_round = self.application_round,
                                country_living_in_during_internship_code = self.barrierstoparticipation.country_living_in_during_internship_code,
                                )

                    except StatisticApplicantCountry.DoesNotExist:
                        stats = StatisticApplicantCountry(
                                internship_round = self.application_round,
                                country_living_in_during_internship = self.barrierstoparticipation.country_living_in_during_internship,
                                country_living_in_during_internship_code = self.barrierstoparticipation.country_living_in_during_internship_code,
                                )
                    stats.total_applicants += 1
                    stats.save()
            except BarriersToParticipation.DoesNotExist:
                pass

            # Collect statistics about race and ethnicity for American applicants
            try:
                payment_eligibility = PaymentEligibility.objects.get(
                        applicant=self,
                        )
                if payment_eligibility.us_national_or_permanent_resident and self.approval_status == ApprovalStatus.APPROVED:
                    try:
                        stats = StatisticAmericanDemographics.objects.get(
                                internship_round = self.application_round,
                                )
                    except StatisticAmericanDemographics.DoesNotExist:
                        stats = StatisticAmericanDemographics(
                                internship_round = self.application_round,
                                )
                    stats.total_approved_american_applicants += 1

                    try:
                        race_and_ethnicity = ApplicantRaceEthnicityInformation.objects.get(
                                applicant=self,
                                )
                        if race_and_ethnicity.us_resident_demographics == True:
                            stats.total_approved_american_bipoc += 1
                    except ApplicantRaceEthnicityInformation.DoesNotExist:
                        pass
                    stats.save()
            except PaymentEligibility.DoesNotExist:
                pass

            # Collect statistics about gender identities
            try:
                gender_identity = ApplicantGenderIdentity.objects.get(
                        applicant=self,
                        )
                try:
                    stats = StatisticGenderDemographics.objects.get(
                            internship_round = self.application_round,
                            )
                except StatisticGenderDemographics.DoesNotExist:
                    stats = StatisticGenderDemographics(
                            internship_round = self.application_round,
                            )

                if gender_identity.transgender:
                    stats.total_transgender_people += 1
                if gender_identity.genderqueer:
                    stats.total_genderqueer_people += 1
                if gender_identity.man:
                    stats.total_men += 1
                if gender_identity.trans_masculine:
                    stats.total_trans_masculine_people += 1
                if gender_identity.woman:
                    stats.total_women += 1
                if gender_identity.trans_feminine:
                    stats.total_trans_feminine_people += 1

                non_binary_genders = [f.attname for f in gender_identity._meta.get_fields() if f.get_internal_type() == 'BooleanField' and f.name != 'prefer_not_to_say' and f.name != 'man' and f.name != 'woman' and f.name != 'trans_masculine' and f.name != 'trans_feminine' and f.name != 'transgender' and f.name != 'genderqueer']

                is_non_binary = False
                for gender in non_binary_genders:
                    if getattr(gender_identity, gender) == True:
                        is_non_binary = True

                if is_non_binary:
                    stats.total_non_binary_people += 1

                if gender_identity.self_identify:
                    stats.total_who_self_identified_gender += 1

                stats.save()

            except ApplicantGenderIdentity.DoesNotExist:
                pass

            self.collected_statistics = True
            self.save()
            # end atomic transaction

    def purge_sensitive_data(self):
        with transaction.atomic():
            try:
                data = ApplicantRaceEthnicityInformation.objects.get(applicant = self)
                data.delete()
            except ApplicantRaceEthnicityInformation.DoesNotExist:
                pass

            try:
                data = ApplicantGenderIdentity.objects.get(applicant = self)
                data.delete()
            except ApplicantGenderIdentity.DoesNotExist:
                pass

            try:
                data = BarriersToParticipation.objects.get(applicant = self)
                data.delete()
            except BarriersToParticipation.DoesNotExist:
                pass

            data = InitialApplicationReview.objects.filter(application = self)
            for d in data:
                d.delete()

            self.essay_qualities.clear()
            # end atomic transaction

    def is_approver(self, user):
        return user.is_staff

    def get_approver_email_list(self):
        return [email.organizers]

    def submission_and_editing_deadline(self):
        return self.application_round.initial_applications_close

    def reverse(self, view_name, **kwargs):
        kwargs['applicant_username'] = self.applicant.account.username
        return reverse(view_name, kwargs=kwargs)

    def get_preview_url(self):
        return self.reverse('applicant-review-detail')

    def get_action_url(self, action):
        return self.reverse('initial-application-action', action=action)

    def get_submitter_email_list(self):
        return [self.applicant.email_address()]

    def is_over_18(self):
        if not self.workeligibility:
            return None
        if self.workeligibility.over_18:
            return True
        return False

    def is_eligible_to_work(self):
        if not self.workeligibility:
            return None
        if self.workeligibility.eligible_to_work:
            return True
        return False

    def is_not_under_export_control(self):
        if not self.workeligibility:
            return None
        if self.workeligibility.under_export_control:
            return False
        return True

    def is_not_under_sanctions(self):
        if not self.workeligibility:
            return None
        if self.workeligibility.us_sanctioned_country:
            return False
        return True

    def was_not_intern_with_gsoc_or_outreachy(self):
        if not self.priorfossexperience:
            return None
        if self.priorfossexperience.gsoc_or_outreachy_internship:
            return False
        return True

    def required_days_free(self):
        try:
            SchoolInformation.objects.get(applicant=self)
            return self.application_round.minimum_days_free_for_students
        except SchoolInformation.DoesNotExist:
            return self.application_round.minimum_days_free_for_non_students

    def get_reason_for_status(self):
        if self.is_approved():
            return ''
        if self.reason_denied == 'GENERAL':
            if not self.workeligibility.over_18:
                return 'Younger than 18'

            if not self.workeligibility.eligible_to_work:
                return 'Not eligible to work'

            if self.workeligibility.under_export_control:
                return 'Under U.S. export control'

            if self.priorfossexperience and self.priorfossexperience.gsoc_or_outreachy_internship:
                return 'Participated in GSoC or Outreachy before'

            return 'Unknown'

        if self.reason_denied == 'SANCTIONED':
            return 'Under U.S. sanctions'

        if self.reason_denied == 'SELFIDENTIFY':
            return 'Self-identified their gender'

        if self.reason_denied == 'TIME':
            return 'Not enough days free'

        if self.reason_denied[:5] == 'ALIGN':
            return 'Essay answers not aligned with Outreachy program goals'

        if self.barrierstoparticipation and self.barrierstoparticipation.applicant_should_update:
            return 'Revisions to essay requested'

        # Not everyone filled out the school information model
        try:
            if self.schoolinformation and self.schoolinformation.applicant_should_update:
                return 'Revisions to school info requested'
        except SchoolInformation.DoesNotExist:
            pass

        if self.is_pending():
            return 'Essay review'

        return 'Unknown'

    def get_reviewer_comments(self):
        reviews = InitialApplicationReview.objects.filter(application=self)
        if not reviews:
            return []
        comments = []
        for r in reviews:
            comments.append((r.reviewer.comrade.public_name, r.comments))
        return comments

    def time_commitment_from_model(self, tc, hours):
        return {
                'start_date': tc.start_date,
                'end_date': tc.end_date,
                'hours': hours,
                }

    def get_time_commitments(self, **kwargs):
        current_round = self.application_round
        relevant = models.Q(applicant=self, **kwargs)

        noncollege_school_time_commitments = NonCollegeSchoolTimeCommitment.objects.filter(relevant)
        school_time_commitments = SchoolTimeCommitment.objects.filter(relevant).order_by('start_date')
        volunteer_time_commitments = VolunteerTimeCommitment.objects.filter(relevant)
        employment_time_commitments = EmploymentTimeCommitment.objects.filter(relevant)

        try:
            # XXX: there's at most one of these, but that isn't enforced in the model
            contractor_time_commitment = self.contractorinformation_set.get()
        except ContractorInformation.DoesNotExist:
            contractor_time_commitment = None

        tcs = [ self.time_commitment_from_model(d, d.hours_per_week)
                for d in volunteer_time_commitments or []
                if d ]
        ctcs = [ self.time_commitment_from_model(d, 0 if d.quit_on_acceptance else d.hours_per_week)
                for d in noncollege_school_time_commitments or []
                if d ]

        etcs = [ self.time_commitment_from_model(d, 0 if d.quit_on_acceptance else d.hours_per_week)
                for d in employment_time_commitments or []
                if d ]

        stcs = [ self.time_commitment_from_model(d, 40)
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

        internship_total_days = current_round.internends - current_round.internstarts

        # Catch the case where the person is never free during the internship period
        if longest_period_free == 0 and free_period_start_day == 0 and counter != 0:
            longest_period_free = None
            free_period_start_date = None
            free_period_end_date = None
            percentage_free = 0
        else:
            free_period_start_date = current_round.internstarts + datetime.timedelta(days=free_period_start_day)
            free_period_end_date = current_round.internstarts + datetime.timedelta(days=free_period_start_day + longest_period_free - 1)
            percentage_free = int(100 * longest_period_free / internship_total_days.days)

        return {
                'longest_period_free': longest_period_free,
                'percentage_free': percentage_free,
                'free_period_start_date': free_period_start_date,
                'free_period_end_date': free_period_end_date,
                'internship_total_days': internship_total_days,
                'school_time_commitments': school_time_commitments,
                'noncollege_school_time_commitments': noncollege_school_time_commitments,
                'volunteer_time_commitments': volunteer_time_commitments,
                'employment_time_commitments': employment_time_commitments,
                'contractor_time_commitment': contractor_time_commitment,
                }

    def get_relevant_time_commitments(self):
        """
        Same as get_time_commitments but limited to 90 days before or after the
        internship period.
        """

        current_round = self.application_round
        nearby_date = datetime.timedelta(days=30 * 3)
        return self.get_time_commitments(
            start_date__lte=current_round.internends + nearby_date,
            end_date__gte=current_round.internstarts - nearby_date,
        )

    def overlapping_school_terms(self):
        school_time_commitments = SchoolTimeCommitment.objects.filter(applicant=self)
        for term in school_time_commitments:
            if term.start_date <= self.application_round.internends and self.application_round.internstarts <= term.end_date:
                return True
        return False

    def get_essay_ratings(self):
        ratings_list = []
        ratings = InitialApplicationReview.objects.filter(application=self)
        for r in ratings:
           ratings_list.append(r.get_essay_rating())
        return ratings_list

    def get_question_models(self):
        parts = (
            ('Work Eligibility', 'workeligibility'),
            ('Tax Form information', 'paymenteligibility'),
            ('Prior Experience with Free and Open Source Software', 'priorfossexperience'),
        )
        result = []
        for label, field in parts:
            try:
                result.append((label, getattr(self, field)))
            except ObjectDoesNotExist:
                pass
        return result

    def get_all_red_flags(self):
        red_flags_list = []
        reviews = InitialApplicationReview.objects.filter(application=self)
        for r in reviews:
           red_flags_list.append(r.get_red_flags())
        return red_flags_list

    def get_possible_reviewers(self):
        return self.application_round.applicationreviewer_set.approved()

    def get_projects_contributed_to(self):
        return self.project_contributions.distinct().order_by(
            'project_round__community__name',
            'short_title',
        )

    def get_projects_applied_to(self):
        # FinalApplication sets the combination of applicant and project to be
        # unique. Since we've restricted results to a single applicant, each
        # matching FinalApplication will contribute exactly one Project. As a
        # result, this query does not need distinct().
        return Project.objects.filter(finalapplication__applicant=self)

    def __str__(self):
        return "{name} <{email}> - {status}".format(
                name=self.applicant.public_name,
                email=self.applicant.account.email,
                status=self.get_approval_status_display())

    class Meta:
        unique_together = (
                ('applicant', 'application_round'),
                )

def get_answers_for_all_booleans(obj):
    # getattr looks up the field's value on the object
    return [
        (f, "Yes" if getattr(obj, f.attname) else "No")
        for f in obj._meta.get_fields()
        if f.get_internal_type() == 'BooleanField'
    ]

class WorkEligibility(models.Model):
    applicant = models.OneToOneField(ApplicantApproval, on_delete=models.CASCADE, primary_key=True)

    over_18 = models.BooleanField(
            verbose_name='Will you be 18 years or older when the Outreachy internship starts?')

    student_visa_restrictions = models.BooleanField(
            verbose_name='Do you have a student visa?')

    eligible_to_work = models.BooleanField(
            verbose_name='Are you eligible to work for 40 hours a week in ALL the countries you will be living in for the entire internship period, and five weeks after the internship period ends?')

    under_export_control = models.BooleanField(
            verbose_name='Are you a person or entity restricted by United States of America export controls or sanctions programs?')

    us_sanctioned_country = models.BooleanField(
            verbose_name='Are you a citizen, resident, or national of Crimea, Cuba, Iran, North Korea, or Syria?',
            help_text="Outreachy's fiscal parent, Software Freedom Conservancy, is a 501(c)(3) charitable non-profit in the United States of America. As a U.S. non-profit, Conservancy must ensure that funds are not sent to countries under U.S. sanctions programs, such as Cuba, Iran, North Korea, or Syria. If you have citizenship with Cuba, Iran, North Korea, or Syria, please answer yes, even if you are not currently living in those countries. We will follow up with additional questions.")

    def get_answers(self):
        return get_answers_for_all_booleans(self)


class PaymentEligibility(models.Model):
    applicant = models.OneToOneField(ApplicantApproval, on_delete=models.CASCADE, primary_key=True)
    us_national_or_permanent_resident = models.BooleanField(
            verbose_name='Are you a citizen, national, or permanent resident of the United States of America?',
            help_text='Outreachy is open to applicants around the world. This question is only to determine which tax form you will need to fill out.')

    living_in_us = models.BooleanField(
            verbose_name='Will you be living in the United States of America during the Outreachy internship period, or for up to five weeks after the internship period ends?',
            help_text='Note that the interval in this question extends past the end of internships.')

    def get_answers(self):
        return get_answers_for_all_booleans(self)


class PriorFOSSExperience(models.Model):
    applicant = models.OneToOneField(ApplicantApproval, on_delete=models.CASCADE, primary_key=True)

    gsoc_or_outreachy_internship = models.BooleanField(
            verbose_name='Have you been accepted as a Google Summer of Code intern, an Outreach Program for Women intern, or an Outreachy intern before?',
            help_text='Please say yes even if you did not successfully complete the internship.')

    prior_contributor = models.BooleanField(
            verbose_name='Have you contributed to open source before?')

    prior_paid_contributor = models.BooleanField(verbose_name='Have you ever been PAID to contribute to free and open source software before?', help_text='Please include paid internships, contract work, employment, stipends, or grants.')

    def get_answers(self):
        return get_answers_for_all_booleans(self)


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

    # Iterate over the fields in self
    # if they're true, return a comma separated list of gender identities,
    # e.g. 'non-binary, agender and self-identify as ⚨'
    def __str__(self):
        # getattr looks up the field's value on the object
        gender_identities = [f.name.replace('_', ' ') for f in self._meta.get_fields() if f.get_internal_type() == 'BooleanField' and getattr(self, f.attname) and f.name != 'prefer_not_to_say']

        if self.self_identify:
            gender_identities.append('self-identifies as ' + self.self_identify)
        if self.prefer_not_to_say:
            gender_identities.append('prefers not to specify their gender identity')

        if not gender_identities:
            return ''

        gender_identity_string = ', '.join(gender_identities[:-1])

        if len(gender_identities) == 1:
            ending_joiner = ''
        else:
            ending_joiner = ' and '
        gender_identity_string = gender_identity_string + ending_joiner + gender_identities[-1]

        return gender_identity_string

    def get_answers(self):
        return [
            ({ 'verbose_name': 'What is your gender identity?' }, str(self)),
        ]


class ApplicantRaceEthnicityInformation(models.Model):
    applicant = models.OneToOneField(ApplicantApproval, on_delete=models.CASCADE, primary_key=True)

    us_resident_demographics = models.BooleanField(
            verbose_name='Are you Black/African American, Hispanic/Latinx, Native American, Alaska Native, Native Hawaiian, or Pacific Islander?')

    def get_answers(self):
        return get_answers_for_all_booleans(self)


class BarriersToParticipation(models.Model):
    ESSAY_LENGTH=1000
    applicant = models.OneToOneField(ApplicantApproval, on_delete=models.CASCADE, primary_key=True)

    content_warnings = models.CharField(verbose_name='Content warnings',
            blank=True,
            max_length=SENTENCE_LENGTH)

    # NOTE: Update home/templates/home/eligibility.html if you change the text here:
    country_living_in_during_internship = models.CharField(
            verbose_name='What country will you be living in during the internship?',
            max_length=PARAGRAPH_LENGTH,
            )

    # NOTE: This field must have the same name as the above field, but with '_code' at the end.
    # This is the two-letter country code from the ISO 3166-1 alpha-2 standard.
    # Country select js automatically fills in the country code via a hidden input field,
    # by looking for an input tag with the same id as the field above, plus '_code' appended.
    country_living_in_during_internship_code = models.CharField(
            verbose_name='ISO 3166-1 alpha-2 country code',
            max_length=2,
            blank=True,
            )

    underrepresentation = models.TextField(verbose_name='Are you part of an underrepresented group (in the technology industry of the country listed above)? How are you underrepresented?',
            max_length=ESSAY_LENGTH)

    lacking_representation = models.TextField(verbose_name='Does your learning environment have few people who share your identity or background? Please provide details.',
            max_length=ESSAY_LENGTH)

    systemic_bias = models.TextField(verbose_name='What systemic bias or discrimination have you faced while building your skills?',
            max_length=ESSAY_LENGTH)

    employment_bias = models.TextField(verbose_name='What systemic bias or discrimination would you face if you applied for a job in the technology industry of your country?',
            max_length=ESSAY_LENGTH)
    
    applicant_should_update = models.BooleanField(default=False)

    def get_answers(self):
        return [
                ({ 'verbose_name':
                    'What country will you be living in during the internship?',
                    }, self.country_living_in_during_internship
                ),
                ({ 'verbose_name':
                    'Are you part of an underrepresented group (in the technology industry of the country listed above)? How are you underrepresented?',
                    }, self.underrepresentation
                ),
                ({ 'verbose_name':
                    'Does your learning environment have few people who share your identity or background? Please provide details.',
                    }, self.lacking_representation
                ),
                ({ 'verbose_name':
                    'What systemic bias or discrimination have you faced while building your skills?',
                    }, self.systemic_bias
                ),
                ({ 'verbose_name':
                    'What systemic bias or discrimination would you face if you applied for a job in the technology industry of your country?',
                    }, self.employment_bias
                ),
        ]

class TimeCommitmentSummary(models.Model):
    applicant = models.OneToOneField(ApplicantApproval, on_delete=models.CASCADE, primary_key=True)

    enrolled_as_student = models.BooleanField(
            verbose_name='Are you (or will you be) a university or college student?')

    enrolled_as_noncollege_student = models.BooleanField(
            verbose_name='Are you (or will you be) enrolled in a coding school or self-paced online courses?')

    employed = models.BooleanField(
            verbose_name='Are you (or will you be) an employee?')

    contractor = models.BooleanField(
            verbose_name='Are you (or will you be) a contractor?',
            )

    volunteer_time_commitments = models.BooleanField(
            verbose_name='Are you (or will you be) a volunteer?')

class VolunteerTimeCommitment(models.Model):
    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)
    start_date = models.DateField(help_text="Date your volunteer time commitments start.")
    end_date = models.DateField(help_text="Date your volunteer time commitments end.")
    hours_per_week = models.IntegerField(
            help_text="Maximum hours per week spent volunteering.",
            validators=[validators.MinValueValidator(1)],
            )
    description = models.TextField(
            max_length=THREE_PARAGRAPH_LENGTH,
            blank=True,
            help_text="Please describe what kind of volunteer position and duties you have.")

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            error_string = 'Volunteer role start date ' + self.start_date.strftime("%Y-%m-%d") + ' is after volunteer role end date ' + self.end_date.strftime("%Y-%m-%d")
            raise ValidationError({'start_date': error_string})

class EmploymentTimeCommitment(models.Model):
    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)
    start_date = models.DateField(help_text="Start date of employment period.")
    end_date = models.DateField(help_text="End date of employment period.")
    hours_per_week = models.IntegerField(
            help_text="Number of hours per week required by your employment contract",
            validators=[validators.MinValueValidator(1)],
            )
    job_title = models.CharField(
            max_length=SENTENCE_LENGTH)
    job_description = models.TextField(
            max_length=THREE_PARAGRAPH_LENGTH,
            help_text="Please tell us about the work you do and your job duties.")
    quit_on_acceptance = models.BooleanField(
            help_text="I will quit this job or contract if I am accepted as an Outreachy intern.")

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            error_string = 'Employment period start date ' + self.start_date.strftime("%Y-%m-%d") + ' is after employment period end date ' + self.end_date.strftime("%Y-%m-%d")
            raise ValidationError({'start_date': error_string})

class NonCollegeSchoolTimeCommitment(models.Model):
    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)
    start_date = models.DateField(help_text="Date your coding school or online course starts.")
    end_date = models.DateField(help_text="Date your coding school or online course ends.")
    hours_per_week = models.IntegerField(
            help_text="Maximum hours per week spent on coursework, exercises, homework, and studying for this course.",
            validators=[validators.MinValueValidator(1)],
            )
    description = models.TextField(
            max_length=THREE_PARAGRAPH_LENGTH,
            blank=True,
            help_text="Please describe the course. Include the name and a link to the website of your coding school or organization offering online courses. Add the course name and a short description of course work.")
    quit_on_acceptance = models.BooleanField(
            help_text="I will quit this coding school or stop this self-paced online course if I am accepted as an Outreachy intern.")

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            error_string = 'Coding school or online class start date ' + self.start_date.strftime("%Y-%m-%d") + ' is after class end date ' + self.end_date.strftime("%Y-%m-%d")
            raise ValidationError({'start_date': error_string})

class OfficialSchool(models.Model):
    university_name = models.CharField(
            max_length=SENTENCE_LENGTH,
            help_text='University or college name')

    university_website = models.URLField(
            help_text="University or college website")

    notes = models.TextField(
            help_text="Notes to display to initial application reviewers",
            blank=True)

class OfficialSchoolTerm(models.Model):
    school = models.ForeignKey(OfficialSchool, on_delete=models.CASCADE)
    term_name = models.CharField(
            max_length=SENTENCE_LENGTH,
            verbose_name="Term name or term number",
            help_text="If the university uses term names (e.g. Winter 2018 term of Sophomore year), enter the current term name, year in college, and term year. If the university uses term numbers (e.g. 7th semester), enter the term number.")

    academic_calendar = models.URLField(
            blank=True,
            verbose_name="Link to the official academic calendar for this school term",
            help_text="If necessary, save a file to a cloud hosting service and add the link to it here.")

    start_date = models.DateField(
            verbose_name="Date classes start.",
            help_text="What is the first possible day of classes for all students?<br>If students who are in different school years or different semester numbers start classes on different dates, use the first possible date that students in that year or semester start classes.<br>If you do not know when the term will start, use the start date of that term from last year.")

    end_date = models.DateField(
            verbose_name="Date all exams end.",
            help_text="This is the date the university advertises for the last possible date of any exam for any student in the semester.")

    def overlaps(self, other):
        return self.start_date <= other.end_date and other.start_date <= self.end_date

class SchoolTimeCommitment(models.Model):
    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)

    term_name = models.CharField(
            max_length=SENTENCE_LENGTH,
            verbose_name="Term name or term number",
            help_text="If your university uses term names (e.g. Winter 2018 term of your Sophomore year), enter your current term name, year in college, and term year. If your university uses term numbers (e.g. 7th semester), enter the term number.")

    start_date = models.DateField(
            verbose_name="Date classes start.",
            help_text="What is the first possible day of classes for all students?<br>If you started this term late (or will start this term late), use the date that classes start for all students, not the late registration date.<br>If students who are in different school years or different semester numbers start classes on different dates, use the first possible date that students in your year or semester start classes.<br>If you do not know when the term will start, use the start date of that term from last year.<br>If you don't see a calendar pop-up, please use the date format YYYY-MM-DD.")

    end_date = models.DateField(
            verbose_name="Date all exams end.",
            help_text="This is the date your university advertises for the last possible date of any exam for any student in your semester. Use the last possible exam date, even if your personal exams end sooner. If you don't see a calendar pop-up, please use the date format YYYY-MM-DD.")

    last_term = models.BooleanField(
            default=False,
            help_text="This is the last term in my degree.")

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            error_string = 'School term (' + self.term_name + ') start date ' + self.start_date.strftime("%Y-%m-%d") + ' is after term end date ' + self.end_date.strftime("%Y-%m-%d")
            raise ValidationError({'start_date': error_string})

class SchoolInformation(models.Model):
    applicant = models.OneToOneField(ApplicantApproval, on_delete=models.CASCADE, primary_key=True)

    university_name = models.CharField(
            max_length=SENTENCE_LENGTH,
            help_text='University or college name')

    university_website = models.URLField(help_text="University or college website")

    current_academic_calendar = models.URLField(verbose_name="Link to your official academic calendar for your *current* school term",
            help_text="Please provide a link on your school's official website. Some schools do not make their calendars publicly available. You can upload your calendar to a file sharing service, but the Outreachy organizers may not take it into account when validating your school dates.")

    next_academic_calendar = models.URLField(
            verbose_name="Link to your official academic calendar for your *next* school term",
            help_text="If the calendar for your next term is not released yet, link to last year's academic calendar for that term. Some schools do not make their calendars publicly available. You can upload your calendar to a file sharing service, but the Outreachy organizers may not take it into account when validating your school dates.")

    degree_name = models.CharField(
            max_length=SENTENCE_LENGTH,
            help_text='What degree(s) are you pursuing?')

    school_term_updates = models.TextField(
            max_length=THREE_PARAGRAPH_LENGTH,
            blank=True,
            verbose_name='Provide any updates about your school term information',
            help_text="<p>If the school terms above are incorrect, or you have forgotten to include a term that overlaps with the Outreachy internship period, please update your terms.<p>For each school term, please provide:</p><ol><li>The term name</li><li>The start date of classes for ALL students in the school</li><li>The end date of exams for ALL students in the school</li></ol><p>Please do not modify your dates to differ from the starting dates in your academic calendar. Outreachy organizers cannot accept statements that you will start your classes late.</p>")
    applicant_should_update = models.BooleanField(default=False)

    @property
    def school_domain(self):
        return urlparse(self.university_website).hostname.removeprefix('www.')

    @staticmethod
    def roll_year(d, years):
        try:
            return d.replace(year=d.year + years)
        except ValueError:
            assert d.month == 2 and d.day == 29
            return d.replace(year=d.year + years, month=3, day=1)

    def find_official_terms(self):
        # find terms happening near the time of the current round from all
        # OfficialSchools with the same domain
        all_terms = OfficialSchoolTerm.objects.filter(
            school__university_website__icontains=self.school_domain,
        ).order_by(
            'school__university_website',
            # sort newest terms first so they override older year's terms
            '-start_date',
        )

        current_round = self.applicant.application_round
        nearby_date = datetime.timedelta(days=30*3)
        start_date = current_round.internstarts - nearby_date
        end_date = current_round.internends + nearby_date

        terms = []
        for school_id, school_terms in groupby(all_terms, key=lambda term: term.school_id):
            best_terms = []
            for term in school_terms:
                years_old = 0
                while self.roll_year(term.end_date, years_old) < start_date:
                    years_old += 1

                term.start_date = self.roll_year(term.start_date, years_old)
                if term.start_date > end_date:
                    # Even after adjusting the year, this term does not overlap
                    # the current round.
                    continue

                term.end_date = self.roll_year(term.end_date, years_old)

                # Okay, we've found an adjusted year that makes this term
                # overlap the current round. But if we've already seen a more
                # recent term (i.e. a term we didn't have to adjust as much)
                # that overlaps this one, prefer that one instead.
                drop = any(
                    other_years < years_old and other_term.overlaps(term)
                    for other_term, other_years in best_terms
                )
                if not drop:
                    best_terms.append((term, years_old))

            # Get this school's best terms in order by adjusted start date
            terms.extend(sorted((term for term, years_old in best_terms), key=lambda term: term.start_date))

        return terms

    def classmate_statistics(self):
        classmates = ApplicantApproval.objects.filter(
            application_round=self.applicant.application_round,
            schoolinformation__university_website__icontains=self.school_domain,
        )

        # Find students who are graduating after their current term. This weird
        # query checks for students who have a last_term but don't have any
        # non-last_terms.
        graduating_students = ApplicantApproval.objects.filter(
            schooltimecommitment__last_term=True,
        ).exclude(
            schooltimecommitment__last_term=False,
        )
        # Check if this student is one of the graduating students.
        graduating = graduating_students.filter(pk=self.applicant_id).exists()

        # Compute statistics only over students who are in the same situation
        # as this student: either they're all graduating, or none of them are.
        # This matters because we interpret time commitments differently for
        # students who are in their last term.
        if graduating:
            classmates = classmates.filter(pk__in=graduating_students)
        else:
            classmates = classmates.exclude(pk__in=graduating_students)

        total = classmates.count()
        accepted = classmates.approved().count()
        rejected = classmates.rejected().filter(reason_denied="TIME").count()

        all_classmates = ApplicantApproval.objects.filter(
            application_round=self.applicant.application_round,
            schoolinformation__university_website__icontains=self.school_domain,
        ).exclude(pk=self.applicant.pk).order_by('pk')
        rejected_classmates = all_classmates.rejected().filter(reason_denied="TIME")
        all_classmates = all_classmates.exclude(pk__in=rejected_classmates)

        return {
            'graduating': graduating,
            'pending_classmates': classmates.pending().count(),
            'total_classmates': total,
            'acceptance_rate': 100 * accepted / total,
            'time_rejection_rate': 100 * rejected / total,
            'all_classmates': all_classmates,
            'rejected_classmates': rejected_classmates,
        }

    def print_terms(school_info):
        print(school_info.applicant.get_approval_status_display(), " ", school_info.applicant.applicant.public_name, " <", school_info.applicant.applicant.account.email, ">")
        print(school_info.university_name)
        terms = SchoolTimeCommitment.objects.filter(applicant__applicant__account__email=school_info.applicant.applicant.account.email)
        for t in terms:
            print("Term: ", t.term_name, "; Start date: ", t.start_date, "; End date: ", t.end_date)

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

    def clean(self):
        if self.university_website and self.current_academic_calendar and self.next_academic_calendar:
            error_string = 'You must provide a valid academic calendar'
            if self.university_website == self.current_academic_calendar:
                raise ValidationError({'current_academic_calendar': error_string})
            if self.university_website == self.next_academic_calendar:
                raise ValidationError({'next_academic_calendar': error_string})

            # Allow students to use the same academic calendar link for both terms,
            # since the terms might be listed on the same page.

class ContractorInformation(models.Model):
    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)

    typical_hours = models.IntegerField(
            validators=[validators.MinValueValidator(1)],
            verbose_name="Average number of hours spent on contractor business",
            help_text="During the past three months, what is the average number of hours/week you have spent on contracted work and unpaid business development or business marketing? You will be able to enter your known contract hours for the Outreachy internship period on the next page.")

    continuing_contract_work = models.BooleanField(
        verbose_name="Will you be doing contract work during the Outreachy internship period?",
        null=True,
    )


class PromotionTracking(models.Model):
    applicant = models.OneToOneField(ApplicantApproval, on_delete=models.CASCADE, primary_key=True)

    AISES = 'AISES'
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
        (AISES, 'Job board - American Indian Science and Engineering Society'),
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


# --------------------------------------------------------------------------- #
# end initial application models
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# reviewer models
# --------------------------------------------------------------------------- #

class InitialApplicationReview(models.Model):
    application = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(ApplicationReviewer, on_delete=models.CASCADE)

    STRONG = '+3'
    GOOD = '+2'
    MAYBE = '+1'
    UNCLEAR = '??'
    UNRATED = '0'
    NOTCOMPELLING = '-1'
    NOTUNDERSTOOD = '-2'
    SPAM = '-3'
    # Change essay choices in home/templates/home/snippet/applicant_review_essay_rating.html
    # if you update this text
    RATING_CHOICES = (
        (STRONG, '+3 - Essay is *strongly* compelling'),
        (GOOD, '+2 - Essay is compelling'),
        (MAYBE, '+1 - Essay is *weakly* compelling'),
        (UNCLEAR, '?? - Essay questions were too short or unclear to make a decision'),
        (UNRATED, 'Not rated'),
        (NOTCOMPELLING, '-1 - Essay is not compelling'),
        (NOTUNDERSTOOD, '-2 - Answers are unrelated to essay questions'),
        (SPAM, '-3 - Essay answers were spam or trolling'),
    )
    essay_rating = models.CharField(
            max_length=2,
            choices=RATING_CHOICES,
            default=UNRATED)

    # Time commitments red flags
    review_school = models.BooleanField(default=False,
            verbose_name="School term info needs review or follow up")

    missing_school = models.BooleanField(default=False,
            verbose_name="Essay mentioned school, but no school term info was supplied")

    review_work = models.BooleanField(default=False,
            verbose_name="Work time commitments need review or follow up")

    missing_work = models.BooleanField(default=False,
            verbose_name="Essay mentioned work, but no work hours info was supplied")

    incorrect_dates = models.BooleanField(default=False,
            verbose_name="Dates on time commitments look incorrect")

    comments = models.TextField(
            max_length=EIGHT_PARAGRAPH_LENGTH,
            blank=True,
            verbose_name="Reviewer comments",
            help_text="Please provide any comments on the status of this initial application, or questions you have while reviewing it.")

    def get_essay_rating(self):
        if self.essay_rating == self.UNRATED:
            return ''

        return (self.essay_rating, self.reviewer.comrade.public_name)

    def get_red_flags(self):
        red_flags = []
        if self.review_school:
            red_flags.append('Review school terms')
        if self.missing_school:
            red_flags.append('Missing school terms')
        if self.review_work:
            red_flags.append('Review work commitments')
        if self.missing_work:
            red_flags.append('Missing work hours')
        if self.incorrect_dates:
            red_flags.append('Needs organizer follow-up')

        return (red_flags, self.reviewer.comrade.public_name)

#class UniversityInformation(models.Model):
#    university_name = models.CharField(
#            max_length=SENTENCE_LENGTH,
#            help_text='University or college name')
#
#    university_website = models.URLField(help_text="University or college website")
#
#    term_name = models.CharField(
#            max_length=SENTENCE_LENGTH,
#            verbose_name="Term name or term number",
#            help_text="If your university uses term names (e.g. Winter 2018 term of your Sophomore year), enter your current term name, year in college, and term year. If your university uses term numbers (e.g. 7th semester), enter the term number.")
#
#    start_date = models.DateField(
#            verbose_name="Date classes start.",
#            help_text="What is the first possible day of classes for all students?<br>If you started this term late (or will start this term late), use the date that classes start for all students, not the late registration date.<br>If students who are in different school years or different semester numbers start classes on different dates, use the first possible date that students in your year or semester start classes.<br>If you do not know when the term will start, use the start date of that term from last year.")
#
#    end_date = models.DateField(
#            verbose_name="Date all exams end.",
#            help_text="This is the date your university advertises for the last possible date of any exam for any student in your semester. Use the last possible exam date, even if your personal exams end sooner.")

# --------------------------------------------------------------------------- #
# end reviewer models
# --------------------------------------------------------------------------- #

class Contribution(models.Model):
    """
    An Outreachy applicant must make contributions to a project in order to be
    eligible to be accepted as an intern. The Contribution model is a record
    of that contribution that the applicant submits to the Outreachy website.
    Contributions are recorded from the start of the contribution period to
    when the final application is due. Applicants who have submitted a final
    application can continue to record contributions until the intern
    announcement.
    """

    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)

    date_started = models.DateField(verbose_name="Date contribution was started")
    date_merged = models.DateField(verbose_name="Date contribution was accepted or merged",
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

    def __str__(self):
        return '{applicant} contribution for {community} - {project}'.format(
                applicant = self.applicant.applicant.public_name,
                community = self.project.project_round.community,
                project = self.project.short_title,
                )

class FinalApplication(ApprovalStatus):
    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)

    experience = models.TextField(
            max_length=EIGHT_PARAGRAPH_LENGTH,
            verbose_name="Past experience with this community",
            help_text="Please describe your experience before this Outreachy application period with this free software community. You can describe your prior experiences as both a user and a contributor.")

    foss_experience = models.TextField(
            max_length=EIGHT_PARAGRAPH_LENGTH,
            verbose_name="Past experience with other communities",
            help_text="Please describe your experience before this Outreachy application period with any other free software communities. You can describe your prior experiences as both a user and a contributor.")

    relevant_projects = models.TextField(
            max_length=EIGHT_PARAGRAPH_LENGTH,
            verbose_name="Relevant Projects",
            help_text="Please describe any relevant projects (either personal, work, or school projects) that helped you gain skills you will use in this project. Talk about what knowledge you gained from working on them. Include links where possible.")

    applying_to_gsoc = models.TextField(
            max_length=EIGHT_PARAGRAPH_LENGTH,
            blank=True,
            verbose_name="(Optional) Please describe which Google Summer of Code communities and projects you are applying for, and provide mentor contact information",
            help_text='If you are a student at an accredited university or college, we highly encourage you to also apply to <a href="https://summerofcode.withgoogle.com/">Google Summer of Code</a> during the May to August internship round. Many Outreachy communities participate in both programs, and applying to Google Summer of Code increases your chances of being accepted as an intern. Please note that <a href="https://developers.google.com/open-source/gsoc/help/student-stipends">Google Summer of Code has stipend amounts that vary per country</a>.<br><br>Please keep the list of communities and projects you are applying to under Google Summer of Code up-to-date, since we often try to coordinate with Google Summer of Code mentors during the intern selection period.<br><br>If this application is for the December to March internship period, or you are not applying to Google Summer of Code, please leave this question blank.')

    time_correct = models.BooleanField(
            verbose_name="Are the time commitments listed above correct?",
            help_text='If any time commitments (like a job or school) are missing, say no. If any start or end dates are incorrect, say no.',
            default=False)

    time_updates = models.TextField(
            max_length=EIGHT_PARAGRAPH_LENGTH,
            blank=True,
            verbose_name="(Optional) If your time commitments are incorrect or have changed, please provide your updated time commitments. **Please leave this blank if your time commitments are correct.**",
            help_text='Make sure your time commitments lists any current or future jobs you have, even if you are taking a leave of absence.')

    community_specific_questions = models.TextField(
            max_length=EIGHT_PARAGRAPH_LENGTH,
            blank=True,
            verbose_name="(Optional) Community-specific Questions",
            help_text="Some communities or projects may want you to answer additional questions. Please check with your mentor and community coordinator to see if you need to provide any additional information after you save your final application.")

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
        approved_mentor = self.project.mentors_set.approved().filter(mentor__account=user)
        if approved_mentor:
            return True
        return False

    def is_submitter(self, user):
        if self.applicant.applicant.account_id == user.id:
            return True
        return False

    # We have a separate view for mentors to see applicants
    def objects_for_dashboard(cls, user):
        return None

    def get_action_url(self, action):
        return self.project.reverse(
            'final-application-action',
            username=self.applicant.applicant.account.username,
            action=action,
        )

    def get_mentor_agreement_url(self):
        return self.project.reverse(
            'select-intern',
            applicant_username=self.applicant.applicant.account.username,
        )

    def submission_and_approval_deadline(self):
        return self.project.round().contributions_close

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
        return self.applicant.internselection_set.exclude(
            funding_source=InternSelection.NOT_FUNDED,
        ).exclude(
            project=self.project,
        )

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
    date_signed = models.DateField(verbose_name="Date contract was signed")

class InternSelection(AugmentDeadlines, models.Model):
    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
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
    organizer_approved = models.BooleanField(
            help_text="Is this intern and funding information confirmed to be correct by the Outreachy organizers?",
            null=True,
            default=None)
    survey_opt_out = models.BooleanField(default=False)
    in_good_standing = models.BooleanField(default=True)

    intern_starts = models.DateField("Date the internship starts", blank=True)
    initial_feedback_opens = models.DateField("Date initial feedback form opens (typically 7 days before the initial feedback deadline)", blank=True)
    initial_feedback_due = models.DateField("Date initial feedback form due", blank=True)
    midpoint_feedback_opens = models.DateField("Date mid-point feedback form opens (typically 7 days before the mid-point feedback deadline)", blank=True)
    midpoint_feedback_due = models.DateField("Date mid-point feedback form due", blank=True)
    feedback3_opens = models.DateField(verbose_name="Date feedback #3 form opens", blank=True, null=True)
    feedback3_due = models.DateField(verbose_name="Date feedback #3 form is due", blank=True, null=True)
    final_feedback_opens = models.DateField("Date final feedback form opens", blank=True)
    final_feedback_due = models.DateField("Date final feedback form due (typically 3 days after the internship ends)", blank=True)
    intern_ends = models.DateField("Date the internship ends", blank=True)

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
        return self.mentors.approved().filter(mentor__account=user).exists()

    def intern_has_custom_dates(self):
        if self.intern_starts != self.project.round().internstarts:
            return True
        if self.intern_ends != self.project.round().internends:
            return True
        if self.initial_feedback_due != self.project.round().initialfeedback:
            return True
        if self.midpoint_feedback_due != self.project.round().midfeedback:
            return True
        if self.feedback3_due != self.project.round().feedback3_due:
            return True
        return False

    def get_internship_extension_amount_in_weeks(self):
        return math.ceil((self.intern_ends - self.project.round().internends).days / 7)

    def is_initial_feedback_on_intern_open(self):
        if not self.initial_feedback_opens.has_passed():
            return False
        try:
            return self.feedback1frommentor.can_edit()
        except Feedback1FromMentor.DoesNotExist:
            return True

    def is_initial_feedback_on_intern_past_due(self):
        if self.initial_feedback_due.has_passed():
            return True
        return False

    def is_initial_feedback_on_mentor_open(self):
        if not self.initial_feedback_opens.has_passed():
            return False
        try:
            return self.feedback1fromintern.can_edit()
        except Feedback1FromIntern.DoesNotExist:
            return True

    def is_feedback_2_form_open_to_mentor(self):
        if not self.midpoint_feedback_opens.has_passed():
            return False
        try:
            return self.feedback2frommentor.can_edit()
        except Feedback2FromMentor.DoesNotExist:
            return True

    def is_feedback_2_from_mentor_past_due(self):
        if self.midpoint_feedback_due.has_passed():
            return True
        return False

    def is_feedback_2_form_open_to_intern(self):
        if not self.midpoint_feedback_opens.has_passed():
            return False
        try:
            return self.feedback2fromintern.can_edit()
        except Feedback2FromIntern.DoesNotExist:
            return True

    def is_feedback_3_form_open_to_mentor(self):
        if not self.feedback3_opens or not self.feedback3_opens.has_passed():
            return False
        try:
            return self.feedback3frommentor.can_edit()
        except Feedback3FromMentor.DoesNotExist:
            return True

    def is_feedback_3_from_mentor_past_due(self):
        if not self.feedback3_due:
            return False
        if self.feedback3_due.has_passed():
            return True
        return False

    def is_feedback_3_form_open_to_intern(self):
        if not self.feedback3_opens or not self.feedback3_opens.has_passed():
            return False
        try:
            return self.feedback3fromintern.can_edit()
        except Feedback3FromIntern.DoesNotExist:
            return True

    def is_final_feedback_on_intern_open(self):
        if not self.final_feedback_opens.has_passed():
            return False
        try:
            return self.feedback4frommentor.can_edit()
        except Feedback4FromMentor.DoesNotExist:
            return True

    def is_final_feedback_on_intern_past_due(self):
        if self.final_feedback_due.has_passed():
            return True
        return False

    def is_final_feedback_on_mentor_open(self):
        if not self.final_feedback_opens.has_passed():
            return False
        try:
            return self.feedback4fromintern.can_edit()
        except Feedback4FromIntern.DoesNotExist:
            return True

    def is_internship_active(self):
        """
        Is the internship currently running?

        The internship "runs" from when the internship is announced until either
        1) the internship is terminated early, or
        2) the Outreachy organizers review the final feedback submitted by the mentor.

        This function returns False if the internship is not approved, has not yet been announced, or has ended.
        Otherwise if the internship is approved and running, it returns true.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        today = get_deadline_date_for(now)

        # Is the intern selection rejected by the Outreachy organizers?
        if not self.organizer_approved:
            return False

        # Has the internship not been announced yet?
        if self.project.project_round.participating_round.internannounce > today:
            return False

        # Has the internship been terminated early?
        if not self.in_good_standing:
            return False

        # Is the mentor final feedback waiting to be reviewed by Outreachy organizers?
        try:
            if self.finalmentorfeedback.organizer_payment_approved == None:
                return True
        # Has the mentor not given final feedback yet?
        except FinalMentorFeedback.DoesNotExist:
            return True

        # The intern final feedback has been reviewed by Outreachy organizers
        return False

    def has_final_payment_passed(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        today = get_deadline_date_for(now)

        try:
            # Even with delays in processing feedback,
            # interns should be paid 60 days after their final feedback due date
            if self.finalmentorfeedback.organizer_payment_approved == True and self.final_feedback_due + datetime.timedelta(days=60) < today:
                return True
            return False
        # Has the mentor not given final feedback yet?
        except FinalMentorFeedback.DoesNotExist:
            return False

    def intern_name(self):
        return self.applicant.applicant.public_name

    def round(self):
        return self.project.round()

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

    def coordinator_names(self):
        return " and ".join(self.project.project_round.community.get_coordinator_names())

    def get_application(self):
        return FinalApplication.objects.get(
                project=self.project,
                applicant=self.applicant,
                )

    def get_previous_initial_applications(self):
        return ApplicantApproval.objects.filter(
                applicant=self.applicant.applicant,
                ).exclude(application_round=self.project.project_round.participating_round)

    def needs_cpt(self):
        work_info = WorkEligibility.objects.get(
                applicant=self.applicant)
        return work_info.student_visa_restrictions

    def get_intern_selection_conflicts(self):
        if self.funding_source == self.NOT_FUNDED:
            return []
        return InternSelection.objects.filter(
            project__project_round__participating_round=self.project.round(),
            applicant=self.applicant,
        ).exclude(funding_source=self.NOT_FUNDED).exclude(project=self.project).all()

    SUBMITTED = 'SUB'
    MISSING = 'MIS'
    PAY = 'PAY'
    PAID = 'PAID'
    EXTEND = 'EXT'
    DUNNO = 'DUN'
    TERMINATE = 'TER'
    def get_mentor_initial_feedback_status(self):
        try:
            if self.feedback1frommentor.organizer_payment_approved:
                return self.PAID

            actions_requested = self.feedback1frommentor.actions_requested
            if actions_requested == BaseMentorFeedback.TERMINATE_PAY or actions_requested == BaseMentorFeedback.TERMINATE_NO_PAY:
                return self.TERMINATE
            elif actions_requested == BaseMentorFeedback.PAY_AND_CONTINUE:
                return self.PAY
            elif actions_requested == BaseMentorFeedback.DONT_KNOW:
                return self.DUNNO
            else:
                return self.EXTEND
        except Feedback1FromMentor.DoesNotExist:
            return self.MISSING

    def get_intern_initial_feedback_status(self):
        try:
            if self.feedback1fromintern:
                return self.SUBMITTED
        except Feedback1FromIntern.DoesNotExist:
            return self.MISSING

    def get_mentor_midpoint_feedback_status(self):
        try:
            if self.feedback2frommentor.organizer_payment_approved:
                return self.PAID

            actions_requested = self.feedback2frommentor.actions_requested
            if actions_requested == BaseMentorFeedback.TERMINATE_PAY or actions_requested == BaseMentorFeedback.TERMINATE_NO_PAY:
                return self.TERMINATE
            elif actions_requested == BaseMentorFeedback.PAY_AND_CONTINUE:
                return self.PAY
            elif actions_requested == BaseMentorFeedback.DONT_KNOW:
                return self.DUNNO
            else:
                return self.EXTEND
        except Feedback2FromMentor.DoesNotExist:
            return self.MISSING

    def get_feedback_3_status_from_mentor(self):
        try:
            if self.feedback3frommentor.organizer_payment_approved:
                return self.PAID

            actions_requested = self.feedback3frommentor.actions_requested
            if actions_requested == BaseMentorFeedback.TERMINATE_PAY or actions_requested == BaseMentorFeedback.TERMINATE_NO_PAY:
                return self.TERMINATE
            elif actions_requested == BaseMentorFeedback.PAY_AND_CONTINUE:
                return self.PAY
            elif actions_requested == BaseMentorFeedback.DONT_KNOW:
                return self.DUNNO
            else:
                return self.EXTEND
        except Feedback3FromMentor.DoesNotExist:
            return self.MISSING

    def get_feedback_3_status_from_intern(self):
        try:
            if self.feedback3fromintern:
                return self.SUBMITTED
        except Feedback3FromIntern.DoesNotExist:
            return self.MISSING

    def get_feedback_4_status_from_mentor(self):
        try:
            if self.feedback4frommentor.organizer_payment_approved:
                return self.PAID

            actions_requested = self.feedback4frommentor.actions_requested
            if actions_requested == BaseMentorFeedback.TERMINATE_PAY or actions_requested == BaseMentorFeedback.TERMINATE_NO_PAY:
                return self.TERMINATE
            elif actions_requested == BaseMentorFeedback.PAY_AND_CONTINUE:
                return self.PAY
            elif actions_requested == BaseMentorFeedback.DONT_KNOW:
                return self.DUNNO
            else:
                return self.EXTEND
        except Feedback4FromMentor.DoesNotExist:
            return self.MISSING

    def get_feedback_4_status_from_intern(self):
        try:
            if self.feedback4fromintern:
                return self.SUBMITTED
        except Feedback4FromIntern.DoesNotExist:
            return self.MISSING

    def get_intern_midpoint_feedback_status(self):
        try:
            if self.feedback2fromintern:
                return self.SUBMITTED
        except Feedback2FromIntern.DoesNotExist:
            return self.MISSING

    def get_mentor_final_feedback_status(self):
        try:
            if self.finalmentorfeedback.organizer_payment_approved:
                return self.PAID

            actions_requested = self.finalmentorfeedback.actions_requested
            if actions_requested == BaseMentorFeedback.TERMINATE_PAY or actions_requested == BaseMentorFeedback.TERMINATE_NO_PAY:
                return self.TERMINATE
            elif actions_requested == BaseMentorFeedback.PAY_AND_CONTINUE:
                return self.PAY
            elif actions_requested == BaseMentorFeedback.DONT_KNOW:
                return self.DUNNO
            else:
                return self.EXTEND
        except FinalMentorFeedback.DoesNotExist:
            return self.MISSING

    def get_intern_final_feedback_status(self):
        try:
            if self.finalinternfeedback:
                return self.SUBMITTED
        except FinalInternFeedback.DoesNotExist:
            return self.MISSING

    def __str__(self):
        return self.mentor_names() + ' mentoring ' + self.applicant.applicant.public_name

class MentorRelationship(models.Model):
    intern_selection = models.ForeignKey(InternSelection, on_delete=models.CASCADE)
    mentor = models.ForeignKey(MentorApproval, on_delete=models.CASCADE)
    # When a mentor relationship is removed, keep the signed mentor contract
    # If a mentor withdraws from the mentor relationship, we still need to preserve the contract they signed
    # This does mean we'll keep the contract after a mentor removes an intern,
    # but we can't tell the difference easily.
    contract = models.OneToOneField(SignedContract, on_delete=models.SET_NULL, null=True)

    def intern_name(self):
        return self.intern_selection.applicant.applicant.public_name

    def round(self):
        return self.intern_selection.project.round()

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

class BaseFeedback(models.Model):
    intern_selection = models.OneToOneField(InternSelection, on_delete=models.CASCADE)
    allow_edits = models.BooleanField()
    ip_address = models.GenericIPAddressField(protocol="both")

    def intern_name(self):
        return self.intern_selection.intern_name()

    def round(self):
        return self.intern_selection.round()

    def community_name(self):
        return self.intern_selection.community_name()

    def project_name(self):
        return self.intern_selection.project_name()

    class Meta:
        abstract = True

class BaseMentorFeedback(BaseFeedback):
    last_contact = models.DateField(verbose_name="What was the last date you were in contact with your intern?")

    mentors_report = models.TextField(verbose_name="Please provide a paragraph describing what support you are providing as an Outreachy mentor. This will be shared with Outreachy organizers and your community coordinator.")

    full_time_effort = models.BooleanField(verbose_name="Do you believe your Outreachy intern is putting in a full-time, 40 hours a week effort into the internship?")

    # FIXME - send email to mentors and interns when organizers approve their payment and send documentation off to Conservancy
    organizer_payment_approved = models.BooleanField(
        help_text="Outreachy organizers approve or do not approve to pay this intern.",
        null=True,
        default=None,
    )

    # Deprecated - this data is set in clean() to be used for intern payment authorization JSON export
    request_extension = models.BooleanField(verbose_name="Does your intern need an extension?", help_text="Sometimes interns do not put in a full-time effort. In this case, one of the options is to delay payment of their stipend and extend their internship a specific number of weeks. You will be asked to re-evaluate your intern after the extension is done.")

    # Deprecated - this data is set in clean() to be used for intern payment authorization JSON export
    request_termination = models.BooleanField(verbose_name="Do you believe the internship should be terminated?", help_text="Sometimes after several extensions, interns still do not put in a full-time effort. If you believe that your intern would not put in a full-time effort with a further extension, you may request to terminate the internship. The Outreachy organizers will be in touch to discuss the request.")

    PAY_AND_CONTINUE = 'PAYCONT'
    EXT_1_WEEK = '1WEEK'
    EXT_2_WEEK = '2WEEK'
    EXT_3_WEEK = '3WEEK'
    EXT_4_WEEK = '4WEEK'
    EXT_5_WEEK = '5WEEK'
    TERMINATE_PAY = 'TERMPAY'
    TERMINATE_NO_PAY = 'TERMNOPAY'
    DONT_KNOW = 'DONTKNOW'

    def set_payment_for_json_export(self):
        # Set whether an internship stipend has been requested to be paid
        if self.actions_requested == BaseMentorFeedback.PAY_AND_CONTINUE or self.actions_requested == BaseMentorFeedback.TERMINATE_PAY:
            self.payment_approved = True
        else:
            self.payment_approved = False

    def set_termination_request_for_json_export(self):
        # Set whether the mentor requested an internship contract be terminated
        if self.actions_requested == BaseMentorFeedback.TERMINATE_PAY or self.actions_requested == BaseMentorFeedback.TERMINATE_NO_PAY:
            self.request_termination = True
        else:
            self.request_termination = False

    def set_and_return_extension_for_json_export(self):
        # Set whether an internship extension has been requested
        # Return how many more weeks a mentor is requesting for an internship extension
        if self.actions_requested == BaseMentorFeedback.PAY_AND_CONTINUE or self.actions_requested == BaseMentorFeedback.TERMINATE_PAY or self.actions_requested == BaseMentorFeedback.TERMINATE_NO_PAY or self.actions_requested == BaseMentorFeedback.DONT_KNOW:
            self.request_extension = False
            return 0

        self.request_extension = True
        if self.actions_requested == BaseMentorFeedback.EXT_1_WEEK:
            return 1
        elif self.actions_requested == BaseMentorFeedback.EXT_2_WEEK:
            return 2
        elif self.actions_requested == BaseMentorFeedback.EXT_3_WEEK:
            return 3
        elif self.actions_requested == BaseMentorFeedback.EXT_4_WEEK:
            return 4
        elif self.actions_requested == BaseMentorFeedback.EXT_5_WEEK:
            return 5

    def get_versions(self):
        return Version.objects.get_for_object(self)

    def find_version_mentor_edited(self):
        # When a staff member modifies the initial feedback to approve payment or change internship dates,
        # it counts as a revision. Look for the latest feedback from an approved mentor.
        # (Note: this may not won't work if we switch mentors.
        # we could ignore all revisions made by staff, but staff can be mentors too.)
        versions = Version.objects.get_for_object(self)
        for v in versions:
            if self.intern_selection.mentors.all().approved().filter(mentor__account=v.revision.user).exists():
                return v
        return None

    def get_submission_date(self):
        version = self.find_version_mentor_edited()
        if version:
            return version.revision.date_created

    def get_mentor_public_name(self):
        version = self.find_version_mentor_edited()
        if version:
            return version.revision.user.comrade.public_name

    def get_mentor_legal_name(self):
        version = self.find_version_mentor_edited()
        if version:
            return version.revision.user.comrade.legal_name

    def get_mentor_email(self):
        version = self.find_version_mentor_edited()
        if version:
            return version.revision.user.email

    def get_date_submitted(self):
        version = self.find_version_mentor_edited()
        if version:
            return version.revision.date_created

    class Meta:
        abstract = True

class Feedback1FromMentor(BaseMentorFeedback):
    # XXX - Make sure to change the questions in
    # home/templates/home/email/initial-feedback-instructions.txt
    # home/templates/home/feedback1frommentor_form.html
    # if you change these verbose names.

    # 1. Clearing up doubts
    mentor_answers_questions = models.BooleanField(verbose_name="Do you (or a co-mentor) answer the intern's questions within 10 hours?")
    intern_asks_questions = models.BooleanField(verbose_name="Does the intern ask you (or a co-mentor) questions when stuck for more than 1 to 3 hours?")
    mentor_support_when_stuck = models.BooleanField(verbose_name="Do you (or a co-mentor) offer more support if the intern is stuck?")

    # 2. Intern and mentor meetings
    meets_privately = models.BooleanField(verbose_name="Do you (or a co-mentor) meet privately with the intern?")
    meets_over_phone_or_video_chat = models.BooleanField(verbose_name="Do you (or a co-mentor) meet with the intern over phone or video chat?")
    intern_missed_meetings = models.BooleanField(verbose_name="Has the intern recently missed more than 2 meetings?")

    # 3. Project progress
    talk_about_project_progress = models.BooleanField(verbose_name="Does the intern and you (or a co-mentor) talk about project progress at least 3 days a week?")
    blog_created = models.BooleanField(verbose_name="Has the intern created a blog?")

    progress_report = models.TextField(verbose_name="Please provide a paragraph describing your intern's progress on establishing communication with you, connecting to your FOSS community, and ramping up on their first tasks. This will only be shown to Outreachy organizers, your community coordinators, and the Software Freedom Conservancy accounting staff.")

    # This data is set in clean() to be used for intern payment authorization JSON export
    payment_approved = models.BooleanField(verbose_name="Should your Outreachy intern be paid the initial $1,000 payment?", help_text="Please base your answer on whether your intern has put in a full-time, 40 hours a week effort. They should have established communication with you and other mentors, and have started learning how to tackle their first tasks. If you are going to ask for an internship extension, please say no to this question.")

    # This data is set in clean() to be used for intern payment authorization JSON export
    extension_date = models.DateField(help_text="If you want to extend the internship, please pick a date when you will be asked to update your intern's initial feedback and authorize payment. Internships can be extended for up to five weeks. We don't recommend extending an internship for more than 1 week at initial feedback. Please leave this field blank if you are not asking for an extension.", blank=True, null=True)

    ACTION_CHOICES = (
        (BaseMentorFeedback.PAY_AND_CONTINUE, 'Pay the initial intern stipend'),
        (BaseMentorFeedback.EXT_1_WEEK, 'Delay payment - extend the internship 1 week total'),
        (BaseMentorFeedback.EXT_2_WEEK, 'Delay payment - extend the internship 2 weeks total'),
        (BaseMentorFeedback.EXT_3_WEEK, 'Delay payment - extend the internship 3 weeks total'),
        (BaseMentorFeedback.EXT_4_WEEK, 'Delay payment - extend the internship 4 weeks total'),
        (BaseMentorFeedback.EXT_5_WEEK, 'Delay payment - extend the internship 5 weeks total'),
        (BaseMentorFeedback.TERMINATE_PAY, 'Terminate the internship contract, and pay the initial intern stipend'),
        (BaseMentorFeedback.TERMINATE_NO_PAY, 'Terminate the internship contract, and do NOT pay the initial intern stipend'),
        (BaseMentorFeedback.DONT_KNOW, "I don't know what action to recommend, please advise"),
    )
    actions_requested = models.CharField(max_length=9, choices=ACTION_CHOICES, default=BaseMentorFeedback.PAY_AND_CONTINUE, verbose_name="What actions are you requesting Outreachy organizers to take, based on your feedback?")

    def can_edit(self):
        if not self.allow_edits:
            return False

        # XXX: I guess we open the feedback form at 4pm UTC?
        if self.intern_selection.initial_feedback_opens.has_passed():
            return True
        return False

    def clean(self):
        # Note - we'd like to be able to check that mentors didn't ask
        # didn't ask to decrease the internship extension.
        # E.g. The intern had a 2 week total extension,
        # and the mentor chose the option for a 1 week total extension.
        # However, if we do that, Outreachy organizers
        # cannot change the internship dates through the Django admin interface.

        # Set historic fields used for JSON export of internship payment authorization
        self.set_payment_for_json_export()
        self.set_termination_request_for_json_export()
        requested_extension = self.set_and_return_extension_for_json_export()
        if requested_extension > 0:
            self.extension_date = self.intern_selection.round().initialfeedback + datetime.timedelta(weeks=requested_extension)

class BaseInternFeedback(BaseFeedback):
    last_contact = models.DateField(verbose_name="What was the last date you were in contact with your mentor?")

    HOURS_5 = '5H'
    HOURS_10 = '10H'
    HOURS_15 = '15H'
    HOURS_20 = '20H'
    HOURS_25 = '25H'
    HOURS_30 = '30H'
    HOURS_35 = '35H'
    HOURS_40 = '40H'
    HOURS_45 = '45H'
    HOURS_50 = '50H'
    HOURS_55 = '55H'
    HOURS_60 = '60H'
    WORK_HOURS_CHOICES = (
        (HOURS_5, '5 hours'),
        (HOURS_10, '10 hours'),
        (HOURS_15, '15 hours'),
        (HOURS_20, '20 hours'),
        (HOURS_25, '25 hours'),
        (HOURS_30, '30 hours'),
        (HOURS_35, '35 hours'),
        (HOURS_40, '40 hours'),
        (HOURS_45, '45 hours'),
        (HOURS_50, '50 hours'),
        (HOURS_55, '55 hours'),
        (HOURS_60, '60 hours'),
    )
    hours_worked = models.CharField(max_length=3, choices=WORK_HOURS_CHOICES, verbose_name="What is the average number of hours per week you spend on your Outreachy internship?", help_text="Include time you spend researching questions, communicating with your mentor and the community, reading about the project and the community, working on skills you need in order to complete your tasks, and working on the tasks themselves. Please be honest about the number of hours you are putting in.")

    # Note: the "expected" number of hours per week shifted from
    # 40 to 30 hours per week (as of the December 2021 cohort).
    # In order to future proof similar changes, we override the help text
    # in the intern feedback form templates:
    # home/templates/home/feedback{1-4}fromintern_form.html
    time_comments = models.TextField(
            max_length=THREE_PARAGRAPH_LENGTH,
            blank=True,
            help_text="(Optional) If you have not been working 40 hours a week, please let us know why. We want to support you, so let us know if there's anything we can do to help.")

    mentor_support = models.TextField(verbose_name="Please provide a paragraph describing how your mentor has (or has not) been helping you. This information will only be seen by Outreachy mentors. We want you to be honest with us if you are having trouble with your mentor, so we can help you get a better internship experience.")
    share_mentor_feedback_with_community_coordinator = models.BooleanField(default=False, verbose_name="(Optional) Do you want us to share feedback about your mentor with community coordinators?", help_text="If you say yes, community coordinators will be able to see your comments and the data you provided about your mentor. This helps coordinators ensure mentors are responsive, coach mentors if they are not responsive, and collect metrics they can use to fund more Outreachy internships.")

    def find_version_intern_edited(self):
        # When a staff member modifies the initial feedback to approve payment or change internship dates,
        # it counts as a revision. Look for the latest feedback from the intern.
        versions = Version.objects.get_for_object(self)
        for v in versions:
            if self.intern_selection.applicant.applicant.account == v.revision.user:
                return v
        return None

    def get_submission_date(self):
        version = self.find_version_intern_edited()
        if version:
            return version.revision.date_created

    class Meta:
        abstract = True

class Feedback1FromIntern(BaseInternFeedback):
    # XXX - Make sure to change the questions in
    # home/templates/home/email/initial-feedback-instructions.txt
    # if you change these verbose names.

    # 1. Clearing up doubts
    mentor_answers_questions = models.BooleanField(verbose_name="Do your mentor(s) answer your questions within 10 hours?")
    intern_asks_questions = models.BooleanField(verbose_name="Do you ask your mentor(s) questions when stuck for more than 1 to 3 hours?")
    mentor_support_when_stuck = models.BooleanField(verbose_name="Do your mentor(s) offer more support if you are stuck?")

    # 2. Intern and mentor meetings
    meets_privately = models.BooleanField(verbose_name="Do your mentor(s) meet privately with you?")
    meets_over_phone_or_video_chat = models.BooleanField(verbose_name="Do your mentor(s) meet with you over phone or video chat?")
    intern_missed_meetings = models.BooleanField(verbose_name="Have you recently missed more than 2 meetings with your mentor(s)?")

    # 3. Project progress
    talk_about_project_progress = models.BooleanField(verbose_name="Do you and your mentor(s) talk about project progress at least 3 days a week?")
    blog_created = models.BooleanField(verbose_name="Have you created a blog?")

    progress_report = models.TextField(verbose_name="Please provide a paragraph describing your progress on establishing communication with your mentor, and ramping up on your first tasks. This information will only be seen by Outreachy organizers. If you are having any difficulties or facing any barriers, please let us know, so we can help you.")

    def can_edit(self):
        if not self.allow_edits:
            return False

        if self.intern_selection.initial_feedback_opens.has_passed():
            return True
        return False

class Feedback2FromMentor(BaseMentorFeedback):
    # XXX - Make sure to change the questions in
    # home/templates/home/email/midpoint-feedback-instructions.txt
    # home/templates/home/feedback2frommentor_form.html
    # if you change these verbose names.

    # 1. Clearing up doubts
    mentor_answers_questions = models.BooleanField(verbose_name="Do you (or a co-mentor) answer the intern's questions within 10 hours?")
    intern_asks_questions = models.BooleanField(verbose_name="Does the intern ask you (or a co-mentor) questions when stuck for more than 1 to 3 hours?")
    mentor_support_when_stuck = models.BooleanField(verbose_name="Do you (or a co-mentor) offer more support if the intern is stuck?")

    # 2. Meetings
    daily_stand_ups = models.BooleanField(verbose_name="Do you (or a co-mentor) have daily stand ups with the intern?")
    meets_privately = models.BooleanField(verbose_name="Do you (or a co-mentor) meet privately with the intern?")
    meets_over_phone_or_video_chat = models.BooleanField(verbose_name="Do you (or a co-mentor) meet with the intern over phone or video chat?")
    intern_missed_meetings = models.BooleanField(verbose_name="Has the intern recently missed more than 2 meetings?")

    # 2. Tracking project progress
    talk_about_project_progress = models.BooleanField(verbose_name="Does the intern and you (or a co-mentor) talk about project progress at least 3 days a week?")

    # 4. Cycles of feedback
    contribution_drafts = models.BooleanField(verbose_name="Does the intern share work-in-progress or draft contributions with mentor(s)?")
    contribution_review = models.BooleanField(verbose_name="Do you (or a co-mentor) review intern contributions within 1 to 3 days?")
    contribution_revised = models.BooleanField(verbose_name="Has your intern revised their contribution(s) based on feedback?")
        
    # 3. Acknowledgment and praise
    mentor_shares_positive_feedback = models.BooleanField(verbose_name="Do you (or a co-mentor) give your intern praise and positive feedback?")
    mentor_promoting_work_to_community = models.BooleanField(verbose_name="Do you (or a co-mentor) promote your intern's contributions within your open source community?")
    mentor_promoting_work_on_social_media = models.BooleanField(verbose_name="Do you (or a co-mentor) promote your intern's contributions on social media?")

    # 3/6. Blogging
    intern_blogging = models.BooleanField(verbose_name="Has the intern been creating blog posts?")
    mentor_discussing_blog = models.BooleanField(verbose_name="Do you (or a co-mentor) discuss your intern's blog posts with them?")
    mentor_promoting_blog_to_community = models.BooleanField(verbose_name="Do you (or a co-mentor) promote your intern's blog posts to your open source community?")
    mentor_promoting_blog_on_social_media = models.BooleanField(verbose_name="Do you (or a co-mentor) promote your intern's blog posts on social media?")

    # 6. Networking opportunities
    mentor_introduced_intern_to_community = models.BooleanField(verbose_name="Did you (or a co-mentor) introduce your intern to your open source community?")
    intern_asks_questions_of_community_members = models.BooleanField(verbose_name="Does your intern seek help from open source community members who are not their mentors?")
    intern_talks_to_community_members = models.BooleanField(verbose_name="Does your intern have casual conversations with open source community members who are not their mentors?")

    progress_report = models.TextField(verbose_name="Please provide a paragraph describing your intern's communication frequency with you, the intern's progress on their project, and the intern's interactions with your open source community. This will only be shown to Outreachy organizers, your community coordinators, and the Software Freedom Conservancy accounting staff.")

    # This data is set in clean() to be used for intern payment authorization JSON export
    payment_approved = models.BooleanField(verbose_name="Should your Outreachy intern be paid the initial $1,000 payment?", help_text="Please base your answer on whether your intern has put in a full-time, 40 hours a week effort. They should have established communication with you and other mentors, and have started learning how to tackle their first tasks. If you are going to ask for an internship extension, please say no to this question.")

    # This data is set in clean() to be used for intern payment authorization JSON export
    extension_date = models.DateField(help_text="If you want to extend the internship, please pick a date when you will be asked to update your intern's initial feedback and authorize payment. Internships can be extended for up to five weeks. We don't recommend extending an internship for more than 1 week at initial feedback. Please leave this field blank if you are not asking for an extension.", blank=True, null=True)

    ACTION_CHOICES = (
        (BaseMentorFeedback.PAY_AND_CONTINUE, 'Continue the internship without an extension'),
        (BaseMentorFeedback.EXT_1_WEEK, 'Extend the internship 1 week total'),
        (BaseMentorFeedback.EXT_2_WEEK, 'Extend the internship 2 weeks total'),
        (BaseMentorFeedback.EXT_3_WEEK, 'Extend the internship 3 weeks total'),
        (BaseMentorFeedback.EXT_4_WEEK, 'Extend the internship 4 weeks total'),
        (BaseMentorFeedback.EXT_5_WEEK, 'Extend the internship 5 weeks total'),
        (BaseMentorFeedback.TERMINATE_NO_PAY, 'Terminate the internship contract, and do NOT pay the final intern stipend'),
        (BaseMentorFeedback.DONT_KNOW, "I don't know what action to recommend, please advise"),
    )
    actions_requested = models.CharField(max_length=9, choices=ACTION_CHOICES, default=BaseMentorFeedback.PAY_AND_CONTINUE, verbose_name="What actions are you requesting Outreachy organizers to take, based on your feedback?")

    def can_edit(self):
        if not self.allow_edits:
            return False

        if self.intern_selection.midpoint_feedback_opens.has_passed():
            return True
        return False

    def clean(self):
        # Note - we'd like to be able to check that mentors didn't ask
        # didn't ask to decrease the internship extension.
        # E.g. The intern had a 2 week total extension,
        # and the mentor chose the option for a 1 week total extension.
        # However, if we do that, Outreachy organizers
        # cannot change the internship dates through the Django admin interface.

        # Set historic fields used for JSON export of internship payment authorization
        self.set_payment_for_json_export()
        self.set_termination_request_for_json_export()
        requested_extension = self.set_and_return_extension_for_json_export()
        if requested_extension > 0:
            self.extension_date = self.intern_selection.round().midfeedback + datetime.timedelta(weeks=requested_extension)

class Feedback2FromIntern(BaseInternFeedback):
    # XXX - Make sure to change the questions in
    # home/templates/home/email/midpoint-feedback-instructions.txt
    # home/templates/home/feedback2fromintern_form.html
    # if you change these verbose names.

    # 1. Clearing up doubts
    mentor_answers_questions = models.BooleanField(verbose_name="Do your mentor(s) answer your questions within 10 hours?")
    intern_asks_questions = models.BooleanField(verbose_name="Do you ask your mentor(s) questions when stuck for more than 1 to 3 hours?")
    mentor_support_when_stuck = models.BooleanField(verbose_name="Do your mentor(s) offer more support if you are stuck?")

    # 2. Tracking project progress
    daily_stand_ups = models.BooleanField(verbose_name="Do you and your mentor(s) have daily stand ups?")
    meets_privately = models.BooleanField(verbose_name="Do you and your mentor(s) meet privately?")
    meets_over_phone_or_video_chat = models.BooleanField(verbose_name="Do you and your mentor(s) meet over phone or video chat?")
    intern_missed_meetings = models.BooleanField(verbose_name="Have you recently missed more than 2 meetings?")
    talk_about_project_progress = models.BooleanField(verbose_name="Do you and your mentor(s) talk about project progress at least 3 days a week?")

    # 4. Cycles of feedback
    contribution_drafts = models.BooleanField(verbose_name="Do you share work-in-progress or draft contributions with your mentor(s)?")
    contribution_review = models.BooleanField(verbose_name="Do your mentor(s) review your contributions within 1 to 3 days?")
    contribution_revised = models.BooleanField(verbose_name="Do you revise your contribution(s) based on mentor feedback?")
        
    # 3. Acknowledgment and praise
    mentor_shares_positive_feedback = models.BooleanField(verbose_name="Do your mentor(s) give you positive feedback and praise?")
    mentor_promoting_work_to_community = models.BooleanField(verbose_name="Do your mentor(s) promote your contributions within your open source community?")
    mentor_promoting_work_on_social_media = models.BooleanField(verbose_name="Do your mentor(s) promote your contributions on social media?")

    # 3/6. Blogging
    intern_blogging = models.BooleanField(verbose_name="Have you been creating blog posts?")
    mentor_discussing_blog = models.BooleanField(verbose_name="Do your mentor(s) discuss your blog posts with you?")
    mentor_promoting_blog_to_community = models.BooleanField(verbose_name="Do your mentor(s) promote your blog posts to your open source community?")
    mentor_promoting_blog_on_social_media = models.BooleanField(verbose_name="Do your mentor(s) promote your blog posts on social media?")

    # 6. Creating networking opportunities
    mentor_introduced_intern_to_community = models.BooleanField(verbose_name="Did your mentor(s) introduce you to your open source community?")
    intern_asks_questions_of_community_members = models.BooleanField(verbose_name="Do you seek help from open source community members who are not your mentors?")
    intern_talks_to_community_members = models.BooleanField(verbose_name="Do you have casual conversations with open source community members who are not your mentors?")

    progress_report = models.TextField(verbose_name="Please provide a paragraph describing your communication frequency with your mentor(s), your progress on your project, and your interactions with your open source community. This will only be shown to Outreachy organizers and the Software Freedom Conservancy accounting staff.")

    def can_edit(self):
        if not self.allow_edits:
            return False

        if self.intern_selection.midpoint_feedback_opens.has_passed():
            return True
        return False

class Feedback3FromMentor(BaseMentorFeedback):
    # XXX - Make sure to change the questions in
    # home/templates/home/email/feedback-3-instructions.txt
    # home/templates/home/feedback3frommentor_form.html
    # if you change these verbose names.

    # 1. Clearing up doubts
    mentor_answers_questions = models.BooleanField(verbose_name="Do you (or a co-mentor) answer the intern's questions within 10 hours?")
    intern_asks_questions = models.BooleanField(verbose_name="Does the intern ask you (or a co-mentor) questions when stuck for more than 1 to 3 hours?")
    mentor_support_when_stuck = models.BooleanField(verbose_name="Do you (or a co-mentor) offer more support if the intern is stuck?")

    # 2. Meetings
    daily_stand_ups = models.BooleanField(verbose_name="Do you (or a co-mentor) have daily stand ups with the intern?")
    meets_privately = models.BooleanField(verbose_name="Do you (or a co-mentor) meet privately with the intern?")
    meets_over_phone_or_video_chat = models.BooleanField(verbose_name="Do you (or a co-mentor) meet with the intern over phone or video chat?")
    intern_missed_meetings = models.BooleanField(verbose_name="Has the intern recently missed more than 2 meetings?")

    # 2. Tracking project progress
    talk_about_project_progress = models.BooleanField(verbose_name="Does the intern and you (or a co-mentor) talk about project progress at least 3 days a week?")
    reviewed_original_timeline = models.BooleanField(verbose_name="Has the intern and you (or a co-mentor) reviewed the original project timeline?")

    # 4. Cycles of feedback
    contribution_drafts = models.BooleanField(verbose_name="Does the intern share work-in-progress or draft contributions with mentor(s)?")
    contribution_review = models.BooleanField(verbose_name="Do you (or a co-mentor) review intern contributions within 1 to 3 days?")
    contribution_revised = models.BooleanField(verbose_name="Has your intern revised their contribution(s) based on feedback?")
        
    # 3. Acknowledgment and praise
    mentor_shares_positive_feedback = models.BooleanField(verbose_name="Do you (or a co-mentor) give your intern praise and positive feedback?")
    mentor_promoting_work_to_community = models.BooleanField(verbose_name="Do you (or a co-mentor) promote your intern's contributions within your open source community?")
    mentor_promoting_work_on_social_media = models.BooleanField(verbose_name="Do you (or a co-mentor) promote your intern's contributions on social media?")

    # 3/6. Blogging
    intern_blogging = models.BooleanField(verbose_name="Has the intern been creating blog posts?")
    mentor_discussing_blog = models.BooleanField(verbose_name="Do you (or a co-mentor) discuss your intern's blog posts with them?")
    mentor_promoting_blog_to_community = models.BooleanField(verbose_name="Do you (or a co-mentor) promote your intern's blog posts to your open source community?")
    mentor_promoting_blog_on_social_media = models.BooleanField(verbose_name="Do you (or a co-mentor) promote your intern's blog posts on social media?")

    # 6. Networking opportunities
    mentor_introduced_intern_to_community = models.BooleanField(verbose_name="Did you (or a co-mentor) introduce your intern to your open source community?")
    intern_asks_questions_of_community_members = models.BooleanField(verbose_name="Does your intern seek help from open source community members who are not their mentors?")
    intern_talks_to_community_members = models.BooleanField(verbose_name="Does your intern have casual conversations with open source community members who are not their mentors?")

    progress_report = models.TextField(verbose_name="Please provide a paragraph describing your intern's communication frequency with you, the intern's progress on their project, and the intern's interactions with your open source community. This will only be shown to Outreachy organizers, your community coordinators, and the Software Freedom Conservancy accounting staff.")

    # This data is set in clean() to be used for intern payment authorization JSON export
    payment_approved = models.BooleanField(verbose_name="Should your Outreachy intern be paid the initial $1,000 payment?", help_text="Please base your answer on whether your intern has put in a full-time, 40 hours a week effort. They should have established communication with you and other mentors, and have started learning how to tackle their first tasks. If you are going to ask for an internship extension, please say no to this question.")

    # This data is set in clean() to be used for intern payment authorization JSON export
    extension_date = models.DateField(help_text="If you want to extend the internship, please pick a date when you will be asked to update your intern's initial feedback and authorize payment. Internships can be extended for up to five weeks. We don't recommend extending an internship for more than 1 week at initial feedback. Please leave this field blank if you are not asking for an extension.", blank=True, null=True)

    ACTION_CHOICES = (
        (BaseMentorFeedback.PAY_AND_CONTINUE, 'Pay the final intern stipend'),
        (BaseMentorFeedback.EXT_1_WEEK, 'Extend the internship 1 week total'),
        (BaseMentorFeedback.EXT_2_WEEK, 'Extend the internship 2 weeks total'),
        (BaseMentorFeedback.EXT_3_WEEK, 'Extend the internship 3 weeks total'),
        (BaseMentorFeedback.EXT_4_WEEK, 'Extend the internship 4 weeks total'),
        (BaseMentorFeedback.EXT_5_WEEK, 'Extend the internship 5 weeks total'),
        (BaseMentorFeedback.TERMINATE_PAY, 'Terminate the internship contract, and pay the final intern stipend'),
        (BaseMentorFeedback.TERMINATE_NO_PAY, 'Terminate the internship contract, and do NOT pay the final intern stipend'),
        (BaseMentorFeedback.DONT_KNOW, "I don't know what action to recommend, please advise"),
    )
    actions_requested = models.CharField(max_length=9, choices=ACTION_CHOICES, default=BaseMentorFeedback.PAY_AND_CONTINUE, verbose_name="What actions are you requesting Outreachy organizers to take, based on your feedback?")

    def can_edit(self):
        if not self.allow_edits:
            return False

        if self.intern_selection.midpoint_feedback_opens.has_passed():
            return True
        return False

    def clean(self):
        # Note - we'd like to be able to check that mentors didn't ask
        # didn't ask to decrease the internship extension.
        # E.g. The intern had a 2 week total extension,
        # and the mentor chose the option for a 1 week total extension.
        # However, if we do that, Outreachy organizers
        # cannot change the internship dates through the Django admin interface.

        # Set historic fields used for JSON export of internship payment authorization
        self.set_payment_for_json_export()
        self.set_termination_request_for_json_export()
        requested_extension = self.set_and_return_extension_for_json_export()
        if requested_extension > 0:
            self.extension_date = self.intern_selection.round().feedback3_due + datetime.timedelta(weeks=requested_extension)

class Feedback3FromIntern(BaseInternFeedback):
    # XXX - Make sure to change the questions in
    # home/templates/home/email/midpoint-feedback-instructions.txt
    # home/templates/home/feedback2fromintern_form.html
    # if you change these verbose names.

    # 1. Clearing up doubts
    mentor_answers_questions = models.BooleanField(verbose_name="Do your mentor(s) answer your questions within 10 hours?")
    intern_asks_questions = models.BooleanField(verbose_name="Do you ask your mentor(s) questions when stuck for more than 1 to 3 hours?")
    mentor_support_when_stuck = models.BooleanField(verbose_name="Do your mentor(s) offer more support if you are stuck?")

    # 2. Tracking project progress
    daily_stand_ups = models.BooleanField(verbose_name="Do you and your mentor(s) have daily stand ups?")
    meets_privately = models.BooleanField(verbose_name="Do you and your mentor(s) meet privately?")
    meets_over_phone_or_video_chat = models.BooleanField(verbose_name="Do you and your mentor(s) meet over phone or video chat?")
    intern_missed_meetings = models.BooleanField(verbose_name="Have you recently missed more than 2 meetings?")
    talk_about_project_progress = models.BooleanField(verbose_name="Do you and your mentor(s) talk about project progress at least 3 days a week?")
    reviewed_original_timeline = models.BooleanField(verbose_name="Have you and your mentor(s) reviewed the original project timeline?")

    # 4. Cycles of feedback
    contribution_drafts = models.BooleanField(verbose_name="Do you share work-in-progress or draft contributions with your mentor(s)?")
    contribution_review = models.BooleanField(verbose_name="Do your mentor(s) review your contributions within 1 to 3 days?")
    contribution_revised = models.BooleanField(verbose_name="Do you revise your contribution(s) based on mentor feedback?")
        
    # 3. Acknowledgment and praise
    mentor_shares_positive_feedback = models.BooleanField(verbose_name="Do your mentor(s) give you positive feedback and praise?")
    mentor_promoting_work_to_community = models.BooleanField(verbose_name="Do your mentor(s) promote your contributions within your open source community?")
    mentor_promoting_work_on_social_media = models.BooleanField(verbose_name="Do your mentor(s) promote your contributions on social media?")

    # 3/6. Blogging
    intern_blogging = models.BooleanField(verbose_name="Have you been creating blog posts?")
    mentor_discussing_blog = models.BooleanField(verbose_name="Do your mentor(s) discuss your blog posts with you?")
    mentor_promoting_blog_to_community = models.BooleanField(verbose_name="Do your mentor(s) promote your blog posts to your open source community?")
    mentor_promoting_blog_on_social_media = models.BooleanField(verbose_name="Do your mentor(s) promote your blog posts on social media?")

    # 6. Creating networking opportunities
    mentor_introduced_intern_to_community = models.BooleanField(verbose_name="Did your mentor(s) introduce you to your open source community?")
    intern_asks_questions_of_community_members = models.BooleanField(verbose_name="Do you seek help from open source community members who are not your mentors?")
    intern_talks_to_community_members = models.BooleanField(verbose_name="Do you have casual conversations with open source community members who are not your mentors?")

    progress_report = models.TextField(verbose_name="Please provide a paragraph describing your communication frequency with your mentor(s), your progress on your project, and your interactions with your open source community. This will only be shown to Outreachy organizers and the Software Freedom Conservancy accounting staff.")

    def can_edit(self):
        if not self.allow_edits:
            return False

        if self.intern_selection.midpoint_feedback_opens.has_passed():
            return True
        return False

class Feedback4FromMentor(BaseMentorFeedback):
    # XXX - Make sure to change the questions in
    # home/templates/home/email/feedback4-instructions.txt
    # home/templates/home/feedback4frommentor_form.html
    # if you change these verbose names.

    # 1. Clearing up doubts
    mentor_answers_questions = models.BooleanField(verbose_name="Do you (or a co-mentor) answer the intern's questions within 10 hours?")
    intern_asks_questions = models.BooleanField(verbose_name="Does the intern ask you (or a co-mentor) questions when stuck for more than 1 to 3 hours?")
    mentor_support_when_stuck = models.BooleanField(verbose_name="Do you (or a co-mentor) offer more support if the intern is stuck?")

    # 2. Meetings
    daily_stand_ups = models.BooleanField(verbose_name="Do you (or a co-mentor) have daily stand ups with the intern?")
    meets_privately = models.BooleanField(verbose_name="Do you (or a co-mentor) meet privately with the intern?")
    meets_over_phone_or_video_chat = models.BooleanField(verbose_name="Do you (or a co-mentor) meet with the intern over phone or video chat?")
    intern_missed_meetings = models.BooleanField(verbose_name="Has the intern recently missed more than 2 meetings?")

    # 2. Tracking project progress
    talk_about_project_progress = models.BooleanField(verbose_name="Does the intern and you (or a co-mentor) talk about project progress at least 3 days a week?")
    reviewed_original_timeline = models.BooleanField(verbose_name="Has the intern and you (or a co-mentor) reviewed the original project timeline?")

    # 4. Cycles of feedback
    contribution_drafts = models.BooleanField(verbose_name="Does the intern share work-in-progress or draft contributions with mentor(s)?")
    contribution_review = models.BooleanField(verbose_name="Do you (or a co-mentor) review intern contributions within 1 to 3 days?")
    contribution_revised = models.BooleanField(verbose_name="Has your intern revised their contribution(s) based on feedback?")
        
    # 3. Acknowledgment and praise
    mentor_shares_positive_feedback = models.BooleanField(verbose_name="Do you (or a co-mentor) give your intern praise and positive feedback?")
    mentor_promoting_work_to_community = models.BooleanField(verbose_name="Do you (or a co-mentor) promote your intern's contributions within your open source community?")
    mentor_promoting_work_on_social_media = models.BooleanField(verbose_name="Do you (or a co-mentor) promote your intern's contributions on social media?")

    # 3/6. Blogging
    intern_blogging = models.BooleanField(verbose_name="Has the intern been creating blog posts?")
    mentor_discussing_blog = models.BooleanField(verbose_name="Do you (or a co-mentor) discuss your intern's blog posts with them?")
    mentor_promoting_blog_to_community = models.BooleanField(verbose_name="Do you (or a co-mentor) promote your intern's blog posts to your open source community?")
    mentor_promoting_blog_on_social_media = models.BooleanField(verbose_name="Do you (or a co-mentor) promote your intern's blog posts on social media?")

    # 6. Networking opportunities
    mentor_introduced_intern_to_community = models.BooleanField(verbose_name="Did you (or a co-mentor) introduce your intern to your open source community?")
    intern_asks_questions_of_community_members = models.BooleanField(verbose_name="Does your intern seek help from open source community members who are not their mentors?")
    intern_talks_to_community_members = models.BooleanField(verbose_name="Does your intern have casual conversations with open source community members who are not their mentors?")
    mentor_introduced_to_informal_chat_contacts = models.BooleanField(verbose_name="Did you (or a co-mentor) suggest people your intern could talk to for informal career chats?")
    intern_had_informal_chats = models.BooleanField(verbose_name="Has your intern had any informal career chats?")

    progress_report = models.TextField(verbose_name="Please provide a paragraph describing your intern's communication frequency with you, the intern's progress on their project, and the intern's interactions with your open source community. This will only be shown to Outreachy organizers, your community coordinators, and the Software Freedom Conservancy accounting staff.")

    # This data is set in clean() to be used for intern payment authorization JSON export
    payment_approved = models.BooleanField(verbose_name="Should your Outreachy intern be paid the initial $1,000 payment?", help_text="Please base your answer on whether your intern has put in a full-time, 40 hours a week effort. They should have established communication with you and other mentors, and have started learning how to tackle their first tasks. If you are going to ask for an internship extension, please say no to this question.")

    # This data is set in clean() to be used for intern payment authorization JSON export
    extension_date = models.DateField(help_text="If you want to extend the internship, please pick a date when you will be asked to update your intern's initial feedback and authorize payment. Internships can be extended for up to five weeks. We don't recommend extending an internship for more than 1 week at initial feedback. Please leave this field blank if you are not asking for an extension.", blank=True, null=True)

    ACTION_CHOICES = (
        (BaseMentorFeedback.PAY_AND_CONTINUE, 'Mark the internship as successfully completed'),
        (BaseMentorFeedback.EXT_1_WEEK, 'Extend the internship 1 week total'),
        (BaseMentorFeedback.EXT_2_WEEK, 'Extend the internship 2 weeks total'),
        (BaseMentorFeedback.EXT_3_WEEK, 'Extend the internship 3 weeks total'),
        (BaseMentorFeedback.EXT_4_WEEK, 'Extend the internship 4 weeks total'),
        (BaseMentorFeedback.EXT_5_WEEK, 'Extend the internship 5 weeks total'),
        (BaseMentorFeedback.TERMINATE_PAY, 'Mark the internship as unsuccessful and remove the intern from the Outreachy alums list'),
        (BaseMentorFeedback.DONT_KNOW, "I don't know what action to recommend, please advise"),
    )
    actions_requested = models.CharField(max_length=9, choices=ACTION_CHOICES, default=BaseMentorFeedback.PAY_AND_CONTINUE, verbose_name="What actions are you requesting Outreachy organizers to take, based on your feedback?")

    NETPROMOTER_SCORE = (
            ('X', 'Prefer not to say'),
            ('0', '0 - not at all likely'),
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6'),
            ('7', '7'),
            ('8', '8'),
            ('9', '9'),
            ('10', '10 - extremely likely'),
    )
    recommend_mentoring = models.CharField(max_length=2, choices=NETPROMOTER_SCORE, default='X', verbose_name="How likely would you be to recommend a friend or colleague mentor for Outreachy?")

    mentoring_positive_impacts = models.TextField(verbose_name="How has being an Outreachy mentor positively impacted you?", blank=True, null=True, max_length=PARAGRAPH_LENGTH)

    mentoring_improvement_suggestions = models.TextField(verbose_name="How could the mentorship experience be improved?", blank=True, null=True, max_length=PARAGRAPH_LENGTH)

    new_mentor_suggestions = models.TextField(verbose_name="What advice would you give to a new Outreachy mentor?", blank=True, null=True, max_length=PARAGRAPH_LENGTH)

    community_positive_impacts = models.TextField(verbose_name="How has this internship positively impacted your open source or open science community?", blank=True, null=True, max_length=PARAGRAPH_LENGTH)

    community_improvement_suggestions = models.TextField(verbose_name="How could the experience for open source or open science communities be improved?", blank=True, null=True, max_length=PARAGRAPH_LENGTH)

    additional_feedback = models.TextField(verbose_name="Please provide any additional feedback for Outreachy organizers", blank=True, null=True, max_length=PARAGRAPH_LENGTH)

    def can_edit(self):
        if not self.allow_edits:
            return False

        if self.intern_selection.midpoint_feedback_opens.has_passed():
            return True
        return False

    def clean(self):
        # Note - we'd like to be able to check that mentors didn't ask
        # didn't ask to decrease the internship extension.
        # E.g. The intern had a 2 week total extension,
        # and the mentor chose the option for a 1 week total extension.
        # However, if we do that, Outreachy organizers
        # cannot change the internship dates through the Django admin interface.

        # Set historic fields used for JSON export of internship payment authorization
        self.set_payment_for_json_export()
        self.set_termination_request_for_json_export()
        requested_extension = self.set_and_return_extension_for_json_export()
        if requested_extension > 0:
            self.extension_date = self.intern_selection.round().finalfeedback + datetime.timedelta(weeks=requested_extension)

class Feedback4FromIntern(BaseInternFeedback):
    # XXX - Make sure to change the questions in
    # home/templates/home/email/midpoint-feedback-instructions.txt
    # home/templates/home/feedback2fromintern_form.html
    # if you change these verbose names.

    # 1. Clearing up doubts
    mentor_answers_questions = models.BooleanField(verbose_name="Do your mentor(s) answer your questions within 10 hours?")
    intern_asks_questions = models.BooleanField(verbose_name="Do you ask your mentor(s) questions when stuck for more than 1 to 3 hours?")
    mentor_support_when_stuck = models.BooleanField(verbose_name="Do your mentor(s) offer more support if you are stuck?")

    # 2. Tracking project progress
    daily_stand_ups = models.BooleanField(verbose_name="Do you and your mentor(s) have daily stand ups?")
    meets_privately = models.BooleanField(verbose_name="Do you and your mentor(s) meet privately?")
    meets_over_phone_or_video_chat = models.BooleanField(verbose_name="Do you and your mentor(s) meet over phone or video chat?")
    intern_missed_meetings = models.BooleanField(verbose_name="Have you recently missed more than 2 meetings?")
    talk_about_project_progress = models.BooleanField(verbose_name="Do you and your mentor(s) talk about project progress at least 3 days a week?")
    reviewed_original_timeline = models.BooleanField(verbose_name="Have you and your mentor(s) reviewed the original project timeline?")

    # 4. Cycles of feedback
    contribution_drafts = models.BooleanField(verbose_name="Do you share work-in-progress or draft contributions with your mentor(s)?")
    contribution_review = models.BooleanField(verbose_name="Do your mentor(s) review your contributions within 1 to 3 days?")
    contribution_revised = models.BooleanField(verbose_name="Do you revise your contribution(s) based on mentor feedback?")
        
    # 3. Acknowledgment and praise
    mentor_shares_positive_feedback = models.BooleanField(verbose_name="Do your mentor(s) give you positive feedback and praise?")
    mentor_promoting_work_to_community = models.BooleanField(verbose_name="Do your mentor(s) promote your contributions within your open source community?")
    mentor_promoting_work_on_social_media = models.BooleanField(verbose_name="Do your mentor(s) promote your contributions on social media?")

    # 3/6. Blogging
    intern_blogging = models.BooleanField(verbose_name="Have you been creating blog posts?")
    mentor_discussing_blog = models.BooleanField(verbose_name="Do your mentor(s) discuss your blog posts with you?")
    mentor_promoting_blog_to_community = models.BooleanField(verbose_name="Do your mentor(s) promote your blog posts to your open source community?")
    mentor_promoting_blog_on_social_media = models.BooleanField(verbose_name="Do your mentor(s) promote your blog posts on social media?")

    # 6. Creating networking opportunities
    mentor_introduced_intern_to_community = models.BooleanField(verbose_name="Did your mentor(s) introduce you to your open source community?")
    intern_asks_questions_of_community_members = models.BooleanField(verbose_name="Do you seek help from open source community members who are not your mentors?")
    intern_talks_to_community_members = models.BooleanField(verbose_name="Do you have casual conversations with open source community members who are not your mentors?")
    mentor_introduced_to_informal_chat_contacts = models.BooleanField(verbose_name="Did your mentors suggest people you could talk to for informal career chats?")
    intern_had_informal_chats = models.BooleanField(verbose_name="Have you had any informal career chats?")

    progress_report = models.TextField(verbose_name="Please provide a paragraph describing your communication frequency with your mentor(s), your progress on your project, and your interactions with your open source community. This will only be shown to Outreachy organizers and the Software Freedom Conservancy accounting staff.")

    NETPROMOTER_SCORE = (
            ('X', 'Prefer not to say'),
            ('0', '0 - not at all likely'),
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6'),
            ('7', '7'),
            ('8', '8'),
            ('9', '9'),
            ('10', '10 - extremely likely'),
    )
    recommend_open_source = models.CharField(max_length=2, choices=NETPROMOTER_SCORE, default='X', verbose_name="How likely would you be to recommend a friend contribute to open source?")

    recommend_interning = models.CharField(max_length=2, choices=NETPROMOTER_SCORE, default='X', verbose_name="How likely would you be to recommend a friend apply to Outreachy?")

    application_period_positive_impacts = models.TextField(verbose_name="How did the Outreachy application period positively impact you?", blank=True, null=True, max_length=PARAGRAPH_LENGTH)
    application_period_improvement_suggestions = models.TextField(verbose_name="How could the application experience be improved?", blank=True, null=True, max_length=PARAGRAPH_LENGTH)
    
    new_applicant_advice = models.TextField(verbose_name="What advice would you give to a new Outreachy applicant?", blank=True, null=True, max_length=PARAGRAPH_LENGTH)

    interning_positive_impacts = models.TextField(verbose_name="How has being an Outreachy intern positively impacted you?", blank=True, null=True, max_length=PARAGRAPH_LENGTH)

    interning_improvement_suggestions = models.TextField(verbose_name="How could the internship experience be improved?", blank=True, null=True, max_length=PARAGRAPH_LENGTH)

    community_positive_impacts = models.TextField(verbose_name="How has working with your open source or open science community positively impacted you?", blank=True, null=True, max_length=PARAGRAPH_LENGTH)

    community_improvement_suggestions = models.TextField(verbose_name="How could your experience working with your open source or open science community be improved?", blank=True, null=True, max_length=PARAGRAPH_LENGTH)

    additional_feedback = models.TextField(verbose_name="Please provide any additional feedback for Outreachy organizers", blank=True, null=True, max_length=PARAGRAPH_LENGTH)

    def can_edit(self):
        if not self.allow_edits:
            return False

        if self.intern_selection.midpoint_feedback_opens.has_passed():
            return True
        return False

class InformalChatContact(models.Model):
    '''
    Information about people that Outreachy interns can contact for informal chats.
    '''
    active = models.BooleanField(verbose_name='Are you currently available for informal chats?')
    # Not all contacts will have an account on the website
    comrade = models.ForeignKey(Comrade, blank=True, null=True, on_delete=models.SET_NULL)
    name = models.CharField(blank=True, max_length=LONG_LEGAL_NAME, help_text="Your full name, which will be publicly displayed to Outreachy interns. This is typically your given name, followed by your family name. You may use a pseudonym or abbreviate your given or family names if you have concerns about privacy.")
    email = models.EmailField(blank=True, verbose_name='Email address')
    relationship_to_outreachy = models.CharField(blank=True, max_length=PARAGRAPH_LENGTH, help_text='Which are you: a current/past Outreachy intern, current/past Outreachy mentor, current/past Outreachy coordinator, or current employee of an Outreachy sponsor?')
    foss_communities = models.CharField(blank=True, max_length=PARAGRAPH_LENGTH, verbose_name='What open source communities do you participate in?')
    company = models.CharField(blank=True, max_length=PARAGRAPH_LENGTH, verbose_name='What company do you work for?')
    paid_foss_roles = models.CharField(blank=True, max_length=PARAGRAPH_LENGTH, verbose_name='What open source roles (e.g. community manager, JavaScript programmer, Linux systems admin) are you paid to work on?')
    volunteer_foss_roles = models.CharField(blank=True, max_length=PARAGRAPH_LENGTH, verbose_name='What open source roles (e.g. community manager, JavaScript programmer, Linux systems admin) do you volunteer for?')

    def get_name(self):
        if self.name:
            return self.name
        if self.comrade:
            return self.comrade.public_name
        return 'Name unknown'

    def get_email(self):
        if self.email:
            return self.email
        if self.comrade:
            return self.comrade.account.email

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
    survey_tracker = models.ForeignKey(AlumSurveyTracker, on_delete=models.PROTECT)

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

class Role(object):
    """
    Compute the role which the current visitor most likely is interested in for
    a given round, and encapsulate that information in a single object that we
    can pass to templates.

    Sometimes this is also used to provide information to an organizer (or
    similar) about someone else. Under those circumstances, the ``requestor``
    should be set to ``request.user`` while the ``user`` argument is set to the
    subject of the inquiry. If this is not done then the requestor can only see
    whatever information the subject is permitted to see.

    This is not a Django model and does not have a database representation, but
    it's too easy to get into circular import dependencies if this class lives
    anywhere outside models.py.
    """

    def __init__(self, user, current_round, requestor=None):
        self.user = user
        self.current_round = current_round
        self.requestor = requestor or user

    # Any properties that do database queries should be cached:

    @cached_property
    def application(self):
        if self.current_round is not None and self.user.is_authenticated:
            try:
                return self.current_round.applicantapproval_set.get(
                    applicant__account=self.user,
                )
            except ApplicantApproval.DoesNotExist:
                pass
        return None

    @cached_property
    def is_coordinator(self):
        if self.current_round is not None and self.user.is_authenticated:
            return self.current_round.is_coordinator(self.user)
        return False

    @cached_property
    def is_mentor(self):
        if self.current_round is not None and self.user.is_authenticated:
            return self.current_round.is_mentor(self.user)
        return False

    @cached_property
    def is_reviewer(self):
        if self.current_round is not None and self.user.is_authenticated:
            return self.current_round.is_reviewer(self.user)
        return False

    @cached_property
    def pending_mentored_projects(self):
        # Get all projects where they're an approved mentor
        # where the project is pending,
        # and the community is approved or pending for the current round.
        # Don't count withdrawn or rejected communities.
        if self.current_round is not None and self.user.is_authenticated:
            try:
                return self.user.comrade.get_mentored_projects().pending().filter(
                    project_round__participating_round=self.current_round,
                    project_round__approval_status__in=(ApprovalStatus.PENDING, ApprovalStatus.APPROVED),
                )
            except Comrade.DoesNotExist:
                pass
        return Project.objects.none()

    @cached_property
    def approved_coordinator_communities(self):
        """
        Get all communities where this person is an approved coordinator
        and the community is approved to participate in the current round.
        """
        if self.current_round is not None and self.user.is_authenticated:
            return self.current_round.participation_set.approved().filter(
                community__coordinatorapproval__coordinator__account=self.user,
                community__coordinatorapproval__approval_status=ApprovalStatus.APPROVED,
            )
        return Community.objects.none()

    @cached_property
    def projects_contributed_to(self):
        applicant = self.application
        if applicant is None:
            return ()

        all_projects = list(applicant.get_projects_contributed_to())
        applied_projects = set(applicant.get_projects_applied_to().values_list('pk', flat=True))

        for project in all_projects:
            project.did_apply = project.pk in applied_projects

        all_projects.sort(key=lambda x: x.did_apply, reverse=True)
        return all_projects

    @cached_property
    def visible_intern_selections(self):
        if self.current_round is None:
            return InternSelection.objects.none()

        if self.is_organizer:
            return self.current_round.get_approved_intern_selections()

        if not self.current_round.internannounce.has_passed():
            return InternSelection.objects.none()

        return self.current_round.get_in_good_standing_intern_selections()

    # Anything that just uses other properties does not need to be cached:

    @property
    def is_organizer(self):
        return self.user.is_staff

    @property
    def is_applicant(self):
        return self.application is not None

    @property
    def is_volunteer(self):
        """
        Coordinators, mentors, reviewers, and organizers often are interested
        in seeing the same things, so lump them all together. "Volunteer" isn't
        necessarily the right name for this but it's good enough.
        """
        return self.is_organizer or self.is_mentor or self.is_coordinator or self.is_reviewer

    @property
    def is_potential_applicant(self):
        """
        This function checks whether a person might be a potential applicant.
        Volunteers (mentors, coordinators, and applicant reviewers) are not
        potential applicants. Someone who filled out an initial application is
        not a *potential applicant*. This does not check any dates (like if the
        initial application period is open).
        """

        if self.current_round is None:
            return False

        return not self.is_volunteer and not self.is_applicant

    @property
    def is_approved_applicant(self):
        """
        Is this application approved? Depends on who is viewing it and when.
        Organizers and reviewers can see the true status of approved applications all the time.
        Applicants get notified of acceptance after contributions open.
        If the contributions period isn't open, applicants can't see they're approved.
        """
        if not self.is_applicant:
            return False
        if self.is_organizer or self.is_reviewer:
            return self.application.is_approved()
        elif self.current_round.contributions_open.has_passed():
            return self.application.is_approved()
        return False

    @property
    def is_rejected_applicant(self):
        """
        Is this application rejected? Depends on who is viewing it and when.
        Organizers and reviewers can see the true status of rejected applications all the time.
        Otherwise applicants get notified of rejection after contributions open.
        """
        if not self.is_applicant:
            return False
        if self.is_organizer or self.is_reviewer:
            return self.is_applicant and self.application.is_rejected()
        elif self.current_round.contributions_open.has_passed():
            return self.application.is_rejected()
        return False

    @property
    def is_pending_applicant(self):
        """
        Is this application pending? Depends on who is viewing it and when.
        Organizers and reviewers can see the true status of pending applications all the time.
        If it's before the contributions open, all applicants see their application as pending until the contribution period opens.
        If it's after the contribution period opens, show whether it's really pending.
        """
        if not self.is_applicant:
            return False
        if self.is_organizer or self.is_reviewer:
            return self.application.is_pending()
        elif self.current_round.contributions_open.has_passed():
            return self.application.is_pending()
        return True

    @property
    def needs_review(self):
        if self.application is not None:
            return self.application.approval_status in (ApprovalStatus.PENDING, ApprovalStatus.REJECTED)
        return False

    @property
    def projects_not_applied_to(self):
        return [ p for p in self.projects_contributed_to if not p.did_apply ]

# --- Deprecated models ---
#
# These models are ones we historically used to collect internship feedback.
#
# Eventually the goal for these models are:
#  - Write an export function that exports all prior feedback collected
#    - CSV export is probably the easiest format for quick checks
#    - JSON export might be nice for preserving data types for data science
#    - explore Django management dumpdata command
#  - Export feedback from all cohorts that are not currently active
#  - Add a new 'inactive' Boolean to the InternSelection class
#  - Mark all interns who had their final stipend approved
#    (FinalMentorFeedback.organizer_payment_approved == True)
#    or are not in good standing
#    as inactive
#  - Manually mark all interns from the May 2018 cohort as inactive
#    - we didn't collect any feedback through the website for that cohort
#  - Stop relying on the final payment authorization data to determine if
#    an internship is inactive in the 'active internship contacts' page
#    (home/views.py - ActiveInternshipContactsView)
#    use the new 'inactive' flag instead
#  - Delete all feedback objects from the website production database
#
# --- Deprecated models ---

# There shouldn't be a need to record which mentor filled out the form.
# The revision control on the object should store which Django user made the changes.
#
# We can dig out the latest feedback version
# (assuming self references the InitialMentorFeedback object):
# from reversion.models import Version
# versions = Version.objects.get_for_object(self)
# print('On {:%Y-%m-%d at %I:%M%p} %u wrote:\n{}'.format(versions[0].revision.date_created, versions[0].revision.user))
#
# This also allows us to keep the feedback around, even if a mentor withdraws from the project.
# As long as their Django user account is intact, the feedback should remain intact.
# This is important to keep around for Conservancy record keeping.
class InitialMentorFeedback(BaseMentorFeedback):
    # XXX - Make sure to change the questions in
    # home/templates/home/email/initial-feedback-instructions.txt
    # if you change these verbose names.
    in_contact = models.BooleanField(verbose_name="Has your intern been in contact to discuss how to approach their first tasks?")
    asking_questions = models.BooleanField(verbose_name="Has your intern been asking questions about their first tasks?")
    active_in_public = models.BooleanField(verbose_name="Has your intern been active on public project channels, such as the community's chat, forums, issue tracker, mailing list, etc?")
    provided_onboarding = models.BooleanField(verbose_name="Have you provided documentation or other resources to help onboard your intern?")

    NOT_SCHEDULED = '0'
    ONCE_DAILY = 'D'
    MULTIPLE_WEEKLY = 'M'
    ONCE_WEEKLY = 'W'
    EVERY_OTHER_WEEK = 'B'
    CHECKIN_FREQUENCY_CHOICES = (
        (NOT_SCHEDULED, 'Not scheduled yet'),
        (ONCE_DAILY, 'Once per day'),
        (MULTIPLE_WEEKLY, 'Multiple times per week'),
        (ONCE_WEEKLY, 'Once per week'),
        (EVERY_OTHER_WEEK, 'Every other week'),
    )
    checkin_frequency = models.CharField(max_length=1, choices=CHECKIN_FREQUENCY_CHOICES, default=NOT_SCHEDULED, verbose_name="How often do you have a real-time chat, video conference, or phone conversation to check in with your intern's progress on tasks?")

    HOURS_1 = '1H'
    HOURS_3 = '3H'
    HOURS_6 = '6H'
    HOURS_12 = '12H'
    DAYS_1 = '1D'
    DAYS_2 = '2D'
    DAYS_4 = '4D'
    DAYS_6 = '6D'
    LONGER = '>7D'
    RESPONSE_TIME_CHOICES = (
        (HOURS_1, '1 hour'),
        (HOURS_3, '3 hours'),
        (HOURS_6, '6 hours'),
        (HOURS_12, '12 hours'),
        (DAYS_1, '1 day'),
        (DAYS_2, '2-3 days'),
        (DAYS_4, '4-5 days'),
        (DAYS_6, '6-7 days'),
        (LONGER, '> 7 days'),
    )
    intern_response_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, verbose_name="On average, how long does it take for <b>your intern</b> to respond to your questions or feedback?")
    mentor_response_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, verbose_name="On average, how long does it take for <b>you</b> to respond to your intern's questions or requests for feedback?")

    progress_report = models.TextField(verbose_name="Please provide a paragraph describing your intern's progress on establishing communication with you, connecting to your FOSS community, and ramping up on their first tasks. This will only be shown to Outreachy organizers, your community coordinators, and the Software Freedom Conservancy accounting staff.")

    # Deprecated - this data is set in clean() to be used for intern payment authorization JSON export
    payment_approved = models.BooleanField(verbose_name="Should your Outreachy intern be paid the initial $1,000 payment?", help_text="Please base your answer on whether your intern has put in a full-time, 40 hours a week effort. They should have established communication with you and other mentors, and have started learning how to tackle their first tasks. If you are going to ask for an internship extension, please say no to this question.")

    # Deprecated - this data is set in clean() to be used for intern payment authorization JSON export
    extension_date = models.DateField(help_text="If you want to extend the internship, please pick a date when you will be asked to update your intern's initial feedback and authorize payment. Internships can be extended for up to five weeks. We don't recommend extending an internship for more than 1 week at initial feedback. Please leave this field blank if you are not asking for an extension.", blank=True, null=True)

    ACTION_CHOICES = (
        (BaseMentorFeedback.PAY_AND_CONTINUE, 'Pay the initial intern stipend'),
        (BaseMentorFeedback.EXT_1_WEEK, 'Delay payment - extend the internship 1 week total'),
        (BaseMentorFeedback.EXT_2_WEEK, 'Delay payment - extend the internship 2 weeks total'),
        (BaseMentorFeedback.EXT_3_WEEK, 'Delay payment - extend the internship 3 weeks total'),
        (BaseMentorFeedback.EXT_4_WEEK, 'Delay payment - extend the internship 4 weeks total'),
        (BaseMentorFeedback.EXT_5_WEEK, 'Delay payment - extend the internship 5 weeks total'),
        (BaseMentorFeedback.TERMINATE_PAY, 'Terminate the internship contract, and pay the initial intern stipend'),
        (BaseMentorFeedback.TERMINATE_NO_PAY, 'Terminate the internship contract, and do NOT pay the initial intern stipend'),
        (BaseMentorFeedback.DONT_KNOW, "I don't know what action to recommend, please advise"),
    )
    actions_requested = models.CharField(max_length=9, choices=ACTION_CHOICES, default=BaseMentorFeedback.PAY_AND_CONTINUE, verbose_name="What actions are you requesting Outreachy organizers to take, based on your feedback?")

    def can_edit(self):
        if not self.allow_edits:
            return False

        # XXX: I guess we open the feedback form at 4pm UTC?
        if self.intern_selection.initial_feedback_opens.has_passed():
            return True
        return False

    def clean(self):
        # Note - we'd like to be able to check that mentors didn't ask
        # didn't ask to decrease the internship extension.
        # E.g. The intern had a 2 week total extension,
        # and the mentor chose the option for a 1 week total extension.
        # However, if we do that, Outreachy organizers
        # cannot change the internship dates through the Django admin interface.

        # Set historic fields used for JSON export of internship payment authorization
        self.set_payment_for_json_export()
        self.set_termination_request_for_json_export()
        requested_extension = self.set_and_return_extension_for_json_export()
        if requested_extension > 0:
            self.extension_date = self.intern_selection.round().initialfeedback + datetime.timedelta(weeks=requested_extension)

# Feedback intern submits about their mentor and their internship
class InitialInternFeedback(BaseInternFeedback):
    # XXX - Make sure to change the questions in
    # home/templates/home/email/initial-feedback-instructions.txt
    # if you change these verbose names.
    in_contact = models.BooleanField(verbose_name="Have you been in contact with your mentor to discuss how to approach your first tasks?")
    asking_questions = models.BooleanField(verbose_name="Have you been asking questions about your first tasks?")
    active_in_public = models.BooleanField(verbose_name="Have you been active on public project channels, such as the community's chat, forums, issue tracker, mailing list, etc?")
    provided_onboarding = models.BooleanField(verbose_name="Has your mentor provided documentation or other resources to help you learn more about your community and your first tasks?")

    NOT_SCHEDULED = '0'
    ONCE_DAILY = 'D'
    MULTIPLE_WEEKLY = 'M'
    ONCE_WEEKLY = 'W'
    EVERY_OTHER_WEEK = 'B'
    CHECKIN_FREQUENCY_CHOICES = (
        (NOT_SCHEDULED, 'Not scheduled yet'),
        (ONCE_DAILY, 'Once per day'),
        (MULTIPLE_WEEKLY, 'Multiple times per week'),
        (ONCE_WEEKLY, 'Once per week'),
        (EVERY_OTHER_WEEK, 'Every other week'),
    )
    checkin_frequency = models.CharField(max_length=1, choices=CHECKIN_FREQUENCY_CHOICES, default=NOT_SCHEDULED, verbose_name="How often does your mentor have a real-time chat, video conference, or phone conversation to check in with your progress on tasks?")

    HOURS_1 = '1H'
    HOURS_3 = '3H'
    HOURS_6 = '6H'
    HOURS_12 = '12H'
    DAYS_1 = '1D'
    DAYS_2 = '2D'
    DAYS_4 = '4D'
    DAYS_6 = '6D'
    LONGER = '>7D'
    RESPONSE_TIME_CHOICES = (
        (HOURS_1, '1 hour'),
        (HOURS_3, '3 hours'),
        (HOURS_6, '6 hours'),
        (HOURS_12, '12 hours'),
        (DAYS_1, '1 day'),
        (DAYS_2, '2-3 days'),
        (DAYS_4, '4-5 days'),
        (DAYS_6, '6-7 days'),
        (LONGER, '> 7 days'),
    )
    intern_response_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, verbose_name="On average, how long does it take for <b>you</b> to respond to your mentor's questions or feedback?")
    mentor_response_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, verbose_name="On average, how long does it take for <b>your mentor</b> to respond to your questions or requests for feedback?")

    progress_report = models.TextField(verbose_name="Please provide a paragraph describing your progress on establishing communication with your mentor, and ramping up on your first tasks. This information will only be seen by Outreachy organizers. If you are having any difficulties or facing any barriers, please let us know, so we can help you.")

    def can_edit(self):
        if not self.allow_edits:
            return False

        if self.intern_selection.initial_feedback_opens.has_passed():
            return True
        return False

class MidpointMentorFeedback(BaseMentorFeedback):
    '''
    This class is deprecated as of the December 2021 intern cohort.
    Please see the Feedback2FromMentor class instead.
    '''
    # XXX - Make sure to change the questions in
    # home/templates/home/email/midpoint-feedback-instructions.txt
    # if you change these verbose names.
    NEVER = '0'
    MULTIPLE_DAILY = 'U'
    ONCE_DAILY = 'D'
    MULTIPLE_WEEKLY = 'M'
    ONCE_WEEKLY = 'W'
    EVERY_OTHER_WEEK = 'B'
    ASKING_FOR_HELP_FREQUENCY_CHOICES = (
        (NEVER, 'Intern has not asked for help'),
        (MULTIPLE_DAILY, 'Multiple times per day'),
        (ONCE_DAILY, 'Once per day'),
        (MULTIPLE_WEEKLY, 'Multiple times per week'),
        (ONCE_WEEKLY, 'Once per week'),
        (EVERY_OTHER_WEEK, 'Every other week'),
    )
    intern_help_requests_frequency = models.CharField(max_length=1, choices=ASKING_FOR_HELP_FREQUENCY_CHOICES, default=NEVER, verbose_name="How often does <b>your intern</b> ask for your help?")

    HOURS_1 = '1H'
    HOURS_3 = '3H'
    HOURS_6 = '6H'
    HOURS_12 = '12H'
    DAYS_1 = '1D'
    DAYS_2 = '2D'
    DAYS_4 = '4D'
    DAYS_6 = '6D'
    LONGER = '>7D'
    RESPONSE_TIME_CHOICES = (
        (HOURS_1, '1 hour'),
        (HOURS_3, '3 hours'),
        (HOURS_6, '6 hours'),
        (HOURS_12, '12 hours'),
        (DAYS_1, '1 day'),
        (DAYS_2, '2-3 days'),
        (DAYS_4, '4-5 days'),
        (DAYS_6, '6-7 days'),
        (LONGER, '> 7 days'),
    )
    mentor_help_response_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, default=LONGER, verbose_name="How long does it take for <b>you</b> to respond to your intern's request for help?")

    CONTRIBUTION_FREQUENCY_CHOICES = (
        (NEVER, 'Intern has not submitted a contribution'),
        (ONCE_DAILY, 'Once per day'),
        (MULTIPLE_WEEKLY, 'Multiple times per week'),
        (ONCE_WEEKLY, 'Once per week'),
        (EVERY_OTHER_WEEK, 'Every other week'),
    )
    intern_contribution_frequency = models.CharField(max_length=1, choices=CONTRIBUTION_FREQUENCY_CHOICES, default=NEVER, verbose_name="How often does <b>your intern</b> submit a project contribution?")

    mentor_review_response_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, default=LONGER, verbose_name="How long does it take for <b>you</b> to give feedback on your intern's contributions?")

    intern_contribution_revision_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, default=LONGER, verbose_name="How long does it take for <b>your intern</b> to incorporate feedback and resubmit a contribution?")

    progress_report = models.TextField(verbose_name="Please provide a paragraph describing your intern's progress on their project. This will only be shown to Outreachy organizers, your community coordinator, and the Software Freedom Conservancy accounting staff.")

    # Deprecated - this data is set in clean() to be used for intern payment authorization JSON export
    payment_approved = models.BooleanField(verbose_name="Should your Outreachy intern be paid the mid-point $2,000 payment?", help_text="Please base your answer on whether your intern has put in a full-time, 40 hours a week effort. They should have made project contributions, promptly responded to feedback on those contributions, and resubmitted their revised contributions. If they were stuck, they should have reached out to you or the community for help. If you are going to ask for an internship extension, please say no to this question.")

    # Deprecated - this data is set in clean() to be used for intern payment authorization JSON export
    extension_date = models.DateField(help_text="If you want to extend the internship, please pick a date when you will be asked to update your intern's mid-point feedback and authorize payment. Internships can be extended for up to five weeks. We don't recommend extending an internship for more than 3 weeks at mid-point feedback. Please leave this field blank if you are not asking for an extension.", blank=True, null=True)

    ACTION_CHOICES = (
        (BaseMentorFeedback.PAY_AND_CONTINUE, 'Pay the midpoint intern stipend'),
        (BaseMentorFeedback.EXT_1_WEEK, 'Delay payment - extend the internship 1 week total'),
        (BaseMentorFeedback.EXT_2_WEEK, 'Delay payment - extend the internship 2 weeks total'),
        (BaseMentorFeedback.EXT_3_WEEK, 'Delay payment - extend the internship 3 weeks total'),
        (BaseMentorFeedback.EXT_4_WEEK, 'Delay payment - extend the internship 4 weeks total'),
        (BaseMentorFeedback.EXT_5_WEEK, 'Delay payment - extend the internship 5 weeks total'),
        (BaseMentorFeedback.TERMINATE_PAY, 'Terminate the internship contract, and pay the midpoint intern stipend'),
        (BaseMentorFeedback.TERMINATE_NO_PAY, 'Terminate the internship contract, and do NOT pay the midpoint intern stipend'),
        (BaseMentorFeedback.DONT_KNOW, "I don't know what action to recommend, please advise"),
    )
    actions_requested = models.CharField(max_length=9, choices=ACTION_CHOICES, default=BaseMentorFeedback.PAY_AND_CONTINUE, verbose_name="What actions are you requesting Outreachy organizers to take, based on your feedback?")

    def can_edit(self):
        if not self.allow_edits:
            return False

        if self.intern_selection.midpoint_feedback_opens.has_passed():
            return True
        return False

    def clean(self):
        # See comments in class Feedback1FromMentor's clean method. Same applies here.
        self.set_payment_for_json_export()
        self.set_termination_request_for_json_export()
        requested_extension = self.set_and_return_extension_for_json_export()
        if requested_extension > 0:
            self.extension_date = self.intern_selection.round().midfeedback + datetime.timedelta(weeks=requested_extension)

class MidpointInternFeedback(BaseInternFeedback):
    '''
    This class is deprecated as of the December 2021 intern cohort.
    Please see the Feedback2FromIntern class instead.
    '''
    # XXX - Make sure to change the questions in
    # home/templates/home/email/midpoint-feedback-instructions.txt
    # if you change these verbose names.
    NEVER = '0'
    MULTIPLE_DAILY = 'U'
    ONCE_DAILY = 'D'
    MULTIPLE_WEEKLY = 'M'
    ONCE_WEEKLY = 'W'
    EVERY_OTHER_WEEK = 'B'
    ASKING_FOR_HELP_FREQUENCY_CHOICES = (
        (NEVER, 'I have not asked for help'),
        (MULTIPLE_DAILY, 'Multiple times per day'),
        (ONCE_DAILY, 'Once per day'),
        (MULTIPLE_WEEKLY, 'Multiple times per week'),
        (ONCE_WEEKLY, 'Once per week'),
        (EVERY_OTHER_WEEK, 'Every other week'),
    )
    intern_help_requests_frequency = models.CharField(max_length=1, choices=ASKING_FOR_HELP_FREQUENCY_CHOICES, default=NEVER, verbose_name="How often do <b>you</b> ask for your mentor's help?")

    HOURS_1 = '1H'
    HOURS_3 = '3H'
    HOURS_6 = '6H'
    HOURS_12 = '12H'
    DAYS_1 = '1D'
    DAYS_2 = '2D'
    DAYS_4 = '4D'
    DAYS_6 = '6D'
    LONGER = '>7D'
    RESPONSE_TIME_CHOICES = (
        (HOURS_1, '1 hour'),
        (HOURS_3, '3 hours'),
        (HOURS_6, '6 hours'),
        (HOURS_12, '12 hours'),
        (DAYS_1, '1 day'),
        (DAYS_2, '2-3 days'),
        (DAYS_4, '4-5 days'),
        (DAYS_6, '6-7 days'),
        (LONGER, '> 7 days'),
    )
    mentor_help_response_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, default=LONGER, verbose_name="How long does it take for <b>your mentor</b> to respond to your requests for help?")

    CONTRIBUTION_FREQUENCY_CHOICES = (
        (NEVER, 'I have not submitted a contribution'),
        (ONCE_DAILY, 'Once per day'),
        (MULTIPLE_WEEKLY, 'Multiple times per week'),
        (ONCE_WEEKLY, 'Once per week'),
        (EVERY_OTHER_WEEK, 'Every other week'),
    )
    intern_contribution_frequency = models.CharField(max_length=1, choices=CONTRIBUTION_FREQUENCY_CHOICES, default=NEVER, verbose_name="How often do <b>you</b> submit a project contribution?")

    mentor_review_response_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, default=LONGER, verbose_name="How long does it take for <b>your mentor</b> to give feedback on your contributions?")

    intern_contribution_revision_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, default=LONGER, verbose_name="How long does it take for <b>you</b> to incorporate your mentor's feedback and resubmit a contribution?")

    progress_report = models.TextField(verbose_name="Please provide a paragraph describing your progress on your project. This will only be shown to Outreachy organizers.")

    def can_edit(self):
        if not self.allow_edits:
            return False

        if self.intern_selection.midpoint_feedback_opens.has_passed():
            return True
        return False

class FinalMentorFeedback(BaseMentorFeedback):
    # XXX - Make sure to change the questions in
    # home/templates/home/email/final-feedback-instructions.txt
    # if you change these verbose names.
    NEVER = '0'
    MULTIPLE_DAILY = 'U'
    ONCE_DAILY = 'D'
    MULTIPLE_WEEKLY = 'M'
    ONCE_WEEKLY = 'W'
    EVERY_OTHER_WEEK = 'B'
    ASKING_FOR_HELP_FREQUENCY_CHOICES = (
        (NEVER, 'Intern has not asked for help'),
        (MULTIPLE_DAILY, 'Multiple times per day'),
        (ONCE_DAILY, 'Once per day'),
        (MULTIPLE_WEEKLY, 'Multiple times per week'),
        (ONCE_WEEKLY, 'Once per week'),
        (EVERY_OTHER_WEEK, 'Every other week'),
    )
    intern_help_requests_frequency = models.CharField(max_length=1, choices=ASKING_FOR_HELP_FREQUENCY_CHOICES, default=NEVER, verbose_name="How often does <b>your intern</b> ask for your help?")

    HOURS_1 = '1H'
    HOURS_3 = '3H'
    HOURS_6 = '6H'
    HOURS_12 = '12H'
    DAYS_1 = '1D'
    DAYS_2 = '2D'
    DAYS_4 = '4D'
    DAYS_6 = '6D'
    LONGER = '>7D'
    RESPONSE_TIME_CHOICES = (
        (HOURS_1, '1 hour'),
        (HOURS_3, '3 hours'),
        (HOURS_6, '6 hours'),
        (HOURS_12, '12 hours'),
        (DAYS_1, '1 day'),
        (DAYS_2, '2-3 days'),
        (DAYS_4, '4-5 days'),
        (DAYS_6, '6-7 days'),
        (LONGER, '> 7 days'),
    )
    mentor_help_response_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, default=LONGER, verbose_name="How long does it take for <b>you</b> to respond to your intern's request for help?")

    CONTRIBUTION_FREQUENCY_CHOICES = (
        (NEVER, 'Intern has not submitted a contribution'),
        (ONCE_DAILY, 'Once per day'),
        (MULTIPLE_WEEKLY, 'Multiple times per week'),
        (ONCE_WEEKLY, 'Once per week'),
        (EVERY_OTHER_WEEK, 'Every other week'),
    )
    intern_contribution_frequency = models.CharField(max_length=1, choices=CONTRIBUTION_FREQUENCY_CHOICES, default=NEVER, verbose_name="How often does <b>your intern</b> submit a project contribution?")

    mentor_review_response_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, default=LONGER, verbose_name="How long does it take for <b>you</b> to give feedback on your intern's contributions?")

    intern_contribution_revision_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, default=LONGER, verbose_name="How long does it take for <b>your intern</b> to incorporate feedback and resubmit a contribution?")

    # Deprecated - this data is set in clean() to be used for intern payment authorization JSON export
    progress_report = models.TextField(verbose_name="Please provide a paragraph describing your intern's progress on their project. This will only be shown to Outreachy organizers, your community coordinator, and the Software Freedom Conservancy accounting staff.")

    # Deprecated - this data is set in clean() to be used for intern payment authorization JSON export
    payment_approved = models.BooleanField(verbose_name="Should your Outreachy intern be paid the final $2,500 payment?", help_text="Please base your answer on whether your intern has put in a full-time, 40 hours a week effort. They should have made project contributions, promptly responded to feedback on those contributions, and resubmitted their revised contributions. If they were stuck, they should have reached out to you or the community for help. If you are going to ask for an internship extension, please say no to this question.")

    extension_date = models.DateField(help_text="If you want to extend the internship, please pick a date when you will be asked to update your intern's final feedback and authorize payment. Internships can be extended for up to five weeks. Please leave this field blank if you are not asking for an extension.", blank=True, null=True)

    # Note that TERMINATE_PAY does not make sense for the final feedback.
    # If we pay the intern, their internship is done, and they're in good standing.
    # We can't both terminate the internship contract abnormally and pay them.
    ACTION_CHOICES = (
        (BaseMentorFeedback.PAY_AND_CONTINUE, 'Pay final intern stipend'),
        (BaseMentorFeedback.EXT_1_WEEK, 'Delay payment - extend the internship 1 week total'),
        (BaseMentorFeedback.EXT_2_WEEK, 'Delay payment - extend the internship 2 weeks total'),
        (BaseMentorFeedback.EXT_3_WEEK, 'Delay payment - extend the internship 3 weeks total'),
        (BaseMentorFeedback.EXT_4_WEEK, 'Delay payment - extend the internship 4 weeks total'),
        (BaseMentorFeedback.EXT_5_WEEK, 'Delay payment - extend the internship 5 weeks total'),
        (BaseMentorFeedback.TERMINATE_NO_PAY, 'Terminate the internship contract, and do not pay the final intern stipend'),
        (BaseMentorFeedback.DONT_KNOW, "I don't know what action to recommend, please advise"),
    )
    actions_requested = models.CharField(max_length=9, choices=ACTION_CHOICES, default=BaseMentorFeedback.PAY_AND_CONTINUE, verbose_name="What actions are you requesting Outreachy organizers to take, based on your feedback?")

    # Survey for Outreachy organizers

    YES = 'YES'
    NO = 'NO'
    DUNNO = 'DUN'
    NO_OPINION = 'NOP'
    SURVEY_RESPONSES = (
        (YES, 'Yes'),
        (NO, 'No'),
        (DUNNO, "I don't know"),
        (NO_OPINION, 'No opinion'),
    )
    mentoring_recommended = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Would you recommend a friend mentor for Outreachy?")

    WEEK1 = '1'
    WEEK2 = '2'
    WEEK3 = '3'
    WEEK4 = '4'
    BLOG_FREQUENCY = (
        (WEEK1, 'Once a week'),
        (WEEK2, 'Every two weeks'),
        (WEEK3, 'Every three weeks'),
        (WEEK4, 'Every four weeks'),
        (NO_OPINION, 'No opinion'),
    )
    blog_frequency = models.CharField(max_length=3, choices=BLOG_FREQUENCY, default=NO_OPINION, verbose_name="How often do you feel Outreachy interns should blog during their 12 week internship?")

    blog_prompts_caused_writing = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Did the Outreachy blog prompt emails encourage your intern to write about their project?")

    blog_prompts_caused_overhead = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Did the Outreachy blog prompts take too much time away from your intern's project work?")

    recommend_blog_prompts = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Should Outreachy organizers provide blog post prompt emails next round?")

    zulip_caused_intern_discussion = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Did the Outreachy Zulip chat encourage your intern to communicate more?")

    zulip_caused_mentor_discussion = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Did the Outreachy Zulip chat encourage you to communicate more?")

    recommend_zulip = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Should Outreachy organizers provide the Zulip chat next round?")

    feedback_for_organizers = models.TextField(verbose_name="Please provide Outreachy organizers any additional feedback.")

    def can_edit(self):
        if not self.allow_edits:
            return False

        if self.intern_selection.final_feedback_opens.has_passed():
            return True
        return False

    def clean(self):
        # See comments in class Feedback1FromMentor's clean method. Same applies here.
        self.set_payment_for_json_export()
        self.set_termination_request_for_json_export()
        requested_extension = self.set_and_return_extension_for_json_export()
        if requested_extension > 0:
            self.extension_date = self.intern_selection.round().finalfeedback + datetime.timedelta(weeks=requested_extension)

class FinalInternFeedback(BaseInternFeedback):
    # XXX - Make sure to change the questions in
    # home/templates/home/email/final-feedback-instructions.txt
    # if you change these verbose names.
    NEVER = '0'
    MULTIPLE_DAILY = 'U'
    ONCE_DAILY = 'D'
    MULTIPLE_WEEKLY = 'M'
    ONCE_WEEKLY = 'W'
    EVERY_OTHER_WEEK = 'B'
    ASKING_FOR_HELP_FREQUENCY_CHOICES = (
        (NEVER, 'I have not asked for help'),
        (MULTIPLE_DAILY, 'Multiple times per day'),
        (ONCE_DAILY, 'Once per day'),
        (MULTIPLE_WEEKLY, 'Multiple times per week'),
        (ONCE_WEEKLY, 'Once per week'),
        (EVERY_OTHER_WEEK, 'Every other week'),
    )
    intern_help_requests_frequency = models.CharField(max_length=1, choices=ASKING_FOR_HELP_FREQUENCY_CHOICES, default=NEVER, verbose_name="How often do <b>you</b> ask for your mentor's help?")

    HOURS_1 = '1H'
    HOURS_3 = '3H'
    HOURS_6 = '6H'
    HOURS_12 = '12H'
    DAYS_1 = '1D'
    DAYS_2 = '2D'
    DAYS_4 = '4D'
    DAYS_6 = '6D'
    LONGER = '>7D'
    RESPONSE_TIME_CHOICES = (
        (HOURS_1, '1 hour'),
        (HOURS_3, '3 hours'),
        (HOURS_6, '6 hours'),
        (HOURS_12, '12 hours'),
        (DAYS_1, '1 day'),
        (DAYS_2, '2-3 days'),
        (DAYS_4, '4-5 days'),
        (DAYS_6, '6-7 days'),
        (LONGER, '> 7 days'),
    )
    mentor_help_response_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, default=LONGER, verbose_name="How long does it take for <b>your mentor</b> to respond to your requests for help?")

    CONTRIBUTION_FREQUENCY_CHOICES = (
        (NEVER, 'I have not submitted a contribution'),
        (ONCE_DAILY, 'Once per day'),
        (MULTIPLE_WEEKLY, 'Multiple times per week'),
        (ONCE_WEEKLY, 'Once per week'),
        (EVERY_OTHER_WEEK, 'Every other week'),
    )
    intern_contribution_frequency = models.CharField(max_length=1, choices=CONTRIBUTION_FREQUENCY_CHOICES, default=NEVER, verbose_name="How often do <b>you</b> submit a project contribution?")

    mentor_review_response_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, default=LONGER, verbose_name="How long does it take for <b>your mentor</b> to give feedback on your contributions?")

    intern_contribution_revision_time = models.CharField(max_length=3, choices=RESPONSE_TIME_CHOICES, default=LONGER, verbose_name="How long does it take for <b>you</b> to incorporate your mentor's feedback and resubmit a contribution?")

    progress_report = models.TextField(verbose_name="Please provide a paragraph describing your progress on your project. This will only be shown to Outreachy organizers.")

    # Survey for Outreachy organizers

    YES = 'YES'
    NO = 'NO'
    DUNNO = 'DUN'
    NO_OPINION = 'NOP'
    SURVEY_RESPONSES = (
        (YES, 'Yes'),
        (NO, 'No'),
        (DUNNO, "I don't know"),
        (NO_OPINION, 'No opinion'),
    )
    interning_recommended = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Would you recommend a friend intern with Outreachy?")

    recommend_intern_chat = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Should Outreachy organizers have video chats with all interns next round?")

    WEEK1 = '1'
    WEEK2 = '2'
    WEEK3 = '3'
    WEEK4 = '4'
    WEEK6 = '6'
    ONCE = '12'
    BLOG_FREQUENCY = (
        (WEEK1, 'Once a week'),
        (WEEK2, 'Every 2 weeks'),
        (WEEK3, 'Every 3 weeks'),
        (WEEK4, 'Every 4 weeks'),
        (WEEK6, 'Every 6 weeks'),
        (ONCE, 'Once during the internship'),
        (NO_OPINION, 'No opinion'),
    )
    chat_frequency = models.CharField(max_length=3, choices=BLOG_FREQUENCY, default=NO_OPINION, verbose_name="How often do you feel Outreachy organizers should host a video chat for all interns during their 12 week internship?")

    blog_frequency = models.CharField(max_length=3, choices=BLOG_FREQUENCY, default=NO_OPINION, verbose_name="How often do you feel Outreachy interns should blog during their 12 week internship?")

    blog_prompts_caused_writing = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Did the Outreachy blog prompt emails encourage you to write about your project?")

    blog_prompts_caused_overhead = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Did the Outreachy blog prompts take too much time away from your project work?")

    recommend_blog_prompts = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Should Outreachy organizers provide blog post prompt emails next round?")

    zulip_caused_intern_discussion = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Did the Outreachy Zulip chat encourage you to communicate more?")

    zulip_caused_mentor_discussion = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Did the Outreachy Zulip chat encourage your mentor to communicate more?")

    recommend_zulip = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Should Outreachy organizers provide the Zulip chat next round?")

    tech_industry_prep = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Do you feel better prepared to work in the technology industry after your Outreachy internship?")

    foss_confidence = models.CharField(max_length=3, choices=SURVEY_RESPONSES, default=NO_OPINION, verbose_name="Do you feel more confident about contributing to free and open source software after your Outreachy internship?")

    feedback_for_organizers = models.TextField(verbose_name="Please provide Outreachy organizers any additional feedback.")

    def can_edit(self):
        if not self.allow_edits:
            return False

        if self.intern_selection.final_feedback_opens.has_passed():
            return True
        return False


# --- Dashboard models --- #

# Please keep this at the end of this file; it has to come after the
# models it mentions, so just keep it after all other definitions.
DASHBOARD_MODELS = (
        CoordinatorApproval,
        Participation,
        Project,
        MentorApproval,
        )
