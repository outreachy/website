from django.contrib.syndication.views import Feed
from django.core.exceptions import ObjectDoesNotExist
from django.utils.feedgenerator import Atom1Feed

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

class WagtailFeed(Feed):
    feed_type = FullHistoryFeed

    def get_object(self, request, page):
        return page

    def title(self, obj):
        return obj.title

    def link(self, obj):
        return obj.full_url

    def items(self, obj):
        return obj.get_children().live().order_by('-first_published_at')

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
