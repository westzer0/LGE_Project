from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json


class Product(models.Model):
    """
    LG 가전 제품 모델 (ERD: PRODUCT)
    """
    
    CATEGORY_CHOICES = [
        ('TV', 'TV/오디오'),
        ('KITCHEN', '주방가전'),
        ('LIVING', '생활가전'),
        ('AIR', '에어컨/에어케어'),
        ('AI', 'AI Home'),
        ('OBJET', 'LG Objet'),
        ('SIGNATURE', 'LG SIGNATURE'),
    ]
    
    product_id = models.AutoField(primary_key=True, verbose_name='제품 ID')
    product_name = models.CharField(max_length=255, verbose_name='제품명')
    main_category = models.CharField(max_length=100, verbose_name='메인 카테고리')
    sub_category = models.CharField(max_length=100, null=True, blank=True, verbose_name='세부 카테고리')
    model_code = models.CharField(max_length=100, null=True, blank=True, verbose_name='모델 코드')
    status = models.CharField(max_length=50, null=True, blank=True, choices=[('판매중', '판매중'), ('품절', '품절')], verbose_name='판매 상태')
    price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name='제품 가격')
    rating = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(5)], verbose_name='제품 평점')
    url = models.CharField(max_length=255, null=True, blank=True, verbose_name='제품 상세 페이지 URL')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='생성일')
    
    # 하위 호환성을 위한 필드 (기존 코드와의 호환)
    name = models.CharField(max_length=200, null=True, blank=True, verbose_name='제품명 (하위 호환)')
    model_number = models.CharField(max_length=100, null=True, blank=True, verbose_name='모델명 (하위 호환)')
    category = models.CharField(max_length=20, null=True, blank=True, choices=CATEGORY_CHOICES, verbose_name='카테고리 (하위 호환)')
    description = models.TextField(verbose_name='설명', blank=True)
    discount_price = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        null=True, 
        blank=True, 
        verbose_name='할인가'
    )
    image_url = models.URLField(verbose_name='이미지 URL', blank=True)
    is_active = models.BooleanField(default=True, verbose_name='판매중')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '제품'
        verbose_name_plural = '제품'
        db_table = 'product'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product_name or self.name} ({self.model_code or self.model_number})"
    
    def save(self, *args, **kwargs):
        # 하위 호환성: name이 없으면 product_name 사용
        if not self.name and self.product_name:
            self.name = self.product_name
        if not self.model_number and self.model_code:
            self.model_number = self.model_code
        if not self.category and self.main_category:
            self.category = self.main_category
        super().save(*args, **kwargs)


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
    """
    사용자 샘플 모델
    
    주의: 이 모델은 실제로 사용되지 않습니다.
    모델만 정의되어 있고 실제 코드에서 조회/사용하지 않습니다.
    """
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
    
    변경사항:
    - session_id: AutoField → CharField (UUID 문자열)
    - CLOB 필드 제거 (정규화 테이블 사용: ONBOARD_SESS_MAIN_SPACES, ONBOARD_SESS_PRIORITIES, ONBOARD_SESS_CATEGORIES, ONBOARD_SESS_REC_PRODUCTS)
    - user_id 필드 제거 (중복)
    - member 필드: NULL 허용, 기본값 'GUEST'
    """
    
    # 세션 정보 (UUID 문자열로 변경)
    session_id = models.CharField(max_length=100, primary_key=True, verbose_name='세션 ID', help_text="UUID 문자열")
    # 하위 호환성을 위한 UUID 문자열 필드 (기존 코드에서 사용)
    session_uuid = models.CharField(max_length=100, unique=True, null=True, blank=True, help_text="UUID 문자열 (하위 호환성)")
    member = models.ForeignKey(
        'Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboarding_sessions',
        db_column='member_id',
        verbose_name='회원'
        # 기본값 'GUEST'는 서비스 레이어에서 처리
    )
    # user_id 필드 제거됨 (중복)
    
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
    
    # main_space 필드 제거됨 (정규화 테이블 ONBOARD_SESS_MAIN_SPACES 사용)
    # main_space = models.JSONField(...)  # 제거
    
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
    
    # priority_list 필드 제거됨 (정규화 테이블 ONBOARD_SESS_PRIORITIES 사용)
    # priority_list = models.JSONField(...)  # 제거
    
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
    
    # Taste ID (TASTE_CONFIG와 매칭된 결과)
    taste_id = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(1920)],
        help_text="매칭된 Taste ID (1-1920, TASTE_CONFIG와 비교하여 설정)"
    )
    
    # selected_categories 필드 제거됨 (정규화 테이블 ONBOARD_SESS_CATEGORIES 사용)
    # selected_categories = models.JSONField(...)  # 제거
    
    # recommended_products 필드 제거됨 (정규화 테이블 ONBOARD_SESS_REC_PRODUCTS 사용)
    # recommended_products = models.JSONField(...)  # 제거
    
    # recommendation_result 필드 (중간 단계 데이터 및 최종 추천 결과 저장용)
    # SQLite에서는 JSONField 사용 가능, Oracle에서는 CLOB 대신 사용
    recommendation_result = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text='중간 단계 데이터 및 최종 추천 결과 (JSON)'
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
    
    # 타임스탬프 (db_column 명시)
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_column='created_at',
        help_text="세션 생성 시간"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        db_column='updated_at',
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
        db_table = 'onboarding_session'
        managed = True  # Django가 테이블 관리 (SQLite용)
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Session {self.session_id} - {self.get_status_display()} (Step {self.current_step})"
    
    def to_user_profile(self) -> dict:
        """
        OnboardingSession을 RecommendationEngine용 user_profile로 변환
        정규화 테이블에서 데이터를 읽어옴
        """
        # 정규화 테이블에서 main_space 읽기
        main_spaces = []
        try:
            from api.db.oracle_client import get_connection
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT MAIN_SPACE FROM ONBOARD_SESS_MAIN_SPACES
                        WHERE SESSION_ID = :session_id
                        ORDER BY MAIN_SPACE
                    """, {'session_id': self.session_id})
                    main_spaces = [row[0] for row in cur.fetchall()]
        except:
            pass
        
        # 정규화 테이블에서 priority_list 읽기
        priority_list = []
        try:
            from api.db.oracle_client import get_connection
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT PRIORITY FROM ONBOARD_SESS_PRIORITIES
                        WHERE SESSION_ID = :session_id
                        ORDER BY PRIORITY_ORDER
                    """, {'session_id': self.session_id})
                    priority_list = [row[0] for row in cur.fetchall()]
        except:
            pass
        
        # 정규화 테이블에서 selected_categories 읽기
        selected_categories = []
        try:
            from api.db.oracle_client import get_connection
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT CATEGORY_NAME FROM ONBOARD_SESS_CATEGORIES
                        WHERE SESSION_ID = :session_id
                        ORDER BY CATEGORY_NAME
                    """, {'session_id': self.session_id})
                    selected_categories = [row[0] for row in cur.fetchall()]
        except:
            pass
        
        main_space_value = main_spaces[0] if main_spaces else 'living'
        
        return {
            'vibe': self.vibe or 'modern',
            'household_size': self.household_size or 2,
            'housing_type': self.housing_type or 'apartment',
            'pyung': self.pyung or 25,
            'priority': self.priority or 'value',
            'budget_level': self.budget_level or 'medium',
            'categories': selected_categories,
            'main_space': main_space_value,
            'space_size': 'medium',
            'has_pet': self.has_pet if self.has_pet is not None else False,
            'cooking': self.cooking or 'sometimes',
            'laundry': self.laundry or 'weekly',
            'media': self.media or 'balanced',
        }
    
    def save(self, *args, **kwargs):
        """세션 UUID 자동 생성 (하위 호환성)"""
        if not self.session_uuid:
            self.session_uuid = str(uuid.uuid4())[:8]
        # session_id가 없으면 UUID 생성
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
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
    taste_id = models.IntegerField(unique=True, primary_key=True, help_text="Taste ID (1-1920)")
    
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


