from django.conf import settings
from django.urls import include, re_path
from django.contrib import admin

from wagtail.admin import urls as wagtailadmin_urls
import debug_toolbar
from home import urls as home_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from contacts import urls as contacts_urls

from . import views as project_views
from search import views as search_views

urlpatterns = [
    re_path(r'^__debug__/', include(debug_toolbar.urls)),
    re_path(r'^django-admin/', admin.site.urls),

    re_path(r'^admin/', include(wagtailadmin_urls)),
    re_path(r'^documents/', include(wagtaildocs_urls)),

    re_path(r'^search/$', search_views.search, name='search'),
    re_path(r'^contact/', include(contacts_urls)),

    # https://docs.djangoproject.com/en/1.11/topics/auth/default/#using-the-views
    re_path(r'', include('django.contrib.auth.urls')),

    re_path(r'', include(home_urls)),

    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    re_path(r'', include(wagtail_urls)),

    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    re_path(r'^pages/', include(wagtail_urls)),
]

handler500 = project_views.server_error


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.conf import settings
    from django.urls import include, re_path

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
