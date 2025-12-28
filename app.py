import streamlit as st
import openai
from PIL import Image
import io
import base64
import firebase_admin
from firebase_admin import credentials, firestore
from streamlit_google_auth import Authenticate

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- 🔐 구글 로그인 설정 (Secrets 정보 사용) ---
auth = Authenticate(
    secret_key=st.secrets.get("AUTH_SECRET_KEY", "default_secret_key"),
    client_id=st.secrets.get("GOOGLE_CLIENT_ID"),
    client_secret=st.secrets.get("GOOGLE_CLIENT_SECRET"),
    redirect_uri=st.secrets.get("REDIRECT_URI"),
    cookie_name="mom_ai_login"
)

# --- 🔥 Firebase 초기화 ---
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"]))
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase 설정 확인 필요: {e}")

db = firestore.client()

# --- ✨ UI 스타일 가이드 (따님 원본 100%) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FCF9F6; font-family: 'Noto Sans KR', sans-serif; }
    label p { font-size: 24px !important; font-weight: bold !important; color: #5D4037 !important; }
    h1 { color: #8D6E63 !important; text-align: center; margin-bottom: 30px; font-weight: 800; }
    .stTextInput input, .stTextArea textarea { 
        font-size: 22px !important; border-radius: 15px !important; 
        border: 2px solid #E0D4CC !important; padding: 20px !important; background-color: #FFFFFF !important; 
    }
    .stButton>button { 
        width: 100%; border-radius: 20px; height: 4.5em; background-color: #8D6E63 !important; 
        color: white !important; font-weight: bold; font-size: 22px !important; transition: 0.3s; 
    }
    .stButton>button:hover { background-color: #6D4C41 !important; transform: translateY(-2px); }
    .result-card { 
        background-color: #FFFFFF; padding: 30px; border-radius: 25px; 
        border-left: 10px solid #D7CCC8; box-shadow: 0 10px 20px rgba(0,0,0,0.05); margin-bottom: 20px; 
    }
    .stTabs [data-baseweb="tab-list"] button { font-size: 26px !important; font-weight: bold !important; padding: 15px 30px; }
    </style>
    """, unsafe_allow_html=True)

# --- 🔑 로그인 체크 ---
auth.check_authentification()

if not st.session_state.get('connected'):
    st.title("🌸 모그 작가님 AI 비서 🌸")
    st.markdown("<h3 style='text-align: center;'>작가님, 로그인을 해주셔야 기록이 저장돼요^^</h3>", unsafe_allow_html=True)
    auth.login()
    st.stop()

# 로그인 성공 시 유저 이메일을 ID로 사용
user_id = st.session_state['user_info'].get('email', 'mom_mog_01')

# 2. 필수 설정
api_key = st.secrets.get("OPENAI_API_KEY")

# --- 💾 Firebase 데이터 연동 함수 ---
def save_data(uid, data):
    db.collection("users").document(uid).set(data)

def load_data(uid):
    doc = db.collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None

# 세션 상태 초기화 및 데이터 로드 (로그인 직후 1회 실행)
if 'init_done' not in st.session_state:
    saved = load_data(user_id)
    if saved:
        st.session_state.update(saved)
    else:
        st.session_state.update({
            'texts': {"인스타": "", "아이디어스": "", "스토어": ""},
            'chat_log': [], 'm_name': '', 'm_mat': '', 'm_per': '', 'm_size': '', 'm_det': '', 'img_analysis': ''
        })
    st.session_state.init_done = True

# --- [로직: 따님 설계 100% 반영] ---
def analyze_image(img_file):
    client = openai.OpenAI(api_key=api_key)
    base64_image = base64.b64encode(img_file.getvalue()).decode('utf-8')
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": "핸드메이드 작가 모그의 작품이야. 색감과 디테일을 1인칭 시점으로 다정하게 묘사해줘."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]}]
    )
    return response.choices[0].message.content

def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    base_style = """
    [절대 규칙: 1인칭 작가 시점]
    - 당신은 작가 '모그(Mog)' 본인입니다. 말투: ~이지요^^, ~해요 등 다정한 어투.
    - 특수기호(*, **) 절대 금지. 줄바꿈 넉넉하게.
    """
    if platform == "인스타그램": system_p = f"{base_style} [📸 인스타그램] 감성 문구와 제작 일기 연결."
    elif platform == "아이디어스": system_p = f"{base_style} [🎨 아이디어스] 💡상세설명, 🍀Add info., 🔉안내, 👍🏻작가보증 포맷 엄수."
    elif platform == "스마트스토어": system_p = f"{base_style} [🛍️ 스토어] 💐상품명, 🌸디자인, 👜기능성, 📏사이즈, 📦소재, 🧼관리, 📍추천 엄수."
    else: system_p = f"{base_style} [💬 상담소] 다정한 선배 작가 시점."

    info = f"작품:{st.session_state.m_name}, 소재:{st.session_state.m_mat}, 정성:{st.session_state.m_det}"
    if st.session_state.img_analysis: info += f"\n[사진 디테일]: {st.session_state.img_analysis}"
    content = f"수정 요청: {feedback}\n기존 내용: {user_in}" if feedback else f"정보: {info} / {user_in}"
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":system_p},{"role":"user","content":content}])
    return res.choices[0].message.content.replace("**", "").replace("*", "").strip()

# --- 3. 메인 화면 ---
st.sidebar.title("🌸 작가님 정보")
st.sidebar.write(f"접속계정: {user_id}")
if st.sidebar.button("로그아웃"):
    auth.logout()

st.title("🌸 모그 작가님 AI 비서 🌸")

with st.container():
    col1, col2 = st.columns([1, 1.5], gap="large")
    with col1:
        st.header("📸 작품 사진")
        up_img = st.file_uploader("작품 사진을 올려주세요^^", type=["jpg", "png", "jpeg"])
        if up_img:
            st.image(up_img, use_container_width=True)
            if st.button("🔍 사진 분석 시작하기"):
                st.session_state.img_analysis = analyze_image(up_img)
                st.rerun()
    with col2:
        st.header("📝 작품 정보")
        c1, c2 = st.columns(2)
        st.session_state.m_name = c1.text_input("📦 작품 이름", value=st.session_state.m_name)
        st.session_state.m_mat = c2.text_input("🧵 소재", value=st.session_state.m_mat)
        c3, c4 = st.columns(2)
        st.session_state.m_per = c3.text_input("⏳ 제작 기간", value=st.session_state.m_per)
        st.session_state.m_size = c4.text_input("📏 사이즈", value=st.session_state.m_size)
        st.session_state.m_det = st.text_area("✨ 정성 포인트와 설명", value=st.session_state.m_det, height=120)
        
        if st.button("💾 이 정보들 저장하기"):
            save_data(user_id, {
                'm_name': st.session_state.m_name, 'm_mat': st.session_state.m_mat,
                'm_per': st.session_state.m_per, 'm_size': st.session_state.m_size,
                'm_det': st.session_state.m_det, 'texts': st.session_state.texts,
                'chat_log': st.session_state.chat_log, 'img_analysis': st.session_state.img_analysis
            })
            st.success("작가님의 소중한 기록을 저장했어요! 🌸")

st.divider()

tabs = st.tabs(["✍️ 판매글 쓰기", "💬 고민 상담소"])

with tabs[0]:
    st.markdown("### 🚀 어떤 플랫폼에 올릴 글을 써볼까요?")
    b1, b2, b3 = st.columns(3)
    if b1.button("📸 인스타그램"): st.session_state.texts["인스타"] = ask_mog_ai("인스타그램")
    if b2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스")
    if b3.button("🛍️ 스마트스토어"): st.session_state.texts["스토어"] = ask_mog_ai("스마트스토어")

    for p_name, key in [("인스타그램", "인스타"), ("아이디어스", "아이디어스"), ("스마트스토어", "스토어")]:
        if st.session_state.texts[key]:
            st.markdown(f"---")
            st.markdown(f"### ✨ 완성된 {p_name} 글입니다^^")
            st.markdown(f'<div class="result-card">{st.session_state.texts[key].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            col_f1, col_f2 = st.columns([4, 1])
            feedback = col_f1.text_input(f"✍️ 수정 요청", key=f"f_{key}")
            if col_f2.button("🚀 반영하기", key=f"b_{key}"):
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
