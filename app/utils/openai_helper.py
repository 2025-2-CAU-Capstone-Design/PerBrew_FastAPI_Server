"""
OpenAI Assistant 관련 헬퍼 함수들
기존 assistant_func.py와 recipe_profile.py를 FastAPI 환경에 맞게 이식
엄격한 검증 규칙 적용
"""
import os
import json
import requests
from openai import OpenAI
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# OpenAI 클라이언트 초기화
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Validation Constants (from recipe_profile.py)
AGITATION_TYPES = ['center', 'spiral_out', 'pulse', 'center pour', 'spiral outward', 
                   'outer edge spiral', 'zig-zag', 'swirling']
BEAN_QUANTITY_G = list(range(1, 51))  # 1g ~ 50g
GRIND_LEVEL = list(range(1, 241))  # 1 ~ 240
GRIND_SIZE_M = list(range(100, 1500))  # 100 ~ 1499 microns
WATER_TEMPERATURE_C = list(range(50, 101))  # 50°C ~ 100°C
BREW_RATIO = list(range(10, 31))  # 1:10 ~ 1:30
BREW_TIME_S = list(range(30, 601))  # 30초 ~ 10분
WATER_G = list(range(10, 501))  # 10g ~ 500g per step
POUR_TIME_S = list(range(5, 181))  # 5초 ~ 3분
BLOOM_TIME_S = list(range(0, 181))  # 0초 ~ 3분

SYSTEM = """
Assume the role of a master coffee brewer. 
You focus exclusively on the pour over method and specialty coffee only. 
You often work with single origin coffees, but you also experiment with blends. 
Your recipes are executed by a robot, not a human, so maximum precision can be achieved. 
Temperatures are all maintained and stable in all steps. 
Always lead with the recipe, and only include explanations below that text, NOT inline. 

Below are the important components of the recipe:
- bean quantity: The amount of coffee beans used, measured in grams (g).
- Grind Level: The grind setting number or level on a specific grinder (e.g., 2.5 on a Comandante grinder)
- Grind Size: The actual particle size of the ground coffee, measured in microns (μm).
- Brew Ratio: How much coffee per water (coffee:water). Values must be between 10 and 30 (1:15 means 15 grams water per 1g coffee).
- Brew Time: Total time that coffee is in contact with water.
- Water Temperature: Determine the dissolution rate and extraction efficiency.
- Rinsing: Remove the paper filter's taste for improving the coffee's purity.
- Number of Pourings: Divide the total water volume into several pours.
- Water Per Pouring: The amount of water used for each individual pour.
- Time of Pourings: The duration of each individual water pouring.
- Blooming Time: The time allowed for blooming to occur after pouring water.
- Agitation: Determine the fluidity between coffee powders through the flow of water.
"""

REFORMAT_SYSTEM = """
You are a coffee recipe data engineer. Parse and structure coffee recipes with STRICT VALIDATION.

CRITICAL VALIDATION RULES:
1. Total water from all pouring_steps MUST equal dose_g × brew_ratio
2. Total time from all pouring_steps (pour_time_s + bloom_time_s) MUST equal total_brew_time_s
3. Step numbers must be consecutive starting from 1
4. All pouring steps must have valid agitation types: 'center', 'spiral_out', 'pulse'

Required structure:
{
  "recipe_name": "string (max 50 chars)",
  "dose_g": "float (1-50g)",
  "water_temperature_c": "float (50-100°C)",
  "total_water_g": "float (must equal dose_g × brew_ratio)",
  "total_brew_time_s": "float (30-600 seconds)",
  "brew_ratio": "float (10-30, represents 1:X ratio)",
  "grind_level": "integer (1-240)",
  "grind_microns": "integer (100-1499 microns)",
  "rinsing": "boolean",
  "pouring_steps": [
    {
      "step_number": "integer (consecutive from 1)",
      "water_g": "float (10-500g per step)",
      "pour_time_s": "float (5-180s)",
      "bloom_time_s": "float (0-180s, optional)",
      "technique": "string ('center', 'spiral_out', or 'pulse')"
    }
  ]
}

ENSURE ALL MATHEMATICAL RELATIONSHIPS ARE CORRECT BEFORE RESPONDING.
If you cannot extract accurate values, return null for optional fields but ensure required fields have sensible defaults.
"""


