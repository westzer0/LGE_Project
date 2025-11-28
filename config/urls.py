from django.contrib import admin
from django.urls import path
from api.views import recommend, products

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/recommend/', recommend),
    path('api/products/', products),
]