# ============================================================
# ERD 기반 추가 모델 (34개 테이블 완성)
# ============================================================

class Member(models.Model):
    """
    회원 테이블 (ERD: MEMBER)
    """
    member_id = models.CharField(max_length=30, primary_key=True, verbose_name='회원 ID')
    password = models.CharField(max_length=255, verbose_name='비밀번호 (암호화)')
    name = models.CharField(max_length=100, verbose_name='회원 이름')
    age = models.IntegerField(null=True, blank=True, verbose_name='나이')
    gender = models.CharField(max_length=10, null=True, blank=True, choices=[('M', '남성'), ('F', '여성')], verbose_name='성별')
    contact = models.CharField(max_length=20, null=True, blank=True, verbose_name='연락처')
    point = models.IntegerField(default=0, null=True, blank=True, verbose_name='포인트')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='가입 일시')
    taste = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(120)], verbose_name='할당된 Taste ID')
    
    class Meta:
        verbose_name = '회원'
        verbose_name_plural = '회원'
        db_table = 'member'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.member_id} - {self.name}"


class CartNew(models.Model):
    """
    장바구니 테이블 (ERD: CART)
    """
    cart_id = models.AutoField(primary_key=True, verbose_name='장바구니 ID')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='carts', db_column='member_id', verbose_name='회원')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='생성 일시')
    
    class Meta:
        verbose_name = '장바구니'
        verbose_name_plural = '장바구니'
        db_table = 'cart'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Cart {self.cart_id} - {self.member.member_id}"


