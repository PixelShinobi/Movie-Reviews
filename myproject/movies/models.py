from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
import os

class Movie(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    actor = models.CharField(max_length=100)  # Main actor
    duration = models.IntegerField()  # Duration in minutes
    delivery_mode = models.CharField(max_length=20)  # THEATER or STREAMING
    keywords = models.CharField(max_length=200)  # Movie genre/type
    release_date = models.DateField()

    def __str__(self):
        return self.name


class MovieProfile(models.Model):
    #Extended profile for Movie with additional data and poster image
    poster_image = models.ImageField(upload_to='movie_posters/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE, related_name='profile') # Link movieprofile to Movie

    def __str__(self):
        return f"{self.movie.name} Profile"


# Signals
@receiver(post_save, sender=Movie)
def create_movie_profile(sender, instance, created, **kwargs):
    #Automatically create MovieProfile when Movie is created
 
    if created: # new movie, create profile
        MovieProfile.objects.create(movie=instance)
    else: 
        instance.profile.save() # updating old movies, just save profile



@receiver(pre_delete, sender=Movie)
def delete_movie_poster(sender, instance, **kwargs):
    #Delete poster image file when movie is deleted
    try:
        if instance.profile.poster_image:
            instance.profile.poster_image.delete(save=False)

    except:
        pass  # No profile or no image, skip

