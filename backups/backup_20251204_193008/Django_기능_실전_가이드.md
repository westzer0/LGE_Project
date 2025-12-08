# Django 기능 실전 가이드

## 🎯 Django의 핵심 기능들

Django는 **"배터리 포함"** 프레임워크입니다. 즉, 웹 개발에 필요한 대부분의 기능이 이미 내장되어 있어서 **별도의 API 키나 외부 서비스 없이** 바로 사용할 수 있습니다!

---

## 📚 현재 프로젝트에서 이미 사용 중인 기능

### 1. **ORM (Object-Relational Mapping)** ✅
**데이터베이스 작업을 Python 코드로**

```python
# api/models.py
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    
# 사용 예시 (이미 사용 중)
products = Product.objects.filter(category='TV', price__gte=1000000)
```

**장점:**
- SQL을 직접 작성할 필요 없음
- 타입 안정성
- 데이터베이스 종류와 무관

---

### 2. **Admin 인터페이스** ✅ (일부 설정됨)
**데이터베이스 관리 웹 인터페이스**

**현재 상태:**
- `api/admin.py`에 일부 설정되어 있음
- 더 커스터마이징 가능

**접속 방법:**
```
1. 관리자 계정 생성:
   python manage.py createsuperuser

2. 서버 실행:
   python manage.py runserver

3. 브라우저에서 접속:
   http://127.0.0.1:8000/admin/
```

**활용:**
- 제품 데이터 확인/수정
- 포트폴리오 관리
- 온보딩 세션 확인

---

### 3. **템플릿 시스템** ✅
**HTML을 동적으로 생성**

```html
<!-- api/templates/main.html -->
{% load static %}
{{ kakao_js_key }}
```

---

## 🚀 추가로 활용 가능한 Django 기능들

### 1. **사용자 인증 시스템** ⭐⭐⭐
**로그인, 회원가입, 권한 관리**

**활용 예시:**
```python
# api/views.py에 추가
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')
    return render(request, 'login.html')

@login_required
def my_portfolios(request):
    # 로그인한 사용자의 포트폴리오만 보기
    portfolios = Portfolio.objects.filter(user_id=request.user.username)
    return render(request, 'my_portfolios.html', {'portfolios': portfolios})
```

**효과:**
- 사용자별 포트폴리오 관리
- 개인화된 추천
- 카카오 로그인 연동 가능

---

### 2. **폼 처리 (Forms)** ⭐⭐
**사용자 입력 검증 및 처리**

**활용 예시:**
```python
# api/forms.py (새로 생성)
from django import forms

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

**템플릿에서:**
```html
<form method="get">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">검색</button>
</form>
```

**효과:**
- 자동 입력 검증
- 에러 메시지 자동 표시
- 코드 간결화

---

### 3. **세션 관리** ⭐⭐
**사용자 상태 저장**

**활용 예시:**
```python
# 온보딩 진행 상황 저장
request.session['onboarding_data'] = {
    'household_size': 4,
    'has_pet': True,
    'current_step': 2
}

# 나중에 가져오기
onboarding_data = request.session.get('onboarding_data', {})
```

**효과:**
- 온보딩 중간에 나가도 다시 돌아올 수 있음
- 임시 데이터 저장
- 로그인 없이도 사용자 상태 관리

---

### 4. **캐싱** ⭐
**성능 향상**

**활용 예시:**
```python
from django.core.cache import cache

# 추천 결과 캐싱
cache_key = f'recommendations_{user_profile_hash}'
cached_result = cache.get(cache_key)

if cached_result:
    return cached_result  # 재계산 안 함!

# 캐시에 저장 (1시간)
result = recommendation_engine.get_recommendations(user_profile)
cache.set(cache_key, result, timeout=3600)
return result
```

**효과:**
- 같은 조건이면 재계산 안 함
- 응답 속도 향상
- 서버 부하 감소

---

### 5. **관리 명령어** ⭐⭐
**커스텀 명령어 생성**

**현재 프로젝트에 이미 있음:**
```bash
python manage.py import_all_data
python manage.py check_data
```

**추가 명령어 예시:**
```python
# api/management/commands/update_recommendations.py
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = '모든 사용자에게 추천 결과 업데이트'
    
    def handle(self, *args, **options):
        sessions = OnboardingSession.objects.filter(status='completed')
        for session in sessions:
            # 추천 결과 재계산
            pass
        self.stdout.write(self.style.SUCCESS('업데이트 완료!'))
