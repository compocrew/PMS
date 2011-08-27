from django.contrib import admin

from models import Schedule,Event

#class ScheduleInline(admin.StackedInline):
#    model = Schedule.events.through
#    extra = 1

#class EventAdmin(admin.ModelAdmin):
#    inlines = [ScheduleInline]

admin.site.register(Schedule)
admin.site.register(Event)
#admin.site.register(Event, EventAdmin)
