from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.db.models import Min, Max, Avg, Count
from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Movie, MovieProfile
from .forms import AddMovieForm, UpdateMovieForm

def orm_exercise(request):
    # 1. Fetch all rows, queryset of all movies
    all_movies = Movie.objects.all()

    # 2. Print the SQL query formed by ORM
    query_sql = str(all_movies.query)

    # 3. Fetch first 5 rows only
    first_5 = Movie.objects.all()[:5]

    # 4. Fetch rows from 5 to 9 (index 4 to 8)
    rows_5_to_9 = Movie.objects.all()[4:9]

    # 5. Count of rows 
    total_count = Movie.objects.count()

    # 6. Filter Movies with "Movie" in the name
    movies_with_movie = Movie.objects.filter(name__icontains='Movie')

    # 7. Filter Movies with duration more than 150 minutes
    duration_more_150 = Movie.objects.filter(duration__gt=150)

    # 8. Filter Movies with duration > 150 and THEATER delivery mode
    theater_long = Movie.objects.filter(duration__gt=150, delivery_mode='THEATER')

    # 9. Filter Movies with duration < 150 and STREAMING delivery mode
    streaming_short = Movie.objects.filter(duration__lt=150, delivery_mode='STREAMING')

    # 10. Min and max duration of movies starring "Leonardo DiCaprio"
    leo_min_max = Movie.objects.filter(actor='Leonardo DiCaprio').aggregate(
        min_duration=Min('duration'),
        max_duration=Max('duration')
    )

    # 11. Average duration of movies starring "Leonardo DiCaprio"
    leo_avg = Movie.objects.filter(actor='Leonardo DiCaprio').aggregate(
        avg_duration=Avg('duration')
    )

    # 12. Count of movies starring "Leonardo DiCaprio"
    leo_count = Movie.objects.filter(actor='Leonardo DiCaprio').count()

    # 13. Min and max duration of movies NOT starring "Leonardo DiCaprio"
    not_leo_min_max = Movie.objects.exclude(actor='Leonardo DiCaprio').aggregate(
        min_duration=Min('duration'),
        max_duration=Max('duration')
    )

    # 14. Average duration of movies NOT starring "Leonardo DiCaprio"
    not_leo_avg = Movie.objects.exclude(actor='Leonardo DiCaprio').aggregate(
        avg_duration=Avg('duration')
    )

    # 15. Count of movies NOT starring "Leonardo DiCaprio"
    not_leo_count = Movie.objects.exclude(actor='Leonardo DiCaprio').count()

    # 16. Min and max duration of movies starring either "Robert Downey Jr" or "Matthew McConaughey"
    rdj_mm_min_max = Movie.objects.filter(
        Q(actor='Robert Downey Jr') | Q(actor='Matthew McConaughey')
    ).aggregate(
        min_duration=Min('duration'),
        max_duration=Max('duration')
    )

    # 17. Average duration of movies starring either "Robert Downey Jr" or "Matthew McConaughey"
    rdj_mm_avg = Movie.objects.filter(
        Q(actor='Robert Downey Jr') | Q(actor='Matthew McConaughey')
    ).aggregate(
        avg_duration=Avg('duration')
    )

    # 18. Count of movies starring either "Robert Downey Jr" or "Matthew McConaughey"
    rdj_mm_count = Movie.objects.filter(
        Q(actor='Robert Downey Jr') | Q(actor='Matthew McConaughey')
    ).count()

    # 19. Count of movies per actor, along with the actor's name
    movies_per_actor = Movie.objects.values('actor').annotate(
        movie_count=Count('id')
    ).order_by('-movie_count')

    # 20. Min and max duration of a movie for each actor, along with the actor's name
    actor_duration_min_max = Movie.objects.values('actor').annotate(
        min_duration=Min('duration'),
        max_duration=Max('duration')
    ).order_by('actor')

    # 21. Max duration of a movie for each actor, and display the actor's name as well
    actor_max_duration = Movie.objects.values('actor').annotate(
        max_duration=Max('duration')
    ).order_by('-max_duration')

    # context dictionary to pass to template
    context = {
        'all_movies': all_movies,
        'query_sql': query_sql,
        'first_5': first_5,
        'rows_5_to_9': rows_5_to_9,
        'total_count': total_count,
        'movies_with_movie': movies_with_movie,
        'duration_more_150': duration_more_150,
        'theater_long': theater_long,
        'streaming_short': streaming_short,
        'leo_min_max': leo_min_max,
        'leo_avg': leo_avg,
        'leo_count': leo_count,
        'not_leo_min_max': not_leo_min_max,
        'not_leo_avg': not_leo_avg,
        'not_leo_count': not_leo_count,
        'rdj_mm_min_max': rdj_mm_min_max,
        'rdj_mm_avg': rdj_mm_avg,
        'rdj_mm_count': rdj_mm_count,
        'movies_per_actor': movies_per_actor,
        'actor_duration_min_max': actor_duration_min_max,
        'actor_max_duration': actor_max_duration,
    }

    return render(request, 'movies/orm_exercise.html', context)









