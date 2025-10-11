from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .auth_utils import TOKEN_MAX_AGE


class SessionExpirationMiddleware:
    #Warn user when session is about to expire
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user has token and it's about to expire
        if request.user.is_authenticated and request.session.get('auth_token'):  # only warn logged-in users, if not logged in, don't run the rest of this middleware

            token_created = request.session.get('token_created')     # get time when token was created from session
 
            if token_created and not request.session.get('warned'):   # only warn when not warned before
                created_time = timezone.datetime.fromisoformat(token_created)
                expire_time = created_time + timedelta(seconds=TOKEN_MAX_AGE)
                time_left = (expire_time - timezone.now()).total_seconds()    # calculate time left

                # Warn if less than 15 minutes left
                if 0 < time_left < 15 * 60:
                    messages.warning(request, f"Session expires in {int(time_left / 60)} minutes")
                    request.session['warned'] = True

        return self.get_response(request) # proceed to next middleware or view
