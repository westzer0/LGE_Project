from django.db import models


class Product(models.Model):
    """LG 가전 제품 모델"""
    
    CATEGORY_CHOICES = [
        ('TV', 'TV/오디오'),
        ('KITCHEN', '주방가전'),
        ('LIVING', '생활가전'),
        ('AIR', '에어컨/에어케어'),
        ('AI', 'AI Home'),
        ('OBJET', 'LG Objet'),
        ('SIGNATURE', 'LG SIGNATURE'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='제품명')
    model_number = models.CharField(max_length=100, verbose_name='모델명', blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='카테고리')
    description = models.TextField(verbose_name='설명', blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='가격')
    discount_price = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        null=True, 
        blank=True, 
        verbose_name='할인가'
    )
    image_url = models.URLField(verbose_name='이미지 URL', blank=True)
    is_active = models.BooleanField(default=True, verbose_name='판매중')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '제품'
        verbose_name_plural = '제품'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.model_number})"


class ProductSpec(models.Model):
    product = models.OneToOneField(
        "Product",
        on_delete=models.CASCADE,
        related_name="spec",
    )
    source = models.CharField(max_length=200, blank=True, default="")  # 예: TV_제품스펙.csv
    spec_json = models.TextField(blank=True, default="{}")  # CSV row 전체를 JSON 문자열로 저장
    ingested_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Spec<{self.product_id}>"


class UserSample(models.Model):
    user_id = models.CharField(max_length=50, unique=True)
    household_size = models.CharField(max_length=20, blank=True)
    space_type = models.CharField(max_length=20, blank=True)
    space_purpose = models.CharField(max_length=50, blank=True)
    space_sqm = models.FloatField(null=True, blank=True)
    space_size_cat = models.CharField(max_length=20, blank=True)
    style_pref = models.CharField(max_length=50, blank=True)
    cooking_freq = models.CharField(max_length=20, blank=True)
    laundry_pattern = models.CharField(max_length=50, blank=True)
    media_pref = models.CharField(max_length=50, blank=True)
    pet = models.CharField(max_length=10, blank=True)
    budget_range = models.CharField(max_length=50, blank=True)
    payment_pref = models.CharField(max_length=20, blank=True)

    recommended_fridge_l = models.IntegerField(null=True, blank=True)
    recommended_washer_kg = models.IntegerField(null=True, blank=True)
    recommended_tv_inch = models.IntegerField(null=True, blank=True)
    recommended_vacuum = models.CharField(max_length=50, blank=True)
    recommended_oven = models.CharField(max_length=50, blank=True)
    purchased_items = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '사용자 샘플'
        verbose_name_plural = '사용자 샘플'
        ordering = ['-created_at']

    def __str__(self):
        return f"UserSample({self.user_id})"
