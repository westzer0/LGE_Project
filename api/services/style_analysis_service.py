"""
스타일 분석 서비스
PRD 기반 스타일 타이틀 및 서브타이틀 생성
"""
import json
from typing import Dict, Optional
from .chatgpt_service import chatgpt_service


class StyleAnalysisService:
    """스타일 분석 서비스 - PRD 기반"""
    
    @staticmethod
    def generate_style_analysis(onboarding_data: dict, user_profile: dict) -> dict:
        """
        온보딩 데이터 기반 스타일 분석 결과 생성
        
        Args:
            onboarding_data: 온보딩 세션 데이터
            user_profile: 사용자 프로필
            
        Returns:
            {
                "title": "스타일 타이틀",
                "subtitle": "스타일 설명",
                "style_type": "modern",
                "color_group": ["Essence White", "Matte Black"],
                "line": ["Basic", "Built-in"]
            }
        """
        # 온보딩 데이터에서 정보 추출
        vibe = onboarding_data.get('vibe') or user_profile.get('vibe', 'modern')
        household_size = onboarding_data.get('household_size') or user_profile.get('household_size', 2)
        housing_type = onboarding_data.get('housing_type') or user_profile.get('housing_type', 'apartment')
        pyung = onboarding_data.get('pyung') or user_profile.get('pyung', 25)
        priority = onboarding_data.get('priority') or user_profile.get('priority', 'value')
        budget_level = onboarding_data.get('budget_level') or user_profile.get('budget_level', 'medium')
        has_pet = onboarding_data.get('has_pet') or user_profile.get('has_pet', False)
        cooking = onboarding_data.get('cooking') or user_profile.get('cooking', 'sometimes')
        laundry = onboarding_data.get('laundry') or user_profile.get('laundry', 'weekly')
        media = onboarding_data.get('media') or user_profile.get('media', 'balanced')
        main_space = onboarding_data.get('main_space') or user_profile.get('main_space', 'living')
        
        # priority가 리스트인 경우 첫 번째 값 사용
        if isinstance(priority, list):
            priority = priority[0] if priority else 'value'
        
        # PRD 로직에 따른 스타일 정보 결정
        style_info = StyleAnalysisService._determine_style_info(
            vibe=vibe,
            household_size=household_size,
            housing_type=housing_type,
            pyung=pyung,
            priority=priority,
            budget_level=budget_level,
            has_pet=has_pet,
            cooking=cooking,
            laundry=laundry,
            media=media,
            main_space=main_space
        )
        
        # ChatGPT로 스타일 메시지 생성 (PRD 패턴 반영)
        if chatgpt_service.is_available():
            try:
                style_message = StyleAnalysisService._generate_style_message_with_gpt(
                    vibe=vibe,
                    household_size=household_size,
                    housing_type=housing_type,
                    pyung=pyung,
                    priority=priority,
                    budget_level=budget_level,
                    has_pet=has_pet,
                    cooking=cooking,
                    laundry=laundry,
                    media=media,
                    main_space=main_space,
                    style_info=style_info
                )
                return {
                    **style_info,
                    **style_message
                }
            except Exception as e:
                print(f"[Style Analysis GPT Error] {e}")
        
        # Fallback: 규칙 기반 생성
        return StyleAnalysisService._generate_style_message_fallback(
            vibe=vibe,
            household_size=household_size,
            housing_type=housing_type,
            pyung=pyung,
            priority=priority,
            budget_level=budget_level,
            has_pet=has_pet,
            cooking=cooking,
            laundry=laundry,
            media=media,
            main_space=main_space,
            style_info=style_info
        )
    
    @staticmethod
    def _determine_style_info(
        vibe: str,
        household_size: int,
        housing_type: str,
        pyung: int,
        priority: str,
        budget_level: str,
        has_pet: bool,
        cooking: str,
        laundry: str,
        media: str,
        main_space: str
    ) -> dict:
        """
        PRD 로직에 따른 스타일 정보 결정
        
        Step 1. Vibe Check 로직:
        - 모던 & 미니멀: Color_Group: Essence White, Matte Black | Line: Basic, Built-in
        - 코지 & 네이처: Color_Group: Nature Beige, Clay Brown | Line: Objet Collection
        - 유니크 & 팝: Color_Group: Calming Green, Active Red | Feature: MoodUP
        - 럭셔리 & 아티스틱: Line: LG SIGNATURE | Material: Stainless Steel, Glass
        """
        style_info = {
            "style_type": vibe,
            "color_group": [],
            "line": [],
            "features": [],
            "materials": []
        }
        
        # Vibe 기반 스타일 정보
        if vibe == 'modern':
            style_info["color_group"] = ["Essence White", "Matte Black"]
            style_info["line"] = ["Basic", "Built-in"]
        elif vibe == 'cozy' or vibe == 'natural':
            style_info["color_group"] = ["Nature Beige", "Clay Brown"]
            style_info["line"] = ["Objet Collection"]
        elif vibe == 'pop' or vibe == 'unique':
            style_info["color_group"] = ["Calming Green", "Active Red"]
            style_info["features"] = ["MoodUP"]
        elif vibe == 'luxury':
            style_info["line"] = ["LG SIGNATURE"]
            style_info["materials"] = ["Stainless Steel", "Glass"]
        
        return style_info
    
    @staticmethod
    def _generate_style_message_with_gpt(
        vibe: str,
        household_size: int,
        housing_type: str,
        pyung: int,
        priority: str,
        budget_level: str,
        has_pet: bool,
        cooking: str,
        laundry: str,
        media: str,
        main_space: str,
        style_info: dict
    ) -> dict:
        """ChatGPT로 스타일 메시지 생성 (PRD 패턴 반영)"""
        
        # PRD 예시 패턴 참고
        prompt = f"""
당신은 LG전자 홈스타일링 전문가입니다. 사용자 프로필을 분석하여 PRD에 명시된 패턴에 맞춰 스타일 메시지를 생성해주세요.

## 사용자 정보
- 인테리어 무드: {vibe}
- 가족 구성: {household_size}인
- 주거 형태: {housing_type}
- 평수: {pyung}평
- 우선순위: {priority}
- 예산: {budget_level}
- 반려동물: {'있음' if has_pet else '없음'}
- 요리 빈도: {cooking}
- 세탁 패턴: {laundry}
- 미디어 소비: {media}
- 주요 공간: {main_space}

## 스타일 정보
- 컬러 그룹: {', '.join(style_info.get('color_group', []))}
- 라인: {', '.join(style_info.get('line', []))}
- 기능: {', '.join(style_info.get('features', []))}

## PRD 타이틀 패턴 예시
1. 디자인 취향 기반:
   - "모던 & 미니멀한 당신에게 어울리는 LG 오브제 스타일"
   - "따스한 코지 & 네이처 무드의 공간 스타일"
   - "개성 넘치는 유니크 & 팝 감성 스타일"
   - "럭셔리 & 아티스틱 하우스 스타일 추천 결과"

2. 종합형 (디자인 + 라이프스타일):
   - "미니멀하지만 스마트한 라이프를 위한 스타일"
   - "자연을 닮은 따뜻한 취향의 라이프스타일 패키지"

3. 고객 타입 기반:
   - "1인 라이프에 꼭 맞춘 컴팩트 & 스타일 패키지"
   - "둘만의 신혼 무드를 완성하는 오브제 스타일"
   - "패밀리 라이프를 위한 실속+대용량 프리미엄 스타일"

## 서브타이틀 패턴 예시
- "당신의 공간 분위기와 요리 중심 라이프스타일을 반영해 Essence White 컬러의 오브제컬렉션 냉장고·전기레인지·식기세척기 중심으로 구성했어요."
- "Nature Beige 톤과 패밀리 구성에 최적화된 대용량 냉장고·표준형 세탁기·에너지 효율 1등급 TV 조합이에요."

## 요청사항
JSON 형식으로 응답:
{{
    "title": "스타일 타이틀 (PRD 패턴 중 하나 선택 또는 유사하게 생성)",
    "subtitle": "스타일 설명 (사용자 특성 반영, 100자 이내)"
}}

타이틀은 PRD 패턴을 참고하되, 사용자의 구체적인 조건을 반영해주세요.
서브타이틀은 컬러 그룹, 라인, 주요 공간, 라이프스타일을 구체적으로 언급해주세요.
"""
        
        try:
            response = chatgpt_service.chat_response(prompt, {})
            # JSON 파싱 시도
            import re
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return {
                    "title": result.get("title", "나에게 딱 맞는 스타일"),
                    "subtitle": result.get("subtitle", "당신의 라이프스타일에 맞춰 구성했어요.")
                }
        except Exception as e:
            print(f"[GPT Style Message Parse Error] {e}")
        
        # 파싱 실패 시 fallback
        return StyleAnalysisService._generate_style_message_fallback(
            vibe, household_size, housing_type, pyung, priority, budget_level,
            has_pet, cooking, laundry, media, main_space, style_info
        )
    
    @staticmethod
    def _generate_style_message_fallback(
        vibe: str,
        household_size: int,
        housing_type: str,
        pyung: int,
        priority: str,
        budget_level: str,
        has_pet: bool,
        cooking: str,
        laundry: str,
        media: str,
        main_space: str,
        style_info: dict
    ) -> dict:
        """규칙 기반 스타일 메시지 생성 (PRD 패턴 반영)"""
        
        # Vibe 기반 타이틀
        vibe_titles = {
            'modern': "모던 & 미니멀 라이프를 위한 오브제 스타일",
            'cozy': "따뜻하고 자연스러운 코지 패밀리 스타일",
            'natural': "자연을 닮은 내추럴 라이프스타일",
            'pop': "나만의 컬러 플레이, 유니크 MoodUP 스타일",
            'unique': "개성 넘치는 유니크 & 팝 감성 스타일",
            'luxury': "프리미엄 감성의 럭셔리 & 아티스틱 스타일"
        }
        
        # 고객 타입 기반 타이틀
        if household_size == 1:
            title = "1인 라이프에 꼭 맞춘 컴팩트 & 스타일 패키지"
        elif household_size == 2:
            title = "둘만의 신혼 무드를 완성하는 오브제 스타일"
        elif household_size >= 4:
            title = "패밀리 라이프를 위한 실속+대용량 프리미엄 스타일"
        else:
            title = vibe_titles.get(vibe, "나에게 딱 맞는 스타일")
        
        # 서브타이틀 생성
        subtitle_parts = []
        
        # 컬러 그룹 언급
        color_group = style_info.get('color_group', [])
        if color_group:
            subtitle_parts.append(f"{color_group[0]} 컬러의")
        
        # 라인 언급
        line = style_info.get('line', [])
        if line:
            subtitle_parts.append(f"{line[0]} 중심으로")
        
        # 주요 공간 및 라이프스타일 반영
        if main_space == 'kitchen' and cooking in ['high', 'often']:
            subtitle_parts.append("요리 중심 라이프스타일을 반영해")
            subtitle_parts.append("냉장고·전기레인지·식기세척기 조합을 구성했어요.")
        elif main_space == 'dress_room' or laundry in ['daily', 'few_times']:
            subtitle_parts.append("세탁 패턴에 맞춘")
            subtitle_parts.append("세탁기·건조기 중심 구성이에요.")
        elif household_size >= 4:
            subtitle_parts.append("패밀리 구성에 최적화된")
            subtitle_parts.append("대용량 냉장고·세탁기·TV 조합이에요.")
        else:
            subtitle_parts.append("균형 잡힌 표준형 예산 안에서")
            subtitle_parts.append("디자인 완성도와 기능성을 모두 담은 베스트 패키지입니다.")
        
        subtitle = " ".join(subtitle_parts)
        
        return {
            "title": title,
            "subtitle": subtitle
        }


# Singleton 인스턴스
style_analysis_service = StyleAnalysisService()

