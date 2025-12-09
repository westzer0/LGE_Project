# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Cart(models.Model):
    """
    CART 테이블
    """

    cart_id = models.AutoField(blank=True, null=True)
    member_id = models.CharField(max_length=30)
    created_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'CART'
        # primary_key = ['CART_ID']

    def __str__(self):
        return f"CART({self.cart_id})"


class Cart_item(models.Model):
    """
    CART_ITEM 테이블
    """

    cart_item_id = models.AutoField(blank=True, null=True)
    cart_id = models.IntegerField(blank=True, null=True)
    product_id = models.IntegerField(blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'CART_ITEM'
        # primary_key = ['CART_ITEM_ID']

    def __str__(self):
        return f"CART_ITEM({self.cart_item_id})"


class Category_common_spec(models.Model):
    """
    CATEGORY_COMMON_SPEC 테이블
    """

    common_id = models.AutoField(blank=True, null=True)
    main_category = models.CharField(max_length=100)
    spec_key = models.CharField(max_length=150)

    class Meta:
        db_table = 'CATEGORY_COMMON_SPEC'
        # primary_key = ['COMMON_ID']

    def __str__(self):
        return f"CATEGORY_COMMON_SPEC({self.common_id})"


class Consultation(models.Model):
    """
    CONSULTATION 테이블
    """

    consult_id = models.AutoField(blank=True, null=True)
    member_id = models.CharField(max_length=30, blank=True, null=True)
    portfolio_id = models.IntegerField(blank=True, null=True)
    store_name = models.CharField(max_length=255, blank=True, null=True)
    reservation_date = models.DateTimeField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'CONSULTATION'
        # primary_key = ['CONSULT_ID']

    def __str__(self):
        return f"CONSULTATION({self.consult_id})"


class Estimate(models.Model):
    """
    ESTIMATE 테이블
    """

    estimate_id = models.AutoField(blank=True, null=True)
    portfolio_id = models.IntegerField(blank=True, null=True)
    total_price = models.IntegerField(blank=True, null=True)
    discount_price = models.IntegerField(blank=True, null=True)
    rental_monthly = models.IntegerField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ESTIMATE'
        # primary_key = ['ESTIMATE_ID']

    def __str__(self):
        return f"ESTIMATE({self.estimate_id})"


class Member(models.Model):
    """
    MEMBER 테이블
    """

    member_id = models.CharField(max_length=30)
    password = models.CharField(max_length=255)
    name = models.CharField(max_length=100)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    contact = models.CharField(max_length=20, blank=True, null=True)
    point = models.IntegerField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    taste = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'MEMBER'
        # primary_key = ['MEMBER_ID']

    def __str__(self):
        return f"MEMBER({self.member_id})"


class Onboarding_answer(models.Model):
    """
    ONBOARDING_ANSWER 테이블
    """

    answer_id = models.AutoField(blank=True, null=True)
    question_code = models.CharField(max_length=50)
    answer_value = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    answer_text = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'ONBOARDING_ANSWER'
        # primary_key = ['ANSWER_ID']

    def __str__(self):
        return f"ONBOARDING_ANSWER({self.answer_id})"


class Onboarding_question(models.Model):
    """
    ONBOARDING_QUESTION 테이블
    """

    question_code = models.CharField(max_length=50)
    question_text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=50)
    is_required = models.CharField(max_length=5)
    created_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ONBOARDING_QUESTION'
        # primary_key = ['QUESTION_CODE']

    def __str__(self):
        return f"ONBOARDING_QUESTION({self.question_code})"


class Onboarding_session(models.Model):
    """
    ONBOARDING_SESSION 테이블
    """

    session_id = models.AutoField(blank=True, null=True)
    member_id = models.CharField(max_length=30)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    vibe = models.CharField(max_length=20, blank=True, null=True)
    household_size = models.IntegerField(blank=True, null=True)
    has_pet = models.CharField(max_length=1, blank=True, null=True)
    housing_type = models.CharField(max_length=20, blank=True, null=True)
    pyung = models.IntegerField(blank=True, null=True)
    main_space = models.TextField(blank=True, null=True)
    cooking = models.CharField(max_length=20, blank=True, null=True)
    laundry = models.CharField(max_length=20, blank=True, null=True)
    media = models.CharField(max_length=20, blank=True, null=True)
    priority = models.CharField(max_length=20, blank=True, null=True)
    priority_list = models.TextField(blank=True, null=True)
    budget_level = models.CharField(max_length=20, blank=True, null=True)
    selected_categories = models.TextField(blank=True, null=True)
    recommended_products = models.TextField(blank=True, null=True)
    recommendation_result = models.TextField(blank=True, null=True)
    current_step = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    user_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'ONBOARDING_SESSION'
        # primary_key = ['SESSION_ID']

    def __str__(self):
        return f"ONBOARDING_SESSION({self.session_id})"


