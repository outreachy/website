from .views import community_cfp_view
from .views import community_read_only_view
from django.conf.urls import url

urlpatterns = [
    url(r'^communities/cfp/(?P<slug>[^/]+)/$', community_read_only_view, name='community-read-only'),
    url(r'^communities/cfp/$', community_cfp_view, name='community-cfp'),
]
