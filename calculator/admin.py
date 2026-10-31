from django.contrib import admin
from .models import Pokemon, Move, HeldItem

# This customizes the admin page to include our JavaScript
class PokemonAdmin(admin.ModelAdmin):
    class Media:
        js = ('calculator/autofill.js',)

# Register the models with the new custom Admin
admin.site.register(Pokemon, PokemonAdmin)
admin.site.register(Move)
admin.site.register(HeldItem)
from django.contrib.auth.models import Group, User
admin.site.unregister(Group)
admin.site.unregister(User)