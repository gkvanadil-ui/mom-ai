import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
from streamlit_google_auth import Authenticate
import json
import os

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- 🔐 구글 로그인 (TypeError 완벽 방지) ---
client_secrets = {
    "web": {
        "client_id": st.secrets["GOOGLE_CLIENT_ID"],
        "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [st.secrets["REDIRECT_URI"]]
    }
}
with open("client_secrets.json", "w") as f:
    json.dump(client_secrets, f)

# 인자 이름을 명시하여 TypeError 해결
auth = Authenticate(
    secret_key=st.secrets["AUTH_SECRET_KEY"],
    google_client_id=st.secrets["GOOGLE_CLIENT_ID"],
    google_client_secret=st.secrets["GOOGLE_CLIENT_SECRET"],
    redirect_uri=st.secrets["REDIRECT_URI"],
    cookie_name="mom_ai_login_cookie",
    cookie_expiry_days=30
)

auth.check_authentification()

if not st.session_state.get('connected'):
    st.markdown("<h1 style='text-align: center; color: #8D6E63;'>🌸 모그 작가님 AI 비서 🌸</h1>", unsafe_allow_html=True)
    auth.login()
    st.stop()

# --- 🔑 로그인 성공 후 로직 ---
user_id = st.session_state['user_info'].get('email', 'mom_mog_01')
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"]))
    firebase_admin.initialize_app(cred)
db = firestore.client()
api_key = st.secrets["OPENAI_API_KEY"]

# --- ✨ [복구 완료] 플랫폼별 프롬프트 ---
def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    base_style = "[1인칭 작가 시점] 당신은 작가 '모그'입니다. 말투: ~이지요^^, ~해요 등 다정하게. 특수기호(*, **) 금지."
    
    if platform == "인스타그램":
        system_p = f"{base_style} [📸 인스타그램] 감성 문구와 제작 일기 형식."
    elif platform == "아이디어스":
        system_p = f"{base_style} [🎨 아이디어스] 💡상세설명, 🍀Add info., 🔉안내, 👍🏻작가보증 포맷 엄수."
    elif platform == "스마트스토어":
        system_p = f"{base_style} [🛍️ 스마트스토어] 💐상품명, 🌸디자인, 👜기능성, 📏사이즈, 📦소재, 🧼관리, 📍추천 포맷 엄수."
    else:
        system_p = f"{base_style} [💬 고민 상담소] 다정하게 공감하며 위로해줘."

    info = f"작품:{st.session_state.get('m_name','')}, 소재:{st.session_state.get('m_mat','')}, 포인트:{st.session_state.get('m_det','')}"
    content = f"수정요청: {feedback}\n기존: {user_in}" if feedback else f"정보: {info}\n요청: {user_in}"
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":system_p},{"role":"user","content":content}])
    return res.choices[0].message.content.replace("**", "").replace("*", "").strip()

# --- 화면 구성 ---
st.title("🌸 모그 작가님 AI 비서 🌸")
if 'texts' not in st.session_state:
    st.session_state.update({'texts': {"인스타": "", "아이디어스": "", "스토어": ""}, 'chat_log': [], 'm_name': '', 'm_mat': '', 'm_det': ''})

with st.container():
    st.header("📝 작품 정보")
    st.session_state.m_name = st.text_input("📦 이름", value=st.session_state.m_name)
    st.session_state.m_mat = st.text_input("🧵 소재", value=st.session_state.m_mat)
    st.session_state.m_det = st.text_area("✨ 포인트", value=st.session_state.m_det)

st.divider()
tabs = st.tabs(["✍️ 판매글 쓰기", "💬 고민 상담소"])

with tabs[0]:
    col1, col2, col3 = st.columns(3)
    if col1.button("📸 인스타"): st.session_state.texts["인스타"] = ask_mog_ai("인스타그램")
    if col2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스")
    if col3.button("🛍️ 스토어"): st.session_state.texts["스토어"] = ask_mog_ai("스마트스토어")

    for key in ["인스타", "아이디어스", "스토어"]:
        if st.session_state.texts[key]:
            st.info(st.session_state.texts[key])
