from __future__ import absolute_import, unicode_literals

from os import urandom
from base64 import urlsafe_b64encode
from datetime import date
from datetime import timedelta
from email.headerregistry import Address

from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.db import models
from django.forms import ValidationError
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
from wagtail.wagtailembeds.blocks import EmbedBlock

from . import email

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
    internannounce = models.DateField("Date interns are announced", default='2017-11-09')
    internstarts = models.DateField("Date internships start", default='2017-12-05')
    midfeedback = models.DateField("Date mid-point feedback is due", blank=True, default='2018-01-16')
    internends = models.DateField("Date internships end", default='2018-03-05')
    finalfeedback = models.DateField("Date final feedback is due", blank=True, default='2018-03-12')
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
    def ProjectsDeadline(self):
        return(self.appsclose - timedelta(days=14))

    def LateApplicationsDeadline(self):
        return(self.appsclose + timedelta(days=7))
    
    def InternSelectionDeadline(self):
        return(self.appsclose + timedelta(days=10))
    
    def InternConfirmationDeadline(self):
        return(self.appsclose + timedelta(days=24))

    def gsoc_round(self):
        # The internships would start before August
        # for rounds aligned with GSoC
        # GSoC traditionally starts either in May or June
        return(self.internstarts.month < 8)

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
    ]

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


