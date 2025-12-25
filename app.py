import streamlit as st
from rembg import remove
from PIL import Image
import io
import openai
import requests

# 1. 앱 페이지 설정
st.set_page_config(page_title="엄마의 프리미엄 AI 스튜디오", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #faf9f6; }
    h1 { color: #5d4037; text-align: center; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; font-size: 18px; background-color: #8d6e63; color: white; }
    </style>
    """, unsafe_allow_stdio=True)

st.title("🕯️ 엄마의 프리미엄 AI 스튜디오")
st.write("사진을 올리면 AI가 소품과 함께 자연스러운 연출샷을 만들어드려요.")

# 2. 사이드바 설정 (비밀번호 형식으로 API 키 입력)
st.sidebar.header("⚙️ 필수 설정")
api_key = st.sidebar.text_input("OpenAI API Key를 넣어주세요", type="password")
author_name = st.sidebar.text_input("작가 이름", value="엄마작가")

# 3. 연출 컨셉 선택 (보내주신 사진 느낌 반영)
st.header("📸 1. 연출 컨셉 선택")
bg_concept = st.selectbox("어떤 분위기에서 찍은 것처럼 만들까요?", [
    "포근한 베이지색 의자와 린넨 쿠션 (내추럴)",
    "따뜻한 원목 테이블과 라탄 매트 (홈카페)",
    "햇살 비치는 창가와 부드러운 화이트 커튼",
    "세련된 대리석 테이블과 향초 소품 (쇼룸)"
])

# 컨셉별 정교한 프롬프트 정의 (제품이 붕 뜨지 않게 'placed on' 강조)
concept_prompts = {
    "포근한 베이지색 의자와 린넨 쿠션 (내추럴)": "placed on a cozy beige fabric chair, leaning against a soft white linen cushion, natural balcony lighting, realistic contact shadows, organic textures",
    "따뜻한 원목 테이블과 라탄 매트 (홈카페)": "placed on a round rattan placemat on a wooden dining table, warm morning sun, cafe atmosphere, sharp focus on product, realistic shadows",
    "햇살 비치는 창가와 부드러운 화이트 커튼": "sitting on a clean white window sill, soft sheer curtains in background, cinematic sunlight, high-end lifestyle photography",
    "세련된 대리석 테이블과 향초 소품 (쇼룸)": "resting on a white marble table, next to a high-end scented candle, minimalist boutique interior, soft studio lighting"
}

st.divider()

# 4. 사진 업로드 및 처리
uploaded_file = st.file_uploader("보정할 작품 사진을 선택하세요", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # API 키 체크
    if not api_key:
        st.info("왼쪽 메뉴에 OpenAI API Key를 입력해주셔야 AI 기능이 작동합니다.")
        st.stop()
    
    openai.api_key = api_key
    
    # 원본 이미지 표시
    original_img = Image.open(uploaded_file)
    st.image(original_img, caption="엄마가 찍은 원본", width=350)

    if st.button("✨ AI 프리미엄 연출 시작"):
        with st.spinner("AI가 배경을 직접 설계하고 합성하는 중입니다..."):
            try:
                # [단계 1] 배경 제거
                input_bytes = uploaded_file.getvalue()
                subject_bytes = remove(input_bytes)
                subject_img = Image.open(io.BytesIO(subject_bytes)).convert("RGBA")
                
                # [단계 2] AI 배경 생성 (DALL-E 3)
                # 바닥면(surface)과 그림자(shadow)를 강력하게 요구함
                detail = concept_prompts[bg_concept]
                full_prompt = f"A professional product photography background, {detail}. 8k resolution, photorealistic, blurred background, spacious surface for a product to be placed on."
                
                response = openai.images.generate(
                    model="dall-e-3",
                    prompt=full_prompt,
                    size="1024x1024",
                    n=1
                )
                
                # 생성된 배경 가져오기
                bg_url = response.data[0].url
                bg_resp = requests.get(bg_url)
                background = Image.open(io.BytesIO(bg_resp.content)).convert("RGBA")
                
                # [단계 3] 제품 합성 (바닥에 닿는 느낌 조절)
                bg_w, bg_h = background.size
                # 제품을 적절한 크기로 리사이즈 (배경의 55% 수준)
                subject_img.thumbnail((bg_w * 0.55, bg_h * 0.55))
                
                # 합성 위치: 중앙 하단(바닥면)에 배치하여 붕 뜨지 않게 함
                paste_x = (bg_w - subject_img.width) // 2
                paste_y = (bg_h - subject_img.height) // 2 + 150 # 바닥 쪽에 가깝게 이동
                
                background.paste(subject_img, (paste_x, paste_y), subject_img)
                
                # [단계 4] 작가 이름표 추가
                from PIL import ImageDraw
                draw = ImageDraw.Draw(background)
                draw.text((bg_w - 350, bg_h - 80), f"Handmade by {author_name}", fill=(255, 255, 255, 120))
                
                final_result = background.convert("RGB")
                st.image(final_result, caption="완성된 프리미엄 연출샷", use_container_width=True)
                
                # 다운로드 버튼
                buf = io.BytesIO()
                final_result.save(buf, format="JPEG", quality=95)
                st.download_button("📥 완성 사진 저장하기", buf.getvalue(), "premium_result.jpg")
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")

st.divider()

# 5. 친절한 상세페이지 문구 (이전 로직 유지)
st.header("✍️ 2. 정성 가득한 설명 쓰기")
prod_name = st.text_input("작품 이름")
prod_desc = st.text_area("작품의 특징 (짧게)")

if st.button("🪄 친절한 문구 생성"):
    if prod_name and prod_desc:
        text = f"🌸 **[{prod_name}]**\n\n안녕하세요, **{author_name}** 작가입니다.\n{prod_desc}\n\n작가인 제가 직접 검수하여 정성껏 보내드립니다. 문의는 언제든 편하게 주세요! 😊"
        st.success("글이 완성되었습니다!")
        st.text_area("복사해서 사용하세요", value=text, height=200)
