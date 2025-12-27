import streamlit as st
import pandas as pd
import openai
from streamlit_gsheets import GSheetsConnection
from PIL import Image, ImageEnhance
import io
import base64

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- ✨ UI 스타일: 엄마를 위해 글씨는 크게, 칸은 명확하게 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FCF9F6; font-family: 'Noto Sans KR', sans-serif; }
    label p { font-size: 22px !important; font-weight: bold !important; color: #8D6E63 !important; }
    .stTextInput input, .stTextArea textarea { font-size: 20px !important; border-radius: 12px !important; border: 2px solid #D7CCC8 !important; padding: 15px !important; }
    .stButton>button { width: 100%; border-radius: 15px; height: 3.5em; background-color: #8D6E63 !important; color: white !important; font-weight: bold; font-size: 20px !important; }
    h1 { color: #8D6E63 !important; text-align: center; margin-bottom: 30px; }
    .stTabs [data-baseweb="tab-list"] button { font-size: 22px !important; font-weight: bold !important; }
    /* 수정 요청 칸 강조 */
    .stTextInput label { color: #E57373 !important; } 
    </style>
    """, unsafe_allow_html=True)

# 2. 필수 연결 설정
api_key = st.secrets.get("OPENAI_API_KEY")
SHEET_URL = "https://docs.google.com/spreadsheets/d/1tz4pYbxyV8PojkzYtPz82OhiAGD2XoWVZqlTpwAebaA/edit?usp=sharing"

# 세션 상태 초기화 (데이터 보존)
if 'texts' not in st.session_state: st.session_state.texts = {"인스타": "", "아이디어스": "", "스토어": ""}
if 'chat_log' not in st.session_state: st.session_state.chat_log = []

# --- [함수: AI 자동 사진 보정 엔진] ---
def ai_auto_enhance(img_file):
    client = openai.OpenAI(api_key=api_key)
    base64_image = base64.b64encode(img_file.getvalue()).decode('utf-8')
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": [{"type": "text", "text": "사진 분석해서 'B:수치, C:수치, S:수치' 형식으로 보정값만 골라줘."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}]
    )
    res_text = response.choices[0].message.content
    try:
        parts = res_text.split(',')
        b_val = float(parts[0].split(':')[1]); c_val = float(parts[1].split(':')[1]); s_val = float(parts[2].split(':')[1])
    except: b_val, c_val, s_val = 1.2, 1.1, 1.1
    
    img = Image.open(img_file)
    img = ImageEnhance.Brightness(img).enhance(b_val)
    img = ImageEnhance.Contrast(img).enhance(c_val)
    img = ImageEnhance.Color(img).enhance(s_val)
    return img, f"밝기:{b_val}, 대비:{c_val}, 채도:{s_val}"

# --- [함수: 모그 작가님 전용 어투 로직 - 따님 가이드 100% 적용] ---
def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    
    # 1️⃣ [공통] 규칙
    base_rules = """
    정체성: 50대 여성 핸드메이드 작가의 다정하고 따뜻한 마음.
    대표 어미: ~이지요^^, ~해요, ~좋아요, ~보내드려요 등 부드러운 말투.
    특수기호 금지: 별표(*)나 볼드체(**) 같은 마크다운 기호는 절대 사용 금지 (엄마가 보기 편하도록!).
    감성 이모지: 꽃(🌸, 🌻), 구름(☁️), 반짝이(✨)를 과하지 않게 섞어서 사용.
    """
    
    # 2️⃣ [플랫폼별] 특화 로직
    if platform == "인스타그램":
        system_p = f"{base_rules} [📸 인스타그램 - 감성 일기 모드] 지침: 사진을 보자마자 마음이 따뜻해지는 문구로 시작할 것. 구성: [첫 줄 감성 문구] + [작가님의 제작 일기] + [작품 상세 정보] + [다정한 인사] + [해시태그]. 특징: 줄바꿈을 아주 넉넉히 해서 가독성을 높이고, 해시태그는 10개 내외로 달기."
    elif platform == "아이디어스":
        system_p = f"{base_rules} [🎨 아이디어스 - 정성 가득 모드] 지침: 작가님의 수고와 정성이 고객에게 고스란히 전달되게 할 것. 구성: 매우 잦은 줄바꿈과 짧은 문장 위주. 내용: '한 땀 한 땀', '밤새 고민하며' 등 정성이 듬뿍 느껴지는 단어 사용."
    elif platform == "스토어":
        system_p = f"{base_rules} [🛍️ 스마트스토어 - 친절 정보 모드] 지침: 필요한 정보를 한눈에 보기 좋게 정리하되, 딱딱하지 않게 설명할 것. 구성: 구분선(⸻)을 사용하여 소재, 사이즈, 관리법을 명확히 구분. 특징: 전문적이면서도 다정한 '상담원' 같은 느낌으로 신뢰감 주기."
    elif platform == "상담":
        system_p = f"{base_rules} [3️⃣ 상담소 전용 로직] 역할: 핸드메이드 작가들의 든든한 선배이자 다정한 동료 '모그 AI'. 규칙: 엄마의 고민에 깊이 공감해주고, 실질적인 도움(이름 짓기, 답장 문구 등)을 줄 것. 마무리: 항상 작가님의 활동을 진심으로 응원하는 따뜻한 격려 멘트 필수."

    if feedback:
        u_content = f"작가님, 방금 쓴 글이 이거예요: '{user_in}' \n\n 그런데 엄마가 이렇게 수정을 요청하셨어요: '{feedback}' \n\n 이 내용을 반영해서 다시 다정하게 고쳐주셔요🌸"
    else:
        info = f"작품명:{st.session_state.get('m_name')}, 소재:{st.session_state.get('m_mat')}, 기간:{st.session_state.get('m_per')}, 대상:{st.session_state.get('m_tar')}, 상세:{st.session_state.get('m_det')}"
        u_content = f"정보: {info} / {user_in}"

    res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":system_p},{"role":"user","content":u_content}])
    
    # 💡 따님의 팁 적용
    response_text = res.choices[0].message.content
    return response_text.replace("**", "").replace("*", "").strip()

# --- 3. 메인 화면 ---
st.title("🌸 모그 작가님 AI 비서 🌸")
st.header("1️⃣ 작품 정보를 입력해주세요")

c1, c2 = st.columns(2)
with c1:
    st.session_state.m_name = st.text_input("📦 작품 이름", value=st.session_state.get('m_name', ""))
    st.session_state.m_mat = st.text_input("🧵 소재", value=st.session_state.get('m_mat', ""))
with c2:
    st.session_state.m_per = st.text_input("⏳ 제작 기간", value=st.session_state.get('m_per', ""))
    st.session_state.m_tar = st.text_input("🎁 추천 대상", value=st.session_state.get('m_tar', ""))
st.session_state.m_det = st.text_area("✨ 정성 포인트와 설명", value=st.session_state.get('m_det', ""), height=150)

if st.button("💾 이 작품 정보 창고에 저장하기"):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=SHEET_URL, ttl=0)
        new_row = pd.DataFrame([{"name":st.session_state.m_name, "material":st.session_state.m_mat, "period":st.session_state.m_per, "target":st.session_state.m_tar, "keys":st.session_state.m_det}])
        conn.update(spreadsheet=SHEET_URL, data=pd.concat([df, new_row], ignore_index=True))
        st.success("작가님, 창고에 예쁘게 저장해두었어요! 🌸")
    except: st.error("저장 중 오류 발생")

st.divider()

# --- 4. 기능 탭 ---
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 AI 자동 사진 보정", "💬 고민 상담소", "📂 작품 창고"])

with tabs[0]: # 판매글 쓰기 및 수정 요청 기능
    st.write("#### 💡 버튼을 눌러 글을 완성하고, 필요하면 수정을 요청하세요.")
    sc1, sc2, sc3 = st.columns(3)
    if sc1.button("📸 인스타그램"): st.session_state.texts["인스타"] = ask_mog_ai("인스타그램")
    if sc2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스")
    if sc3.button("🛍️ 스토어"): st.session_state.texts["스토어"] = ask_mog_ai("스토어")
    
    for platform_key, result_text in st.session_state.texts.items():
        if result_text:
            st.markdown(f"### ✨ 완성된 {platform_key} 글")
            # 엄마가 보기 편하게 출력
            st.text_area(f"{platform_key} 결과", value=result_text, height=350, key=f"area_{platform_key}")
            
            # [수정 요청 섹션]
            with st.expander(f"✍️ {platform_key} 글 수정 요청하기"):
                feedback_input = st.text_input("수정하고 싶은 내용을 말씀해주세요 (예: 좀 더 다정하게 써줘)", key=f"feed_{platform_key}")
                if st.button(f"🚀 {platform_key} 수정본 다시 만들기", key=f"btn_{platform_key}"):
                    with st.spinner("작가님의 요청을 반영 중이에요..."):
                        new_text = ask_mog_ai(platform_key, user_in=result_text, feedback=feedback_input)
                        st.session_state.texts[platform_key] = new_text
                        st.rerun()

with tabs[1]: # 📸 AI 자동 사진 보정
    st.header("📸 AI 자동 사진 보정")
    up_img = st.file_uploader("사진을 올려주시면 AI가 화사하게 만져드려요", type=["jpg", "png", "jpeg"])
    if up_img and st.button("✨ 보정 시작"):
        with st.spinner("우리 작품을 화사하게 만드는 중이에요..."):
            e_img, reason = ai_auto_enhance(up_img)
            c_l, c_r = st.columns(2)
            c_l.image(up_img, caption="보정 전")
            c_r.image(e_img, caption="보정 후")
            buf = io.BytesIO(); e_img.save(buf, format="JPEG")
            st.download_button("📥 저장", buf.getvalue(), "fixed.jpg", "image/jpeg")

with tabs[2]: # 💬 고민 상담소
    st.header("💬 작가님 고민 상담소")
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.write(m["content"])
    if pr := st.chat_input("작가님, 무엇이든 말씀하셔요..."):
        st.session_state.chat_log.append({"role": "user", "content": pr})
        st.session_state.chat_log.append({"role": "assistant", "content": ask_mog_ai("상담", user_in=pr)})
        st.rerun()

with tabs[3]: # 📂 작품 창고
    st.header("📂 나의 저장된 작품들")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=SHEET_URL, ttl=0)
        for i, r in df.iterrows():
            with st.expander(f"📦 {r['name']}"):
                if st.button("📥 불러오기", key=f"get_{i}"):
                    st.session_state.m_name, st.session_state.m_mat = r['name'], r['material']
                    st.session_state.m_per, st.session_state.m_tar = r['period'], r['target']
                    st.session_state.m_det = r['keys']
                    st.rerun()
    except: st.warning("창고 확인 중...")
