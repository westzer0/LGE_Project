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
    """제품 스펙 (JSON) - 1:1"""
    product = models.OneToOneField(
        "Product",
        on_delete=models.CASCADE,
        related_name="spec",
    )
    source = models.CharField(max_length=200, blank=True, default="")  # 예: TV_제품스펙.csv
    spec_json = models.TextField(blank=True, default="{}")  # CSV row 전체를 JSON 문자열로 저장
    ingested_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '제품 스펙'
        verbose_name_plural = '제품 스펙'

    def __str__(self):
        return f"Spec<{self.product_id}>"


class ProductDemographics(models.Model):
    """제품 인구통계 (1:1) - 어떤 사람들이 구매했는지
    
    정규화된 테이블 사용:
    - PROD_DEMO_FAMILY_TYPES
    - PROD_DEMO_HOUSE_SIZES
    - PROD_DEMO_HOUSE_TYPES
    """
    product = models.OneToOneField(
        "Product",
        on_delete=models.CASCADE,
        related_name="demographics",
    )
    # 가족 구성 (예: ['신혼', '부모님', '1인가구'])
    # 정규화 테이블에서 읽어옴 (하위 호환성을 위해 JSONField 유지)
    family_types = models.JSONField(default=list, blank=True)
    # 집 크기 (예: ['20평', '30평대'])
    # 정규화 테이블에서 읽어옴
    house_sizes = models.JSONField(default=list, blank=True)
    # 주거 형태 (예: ['아파트', '원룸'])
    # 정규화 테이블에서 읽어옴
    house_types = models.JSONField(default=list, blank=True)
    
    source = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '제품 인구통계'
        verbose_name_plural = '제품 인구통계'

    def __str__(self):
        return f"Demographics<{self.product_id}>"
    
    def get_family_types_from_normalized(self):
        """정규화 테이블에서 family_types 읽기"""
        try:
            from api.db.oracle_client import get_connection
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT FAMILY_TYPE FROM PROD_DEMO_FAMILY_TYPES
                        WHERE PRODUCT_ID = :product_id
                        ORDER BY FAMILY_TYPE
                    """, {'product_id': self.product_id})
                    return [row[0] for row in cur.fetchall()]
        except:
            # 정규화 테이블이 없거나 오류 시 기존 JSONField 반환
            return self.family_types if isinstance(self.family_types, list) else []
    
    def get_house_sizes_from_normalized(self):
        """정규화 테이블에서 house_sizes 읽기"""
        try:
            from api.db.oracle_client import get_connection
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT HOUSE_SIZE FROM PROD_DEMO_HOUSE_SIZES
                        WHERE PRODUCT_ID = :product_id
                        ORDER BY HOUSE_SIZE
                    """, {'product_id': self.product_id})
                    return [row[0] for row in cur.fetchall()]
        except:
            return self.house_sizes if isinstance(self.house_sizes, list) else []
    
    def get_house_types_from_normalized(self):
        """정규화 테이블에서 house_types 읽기"""
        try:
            from api.db.oracle_client import get_connection
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT HOUSE_TYPE FROM PROD_DEMO_HOUSE_TYPES
                        WHERE PRODUCT_ID = :product_id
                        ORDER BY HOUSE_TYPE
                    """, {'product_id': self.product_id})
                    return [row[0] for row in cur.fetchall()]
        except:
            return self.house_types if isinstance(self.house_types, list) else []
    
    def save_to_normalized(self):
        """정규화 테이블에 데이터 저장"""
        try:
            from api.db.oracle_client import get_connection
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 기존 데이터 삭제
                    cur.execute("DELETE FROM PROD_DEMO_FAMILY_TYPES WHERE PRODUCT_ID = :product_id", {'product_id': self.product_id})
                    cur.execute("DELETE FROM PROD_DEMO_HOUSE_SIZES WHERE PRODUCT_ID = :product_id", {'product_id': self.product_id})
                    cur.execute("DELETE FROM PROD_DEMO_HOUSE_TYPES WHERE PRODUCT_ID = :product_id", {'product_id': self.product_id})
                    
                    # 새 데이터 저장
                    family_types = self.family_types if isinstance(self.family_types, list) else []
                    for ft in family_types:
                        cur.execute("""
                            INSERT INTO PROD_DEMO_FAMILY_TYPES (PRODUCT_ID, FAMILY_TYPE)
                            VALUES (:product_id, :family_type)
                        """, {'product_id': self.product_id, 'family_type': str(ft)})
                    
                    house_sizes = self.house_sizes if isinstance(self.house_sizes, list) else []
                    for hs in house_sizes:
                        cur.execute("""
                            INSERT INTO PROD_DEMO_HOUSE_SIZES (PRODUCT_ID, HOUSE_SIZE)
                            VALUES (:product_id, :house_size)
                        """, {'product_id': self.product_id, 'house_size': str(hs)})
                    
                    house_types = self.house_types if isinstance(self.house_types, list) else []
                    for ht in house_types:
                        cur.execute("""
                            INSERT INTO PROD_DEMO_HOUSE_TYPES (PRODUCT_ID, HOUSE_TYPE)
                            VALUES (:product_id, :house_type)
                        """, {'product_id': self.product_id, 'house_type': str(ht)})
                    
                    conn.commit()
                    return True
        except Exception as e:
            # 오류 발생 시에도 계속 진행 (하위 호환성)
            return False


class ProductReview(models.Model):
    """제품 리뷰 (1:N) - 실제 고객 리뷰"""
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    star = models.CharField(max_length=20, blank=True, default="")  # 별점/평가
    review_text = models.TextField(blank=True, default="")  # 리뷰 내용
    
    source = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '제품 리뷰'
        verbose_name_plural = '제품 리뷰'
        ordering = ['-created_at']

    def __str__(self):
        return f"Review<{self.product_id}>: {self.review_text[:30]}..."


class ProductRecommendReason(models.Model):
    """제품 추천이유 (1:1) - LLM 생성 또는 리뷰 요약 기반"""
    product = models.OneToOneField(
        "Product",
        on_delete=models.CASCADE,
        related_name="recommend_reason",
    )
    reason_text = models.TextField(blank=True, default="")  # 추천 이유 텍스트
    
    source = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '제품 추천이유'
        verbose_name_plural = '제품 추천이유'

    def __str__(self):
        return f"RecommendReason<{self.product_id}>"


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
    
    has_pet = models.BooleanField(
        null=True,
        blank=True,
        help_text="Step 2: 반려동물 여부"
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
    
    main_space = models.JSONField(
        default=list,
        blank=True,
        help_text="Step 3: 주요 공간 (JSON 배열, 예: ['living', 'kitchen'])"
    )
    
    # Step 4: 라이프스타일
    cooking = models.CharField(
        max_length=20,
        choices=[
            ('rarely', '거의 하지 않아요'),
            ('sometimes', '가끔 해요'),
            ('often', '자주 해요'),
        ],
        null=True,
        blank=True,
        help_text="Step 4: 요리 빈도"
    )
    
    laundry = models.CharField(
        max_length=20,
        choices=[
            ('weekly', '일주일 1번 정도'),
            ('few_times', '일주일 2~3번 정도'),
            ('daily', '매일 조금씩'),
        ],
        null=True,
        blank=True,
        help_text="Step 4: 세탁 빈도"
    )
    
    media = models.CharField(
        max_length=20,
        choices=[
            ('ott', 'OTT를 즐기는 편'),
            ('gaming', '게임이 취미'),
            ('tv', '일반 프로그램 시청'),
            ('none', 'TV/영상을 즐기지 않음'),
        ],
        null=True,
        blank=True,
        help_text="Step 4: 미디어 사용 패턴"
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
        help_text="Step 5: 첫 번째 구매 우선순위"
    )
    
    priority_list = models.JSONField(
        default=list,
        blank=True,
        help_text="Step 5: 우선순위 목록 (JSON 배열, 순서 중요, 예: ['design', 'tech', 'eco'])"
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
        help_text="Step 6: 예산 범위"
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
        # recommendation_result에서 추가 정보 추출 (온보딩 데이터가 저장된 경우)
        extra_data = {}
        if isinstance(self.recommendation_result, dict):
            extra_data = self.recommendation_result.get('onboarding_data', {})
        
        # main_space 처리 (JSONField 또는 extra_data에서)
        main_space_value = self.main_space if isinstance(self.main_space, list) and len(self.main_space) > 0 else (
            extra_data.get('main_space', ['living']) if isinstance(extra_data, dict) else ['living']
        )
        if isinstance(main_space_value, str):
            main_space_value = [main_space_value]
        
        return {
            'vibe': self.vibe or 'modern',
            'household_size': self.household_size or 2,
            'housing_type': self.housing_type or 'apartment',
            'pyung': self.pyung or 25,
            'priority': self.priority or 'value',
            'budget_level': self.budget_level or 'medium',
            'categories': self.selected_categories or [],
            'main_space': main_space_value[0] if main_space_value else 'living',
            'space_size': 'medium',
            'has_pet': self.has_pet if self.has_pet is not None else (
                extra_data.get('pet') == 'yes' or extra_data.get('has_pet') == True if isinstance(extra_data, dict) else False
            ),
            'cooking': self.cooking or extra_data.get('cooking', 'sometimes') if isinstance(extra_data, dict) else 'sometimes',
            'laundry': self.laundry or extra_data.get('laundry', 'weekly') if isinstance(extra_data, dict) else 'weekly',
            'media': self.media or extra_data.get('media', 'balanced') if isinstance(extra_data, dict) else 'balanced',
        }
    
    def save(self, *args, **kwargs):
        """세션 ID 자동 생성"""
        if not self.session_id:
            self.session_id = str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)
    
    def mark_completed(self):
        """온보딩 완료 표시"""
        self.status = 'completed'
        self.current_step = 6
        self.completed_at = timezone.now()
        self.save()


class Portfolio(models.Model):
    """
    사용자 포트폴리오 - 추천 결과 저장 (1:N)
    PRD: ID와 포트폴리오는 1대 N 관계
    """
    
    # 고유 식별자
    portfolio_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="포트폴리오 내부 키 (예: PF-001, PF-002)"
    )
    
    # 내부 키 (LGDX-3) - portfolio_id와 동일하거나 별도 키
    internal_key = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="포트폴리오 내부 키 (portfolio_id와 동일 또는 별도 키)"
    )
    
    # 사용자 식별 (추후 카카오 로그인 연동 시 활용)
    user_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="사용자 ID (카카오 ID 또는 세션 ID)"
    )
    
    # 온보딩 세션 연결 (선택적)
    onboarding_session = models.ForeignKey(
        'OnboardingSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='portfolios',
        help_text="연결된 온보딩 세션"
    )
    
    # 스타일 정보
    style_type = models.CharField(
        max_length=50,
        choices=[
            ('modern', '모던 & 미니멀'),
            ('cozy', '따뜻한 코지'),
            ('natural', '내추럴 & 네이처'),
            ('luxury', '럭셔리 & 프리미엄'),
        ],
        default='modern',
        help_text="스타일 유형"
    )
    style_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="스타일 타이틀 (예: 모던 & 미니멀 라이프를 위한 오브제 스타일)"
    )
    style_subtitle = models.TextField(
        blank=True,
        help_text="스타일 설명 (ChatGPT 생성 가능)"
    )
    
    # 온보딩 결과 데이터
    onboarding_data = models.JSONField(
        default=dict,
        help_text="온보딩 설문 응답 데이터"
    )
    
    # 추천 제품 목록
    products = models.JSONField(
        default=list,
        help_text="추천 제품 목록 [{id, name, price, ...}, ...]"
    )
    
    # 가격 정보
    total_original_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        help_text="정가 합계"
    )
    total_discount_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        help_text="할인가 합계"
    )
    
    # 매칭 점수
    match_score = models.IntegerField(
        default=0,
        help_text="전체 매칭 점수 (0-100)"
    )
    
    # 상태
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', '임시저장'),
            ('saved', '저장됨'),
            ('shared', '공유됨'),
            ('purchased', '구매완료'),
        ],
        default='draft',
        help_text="포트폴리오 상태"
    )
    
    # 공유 정보
    share_url = models.CharField(
        max_length=200,
        blank=True,
        help_text="공유 URL"
    )
    share_count = models.IntegerField(
        default=0,
        help_text="공유 횟수"
    )
    
    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '포트폴리오'
        verbose_name_plural = '포트폴리오'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['portfolio_id']),
            models.Index(fields=['internal_key']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.portfolio_id} - {self.style_type}"
    
    def save(self, *args, **kwargs):
        """포트폴리오 ID 자동 생성"""
        if not self.portfolio_id:
            # PF-XXXXXX 형식
            import random
            import string
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.portfolio_id = f"PF-{random_str}"
        
        # internal_key가 없으면 portfolio_id와 동일하게 설정
        if not self.internal_key:
            self.internal_key = self.portfolio_id
        
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """가격 합계 계산"""
        original = sum(p.get('price', 0) for p in self.products)
        discount = sum(p.get('discountPrice', p.get('price', 0)) for p in self.products)
        self.total_original_price = original
        self.total_discount_price = discount
        self.save()


class Cart(models.Model):
    """장바구니 모델 - LGDX-12"""
    user_id = models.CharField(max_length=100, db_index=True, help_text="사용자 ID (카카오 ID 또는 세션 ID)")
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='cart_items', help_text="장바구니에 담긴 제품")
    quantity = models.IntegerField(default=1, help_text="제품 수량")
    extra_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '장바구니'
        verbose_name_plural = '장바구니'
        unique_together = ['user_id', 'product']
        ordering = ['-created_at']

    def __str__(self):
        return f"Cart({self.user_id}, {self.product.name})"


class Wishlist(models.Model):
    """찜하기 모델"""
    user_id = models.CharField(max_length=100, db_index=True, help_text="사용자 ID")
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='wishlist_items')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = '찜하기'
        verbose_name_plural = '찜하기'
        unique_together = ['user_id', 'product']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Wishlist({self.user_id}, {self.product.name})"


class TasteConfig(models.Model):
    """
    Taste별 추천 설정 관리
    - 각 taste_id에 대해 카테고리와 추천 제품을 미리 정의
    - 변동사항이 있으면 이 테이블만 업데이트하면 됨
    """
    taste_id = models.IntegerField(unique=True, primary_key=True, help_text="Taste ID (1-120)")
    
    # Taste 설명
    description = models.CharField(max_length=500, blank=True, help_text="Taste 설명")
    
    # 대표 온보딩 특성 (참고용)
    representative_vibe = models.CharField(max_length=20, blank=True)
    representative_household_size = models.IntegerField(null=True, blank=True)
    representative_main_space = models.CharField(max_length=50, blank=True)
    representative_has_pet = models.BooleanField(null=True, blank=True)
    representative_priority = models.CharField(max_length=20, blank=True)
    representative_budget_level = models.CharField(max_length=20, blank=True)
    
    # 추천 카테고리 (JSON 배열)
    recommended_categories = models.JSONField(
        default=list,
        help_text="추천 MAIN_CATEGORY 리스트 (예: ['TV', '냉장고', '에어컨'])"
    )
    
    # 추천 카테고리와 점수 (JSON 객체)
    # 구조: {"TV": 85.0, "냉장고": 70.0, "에어컨": 65.0}
    # Oracle DB 컬럼명: CATEGORY_SCORES (30자 제한으로 인해)
    recommended_categories_with_scores = models.JSONField(
        default=dict,
        blank=True,
        help_text="카테고리별 점수 매핑 (0~100점)"
    )
    
    # Ill-suited 카테고리 리스트 (JSON 배열)
    # 온보딩 답변에 완전히 부적합한 카테고리들 (0점)
    ill_suited_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="Ill-suited 카테고리 리스트 (온보딩 답변과 완전히 부적합한 카테고리)"
    )
    
    # 추천 제품 모델 (카테고리별 상위 3개씩, JSON)
    # 구조: {"TV": [product_id1, product_id2, product_id3], "냉장고": [...]}
    recommended_products = models.JSONField(
        default=dict,
        help_text="카테고리별 추천 제품 ID 매핑"
    )
    
    # 메타 정보
    is_active = models.BooleanField(default=True, help_text="활성화 여부")
    auto_generated = models.BooleanField(default=False, help_text="자동 생성 여부")
    last_simulation_date = models.DateTimeField(null=True, blank=True, help_text="마지막 시뮬레이션 실행일")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Taste 설정'
        verbose_name_plural = 'Taste 설정'
        ordering = ['taste_id']
    
    def __str__(self):
        return f"Taste {self.taste_id}: {', '.join(self.recommended_categories[:3]) if self.recommended_categories else 'N/A'}..."


class Reservation(models.Model):
    """
    베스트샵 상담 예약 모델
    PRD: 예약 조회/변경 기능
    """
    
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('confirmed', '확정됨'),
        ('completed', '완료됨'),
        ('cancelled', '취소됨'),
    ]
    
    # 예약 ID
    reservation_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="예약 ID (예: BS-PF-XXXXXX-TIMESTAMP)"
    )
    
    # 사용자 정보
    user_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="사용자 ID (카카오 ID 또는 세션 ID)"
    )
    
    # 포트폴리오 연결
    portfolio = models.ForeignKey(
        'Portfolio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations',
        help_text="연결된 포트폴리오"
    )
    
    # 예약 정보
    consultation_purpose = models.CharField(
        max_length=100,
        default='이사',
        help_text="상담 목적 (이사, 신혼, 리모델링 등)"
    )
    
    preferred_date = models.DateField(
        null=True,
        blank=True,
        help_text="희망 날짜"
    )
    
    preferred_time = models.TimeField(
        null=True,
        blank=True,
        help_text="희망 시간"
    )
    
    store_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="매장 위치 (예: 서울 강남점)"
    )
    
    # 상태
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="예약 상태"
    )
    
    # 추가 정보
    contact_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="연락처 이름"
    )
    
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="연락처 전화번호"
    )
    
    contact_email = models.EmailField(
        blank=True,
        help_text="연락처 이메일"
    )
    
    memo = models.TextField(
        blank=True,
        help_text="추가 메모"
    )
    
    # 외부 시스템 연동 정보
    external_reservation_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="베스트샵 시스템 예약 ID (외부 시스템 연동 시)"
    )
    
    external_system_url = models.URLField(
        blank=True,
        help_text="외부 시스템 URL"
    )
    
    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = '상담 예약'
        verbose_name_plural = '상담 예약'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['reservation_id']),
            models.Index(fields=['status']),
            models.Index(fields=['preferred_date']),
        ]
    
    def __str__(self):
        return f"{self.reservation_id} - {self.get_status_display()} ({self.store_location or '미정'})"
    
    def save(self, *args, **kwargs):
        """예약 ID 자동 생성"""
        if not self.reservation_id:
            import random
            import string
            timestamp = int(timezone.now().timestamp())
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            portfolio_prefix = f"PF-{self.portfolio.portfolio_id.split('-')[-1]}" if self.portfolio else "BS"
            self.reservation_id = f"{portfolio_prefix}-{random_str}-{timestamp}"
        super().save(*args, **kwargs)
