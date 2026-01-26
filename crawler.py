import feedparser
import json
import os
import time
import re
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# --- [설정] ---
SEARCH_COUNT = 15
TOP_K = 5
# ----------------

API_KEY = os.getenv("GEMINI_API_KEY")
client = None
if API_KEY:
    client = genai.Client(api_key=API_KEY)

# RSS 피드 설정
RSS_FEEDS = {
    # 한국 내 AI 기술, 연구, 생성형 AI 관련 메이저 뉴스 수집
    'AI_Tech': 'https://news.google.com/rss/search?q=AI+기술+OR+인공지능+연구+OR+LLM+OR+생성형AI+when:1d&hl=ko&gl=KR&ceid=KR:ko',
    
    'IT_Biz': 'https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ko&gl=KR&ceid=KR:ko',
    'Economy': 'https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko',
    'World': 'https://news.google.com/rss/headlines/section/topic/WORLD?hl=ko&gl=KR&ceid=KR:ko'
}

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DATA_FILE = os.path.join(DATA_DIR, 'news_data.json')

def clean_json_text(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(json)?", "", text)
        text = re.sub(r"```$", "", text)
    return text.strip()

def process_category(category, url):
    print(f"[{category}] RSS 수집 중... ({'Global/Eng' if category == 'AI_Tech' else 'Local/Kor'})")
    feed = feedparser.parse(url)
    
    candidates = []
    limit = SEARCH_COUNT + 5 if category == 'AI_Tech' else SEARCH_COUNT
    
    for i, entry in enumerate(feed.entries[:limit]):
        # 영문 기사일 경우 제목 옆에 (Eng) 표시를 하거나 그대로 둠 (여기선 그대로)
        candidates.append(f"ID: {i}\n제목: {entry.title}\n링크: {entry.link}\n")
    
    candidates_text = "\n".join(candidates)

    if not client: return None

    # 프롬프트 설정 (수정본)
    if category == 'AI_Tech':
        focus_instruction = """
        ★중요★: 이 분야는 'Global AI Tech Trend'야.
        1. **메이저 뉴스 선별**: 조회수나 화제성이 낮은 사소한 뉴스는 무시해. Google, OpenAI, Meta, NVIDIA, Anthropic 등 주요 글로벌 대기업이나, Naver, SKT 등 국내 AI 빅테크 기업이나, 유명 대학 연구소의 발표를 우선해.
        2. **기술 중심**: 단순 주가 변동이나 가십보다는 새로운 모델 출시, 논문, 획기적인 기술적 돌파구를 선정해.
        3. **언어**: 영어 기사가 있다면, 반드시 한국어로 자연스럽게 번역해서 출력해.
        4. **전달력**: 기술 용어는 쉬운 비유를 섞어 설명하되, '왜 이 뉴스가 중요한지' 가치를 꼭 포함해줘.
        """
    else:
        focus_instruction = """
        ★중요★: 국내외 주요 미디어에서 공통적으로 다루는 '비중 있는 뉴스'만 선정해.
        1. **사소한 소식 배제**: 개인의 블로그성 기사, 특정 업체의 단순 이벤트, 광고성 기사는 절대 제외해.
        2. **영향력 기준**: 해당 산업(IT/경제/세계)의 판도를 바꿀 만한 정책 변화, 대규모 투자, 혁신적인 서비스 출시 위주로 뽑아.
        3. **중복 제거**: 비슷한 내용의 기사가 여러 개라면 가장 정보량이 많은 하나만 선택해.
        """

    prompt = f"""
    아래는 '{category}' 분야의 뉴스 기사 목록이야.
    이 중에서 **가장 파급력이 크고 신뢰도 높은** 뉴스 {TOP_K}개를 엄선해줘.

    [지시사항]
    {focus_instruction}
    
    [기사 목록]
    {candidates_text}

    [출력 포맷 (JSON Only)]
    [
        {{
            "title": "기사 제목 (한국어)",
            "points": [
                "이 뉴스가 왜 메이저한 소식인지 설명 (한국어)",
                "핵심 기술적/경제적 변화 포인트 (한국어)"
            ],
            "link": "원문 링크(변경금지)"
        }}
    ]
    """

    print(f"[{category}] Gemini 2.5에게 요약 요청 중...")
    try:
        # [변경됨] 모델 버전 gemini-2.5-flash 적용
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        
        cleaned_text = clean_json_text(response.text)
        news_items = json.loads(cleaned_text)
        
        for item in news_items:
            item['category'] = category
            item['published'] = datetime.now().isoformat()
            
        return news_items

    except Exception as e:
        # 429 에러 등 발생 시 처리
        if "429" in str(e):
             print(f"[{category}] ⚠️ Quota Exceeded (429). Skipping this category temporarily.")
        else:
             print(f"[{category}] Error: {e}")
        return []

def save_to_json(new_data_dict):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data_dict, f, ensure_ascii=False, indent=4)
    print(f"✅ 데이터 저장 완료")

if __name__ == "__main__":
    result_data = {}
    for category, url in RSS_FEEDS.items():
        items = process_category(category, url)
        if items:
            result_data[category] = items
        
        # 무료 티어 안정성을 위해 대기 시간 부여
        if items: 
            time.sleep(5) 
    
    if result_data:
        save_to_json(result_data)