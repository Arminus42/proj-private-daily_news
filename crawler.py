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
    # [변경됨] AI Tech: 미국(US) 구글 뉴스에서 영어 원문 수집
    'AI_Tech': 'https://news.google.com/rss/search?q=AI+Tech+OR+LLM+OR+Generative+AI+OR+Deep+Learning+when:2d&hl=en-US&gl=US&ceid=US:en',
    
    # 나머지는 기존 한국 뉴스 유지
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

    # 프롬프트 설정
    if category == 'AI_Tech':
        # [중요] 영문 기사를 한국어로 번역 요약 요청
        focus_instruction = """
        ★중요★: 이 분야는 'Global AI Tech Trend'야. 기사는 영어로 되어 있어.
        1. **반드시 한국어로 번역해서 출력해.**
        2. 기업 주가나 매출 같은 비즈니스 뉴스보다는, **새로운 모델, 알고리즘, 연구 논문, 오픈소스 공개** 같은 기술적 뉴스를 최우선으로 뽑아.
        3. 제목도 한국어로 자연스럽게 번역하되, 원문의 의미를 정확히 반영해줘.
        4. points(요약)에는 해당 기술의 혁신적인 점이나 원리를 설명해줘.
        5. 전공자가 아닌 일반인도 이해할 수 있게 쉽게 작성해줘.
        6. 전공자만 이해할 수 있는 어려운 용어는 피하고, 꼭 필요한 경우에는 간단한 설명을 덧붙여줘.
        """
    else:
        focus_instruction = "이 분야의 가장 파급력 있고 중요한 뉴스를 선정해줘. 언어는 한국어야."

    prompt = f"""
    아래는 '{category}' 분야의 뉴스 기사 목록이야.
    이 중에서 가장 중요한 뉴스 {TOP_K}개를 선정해줘.

    [지시사항]
    {focus_instruction}
    
    [기사 목록]
    {candidates_text}

    [출력 포맷 (JSON Only)]
    [
        {{
            "title": "기사 제목 (한국어)",
            "points": ["핵심 내용 1 (한국어)", "핵심 내용 2 (한국어)"],
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