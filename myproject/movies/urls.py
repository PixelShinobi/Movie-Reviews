from django.urls import path
from django.contrib.auth.views import LogoutView
from rest_framework.authtoken.views import obtain_auth_token
from . import views

app_name = 'movies'

urlpatterns = [
    # Authentication URLs
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Movie Database - list all movies
    path('movie-database/', views.movie_list, name='movie_list'),

    # CRUD operations - Class-Based Views
    path('movie-database/add/', views.MovieCreateView.as_view(), name='add_movie'),
    path('movie-database/update/<int:pk>/', views.MovieUpdateView.as_view(), name='update_movie'),
    path('movie-database/delete/<int:pk>/', views.MovieDeleteView.as_view(), name='delete_movie'),

    # Movie Detail and Reviews
    path('movie-database/<int:pk>/', views.movie_detail, name='movie_detail'),
    path('reviews/delete/<int:pk>/', views.delete_review, name='delete_review'),

    # Watchlist
    path('watchlist/', views.watchlist_page, name='watchlist'),
    path('watchlist/toggle/<int:pk>/', views.toggle_watchlist, name='toggle_watchlist'),

    # REST API endpoints - Movie operations
    path('api/movies/', views.MovieListCreateAPIView.as_view(), name='api_movie_list'),
    path('api/movies/<int:pk>/', views.MovieRetrieveUpdateDestroyAPIView.as_view(), name='api_movie_detail'),

    # REST API endpoints - Authentication
    path('api/auth/register/', views.APIRegisterView.as_view(), name='api_register'),
    path('api/auth/login/', obtain_auth_token, name='api_login'),
    path('api/auth/logout/', views.APILogoutView.as_view(), name='api_logout'),

    # REST API endpoints - Reviews
    path('api/movies/<int:movie_id>/reviews/', views.ReviewListCreateAPIView.as_view(), name='api_review_list'),
    path('api/reviews/<int:pk>/', views.ReviewRetrieveUpdateDestroyAPIView.as_view(), name='api_review_detail'),
]


