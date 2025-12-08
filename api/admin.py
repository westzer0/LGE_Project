from django.contrib import admin
from .models import Product  # 다른 모델들도 import

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'main_category', 'price', 'status']
