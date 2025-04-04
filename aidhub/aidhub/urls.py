from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "AidHub Administration"  
admin.site.site_title = "AidHub Admin Portal"
admin.site.index_title = "Welcome to AidHub Administration"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('donations.urls')),
]
