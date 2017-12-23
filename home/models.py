from __future__ import absolute_import, unicode_literals

from os import urandom
from base64 import urlsafe_b64encode

from django.db import models

from modelcluster.fields import ParentalKey
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
        ('heading', blocks.CharBlock(classname="full title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('logo', ImageChooserBlock()),
        ('date', blocks.DateBlock()),
        ('table', TableBlock()),
        ('quote', blocks.RichTextBlock()),
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

# Current maximum description paragraph on round 15 page is 684.
PARAGRAPH_LENGTH=800
THREE_PARAGRAPH_LENGTH=3000

class Community(models.Model):
    name = models.CharField(
            max_length=50, verbose_name="Community name")
    description = models.CharField(
            max_length=PARAGRAPH_LENGTH,
            verbose_name="Short description of community (3 sentences for someone who has never heard of your community or the technologies involved)")
    rounds = models.ManyToManyField(RoundPage, through='Participation')

    def __str__(self):
        return self.name

class Participation(models.Model):
    community = models.ForeignKey(Community)
    participating_round = models.ForeignKey(RoundPage)

    interns_funded = models.IntegerField(
            verbose_name="How many interns do you expect to fund for this round? (Include any Outreachy community credits to round up to an integer number.)")
    cfp_text = models.CharField(max_length=THREE_PARAGRAPH_LENGTH,
            verbose_name="Additional information to provide on a call for mentors and volunteers page (e.g. what kinds of projects you're looking for, ways for volunteers to help Outreachy applicants)")
    # Note that this should automatically close two weeks before the round deadline and not allow coordinators to set it to True
    cfp_open = models.BooleanField(
            verbose_name="Open call for mentors and volunteers?")
    # FIXME: hide this for everyone except those in the organizer group (or perhaps admin for now)
    list_community = models.BooleanField(
            default=False,
            verbose_name="Organizers: Check this box once you have reviewed the community information, confirmed funding, and collected billing information")

    def __str__(self):
        return '{community} in {start:%B %Y} to {end:%B %Y} round'.format(
                community = self.community.name,
                start = self.participating_round.internstarts,
                end = self.participating_round.internends,
                )
