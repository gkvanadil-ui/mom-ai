import streamlit as st
from PIL import Image, ImageEnhance
import io
import openai
import base64
import json

# 1. 앱 페이지 설정
st.set_page_config(page_title="핸드메이드 잡화점 모그 AI 비서", layout="wide")

# 사이드바 API 설정
st.sidebar.header("⚙️ AI 설정")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")

st.title("🕯️ 작가 '모그(Mog)' 전용 AI 통합 비서")
st.write("'세상에 단 하나뿐인 온기'를 전하는 모그 작가님의 철학을 문장에 담아드립니다.")

st.divider()

# --- 1. 사진 일괄 AI 지능형 보정 ---
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
        st.warning("API 키를 넣어주세요.")
        return None
    if not name:
        st.warning("이름을 입력해주세요.")
        return None

    client = openai.OpenAI(api_key=api_key)
    full_prompt = f"""
    당신은 브랜드 '모그(Mog)'의 전담 카피라이터입니다. 
    작가 '모그'님의 철학이 드러나도록 [{platform_type}] 판매글을 아주 상세하고 길게 작성하세요.

    [모그 작가님의 브랜드 철학 및 어투]
    1. 희소성: "같은 디자인은 다시 만들지 않습니다. 세상에 단 하나뿐인 작품입니다."
    2. 손맛: "일정하지 않은 스티치와 바느질 자국에서 느껴지는 손작업만의 온기."
    3. 실용성: "뒷포켓의 편리함, 안감 처리된 튼튼한 파우치, 야무진 수납" 포인트 강조.
    4. 포장: "모든 배송은 소중한 친구에게 선물하는 마음으로 정성껏 포장합니다."
    5. 어투: "~이지요^^", "~만들어봤어요", "ok👭", "좋아요🌻" 처럼 밝고 다정한 말투.

    [데이터 정보]
    제품명: {name} / 특징: {keys} / 소재: {mat} / 사이즈: {size} / 제작진심: {process} / 포장: {care}

    {specific_prompt}
    """
    
    with st.spinner(f"작가 '모그'의 진심을 담아 작성 중..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": full_prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
            return None

with tab1:
    st.subheader("인스타그램 스타일")
    if st.button("🪄 인스타용 글 만들기"):
        instr = "감성적인 도입부, 문장 중간의 해시태그, 다정한 말투를 섞어 상세히 써주세요."
        result = generate_text("인스타그램", instr)
        if result:
            st.text_area("인스타 결과", value=result, height=550)

with tab2:
    st.subheader("아이디어스 스타일")
    if st.button("🪄 아이디어스용 글 만들기"):
        instr = "작가님의 제작 스토리와 샘플 어투(ok👭, 좋아요🌻)를 듬뿍 넣어 아주 정성스럽게 길게 써주세요."
        result = generate_text("아이디어스", instr)
        if result:
            st.text_area("아이디어스 결과", value=result, height=600)

with tab3:
    st.subheader("스마트스토어 스타일")
    if st.button("🪄 스마트스토어용 글 만들기"):
        instr = "구분선(⸻)과 불렛 포인트를 사용하고, 샘플처럼 정보(사이즈, 관리법 등)를 매우 상세하고 친절하게 정리하세요."
        result = generate_text("스마트스토어", instr)
        if result:
            st.text_area("스토어 결과", value=result, height=700)
