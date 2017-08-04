from __future__ import absolute_import, unicode_literals

from django.db import models

from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailadmin.edit_handlers import FieldPanel

class HomePage(Page):

    body = RichTextField(default='<p>Outreachy provides three-month, paid, remote internships for people traditionally underrepresented in tech. Individual donors and corporate sponsors provide funding for the program, and interns are often hired by our sponsors! Interns work directly with mentors from Free and Open Source (FOSS) communities on projects ranging from programming, user experience, documentation, illustration and graphical design, and data science.</p><p>Outreachy internships are open internationally to women (cis and trans), trans men, and genderqueer people. Internships are also open to residents and nationals of the United States of any gender who are Black/African American, Hispanic/Latin@, American Indian, Alaska Native, Native Hawaiian, or Pacific Islander. We are planning to expand the program to more participants from underrepresented backgrounds in the future.</p><p>Outreachy internships run twice a year.</p>')
    content_panels = Page.content_panels + [
        FieldPanel('body', classname="full"),
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
    applicationsopendate = models.DateField("Date applications open")
    internshipstartdate = models.DateField("Date internships start")
    internshipenddate = models.DateField("Date internships end")
    sponsordetails = RichTextField(default='<p>Outreachy is hosted by the <a href="https://sfconservancy.org/">Software Freedom Conservancy</a> with special support from Red Hat, GNOME, and <a href="http://otter.technology">Otter Tech</a>. We invite companies and free and open source communities to sponsor internships in the next round.</p>')

    content_panels = Page.content_panels + [
        FieldPanel('roundnumber'),
        FieldPanel('applicationsopendate'),
        FieldPanel('internshipstartdate'),
        FieldPanel('internshipenddate'),
        FieldPanel('sponsordetails', classname="full"),
    ]
