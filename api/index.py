import streamlit as st
import openai
from PIL import Image
import io
import base64

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- ✨ UI 스타일 가이드 (가독성 및 심미성 강화) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FCF9F6; font-family: 'Noto Sans KR', sans-serif; }
    label p { font-size: 24px !important; font-weight: bold !important; color: #5D4037 !important; }
    h1 { color: #8D6E63 !important; text-align: center; margin-bottom: 30px; font-weight: 800; }
    .stTextInput input, .stTextArea textarea { font-size: 22px !important; border-radius: 15px !important; padding: 20px !important; }
    .stButton>button { width: 100%; border-radius: 20px; height: 4.5em; background-color: #8D6E63 !important; color: white !important; font-weight: bold; font-size: 22px !important; }
    .result-card { background-color: #FFFFFF; padding: 30px; border-radius: 25px; border-left: 10px solid #D7CCC8; box-shadow: 0 10px 20px rgba(0,0,0,0.05); margin-bottom: 20px; line-height: 1.6; }
    .stTabs [data-baseweb="tab-list"] button { font-size: 26px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 필수 설정
api_key = st.secrets.get("OPENAI_API_KEY")

# 세션 상태 초기화
for key in ['texts', 'chat_log', 'm_name', 'm_mat', 'm_per', 'm_size', 'm_det', 'img_analysis']:
    if key not in st.session_state:
        if key == 'texts': st.session_state[key] = {"인스타": "", "아이디어스": "", "스토어": ""}
        elif key == 'chat_log': st.session_state[key] = []
        elif key == 'img_analysis': st.session_state[key] = ""
        else: st.session_state[key] = ""

# --- [로직 1: 사진 특징 분석] ---
def analyze_image(img_file):
    client = openai.OpenAI(api_key=api_key)
    base64_image = base64.b64encode(img_file.getvalue()).decode('utf-8')
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": [{"type": "text", "text": "핸드메이드 작가 모그의 작품이야. 색감과 디테일을 다정하게 묘사해줘."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}]
    )
    return response.choices[0].message.content

# --- [로직 2: 글쓰기 엔진] ---
def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    base_style = """[절대 규칙: 1인칭 작가 시점] 당신은 작가 '모그(Mog)' 본인입니다. 말투: ~이지요^^, ~해요 등 다정한 50대 여성 작가 어투. 특수기호(*, **) 절대 금지."""
    
    if platform == "인스타그램":
        system_p = f"{base_style} [📸 인스타그램] 감성 일기 형식."
    elif platform == "아이디어스":
        system_p = f"{base_style} [🎨 아이디어스] 💡상세설명, 🍀Add info., 🔉안내, 👍🏻작가보증 포맷 엄수. 아주 길게 작성."
    elif platform == "스마트스토어":
        system_p = f"{base_style} [🛍️ 스토어] 💐상품명, 🌸디자인, 👜기능성, 📏사이즈, 📦소재, 🧼관리, 📍추천 포맷 엄수."
    else:
        system_p = f"{base_style} [💬 상담소] 선배 작가의 조언."

    info = f"작품:{st.session_state.m_name}, 소재:{st.session_state.m_mat}, 사이즈:{st.session_state.m_size}, 정성:{st.session_state.m_det}"
    if st.session_state.img_analysis: info += f"\n[사진 특징]: {st.session_state.img_analysis}"
    
    content = f"수정 요청: {feedback}\n기존 글: {user_in}" if feedback else f"정보: {info} / {user_in}"
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":system_p},{"role":"user","content":content}])
    return res.choices[0].message.content.replace("**", "").replace("*", "").strip()

# --- 3. 메인 화면 ---
st.title("🌸 모그 작가님 AI 비서 🌸")

with st.container():
    col1, col2 = st.columns([1, 1.5], gap="large")
    with col1:
        st.header("📸 작품 사진")
        up_img = st.file_uploader("사진을 올려주세요^^", type=["jpg", "png", "jpeg"])
        if up_img:
            st.image(up_img, use_container_width=True)
            if st.button("🔍 사진 분석 시작"):
                st.session_state.img_analysis = analyze_image(up_img)
                st.rerun()
    with col2:
        st.header("📝 작품 정보")
        c1, c2 = st.columns(2)
        st.session_state.m_name = c1.text_input("📦 작품 이름", value=st.session_state.m_name)
        st.session_state.m_mat = c2.text_input("🧵 소재", value=st.session_state.m_mat)
        c3, c4 = st.columns(2)
        st.session_state.m_per = c3.text_input("⏳ 기간", value=st.session_state.m_per)
        st.session_state.m_size = c4.text_input("📏 사이즈", value=st.session_state.m_size)
        st.session_state.m_det = st.text_area("✨ 정성 포인트", value=st.session_state.m_det, height=120)

st.divider()

tabs = st.tabs(["✍️ 판매글 쓰기", "💬 고민 상담소"])

with tabs[0]:
    st.markdown("### 🚀 플랫폼 선택")
    b1, b2, b3 = st.columns(3)
    if b1.button("📸 인스타그램"): st.session_state.texts["인스타"] = ask_mog_ai("인스타그램")
    if b2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스")
    if b3.button("🛍️ 스마트스토어"): st.session_state.texts["스토어"] = ask_mog_ai("스마트스토어")

    for p_name, key in [("인스타그램", "인스타"), ("아이디어스", "아이디어스"), ("스마트스토어", "스토어")]:
        if st.session_state.texts[key]:
            st.markdown(f"---")
            st.markdown(f"### ✨ 완성된 {p_name} 글")
            st.markdown(f'<div class="result-card">{st.session_state.texts[key].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            col_f1, col_f2 = st.columns([4, 1])
            feedback = col_f1.text_input(f"✍️ 수정 요청", key=f"f_{key}")
            if col_f2.button("🚀 반영", key=f"b_{key}"):
                st.session_state.texts[key] = ask_mog_ai(p_name, user_in=st.session_state.texts[key], feedback=feedback)
                st.rerun()

with tabs[1]:
    st.header("💬 작가님 고민 상담소")
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.write(m["content"])
    if pr := st.chat_input("작가님, 어떤 고민이 있으신가요?"):
        st.session_state.chat_log.append({"role": "user", "content": pr})
        st.session_state.chat_log.append({"role": "assistant", "content": ask_mog_ai("상담", user_in=pr)})
        st.rerun()
