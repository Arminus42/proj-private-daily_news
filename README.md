# <데일리 최신 동향 알림 서비스>
뉴스 크롤링을 통해 AI, IT, 경제, 글로벌 이슈 부문의 최신 동향을 받아보는 프로그램입니다.

## 🧬 AI-Powered Daily Tech Briefing

최신 글로벌 AI 트렌드와 IT/경제 뉴스를 매일 아침 자동으로 수집, 요약하여 제공하는 웹 서비스입니다.
GitHub Actions를 활용한 Serverless 아키텍처로 구축되었으며, Gemini 2.5 Flash 모델을 통해 고품질의 한국어 요약을 제공합니다.

## 🚀 Key Features
* **Automated Crawling:** GitHub Actions를 이용해 매일 아침 06:00(KST) 자동 뉴스 수집.
* **Global Tech Trends:** 미국 Google News RSS를 기반으로 최신 AI/LLM 기술 트렌드 파악.
* **AI Summarization:** Google Gemini 2.5 Flash를 활용하여 영문 기사를 한국어로 번역 및 핵심 요약.
* **Interactive UI:** Streamlit 기반의 반응형 UI, 사용자 설정(분야, 개수) 기능 제공.

## 🏗 Architecture
1.  **Crawler:** Python + Feedparser + Google GenAI SDK
2.  **Automation:** GitHub Actions (Cron Job)
3.  **Frontend:** Streamlit Community Cloud
4.  **Data Storage:** JSON (File-based DB within Git repo)

## 🛠 Tech Stack
* **Language:** Python 3.10
* **AI Model:** Gemini 2.5 Flash
* **Libraries:** Streamlit, Feedparser, BeautifulSoup4
* **DevOps:** GitHub Actions