import streamlit as st
import openai
from PIL import Image, ImageEnhance
import io
import base64

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- ✨ UI 스타일: 엄마를 위한 다정하고 큼직한 디자인 ---
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

# 세션 상태 초기화
for key in ['texts', 'chat_log', 'm_name', 'm_mat', 'm_per', 'm_size', 'm_det']:
    if key not in st.session_state:
        if key == 'texts': st.session_state[key] = {"인스타": "", "아이디어스": "", "스토어": ""}
        elif key == 'chat_log': st.session_state[key] = []
        else: st.session_state[key] = ""

# --- [로직 1: AI 자동 사진 보정 엔진] ---
def ai_auto_enhance(img_file):
    client = openai.OpenAI(api_key=api_key)
    img = Image.open(img_file)
    img = ImageEnhance.Brightness(img).enhance(1.3)
    img = ImageEnhance.Contrast(img).enhance(1.1)
    img = ImageEnhance.Color(img).enhance(1.2)
    return img

# --- [로직 2: 모그 작가님 전용 글쓰기 엔진 (자율성 변주 적용)] ---
def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    
    base_style = """
    [절대 규칙: 1인칭 작가 시점 및 자율성]
    - 당신은 핸드메이드 작가 '모그(Mog)' 본인입니다. AI 비서 티를 절대 내지 마세요.
    - 모든 글은 작가 본인의 1인칭 에세이/일기 시점으로 작성합니다.
    - 아래 제시된 각 플랫폼의 '기본 포맷'과 '필수 섹션'은 반드시 유지하되, 내부의 문장 표현과 전개 방식에는 자율성을 발휘하여 작품마다 고유한 감성이 느껴지도록 다채롭게 변주하세요.
    - 특수기호 금지: 볼드(**)나 별표(*)는 사용하지 마세요.
    - 말투: 50대 여성 작가의 다정하고 따뜻한 어투 (~이지요^^, ~해요).
    """
    
    if platform == "인스타그램":
        system_p = f"""{base_style} 
        [📸 인스타그램] 감성 인사로 시작해 제작 과정의 소회를 밝히고 작품 정보를 자연스럽게 녹여주세요. 해시태그 10개 내외."""
    
    elif platform == "아이디어스":
        system_p = f"""{base_style} 
        [🎨 아이디어스 자율 에세이 모드] 기본 포맷을 지키되 작가님의 진심이 담긴 이야기를 아주 풍성하게 들려주세요.
        1. 인사 및 소개: "안녕하세요. 모그입니다."로 시작하여 작품을 만든 계기를 다정하게 서술.
        2. 구분선: ☘🌱🌿🌳🌴🌵🍃🌱
        3. 정성 서술: 제작 과정에서의 고민과 손맛을 에세이처럼 길게 작성.
        4. 💡 상세설명 섹션 (필수 항목: 상품명, 구성, 사이즈, 소재)
        5. 🍀 Add info. 섹션 (필수 항목: 사용 팁, 소재의 장점 등)
        6. 🔉 안내 섹션 (필수 항목: 제작 기간 2~14일, 취소/환불 규정)
        7. 👍🏻 작가보증: 직접 제작 및 검수함을 강조하며 마무리."""
        
    elif platform == "스마트스토어":
        system_p = f"""{base_style} 
        [🛍️ 스마트스토어 자율 상세 모드] 기본 양식을 뼈대로 하되, 각 섹션의 내용을 딱딱하지 않게 풍성하게 채워주세요.
        💐 [상품명]
        ⸻
        [작가 본인의 감성이 담긴 첫인사 및 작품 소개글]
        ⸻
        🌸 디자인 & 특징 (정성이 깃든 디자인 포인트를 상세히)
        👜 기능성 & 내구성 (튼튼함과 사용 편의성을 다정하게 설명)
        📏 사이즈 (±1~2cm 오차 안내 포함)
        📦 소재 (작가님이 고심해서 고른 소재 이야기)
        🧼 관리 방법 (작가님이 알려주는 오래 쓰는 팁)
        ⸻
        📍 이런 분께 추천 (작품이 필요할 것 같은 분들을 다정하게 제안)
        ⸻
        #[해시태그]"""
    
    elif platform == "상담":
        system_p = f"""{base_style} 
        [💬 상담소] 든든한 선배 작가가 되어 동료 작가의 고민에 진심으로 공감하고 따뜻한 조언을 건네주세요."""

    if feedback:
        u_content = f"기존 글: {user_in}\n\n수정 요청: {feedback}\n\n위 요청을 반영하여 작가님의 감성을 담아 다시 고쳐주셔요🌸"
    else:
        info = f"작품명:{st.session_state.m_name}, 소재:{st.session_state.m_mat}, 사이즈:{st.session_state.m_size}, 정성 포인트:{st.session_state.m_det}"
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

st.divider()

# --- 4. 기능 탭 ---
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 AI 자동 사진 보정", "💬 고민 상담소"])

with tabs[0]: 
    sc1, sc2, sc3 = st.columns(3)
    if sc1.button("📸 인스타그램"): st.session_state.texts["인스타"] = ask_mog_ai("인스타그램")
    if sc2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스")
    if sc3.button("🛍️ 스마트스토어"): st.session_state.texts["스토어"] = ask_mog_ai("스마트스토어")
    
    for k, v in st.session_state.texts.items():
        if v:
            st.markdown(f"### ✨ 완성된 {k} 글")
            st.text_area(f"{k} 결과", value=v, height=600, key=f"area_{k}")
            feed = st.text_input(f"✍️ {k} 글에서 수정하고 싶은 부분이 있으신가요?", key=f"feed_{k}")
            if st.button(f"🚀 {k} 글 다시 수정하기", key=f"btn_{k}"):
                with st.spinner("작가님의 마음을 담아 다시 고치는 중이에요..."):
                    st.session_state.texts[k] = ask_mog_ai(k, user_in=v, feedback=feed)
                    st.rerun()

with tabs[1]: 
    st.header("📸 AI 자동 사진 보정")
    up_img = st.file_uploader("사진을 올려주시면 AI가 화사하게 직접 보정해드릴게요 🌸", type=["jpg", "png", "jpeg"])
    if up_img and st.button("✨ 보정 시작하기"):
        e_img = ai_auto_enhance(up_img)
        col1, col2 = st.columns(2)
        col1.image(up_img, caption="보정 전")
        col2.image(e_img, caption="AI 보정 결과")
        buf = io.BytesIO(); e_img.save(buf, format="JPEG")
        st.download_button("📥 저장", buf.getvalue(), "mogs_fixed.jpg", "image/jpeg")

with tabs[2]: 
    st.header("💬 작가님 고민 상담소")
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.write(m["content"])
    if pr := st.chat_input("작가님, 무엇이든 말씀하셔요..."):
        st.session_state.chat_log.append({"role": "user", "content": pr})
        st.session_state.chat_log.append({"role": "assistant", "content": ask_mog_ai("상담", user_in=pr)})
        st.rerun()
