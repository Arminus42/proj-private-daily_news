import streamlit as st
import json
import os

# 페이지 설정
st.set_page_config(
    page_title="Deep Tech Briefing",
    page_icon="🧬",
    layout="centered" # 모바일 가독성을 위해 centered 추천
)

# 커스텀 CSS (제목 폰트 사이즈 조절 및 여백 최적화)
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; }
    h1 { font-size: 1.8rem !important; }
    </style>
""", unsafe_allow_html=True)

def load_data():
    data_path = 'data/news_data.json'
    if not os.path.exists(data_path): return None
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    st.title("🧬 Deep Tech & Trends")
    
    # --- [상단 설정 메뉴] ---
    # 사이드바 대신 Expander를 사용하여 '우상단 메뉴' 느낌을 냄
    with st.expander("⚙️ 앱 설정 (클릭하여 열기)"):
        st.caption("보고 싶은 분야와 뉴스 개수를 설정하세요.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**표시할 분야**")
            show_ai = st.checkbox("🧬 AI / 신기술", value=True)
            show_it = st.checkbox("🏢 IT / 기업", value=True)
        with col2:
            st.write("") # 줄맞춤용
            show_eco = st.checkbox("💰 경제 / 시장", value=True)
            show_world = st.checkbox("🌍 세계 / 이슈", value=True)
            
        st.markdown("---")
        news_count = st.slider("분야별 뉴스 개수", 1, 5, 3)

    # --- [메인 뉴스 화면] ---
    data = load_data()
    if not data:
        st.info("데이터 수집 중입니다. 잠시 후 다시 접속해주세요.")
        return

    # 탭 구성 (AI 기술을 가장 먼저 보여줌)
    tabs_mapping = {}
    if show_ai: tabs_mapping["🧬 AI Tech"] = "AI_Tech"
    if show_it: tabs_mapping["🏢 IT Biz"] = "IT_Biz"
    if show_eco: tabs_mapping["💰 Economy"] = "Economy"
    if show_world: tabs_mapping["🌍 World"] = "World"

    if not tabs_mapping:
        st.warning("설정 메뉴에서 최소 하나의 분야를 선택해주세요.")
        return

    # 탭 생성
    tabs = st.tabs(list(tabs_mapping.keys()))

    for i, (tab_name, data_key) in enumerate(tabs_mapping.items()):
        with tabs[i]:
            if data_key in data and data[data_key]:
                # 최신 업데이트 시간 표시
                pub_date = data[data_key][0].get('published', '')[:10]
                st.caption(f"Update: {pub_date}")
                
                # 뉴스 카드 출력
                news_items = data[data_key][:news_count]
                for idx, item in enumerate(news_items):
                    with st.container():
                        st.markdown(f"### {idx+1}. {item['title']}")
                        
                        # AI 기술 분야면 강조 박스 사용
                        if data_key == "AI_Tech":
                            st.info("💡 **Key Tech:** " + " ".join(item['points']))
                        else:
                            for point in item['points']:
                                st.markdown(f"- {point}")
                        
                        st.markdown(f"[🔗 원문 보기]({item['link']})")
                        st.divider()
            else:
                st.write("최신 뉴스가 없습니다.")

if __name__ == "__main__":
    main()