# From Wordnik:
# comrade: A person who shares one's interests or activities; a friend or companion.
# user: One who uses addictive drugs.
class Comrade(models.Model):
    account = models.OneToOneField(User, primary_key=True)
    public_name = models.CharField(max_length=LONG_LEGAL_NAME, verbose_name="Name (public)", help_text="Your full name, which will be publicly displayed on the Outreachy website. This is typically your given name, followed by your family name. You may use a pseudonym or abbreviate your given or family names if you have concerns about privacy.")

    nick_name = models.CharField(max_length=SHORT_NAME, verbose_name="Nick name (internal)", help_text="The short name used in emails to you. You would use this name when introducing yourself to a new person, such as 'Hi, I'm (nick name)'. Emails will be addressed 'Hi (nick name)'. This name will be shown to organizers, coordinators, mentors, and volunteers.")

    legal_name = models.CharField(max_length=LONG_LEGAL_NAME, verbose_name="Legal name (private)", help_text="Your name on your government identification. This is the name that you would use to sign a legal document. This will be used only by Outreachy organizers on any private legal contracts. Other applicants, coordinators, mentors, and volunteers will not see this name.")

    # Reference: https://uwm.edu/lgbtrc/support/gender-pronouns/
    EY_PRONOUNS = ['ey', 'em', 'eir', 'eirs', 'eirself', 'http://pronoun.is/ey']
    FAE_PRONOUNS = ['fae', 'faer', 'faer', 'faers', 'faerself', 'http://pronoun.is/fae']
    HE_PRONOUNS = ['he', 'him', 'his', 'his', 'himself', 'http://pronoun.is/he']
    PER_PRONOUNS = ['per', 'per', 'pers', 'pers', 'perself', 'http://pronoun.is/per']
    SHE_PRONOUNS = ['she', 'her', 'her', 'hers', 'herself', 'http://pronoun.is/she']
    THEY_PRONOUNS = ['they', 'them', 'their', 'theirs', 'themself', 'http://pronoun.is/they']
    VE_PRONOUNS = ['ve', 'ver', 'vis', 'vis', 'verself', 'http://pronoun.is/ve']
    XE_PRONOUNS = ['xe', 'xem', 'xyr', 'xyrs', 'xemself', 'http://pronoun.is/xe']
    ZE_PRONOUNS = ['ze', 'hir', 'hir', 'hirs', 'hirself', 'http://pronoun.is/ze']
    PRONOUN_CHOICES = (
            (SHE_PRONOUNS[0], '{subject}/{Object}/{possessive}'.format(subject=SHE_PRONOUNS[0], Object=SHE_PRONOUNS[1], possessive=SHE_PRONOUNS[2])),
            (HE_PRONOUNS[0], '{subject}/{Object}/{possessive}'.format(subject=HE_PRONOUNS[0], Object=HE_PRONOUNS[1], possessive=HE_PRONOUNS[1])),
            (THEY_PRONOUNS[0], '{subject}/{Object}/{possessive}'.format(subject=THEY_PRONOUNS[0], Object=THEY_PRONOUNS[1], possessive=THEY_PRONOUNS[2])),
            (FAE_PRONOUNS[0], '{subject}/{Object}/{possessive}'.format(subject=FAE_PRONOUNS[0], Object=FAE_PRONOUNS[1], possessive=FAE_PRONOUNS[2])),
            (EY_PRONOUNS[0], '{subject}/{Object}/{possessive}'.format(subject=EY_PRONOUNS[0], Object=EY_PRONOUNS[1], possessive=EY_PRONOUNS[2])),
            (PER_PRONOUNS[0], '{subject}/{Object}/{possessive}'.format(subject=PER_PRONOUNS[0], Object=PER_PRONOUNS[1], possessive=PER_PRONOUNS[2])),
            (VE_PRONOUNS[0], '{subject}/{Object}/{possessive}'.format(subject=VE_PRONOUNS[0], Object=VE_PRONOUNS[1], possessive=VE_PRONOUNS[2])),
            (XE_PRONOUNS[0], '{subject}/{Object}/{possessive}'.format(subject=XE_PRONOUNS[1], Object=XE_PRONOUNS[2], possessive=XE_PRONOUNS[3])),
            (ZE_PRONOUNS[0], '{subject}/{Object}/{possessive}'.format(subject=ZE_PRONOUNS[1], Object=ZE_PRONOUNS[2], possessive=ZE_PRONOUNS[3])),
            )
    pronouns = models.CharField(
            max_length=4,
            choices=PRONOUN_CHOICES,
            default=THEY_PRONOUNS,
            verbose_name="Pronouns",
            help_text="Your preferred pronoun. This will be used in emails from Outreachy organizers directly to you. The format is subject/object/possessive. Example: '__(subject)__ interned with Outreachy. The mentor liked working with __(object)__. __(possessive)__ internship project was challenging.",
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

    def __str__(self):
        return self.public_name

    def email_address(self):
        return Address(self.public_name, addr_spec=self.account.email)

    def get_pronouns_html(self):
        return "<a href=http://pronoun.is/{short_name}>{pronouns}</a>".format(
                short_name=self.pronouns,
                pronouns=self.get_pronouns_display(),
                )


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
        contributions = Contribution.objects.filter(applicant=applicant)
        projects = []
        for c in contributions:
            if not c.project in projects:
                projects.append(c.project)
        return projects


class ApprovalStatusQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(approval_status=ApprovalStatus.APPROVED)

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
            help_text="Short description of community. This should be three sentences for someone who has never heard of your community or the technologies involved. Do not put any links in the short description (use the long description instead).")

    long_description = CKEditorField(
            blank=True,
            help_text="(Optional) Longer description of community.")

    website = models.URLField(
            blank=True,
            help_text="(Optional) Please provide the URL for your FOSS community's website")

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

    def get_approved_mentored_projects(self):
        current_round = RoundPage.objects.latest('internstarts')
        # Get all projects for this community
        # where the project is approved,
        # and the community is approved to participate in the current round.
        projects = Project.objects.filter(
                project_round__community = self,
                approval_status = ApprovalStatus.APPROVED,
                project_round__participating_round = current_round,
                project_round__approval_status = ApprovalStatus.APPROVED,
                )
        return projects

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
        help_text="How many people are contributing to this FOSS community regularly?",
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
        help_text="How long has this FOSS community accepted public contributions?",
    )

    participating_orgs = models.CharField(max_length=THREE_PARAGRAPH_LENGTH,
            help_text="What different organizations and companies participate in this FOSS community? If there are many organizations, list the top five organizations who make large contributions.")

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

    goverance = models.URLField(blank=True, help_text="(Optional) Please provide a URL for a description of your community's governance model")
    code_of_conduct = models.URLField(blank=True, help_text="(Optional) Please provide a URL for to your community's Code of Conduct")
    cla = models.URLField(blank=True, help_text="(Optional) Please provide a URL for your community's Contributor License Agreement (CLA)")
    dco = models.URLField(blank=True, help_text="(Optional) Please provide a URL for your community's Developer Certificate of Origin (DCO) agreement")

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

    def get_submitter_email_list(self):
        return self.community.get_coordinator_email_list()

    @classmethod
    def objects_for_dashboard(cls, user):
        if user.is_staff:
            return cls.objects.all()
        return cls.objects.filter(
                community__coordinatorapproval__approval_status=ApprovalStatus.APPROVED,
                community__coordinatorapproval__coordinator__account=user,
                )

