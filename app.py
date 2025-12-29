import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
from streamlit_google_auth import Authenticate
import json
import os
import inspect

# 1. 페이지 설정 (반드시 최상단)
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- 🔐 구글 로그인 설정 (어떤 라이브러리 버전이든 대응) ---
# JSON 파일 생성
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

# [무적의 Authenticate 로직] - 라이브러리가 원하는 이름을 알아서 찾습니다.
try:
    sig = inspect.signature(Authenticate.__init__)
    params = sig.parameters.keys()
    
    auth_kwargs = {}
    # 버전 1 대응
    if 'client_secrets_file' in params:
        auth_kwargs['client_secrets_file'] = "client_secrets.json"
    # 버전 2 대응 (직접 ID를 받는 경우)
    elif 'google_client_id' in params:
        auth_kwargs['google_client_id'] = st.secrets["GOOGLE_CLIENT_ID"]
        auth_kwargs['google_client_secret'] = st.secrets["GOOGLE_CLIENT_SECRET"]
        auth_kwargs['redirect_uri'] = st.secrets["REDIRECT_URI"]

    # 키 이름 자동 매칭
    if 'cookie_key' in params: auth_kwargs['cookie_key'] = st.secrets["AUTH_SECRET_KEY"]
    elif 'secret_key' in params: auth_kwargs['secret_key'] = st.secrets["AUTH_SECRET_KEY"]
    
    if 'cookie_name' in params: auth_kwargs['cookie_name'] = "mom_ai_login_cookie"
    if 'cookie_expiry_days' in params: auth_kwargs['cookie_expiry_days'] = 30

    auth = Authenticate(**auth_kwargs)

except Exception as e:
    # 위 방법도 실패할 경우를 대비한 최후의 보루 (강제 주입)
    try:
        auth = Authenticate("client_secrets.json", "mom_ai_login_cookie", st.secrets["AUTH_SECRET_KEY"], 30)
    except:
        auth = Authenticate(
            secret_key=st.secrets["AUTH_SECRET_KEY"],
            google_client_id=st.secrets["GOOGLE_CLIENT_ID"],
            google_client_secret=st.secrets["GOOGLE_CLIENT_SECRET"],
            redirect_uri=st.secrets["REDIRECT_URI"]
        )

# 🔑 로그인 체크
auth.check_authentification()

if not st.session_state.get('connected'):
    st.markdown("<h1 style='text-align: center;'>🌸 모그 작가님 AI 비서 🌸</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>작가님, 로그인이 필요해요^^</p>", unsafe_allow_html=True)
    auth.login()
    st.stop()

# --- 🔑 로그인 성공 후 본문 ---
user_id = st.session_state['user_info'].get('email', 'mom_mog_01')

# Firebase 초기화
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()
api_key = st.secrets["OPENAI_API_KEY"]

# --- ✨ UI 및 로직 ---
def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    base_style = "[1인칭 작가 시점] 당신은 핸드메이드 작가 '모그(Mog)'입니다. 말투: ~이지요^^, ~해요. 특수기호(*, **) 금지."
    
    if platform == "인스타그램": system_p = f"{base_style} 감성 제작 일기 형식."
    elif platform == "아이디어스": system_p = f"{base_style} 💡상세설명, 🍀Add info., 🔉안내 포맷 엄수."
    elif platform == "스마트스토어": system_p = f"{base_style} 💐상품명, 🌸디자인, 📏사이즈 포맷 엄수."
    else: system_p = f"{base_style} 다정한 선배 작가로서 고민 상담."

    info = f"작품:{st.session_state.get('m_name','')}, 소재:{st.session_state.get('m_mat','')}, 포인트:{st.session_state.get('m_det','')}"
    content = f"수정요청: {feedback}\n기존: {user_in}" if feedback else f"정보: {info} / {user_in}"
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":system_p},{"role":"user","content":content}])
    return res.choices[0].message.content.replace("**", "").replace("*", "").strip()

# --- 메인 화면 ---
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
    if col1.button("📸 인스타그램"): st.session_state.texts["인스타"] = ask_mog_ai("인스타그램")
    if col2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스")
    if col3.button("🛍️ 스마트스토어"): st.session_state.texts["스토어"] = ask_mog_ai("스마트스토어")

    for p_name, key in [("인스타그램", "인스타"), ("아이디어스", "아이디어스"), ("스마트스토어", "스토어")]:
        if st.session_state.texts[key]:
            st.markdown(f"### ✨ 완성된 {p_name} 글")
            st.info(st.session_state.texts[key])

with tabs[1]:
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.write(m["content"])
    if pr := st.chat_input("작가님 고민을 말해주세요^^"):
        st.session_state.chat_log.append({"role": "user", "content": pr})
        st.session_state.chat_log.append({"role": "assistant", "content": ask_mog_ai("상담", user_in=pr)})
        st.rerun()
