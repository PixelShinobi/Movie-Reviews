from django.contrib import admin
from .models import Movie, MovieProfile, Review, Watchlist




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


class ReviewAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Review Information', {
            'fields': ['user', 'movie', 'rating', 'comment']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']  # Collapsible section
        }),
    ]
    list_display = ['movie', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at', 'movie']
    search_fields = ['user__username', 'movie__name', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'movie__name']
    readonly_fields = ['added_at']
    ordering = ['-added_at']


admin.site.register(Movie, MovieAdmin)
admin.site.register(MovieProfile, MovieProfileAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Watchlist, WatchlistAdmin)
