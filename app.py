import streamlit as st
from rembg import remove
from PIL import Image
import io

# 1. 엄마를 위한 화면 스타일 설정 (큰 글씨와 분홍색 테마)
st.set_page_config(page_title="엄마의 AI 비서", layout="centered")

st.markdown("""
    <style>
    /* 전체 배경색과 글자 크기 */
    .main { background-color: #FFF5F5; }
    h1 { color: #FF69B4; font-size: 45px !important; text-align: center; }
    h2 { color: #333; font-size: 30px !important; }
    p, label, .stMarkdown { font-size: 22px !important; line-height: 1.6; }
    
    /* 버튼 예쁘고 크게 만들기 */
    .stButton>button { 
        background-color: #FF69B4; 
        color: white; 
        font-size: 25px !important; 
        height: 3.5em; 
        width: 100%;
        border-radius: 15px;
        border: none;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    }
    .stButton>button:hover { background-color: #FF1493; color: white; }
    
    /* 입력창 글자 크기 */
    input, textarea { font-size: 20px !important; }
    </style>
    """, unsafe_allow_stdio=True)

# 축하 효과 (사이트 열릴 때 풍선 팡팡!)
st.balloons()

st.title("🌸 엄마 전용 AI 비서 🌸")
st.write("딸이 만든 엄마만을 위한 마법 도구예요! 순서대로 따라 해보세요.")

st.divider()

# --- 1단계: 사진 배경 지우기 기능 ---
st.header("📸 1. 작품 사진을 골라주세요")
uploaded_file = st.file_uploader("여기를 눌러서 폰에 있는 사진을 선택하세요", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # 엄마가 올린 원본 사진 보여주기
    input_image = Image.open(uploaded_file)
    st.image(input_image, caption="엄마가 방금 올린 사진", width=350)
    
    # 배경 지우기 버튼
    if st.button("✨ 배경 깔끔하게 지우기 (클릭!)"):
        with st.spinner("AI가 예쁘게 고치는 중이에요. 잠시만요..."):
            try:
                # 배경 제거 로직
                input_bytes = uploaded_file.getvalue()
                output_bytes = remove(input_bytes)
                result_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
                
                # 하얀색 배경 깔기
                white_bg = Image.new("RGBA", result_img.size, "WHITE")
                white_bg.paste(result_img, (0, 0), result_img)
                final_img = white_bg.convert("RGB")
                
                # 결과물 보여주기
                st.image(final_img, caption="짜잔! 배경이 깨끗해졌어요!", width=350)
                
                # 저장 버튼 만들기
                buf = io.BytesIO()
                final_img.save(buf, format="JPEG")
                st.download_button(
                    label="🎁 보정된 사진 폰에 저장하기",
                    data=buf.getvalue(),
                    file_name="mom_product.jpg",
                    mime="image/jpeg"
                )
            except Exception as e:
                st.error(f"에러가 났어요. 딸에게 알려주세요! : {e}")

st.divider()

# --- 2단계: 홍보 글 만들기 기능 ---
st.header("✍️ 2. 홍보 글 만들기")
st.write("작품 이름이랑 엄마의 정성을 짧게 적어보세요.")

prod_name = st.text_input("작품 이름이 뭔가요?", placeholder="예: 뜨개 꽃 인형")
mom_heart = st.text_area("어떤 마음으로 만드셨나요?", placeholder="예: 손주 주려고 정성껏 만들었어요.")

if st.button("🪄 멋진 홍보 글 만들기 (클릭!)"):
    if prod_name and mom_heart:
        # 엄마 맞춤형 문구 생성
        description = f"""
안녕하세요, 핸드메이드 작가입니다. 😊

오늘 소개해드릴 작품은 **'{prod_name}'**입니다.
{mom_heart}

공방에서 한 땀 한 땀 직접 손으로 만들어서 
기성품과는 다른 따뜻한 온기를 느끼실 수 있을 거예요.

소중한 분께 드리는 특별한 선물로 추천드립니다.
궁금하신 점은 언제든 톡톡 문의주세요! 🌸
        """
        st.success("글이 완성됐어요! 아래 내용을 꾹 눌러서 복사하세요.")
        st.text_area("내용 복사하기", value=description, height=300)
    else:
        st.warning("작품 이름과 정성을 조금만 더 적어주세요!")

st.divider()
st.caption("우리 딸이 엄마를 위해 정성껏 만들었습니다. 사랑해요 엄마! ❤️")