def scrape_website(url: str) -> str:
    """웹 페이지를 가져오고 HTML을 반환합니다."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error fetching '{url}': {str(e)}"


def generate_recipe_from_description(coffee_description: str) -> str:
    """설명을 바탕으로 새로운 레시피(텍스트)를 생성합니다."""
    if not client:
        raise ValueError("OpenAI API key not configured")
    
    try:
        guidance = "Suggest a pour-over coffee recipe for the following. Provide your explanations below the recipe.\n"
        full_prompt = guidance + coffee_description
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": full_prompt}
            ]
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Failed to generate recipe: {e}")


def extract_recipe_from_html(html_content: str) -> Optional[Dict[str, Any]]:
    """HTML에서 레시피 정보를 추출하고 검증합니다."""
    if not client:
        raise ValueError("OpenAI API key not configured")
    
    try:
        # HTML에서 텍스트 추출
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text(separator='\n', strip=True)
        
        # OpenAI로 구조화
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": REFORMAT_SYSTEM},
                {"role": "user", "content": f"Extract coffee recipe from this text and return as JSON:\n\n{text_content[:4000]}"}
            ],
            response_format={"type": "json_object"}
        )
        
        recipe_data = json.loads(completion.choices[0].message.content)
        
        # 검증 수행
        is_valid, errors = validate_recipe_data(recipe_data)
        
        if not is_valid:
            print(f"Recipe validation warnings: {errors}")
            # 자동 수정 시도
            recipe_data = fix_recipe_data(recipe_data)
            print(f"Applied automatic fixes to recipe data")
        
        return recipe_data
        
    except Exception as e:
        raise Exception(f"Failed to extract recipe from HTML: {e}")


def extract_recipe_from_description(recipe_text: str) -> Optional[Dict[str, Any]]:
    """텍스트 설명에서 구조화된 레시피를 추출합니다."""
    if not client:
        raise ValueError("OpenAI API key not configured")
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": REFORMAT_SYSTEM},
                {"role": "user", "content": f"Extract recipe from this text and return as JSON:\n\n{recipe_text}"}
            ],
            response_format={"type": "json_object"}
        )
        
        recipe_data = json.loads(completion.choices[0].message.content)
        return recipe_data
        
    except Exception as e:
        raise Exception(f"Failed to extract recipe from description: {e}")


def validate_recipe_data(recipe_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    레시피 데이터의 일관성을 검증합니다.
    Returns: (is_valid, error_messages)
    """
    errors = []
    
    try:
        # 1. 필수 필드 확인
        required_fields = ['dose_g', 'brew_ratio', 'total_water_g', 'total_brew_time_s', 'pouring_steps']
        for field in required_fields:
            if field not in recipe_data or recipe_data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return False, errors
        
        dose_g = float(recipe_data['dose_g'])
        brew_ratio = float(recipe_data['brew_ratio'])
        total_water_g = float(recipe_data['total_water_g'])
        total_brew_time_s = float(recipe_data['total_brew_time_s'])
        pouring_steps = recipe_data['pouring_steps']
        
        # 2. 범위 검증
        if dose_g < 1 or dose_g > 50:
            errors.append(f"dose_g must be between 1-50g, got {dose_g}")
        
        if brew_ratio < 10 or brew_ratio > 30:
            errors.append(f"brew_ratio must be between 10-30, got {brew_ratio}")
        
        if total_brew_time_s < 30 or total_brew_time_s > 600:
            errors.append(f"total_brew_time_s must be between 30-600s, got {total_brew_time_s}")
        
        # 3. 물의 양 일관성 체크
        total_water_from_steps = sum(float(step.get('water_g', 0)) for step in pouring_steps)
        expected_water = dose_g * brew_ratio
        
        # 5% 오차 허용
        if abs(total_water_from_steps - expected_water) > expected_water * 0.05:
            errors.append(
                f"Water quantity mismatch: sum of pouring steps = {total_water_from_steps}g, "
                f"but dose_g({dose_g}) × brew_ratio({brew_ratio}) = {expected_water}g"
            )
        
        if abs(total_water_g - expected_water) > expected_water * 0.05:
            errors.append(
                f"total_water_g ({total_water_g}g) doesn't match expected {expected_water}g"
            )
        
        # 4. 시간 일관성 체크
        total_time_from_steps = sum(
            float(step.get('pour_time_s', 0)) + float(step.get('bloom_time_s', 0)) 
            for step in pouring_steps
        )
        
        # 10% 오차 허용
        if abs(total_time_from_steps - total_brew_time_s) > total_brew_time_s * 0.1:
            errors.append(
                f"Brew time mismatch: sum of pouring times = {total_time_from_steps}s, "
                f"but total_brew_time_s = {total_brew_time_s}s"
            )
        
        # 5. 포링 단계 번호 연속성 확인
        step_numbers = [step.get('step_number', 0) for step in pouring_steps]
        expected_steps = list(range(1, len(step_numbers) + 1))
        if step_numbers != expected_steps:
            errors.append(f"Pouring step numbers must be consecutive starting from 1. Got: {step_numbers}")
        
        # 6. 포링 단계 수 확인
        num_steps = len(pouring_steps)
        if num_steps < 1 or num_steps > 5:
            errors.append(f"Number of pouring steps must be between 1 and 5. Got: {num_steps}")
        
        # 7. Agitation 타입 검증
        for i, step in enumerate(pouring_steps):
            technique = step.get('technique', '')
            if technique and technique not in AGITATION_TYPES:
                errors.append(
                    f"Step {i+1}: Invalid technique '{technique}'. Must be one of {AGITATION_TYPES}"
                )
        
        return len(errors) == 0, errors
        
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
        return False, errors


def fix_recipe_data(recipe_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    레시피 데이터를 자동으로 수정하여 일관성을 맞춥니다.
    """
    try:
        dose_g = float(recipe_data.get('dose_g', 15.0))
        brew_ratio = float(recipe_data.get('brew_ratio', 15.0))
        
        # total_water_g 자동 계산
        expected_water = dose_g * brew_ratio
        recipe_data['total_water_g'] = expected_water
        
        # pouring_steps가 있으면 물의 양 재분배
        if 'pouring_steps' in recipe_data and recipe_data['pouring_steps']:
            steps = recipe_data['pouring_steps']
            num_steps = len(steps)
            
            # 각 단계에 물을 균등 분배
            water_per_step = expected_water / num_steps
            
            for i, step in enumerate(steps):
                step['step_number'] = i + 1
                # 마지막 단계는 남은 물 모두 할당 (반올림 오차 보정)
                if i == num_steps - 1:
                    step['water_g'] = expected_water - (water_per_step * (num_steps - 1))
                else:
                    step['water_g'] = round(water_per_step, 1)
            
            # total_brew_time_s 자동 계산
            total_time = sum(
                float(step.get('pour_time_s', 0)) + float(step.get('bloom_time_s', 0))
                for step in steps
            )
            recipe_data['total_brew_time_s'] = total_time
        
        return recipe_data
        
    except Exception as e:
        # 수정 실패 시 원본 반환
        return recipe_data
