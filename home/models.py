from __future__ import absolute_import, unicode_literals

from os import urandom
from base64 import urlsafe_b64encode
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.validators import URLValidator
from django.db import models
from django.forms import ValidationError
from django.template.loader import render_to_string
from django.urls import reverse

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
            help_text = "If this box is checked, applicant pronouns will be shared with coordinators, mentors and volunteers. If the box is checked, coordinator and mentor pronouns will be shared with applicants. If you don't want to share your pronouns, all Outreachy organizer email that Cc's another participant will use they/them/their pronouns for you.",
            default=True,
            )

    pronouns_public = models.BooleanField(
            verbose_name = "Share pronouns publicly on the Outreachy website",
            help_text = "Mentor, coordinator, and accepted interns' pronouns will be displayed publicly on the Outreachy website to anyone who is not logged in. Sharing pronouns can be a way for people to proudly display their gender identity and connect with other Outreachy participants, but other people may prefer to keep their pronouns private.",
            default=False,
            )

    timezone = TimeZoneField(blank=True, verbose_name="(Optional) Your timezone", help_text="The timezone in your current location. Shared with other Outreachy participants to help facilitate communication.")

    primary_language = LanguageField(blank=True, verbose_name="(Optional) Primary language", help_text="The spoken/written language you are most comfortable using. Shared with other Outreachy participants to help facilitate communication. Many Outreachy participants have English as a second language, and we want them to find others who speak their native language.")
    second_language = LanguageField(blank=True, verbose_name="(Optional) Second language", help_text="The second language you are most fluent in.")
    third_language = LanguageField(blank=True, verbose_name="(Optional) Third language", help_text="The next language you are most fluent in.")
    fourth_language = LanguageField(blank=True, verbose_name="(Optional) Fourth language", help_text="The next language you are most fluent in.")

    def __str__(self):
        return self.public_name

    def get_pronouns_html(self):
        return "<a href=http://pronoun.is/{short_name}>{pronouns}</a>".format(
                short_name=self.pronouns,
                pronouns=self.get_pronouns_display(),
                )

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

    class Meta:
        abstract = True

    def is_approver(self, user):
        """
        Override in subclasses to return True if the given user has
        permission to approve or reject this request, False otherwise.
        """
        raise NotImplemented

    def is_submitter(self, user):
        """
        Override in subclasses to return True if the given user has
        permission to withdraw or re-submit this request, False
        otherwise.
        """
        raise NotImplemented

    @classmethod
    def objects_for_dashboard(cls, user):
        """
        Override in subclasses to return all instances of this model for
        which the given user is either an approver or a submitter.
        """
        raise NotImplemented

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

    def __str__(self):
        return self.name

    def get_preview_url(self):
        return reverse('community-read-only', kwargs={'community_slug': self.slug})

    def is_coordinator(self, user):
        return self.coordinatorapproval_set.filter(
                approval_status=ApprovalStatus.APPROVED,
                coordinator__account=user).exists()

    def get_coordinator_email_list(self):
        return ['"{name}" <{email}>'.format(
                name=ca.coordinator.public_name, email=ca.coordinator.account.email)
                for ca in
            self.coordinatorapproval_set.filter(
                approval_status=ApprovalStatus.APPROVED)]

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

