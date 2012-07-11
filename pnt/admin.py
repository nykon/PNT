from models import *
from django.contrib import admin


class HipChemTakenAdmin(admin.ModelAdmin):
    list_display = ('casehistory', 'hipotension_chemical')
    search_fields = ('casehistory__patient__last_name',)


admin.site.register(Patient)
admin.site.register(Address)
admin.site.register(Disease)
admin.site.register(CaseHistory)
admin.site.register(HipotensionChemical)
admin.site.register(HipotensionChemicalTaken, HipChemTakenAdmin)
admin.site.register(PharmaGroup)
admin.site.register(ChemicalInternationalType)
admin.site.register(Etiology)
admin.site.register(Meal)
admin.site.register(Appointment)