class CartItem(models.Model):
    """
    장바구니 항목 테이블 (ERD: CART_ITEM)
    """
    cart_item_id = models.AutoField(primary_key=True, verbose_name='장바구니 항목 ID')
    cart = models.ForeignKey(CartNew, on_delete=models.CASCADE, related_name='items', db_column='cart_id', verbose_name='장바구니')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items_new', db_column='product_id', verbose_name='제품')
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name='수량')
    
    class Meta:
        verbose_name = '장바구니 항목'
        verbose_name_plural = '장바구니 항목'
        db_table = 'cart_item'
        unique_together = ['cart', 'product']
        ordering = ['-cart_item_id']
    
    def __str__(self):
        return f"CartItem {self.cart_item_id} - {self.product.name} x{self.quantity}"


class Orders(models.Model):
    """
    주문 테이블 (ERD: ORDERS)
    """
    order_id = models.AutoField(primary_key=True, verbose_name='주문 ID')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='orders', db_column='member_id', verbose_name='회원')
    order_date = models.DateTimeField(auto_now_add=True, verbose_name='주문 일시')
    total_amount = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name='주문 총액')
    order_status = models.CharField(max_length=50, null=True, blank=True, verbose_name='주문 상태')
    payment_status = models.CharField(max_length=50, null=True, blank=True, verbose_name='결제 상태')
    
    class Meta:
        verbose_name = '주문'
        verbose_name_plural = '주문'
        db_table = 'orders'
        ordering = ['-order_date']
    
    def __str__(self):
        return f"Order {self.order_id} - {self.member.member_id}"


class OrderDetail(models.Model):
    """
    주문 상세 테이블 (ERD: ORDER_DETAIL)
    """
    detail_id = models.AutoField(primary_key=True, verbose_name='주문 상세 ID')
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='details', db_column='order_id', verbose_name='주문')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_details', db_column='product_id', verbose_name='제품')
    quantity = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='수량')
    
    class Meta:
        verbose_name = '주문 상세'
        verbose_name_plural = '주문 상세'
        db_table = 'order_detail'
        ordering = ['detail_id']
    
    def __str__(self):
        return f"OrderDetail {self.detail_id} - {self.product.name} x{self.quantity}"


class Payment(models.Model):
    """
    결제 테이블 (ERD: PAYMENT)
    """
    payment_id = models.AutoField(primary_key=True, verbose_name='결제 ID')
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name='결제 일시')
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='payments', db_column='order_id', verbose_name='주문')
    payment_status = models.CharField(max_length=50, null=True, blank=True, verbose_name='결제 상태')
    method = models.CharField(max_length=50, null=True, blank=True, verbose_name='결제 방법')
    
    class Meta:
        verbose_name = '결제'
        verbose_name_plural = '결제'
        db_table = 'payment'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.order.order_id}"


class OnboardingQuestion(models.Model):
    """
    온보딩 질문 테이블 (ERD: ONBOARDING_QUESTION)
    """
    question_code = models.CharField(max_length=50, primary_key=True, verbose_name='질문 코드')
    question_text = models.CharField(max_length=255, verbose_name='질문 텍스트')
    question_type = models.CharField(max_length=50, verbose_name='질문 유형')
    is_required = models.CharField(max_length=5, default='Y', choices=[('Y', '필수'), ('N', '선택')], verbose_name='필수 여부')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='생성 일시')
    
    class Meta:
        verbose_name = '온보딩 질문'
        verbose_name_plural = '온보딩 질문'
        db_table = 'onboarding_question'
        ordering = ['question_code']
    
    def __str__(self):
        return f"{self.question_code} - {self.question_text[:30]}"


