from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda req: redirect('dashboard'), name='home'),
    path('', include('academica.urls')),
]
