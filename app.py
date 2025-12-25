import streamlit as st
from rembg import remove
from PIL import Image
import io

# 설정 및 제목
st.set_page_config(page_title="엄마의 프리미엄 AI 비서")
st.title("🕯️ 엄마를 위한 프리미엄 AI 비서")
st.write("사진은 고급스럽게, 글은 정성스럽게!")

st.divider()

# --- 1단계: 고급 설정샷 만들기 ---
st.header("📸 1. 사진을 고급스럽게 변형")
uploaded_file = st.file_uploader("작품 사진을 선택하세요", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="원본 사진", width=300)
    
    if st.button("✨ 프리미엄 스튜디오 배경 입히기"):
        with st.spinner("고급 배경을 입히는 중..."):
            # 배경 제거
            input_bytes = uploaded_file.getvalue()
            output_bytes = remove(input_bytes)
            subject = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
            
            # 고급스러운 베이지톤 배경지 만들기
            # (따뜻한 감성을 주는 색상으로 설정했습니다)
            bg_color = (242, 235, 225) 
            canvas = Image.new("RGBA", subject.size, bg_color)
            canvas.paste(subject, (0, 0), subject)
            final_img = canvas.convert("RGB")
            
            st.image(final_img, caption="완성된 고급 설정샷", width=400)
            
            # 저장 버튼
            buf = io.BytesIO()
            final_img.save(buf, format="JPEG", quality=95)
            st.download_button("📥 보정 사진 저장하기", buf.getvalue(), "premium_photo.jpg")

st.divider()

# --- 2단계: 친절한 상품 설명 ---
st.header("✍️ 2. 정성 가득한 설명 쓰기")
name = st.text_input("제품 이름")
detail = st.text_area("엄마의 정성 (짧게 써도 괜찮아요!)")

if st.button("🪄 친절한 긴 설명으로 바꾸기"):
    if name and detail:
        full_text = f"""
안녕하세요, 한 땀 한 땀 정성을 다하는 작가입니다. 😊

오늘 소개할 저희 작품은 **[{name}]**입니다. 
가족에게 선물하는 마음으로 제작해 보았어요.

✨ **이 작품에 담긴 정성**
{detail}

핸드메이드 작품의 매력은 세상에 단 하나뿐이라는 것이죠.
작가로서 자부심을 가지고 꼼꼼하게 검수하여 보내드리고 있습니다.

배송이나 관리법에 대해 궁금한 점이 있으시면 언제든 톡톡으로 편하게 말씀해 주세요.
오늘도 따뜻한 하루 보내시길 바랍니다. 감사합니다. 🌸
        """
        st.success("친절한 글이 완성됐어요!")
        st.text_area("결과 (꾹 눌러 복사하세요)", value=full_text, height=350)
