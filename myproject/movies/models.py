from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
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

    def get_average_rating(self):
        """Calculate average rating for this movie"""
        reviews = self.reviews.all()
        if reviews.exists():
            total = sum(review.rating for review in reviews)
            return round(total / reviews.count(), 1)
        return 0

    def get_review_count(self):
        """Get total number of reviews for this movie"""
        return self.reviews.count()


class MovieProfile(models.Model):
    #Extended profile for Movie with additional data and poster image
    poster_image = models.ImageField(upload_to='movie_posters/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE, related_name='profile') # Link movieprofile to Movie

    def __str__(self):
        return f"{self.movie.name} Profile"


class Review(models.Model):
    """User reviews for movies with rating and comments"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(help_text="Your review comment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Newest reviews first
        unique_together = ['user', 'movie']  # One review per user per movie

    def __str__(self):
        return f"{self.user.username}'s review of {self.movie.name} ({self.rating}/5)"


class Watchlist(models.Model):
    """User's watchlist/favorites for movies"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='watchlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']  # Most recently added first
        unique_together = ['user', 'movie']  # One entry per user per movie

    def __str__(self):
        return f"{self.user.username}'s watchlist: {self.movie.name}"


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

