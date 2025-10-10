from django.urls import path
from . import views

app_name = 'my_templates'

urlpatterns = [
    # Home page
    path('', views.inherited_form, name='inherited_form'),
]