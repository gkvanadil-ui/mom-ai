import streamlit as st
import pandas as pd
from PIL import Image, ImageEnhance, ImageOps
import io
import openai
import base64
import json

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="centered")

# --- CSS: 시인성 및 버튼 크기 최적화 ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { color: inherit; }
    h1, h2, h3 { color: #D4A373 !important; font-weight: bold !important; margin-bottom: 12px; }
    
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.8em;
        background-color: #7d6e63; color: white !important;
        font-weight: bold; font-size: 18px !important;
        border: none; margin-bottom: 8px;
    }
    
    .stTextArea textarea {
        font-size: 17px !important;
        line-height: 1.6 !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: inherit !important;
        border: 1px solid #7d6e63 !important;
    }
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 55px; border-radius: 10px 10px 0 0;
        padding: 5px 20px; font-weight: bold; font-size: 16px !important;
    }
    
    hr { border-top: 1px solid #7d6e63; opacity: 0.3; }
    </style>
    """, unsafe_allow_html=True)

# --- API 키 설정 ---
api_key = st.secrets.get("OPENAI_API_KEY")

st.title("🕯️ 모그(Mog) 작가 전용 비서")
st.write("<p style='text-align: center;'>작가님의 따뜻한 진심을 플랫폼에 맞게 전해드려요🌸</p>", unsafe_allow_html=True)

# --- [1단계: 정보 입력] ---
st.header("1️⃣ 작품 정보 입력")
with st.expander("📝 이곳을 눌러 내용을 작성해주세요", expanded=True):
    name = st.text_input("📦 작품 이름", placeholder="예: 빈티지 튤립 뜨개 파우치")
    c1, c2 = st.columns(2)
    with c1:
        mat = st.text_input("🧵 소재", placeholder="코튼 100%")
        size = st.text_input("📏 크기", placeholder="20*15cm")
    with c2:
        period = st.text_input("⏳ 제작 기간", placeholder="주문 후 3일")
        care = st.text_input("💡 세탁 방법", placeholder="미온수 손세탁 권장")
    keys = st.text_area("🔑 작품 특징", placeholder="색감이 화사해서 포인트 아이템으로 좋아요.")
    process = st.text_area("🛠️ 제작 포인트", placeholder="안감까지 꼼꼼히 제작했습니다.")

st.divider()

# --- AI 처리 함수 ---
def process_ai_text(full_prompt):
    if not api_key: return None
    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": full_prompt}])
        return response.choices[0].message.content.replace("**", "").strip()
    except: return "오류가 발생했습니다. 다시 시도해 주세요."

# --- [2단계: 작업 선택] ---
st.header("2️⃣ 작업실 선택")
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 사진보정", "💡 캔바 & 에픽"])

# --- Tab 1: 판매글 쓰기 (수정 요청 기능 복구) ---
with tabs[0]:
    st.subheader("✍️ 플랫폼별 맞춤 글쓰기")
    
    if 'texts' not in st.session_state:
        st.session_state.texts = {"인스타그램": "", "아이디어스": "", "네이버 스마트스토어": ""}

    btn_col1, btn_col2, btn_col3 = st.columns(3)
    platform = None
    
    if btn_col1.button("📸 인스타그램"): platform = "인스타그램"
    if btn_col2.button("🎨 아이디어스"): platform = "아이디어스"
    if btn_col3.button("🛍️ 네이버 스마트스토어"): platform = "네이버 스마트스토어"

    if platform:
        with st.spinner(f"[{platform}]용 글을 작성 중입니다..."):
            guide_text = ""
            if platform == "인스타그램": guide_text = "해시태그 포함, 감성적인 인사말."
            elif platform == "아이디어스": guide_text = "줄바꿈 자주, 꽃/하트 이모지 풍성하게."
            else: guide_text = "구분선 활용, 정보 위주 정리."

            prompt = f"""당신은 핸드메이드 작가 '모그'입니다. 말투: 다정한 엄마 말투 (~이지요^^, ~해요, ~좋아요). 별표(*) 절대 금지. 
            내용: {platform} 판매글 ({guide_text}) 
            정보: 이름:{name}, 특징:{keys}, 소재:{mat}, 사이즈:{size}, 제작:{process}, 관리:{care}, 기간:{period}"""
            st.session_state.texts[platform] = process_ai_text(prompt)
    
    for p_key in ["인스타그램", "아이디어스", "네이버 스마트스토어"]:
        if st.session_state.texts[p_key]:
            st.write(f"---")
            st.write(f"**✅ {p_key} 결과**")
            current_txt = st.text_area(f"{p_key} (복사용)", value=st.session_state.texts[p_key], height=300, key=f"txt_{p_key}")
            
            # [수정 요청 칸 복구]
            with st.expander(f"✨ {p_key} 글 수정 요청하기"):
                feedback = st.text_input("고치고 싶은 내용을 적어주세요", placeholder="예: 조금 더 다정하게 써줘 / 내용을 더 늘려줘", key=f"f_{p_key}")
                if st.button("♻️ 다시 쓰기", key=f"b_{p_key}"):
                    refine_prompt = f"기존글: {current_txt}\n요청사항: {feedback}\n작가님 말투(~이지요^^)를 유지하며 다시 작성해줘."
                    st.session_state.texts[p_key] = process_ai_text(refine_prompt)
                    st.rerun()

# --- Tab 2: 사진보정 ---
with tabs[1]:
    st.subheader("📸 AI 자율 분석 보정")
    uploaded_files = st.file_uploader("사진 선택", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if uploaded_files and api_key and st.button("🚀 AI 자동 보정 시작"):
        client = openai.OpenAI(api_key=api_key)
        for idx, file in enumerate(uploaded_files):
            img_bytes = file.getvalue()
            try:
                b64_img = base64.b64encode(img_bytes).decode('utf-8')
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": '이 사진을 분석해 {"b":밝기, "c":대비, "s":채도, "sh":선명도} JSON으로만 답하세요.'},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                    ]}],
                    response_format={ "type": "json_object" }
                )
                res = json.loads(response.choices[0].message.content)
                img = Image.open(io.BytesIO(img_bytes))
                img = ImageOps.exif_transpose(img)
                img = ImageEnhance.Brightness(img).enhance(res.get('b', 1.1))
                img = ImageEnhance.Contrast(img).enhance(res.get('c', 1.0))
                img = ImageEnhance.Color(img).enhance(res.get('s', 1.0))
                img = ImageEnhance.Sharpness(img).enhance(res.get('sh', 1.2))
                st.image(img, caption=f"보정 완료 {idx+1}")
                buf = io.BytesIO(); img.save(buf, format="JPEG")
                st.download_button(f"📥 {idx+1}번 사진 저장", buf.getvalue(), f"mog_{idx+1}.jpg")
            except: st.error("보정 실패")

# --- Tab 3: 캔바 & 에픽 ---
with tabs[2]:
    st.subheader("🎨 상세페이지 & 영상 꿀팁")
    st.link_button("✨ 캔바(Canva) 앱 열기", "https://www.canva.com/templates/?query=상세페이지")
    if st.button("🪄 상세페이지 기획안 만들기"):
        if not name: st.warning("정보를 먼저 입력해 주셔요🌸")
        else:
            with st.spinner("기획안 작성 중..."):
                prompt = f"모그 작가 말투로 {name} 상세페이지 5장 기획안 작성."
                st.write(process_ai_text(prompt))
    st.divider()
    with st.expander("🎥 에픽(EPIK) 영상 가이드"):
        st.info("에픽 앱 실행 -> [템플릿] -> '감성' 검색 -> 사진 선택 -> 저장! 🌸")
