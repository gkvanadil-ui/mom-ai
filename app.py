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

# --- [로직 2: 모그 작가님 전용 글쓰기 엔진 (아이디어스 포맷 고정)] ---
def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    
    base_style = """
    [절대 규칙: 1인칭 작가 시점]
    - 당신은 핸드메이드 작가 '모그(Mog)' 본인입니다.
    - AI 비서 같은 멘트("작가님의 글입니다" 등)는 절대 금지합니다.
    - 모든 문장은 "내가", "나의" 등 작가 본인이 직접 쓰는 일기/에세이 형식입니다.
    - 특수기호 금지: 볼드(**)나 별표(*) 기호는 절대 사용하지 마세요.
    """
    
    if platform == "인스타그램":
        system_p = f"{base_style} [📸 인스타그램] 지침: 감성 인사, 제작 일기, 작품 정보, 해시태그 10개 내외."
    elif platform == "아이디어스":
        system_p = f"{base_style} [🎨 아이디어스 신규 포맷] 지침: 아래 형식을 엄격히 준수하여 아주 상세하게 작성하세요.
        
        1. 인사: 안녕하세요. 모그입니다. (다정한 첫 인사)
        2. 소개: 오늘은 [작품명]을 소개해드려요. (감성적인 제작 동기와 마음 서술)
        3. 구분선: ☘🌱🌿🌳🌴🌵🍃🌱 (이모티콘 한 줄)
        4. 특징 서술: 소재의 조화, 내추럴함, 튼튼한 바느질 등 작가님의 정성 강조 ("세탁기 쌩쌩 돌리셔도 말짱해요" 등 구어체 사용)
        5. 💡 상세설명 섹션: 상품명, 구성, 사이즈, 소재 기재
        6. 🍀 Add info. 섹션: 사용 편의성(지퍼 등), 피부 친화적 특징 등 상세 서술
        7. 🔉 안내 섹션: 주문 제작 기간(2~14일), 취소/환불 규정 안내
        8. 👍🏻 작가보증: 모그에서 직접 디자인, 제작, 검수, 출고함을 강조하며 다정하게 마무리."
        
    elif platform == "스마트스토어":
        system_p = f"{base_style} [🛍️ 스마트스토어] 지침: 💐상품명, 🌸디자인&특징, 👜기능성, 📏사이즈, 📦소재, 🧼관리방법, 📍추천대상 순서로 상세히 작성."
    
    elif platform == "상담":
        system_p = f"{base_style} [💬 상담소] 든든한 선배 작가가 되어 동료의 고민에 공감하고 조언해주세요."

    if feedback:
        u_content = f"기존 글: {user_in}\n\n나의 수정 요청: {feedback}\n\n반영해서 더 길고 다정하게 다시 써주셔요🌸"
    else:
        info = f"작품명:{st.session_state.m_name}, 소재:{st.session_state.m_mat}, 사이즈:{st.session_state.m_size}, 나의 정성:{st.session_state.m_det}"
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
            feed = st.text_input(f"✍️ {k} 글 수정 요청사항", key=f"feed_{k}")
            if st.button(f"🚀 {k} 수정본 만들기", key=f"btn_{k}"):
                st.session_state.texts[k] = ask_mog_ai(k, user_in=v, feedback=feed)
                st.rerun()

with tabs[1]: 
    st.header("📸 AI 자동 사진 보정")
    up_img = st.file_uploader("사진을 올려주세요 🌸", type=["jpg", "png", "jpeg"])
    if up_img and st.button("✨ 보정 시작"):
        e_img = ai_auto_enhance(up_img)
        st.image(e_img, caption="AI 보정 결과")
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
