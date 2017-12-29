from django.contrib import admin
from .models import Community
from .models import Participation
from .models import RoundPage
from .models import Project

admin.site.register(Community)
admin.site.register(Participation)
admin.site.register(RoundPage)
admin.site.register(Project)