# Movie List View - Home page for forms
@login_required
def movie_list(request):
    movies = Movie.objects.all().order_by('-release_date')

    # Pagination: 6 movies per page
    paginator = Paginator(movies, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Cookie handling: Get view mode from URL or cookie
    view_mode = request.GET.get('view')  # Check URL first and see if we can get view mode from there, when we click the button
    if not view_mode:            
        view_mode = request.COOKIES.get('view_mode', 'grid')  # if url didn't specify view mode, which is when we just entered movie list page. check cookie value, if cookie value is empty too, default to grid

    context = {
        'page_obj': page_obj,
        'view_mode': view_mode
    }

    # Set cookie in response
    response = render(request, 'movies/movie_list.html', context)

    response.set_cookie('view_mode', view_mode, max_age=30*24*60*60)  # set cookie with current view mode, expires in 30 days
    return response


# Add Movie View - Using CreateView (ClassView)
class MovieCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Movie
    form_class = AddMovieForm
    template_name = 'movies/add_movie.html'
    success_url = reverse_lazy('movies:movie_list')

    def test_func(self):
        # Only staff/admin users can create movies
        return self.request.user.is_staff  # if test fails, returns 403 Forbidden

    @transaction.atomic
    def form_valid(self, form):
        # Save the movie first (signal will create profile automatically)
        self.object = form.save()  # Manual save

        # Update the profile with additional fields
        profile = self.object.profile
        profile.is_featured = form.cleaned_data.get('is_featured', False)
        profile.is_trending = form.cleaned_data.get('is_trending', False)
        if form.cleaned_data.get('poster_image'):
            profile.poster_image = form.cleaned_data.get('poster_image')
        profile.save()

        return HttpResponseRedirect(self.get_success_url())  


# Update Movie View - Using UpdateView (ClassView)
class MovieUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Movie
    form_class = UpdateMovieForm
    template_name = 'movies/update_movie.html'
    success_url = reverse_lazy('movies:movie_list')

    def test_func(self):
        # Only staff/admin users can update movies
        return self.request.user.is_staff

    def get_initial(self):
        # Pre-populate form with existing profile data
        initial = super().get_initial()
        if hasattr(self.object, 'profile'):
            initial['is_featured'] = self.object.profile.is_featured
            initial['is_trending'] = self.object.profile.is_trending
        return initial

    @transaction.atomic
    def form_valid(self, form):
        # Save the movie first
        self.object = form.save()

        # Update the profile with additional fields
        profile = self.object.profile
        profile.is_featured = form.cleaned_data.get('is_featured', False)
        profile.is_trending = form.cleaned_data.get('is_trending', False)
        if form.cleaned_data.get('poster_image'):
            profile.poster_image = form.cleaned_data.get('poster_image')
        profile.save()

        return HttpResponseRedirect(self.get_success_url())  


# Delete Movie View - Using DeleteView (ClassView)
class MovieDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Movie
    template_name = 'movies/delete_movie.html'
    success_url = reverse_lazy('movies:movie_list')

    def test_func(self):
        # Only staff/admin users can delete movies
        return self.request.user.is_staff




# Authentication Views

# Register View - User Registration
class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'movies/register.html'
    success_url = reverse_lazy('movies:login')  # Redirect to login page after registration







#http://localhost:8000/templates/

#http://localhost:8000/admin/

# TESTING BLOCKING/PERMISSIONS:
# 1. Anonymous (not logged in) - Try: http://127.0.0.1:8000/movies/movie-database/  (will Redirects to login)
# 2. Regular user (non-staff) - Try: http://127.0.0.1:8000/movies/movie-database/add/  (403 Forbidden)



'''
Admin
user: admin 
Email: admin@example.com
password: admin123




Regular user
user: user1
password: user123





'''