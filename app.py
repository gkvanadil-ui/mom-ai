import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import io

# 1. 앱 페이지 설정
st.set_page_config(page_title="작가님을 위한 명품 보정 도구", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    h1 { color: #2c3e50; text-align: center; font-size: 35px !important; }
    .stButton>button { 
        width: 100%; border-radius: 12px; height: 3.5em; 
        background-color: #4a69bd; color: white; font-weight: bold;
    }
    .stSlider [data-baseweb="slider"] { margin-bottom: 25px; }
    </style>
    """, unsafe_allow_stdio=True)

st.title("✨ 작가님 전용 명품 보정 도구")
st.write("AI 생성 대신, 엄마가 찍은 소중한 사진을 더 선명하고 아름답게 고쳐드려요.")

st.divider()

# 2. 사진 업로드
uploaded_file = st.file_uploader("보정할 작품 사진을 선택하세요", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # 사진 불러오기
    img = Image.open(uploaded_file)
    
    # 원본과 보정본을 나란히 보여주기 위해 컬럼 나누기
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("원본 사진")
        st.image(img, use_container_width=True)

    # 3. 보정 컨트롤러 (사이드바 대신 직관적으로 화면에 배치)
    st.header("🎨 어떻게 보정할까요?")
    
    # 잡티 제거 느낌을 주는 부드러움 조절 (Smooth)
    smooth = st.slider("✨ 피부/바탕 부드럽게 (잡티 완화)", 0, 5, 0)
    # 화사함 조절 (Brightness)
    bright = st.slider("☀️ 사진 화사하게 (밝기)", 0.5, 2.0, 1.1)
    # 선명도 조절 (Sharpness)
    sharp = st.slider("🔍 디테일 선명하게", 0.5, 3.0, 1.5)
    # 색감 조절 (Color)
    color = st.slider("🌈 색감 생생하게 (채도)", 0.5, 2.0, 1.2)

    if st.button("🚀 보정 적용하기"):
        # 보정 로직 시작
        with st.spinner("사진을 예쁘게 고치는 중..."):
            # A. 밝기 보정
            enhancer = ImageEnhance.Brightness(img)
            edited = enhancer.enhance(bright)
            
            # B. 채도 보정 (색감)
            enhancer = ImageEnhance.Color(edited)
            edited = enhancer.enhance(color)
            
            # C. 잡티 완화 (부드러운 필터 적용)
            for _ in range(smooth):
                edited = edited.filter(ImageFilter.SMOOTH_MORE)
                
            # D. 선명도 보정
            enhancer = ImageEnhance.Sharpness(edited)
            edited = enhancer.enhance(sharp)
            
            with col2:
                st.subheader("보정 결과")
                st.image(edited, use_container_width=True)
            
            # 4. 저장 버튼
            buf = io.BytesIO()
            edited.save(buf, format="JPEG", quality=95)
            st.download_button(
                label="📥 보정된 명품 사진 저장하기",
                data=buf.getvalue(),
                file_name="refined_product.jpg",
                mime="image/jpeg"
            )

st.divider()

# 5. 상세페이지 글쓰기는 덤!
st.header("✍️ 2. 상품 설명글 만들기")
p_name = st.text_input("상품 이름")
p_heart = st.text_area("엄마의 정성 한마디")

if st.button("🪄 친절한 설명글 완성"):
    if p_name and p_heart:
        desc = f"🌸 **[{p_name}]**\n\n안녕하세요. 하나하나 손수 만드는 작가입니다.\n\n{p_heart}\n\n실물 느낌을 그대로 담기 위해 정성껏 보정했습니다. 궁금한 점은 톡톡 주세요!"
        st.success("글이 완성되었습니다!")
        st.text_area("결과", value=desc, height=200)
