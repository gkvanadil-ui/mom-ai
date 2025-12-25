import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import io

# 1. 앱 기본 설정 (에러 방지를 위해 간단하게 구성)
st.set_page_config(page_title="엄마의 명품 보정 도구")

st.title("✨ 작가님 전용 명품 보정 도구")
st.write("잡티는 지우고, 색감은 살리고! 사진의 품격을 높여드려요.")

st.divider()

# 2. 사진 업로드
uploaded_file = st.file_uploader("보정할 작품 사진을 선택하세요", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # 원본 이미지 로드
    img = Image.open(uploaded_file)
    
    st.subheader("🎨 보정 강도 조절")
    
    # 보정 컨트롤러
    smooth = st.slider("✨ 바탕 부드럽게 (잡티 완화)", 0, 5, 1)
    bright = st.slider("☀️ 밝기 (화사하게)", 0.5, 2.0, 1.1)
    sharp = st.slider("🔍 선명도 (디테일 강조)", 0.5, 3.0, 1.5)
    color = st.slider("🌈 색감 (생생하게)", 0.5, 2.0, 1.2)

    if st.button("🚀 보정 적용 및 결과 보기"):
        # 보정 프로세스
        # A. 밝기
        enhancer = ImageEnhance.Brightness(img)
        edited = enhancer.enhance(bright)
        
        # B. 채도
        enhancer = ImageEnhance.Color(edited)
        edited = enhancer.enhance(color)
        
        # C. 부드럽게 (잡티 제거 효과)
        for _ in range(smooth):
            edited = edited.filter(ImageFilter.SMOOTH_MORE)
            
        # D. 선명도
        enhancer = ImageEnhance.Sharpness(edited)
        edited = enhancer.enhance(sharp)
        
        # 결과 표시
        col1, col2 = st.columns(2)
        with col1:
            st.write("보정 전")
            st.image(img, use_container_width=True)
        with col2:
            st.write("보정 후")
            st.image(edited, use_container_width=True)
        
        # 저장 버튼
        buf = io.BytesIO()
        edited.save(buf, format="JPEG", quality=95)
        st.download_button(
            label="📥 보정된 사진 저장하기",
            data=buf.getvalue(),
            file_name="refined_photo.jpg",
            mime="image/jpeg"
        )

st.divider()

# 3. 간단한 상품 설명글 제작
st.header("✍️ 2. 정성 담긴 문구 만들기")
p_name = st.text_input("상품 이름")
p_msg = st.text_area("엄마의 한마디")

if st.button("🪄 문구 완성"):
    if p_name and p_msg:
        full_text = f"🌸 **[{p_name}]**\n\n{p_msg}\n\n정성을 다해 만들었습니다. 문의는 언제든 환영이에요! 😊"
        st.success("글이 완성되었습니다!")
        st.text_area("복사해서 사용하세요", value=full_text, height=150)
