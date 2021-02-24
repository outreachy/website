from django.conf import settings


def show_debug_toolbar(request):
    """Shows the debug toolbar based on the debug arg in the URL.

    ?debug=on - turns debugging on in the current session
    ?debug=off - turns debugging off in the current session

    Based on http://djangosnippets.org/snippets/2574/, but allowing staff to
    use it in production.
    """
    if settings.DEBUG or request.user.is_staff:
        debug = request.GET.get("debug", None)
        if debug == "on":
            request.session["debug"] = True
        elif debug == "off" and "debug" in request.session:
            del request.session["debug"]
        return "debug" in request.session
    return False
