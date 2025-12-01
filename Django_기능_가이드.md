# Django 주요 기능 가이드

## 🎯 Django란?

Django는 Python으로 작성된 웹 프레임워크로, **"배터리 포함"** 철학을 가지고 있습니다.
즉, 웹 개발에 필요한 대부분의 기능이 이미 내장되어 있습니다!

## 📚 Django의 주요 기능들

### 1. **ORM (Object-Relational Mapping)** ⭐⭐⭐
**데이터베이스 작업을 Python 코드로 쉽게 처리**

**현재 프로젝트에서 사용 중:**
```python
# api/models.py
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
# 사용 예시
products = Product.objects.filter(category='TV', price__gte=1000000)
```

**장점:**
- SQL을 직접 작성하지 않아도 됨
- 데이터베이스 종류와 무관하게 동작
- 타입 안정성

**활용 방법:**
```python
# 복잡한 쿼리도 쉽게!
Product.objects.filter(
    category='TV',
    price__range=(500000, 2000000),
    is_active=True
).order_by('-price')[:10]
```

---

### 2. **Admin 인터페이스** ⭐⭐⭐
**데이터베이스 관리를 위한 웹 인터페이스 (자동 생성!)**

**현재 상태:**
- 기본 Admin만 사용 중
- 커스터마이징 가능

**활용 방법:**
```python
# api/admin.py에 추가
from django.contrib import admin
from .models import Product, Portfolio

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'model_number']
    ordering = ['-price']

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['portfolio_id', 'user_id', 'style_type', 'created_at']
    list_filter = ['style_type', 'status']
    readonly_fields = ['portfolio_id', 'created_at']
```

**접속:**
```
http://127.0.0.1:8000/admin/
```

**장점:**
- 데이터베이스 내용을 웹에서 직접 확인/수정 가능
- 코드 한 줄로 강력한 관리 인터페이스 생성
- 권한 관리 가능

---

### 3. **템플릿 시스템** ⭐⭐
**HTML을 동적으로 생성**

**현재 프로젝트에서 사용 중:**
```html
<!-- api/templates/main.html -->
{% load static %}
{{ kakao_js_key }}
```

**활용 방법:**
```html
<!-- 조건문 -->
{% if user.is_authenticated %}
    <p>안녕하세요, {{ user.username }}님!</p>
{% else %}
    <p>로그인이 필요합니다.</p>
{% endif %}

<!-- 반복문 -->
{% for product in products %}
    <div>{{ product.name }} - {{ product.price }}원</div>
{% endfor %}

<!-- 필터 -->
{{ product.price|floatformat:0 }}원
{{ product.name|truncatewords:10 }}
```

---

### 4. **폼 처리 (Forms)** ⭐⭐
**사용자 입력을 쉽게 처리**

**활용 예시:**
```python
# api/forms.py (새로 생성 가능)
from django import forms
from .models import Product

class ProductSearchForm(forms.Form):
    category = forms.ChoiceField(
        choices=[('TV', 'TV'), ('LIVING', '생활가전')],
        required=False
    )
    min_price = forms.IntegerField(required=False, min_value=0)
    max_price = forms.IntegerField(required=False, min_value=0)
    
    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        if min_price and max_price and min_price > max_price:
            raise forms.ValidationError("최소 가격이 최대 가격보다 클 수 없습니다.")
        
        return cleaned_data
```

**템플릿에서 사용:**
```html
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">검색</button>
</form>
```

---

### 5. **인증/권한 시스템** ⭐⭐⭐
**사용자 로그인, 권한 관리**

**활용 방법:**
```python
# 사용자 인증
from django.contrib.auth import authenticate, login

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')
```

**템플릿에서:**
```html
{% if user.is_authenticated %}
    <p>로그인: {{ user.username }}</p>
    <a href="{% url 'logout' %}">로그아웃</a>
{% else %}
    <a href="{% url 'login' %}">로그인</a>
{% endif %}
```

**현재 프로젝트에 추가 가능:**
- 카카오 로그인 연동
- 사용자별 포트폴리오 관리
- 권한별 기능 제한

---

### 6. **세션 관리** ⭐⭐
**사용자 상태 저장**

**활용 방법:**
```python
# 세션에 데이터 저장
request.session['onboarding_data'] = {
    'household_size': 4,
    'has_pet': True
}

# 세션에서 데이터 가져오기
onboarding_data = request.session.get('onboarding_data', {})
```

**현재 프로젝트 활용:**
- 온보딩 진행 상황 저장
- 임시 추천 결과 저장
- 사용자 선호도 저장

---

### 7. **캐싱** ⭐
**성능 향상을 위한 캐싱**

**활용 방법:**
```python
from django.core.cache import cache

# 캐시에 저장
cache.set('recommendations_user_123', result, timeout=3600)

# 캐시에서 가져오기
cached_result = cache.get('recommendations_user_123')
if cached_result:
    return cached_result
```