class OnboardingAnswer(models.Model):
    """
    온보딩 답변 선택지 테이블 (ERD: ONBOARDING_ANSWER)
    """
    answer_id = models.AutoField(primary_key=True, verbose_name='선택지 ID')
    question = models.ForeignKey(OnboardingQuestion, on_delete=models.CASCADE, related_name='answers', db_column='question_code', verbose_name='질문')
    answer_value = models.CharField(max_length=255, null=True, blank=True, verbose_name='선택지 값')
    answer_text = models.CharField(max_length=255, null=True, blank=True, verbose_name='선택지 텍스트')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='생성 일시')
    
    class Meta:
        verbose_name = '온보딩 답변 선택지'
        verbose_name_plural = '온보딩 답변 선택지'
        db_table = 'onboarding_answer'
        ordering = ['answer_id']
    
    def __str__(self):
        return f"{self.question.question_code} - {self.answer_text or self.answer_value}"


class OnboardingUserResponse(models.Model):
    """
    사용자 온보딩 응답 테이블 (ERD: ONBOARDING_USER_RESPONSE)
    """
    response_id = models.AutoField(primary_key=True, verbose_name='응답 ID')
    session = models.ForeignKey(OnboardingSession, on_delete=models.CASCADE, related_name='user_responses', db_column='session_id', verbose_name='세션')
    question = models.ForeignKey(OnboardingQuestion, on_delete=models.CASCADE, related_name='user_responses', db_column='question_code', verbose_name='질문')
    answer = models.ForeignKey(OnboardingAnswer, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_responses', db_column='answer_id', verbose_name='선택지')
    input_value = models.CharField(max_length=255, null=True, blank=True, verbose_name='사용자 입력 값')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, db_column='created_at', verbose_name='생성 일시')
    
    class Meta:
        verbose_name = '온보딩 사용자 응답'
        verbose_name_plural = '온보딩 사용자 응답'
        db_table = 'onboarding_user_response'
        ordering = ['response_id']
    
    def __str__(self):
        return f"Response {self.response_id} - {self.question.question_code}"


class OnboardingSessionCategories(models.Model):
    """
    온보딩 세션 카테고리 테이블 (ERD: ONBOARDING_SESSION_CATEGORIES)
    
    주의: 이 모델은 실제로 사용되지 않습니다.
    실제 코드에서는 OnboardSessCategories (ONBOARD_SESS_CATEGORIES)를 사용합니다.
    """
    session = models.ForeignKey(OnboardingSession, on_delete=models.CASCADE, related_name='session_categories', db_column='session_id', primary_key=True, verbose_name='세션')
    category_name = models.CharField(max_length=50, verbose_name='카테고리명')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name='생성 일시')
    
    class Meta:
        verbose_name = '온보딩 세션 카테고리'
        verbose_name_plural = '온보딩 세션 카테고리'
        db_table = 'onboarding_session_categories'
        unique_together = ['session', 'category_name']
    
    def __str__(self):
        return f"{self.session.session_id} - {self.category_name}"


class OnboardingSessionMainSpaces(models.Model):
    """
    온보딩 세션 주요 공간 테이블 (ERD: ONBOARDING_SESSION_MAIN_SPACES)
    
    주의: 이 모델은 실제로 사용되지 않습니다.
    실제 코드에서는 OnboardSessMainSpaces (ONBOARD_SESS_MAIN_SPACES)를 사용합니다.
    """
    session = models.ForeignKey(OnboardingSession, on_delete=models.CASCADE, related_name='session_main_spaces', db_column='session_id', primary_key=True, verbose_name='세션')
    main_space = models.CharField(max_length=50, verbose_name='주요 공간')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name='생성 일시')
    
    class Meta:
        verbose_name = '온보딩 세션 주요 공간'
        verbose_name_plural = '온보딩 세션 주요 공간'
        db_table = 'onboarding_session_main_spaces'
        unique_together = ['session', 'main_space']
    
    def __str__(self):
        return f"{self.session.session_id} - {self.main_space}"


class OnboardingSessionPriorities(models.Model):
    """
    온보딩 세션 우선순위 테이블 (ERD: ONBOARDING_SESSION_PRIORITIES)
    
    주의: 이 모델은 실제로 사용되지 않습니다.
    실제 코드에서는 OnboardSessPriorities (ONBOARD_SESS_PRIORITIES)를 사용합니다.
    """
    session = models.ForeignKey(OnboardingSession, on_delete=models.CASCADE, related_name='session_priorities', db_column='session_id', verbose_name='세션')
    priority = models.CharField(max_length=20, verbose_name='우선순위 값')
    priority_order = models.IntegerField(verbose_name='우선순위 순서')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name='생성 일시')
    
    class Meta:
        verbose_name = '온보딩 세션 우선순위'
        verbose_name_plural = '온보딩 세션 우선순위'
        db_table = 'onboarding_session_priorities'
        unique_together = ['session', 'priority_order']
        ordering = ['priority_order']
    
    def __str__(self):
        return f"{self.session.session_id} - {self.priority} ({self.priority_order})"


