from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
from .auth_utils import validate_token


def token_required(view_func):
    #Check if user has valid token, redirect to homepage if not
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check login
        if not request.user.is_authenticated:
            messages.error(request, "Please login to access this page")  # @loginrequired 
            return redirect('my_templates:inherited_form')

        # Check token
        token = request.session.get('auth_token')
        if not token or not validate_token(token):
            messages.error(request, "Session expired. Please login again")
            logout(request)
            request.session.flush()
            return redirect('my_templates:inherited_form')

        return view_func(request, *args, **kwargs)

    return wrapper
