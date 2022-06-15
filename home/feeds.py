from collections import namedtuple
import datetime
from django.contrib.auth.models import User
from django.contrib.syndication.views import Feed
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils.feedgenerator import Atom1Feed
import operator
from pytz import timezone


class FullHistoryFeed(Atom1Feed):
    """
    Use this feed type when your feed contains an entry for every post
    ever, rather than cutting off after the most recent 10. This
    generator adds the <fh:complete/> tag specified in RFC5005 ("Feed
    Paging and Archiving"), section 2 ("Complete Feeds").
    """

    def root_attributes(self):
        attrs = super(FullHistoryFeed, self).root_attributes()
        attrs['xmlns:fh'] = 'http://purl.org/syndication/history/1.0'
        return attrs

    def add_root_elements(self, handler):
        super(FullHistoryFeed, self).add_root_elements(handler)
        handler.addQuickElement('fh:complete')


PseudoPage = namedtuple('PseudoPage', [
    'title',
    'full_url',
    'owner',
    'first_published_at',
    'last_published_at',
])
PseudoPage.__doc__ = "Just enough like Wagtail's Page model to work as an item of a WagtailFeed."


class WagtailFeed(Feed):
    feed_type = FullHistoryFeed

    def get_object(self, request, page):
        return page

    def title(self, obj):
        return obj.title

    def link(self, obj):
        return obj.full_url

    def items(self, obj):
        items = list(obj.get_children().live())

        # add special posts that aren't stored as Wagtail pages

        staff = User.objects.filter(is_staff=True, comrade__isnull=False)
        try:
            author = staff.get(username='sage')
        except User.DoesNotExist:
            author = staff[0]

        pacific = timezone('US/Pacific')

        # Append blog pages created with Django here.
        # Append the newest blog post last.
        #
        # These blog posts will automatically show up in the RSS feed,
        # and show up on the blog index page
        # https://www.outreachy.org/blog/
        # Unfortunately, that page created in the Wagtail Outreachy website database.
        # That means that it will show up as a 404 if you access localhost:8000/blog/
        # You'll have to push this code to the test website to check it.
        #
        # TODO: FIXME: Move all blog posts from Wagtail into Django templates,
        # and stop using a Wagtail page.
        items.append(PseudoPage(
            title='Schedule changes for Outreachy',
            full_url=reverse('blog-schedule-changes'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2019, 7, 23, 15, 5, 1)),
            last_published_at=pacific.localize(datetime.datetime(2019, 7, 24, 16, 5, 38)),
        ))

        items.append(PseudoPage(
            title='Picking an Outreachy Project - December 2019 round',
            full_url=reverse('2019-12-pick-a-project'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2019, 10, 1, 7, 26, 0)),
            last_published_at=pacific.localize(datetime.datetime(2019, 10, 4, 12, 49, 0)),
        ))
        items.append(PseudoPage(
            title='Projects that need more applicants - December 2019 round',
            full_url=reverse('2019-12-project-promotion'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2019, 10, 17, 17, 38, 0)),
            last_published_at=pacific.localize(datetime.datetime(2019, 10, 17, 17, 38, 0)),
        ))
        items.append(PseudoPage(
            title='Outreachy response to COVID-19',
            full_url=reverse('2020-03-covid'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2020, 3, 27, 16, 00, 0)),
            last_published_at=pacific.localize(datetime.datetime(2020, 5, 1, 16, 00, 0)),
        ))
        items.append(PseudoPage(
            title='December 2020 internship applications open',
            full_url=reverse('2020-08-initial-apps-open'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2020, 8, 28, 9, 00, 0)),
            last_published_at=pacific.localize(datetime.datetime(2020, 8, 28, 9, 00, 0)),
        ))
        items.append(PseudoPage(
            title='Call for May 2021 mentoring communities',
            full_url=reverse('2021-01-community-cfp-open'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2021, 1, 15, 11, 00, 0)),
            last_published_at=pacific.localize(datetime.datetime(2021, 1, 15, 11, 00, 0)),
        ))
        items.append(PseudoPage(
            title='Initial applications open for May 2021 internships',
            full_url=reverse('2021-01-initial-applications-open'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2021, 2, 1, 14, 00, 0)),
            last_published_at=pacific.localize(datetime.datetime(2021, 2, 1, 14, 00, 0)),
        ))
        items.append(PseudoPage(
            title='Outreachy bars FSF from participation in its program',
            full_url=reverse('2021-03-fsf-participation-barred'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2021, 3, 23, 14, 00, 0)),
            last_published_at=pacific.localize(datetime.datetime(2021, 3, 23, 14, 00, 0)),
        ))
        items.append(PseudoPage(
            title='Outreachy May 2021 contribution period open',
            full_url=reverse('2021-03-contribution-period-open'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2021, 3, 30, 16, 00, 0)),
            last_published_at=pacific.localize(datetime.datetime(2021, 3, 30, 16, 00, 0)),
        ))
        items.append(PseudoPage(
            title='Outreachy December 2021 internship applications open',
            full_url=reverse('2021-08-initial-applications-open'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2021, 8, 13, 16, 00, 0)),
            last_published_at=pacific.localize(datetime.datetime(2021, 8, 18, 16, 00, 0)),
        ))
        items.append(PseudoPage(
            title='Call for December 2021 mentoring communities',
            full_url=reverse('2021-08-cfp-open'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2021, 8, 18, 16, 00, 0)),
            last_published_at=pacific.localize(datetime.datetime(2021, 8, 18, 16, 00, 0)),
        ))
        items.append(PseudoPage(
            title='Hiring for an Outreachy community manager',
            full_url=reverse('2021-10-outreachy-hiring'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2021, 10, 14, 17, 25, 0)),
            last_published_at=pacific.localize(datetime.datetime(2021, 10, 15, 16, 20, 0)),
        ))
        items.append(PseudoPage(
            title='Call for May 2022 mentoring communities',
            full_url=reverse('2022-01-cfp-open'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2022, 1, 10, 16, 00, 0)),
            last_published_at=pacific.localize(datetime.datetime(2021, 1, 10, 16, 00, 0)),
        ))
        items.append(PseudoPage(
            title='Outreachy May 2022 internship applications',
            full_url=reverse('2022-02-initial-applications-open'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2022, 2, 4, 16, 00, 0)),
            last_published_at=pacific.localize(datetime.datetime(2022, 2, 4, 16, 00, 0)),
        ))
        items.append(PseudoPage(
            title='Outreachy welcomes new community manager',
            full_url=reverse('2022-04-new-community-manager'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2022, 4, 15, 16, 00, 0)),
            last_published_at=pacific.localize(datetime.datetime(2022, 4, 15, 16, 00, 0)),
        ))
        items.append(PseudoPage(
            title='Remembering and Honoring Marina Zhurakhinskaya, Founder of Outreachy',
            full_url=reverse('2022-06-remembering-marina'),
            owner=author,
            first_published_at=pacific.localize(datetime.datetime(2022, 6, 15, 3, 00, 0)),
            last_published_at=pacific.localize(datetime.datetime(2022, 6, 15, 14, 00, 0)),
        ))

        # put the Wagtail pages and special posts together in the right order
        items.sort(key=operator.attrgetter('first_published_at'), reverse=True)
        return items

    def item_title(self, item):
        return item.title

    item_description = None

    def item_link(self, item):
        return item.full_url

    def item_author_name(self, item):
        try:
            return item.owner.comrade.public_name
        except ObjectDoesNotExist:
            return None

    def item_pubdate(self, item):
        return item.first_published_at

    def item_updateddate(self, item):
        return item.last_published_at
