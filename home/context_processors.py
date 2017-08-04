from wagtail.wagtailcore.models import Page

def headerpages(request):
    return { 'header_pages': Page.objects.live().in_menu() }
