from .views import community_cfp_view
from .views import community_read_only_view
from .views import community_landing_view
from django.conf.urls import url

urlpatterns = [
    url(r'^communities/cfp/(?P<slug>[^/]+)/$', community_read_only_view, name='community-read-only'),
    url(r'^communities/(?P<slug>[^/]+)/$', community_landing_view, {'gsoc': False}, name='community-landing'),
    url(r'^communities/(?P<slug>[^/]+)/gsoc/$', community_landing_view, {'gsoc': True}, name='community-landing-gsoc'),
    url(r'^communities/cfp/$', community_cfp_view, name='community-cfp'),
]
