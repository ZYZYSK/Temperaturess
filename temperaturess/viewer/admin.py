from django.contrib import admin
from viewer.models import TimeData, DayData, NormalData
# Register your models here.

admin.site.register(TimeData)
admin.site.register(DayData)
admin.site.register(NormalData)
