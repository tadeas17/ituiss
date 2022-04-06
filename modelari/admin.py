from django.contrib import admin
from .models import Competition, CompetitionMiniatureCategory, CompetitionType, Miniature, MiniatureType, MiniatureRegistration, Person

# Register your models here.
admin.site.register(Miniature)
admin.site.register(MiniatureType)
admin.site.register(Competition)
admin.site.register(CompetitionMiniatureCategory)
admin.site.register(CompetitionType)
admin.site.register(Person)
admin.site.register(MiniatureRegistration)