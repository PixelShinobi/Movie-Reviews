from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from movies.models import Movie, Review
import random


class Command(BaseCommand):
    help = 'Populate movies with sample reviews for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing reviews before populating',
        )

    def handle(self, *args, **options):
        # Sample review comments
        positive_comments = [
            "Absolutely loved this movie! The acting was superb and the storyline kept me engaged throughout.",
            "A masterpiece! This is definitely one of the best movies I've seen this year.",
            "Amazing cinematography and brilliant performances. Highly recommend!",
            "This movie exceeded all my expectations. A must-watch!",
            "Fantastic film with great character development and an engaging plot.",
            "One of the best movies in its genre. The direction was outstanding!",
            "I was blown away by this movie. Everything from the acting to the music was perfect.",
            "A truly unforgettable cinematic experience. Loved every minute of it!",
        ]

        good_comments = [
            "Really enjoyed this movie. Great entertainment value!",
            "Solid movie with good performances. Worth watching.",
            "Good storyline and decent execution. I'd recommend it.",
            "An enjoyable watch with some memorable moments.",
            "Pretty good movie overall. Had a few slow parts but mostly engaging.",
            "Nice movie with good acting. Would watch again.",
        ]

        average_comments = [
            "It was okay. Nothing special but not bad either.",
            "Decent movie but could have been better.",
            "Average film with some good moments and some not-so-good ones.",
            "It's watchable but forgettable.",
            "Middle of the road. Some parts were good, others were meh.",
        ]

        negative_comments = [
            "Disappointing. Expected much more from this movie.",
            "Not great. The plot was weak and the pacing was off.",
            "Could have been better. Felt like it was missing something.",
            "Below average. Wouldn't really recommend it.",
            "Not my cup of tea. The story didn't resonate with me.",
        ]

        very_negative_comments = [
            "Terrible movie. Waste of time.",
            "One of the worst movies I've seen. Poor execution.",
            "Extremely disappointed. Nothing worked in this film.",
            "Avoid this one. Not worth your time.",
        ]

        # Clear existing reviews if requested
        if options['clear']:
            Review.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all existing reviews'))

        # Get or create test users
        users = []
        usernames = ['reviewer1', 'reviewer2', 'reviewer3', 'reviewer4', 'reviewer5',
                     'moviefan', 'cinemafan', 'filmcritic', 'moviebuff', 'casual_viewer']

        for username in usernames:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@example.com'}
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
            users.append(user)

        # Get all movies
        movies = Movie.objects.all()

        if not movies.exists():
            self.stdout.write(self.style.ERROR('No movies found in database. Please add some movies first.'))
            return

        reviews_created = 0

        # Populate each movie with random reviews
        for movie in movies:
            # Randomly decide how many reviews (2-8 reviews per movie to ensure all have some)
            num_reviews = random.randint(2, 8)

            # Select random users for this movie (no duplicates)
            selected_users = random.sample(users, min(num_reviews, len(users)))

            for user in selected_users:
                # Check if review already exists
                if Review.objects.filter(user=user, movie=movie).exists():
                    continue

                # Generate rating (weighted towards higher ratings)
                rating_weights = [5, 15, 25, 30, 25]  # Weights for ratings 1-5
                rating = random.choices([1, 2, 3, 4, 5], weights=rating_weights)[0]

                # Select comment based on rating
                if rating == 5:
                    comment = random.choice(positive_comments)
                elif rating == 4:
                    comment = random.choice(good_comments)
                elif rating == 3:
                    comment = random.choice(average_comments)
                elif rating == 2:
                    comment = random.choice(negative_comments)
                else:  # rating == 1
                    comment = random.choice(very_negative_comments)

                # Create review
                Review.objects.create(
                    user=user,
                    movie=movie,
                    rating=rating,
                    comment=comment
                )
                reviews_created += 1

            avg_rating = movie.get_average_rating()
            review_count = movie.get_review_count()
            self.stdout.write(
                f'  {movie.name}: {review_count} reviews, avg rating: {avg_rating}/5'
            )

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {reviews_created} reviews!')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total movies with reviews: {movies.filter(reviews__isnull=False).distinct().count()}/{movies.count()}')
        )
