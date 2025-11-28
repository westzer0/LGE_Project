from django.contrib import admin
from django.urls import path
from api.views import index_view, recommend, products, recommend_view

urlpatterns = [
    path('', index_view, name='index'),
    path('admin/', admin.site.urls),
    path('api/recommend/', recommend_view),
    path('api/products/', products),
]