class Sponsorship(models.Model):
    participation = models.ForeignKey(Participation, on_delete=models.CASCADE)

    coordinator_can_update = models.BooleanField(
            help_text="""
            Can a community coordinator update this information, or is
            it provided by the Outreachy organizers?
            """)

    name = models.CharField(
            max_length=SENTENCE_LENGTH,
            help_text='The full sponsor name to be used on invoices.')

    amount = models.PositiveIntegerField()

    funding_secured = models.BooleanField(
            default=False,
            help_text="""
            Is this funding confirmed by the sponsoring organization, or
            is it currently only tentative?
            """)

    funding_decision_date = models.DateField(
            default=date.today,
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
        help_text="How long has the team accepted publicly submitted contributions? (See the 'Terms Used' section above for a definition of a team.",
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
        help_text="How many regular contributors does this team have?",
    )

    intern_tasks = CKEditorField(
            max_length=THREE_PARAGRAPH_LENGTH,
            blank=True,
            help_text='(Optional) Description of possible internship tasks.')

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
            help_text='Short title for this internship project proposal. This should be 100 characters or less, starting with a verb like "Create", "Improve", "Extend", "Survey", "Document", etc. Assume the applicant has never heard of your technology before and keep it simple. The short title will be used in your project page URL, so keep it short.')
    slug = models.SlugField(
            max_length=50,
            verbose_name="Project URL slug")
    long_description = CKEditorField(
            blank=True,
            help_text='Description of the internship project, excluding applicant skills and communication channels. Those will be added in the next step.')

    repository = models.URLField(blank=True, help_text="(Optional) URL for your team's repository or contribution mechanism")
    issue_tracker = models.URLField(blank=True, help_text="(Optional) URL for your team's issue tracker")
    newcomer_issue_tag = models.CharField(
            blank=True,
            max_length=SENTENCE_LENGTH,
            help_text="(Optional) What tag is used for newcomer-friendly issues for your team or for this internship project?")

    contribution_tasks = CKEditorField(
            help_text='Instructions for how applicants can make contributions during the Outreachy application period. Make sure to include links to getting started tutorials or documentation, how applicants can find contribution tasks on your project website or issue tracker, who they should ask for tasks, and everything they need to know to get started.')

    accepting_new_applicants = models.BooleanField(help_text='Is this internship project currently accepting contributions from new applicants? If you have an applicant in mind to accept as an intern (or several promising applicants) who have filled out the eligibility information and an application, you can uncheck this box to close the internship project to new applicants.', default=True)

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

    def get_contributions_url(self):
        return reverse('contributions', kwargs={'round_slug': self.project_round.participating_round.slug, 'community_slug': self.project_round.community.slug, 'project_slug': self.slug})

    def get_action_url(self, action):
        return reverse('project-action', kwargs={
            'community_slug': self.project_round.community.slug,
            'project_slug': self.slug,
            'action': action,
            })

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
            if a.finalapplication_set.filter(project=self):
                a.submitted_application = True
            else:
                a.submitted_application = False

        return applicants

    def get_applications(self):
        return FinalApplication.objects.filter(project = self)

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
            help_text='I have read the <a href="/mentor/#mentor">mentor duties</a> and <a href="/mentor/mentor-faq/">mentor FAQ</a>.')

    understands_intern_time_commitment = models.BooleanField(
            default=False,
            validators=[mentor_read_instructions],
            help_text='I understand that Outreachy mentors will spend a minimum of 5 hours a week mentoring their intern during the three month internship period')

    understands_applicant_time_commitment = models.BooleanField(
            default=False,
            validators=[mentor_read_instructions],
            help_text='I understand that Outreachy mentors often find they must spend more time helping applicants during the application period than helping their intern during the internship period')

    understands_mentor_contract = models.BooleanField(
            default=False,
            validators=[mentor_read_contract],
            help_text='I understand that Outreachy mentors will need to sign a <a href="/documents/1/Outreachy-Program--Mentorship-Terms-of-Participation-May-2017.pdf">mentor contract</a> after they accept an applicant as an intern')

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
        help_text="How long have you been a contributor on this team?",
    )

    mentor_foss_contributions = models.CharField(
        max_length=PARAGRAPH_LENGTH,
        help_text="What contributions have you made to this team and the FOSS community who is funding this internship? If none, what contributions have you made to other FOSS communities?",
    )

    communication_channel_username = models.CharField(
        max_length=SENTENCE_LENGTH,
        blank=True,
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
        help_text="Have you been a mentor for Outreachy before? (Note that Outreachy welcomes first time mentors, but this information allows the coordinator and other mentors to provide extra help to new mentors.)",
    )

    mentorship_style = models.CharField(
        max_length=PARAGRAPH_LENGTH,
        help_text="What is your mentorship style? Do you prefer short daily standups, longer weekly reports, or informal progress reports? Are you willing to try pair programming when your intern gets stuck? Do you like talking over video chat or answering questions via email? Give the applicants a sense of what it will be like to work with you during the internship.",
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
            help_text='Name of the communication tool your project uses. E.g. "a mailing list", "IRC", "Zulip", "Mattermost", or "Discourse"')

    url = models.CharField(
            max_length=200,
            validators=[URLValidator(schemes=['http', 'https', 'irc'])],
            help_text='URL for the communication channel applicants will use to reach mentors and ask questions about this internship project. IRC URLs should be in the form irc://&lt;host&gt;[:port]/[channel]. Since many applicants have issues with IRC port blocking at their universities, IRC communication links will use <a href="https://kiwiirc.com/">Kiwi IRC</a> to direct applicants to a web-based IRC client. If this is a mailing list, the URL should be the mailing list subscription page.')

    instructions = CKEditorField(
            blank=True,
            help_text='(Optional) After following the communication channel link, are there any special instructions? For example: "Join the #outreachy channel and make sure to introduce yourself.')

    norms = CKEditorField(
            blank=True,
            help_text="(Optional) What communication norms would a newcomer need to know about this communication channel? Example: newcomers to open source don't know they should Cc their mentor or the software maintainer when asking a question to a large mailing list. Think about what a newcomer would find surprising when communicating on this channel.")

    communication_help = models.URLField(
            blank=True,
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
            date = date + timedelta(days=1)
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

    # XXX: Make sure to update the text in the eligibility results template
    # if you update the verbose name of any of these fields.
    over_18 = models.NullBooleanField(
            verbose_name='Will you be 18 years or older when the Outreachy internship starts?')
    gsoc_or_outreachy_internship = models.NullBooleanField(
            verbose_name='Previous Google Summer of Code or Outreachy internship?',
            help_text='Have you been accepted as a Google Summer of Code intern or an Outreachy intern before? Please say yes even if you did not complete the internship.')

    enrolled_as_student = models.NullBooleanField(
            help_text='Will you be enrolled in a university or college during the Outreachy internship period?')

    employed = models.NullBooleanField(
            help_text='Will you be an employee (for any number of hours) during the Outreachy internship period?')

    contractor = models.NullBooleanField(
            help_text='Will you be a contractor during the Outreachy internship period?')

    volunteer_time_commitments = models.NullBooleanField(
            help_text='Will you have volunteer time commitments that require more than 10 hours a week during the Outreachy internship period?')

    other_time_commitments = models.TextField(
            max_length=THREE_PARAGRAPH_LENGTH,
            blank=True,
            help_text="(Optional) If you have other time commitments outside of school, work, or volunteer hours, please use this field to let your mentor know. Examples of other time commitments include vacation that lasts longer than a week, coding school time commitments, community or online classes, etc.")

    us_national_or_permanent_resident = models.NullBooleanField(
            help_text='Are you a national or permanent resident of the United States of America? Outreachy is open to some people around the world, and additional grpous of people in the U.S.A.')

    living_in_us = models.NullBooleanField(
            verbose_name='Will you be living for the majority of the Outreachy internship period in the United States of America and be eligible to work in the U.S.A?',
            help_text='Please answer yes even if you are a citizen of a country other than USA.')

    under_export_control = models.NullBooleanField(
            verbose_name='Are you a person or entity restricted by United States of America export controls or sanctions programs?',
            help_text='See the <a href="https://www.treasury.gov/resource-center/sanctions/Programs/Pages/Programs.aspx">US export control and sanctions list</a> for more information')

    us_sanctioned_country = models.NullBooleanField(
            verbose_name='Are you a citizen, resident, or national of Crimea, Cuba, Iran, North Korea, or Syria?',
            help_text='If you have citizenship with Cuba, Iran, North Korea, or Syria, please answer yes, even if you are not currently living in those countries.')

    eligible_to_work = models.NullBooleanField(
            help_text='Are you eligible to work for 40 hours a week in the country (or countries) you will be living in during the Outreachy internship period?</p><p>Student visas: Please note that in some countries, students studying abroad on a student visa may not be eligible to work full-time (40 hours a week). If you are on a student visa, please double check with your school counselors before applying.</p><p>Spouse visas: In some countries, spousal visas may not allow spouses to work. Please contact your immigration officer if you have any questions about whether your visa allows you to work full-time (40 hours a week).')

    # Race/Ethnicity Information
    us_resident_demographics = models.NullBooleanField(
            verbose_name='Are you Black/African American, Hispanic/Latin@, Native American, Alaska Native, Native Hawaiian, or Pacific Islander?')

    # Gender Information
    transgender = models.NullBooleanField(
            verbose_name='Do you identify as transgender?',
            help_text='If you are questioning whether you are transgender, please say yes.')

    genderqueer = models.NullBooleanField(
            verbose_name='Do you identify as genderqueer?',
            help_text='Do you identify as genderqueer, gender non-conforming, gender diverse, gender varient, or gender expansive? If you are questioning whether you identify with any of those terms, please say yes.')

    man = models.NullBooleanField()

    woman = models.NullBooleanField()

    demi_boy = models.NullBooleanField()

    demi_girl = models.NullBooleanField()

    non_binary = models.NullBooleanField()

    demi_non_binary = models.NullBooleanField()

    genderflux = models.NullBooleanField()

    genderfluid = models.NullBooleanField()

    demi_genderfluid = models.NullBooleanField()

    demi_gender = models.NullBooleanField()

    bi_gender = models.NullBooleanField()

    tri_gender = models.NullBooleanField()

    multigender = models.NullBooleanField()

    pangender = models.NullBooleanField()

    maxigender = models.NullBooleanField()

    aporagender = models.NullBooleanField()

    intergender = models.NullBooleanField()

    mavrique = models.NullBooleanField()

    gender_confusion = models.NullBooleanField()

    gender_indifferent = models.NullBooleanField()

    graygender = models.NullBooleanField()

    agender = models.NullBooleanField()

    genderless = models.NullBooleanField()

    gender_neutral = models.NullBooleanField()

    neutrois = models.NullBooleanField()

    androgynous = models.NullBooleanField()

    androgyne = models.NullBooleanField()

    prefer_not_to_say = models.NullBooleanField()

    self_identify = models.CharField(max_length=SENTENCE_LENGTH,
            blank=True,
            help_text="If your gender identity is not listed above, please let us know how you identify so we can add it to the list.")

    def is_approver(self, user):
        return user.is_staff

    def get_approver_email_list(self):
        return [email.organizers]

    def time_commitment_from_model(self, tc, hours):
        return {
                'start_date': tc.start_date,
                'end_date': tc.end_date,
                'hours': hours,
                }

    def get_time_commitments(self):
        current_round = RoundPage.objects.latest('internstarts')
        school_time_commitments = SchoolTimeCommitment.objects.filter(applicant=self)
        volunteer_time_commitments = VolunteerTimeCommitment.objects.filter(applicant=self)
        employment_time_commitments = EmploymentTimeCommitment.objects.filter(applicant=self)
        tcs = [ self.time_commitment_from_model(d, d.hours_per_week)
                for d in volunteer_time_commitments or []
                if d ]

        etcs = [ self.time_commitment_from_model(d, 0 if d.quit_on_acceptance else d.hours_per_week)
                for d in employment_time_commitments or []
                if d ]

        stcs = [ self.time_commitment_from_model(d, 40 * ((d.registered_credits - d.outreachy_credits - d.thesis_credits) / d.typical_credits))
                for d in school_time_commitments or []
                if d ]
        calendar = create_time_commitment_calendar(chain(tcs, etcs, stcs), current_round)

        longest_period_free = 0
        free_period_start_day = 0
        counter = 0
        for key, group in groupby(calendar, lambda hours: hours <= 20):
            group_len = len(list(group))
            if key is True and group_len > longest_period_free:
                longest_period_free = group_len
                free_period_start_day = counter
            counter = counter + group_len
        free_period_start_date = current_round.internstarts + timedelta(days=free_period_start_day)
        free_period_end_date = current_round.internstarts + timedelta(days=free_period_start_day + longest_period_free - 1)
        internship_total_days = current_round.internends - current_round.internstarts

        return {
                'longest_period_free': longest_period_free,
                'free_period_start_date': free_period_start_date,
                'free_period_end_date': free_period_end_date,
                'internship_total_days': internship_total_days,
                'school_time_commitments': school_time_commitments,
                'volunteer_time_commitments': volunteer_time_commitments,
                'employment_time_commitments': employment_time_commitments,
                }

class VolunteerTimeCommitment(models.Model):
    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)
    start_date = models.DateField(help_text="Date your volunteer time commitments start. Use YYYY-MM-DD format.")
    end_date = models.DateField(help_text="Date your volunteer time commitments end. Use YYYY-MM-DD format.")
    hours_per_week = models.IntegerField(help_text="Maximum hours per week spent volunteering.")
    description = models.TextField(
            max_length=THREE_PARAGRAPH_LENGTH,
            blank=True,
            help_text="Please describe what kind of volunteer position and duties you have.")

