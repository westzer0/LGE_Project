from django.db import models
from django.utils import timezone
import uuid


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


class OnboardingSession(models.Model):
    """
    사용자 온보딩 세션
    = 사용자의 설문 응답을 저장하는 모델
    """
    
    # 세션 정보
    session_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="고유 세션 ID"
    )
    
    # 온보딩 답변 (Step 1~5)
    vibe = models.CharField(
        max_length=20,
        choices=[
            ('modern', '모던/심플'),
            ('cozy', '따뜻한 톤'),
            ('pop', '팝/생기있는'),
            ('luxury', '럭셔리/고급'),
        ],
        null=True,
        blank=True,
        help_text="Step 1: 인테리어 무드"
    )
    
    household_size = models.IntegerField(
        null=True,
        blank=True,
        help_text="Step 2: 가구 인원수"
    )
    
    housing_type = models.CharField(
        max_length=20,
        choices=[
            ('apartment', '아파트'),
            ('detached', '단독주택'),
            ('villa', '빌라/연립'),
            ('officetel', '오피스텔'),
            ('studio', '원룸'),
        ],
        null=True,
        blank=True,
        help_text="Step 3: 주거 형태"
    )
    
    pyung = models.IntegerField(
        null=True,
        blank=True,
        help_text="Step 3: 주거 평수"
    )
    
    priority = models.CharField(
        max_length=20,
        choices=[
            ('design', '디자인/무드'),
            ('tech', '기술/성능'),
            ('eco', '에너지효율'),
            ('value', '가성비'),
        ],
        default='value',
        help_text="Step 4: 구매 우선순위"
    )
    
    budget_level = models.CharField(
        max_length=20,
        choices=[
            ('low', '500만원 이하'),
            ('medium', '500~2000만원'),
            ('high', '2000만원 이상'),
            # 기존 매핑과의 호환성
            ('budget', '500만원 이하'),
            ('standard', '500~2000만원'),
            ('premium', '2000만원 이상'),
            ('luxury', '2000만원 이상'),
        ],
        default='medium',
        help_text="Step 5: 예산 범위"
    )
    
    # 선택한 카테고리
    selected_categories = models.JSONField(
        default=list,
        help_text="선택한 제품 카테고리 (예: ['TV', 'KITCHEN'])"
    )
    
    # 추천 결과 저장
    recommended_products = models.JSONField(
        default=list,
        help_text="추천 제품 ID 목록"
    )
    
    recommendation_result = models.JSONField(
        default=dict,
        help_text="최종 추천 결과 (JSON)"
    )
    
    # 상태 관리
    current_step = models.IntegerField(
        default=1,
        choices=[(i, f'Step {i}') for i in range(1, 7)],
        help_text="현재 진행 중인 스텝"
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('in_progress', '진행중'),
            ('completed', '완료'),
            ('abandoned', '중단됨'),
        ],
        default='in_progress',
        help_text="온보딩 상태"
    )
    
    # 타임스탬프
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="세션 생성 시간"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="마지막 업데이트 시간"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="온보딩 완료 시간"
    )
    
    class Meta:
        verbose_name = '온보딩 세션'
        verbose_name_plural = '온보딩 세션'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.session_id} - {self.get_status_display()} (Step {self.current_step})"
    
    def to_user_profile(self) -> dict:
        """
        OnboardingSession을 RecommendationEngine용 user_profile로 변환
        """
        return {
            'vibe': self.vibe or 'modern',
            'household_size': self.household_size or 2,
            'housing_type': self.housing_type or 'apartment',
            'pyung': self.pyung or 25,
            'priority': self.priority or 'value',
            'budget_level': self.budget_level or 'medium',
            'categories': self.selected_categories or [],
            'main_space': 'living',
            'space_size': 'medium',
        }
    
    def save(self, *args, **kwargs):
        """세션 ID 자동 생성"""
        if not self.session_id:
            self.session_id = str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)
    
    def mark_completed(self):
        """온보딩 완료 표시"""
        self.status = 'completed'
        self.current_step = 5
        self.completed_at = timezone.now()
        self.save()