# ONBOARD_SESS_* 테이블들 (ERD에 중복으로 나타남, 별칭으로 처리)
class OnboardSessCategories(models.Model):
    """ONBOARD_SESS_CATEGORIES (ONBOARDING_SESSION_CATEGORIES와 동일)"""
    session = models.ForeignKey(OnboardingSession, on_delete=models.CASCADE, related_name='onboard_sess_categories', db_column='session_id', primary_key=True)
    category_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    class Meta:
        db_table = 'onboard_sess_categories'
        unique_together = ['session', 'category_name']


class OnboardSessMainSpaces(models.Model):
    """ONBOARD_SESS_MAIN_SPACES (ONBOARDING_SESSION_MAIN_SPACES와 동일)"""
    session = models.ForeignKey(OnboardingSession, on_delete=models.CASCADE, related_name='onboard_sess_main_spaces', db_column='session_id', primary_key=True)
    main_space = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    class Meta:
        db_table = 'onboard_sess_main_spaces'
        unique_together = ['session', 'main_space']


class OnboardSessPriorities(models.Model):
    """ONBOARD_SESS_PRIORITIES (ONBOARDING_SESSION_PRIORITIES와 동일)"""
    session = models.ForeignKey(OnboardingSession, on_delete=models.CASCADE, related_name='onboard_sess_priorities', db_column='session_id')
    priority = models.CharField(max_length=20)
    priority_order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    class Meta:
        db_table = 'onboard_sess_priorities'
        unique_together = ['session', 'priority_order']


class OnboardSessRecProducts(models.Model):
    """
    온보딩 세션 추천 제품 테이블 (ERD: ONBOARD_SESS_REC_PRODUCTS)
    """
    session = models.ForeignKey(OnboardingSession, on_delete=models.CASCADE, related_name='onboard_sess_rec_products', db_column='session_id', verbose_name='세션')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='onboard_sess_rec_products', db_column='product_id', verbose_name='제품')
    category_name = models.CharField(max_length=50, null=True, blank=True, verbose_name='카테고리명')
    rank_order = models.IntegerField(null=True, blank=True, verbose_name='카테고리 내 순위')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='점수')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name='생성 일시')
    
    class Meta:
        verbose_name = '온보딩 세션 추천 제품'
        verbose_name_plural = '온보딩 세션 추천 제품'
        db_table = 'onboard_sess_rec_products'
        unique_together = ['session', 'product']
        ordering = ['rank_order']
    
    def __str__(self):
        return f"{self.session.session_id} - {self.product.name} (순위: {self.rank_order})"


class PortfolioSession(models.Model):
    """
    포트폴리오 세션 테이블 (ERD: PORTFOLIO_SESSION)
    """
    portfolio = models.OneToOneField(Portfolio, on_delete=models.CASCADE, related_name='portfolio_session', db_column='portfolio_id', primary_key=True, verbose_name='포트폴리오')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='portfolio_sessions', db_column='member_id', verbose_name='회원')
    session = models.ForeignKey(OnboardingSession, on_delete=models.CASCADE, related_name='portfolio_sessions', db_column='session_id', verbose_name='세션')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='생성 일시')
    
    class Meta:
        verbose_name = '포트폴리오 세션'
        verbose_name_plural = '포트폴리오 세션'
        db_table = 'portfolio_session'
    
    def __str__(self):
        return f"PortfolioSession - {self.portfolio.portfolio_id}"


class StyleMessage(models.Model):
    """
    신규 모델: 스타일 분석 메시지
    포트폴리오 결과 화면의 스타일 분석 메시지 관리
    """
    message_id = models.AutoField(primary_key=True)
    vibe = models.CharField(max_length=20)
    household_size = models.IntegerField(null=True, blank=True)
    budget_level = models.CharField(max_length=20, null=True, blank=True)
    title_text = models.CharField(max_length=500)
    subtitle_text = models.CharField(max_length=1000)
    is_active = models.CharField(max_length=1, default='Y')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'style_message'
        managed = False  # Oracle에서 직접 관리
    
    def __str__(self):
        return f"StyleMessage({self.vibe}, {self.household_size})"


