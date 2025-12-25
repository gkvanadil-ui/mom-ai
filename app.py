import streamlit as st
import pandas as pd
from PIL import Image, ImageEnhance, ImageOps
import io
import openai
import base64
import json

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="centered")

# --- CSS: 다크모드 대응 및 시각적 요소 ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { color: inherit; }
    h1, h2, h3 { color: #D4A373 !important; font-weight: bold !important; }
    p, li, label, .stMarkdown { font-size: 18px !important; line-height: 1.6; }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5em;
        background-color: #7d6e63; color: white !important;
        font-weight: bold; font-size: 18px !important;
        border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .stTextInput input, .stTextArea textarea { font-size: 16px !important; }
    hr { border-top: 2px solid #7d6e63; opacity: 0.3; }
    </style>
    """, unsafe_allow_html=True)

# --- API 키 설정 ---
api_key = st.secrets.get("OPENAI_API_KEY")

st.title("🕯️ 모그(Mog) 작가 전용 비서")
st.write("<p style='text-align: center;'>AI가 사진을 분석하고 작가님의 어투로 글을 써드립니다🌸</p>", unsafe_allow_html=True)

# --- [1단계: 작품 정보 입력] ---
st.header("1️⃣ 작품 정보 입력")
with st.expander("📝 이곳을 터치해서 내용을 채워주세요", expanded=True):
    name = st.text_input("📦 작품 이름", placeholder="예: 빈티지 튤립 뜨개 파우치")
    col1, col2 = st.columns(2)
    with col1:
        mat = st.text_input("🧵 소재", placeholder="예: 코튼 100%")
        size = st.text_input("📏 크기", placeholder="예: 20*15cm")
    with col2:
        period = st.text_input("⏳ 제작 기간", placeholder="예: 주문 후 3일")
        care = st.text_input("💡 세탁법", placeholder="예: 미온수 손세탁")
    keys = st.text_area("🔑 작품 특징", placeholder="예: 색감이 화사해서 포인트로 좋아요.")
    process = st.text_area("🛠️ 제작 포인트", placeholder="예: 안감까지 꼼꼼히 제작했습니다.")

st.divider()

# --- [2단계: 작업실 선택] ---
st.header("2️⃣ 작업실 선택")
tabs = st.tabs(["✍️ 글쓰기", "📸 AI 자율 보정", "💡 홍보 꿀팁"])

# --- AI 처리 함수 ---
def process_ai_text(full_prompt):
    if not api_key: return None
    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": full_prompt}])
        return response.choices[0].message.content.replace("**", "").strip()
    except: return None

# --- [Tab 1: 글쓰기 - 어투 복구 버전] ---
with tabs[0]:
    if 'generated_texts' not in st.session_state:
        st.session_state.generated_texts = {"인스타그램": "", "아이디어스": "", "스마트스토어": ""}
    
    st.write("💡 아래 버튼을 누르면 모그 작가님 말투로 글이 써집니다.")
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("📸 인스타"): platform = "인스타그램"
    with c2: 
        if st.button("🎨 아디스"): platform = "아이디어스"
    with c3: 
        if st.button("🛍️ 스토어"): platform = "스마트스토어"

    if 'platform' in locals():
        platform_guides = {
            "인스타그램": "해시태그 포함, 계절 인사와 함께하는 감성 일기 스타일.",
            "아이디어스": "짧은 문장 위주, 줄바꿈 매우 자주, 꽃과 하트 이모지를 풍성하게 사용.",
            "스마트스토어": "구분선(⸻)을 활용한 가독성 강조, 카테고리별 정보 정리."
        }
        full_prompt = f"""당신은 핸드메이드 브랜드 '모그(Mog)' 작가입니다. [{platform}] 판매글을 작성하세요.
        말투: 다정한 엄마/작가 말투 (~이지요^^, ~해요, ~좋아요). 별표(*) 사용 금지. 이모지(🌸,✨) 활용.
        지침: {platform_guides[platform]}
        정보: 이름:{name}, 특징:{keys}, 소재:{mat}, 사이즈:{size}, 제작:{process}, 관리:{care}, 기간:{period}"""
        st.session_state.generated_texts[platform] = process_ai_text(full_prompt)

    for p in ["인스타그램", "아이디어스", "스마트스토어"]:
        if st.session_state.generated_texts.get(p):
            st.subheader(f"✅ {p} 결과")
            txt = st.text_area(f"{p} 결과", value=st.session_state.generated_texts[p], height=350, key=f"area_{p}")

# --- [Tab 2: AI 자율 보정] ---
with tabs[1]:
    st.subheader("📸 AI 자율 분석 보정")
    st.write("AI가 사진의 밝기, 색감, 그림자를 분석하여 '가장 깔끔한 상태'로 보정합니다.")
    
    uploaded_files = st.file_uploader("보정할 사진 선택", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_files and api_key and st.button("🚀 AI 분석 및 보정 시작"):
        def encode_image(image_bytes): return base64.b64encode(image_bytes).decode('utf-8')
        client = openai.OpenAI(api_key=api_key)
        
        for idx, file in enumerate(uploaded_files):
            img_bytes = file.getvalue()
            try:
                # [자율 분석 프롬프트]
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": """이 사진은 핸드메이드 제품 사진입니다. 사진을 분석하여 다음 수치를 JSON으로 보내주세요:
                        - 'brightness': 전체적으로 어두우면 1.1~1.3, 너무 밝으면 0.9, 적당하면 1.0
                        - 'contrast': 흐릿하면 1.1~1.2, 너무 강하면 0.9, 적당하면 1.0
                        - 'color': 색감이 창백하면 1.1~1.2, 너무 진하면 0.9, 따스한 느낌이 필요하면 1.1
                        - 'sharpness': 초점이 약간 흐리다면 1.5~2.0, 선명하면 1.0
                        형식: {"b": 수치, "c": 수치, "s": 수치, "sh": 수치}"""},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(img_bytes)}"}}
                    ]}],
                    response_format={ "type": "json_object" }
                )
                res = json.loads(response.choices[0].message.content)
                img = Image.open(io.BytesIO(img_bytes))
                img = ImageOps.exif_transpose(img) # 사진 방향 자동 회전 방지
                
                # 분석 결과에 따른 보정 적용
                img = ImageEnhance.Brightness(img).enhance(res.get('b', 1.0))
                img = ImageEnhance.Contrast(img).enhance(res.get('c', 1.0))
                img = ImageEnhance.Color(img).enhance(res.get('s', 1.0))
                img = ImageEnhance.Sharpness(img).enhance(res.get('sh', 1.0))
                
                st.image(img, caption=f"AI 분석 보정 완료 {idx+1}")
                buf = io.BytesIO(); img.save(buf, format="JPEG")
                st.download_button(f"📥 보정된 {idx+1}번 사진 저장", buf.getvalue(), f"img_{idx+1}.jpg")
            except: st.error(f"{idx+1}번 사진 분석 중 오류가 발생했어요.")

# --- [Tab 3: 홍보 꿀팁] ---
with tabs[2]:
    st.subheader("🎨 상세페이지 & 영상 팁")
    if st.button("🪄 캔바용 상세페이지 기획안 만들기"):
        if not name: st.warning("정보를 먼저 입력해 주셔요🌸")
        else:
            client = openai.OpenAI(api_key=api_key)
            prompt = f"모그 작가로서 {name} 상세페이지 5장 기획 JSON."
            res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], response_format={"type":"json_object"})
            data = json.loads(res.choices[0].message.content)
            df = pd.DataFrame(data[list(data.keys())[0]])
            for index, row in df.iterrows():
                with st.expander(f"📍 {row['순서']}번 화면 내용"):
                    st.write(f"**제목:** {row['메인문구']}\n\n**설명:** {row['설명']}")
                    st.caption(f"📸 촬영 팁: {row['사진구도']}")
    
    st.divider()
    st.subheader("🎥 에픽(EPIK) 영상 가이드")
    st.info("에픽 앱 실행 -> [템플릿] 검색 -> 사진 넣기 -> 저장! 🌸")
