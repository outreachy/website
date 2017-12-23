from django.contrib import admin
from .models import Community
from .models import Participation
from .models import RoundPage

admin.site.register(Community)
admin.site.register(Participation)
admin.site.register(RoundPage)