class Onboarding_session_categories(models.Model):
    """
    ONBOARDING_SESSION_CATEGORIES 테이블
    """

    session_id = models.AutoField(blank=True, null=True)
    category_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ONBOARDING_SESSION_CATEGORIES'
        # primary_key = ['SESSION_ID', 'CATEGORY_NAME']

    def __str__(self):
        return f"ONBOARDING_SESSION_CATEGORIES({self.session_id})"


class Onboarding_session_main_spaces(models.Model):
    """
    ONBOARDING_SESSION_MAIN_SPACES 테이블
    """

    session_id = models.AutoField(blank=True, null=True)
    main_space = models.CharField(max_length=50)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ONBOARDING_SESSION_MAIN_SPACES'
        # primary_key = ['SESSION_ID', 'MAIN_SPACE']

    def __str__(self):
        return f"ONBOARDING_SESSION_MAIN_SPACES({self.session_id})"


class Onboarding_session_priorities(models.Model):
    """
    ONBOARDING_SESSION_PRIORITIES 테이블
    """

    session_id = models.AutoField(blank=True, null=True)
    priority = models.CharField(max_length=20)
    priority_order = models.AutoField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ONBOARDING_SESSION_PRIORITIES'
        # primary_key = ['SESSION_ID', 'PRIORITY_ORDER']

    def __str__(self):
        return f"ONBOARDING_SESSION_PRIORITIES({self.session_id})"


class Onboarding_user_response(models.Model):
    """
    ONBOARDING_USER_RESPONSE 테이블
    """

    response_id = models.AutoField(blank=True, null=True)
    session_id = models.IntegerField(blank=True, null=True)
    question_code = models.CharField(max_length=50)
    answer_id = models.IntegerField(blank=True, null=True)
    input_value = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ONBOARDING_USER_RESPONSE'
        # primary_key = ['RESPONSE_ID']

    def __str__(self):
        return f"ONBOARDING_USER_RESPONSE({self.response_id})"


class Onboard_sess_categories(models.Model):
    """
    ONBOARD_SESS_CATEGORIES 테이블
    """

    session_id = models.AutoField(blank=True, null=True)
    category_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ONBOARD_SESS_CATEGORIES'
        # primary_key = ['SESSION_ID', 'CATEGORY_NAME']

    def __str__(self):
        return f"ONBOARD_SESS_CATEGORIES({self.session_id})"


class Onboard_sess_main_spaces(models.Model):
    """
    ONBOARD_SESS_MAIN_SPACES 테이블
    """

    session_id = models.AutoField(blank=True, null=True)
    main_space = models.CharField(max_length=50)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ONBOARD_SESS_MAIN_SPACES'
        # primary_key = ['SESSION_ID', 'MAIN_SPACE']

    def __str__(self):
        return f"ONBOARD_SESS_MAIN_SPACES({self.session_id})"


class Onboard_sess_priorities(models.Model):
    """
    ONBOARD_SESS_PRIORITIES 테이블
    """

    session_id = models.AutoField(blank=True, null=True)
    priority = models.CharField(max_length=20)
    priority_order = models.AutoField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ONBOARD_SESS_PRIORITIES'
        # primary_key = ['SESSION_ID', 'PRIORITY_ORDER']

    def __str__(self):
        return f"ONBOARD_SESS_PRIORITIES({self.session_id})"


class Onboard_sess_rec_products(models.Model):
    """
    ONBOARD_SESS_REC_PRODUCTS 테이블
    """

    session_id = models.AutoField(blank=True, null=True)
    product_id = models.AutoField(blank=True, null=True)
    category_name = models.CharField(max_length=50, blank=True, null=True)
    rank_order = models.IntegerField(blank=True, null=True)
    score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ONBOARD_SESS_REC_PRODUCTS'
        # primary_key = ['SESSION_ID', 'PRODUCT_ID']

    def __str__(self):
        return f"ONBOARD_SESS_REC_PRODUCTS({self.session_id})"


class Orders(models.Model):
    """
    ORDERS 테이블
    """

    order_id = models.AutoField(blank=True, null=True)
    member_id = models.CharField(max_length=30)
    order_date = models.DateTimeField(blank=True, null=True)
    total_amount = models.IntegerField(blank=True, null=True)
    order_status = models.CharField(max_length=50, blank=True, null=True)
    payment_status = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'ORDERS'
        # primary_key = ['ORDER_ID']

    def __str__(self):
        return f"ORDERS({self.order_id})"


