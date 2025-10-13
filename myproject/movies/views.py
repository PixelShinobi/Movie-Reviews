from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.utils import timezone
from rest_framework import generics, mixins, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.authtoken.models import Token
from .models import Movie, MovieProfile
from .forms import AddMovieForm, UpdateMovieForm
from .decorators import token_required
from .auth_utils import create_token
from .serializers import MovieSerializer, UserSerializer
from .permissions import IsStaffOrReadOnly


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
        self.request.session['auth_token'] = token                           # save token in session, record time created
        self.request.session['token_created'] = timezone.now().isoformat()
        response.set_cookie('auth_token', token, max_age=60*60)              # also save token in cookie for 1 hour

        messages.success(self.request, f"Welcome back, {self.request.user.username}!")
        return response


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'movies/register.html'
    success_url = reverse_lazy('movies:login')








# ====================================
# REST API Views
# ====================================

# Using Concrete View Class, for list all movies and create new movie
class MovieListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all movies
    POST: Create new movie
    Uses: Concrete View Class (ListCreateAPIView)
    Permission: IsAuthenticated (from application-level default)
    """
    queryset = Movie.objects.all().order_by('-release_date')
    serializer_class = MovieSerializer
    # Permission: Uses default IsAuthenticated from settings


# Using GenericAPIView + Mixins, for retrieve, update, delete single movie
class MovieRetrieveUpdateDestroyAPIView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView
):
    """
    GET: Retrieve single movie
    PUT: Update movie
    DELETE: Delete movie
    Uses: GenericAPIView + RetrieveModelMixin + UpdateModelMixin + DestroyModelMixin
    Permission: IsStaffOrReadOnly (custom permission, overrides default)
    """
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [IsStaffOrReadOnly]  # View-specific permission (overrides default one that's in settings)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)








# API Authentication Views

class APIRegisterView(APIView):
    """
    POST: Register a new user and return auth token
    Permission: AllowAny (anyone can register)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Create token for the new user
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class APILogoutView(APIView):
    """
    POST: Logout user and delete auth token
    Permission: IsAuthenticated (must be logged in to logout)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Delete user's token
        request.user.auth_token.delete()
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)





# Testing Links:
# Home: http://127.0.0.1:8000/
# Login: http://127.0.0.1:8000/movies/login/
# Register: http://127.0.0.1:8000/movies/register/
# Movie Database: http://127.0.0.1:8000/movies/movie-database/
# Add Movie: http://127.0.0.1:8000/movies/movie-database/add/
# Admin: http://127.0.0.1:8000/admin/









# 1. REGISTER - Get your token
# POST http://127.0.0.1:8000/movies/api/auth/register/
# Body: {"username": "testuser", "password": "test123", "password2": "test123"}
# Response: {"token": "abc123...", "user": {...}}  ← SAVE THIS TOKEN!

# 2. LOGIN (alternative)
# POST http://127.0.0.1:8000/movies/api/auth/login/
# Body: {"username": "testuser", "password": "test123"}
# Response: {"token": "abc123..."}

# 3. GET ALL MOVIES
# GET http://127.0.0.1:8000/movies/api/movies/
# Headers: Authorization: Token abc123...

# 4. CREATE MOVIE
# POST http://127.0.0.1:8000/movies/api/movies/
# Headers: Authorization: Token abc123...
# Body: {"name": "Inception", "description": "...", "actor": "Leonardo DiCaprio",
#        "duration": 148, "delivery_mode": "THEATER", "keywords": "Sci-Fi",
#        "release_date": "2010-07-16"}

# 5. GET SINGLE MOVIE
# GET http://127.0.0.1:8000/movies/api/movies/1/
# Headers: Authorization: Token abc123...

# 6. UPDATE MOVIE (staff only)
# PUT http://127.0.0.1:8000/movies/api/movies/1/
# Headers: Authorization: Token abc123...
# Body: Same as CREATE

# 7. DELETE MOVIE (staff only)
# DELETE http://127.0.0.1:8000/movies/api/movies/1/
# Headers: Authorization: Token abc123...

# 8. LOGOUT
# POST http://127.0.0.1:8000/movies/api/auth/logout/
# Headers: Authorization: Token abc123...

# SESSION AUTH: Login via browser, then use Postman with cookies (no Token header needed)

# PERMISSIONS:
# - Application-level: IsAuthenticated (must login for all APIs)
# - MovieListCreateAPIView: IsAuthenticated
# - MovieRetrieveUpdateDestroyAPIView: IsStaffOrReadOnly (read=anyone, write=staff only)
# - Register/Logout: AllowAny/IsAuthenticated

# VIEW TYPES:
# - MovieListCreateAPIView: Concrete View Class (ListCreateAPIView)
# - MovieRetrieveUpdateDestroyAPIView: GenericAPIView + Mixins
