from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.utils import timezone
from .models import Movie, MovieProfile
from .forms import AddMovieForm, UpdateMovieForm
from .decorators import token_required
from .auth_utils import create_token


# Movie List View - Home page for forms
@token_required
def movie_list(request):
    movies = Movie.objects.all().order_by('-release_date')

    # Pagination: 6 movies per page
    paginator = Paginator(movies, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Cookie handling: Get view mode from URL or cookie
    view_mode = request.GET.get('view')
    if not view_mode:
        view_mode = request.COOKIES.get('view_mode', 'grid')

    context = {
        'page_obj': page_obj,
        'view_mode': view_mode
    }

    # Set cookie in response
    response = render(request, 'movies/movie_list.html', context)
    response.set_cookie('view_mode', view_mode, max_age=30*24*60*60)
    return response


# Add Movie View - Using CreateView (ClassView)
class MovieCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Movie
    form_class = AddMovieForm
    template_name = 'movies/add_movie.html'
    success_url = reverse_lazy('movies:movie_list')

    def test_func(self):
        return self.request.user.is_staff

    @transaction.atomic     # ensure both Movie and MovieProfile are created atomically, if one fails, both fail
    def form_valid(self, form):
        self.object = form.save()

        # Update profile
        profile = self.object.profile
        profile.is_featured = form.cleaned_data.get('is_featured', False)
        profile.is_trending = form.cleaned_data.get('is_trending', False)
        if form.cleaned_data.get('poster_image'):
            profile.poster_image = form.cleaned_data.get('poster_image')
        profile.save()

        messages.success(self.request, f"Movie '{self.object.name}' added successfully to the catalog!")
        return HttpResponseRedirect(self.get_success_url())


# Update Movie View - Using UpdateView (ClassView)
class MovieUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Movie
    form_class = UpdateMovieForm
    template_name = 'movies/update_movie.html'
    success_url = reverse_lazy('movies:movie_list')

    def test_func(self):
        return self.request.user.is_staff

    def get_initial(self):
        initial = super().get_initial()
        if hasattr(self.object, 'profile'):
            initial['is_featured'] = self.object.profile.is_featured
            initial['is_trending'] = self.object.profile.is_trending
        return initial

    @transaction.atomic
    def form_valid(self, form):
        self.object = form.save()

        # Update profile
        profile = self.object.profile
        profile.is_featured = form.cleaned_data.get('is_featured', False)
        profile.is_trending = form.cleaned_data.get('is_trending', False)
        if form.cleaned_data.get('poster_image'):
            profile.poster_image = form.cleaned_data.get('poster_image')
        profile.save()

        messages.info(self.request, f"Movie '{self.object.name}' has been updated!")
        return HttpResponseRedirect(self.get_success_url())


# Delete Movie View - Using DeleteView (ClassView)
class MovieDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Movie
    template_name = 'movies/delete_movie.html'
    success_url = reverse_lazy('movies:movie_list')

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        movie_name = self.get_object().name
        response = super().delete(request, *args, **kwargs)
        messages.warning(request, f"Movie '{movie_name}' has been deleted from the catalog")
        return response


# Authentication Views
class CustomLoginView(DjangoLoginView):
    template_name = 'movies/login.html'

    def form_valid(self, form):
        response = super().form_valid(form)   

        # Create and save token
        token = create_token(self.request.user.id)
        self.request.session['auth_token'] = token                           # save token in session
        self.request.session['token_created'] = timezone.now().isoformat()
        response.set_cookie('auth_token', token, max_age=60*60)              # also save token in cookie for 1 hour

        messages.success(self.request, f"Welcome back, {self.request.user.username}!")
        return response


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'movies/register.html'
    success_url = reverse_lazy('movies:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(self.request, "Registration successful! Please login to continue")
        return response


# Testing Links:
# Home: http://127.0.0.1:8000/
# Login: http://127.0.0.1:8000/movies/login/
# Register: http://127.0.0.1:8000/movies/register/
# Movie Database: http://127.0.0.1:8000/movies/movie-database/
# Add Movie: http://127.0.0.1:8000/movies/movie-database/add/
# Admin: http://127.0.0.1:8000/admin/