**현재 프로젝트 활용:**
- 추천 결과 캐싱 (같은 조건이면 재계산 안 함)
- 제품 리스트 캐싱

---

### 8. **관리 명령어 (Management Commands)** ⭐⭐
**커스텀 명령어 생성**

**현재 프로젝트에 이미 있음:**
```python
# api/management/commands/import_all_data.py
python manage.py import_all_data
```

**추가 명령어 예시:**
```python
# api/management/commands/update_scores.py
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = '모든 제품의 점수를 재계산합니다'
    
    def handle(self, *args, **options):
        products = Product.objects.all()
        for product in products:
            # 점수 재계산 로직
            pass
        self.stdout.write(self.style.SUCCESS('점수 업데이트 완료!'))
```

**사용:**
```bash
python manage.py update_scores
```

---

### 9. **시그널 (Signals)** ⭐
**이벤트 기반 프로그래밍**

**활용 방법:**
```python
# api/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Portfolio

@receiver(post_save, sender=Portfolio)
def portfolio_created(sender, instance, created, **kwargs):
    if created:
        print(f'새 포트폴리오 생성: {instance.portfolio_id}')
        # 자동으로 이메일 발송, 통계 업데이트 등
```

---

### 10. **국제화 (i18n)** ⭐
**다국어 지원**

**활용 방법:**
```python
# settings.py
LANGUAGE_CODE = 'ko-kr'
USE_I18N = True

# 템플릿에서
{% load i18n %}
{% trans "Hello" %}
```

---

### 11. **정적 파일 관리** ⭐
**CSS, JS, 이미지 파일 관리**

**현재 프로젝트에서 사용 중:**
```html
{% load static %}
<link rel="stylesheet" href="{% static 'css/style.css' %}">
<script src="{% static 'js/script.js' %}"></script>
```

---

### 12. **미들웨어** ⭐
**요청/응답 처리 중간에 로직 실행**

**활용 예시:**
```python
# api/middleware.py
class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 요청 전 처리
        print(f'요청: {request.path}')
        
        response = self.get_response(request)
        
        # 응답 후 처리
        print(f'응답: {response.status_code}')
        
        return response
```

---

## 🎯 현재 프로젝트에서 활용 가능한 기능

### 1. **Admin 커스터마이징** (추천!)
```python
# api/admin.py에 추가
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price']
    list_filter = ['category']
    search_fields = ['name']
```

**효과:**
- `/admin/`에서 제품을 쉽게 관리
- 검색, 필터링 기능 자동 제공

### 2. **사용자 인증 추가**
```python
# 카카오 로그인 연동
# 사용자별 포트폴리오 관리
# 권한별 기능 제한
```

### 3. **폼 처리 개선**
```python
# 온보딩 폼을 Django Form으로 변환
# 자동 검증, 에러 처리
```

### 4. **캐싱 추가**
```python
# 추천 결과 캐싱
# 같은 조건이면 재계산 안 함
```

### 5. **세션 활용**
```python
# 온보딩 진행 상황 저장
# 임시 데이터 저장
```

---

## 🚀 빠른 시작 가이드

### 1. Admin 커스터마이징 (가장 쉬움!)

**api/admin.py 수정:**
```python
from django.contrib import admin
from .models import Product, Portfolio, OnboardingSession

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'model_number']

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['portfolio_id', 'user_id', 'style_type', 'created_at']
    list_filter = ['style_type', 'status']
```

**효과:**
- `/admin/` 접속하면 깔끔한 관리 인터페이스
- 검색, 필터링 자동 제공

### 2. 사용자 인증 추가

**간단한 로그인 시스템:**
```python
# api/views.py
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})
```

### 3. 폼 처리

**온보딩 폼을 Django Form으로:**
```python
# api/forms.py
from django import forms

class OnboardingForm(forms.Form):
    household_size = forms.IntegerField(min_value=1, max_value=10)
    has_pet = forms.BooleanField(required=False)
    # 자동 검증!
```

---

## 📊 Django 기능 우선순위

### 필수 기능 (이미 사용 중)
- ✅ ORM (데이터베이스 작업)
- ✅ 템플릿 시스템
- ✅ 정적 파일 관리

### 추천 기능 (추가하면 좋음)
- ⭐ Admin 커스터마이징
- ⭐ 사용자 인증
- ⭐ 폼 처리
- ⭐ 세션 관리

### 고급 기능 (나중에)
- 캐싱
- 시그널
- 미들웨어
- 국제화

---

## 🎯 다음 단계

어떤 기능부터 시작할까요?

1. **Admin 커스터마이징** - 가장 쉬움, 즉시 효과
2. **사용자 인증** - 카카오 로그인 연동
3. **폼 처리** - 온보딩 폼 개선
4. **캐싱** - 성능 향상

원하시는 기능을 알려주시면 바로 구현해드리겠습니다!