```

**사용:**
```bash
python manage.py update_recommendations
```

---

### 6. **시그널 (Signals)** ⭐
**이벤트 기반 프로그래밍**

**활용 예시:**
```python
# api/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Portfolio

@receiver(post_save, sender=Portfolio)
def portfolio_created(sender, instance, created, **kwargs):
    if created:
        print(f'새 포트폴리오 생성: {instance.portfolio_id}')
        # 자동으로 통계 업데이트, 이메일 발송 등
```

---

### 7. **미들웨어** ⭐
**요청/응답 처리 중간에 로직 실행**

**활용 예시:**
```python
# api/middleware.py
class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 요청 전 처리
        print(f'[요청] {request.method} {request.path}')
        
        response = self.get_response(request)
        
        # 응답 후 처리
        print(f'[응답] {response.status_code}')
        
        return response
```

---

## 🎯 현재 프로젝트에 바로 적용 가능한 기능

### 1. Admin 개선 (가장 쉬움!)

**api/admin.py에 추가:**
```python
from django.contrib import admin
from .models import Portfolio

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['portfolio_id', 'user_id', 'style_type', 'match_score', 'created_at']
    list_filter = ['style_type', 'status', 'created_at']
    search_fields = ['portfolio_id', 'user_id']
    readonly_fields = ['portfolio_id', 'created_at']
    
    # 상세 페이지에서 보기 좋게
    fieldsets = (
        ('기본 정보', {
            'fields': ('portfolio_id', 'user_id', 'style_type')
        }),
        ('제품 정보', {
            'fields': ('products', 'match_score')
        }),
    )
```

**효과:**
- `/admin/`에서 포트폴리오를 쉽게 관리
- 검색, 필터링 자동 제공

---

### 2. 사용자 인증 추가

**간단한 로그인 시스템:**
```python
# api/views.py에 추가
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

**효과:**
- 사용자별 포트폴리오 관리
- 개인화된 추천
- 카카오 로그인 연동 가능

---

### 3. 세션 활용

**온보딩 진행 상황 저장:**
```python
# 온보딩 중간에 나가도 다시 돌아올 수 있음
request.session['onboarding_step'] = 2
request.session['onboarding_data'] = {
    'household_size': 4,
    'has_pet': True
}
```

---

### 4. 캐싱 추가

**추천 결과 캐싱:**
```python
from django.core.cache import cache

def recommend_view(request):
    # 캐시 키 생성
    cache_key = f"recommend_{hash(str(user_profile))}"
    
    # 캐시에서 가져오기
    cached_result = cache.get(cache_key)
    if cached_result:
        return JsonResponse(cached_result)
    
    # 없으면 계산
    result = recommendation_engine.get_recommendations(user_profile)
    
    # 캐시에 저장 (1시간)
    cache.set(cache_key, result, timeout=3600)
    
    return JsonResponse(result)
```

---

## 📊 Django 기능 우선순위

### 필수 기능 (이미 사용 중) ✅
- ORM (데이터베이스 작업)
- 템플릿 시스템
- 정적 파일 관리
- Admin (일부)

### 추천 기능 (추가하면 좋음) ⭐
1. **Admin 커스터마이징** - 가장 쉬움, 즉시 효과
2. **사용자 인증** - 개인화 기능
3. **세션 관리** - 온보딩 진행 상황 저장
4. **폼 처리** - 입력 검증 개선

### 고급 기능 (나중에)
- 캐싱 (성능 향상)
- 시그널 (자동화)
- 미들웨어 (로깅 등)

---

## 🚀 빠른 시작: Admin 개선하기

**가장 쉬운 방법부터 시작!**

```python
# api/admin.py에 Portfolio 추가
@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['portfolio_id', 'user_id', 'style_type', 'created_at']
    list_filter = ['style_type', 'status']
    search_fields = ['portfolio_id', 'user_id']
```

**효과:**
- `/admin/` 접속하면 포트폴리오를 쉽게 관리할 수 있음
- 검색, 필터링 자동 제공

---

## 💡 다음 단계

어떤 기능부터 시작할까요?

1. **Admin 개선** - 가장 쉬움, 즉시 효과
2. **사용자 인증** - 카카오 로그인 연동
3. **세션 관리** - 온보딩 진행 상황 저장
4. **캐싱** - 성능 향상

원하시는 기능을 알려주시면 바로 구현해드리겠습니다!