class Order_detail(models.Model):
    """
    ORDER_DETAIL 테이블
    """

    detail_id = models.AutoField(blank=True, null=True)
    order_id = models.IntegerField(blank=True, null=True)
    product_id = models.IntegerField(blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'ORDER_DETAIL'
        # primary_key = ['DETAIL_ID']

    def __str__(self):
        return f"ORDER_DETAIL({self.detail_id})"


class Payment(models.Model):
    """
    PAYMENT 테이블
    """

    payment_id = models.AutoField(blank=True, null=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    order_id = models.IntegerField(blank=True, null=True)
    payment_status = models.CharField(max_length=50, blank=True, null=True)
    method = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'PAYMENT'
        # primary_key = ['PAYMENT_ID']

    def __str__(self):
        return f"PAYMENT({self.payment_id})"


class Portfolio_product(models.Model):
    """
    PORTFOLIO_PRODUCT 테이블
    """

    id = models.AutoField(blank=True, null=True)
    portfolio_id = models.IntegerField(blank=True, null=True)
    product_id = models.IntegerField(blank=True, null=True)
    recommend_reason = models.CharField(max_length=500, blank=True, null=True)
    priority = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'PORTFOLIO_PRODUCT'
        # primary_key = ['ID']

    def __str__(self):
        return f"PORTFOLIO_PRODUCT({self.id})"


class Portfolio_session(models.Model):
    """
    PORTFOLIO_SESSION 테이블
    """

    portfolio_id = models.AutoField(blank=True, null=True)
    member_id = models.CharField(max_length=30)
    session_id = models.IntegerField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'PORTFOLIO_SESSION'
        # primary_key = ['PORTFOLIO_ID']

    def __str__(self):
        return f"PORTFOLIO_SESSION({self.portfolio_id})"


class Product(models.Model):
    """
    PRODUCT 테이블
    """

    product_id = models.AutoField(blank=True, null=True)
    product_name = models.CharField(max_length=255)
    main_category = models.CharField(max_length=100)
    sub_category = models.CharField(max_length=100, blank=True, null=True)
    model_code = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    price = models.IntegerField(blank=True, null=True)
    rating = models.CharField(max_length=255, blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'PRODUCT'
        # primary_key = ['PRODUCT_ID']

    def __str__(self):
        return f"PRODUCT({self.product_id})"


class Product_image(models.Model):
    """
    PRODUCT_IMAGE 테이블
    """

    product_image_id = models.AutoField(blank=True, null=True)
    product_id = models.IntegerField(blank=True, null=True)
    image_url = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'PRODUCT_IMAGE'
        # primary_key = ['PRODUCT_IMAGE_ID']

    def __str__(self):
        return f"PRODUCT_IMAGE({self.product_image_id})"


class Product_review(models.Model):
    """
    PRODUCT_REVIEW 테이블
    """

    product_id = models.BigAutoField(blank=True, null=True)
    review_vector = models.TextField(blank=True, null=True)
    family_list = models.TextField(blank=True, null=True)
    size_list = models.TextField(blank=True, null=True)
    house_list = models.TextField(blank=True, null=True)
    reason_text = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'PRODUCT_REVIEW'
        # primary_key = ['PRODUCT_ID']

    def __str__(self):
        return f"PRODUCT_REVIEW({self.product_id})"


class Product_spec(models.Model):
    """
    PRODUCT_SPEC 테이블
    """

    spec_id = models.AutoField(blank=True, null=True)
    product_id = models.IntegerField(blank=True, null=True)
    spec_key = models.CharField(max_length=4000)
    spec_value = models.CharField(max_length=4000, blank=True, null=True)
    spec_type = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'PRODUCT_SPEC'
        # primary_key = ['SPEC_ID']

    def __str__(self):
        return f"PRODUCT_SPEC({self.spec_id})"


class Prod_demo_family_types(models.Model):
    """
    PROD_DEMO_FAMILY_TYPES 테이블
    """

    product_id = models.AutoField(blank=True, null=True)
    family_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'PROD_DEMO_FAMILY_TYPES'
        # primary_key = ['PRODUCT_ID', 'FAMILY_TYPE']

    def __str__(self):
        return f"PROD_DEMO_FAMILY_TYPES({self.product_id})"


class Prod_demo_house_sizes(models.Model):
    """
    PROD_DEMO_HOUSE_SIZES 테이블
    """

    product_id = models.AutoField(blank=True, null=True)
    house_size = models.CharField(max_length=50)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'PROD_DEMO_HOUSE_SIZES'
        # primary_key = ['PRODUCT_ID', 'HOUSE_SIZE']

    def __str__(self):
        return f"PROD_DEMO_HOUSE_SIZES({self.product_id})"


class Prod_demo_house_types(models.Model):
    """
    PROD_DEMO_HOUSE_TYPES 테이블
    """

    product_id = models.AutoField(blank=True, null=True)
    house_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'PROD_DEMO_HOUSE_TYPES'
        # primary_key = ['PRODUCT_ID', 'HOUSE_TYPE']

    def __str__(self):
        return f"PROD_DEMO_HOUSE_TYPES({self.product_id})"


class Taste_category_scores(models.Model):
    """
    TASTE_CATEGORY_SCORES 테이블
    """

    taste_id = models.AutoField(blank=True, null=True)
    category_name = models.CharField(max_length=50)
    score = models.DecimalField(max_digits=19, decimal_places=2)
    is_recommended = models.CharField(max_length=1, blank=True, null=True)
    is_ill_suited = models.CharField(max_length=1, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'TASTE_CATEGORY_SCORES'
        # primary_key = ['TASTE_ID', 'CATEGORY_NAME']

    def __str__(self):
        return f"TASTE_CATEGORY_SCORES({self.taste_id})"


class Taste_config(models.Model):
    """
    TASTE_CONFIG 테이블
    """

    taste_id = models.AutoField(blank=True, null=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    representative_vibe = models.CharField(max_length=20, blank=True, null=True)
    representative_household_size = models.IntegerField(blank=True, null=True)
    representative_main_space = models.CharField(max_length=50, blank=True, null=True)
    representative_has_pet = models.CharField(max_length=1, blank=True, null=True)
    representative_priority = models.CharField(max_length=20, blank=True, null=True)
    representative_budget_level = models.CharField(max_length=20, blank=True, null=True)
    recommended_categories = models.TextField(blank=True, null=True)
    recommended_products = models.TextField(blank=True, null=True)
    is_active = models.CharField(max_length=1, blank=True, null=True)
    auto_generated = models.CharField(max_length=1, blank=True, null=True)
    last_simulation_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    category_scores = models.TextField(blank=True, null=True)
    프로젝터_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    스탠바이미_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    오디오_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    사운드바_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    김치냉장고_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    건조기_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    워시타워_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    전자레인지_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    오븐_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    공기청정기_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    가습기_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    제습기_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    와인셀러_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    objet_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    signature_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    냉장고_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    세탁기_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    에어컨_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    청소기_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    ill_suited_categories = models.TextField(blank=True, null=True)
    정수기_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    tv_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    aihome_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    식기세척기_score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    recommended_product_scores = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'TASTE_CONFIG'
        # primary_key = ['TASTE_ID']

    def __str__(self):
        return f"TASTE_CONFIG({self.taste_id})"


class Taste_recommended_products(models.Model):
    """
    TASTE_RECOMMENDED_PRODUCTS 테이블
    """

    taste_id = models.AutoField(blank=True, null=True)
    category_name = models.CharField(max_length=50)
    product_id = models.AutoField(blank=True, null=True)
    score = models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)
    rank_order = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'TASTE_RECOMMENDED_PRODUCTS'
        # primary_key = ['TASTE_ID', 'CATEGORY_NAME', 'PRODUCT_ID']

    def __str__(self):
        return f"TASTE_RECOMMENDED_PRODUCTS({self.taste_id})"


class User_sample_purchased_items(models.Model):
    """
    USER_SAMPLE_PURCHASED_ITEMS 테이블
    """

    user_id = models.CharField(max_length=50)
    product_id = models.AutoField(blank=True, null=True)
    purchased_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'USER_SAMPLE_PURCHASED_ITEMS'
        # primary_key = ['USER_ID', 'PRODUCT_ID']

    def __str__(self):
        return f"USER_SAMPLE_PURCHASED_ITEMS({self.user_id})"


class User_sample_recommendations(models.Model):
    """
    USER_SAMPLE_RECOMMENDATIONS 테이블
    """

    user_id = models.CharField(max_length=50)
    category_name = models.CharField(max_length=50)
    recommended_value = models.CharField(max_length=100, blank=True, null=True)
    recommended_unit = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'USER_SAMPLE_RECOMMENDATIONS'
        # primary_key = ['USER_ID', 'CATEGORY_NAME']

    def __str__(self):
        return f"USER_SAMPLE_RECOMMENDATIONS({self.user_id})"

