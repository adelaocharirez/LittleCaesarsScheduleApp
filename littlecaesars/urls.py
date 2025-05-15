# littlecaesars/urls.py
from django.urls import path
from . import views

# Define an app_name for namespacing URLs
app_name = 'littlecaesars'

urlpatterns = [
    path('enter-name/', views.enter_name_view, name='enter_name'),
    path('select-availability/', views.select_availability_view, name='select_availability'),
    # Add the new path for viewing availability
    path('view-availability/', views.view_availability, name='view_availability'),
    # Add other app-specific URLs here later
    # Maybe redirect root of app to name entry?
    path('', views.enter_name_view, name='index'),
]