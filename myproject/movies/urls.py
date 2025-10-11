from django.urls import path
from django.contrib.auth.views import LogoutView
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
]


