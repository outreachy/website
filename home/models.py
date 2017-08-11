from __future__ import absolute_import, unicode_literals

from django.db import models

from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailcore import blocks
from wagtail.wagtailadmin.edit_handlers import StreamFieldPanel
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
