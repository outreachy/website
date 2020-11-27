from django.shortcuts import render


def server_error(request):
    # use the "errorsafe" engine from settings.TEMPLATES
    return render(request, "500.html", status=500, using="errorsafe")
