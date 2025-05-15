# ScheduleSystem/urls.py
from django.contrib import admin
from django.urls import path, include # Make sure include is imported
from django.views.generic import RedirectView # Import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Include your app's URLs under a specific path, e.g., 'schedule/'
    # The namespace parameter should match the app_name defined in littlecaesars/urls.py
    path('schedule/', include('littlecaesars.urls', namespace='littlecaesars')),
    # You might want a root path redirect later, e.g.:
    # from django.views.generic import RedirectView
    path('', RedirectView.as_view(pattern_name='littlecaesars:index', permanent=False)),
]