class ShareLink(models.Model):
    """
    신규 모델: 공유 링크
    포트폴리오 외부 공유 링크 관리
    """
    link_id = models.CharField(max_length=50, primary_key=True)
    portfolio = models.ForeignKey('PortfolioSession', on_delete=models.CASCADE, db_column='portfolio_id')
    share_type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    access_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'share_link'
        managed = False  # Oracle에서 직접 관리
    
    def __str__(self):
        return f"ShareLink({self.link_id}, {self.share_type})"


class PortfolioVersion(models.Model):
    """
    신규 모델: 포트폴리오 버전 관리
    포트폴리오 버전 이력 관리 (다시 추천받기 기능)
    """
    version_id = models.AutoField(primary_key=True)
    portfolio = models.ForeignKey('PortfolioSession', on_delete=models.CASCADE, db_column='portfolio_id')
    version_number = models.IntegerField()
    change_type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'portfolio_version'
        managed = False  # Oracle에서 직접 관리
        unique_together = [['portfolio', 'version_number']]
    
    def __str__(self):
        return f"PortfolioVersion({self.portfolio_id}, v{self.version_number})"


class PortfolioProduct(models.Model):
    """
    포트폴리오 제품 테이블 (ERD: PORTFOLIO_PRODUCT)
    """
    id = models.AutoField(primary_key=True, verbose_name='포트폴리오 제품 ID')
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='portfolio_products', db_column='portfolio_id', verbose_name='포트폴리오')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='portfolio_products', db_column='product_id', verbose_name='제품')
    recommend_reason = models.CharField(max_length=500, null=True, blank=True, verbose_name='추천 이유')
    priority = models.IntegerField(null=True, blank=True, verbose_name='우선순위')
    
    class Meta:
        verbose_name = '포트폴리오 제품'
        verbose_name_plural = '포트폴리오 제품'
        db_table = 'portfolio_product'
        ordering = ['priority']
    
    def __str__(self):
        return f"PortfolioProduct {self.id} - {self.product.name}"


class Estimate(models.Model):
    """
    견적 테이블 (ERD: ESTIMATE)
    """
    estimate_id = models.AutoField(primary_key=True, verbose_name='견적 ID')
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='estimates', db_column='portfolio_id', verbose_name='포트폴리오')
    total_price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name='총 가격 (정가 합계)')
    discount_price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name='할인 가격 (할인가 합계)')
    rental_monthly = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name='월 렌탈 비용')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='견적 생성 일시')
    
    class Meta:
        verbose_name = '견적'
        verbose_name_plural = '견적'
        db_table = 'estimate'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Estimate {self.estimate_id} - {self.portfolio.portfolio_id}"


class Consultation(models.Model):
    """
    상담 테이블 (ERD: CONSULTATION)
    """
    consult_id = models.AutoField(primary_key=True, verbose_name='상담 ID')
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='consultations', db_column='member_id', verbose_name='회원')
    portfolio = models.ForeignKey(Portfolio, on_delete=models.SET_NULL, null=True, blank=True, related_name='consultations', db_column='portfolio_id', verbose_name='포트폴리오')
    store_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='매장명')
    reservation_date = models.DateTimeField(null=True, blank=True, verbose_name='상담 예약 일시')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at', verbose_name='상담 신청 일시')
    
    class Meta:
        verbose_name = '상담'
        verbose_name_plural = '상담'
        db_table = 'consultation'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Consultation {self.consult_id} - {self.store_name or '미정'}"


class ProductImage(models.Model):
    """
    제품 이미지 테이블 (ERD: PRODUCT_IMAGE)
    """
    product_image_id = models.AutoField(primary_key=True, verbose_name='제품 이미지 ID')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_images', db_column='product_id', verbose_name='제품')
    image_url = models.CharField(max_length=255, null=True, blank=True, verbose_name='제품 이미지 URL')
    
    class Meta:
        verbose_name = '제품 이미지'
        verbose_name_plural = '제품 이미지'
        db_table = 'product_image'
        ordering = ['product_image_id']
    
    def __str__(self):
        return f"ProductImage {self.product_image_id} - {self.product.name}"


