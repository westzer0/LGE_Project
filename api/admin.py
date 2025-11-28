from django.contrib import admin
from .models import Product, ProductSpec, UserSample

class ProductSpecInline(admin.StackedInline):
    model = ProductSpec
    extra = 0
    fields = ("source", "spec_json", "ingested_at")
    readonly_fields = ("ingested_at",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "name", "model_number", "price")
    search_fields = ("name", "model_number")
    list_filter = ("category",)
    inlines = [ProductSpecInline]

@admin.register(UserSample)
class UserSampleAdmin(admin.ModelAdmin):
    list_display = ("user_id", "household_size", "space_type", "budget_range", "created_at")
    search_fields = ("user_id",)
    list_filter = ("household_size", "space_type", "budget_range", "created_at")
