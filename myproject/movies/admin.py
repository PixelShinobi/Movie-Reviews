from django.contrib import admin
from .models import Movie, MovieProfile




# Fieldsets for admin interface

class MovieAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Movie Information', {
            'fields': ['name', 'description', 'actor', 'duration', 'delivery_mode', 'keywords', 'release_date']
        }),
    ]
    list_display = ['name', 'actor', 'duration', 'delivery_mode', 'release_date']


class MovieProfileAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Profile Settings', {
            'fields': ['movie', 'poster_image', 'is_featured', 'is_trending']
        }),
    ]
    list_display = ['movie', 'is_featured', 'is_trending']


admin.site.register(Movie, MovieAdmin)
admin.site.register(MovieProfile, MovieProfileAdmin)