class ProductSpecNew(models.Model):
    """
    제품 스펙 테이블 (ERD: PRODUCT_SPEC) - 기존 ProductSpec과 구분
    """
    spec_id = models.AutoField(primary_key=True, verbose_name='스펙 ID')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_specs_new', db_column='product_id', verbose_name='제품')
    spec_key = models.CharField(max_length=4000, verbose_name='스펙 키')
    spec_value = models.CharField(max_length=4000, null=True, blank=True, verbose_name='스펙 값')
    spec_type = models.CharField(max_length=50, null=True, blank=True, choices=[('COMMON', '공통'), ('SPECIFIC', '특정 variant 전용')], verbose_name='스펙 타입')
    
    class Meta:
        verbose_name = '제품 스펙 (ERD)'
        verbose_name_plural = '제품 스펙 (ERD)'
        db_table = 'product_spec'
        ordering = ['spec_id']
    
    def __str__(self):
        return f"ProductSpec {self.spec_id} - {self.product.name}: {self.spec_key}"


class ProductReviewNew(models.Model):
    """
    제품 리뷰 테이블 (ERD: PRODUCT_REVIEW) - 기존 ProductReview와 구분
    """
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='product_review_new', db_column='product_id', primary_key=True, verbose_name='제품')
    review_vector = models.TextField(null=True, blank=True, verbose_name='리뷰 텍스트 기반 임베딩 벡터')
    family_list = models.TextField(null=True, blank=True, verbose_name='가족 구성 정보')
    size_list = models.TextField(null=True, blank=True, verbose_name='집 크기/평수 정보')
    house_list = models.TextField(null=True, blank=True, verbose_name='주거 형태 정보')
    reason_text = models.TextField(null=True, blank=True, verbose_name='제품 추천 사유 요약')
    
    class Meta:
        verbose_name = '제품 리뷰 (ERD)'
        verbose_name_plural = '제품 리뷰 (ERD)'
        db_table = 'product_review'
    
    def __str__(self):
        return f"ProductReview - {self.product.name}"


class ProdDemoFamilyTypes(models.Model):
    """
    제품 인구통계 - 가족 구성 타입 테이블 (ERD: PROD_DEMO_FAMILY_TYPES)
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='demo_family_types', db_column='product_id', verbose_name='제품')
    family_type = models.CharField(max_length=50, verbose_name='가족 구성 타입')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name='생성 일시')
    
    class Meta:
        verbose_name = '제품 인구통계 - 가족 구성'
        verbose_name_plural = '제품 인구통계 - 가족 구성'
        db_table = 'prod_demo_family_types'
        unique_together = ['product', 'family_type']
    
    def __str__(self):
        return f"{self.product.name} - {self.family_type}"


class ProdDemoHouseSizes(models.Model):
    """
    제품 인구통계 - 집 크기 테이블 (ERD: PROD_DEMO_HOUSE_SIZES)
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='demo_house_sizes', db_column='product_id', verbose_name='제품')
    house_size = models.CharField(max_length=50, verbose_name='집 크기')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name='생성 일시')
    
    class Meta:
        verbose_name = '제품 인구통계 - 집 크기'
        verbose_name_plural = '제품 인구통계 - 집 크기'
        db_table = 'prod_demo_house_sizes'
        unique_together = ['product', 'house_size']
    
    def __str__(self):
        return f"{self.product.name} - {self.house_size}"


