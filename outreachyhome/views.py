from django.shortcuts import render


def server_error(request):
    # use the "errorsafe" engine from settings.TEMPLATES
    return render(request, "500.html", status=500, using="errorsafe")

def applicant_faq(request):
    return render(request, "home/docs/applicant_faq.html")