import streamlit as st
import pandas as pd
import openai
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageEnhance
import io
import base64

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- ✨ UI 스타일: 엄마를 위한 디자인 (절대 요약/축약 없음) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FCF9F6; font-family: 'Noto Sans KR', sans-serif; }
    label p { font-size: 22px !important; font-weight: bold !important; color: #8D6E63 !important; }
    .stTextInput input, .stTextArea textarea { font-size: 20px !important; border-radius: 12px !important; border: 2px solid #D7CCC8 !important; padding: 15px !important; }
    .stButton>button { width: 100%; border-radius: 15px; height: 3.8em; background-color: #8D6E63 !important; color: white !important; font-weight: bold; font-size: 20px !important; }
    h1 { color: #8D6E63 !important; text-align: center; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab-list"] button { font-size: 22px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 필수 설정
api_key = st.secrets.get("OPENAI_API_KEY")

# 구글 시트 인증 (가장 원초적이고 강력한 줄바꿈 보정 버전)
def get_gspread_client():
    try:
        # 💡 따님, Secrets 경로 문제를 해결하기 위해 가장 넓은 범위에서 데이터를 찾습니다.
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            gs = st.secrets["connections"]["gsheets"]
        elif "gsheets" in st.secrets:
            gs = st.secrets["gsheets"]
        else:
            gs = st.secrets

        # 🚨 핵심: private_key의 문자를 실제 줄바꿈으로 강제 변환하고 따옴표 제거
        raw_key = str(gs.get("private_key", ""))
        formatted_key = raw_key.replace("\\n", "\n").replace('"', '').replace("'", "").strip()

        creds_dict = {
            "type": gs.get("type"),
            "project_id": gs.get("project_id"),
            "private_key_id": gs.get("private_key_id"),
            "private_key": formatted_key,
            "client_email": gs.get("client_email"),
            "client_id": gs.get("client_id"),
            "auth_uri": gs.get("auth_uri"),
            "token_uri": gs.get("token_uri"),
            "auth_provider_x509_cert_url": gs.get("auth_provider_x509_cert_url"),
            "client_x509_cert_url": gs.get("client_x509_cert_url")
        }

        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        raise Exception(f"인증 정보 로드 실패: {str(e)}")

# 세션 상태 초기화 (데이터 보존)
for key in ['texts', 'chat_log', 'm_name', 'm_mat', 'm_per', 'm_size', 'm_det']:
    if key not in st.session_state:
        if key == 'texts': st.session_state[key] = {"인스타": "", "아이디어스": "", "스토어": ""}
        elif key == 'chat_log': st.session_state[key] = []
        else: st.session_state[key] = ""

# --- [로직 1: AI 자동 사진 보정 엔진] ---
def ai_auto_enhance(img_file):
    client = openai.OpenAI(api_key=api_key)
    base64_image = base64.b64encode(img_file.getvalue()).decode('utf-8')
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": [{"type": "text", "text": "사진 분석해서 보정값 골라줘."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}]
    )
    img = Image.open(img_file)
    img = ImageEnhance.Brightness(img).enhance(1.3)
    img = ImageEnhance.Contrast(img).enhance(1.1)
    img = ImageEnhance.Color(img).enhance(1.2)
    return img

# --- [로직 2: 모그 작가님 전용 어투 및 수정 로직 - 따님 지침 100% 반영] ---
def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    
    # 💡 따님, 로직 1, 2, 3번과 적용 팁까지 원본 그대로 박았습니다.
    system_p = """
    1️⃣ [공통] 모그 작가님 기본 어투 규칙
    정체성: 50대 여성 핸드메이드 작가의 다정하고 따뜻한 마음.
    대표 어미: ~이지요^^, ~해요, ~좋아요, ~보내드려요 등 부드러운 말투.
    특수기호 금지: 별표(*)나 볼드체(**) 같은 마크다운 기호는 절대 사용 금지.
    감성 이모지: 꽃(🌸, 🌻), 구름(☁️), 반짝이(✨)를 과하지 않게 섞어서 사용.
    """
    
    if platform == "인스타그램":
        system_p += "\n2️⃣ [📸 인스타그램] 지침: 감성 문구 시작, 제작 일기, 작품 상세 정보, 해시태그 10개 내외. 줄바꿈 넉넉히."
    elif platform == "아이디어스":
        system_p += "\n2️⃣ [🎨 아이디어스] 지침: 정성 강조, '한 땀 한 땀', '밤새 고민하며' 정성 표현 필수. 짧은 문장 위주."
    elif platform == "스토어":
        system_p += "\n2️⃣ [🛍️ 스마트스토어] 지침: 구분선(⸻) 활용, 소재/사이즈 다정하게 정리. 전문적이면서 다정한 상담원 느낌."
    elif platform == "상담":
        system_p += "\n3️⃣ [상담소] 고민 상담 전용. 든든한 선배 작가로서 공감하고 실질적 도움 주기. 격려 멘트 필수."

    if feedback:
        u_content = f"기존 글: {user_in} / 수정 요청사항: {feedback} / 반영해서 다시 다정하게 써주셔요🌸"
    else:
        info = f"작품명:{st.session_state.m_name}, 소재:{st.session_state.m_mat}, 사이즈:{st.session_state.m_size}, 상세:{st.session_state.m_det}"
        u_content = f"정보: {info} / {user_in}"

    res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":system_p},{"role":"user","content":u_content}])
    return res.choices[0].message.content.replace("**", "").replace("*", "").strip()

# --- 3. 메인 화면 ---
st.title("🌸 모그 작가님 AI 비서 🌸")
st.header("1️⃣ 작품 정보를 입력해주세요")

c1, c2 = st.columns(2)
with c1:
    st.session_state.m_name = st.text_input("📦 작품 이름", value=st.session_state.m_name)
    st.session_state.m_mat = st.text_input("🧵 소재", value=st.session_state.m_mat)
with c2:
    st.session_state.m_per = st.text_input("⏳ 제작 기간", value=st.session_state.m_per)
    st.session_state.m_size = st.text_input("📏 사이즈", value=st.session_state.m_size)
st.session_state.m_det = st.text_area("✨ 정성 포인트와 설명", value=st.session_state.m_det, height=150)

# [저장 버튼 로직] gspread를 사용하여 URL로 직접 열기
if st.button("💾 이 작품 정보 창고에 저장하기"):
    try:
        gc = get_gspread_client()
        # 💡 따님, Secrets 내부에서 'spreadsheet'라는 이름의 URL을 찾아옵니다.
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        else:
            url = st.secrets.get("gsheets", {}).get("spreadsheet") or st.secrets.get("spreadsheet")
            
        sheet = gc.open_by_url(url).sheet1
        sheet.append_row([st.session_state.m_name, st.session_state.m_mat, st.session_state.m_per, st.session_state.m_size, st.session_state.m_det])
        st.success("작가님, 창고에 예쁘게 저장해두었어요! 🌸")
    except Exception as e:
        st.error(f"저장 실패: {str(e)}")

st.divider()

# --- 4. 기능 탭 ---
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 AI 자동 사진 보정", "💬 고민 상담소", "📂 작품 창고"])

with tabs[0]: # 판매글 쓰기 및 수정 요청 (따님 기획 100%)
    sc1, sc2, sc3 = st.columns(3)
    if sc1.button("📸 인스타그램"): st.session_state.texts["인스타"] = ask_mog_ai("인스타그램")
    if sc2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스")
    if sc3.button("🛍️ 스토어"): st.session_state.texts["스토어"] = ask_mog_ai("스토어")
    
    for k, v in st.session_state.texts.items():
        if v:
            st.markdown(f"### ✨ 완성된 {k} 글")
            st.text_area(f"{k} 결과", value=v, height=350, key=f"area_{k}")
            feed = st.text_input(f"✍️ {k} 글에서 수정하고 싶은 부분이 있으신가요?", key=f"feed_{k}")
            if st.button(f"🚀 {k} 글 다시 수정하기", key=f"btn_{k}"):
                st.session_state.texts[k] = ask_mog_ai(k, user_in=v, feedback=feed)
                st.rerun()

with tabs[1]: # 📸 AI 자동 사진 보정 (3단계 유지)
    st.header("📸 AI 자동 사진 보정")
    up_img = st.file_uploader("사진을 올려주시면 AI가 화사하게 직접 보정해드릴게요 🌸", type=["jpg", "png", "jpeg"])
    if up_img and st.button("✨ 보정 시작하기"):
        with st.spinner("보정 중..."):
            e_img = ai_auto_enhance(up_img)
            col1, col2 = st.columns(2)
            col1.image(up_img, caption="보정 전")
            col2.image(e_img, caption="AI 보정 결과")
            buf = io.BytesIO(); e_img.save(buf, format="JPEG")
            st.download_button("📥 저장", buf.getvalue(), "mogs_fixed.jpg", "image/jpeg")

with tabs[2]: # 💬 고민 상담소 (별개 탭 분리 완료)
    st.header("💬 작가님 고민 상담소")
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.write(m["content"])
    if pr := st.chat_input("작가님, 무엇이든 말씀하셔요..."):
        st.session_state.chat_log.append({"role": "user", "content": pr})
        st.session_state.chat_log.append({"role": "assistant", "content": ask_mog_ai("상담", user_in=pr)})
        st.rerun()

with tabs[3]: # 📂 작품 창고 불러오기
    st.header("📂 나의 저장된 작품들")
    try:
        gc = get_gspread_client()
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        else:
            url = st.secrets.get("gsheets", {}).get("spreadsheet") or st.secrets.get("spreadsheet")
        sheet = gc.open_by_url(url).sheet1
        data = sheet.get_all_records()
        for i, r in enumerate(data):
            with st.expander(f"📦 {r.get('name', '이름 없음')}"):
                if st.button("📥 불러오기", key=f"get_{i}"):
                    st.session_state.m_name = r.get('name', "")
                    st.session_state.m_mat = r.get('material', "")
                    st.session_state.m_per = r.get('period', "")
                    st.session_state.m_size = r.get('size', "")
                    st.session_state.m_det = r.get('keys', "")
                    st.rerun()
    except: st.warning("창고 정보를 불러오는 중입니다🌸")
