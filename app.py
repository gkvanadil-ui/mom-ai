import streamlit as st
from rembg import remove
from PIL import Image, ImageOps
import io

# 앱 설정 및 예쁜 테마
st.set_page_config(page_title="작가님을 위한 AI 상세페이지 비서")

st.markdown("""
    <style>
    .main { background-color: #fcfaf8; }
    h1 { color: #8e735b; font-size: 40px !important; text-align: center; }
    .stButton>button { 
        background-color: #8e735b; color: white; border-radius: 10px; height: 3em; font-size: 20px;
    }
    </style>
    """, unsafe_allow_stdio=True)

st.title("🕯️ 엄마를 위한 프리미엄 AI 비서")
st.write("사진은 고급스럽게, 설명은 친절하게 바꿔드릴게요.")

st.divider()

# --- 1단계: 고급 설정샷 이미지 만들기 ---
st.header("📸 1. 제품 사진 업로드")
file = st.file_uploader("작품 사진을 선택하세요", type=["jpg", "jpeg", "png"])

if file:
    img = Image.open(file)
    st.image(img, caption="원본 사진", width=300)
    
    if st.button("✨ 프리미엄 스튜디오 컷으로 변형하기"):
        with st.spinner("AI가 조명을 맞추고 배경을 꾸미는 중입니다..."):
            # 1. 배경 제거
            input_bytes = file.getvalue()
            no_bg_bytes = remove(input_bytes)
            subject = Image.open(io.BytesIO(no_bg_bytes)).convert("RGBA")
            
            # 2. 고급스러운 베이지톤 스튜디오 배경 생성 (이미지 합성)
            # 엄마들 취향에 가장 맞는 따뜻하고 고급스러운 색감입니다.
            bg_color = (245, 242, 235) # 고급스러운 샴페인 베이지
            canvas = Image.new("RGBA", subject.size, bg_color)
            
            # 그림자 효과를 살짝 주기 위해 원본 위치에 배치
            canvas.paste(subject, (0, 0), subject)
            final_img = canvas.convert("RGB")
            
            st.image(final_img, caption="고급 설정샷 완성!", width=400)
            
            buf = io.BytesIO()
            final_img.save(buf, format="JPEG", quality=95)
            st.download_button("📥 완성된 사진 저장하기", buf.getvalue(), "luxury_product.jpg")

st.divider()

# --- 2단계: 자세하고 친절한 상품 설명 ---
st.header("✍️ 2. 상세페이지 문구 제작")
p_name = st.text_input("작품의 이름을 알려주세요", placeholder="예: 봄날의 코튼 뜨개 가방")
p_point = st.text_area("작품의 특징이나 엄마의 정성을 적어주세요", placeholder="예: 부드러운 순면 실로 한 달 동안 정성껏 떴어요. 무겁지 않아요.")

if st.button("🪄 전문가 버전 문구 만들기"):
    if p_name and p_point:
        # 자세하고 친절한 스토리텔링 형식의 템플릿
        long_description = f"""
안녕하세요, 따뜻한 마음을 담아 만드는 핸드메이드 작가입니다. 😊

오늘 소개해드릴 작품은 **'{p_name}'**입니다.

작품을 하나하나 완성할 때마다 내 가족이 사용한다는 마음으로 
가장 좋은 재료를 고르고, 수천 번의 손길을 더해 완성하고 있습니다.

✨ **이 작품의 특별한 점**
- {p_point}
- 기성품에서는 느낄 수 없는 핸드메이드만의 자연스러운 멋이 담겨 있어요.
- 오랜 시간 곁에 두고 사용하실 수 있도록 보이지 않는 곳까지 꼼꼼하게 마무리했습니다.

선물을 하시는 분의 정성까지 느껴지도록 정성껏 포장하여 보내드릴게요.
한 땀 한 땀 담긴 진심을 느껴보세요. 🌸

---
* 궁금하신 점이나 특별한 요청사항은 언제든 편하게 '네이버 톡톡'으로 문의주세요. 
항상 친절하게 답변해 드릴게요! 감사합니다.
        """
        st.success("친절한 설명글이 완성되었습니다!")
        st.text_area("이 내용을 복사해서 사용하세요", value=long_description, height=400)
    else:
        st.warning("이름과 특징을 적어주시면 AI가 더 예쁘게 글을 써드려요!")
