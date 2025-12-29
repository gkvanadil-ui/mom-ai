import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
from streamlit_google_auth import Authenticate
import json
import os
import base64

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- 🔐 구글 로그인 및 TypeError 방어 ---
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

try:
    auth = Authenticate(
        client_secrets_file="client_secrets.json",
        cookie_name="mom_ai_login_cookie",
        cookie_key=st.secrets["AUTH_SECRET_KEY"],
        cookie_expiry_days=30
    )
except TypeError:
    auth = Authenticate("client_secrets.json", "mom_ai_login_cookie", st.secrets["AUTH_SECRET_KEY"])

auth.check_authentification()

if not st.session_state.get('connected'):
    st.markdown("<h1 style='text-align: center; color: #8D6E63;'>🌸 모그 작가님 AI 비서 🌸</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 20px;'>작가님, 안전한 기록 저장을 위해 로그인이 필요해요^^</p>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        auth.login()
    st.stop()

# --- 🔑 로그인 성공 후 본문 ---
user_id = st.session_state['user_info'].get('email', 'mom_mog_01')

if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()
api_key = st.secrets["OPENAI_API_KEY"]

# --- ✨ [핵심] 복구된 AI 프롬프트 (따님 설계 100% 반영) ---

def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    # 작가님 특유의 다정한 말투 기본 장착
    base_style = "[절대 규칙: 1인칭 작가 시점] 당신은 핸드메이드 작가 '모그(Mog)'입니다. 말투: ~이지요^^, ~해요, ~답니다 등 다정하고 따뜻하게. 특수기호(*, **) 사용 금지."
    
    if platform == "인스타그램":
        system_p = f"{base_style} [📸 인스타그램 전용] 감성적인 문구로 시작해서 제작 과정의 정성을 일기처럼 적고, 마지막엔 따뜻한 인사를 건네줘."
    elif platform == "아이디어스":
        system_p = f"{base_style} [🎨 아이디어스 전용] 반드시 다음 포맷을 지켜줘: 💡상세설명, 🍀Add info., 🔉안내, 👍🏻작가보증."
    elif platform == "스마트스토어":
        system_p = f"{base_style} [🛍️ 스마트스토어 전용] 반드시 다음 포맷을 지켜줘: 💐상품명, 🌸디자인, 👜기능성, 📏사이즈, 📦소재, 🧼관리, 📍추천."
    else:
        system_p = f"{base_style} [💬 고민 상담소] 따뜻한 선배 작가로서 후배의 고민을 들어주고 공감하며 위로해줘."

    info = f"작품명:{st.session_state.get('m_name','')}, 소재:{st.session_state.get('m_mat','')}, 포인트:{st.session_state.get('m_det','')}"
    content = f"수정요청: {feedback}\n기존글: {user_in}" if feedback else f"정보: {info}\n작가님 요청: {user_in}"
    
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":system_p},{"role":"user","content":content}])
    return res.choices[0].message.content.replace("**", "").replace("*", "").strip()

# --- 화면 구성 및 데이터 로드 ---
if 'texts' not in st.session_state:
    doc = db.collection("users").document(user_id).get()
    if doc.exists: st.session_state.update(doc.to_dict())
    else: st.session_state.update({'texts': {"인스타": "", "아이디어스": "", "스토어": ""}, 'chat_log': [], 'm_name': '', 'm_mat': '', 'm_det': ''})

st.title("🌸 모그 작가님 AI 비서 🌸")

with st.container():
    st.header("📝 작품 정보")
    c1, c2 = st.columns(2)
    st.session_state.m_name = c1.text_input("📦 이름", value=st.session_state.m_name)
    st.session_state.m_mat = c2.text_input("🧵 소재", value=st.session_state.m_mat)
    st.session_state.m_det = st.text_area("✨ 정성 가득한 포인트", value=st.session_state.m_det)
    if st.button("💾 이 정보 저장하기"):
        db.collection("users").document(user_id).set({
            'm_name': st.session_state.m_name, 'm_mat': st.session_state.m_mat, 
            'm_det': st.session_state.m_det, 'texts': st.session_state.texts, 'chat_log': st.session_state.chat_log
        })
        st.success("저장되었어요^^ 🌸")

st.divider()
tabs = st.tabs(["✍️ 판매글 쓰기", "💬 고민 상담소"])

with tabs[0]:
    b1, b2, b3 = st.columns(3)
    if b1.button("📸 인스타 감성글"): st.session_state.texts["인스타"] = ask_mog_ai("인스타그램")
    if b2.button("🎨 아이디어스 양식"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스")
    if b3.button("🛍️ 스토어 상세설명"): st.session_state.texts["스토어"] = ask_mog_ai("스마트스토어")

    for p_name, key in [("인스타그램", "인스타"), ("아이디어스", "아이디어스"), ("스마트스토어", "스토어")]:
        if st.session_state.texts[key]:
            st.markdown(f"### ✨ 완성된 {p_name} 글")
            st.markdown(f'<div style="background: white; padding: 25px; border-radius: 15px; border-left: 10px solid #D7CCC8;">{st.session_state.texts[key].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            f_in = st.text_input(f"✍️ 여기를 조금 고쳐볼까요? ({p_name})", key=f"f_{key}")
            if st.button(f"🚀 반영하기", key=f"b_{key}"):
                st.session_state.texts[key] = ask_mog_ai(p_name, st.session_state.texts[key], f_in)
                st.rerun()

with tabs[1]:
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.write(m["content"])
    if pr := st.chat_input("작가님, 어떤 고민이 있으신가요?^^"):
        st.session_state.chat_log.append({"role": "user", "content": pr})
        st.session_state.chat_log.append({"role": "assistant", "content": ask_mog_ai("상담", user_in=pr)})
        st.rerun()
