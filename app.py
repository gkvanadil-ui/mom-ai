import streamlit as st
from PIL import Image, ImageEnhance
import io
import openai
import base64
import json

# 1. 앱 페이지 설정
st.set_page_config(page_title="사랑하는 엄마, 모그의 AI 명품 비서", layout="wide")

# 사이드바 API 설정
st.sidebar.header("⚙️ AI 설정")
api_key = st.sidebar.text_input("OpenAI API Key를 넣어주세요", type="password")

st.title("🕯️ 사랑하는 엄마, 모그 작가님을 위한 AI 통합 비서")
st.write("사진 보정부터 매체별(인스타/아이디어스/스토어) 맞춤 글쓰기까지 한 번에!")

st.divider()

# --- 1. 사진 일괄 AI 지능형 보정 ---
st.header("📸 1. 사진 한 번에 보정하기")
uploaded_files = st.file_uploader("보정할 사진들을 선택하세요 (최대 10장)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

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
                    messages=[{"role": "user", "content": [{"type": "text", "text": "화사하고 선명한 보정 수치 JSON으로 줘. 예: {'b': 1.2, 'c': 1.1, 's': 1.3}"},
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

# --- 2. 매체별 맞춤형 글 생성 섹션 ---
st.header("✍️ 2. 매체별 맞춤 글 만들기")
st.write("아래 빈칸을 채우고, 원하는 매체 탭을 눌러 글을 생성해 보세요!")

# 입력 영역
col_in1, col_in2 = st.columns(2)
with col_in1:
    name = st.text_input("📦 작품 이름", placeholder="예: 뜨왈 스트링 파우치")
    keys = st.text_area("🔑 핵심 특징/감성", placeholder="예: 가을을 기다리며 만든 셔츠, 부드러운 촉감")
    mat = st.text_input("🧵 원단/소재", placeholder="예: 수입 리넨, 텐셜 레이온")
with col_in2:
    size = st.text_input("📏 사이즈/디테일", placeholder="예: 28*30, 수놓은 꽃모양")
    process = st.text_area("🛠️ 제작 포인트/진심", placeholder="예: 하나하나 들어간 정성은 일정해요")
    care = st.text_input("💡 주의사항", placeholder="예: 리넨 특성상 표면 돌출은 불량이 아닙니다")

# 매체별 탭 생성
tab1, tab2, tab3 = st.tabs(["📸 인스타그램", "🎨 아이디어스", "🛍️ 스마트스토어"])

def generate_text(platform_type, specific_prompt):
    if not api_key:
        st.warning("사이드바에 API 키를 입력해주세요.")
        return
    if not name:
        st.warning("작품 이름을 입력해주세요.")
        return

    client = openai.OpenAI(api_key=api_key)
    
    full_prompt = f"""
    당신은 핸드메이드 작가님의 판매를 돕는 전문 카피라이터입니다. 
    엄마 작가님의 진심이 전달되도록 [{platform_type}] 전용 판매글을 작성하세요.

    [공통 지침]
    - 과한 미사여구는 자제하고 판매자의 진심이 느껴지는 따뜻한 어투를 사용할 것.
    - 문단을 가독성 좋게 나누고 짧게 끊어서 작성할 것.
    - 맞춤법을 완벽하게 검수할 것.

    [데이터 정보]
    작품명: {name} / 특징: {keys} / 소재: {mat} / 사이즈: {size} / 제작진심: {process} / 주의사항: {care}

    {specific_prompt}
    """
    
    with st.spinner(f"{platform_type} 스타일에 맞춰 정성을 담는 중..."):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": full_prompt}]
        )
        return response.choices[0].message.content

with tab1:
    st.subheader("인스타그램 스타일")
    st.write("감성적이고 소통 중심인 경쾌한 어투")
    if st.button("🪄 인스타용 글 만들기"):
        instr = """
        - 어투: 문장 중간에 #해시태그를 섞고, '~이지요?', '^^', 'ㅠㅠ' 같은 친근한 표현 사용.
        - 구성: 감성적인 도입부(날씨/기분) -> 작품의 촉감과 느낌 -> 상세 정보 -> 하단 해시태그 모음.
        - 포인트: 이모지를 적절히 활용해 작가님의 개성을 드러낼 것.
        """
        result = generate_text("인스타그램", instr)
        st.text_area("인스타용 완성글", value=result, height=450)

with tab2:
    st.subheader("아이디어스 스타일")
    st.write("작가님의 정성과 제작 스토리가 담긴 따뜻한 어투")
    if st.button("🪄 아이디어스용 글 만들기"):
        instr = """
        - 어투: 정중하고 다정한 어투. 작품의 쓰임새와 가치를 강조.
        - 구성: 제작 동기 -> 원단의 특별함 -> 사용자를 향한 배려와 정성 -> 끝인사.
        - 포인트: "모양이 잡혀서 좋지요👍" 처럼 작가의 경험과 정성을 강조할 것.
        """
        result = generate_text("아이디어스", instr)
        st.text_area("아이디어스용 완성글", value=result, height=450)

with tab3:
    st.subheader("스마트스토어 스타일")
    st.write("정확한 정보와 가독성을 중시하는 깔끔한 어투")
    if st.button("🪄 스마트스토어용 글 만들기"):
        instr = """
        - 어투: 군더더기 없이 깔끔하고 신뢰감을 주는 어투. 
        - 구성: [상품 요약] -> [상세 특징] -> [소재 및 규격] -> [관리 안내].
        - 포인트: 불렛 포인트(•)를 적극 활용하여 구매자가 정보를 한눈에 보게 할 것. 
        """
        result = generate_text("스마트스토어", instr)
        st.text_area("스마트스토어용 완성글", value=result, height=450)
