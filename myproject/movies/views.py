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
from .models import Movie, MovieProfile, Review, Watchlist
from .forms import AddMovieForm, UpdateMovieForm, ReviewForm
from .decorators import token_required
from .auth_utils import create_token
from .serializers import MovieSerializer, UserSerializer, ReviewSerializer
from .permissions import IsStaffOrReadOnly


# Movie List View - Home page for forms
@token_required
def movie_list(request):
    from django.db.models import Avg, Count, Q

    # Get parameters
    sort_by = request.GET.get('sort', 'newest')
    search_query = request.GET.get('search', '').strip()
    delivery_mode = request.GET.get('delivery_mode', '')
    min_rating = request.GET.get('min_rating', '')
    year_from = request.GET.get('year_from', '')
    year_to = request.GET.get('year_to', '')

    # Annotate movies with average rating and review count for efficient sorting
    movies = Movie.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )

    # Apply search filter
    if search_query:
        movies = movies.filter(
            Q(name__icontains=search_query) |
            Q(actor__icontains=search_query) |
            Q(keywords__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Apply delivery mode filter
    if delivery_mode:
        movies = movies.filter(delivery_mode=delivery_mode)

    # Apply minimum rating filter
    if min_rating:
        try:
            min_rating_val = float(min_rating)
            movies = movies.filter(avg_rating__gte=min_rating_val)
        except ValueError:
            pass

    # Apply year range filter
    if year_from:
        try:
            movies = movies.filter(release_date__year__gte=int(year_from))
        except ValueError:
            pass

    if year_to:
        try:
            movies = movies.filter(release_date__year__lte=int(year_to))
        except ValueError:
            pass

    # Apply sorting based on parameter
    if sort_by == 'best_rated':
        movies = movies.order_by('-avg_rating', '-review_count')
    elif sort_by == 'worst_rated':
        movies = movies.order_by('avg_rating', '-review_count')
    elif sort_by == 'most_reviewed':
        movies = movies.order_by('-review_count', '-avg_rating')
    elif sort_by == 'least_reviewed':
        movies = movies.order_by('review_count', '-avg_rating')
    elif sort_by == 'oldest':
        movies = movies.order_by('release_date')
    else:  # Default: newest
        movies = movies.order_by('-release_date')

    # Pagination: 6 movies per page
    paginator = Paginator(movies, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Cookie handling: Get view mode from URL or cookie
    view_mode = request.GET.get('view')
    if not view_mode:
        view_mode = request.COOKIES.get('view_mode', 'grid')

    # Get unique years for year filter dropdown
    from datetime import datetime
    current_year = datetime.now().year
    years = range(1900, current_year + 1)

    # Get watchlist movie IDs for current user
    watchlist_movie_ids = []
    if request.user.is_authenticated:
        watchlist_movie_ids = list(Watchlist.objects.filter(user=request.user).values_list('movie_id', flat=True))

    context = {
        'page_obj': page_obj,
        'view_mode': view_mode,
        'current_sort': sort_by,
        'search_query': search_query,
        'delivery_mode': delivery_mode,
        'min_rating': min_rating,
        'year_from': year_from,
        'year_to': year_to,
        'years': years,
        'total_results': paginator.count,
        'watchlist_movie_ids': watchlist_movie_ids,
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


# Movie Detail View - Show movie details with reviews
@token_required
def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    reviews = movie.reviews.all()
    user_review = None
    in_watchlist = False

    # Check if current user has already reviewed this movie and if it's in watchlist
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
        in_watchlist = Watchlist.objects.filter(user=request.user, movie=movie).exists()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to submit a review")
            return redirect('movies:login')

        form = ReviewForm(request.POST)
        if form.is_valid():
            # Check if user already has a review
            if user_review:
                # Update existing review
                user_review.rating = form.cleaned_data['rating']
                user_review.comment = form.cleaned_data['comment']
                user_review.save()
                messages.success(request, "Your review has been updated!")
            else:
                # Create new review
                review = form.save(commit=False)
                review.user = request.user
                review.movie = movie
                review.save()
                messages.success(request, "Your review has been submitted!")
            return redirect('movies:movie_detail', pk=pk)
    else:
        # Pre-fill form if user has existing review
        if user_review:
            form = ReviewForm(instance=user_review)
        else:
            form = ReviewForm()

    context = {
        'movie': movie,
        'reviews': reviews,
        'form': form,
        'user_review': user_review,
        'in_watchlist': in_watchlist,
    }
    return render(request, 'movies/movie_detail.html', context)


# Delete Review View
@login_required
def delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk)
    movie_pk = review.movie.pk

    # Only allow review owner or admin to delete
    if request.user == review.user or request.user.is_staff:
        review.delete()
        messages.warning(request, "Review has been deleted")
    else:
        messages.error(request, "You don't have permission to delete this review")

    return redirect('movies:movie_detail', pk=movie_pk)


# Watchlist Views
@login_required
def toggle_watchlist(request, pk):
    """Add or remove a movie from user's watchlist"""
    movie = get_object_or_404(Movie, pk=pk)
    watchlist_item = Watchlist.objects.filter(user=request.user, movie=movie).first()

    if watchlist_item:
        # Remove from watchlist
        watchlist_item.delete()
        messages.info(request, f"'{movie.name}' removed from your watchlist")
    else:
        # Add to watchlist
        Watchlist.objects.create(user=request.user, movie=movie)
        messages.success(request, f"'{movie.name}' added to your watchlist!")

    # Redirect back to the referring page or movie detail
    next_url = request.GET.get('next', reverse('movies:movie_detail', args=[pk]))
    return redirect(next_url)


@token_required
def watchlist_page(request):
    """Display user's watchlist"""
    watchlist_items = Watchlist.objects.filter(user=request.user).select_related('movie')

    # Get movie IDs in watchlist
    watchlist_movies = [item.movie for item in watchlist_items]

    # Annotate with ratings
    from django.db.models import Avg, Count
    for movie in watchlist_movies:
        reviews = movie.reviews.all()
        if reviews.exists():
            movie.avg_rating = sum(r.rating for r in reviews) / reviews.count()
            movie.review_count = reviews.count()
        else:
            movie.avg_rating = 0
            movie.review_count = 0

    context = {
        'watchlist_items': watchlist_items,
        'watchlist_movies': watchlist_movies,
        'total_count': watchlist_items.count(),
    }
    return render(request, 'movies/watchlist.html', context)


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







# Using Concrete View Class, for list all movies and create new movie
class MovieListCreateAPIView(generics.ListCreateAPIView):

    queryset = Movie.objects.all().order_by('-release_date')
    serializer_class = MovieSerializer

    def get_permissions(self):
        # GET: Anyone can list movies, POST: Only admins can create
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [AllowAny()]


# Using GenericAPIView + Mixins, for retrieve, update, delete single movie
class MovieRetrieveUpdateDestroyAPIView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView
):

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


    permission_classes = [AllowAny] # view permission

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

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Delete user's token
        request.user.auth_token.delete()
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)


# Review API Views

class ReviewListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all reviews for a specific movie
    POST: Create a new review for a movie (authenticated users only)
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        movie_id = self.kwargs.get('movie_id')
        return Review.objects.filter(movie_id=movie_id)

    def perform_create(self, serializer):
        movie_id = self.kwargs.get('movie_id')
        movie = get_object_or_404(Movie, pk=movie_id)

        # Check if user already reviewed this movie
        existing_review = Review.objects.filter(user=self.request.user, movie=movie).first()
        if existing_review:
            # Update existing review instead
            existing_review.rating = serializer.validated_data['rating']
            existing_review.comment = serializer.validated_data['comment']
            existing_review.save()
            return existing_review

        serializer.save(user=self.request.user, movie=movie)


class ReviewRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific review
    PUT/PATCH: Update a review (owner only)
    DELETE: Delete a review (owner or admin only)
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        review = self.get_object()
        # Only allow owner to update
        if review.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only update your own reviews")
        serializer.save()

    def perform_destroy(self, instance):
        # Allow owner or admin to delete
        if instance.user != self.request.user and not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own reviews or must be an admin")
        instance.delete()





# Testing Links:
# Home: http://127.0.0.1:8000/
# Login: http://127.0.0.1:8000/movies/login/
# Register: http://127.0.0.1:8000/movies/register/
# Movie Database: http://127.0.0.1:8000/movies/movie-database/
# Add Movie: http://127.0.0.1:8000/movies/movie-database/add/
# Admin: http://127.0.0.1:8000/admin/




# User login: user1   user123

# Admin login: admin   admin123

