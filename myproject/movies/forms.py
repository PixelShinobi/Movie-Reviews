from django import forms
from .models import Movie, MovieProfile, Review


# 1. ModelForm - for adding movies (includes MovieProfile fields)
class AddMovieForm(forms.ModelForm):
    # MovieProfile fields
    poster_image = forms.ImageField(required=False, label='Movie Poster')
    is_featured = forms.BooleanField(required=False, label='Feature this movie')
    is_trending = forms.BooleanField(required=False, label='Mark as trending')

    class Meta:
        model = Movie
        fields = ['name', 'description', 'actor', 'duration', 'delivery_mode', 'keywords', 'release_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'release_date': forms.DateInput(attrs={'type': 'date'}),
        }


# 2. ModelForm - for updating movies (includes MovieProfile fields)
class UpdateMovieForm(forms.ModelForm):
    # MovieProfile fields
    poster_image = forms.ImageField(required=False, label='Movie Poster')
    is_featured = forms.BooleanField(required=False, label='Feature this movie')
    is_trending = forms.BooleanField(required=False, label='Mark as trending')

    class Meta:
        model = Movie
        fields = ['name', 'description', 'actor', 'duration', 'delivery_mode', 'keywords', 'release_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'release_date': forms.DateInput(attrs={'type': 'date'}),
        }


# 3. ModelForm - for adding reviews
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your thoughts about this movie...'}),
        }
        labels = {
            'rating': 'Your Rating',
            'comment': 'Your Review',
        }