class EmploymentTimeCommitment(models.Model):
    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)
    start_date = models.DateField(help_text="Start date of employment period. Use YYYY-MM-DD format.")
    end_date = models.DateField(help_text="End date of employment period. Use YYYY-MM-DD format.")
    hours_per_week = models.IntegerField(help_text="Number of hours per week required by your employment contract")
    quit_on_acceptance = models.BooleanField(
            help_text="I will quit this job or contract if I am accepted as an Outreachy intern.")

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
            verbose_name="Number of credits for a typical student",
            help_text="How many credits does a typical student register for?<br> If your university has different credit requirements for each semester for students in your major, use the number of credits that are listed on your syllabus or class schedule.")

    registered_credits = models.IntegerField(
            verbose_name="Number of credits you're registered for",
            help_text="What is the total number of credits you are enrolled for this term?<br>If you aren't registered yet, please provide an approximate number of credits?")

    outreachy_credits = models.IntegerField(
            verbose_name="Number of internship or project credits for Outreachy",
            help_text="If you are going to seek university credit for your Outreachy internship, how many credits will you earn?")

    thesis_credits = models.IntegerField(
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

class ContractorInformation(models.Model):
    applicant = models.ForeignKey(ApplicantApproval, on_delete=models.CASCADE)

    typical_hours = models.IntegerField(
            verbose_name="Average number of hours spent on contractor business",
            help_text="During the past three months, what is the average number of hours/week you have spent on contracted work and unpaid business development or business marketing? You will be able to enter your known contract hours for the Outreachy internship period on the next page.")

    continuing_contract_work = models.NullBooleanField(
            verbose_name="Will you be doing contract work during the Outreachy internship period?")

# Please keep this at the end of this file; it has to come after the
# models it mentions, so just keep it after all other definitions.
DASHBOARD_MODELS = (
        CoordinatorApproval,
        Participation,
        Project,
        MentorApproval,
        )

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

class FinalApplication(models.Model):
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

    timeline = models.TextField(
            max_length=EIGHT_PARAGRAPH_LENGTH,
            blank=True,
            verbose_name="Outreachy internship project timeline",
            help_text="Please work with your mentor to provide a timeline of the work you plan to accomplish on the project and what tasks you will finish at each step. Make sure take into account any time commitments you have during the Outreachy internship round. If you are still working on your contributions and need more time, you can leave this blank and edit your application later.")

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
