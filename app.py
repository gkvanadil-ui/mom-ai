import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import io
import openai  # API 연동을 위해 추가

# 1. 앱 설정
st.set_page_config(page_title="엄마의 AI 명품 비서", layout="wide")

# 사이드바에서 API 키 입력 받기
st.sidebar.header("⚙️ AI 설정")
api_key = st.sidebar.text_input("OpenAI API Key를 넣어주세요", type="password")

st.title("🕯️ 엄마작가님 전용 AI 명품 비서")
st.write("사진 보정부터 AI 작가의 상세페이지 대행까지 한 번에!")

st.divider()

# --- 1. 사진 일괄 보정 (기능 유지) ---
st.header("📸 1. 사진 한 번에 보정하기")
uploaded_files = st.file_uploader("사진들을 선택하세요", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    st.subheader("🎨 보정 강도")
    c1, c2, c3 = st.columns(3)
    with c1: bright = st.select_slider("☀️ 화사함", options=["기본", "밝게", "매우 밝게"], value="밝게")
    with c2: sharp = st.select_slider("🔍 선명함", options=["자연스럽게", "선명하게", "또렷하게"], value="선명하게")
    with c3: smooth = st.select_slider("✨ 잡티 제거", options=["없음", "약하게", "강하게"], value="약하게")

    if st.button("🚀 모든 사진 일괄 보정하기"):
        b_val = {"기본": 1.0, "밝게": 1.2, "매우 밝게": 1.4}[bright]
        s_val = {"자연스럽게": 1.0, "선명하게": 1.5, "또렷하게": 2.0}[sharp]
        m_val = {"없음": 0, "약하게": 1, "강하게": 2}[smooth]
        
        cols = st.columns(len(uploaded_files))
        for idx, file in enumerate(uploaded_files):
            img = Image.open(file)
            edited = ImageEnhance.Brightness(img).enhance(b_val)
            for _ in range(m_val): edited = edited.filter(ImageFilter.SMOOTH_MORE)
            edited = ImageEnhance.Sharpness(edited).enhance(s_val)
            with cols[idx]:
                st.image(edited, use_container_width=True)
                buf = io.BytesIO()
                edited.save(buf, format="JPEG", quality=95)
                st.download_button(f"📥 저장 {idx+1}", buf.getvalue(), f"photo_{idx+1}.jpg")

st.divider()

# --- 2. 진짜 AI(ChatGPT) 상세페이지 생성 ---
st.header("✍️ 2. AI 작가의 상세페이지 작성")
st.write("키워드만 넣으면 AI가 맞춤법에 맞춰 감성적인 글을 써드립니다.")

if not api_key:
    st.info("💡 왼쪽 사이드바에 OpenAI API Key를 입력하면 AI 글쓰기를 시작할 수 있어요!")
else:
    with st.container():
        p_name = st.text_input("📦 작품 이름", placeholder="예: 한정판 빈티지 퀼트 백")
        p_keys = st.text_area("🔑 핵심 키워드 및 특징", placeholder="예: 부드러운 안감, 넉넉한 수납, 30년 경력의 손바느질, 선물용 추천")
        p_tone = st.select_slider("💬 원하는 말투", options=["매우 친절하게", "담백하고 깔끔하게", "감성적이고 따뜻하게"])

    if st.button("🪄 AI에게 글쓰기 부탁하기"):
        client = openai.OpenAI(api_key=api_key)
        
        # AI에게 줄 명령문(프롬프트)
        prompt = f"""
        당신은 핸드메이드 작가를 돕는 전문 카피라이터입니다.
        아래 정보를 바탕으로 네이버 스마트스토어에 올릴 상세페이지 판매글을 작성해주세요.
        
        - 작품 이름: {p_name}
        - 핵심 키워드: {p_keys}
        - 말투: {p_tone}
        
        조건:
        1. 문장을 매우 자연스럽고 감성적으로 작성할 것.
        2. 맞춤법을 완벽하게 지킬 것.
        3. [작품 소개], [상세 정보], [작가 한마디] 구분을 넣을 것.
        4. 이모지를 적절히 사용하여 따뜻한 느낌을 줄 것.
        """
        
        with st.spinner("AI 작가가 정성껏 글을 쓰는 중입니다..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_text = response.choices[0].message.content
                st.success("AI 작가가 글을 완성했어요!")
                st.text_area("결과 (복사해서 사용하세요)", value=ai_text, height=500)
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