class Participation(ApprovalStatus):
    community = models.ForeignKey(Community)
    participating_round = models.ForeignKey(RoundPage)

    interns_funded = models.IntegerField(
            verbose_name="How many interns do you expect to fund for this round? (Include any Outreachy community credits to round up to an integer number.)")
    cfp_text = models.CharField(max_length=THREE_PARAGRAPH_LENGTH,
            blank=True,
            verbose_name="Additional information to provide on a call for mentors and volunteers page (e.g. what kinds of internship projects you're looking for, ways for volunteers to help Outreachy applicants)")

    def __str__(self):
        return '{start:%Y %B} to {end:%Y %B} round - {community}'.format(
                community = self.community.name,
                start = self.participating_round.internstarts,
                end = self.participating_round.internends,
                )

    def get_absolute_url(self):
        return reverse('community-landing', kwargs={'round_slug': self.participating_round.slug, 'slug': self.community.slug})

    def get_preview_url(self):
        return self.community.get_preview_url()

    def is_approver(self, user):
        return user.is_staff

    def is_submitter(self, user):
        return self.community.is_coordinator(user)

    @classmethod
    def objects_for_dashboard(cls, user):
        if user.is_staff:
            return cls.objects.all()
        return cls.objects.filter(
                community__coordinatorapproval__approval_status=ApprovalStatus.APPROVED,
                community__coordinatorapproval__coordinator__account=user,
                )

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

    intern_tasks = models.CharField(
            max_length=PARAGRAPH_LENGTH,
            blank=True,
            help_text='(Optional) Description of possible internship tasks.')

    intern_benefits = models.CharField(
            max_length=PARAGRAPH_LENGTH,
            blank=True,
            help_text="(Optional) How will the intern benefit from working with your team on this project? Imagine you're pitching this internship to a promising candidate. What would you say to convince them to apply? For example, what technical and non-technical skills will they learn from working on this project? How will this help them further their career in open source?")

    community_benefits = models.CharField(
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

    def __str__(self):
        return '{start:%Y %B} to {end:%Y %B} round - {community} - {title}'.format(
                start = self.project_round.participating_round.internstarts,
                end = self.project_round.participating_round.internends,
                community = self.project_round.community,
                title = self.short_title,
                )

    def get_preview_url(self):
        return reverse('project-read-only', kwargs={'community_slug': self.project_round.community.slug, 'project_slug': self.slug})

    def is_approver(self, user):
        return self.project_round.community.is_coordinator(user)

    def is_submitter(self, user):
        # Everyone is allowed to propose new projects.
        if self.id is None:
            return True
        # XXX: Should coordinators also be allowed to edit projects?
        return self.mentorapproval_set.filter(
                approval_status=self.APPROVED,
                mentor__account=user).exists()

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
        max_length=4,
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

    def is_approver(self, user):
        return self.project.project_round.community.is_coordinator(user)

    def is_submitter(self, user):
        return self.mentor.account_id == user.id

    @classmethod
    def objects_for_dashboard(cls, user):
        return cls.objects.filter(
                models.Q(
                    project__project_round__community__coordinatorapproval__approval_status=ApprovalStatus.APPROVED,
                    project__project_round__community__coordinatorapproval__coordinator__account=user,
                    )
                | models.Q(mentor__account=user)
                )

    # We should only send email to approved mentors if:
    # - Their project is approved AND
    # - Their community is approved
    #
    # Otherwise there's no point in telling them they can now advertise their project.
    # We also don't want to subscribe mentors to the mentors mailing list until
    # both their community, project, and mentor status is approved.
    def email_approved_mentor(self, request):

        mentor = self.mentor
        project = self.project
        communityapproval = self.project.project_round
        community = communityapproval.community

        if (communityapproval.approval_status == ApprovalStatus.APPROVED and
                project.approval_status == ApprovalStatus.APPROVED):

            email_string = render_to_string('home/email/mentor-approved.txt', {
                'community': community,
                'project': self.project,
                }, request=request)
            send_mail(
                    from_email='Outreachy Organizers <organizers@outreachy.org>',
                    recipient_list=['"{name}" <{email}>'.format(
                        name=mentor.public_name, email=mentor.account.email)],
                    subject='Approved as Outreachy mentor for {name}'.format(name=community.name),
                    message=email_string)

            # Subscribe the mentor to the mentor mailing list
            # We need to spoof sending email from the email address we want to subscribe,
            # since using 'subscribe address=email' in the body doesn't work.
            # This is still a pain because organizers need to approve subscription requests.
            # We really need mailman 3.
            email_string = render_to_string('home/email/mentor-list-subscribe.txt', {
                'comrade': mentor,
                }, request=request)
            send_mail(
                    from_email='"{name} via {domain} mentor approval" <{email}>'.format(
                        domain=request.scheme + '://' + request.get_host(),
                        name=mentor.public_name, email=mentor.account.email),
                    recipient_list=['mentors-join@lists.outreachy.org'],
                    subject='Subscribe {name}'.format(name=mentor.public_name),
                    message=email_string)

class CommunicationChannel(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    tool_name = models.CharField(
            max_length=SENTENCE_LENGTH,
            help_text='Name of the communication tool your project uses. E.g. "a mailing list", "IRC", "Zulip", "Mattermost", or "Discourse"')

    url = models.CharField(
            max_length=200,
            validators=[URLValidator(schemes=['http', 'https', 'irc'])],
            help_text='URL for the communication channel applicants will use to reach mentors and ask questions about this internship project. IRC URLs should be in the form irc://<host>[:port]/[channel]. Since many applicants have issues with IRC port blocking at their universities, IRC communication links will use <a href="https://kiwiirc.com/">Kiwi IRC</a> to direct applicants to a web-based IRC client. If this is a mailing list, the URL should be the mailing list subscription page.')

    instructions = CKEditorField(
            blank=True,
            help_text='(Optional) After following the communication channel link, are there any special instructions? For example: "Join the #outreachy channel and make sure to introduce yourself.')

    norms = CKEditorField(
            blank=True,
            help_text="(Optional) What communication norms would a newcomer need to know about this communication channel? Example: newcomers to open source don't know they should Cc their mentor or the software maintainer when asking a question to a large mailing list. Think about what a newcomer would find surprising when communicating on this channel.")

    communication_help = models.URLField(
            blank=True,
            help_text='(Optional) URL for the documentation for your communication tool. This should be user-focused documentation that explains the basic mechanisms of logging in and features. Suggestions: IRC - https://wiki.gnome.org/Outreachy/IRC; Zulip - https://chat.zulip.org/help/; Mattersmost - https://docs.mattermost.com/guides/user.html')


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

    def is_approver(self, user):
        return user.is_staff or self.community.is_coordinator(user)

    def is_submitter(self, user):
        return self.coordinator.account_id == user.id

    @classmethod
    def objects_for_dashboard(cls, user):
        if user.is_staff:
            return cls.objects.all()
        return cls.objects.filter(coordinator__account=user)
