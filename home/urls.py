from .views import community_cfp_view
from django.conf.urls import url

urlpatterns = [
    url(r'^communities/cfp/$', community_cfp_view, name='community-cfp'),
]
