from django import forms
from .models import Movie, MovieProfile


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