class ProdDemoHouseTypes(models.Model):
    """
    제품 인구통계 - 주거 형태 테이블 (ERD: PROD_DEMO_HOUSE_TYPES)
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='demo_house_types', db_column='product_id', verbose_name='제품')
    house_type = models.CharField(max_length=50, verbose_name='주거 형태')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name='생성 일시')
    
    class Meta:
        verbose_name = '제품 인구통계 - 주거 형태'
        verbose_name_plural = '제품 인구통계 - 주거 형태'
        db_table = 'prod_demo_house_types'
        unique_together = ['product', 'house_type']
    
    def __str__(self):
        return f"{self.product.name} - {self.house_type}"


class TasteCategoryScores(models.Model):
    """
    Taste 카테고리 점수 테이블 (ERD: TASTE_CATEGORY_SCORES)
    """
    taste = models.ForeignKey(TasteConfig, on_delete=models.CASCADE, related_name='category_scores', db_column='taste_id', verbose_name='Taste')
    category_name = models.CharField(max_length=50, verbose_name='카테고리명')
    score = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='카테고리 점수')
    is_recommended = models.CharField(max_length=1, null=True, blank=True, choices=[('Y', '추천'), ('N', '비추천')], default='N', verbose_name='추천 카테고리 여부')
    is_ill_suited = models.CharField(max_length=1, null=True, blank=True, choices=[('Y', '부적합'), ('N', '적합')], default='N', verbose_name='부적합 카테고리 여부')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name='생성 일시')
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name='수정 일시')
    
    class Meta:
        verbose_name = 'Taste 카테고리 점수'
        verbose_name_plural = 'Taste 카테고리 점수'
        db_table = 'taste_category_scores'
        unique_together = ['taste', 'category_name']
        ordering = ['-score']
    
    def __str__(self):
        return f"Taste {self.taste.taste_id} - {self.category_name}: {self.score}"


class TasteRecommendedProducts(models.Model):
    """
    Taste 추천 제품 테이블 (ERD: TASTE_RECOMMENDED_PRODUCTS)
    """
    taste = models.ForeignKey(TasteConfig, on_delete=models.CASCADE, related_name='recommended_products_new', db_column='taste_id', verbose_name='Taste')
    category_name = models.CharField(max_length=50, verbose_name='카테고리명')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='taste_recommended_products', db_column='product_id', verbose_name='제품')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='제품 점수')
    rank_order = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)], verbose_name='카테고리 내 순위')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name='생성 일시')
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name='수정 일시')
    
    class Meta:
        verbose_name = 'Taste 추천 제품'
        verbose_name_plural = 'Taste 추천 제품'
        db_table = 'taste_recommended_products'
        unique_together = ['taste', 'category_name', 'product']
        ordering = ['rank_order']
    
    def __str__(self):
        return f"Taste {self.taste.taste_id} - {self.category_name} - {self.product.name} (순위: {self.rank_order})"


class UserSamplePurchasedItems(models.Model):
    """
    사용자 샘플 구매 항목 테이블 (ERD: USER_SAMPLE_PURCHASED_ITEMS)
    
    주의: 이 모델은 실제로 사용되지 않습니다.
    모델만 정의되어 있고 실제 코드에서 조회/사용하지 않습니다.
    """
    user = models.ForeignKey(UserSample, on_delete=models.CASCADE, related_name='sample_purchased_items', db_column='user_id', verbose_name='사용자')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='user_sample_purchased_items', db_column='product_id', verbose_name='제품')
    purchased_at = models.DateTimeField(null=True, blank=True, verbose_name='구매 일시')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name='생성 일시')
    
    class Meta:
        verbose_name = '사용자 샘플 구매 항목'
        verbose_name_plural = '사용자 샘플 구매 항목'
        db_table = 'user_sample_purchased_items'
        unique_together = ['user', 'product']
        ordering = ['-purchased_at']
    
    def __str__(self):
        return f"{self.user.user_id} - {self.product.name}"


class UserSampleRecommendations(models.Model):
    """
    사용자 샘플 추천 테이블 (ERD: USER_SAMPLE_RECOMMENDATIONS)
    
    주의: 이 모델은 실제로 사용되지 않습니다.
    모델만 정의되어 있고 실제 코드에서 조회/사용하지 않습니다.
    """
    user = models.ForeignKey(UserSample, on_delete=models.CASCADE, related_name='recommendations', db_column='user_id', verbose_name='사용자')
    category_name = models.CharField(max_length=50, verbose_name='카테고리명')
    recommended_value = models.CharField(max_length=100, null=True, blank=True, verbose_name='추천 값')
    recommended_unit = models.CharField(max_length=20, null=True, blank=True, verbose_name='추천 단위')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name='생성 일시')
    
    class Meta:
        verbose_name = '사용자 샘플 추천'
        verbose_name_plural = '사용자 샘플 추천'
        db_table = 'user_sample_recommendations'
        unique_together = ['user', 'category_name']
        ordering = ['category_name']
    
    def __str__(self):
        return f"{self.user.user_id} - {self.category_name}: {self.recommended_value} {self.recommended_unit}"


class CategoryCommonSpec(models.Model):
    """
    카테고리 공통 스펙 테이블 (ERD: CATEGORY_COMMON_SPEC)
    """
    common_id = models.AutoField(primary_key=True, verbose_name='공통 스펙 ID')
    main_category = models.CharField(max_length=100, verbose_name='메인 카테고리')
    spec_key = models.CharField(max_length=150, verbose_name='스펙 키')
    
    class Meta:
        verbose_name = '카테고리 공통 스펙'
        verbose_name_plural = '카테고리 공통 스펙'
        db_table = 'category_common_spec'
        unique_together = ['main_category', 'spec_key']
        ordering = ['main_category', 'spec_key']
    
    def __str__(self):
        return f"{self.main_category} - {self.spec_key}"
