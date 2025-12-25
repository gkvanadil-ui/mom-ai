import streamlit as st
from PIL import Image, ImageEnhance
import io
import openai
import base64
import json

# 1. 앱 페이지 설정
st.set_page_config(page_title="핸드메이드 잡화점 모그 AI 비서", layout="wide")

# --- API 키 설정 (Secrets 우선) ---
api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.sidebar.header("⚙️ AI 설정")
    api_key = st.sidebar.text_input("OpenAI API Key를 넣어주세요", type="password")
else:
    st.sidebar.success("✅ API 키가 자동으로 로드되었습니다.")

st.title("🕯️ 작가 '모그(Mog)' 전용 AI 통합 비서")
st.write("'세상에 단 하나뿐인 온기'를 전하는 모그 작가님의 진심을 담아드립니다.")

st.divider()

# --- 1. 사진 일괄 AI 지능형 보정 (기존 기능 유지) ---
st.header("📸 1. 사진 한 번에 보정하기")
uploaded_files = st.file_uploader("보정할 사진들을 선택하세요", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

if uploaded_files and api_key:
    if st.button("🚀 모든 사진 AI 보정 시작"):
        client = openai.OpenAI(api_key=api_key)
        cols = st.columns(len(uploaded_files))
        for idx, file in enumerate(uploaded_files):
            with st.spinner(f"{idx+1}번 사진 분석 중..."):
                img_bytes = file.getvalue()
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": [{"type": "text", "text": "화사하고 선명한 보정 수치 JSON."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(img_bytes)}"}}]}],
                        response_format={ "type": "json_object" }
                    )
                    res = json.loads(response.choices[0].message.content)
                    img = Image.open(io.BytesIO(img_bytes))
                    edited = ImageEnhance.Brightness(img).enhance(res.get('b', 1.1))
                    edited = ImageEnhance.Color(edited).enhance(res.get('c', 1.1))
                    edited = ImageEnhance.Sharpness(edited).enhance(res.get('s', 1.2))
                    with cols[idx]:
                        st.image(edited, use_container_width=True)
                        buf = io.BytesIO()
                        edited.save(buf, format="JPEG")
                        st.download_button(f"📥 저장 {idx+1}", buf.getvalue(), f"img_{idx+1}.jpg")
                except Exception as e:
                    st.error(f"사진 보정 중 오류 발생: {e}")

st.divider()

# --- 2. 매체별 맞춤형 상세 글 생성 섹션 ---
st.header("✍️ 2. 모그(Mog) 작가님의 진심이 담긴 글 작성")

col_in1, col_in2 = st.columns(2)
with col_in1:
    name = st.text_input("📦 작품 이름", placeholder="예: 앤과 숲속 푸우 패치워크 보스턴백")
    keys = st.text_area("🔑 핵심 특징/이야기", placeholder="예: 여행을 꿈꾸며 만든 야무진 백, 세상에 단 하나뿐인 패치워크")
    mat = st.text_input("🧵 원단/소재", placeholder="예: 유럽 햄프리넨, 오일 워싱 원단, 가죽 손잡이")
with col_in2:
    size = st.text_input("📏 사이즈/수납", placeholder="예: 높이 31 폭 42, 노트북 수납 가능, 뒷포켓 있음")
    process = st.text_area("🛠️ 제작 포인트", placeholder="예: 손바느질 스티치, 리넨 파우치 증정, 모그 스타일 장식")
    care = st.text_input("💡 배송/포장", placeholder="예: 별도 요청 없어도 선물용으로 정성껏 포장")

tab1, tab2, tab3 = st.tabs(["📸 인스타그램", "🎨 아이디어스", "🛍️ 스마트스토어"])

def generate_text(platform_type, specific_prompt):
    if not api_key:
        st.warning("API 키가 필요합니다.")
        return None
    if not name:
        st.warning("이름을 입력해주세요.")
        return None

    client = openai.OpenAI(api_key=api_key)
    full_prompt = f"""
    당신은 브랜드 '모그(Mog)'의 작가 본인입니다. 직접 고객에게 건네는 말투로 [{platform_type}] 판매글을 작성하세요.

    [핵심 어투 지침]
    - 말투: 밝고 다정하며 정감이 가는 어른스러운 말투를 사용하세요. (예: ~이지요^^, ~했답니다, ~좋아요)
    - 주의: 'ok👭' 같은 특정 예시 문구를 그대로 반복하지 마세요. 상황에 맞는 자연스러운 이모지를 사용하세요.
    - 본인을 '모그'라고 지칭하고, 제작 과정의 즐거움과 원단의 퀄리티를 강조하세요.

    [출력 형식 지침]
    - 강조를 위한 별표 기호(**)를 절대 사용하지 마세요. 굵은 글씨 금지입니다.
    - 본인을 카피라이터나 AI라고 소개하는 서론을 절대 넣지 마세요. 바로 본론(인사말)으로 시작하세요.
    - 복사해서 바로 붙여넣을 수 있는 깨끗한 일반 텍스트로만 답변하세요.

    [데이터 정보] 제품명: {name} / 특징: {keys} / 소재: {mat} / 사이즈: {size} / 제작진심: {process} / 포장: {care}

    {specific_prompt}
    """
    
    with st.spinner(f"작가 '모그'의 목소리로 작성 중..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": full_prompt}]
            )
            # 1. 별표(**) 제거, 2. AI의 불필요한 서론 제거 로직
            clean_text = response.choices[0].message.content.replace("**", "")
            return clean_text.strip()
        except Exception as e:
            st.error(f"오류 발생: {e}")
            return None

with tab1:
    st.subheader("인스타그램 스타일 (깔끔&감성)")
    if st.button("🪄 인스타용 글 만들기"):
        instr = "작가로서 가벼운 일상 인사를 건네며 시작하세요. 너무 길지 않게 요약하고, 매력 포인트를 해시태그와 섞어주세요. 특정 예시 문구(ok 등)를 그대로 쓰지 말고 작가님만의 감성으로 새로 쓰세요."
        result = generate_text("인스타그램", instr)
        if result:
            st.text_area("인스타 결과", value=result, height=400)

with tab2:
    st.subheader("아이디어스 스타일 (한 줄씩 정성 상세글)")
    if st.button("🪄 아이디어스용 글 만들기"):
        instr = """
        - 모든 문장이 끝나면 반드시 줄바꿈을 하여 '한 줄에 한 문장'만 나오게 하세요.
        - 문단 사이에는 빈 줄을 넣어 여유 있게 구성하세요.
        - 작가님의 제작 스토리와 정성을 다정하게 풀어내세요. 특정 예시 단어를 반복하지 마세요.
        """
        result = generate_text("아이디어스", instr)
        if result:
            st.text_area("아이디어스 결과", value=result, height=600)

with tab3:
    st.subheader("스마트스토어 스타일 (상세 정보 가이드)")
    if st.button("🪄 스마트스토어용 글 만들기"):
        instr = "구분선(⸻)과 불렛 포인트를 사용하세요. 작가로서 정보를 상세하고 친절하게 정리하세요. 제목에 별표 사용은 금지입니다."
        result = generate_text("스마트스토어", instr)
        if result:
            st.text_area("스토어 결과", value=result, height=700)
