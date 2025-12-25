import streamlit as st
import pandas as pd
from PIL import Image, ImageEnhance, ImageOps
import io
import openai
import base64
import json
from streamlit_drawable_canvas import st_canvas  # 🖌️ 직접 그리기 도구 추가

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="centered")

# --- CSS: 다크모드 및 모바일 시인성 ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { color: inherit; }
    h1, h2, h3 { color: #D4A373 !important; font-weight: bold !important; margin-bottom: 12px; }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.8em;
        background-color: #7d6e63; color: white !important;
        font-weight: bold; font-size: 18px !important;
        border: none; margin-bottom: 8px;
    }
    .stTextArea textarea {
        font-size: 17px !important;
        line-height: 1.6 !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: inherit !important;
        border: 1px solid #7d6e63 !important;
    }
    hr { border-top: 1px solid #7d6e63; opacity: 0.3; }
    </style>
    """, unsafe_allow_html=True)

# --- API 키 설정 ---
api_key = st.secrets.get("OPENAI_API_KEY")

st.title("🕯️ 모그(Mog) 작가 전용 비서")
st.write("<p style='text-align: center;'>작가님의 따뜻한 진심이 글에 그대로 담기도록 도와드려요🌸</p>", unsafe_allow_html=True)

# --- [1단계: 정보 입력] ---
st.header("1️⃣ 작품 정보 입력")
with st.expander("📝 이곳을 눌러 내용을 작성해주세요", expanded=True):
    name = st.text_input("📦 작품 이름", placeholder="예: 빈티지 튤립 뜨개 파우치")
    c1, c2 = st.columns(2)
    with c1:
        mat = st.text_input("🧵 소재", placeholder="코튼 100%")
        size = st.text_input("📏 크기", placeholder="20*15cm")
    with c2:
        period = st.text_input("⏳ 제작 기간", placeholder="주문 후 3일")
        care = st.text_input("💡 세탁 방법", placeholder="미온수 손세탁 권장")
    keys = st.text_area("🔑 작품 특징", placeholder="색감이 화사해서 포인트 아이템으로 좋아요.")
    process = st.text_area("🛠️ 제작 포인트", placeholder="안감까지 꼼꼼히 제작했습니다.")

st.divider()

# --- AI 처리 함수 (어투 지침 강화) ---
def process_mog_ai(platform_guide):
    if not api_key: return None
    client = openai.OpenAI(api_key=api_key)
    
    # [핵심 어투 프롬프트]
    mog_tone_prompt = f"""
    당신은 핸드메이드 브랜드 '모그(Mog)'를 운영하는 작가입니다. 
    다음 지침을 반드시 지켜서 [{platform_guide['name']}] 판매글을 작성하세요.

    [어투 지침 - 가장 중요]
    - 말투: 50대 여성 작가의 다정하고 따뜻한 말투를 사용하세요.
    - 어미: '~이지요^^', '~해요', '~좋아요', '~보내드려요'를 주로 사용하세요.
    - 금지 사항: 절대로 별표(*)나 볼드체(**) 같은 특수 기호를 사용하지 마세요. 
    - 이모지: 꽃(🌸,🌻), 구름(☁️), 반짝이(✨)를 적절히 섞어주세요.

    [플랫폼 지침]
    - {platform_guide['desc']}

    [작품 정보]
    이름: {name} / 소재: {mat} / 크기: {size} / 기간: {period} / 관리: {care}
    특징: {keys} / 포인트: {process}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "user", "content": mog_tone_prompt}]
        )
        return response.choices[0].message.content.replace("**", "").replace("*", "").strip()
    except:
        return "오류가 발생했습니다. 다시 시도해 주세요."

# --- [2단계: 작업실 선택] ---
st.header("2️⃣ 작업실 선택")
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 사진보정", "💡 캔바 & 에픽"])

# --- Tab 1: 판매글 쓰기 ---
with tabs[0]:
    if 'texts' not in st.session_state:
        st.session_state.texts = {"인스타그램": "", "아이디어스": "", "네이버 스마트스토어": ""}

    st.write("💡 아래 버튼을 누르면 작가님 말투로 글이 써집니다.")
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    if btn_col1.button("📸 인스타그램"):
        st.session_state.texts["인스타그램"] = process_mog_ai({"name": "인스타그램", "desc": "해시태그 포함, 감성적인 인사말과 계절감을 담은 일기 스타일."})
    if btn_col2.button("🎨 아이디어스"):
        st.session_state.texts["아이디어스"] = process_mog_ai({"name": "아이디어스", "desc": "줄바꿈을 매우 자주 하고, 작가님의 정성이 느껴지도록 짧은 문장 위주 작성."})
    if btn_col3.button("🛍️ 스마트스토어"):
        st.session_state.texts["네이버 스마트스토어"] = process_mog_ai({"name": "네이버 스마트스토어", "desc": "구분선(⸻)을 활용하여 소재, 사이즈, 관리법 정보를 한눈에 보기 좋게 정리."})

    for p_key in ["인스타그램", "아이디어스", "네이버 스마트스토어"]:
        if st.session_state.texts[p_key]:
            st.write(f"---")
            st.write(f"**✅ {p_key} 결과**")
            current_txt = st.text_area(f"{p_key} 내용", value=st.session_state.texts[p_key], height=300, key=f"area_{p_key}")
            
            with st.expander(f"✨ {p_key} 글 수정 요청"):
                feedback = st.text_input("고칠 점을 적어주세요", key=f"f_{p_key}")
                if st.button("♻️ 다시 쓰기", key=f"b_{p_key}"):
                    refine_prompt = f"기존글: {current_txt}\n요청사항: {feedback}\n작가님 말투(~이지요^^)와 기호 금지 규칙을 지켜서 다시 써줘."
                    st.session_state.texts[p_key] = process_mog_ai({"name": p_key, "desc": refine_prompt})
                    st.rerun()

# --- Tab 2: 사진보정 ---
with tabs[1]:
    st.subheader("📸 AI 섬세한 사진 작업실")
    st.write("AI가 사진의 밝기, 색감, 질감을 아주 섬세하게 분석하여 원본보다 조금 더 화사하고 깔끔하게만 다듬어 드려요.")
    
    uploaded_files = st.file_uploader("작업할 사진 선택", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_files and api_key:
        c1, c2 = st.columns(2)
        
        # --- 기능 1: AI 섬세 자율 보정 ---
        if c1.button("✨ AI 섬세 보정 시작"):
            client = openai.OpenAI(api_key=api_key)
            def encode_image(image_bytes): return base64.b64encode(image_bytes).decode('utf-8')
            
            for idx, file in enumerate(uploaded_files):
                img_bytes = file.getvalue()
                with st.spinner(f"{idx+1}번 사진을 조심스럽게 분석 중..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "user", "content": [
                                {"type": "text", "text": """당신은 핸드메이드 작품 전문 사진가입니다. 
                                다음 가이드를 바탕으로 이 사진의 최적 보정 수치를 결정하세요. 
                                이미지가 하얗게 날아가거나(Overexposed) 인위적으로 보이지 않게 하는 것이 가장 중요합니다.

                                [보정 철학]
                                1. 자연스러움: 원본의 분위기를 최대한 유지하세요.
                                2. 밝기(brightness): 사진이 어두울 때만 '아주 미세하게' 높이세요 (최대 1.15). 충분히 밝다면 1.0을 유지하세요.
                                3. 대비(contrast): 상품이 흐릿할 때만 아주 살짝 높이세요 (최대 1.1).
                                4. 채도(saturation): 색감을 생기 있게 만들되 과하지 않게 (0.95~1.1).
                                5. 선명도(sharpness): 질감이 보일 정도로만 살짝 높이세요 (최대 1.3).

                                오직 JSON 형식으로만 답하세요: 
                                {"brightness": n, "contrast": n, "saturation": n, "sharpness": n}"""},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(img_bytes)}"}}
                            ]}],
                            response_format={ "type": "json_object" }
                        )
                        res = json.loads(response.choices[0].message.content)
                        img = Image.open(io.BytesIO(img_bytes))
                        img = ImageOps.exif_transpose(img)
                        if img.mode == 'RGBA': img = img.convert('RGB')
                        
                        img = ImageEnhance.Brightness(img).enhance(res.get('brightness', 1.0))
                        img = ImageEnhance.Contrast(img).enhance(res.get('contrast', 1.0))
                        img = ImageEnhance.Color(img).enhance(res.get('saturation', 1.0))
                        img = ImageEnhance.Sharpness(img).enhance(res.get('sharpness', 1.0))
                        
                        st.image(img, caption=f"✅ {idx+1}번 자연스러운 보정 완료")
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=95)
                        st.download_button(f"📥 {idx+1}번 사진 저장", buf.getvalue(), f"mog_natural_{idx+1}.jpg", key=f"dl_{idx}")
                    except:
                        st.error(f"{idx+1}번 보정 실패🌸")

        # --- 기능 2: 얼굴 모자이크 (AI 정밀 감지) ---
        if c2.button("👤 정밀 얼굴 모자이크 시작"):
            client = openai.OpenAI(api_key=api_key)
            def encode_image(image_bytes): return base64.b64encode(image_bytes).decode('utf-8')

            for idx, file in enumerate(uploaded_files):
                img_bytes = file.getvalue()
                raw_img = Image.open(io.BytesIO(img_bytes))
                raw_img = ImageOps.exif_transpose(raw_img)
                w, h = raw_img.size

                with st.spinner(f"{idx+1}번 사진에서 얼굴 탐색 중..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "user", "content": [
                                {"type": "text", "text": f"이 이미지(가로 {w}px, 세로 {h}px)에서 실제 사람의 얼굴만 찾아 [ymin, xmin, ymax, xmax] (0~1000 기준) 리스트로 답하세요. JSON 형식: {{'faces': [[...]]}}"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(img_bytes)}"}}
                            ]}],
                            response_format={ "type": "json_object" }
                        )
                        res = json.loads(response.choices[0].message.content)
                        faces = res.get('faces', [])
                        img = raw_img.copy()
                        if not faces:
                            st.info(f"💡 {idx+1}번 사진은 가릴 얼굴을 찾지 못했어요.")
                        else:
                            for face in faces:
                                ymin, xmin, ymax, xmax = face
                                left, top, right, bottom = (xmin/1000)*w, (ymin/1000)*h, (xmax/1000)*w, (ymax/1000)*h
                                # 영역 확장 및 모자이크
                                face_area = img.crop((int(left-10), int(top-10), int(right+10), int(bottom+10)))
                                mosaic = face_area.resize((15, 15), resample=Image.BILINEAR).resize(face_area.size, resample=Image.NEAREST)
                                img.paste(mosaic, (int(left-10), int(top-10)))
                            st.image(img, caption=f"👤 {idx+1}번 얼굴 보호 완료")
                            buf = io.BytesIO(); img.save(buf, format="JPEG", quality=95)
                            st.download_button(f"📥 {idx+1}번 저장하기", buf.getvalue(), f"mog_face_{idx+1}.jpg", key=f"btn_face_{idx}")
                    except:
                        st.error(f"{idx+1}번 처리 오류🌸")

# --- ✨ 기능 3: 직접 그려서 모자이크 (에러 절대 안 나는 버전) ---
    st.divider()
    st.subheader("🎨 직접 그려서 모자이크 하기")
    st.write("위의 사진 위치를 참고해서, 아래 회색 판의 같은 자리에 슥슥 칠해 주세요.")
    
    manual_file = st.file_uploader("그림 그릴 사진 1장 선택", type=["jpg", "jpeg", "png"], key="manual_up")
    
    if manual_file:
        # 1. 사진 전처리 (회전 보정 및 RGB 변환)
        bg = Image.open(manual_file)
        bg = ImageOps.exif_transpose(bg)
        if bg.mode != 'RGB': bg = bg.convert('RGB')
        
        # 2. 크기 계산 (화면에 꽉 차게 조절)
        canvas_width = 600
        canvas_height = int(bg.height * (canvas_width / bg.width))
        
        # 3. 사진을 먼저 보여줌 (엄마가 위치를 확인할 수 있는 기준 사진)
        st.image(bg, width=canvas_width, caption="위 사진의 얼굴 위치를 아래 판에 그려주세요")

        # 4. 🛠️ 에러 해결 핵심: background_image를 None으로 설정!
        # 에러가 나는 원인인 '사진 주소 변환' 과정을 아예 삭제했습니다.
        stroke_width = st.slider("붓 크기 조절 (얼굴 크기에 맞게)", 5, 150, 40)
        
        st.write("👇 아래 판에 위치를 똑같이 색칠하세요 (색칠한 곳이 모자이크됩니다)")
        canvas_result = st_canvas(
            fill_color="rgba(0, 0, 0, 1)",  # 칠하는 색 (검정)
            stroke_width=stroke_width,
            stroke_color="rgba(0, 0, 0, 1)",
            background_color="#dcdcdc",     # 사진 대신 밝은 회색 판 사용
            height=canvas_height,
            width=canvas_width,
            drawing_mode="freedraw",
            key="safe_canvas_no_error",      # 에러 방지를 위해 새로운 키값 부여
            display_toolbar=True
        )
        
        if st.button("🚀 선택한 부분 모자이크 실행"):
            if canvas_result.image_data is not None:
                with st.spinner("칠하신 위치에 모자이크를 입히는 중..."):
                    # 엄마가 그린 붓자국(알파 채널)만 가져오기
                    mask_data = canvas_result.image_data[:, :, 3] 
                    mask_img = Image.fromarray(mask_data).resize(bg.size, resample=Image.NEAREST)
                    
                    # 5. 모자이크 배경 만들기 (입자를 45px로 굵고 확실하게!)
                    grain = 45
                    mosaic_bg = bg.resize((max(1, bg.width // grain), max(1, bg.height // grain)), resample=Image.BILINEAR)
                    mosaic_bg = mosaic_bg.resize(bg.size, resample=Image.NEAREST)
                    
                    # 6. 원본 사진 위에 '그린 부분'만 모자이크 덮어씌우기
                    final_img = Image.composite(mosaic_bg, bg, mask_img)
                    
                    st.image(final_img, caption="✨ 수동 모자이크가 완료되었습니다!")
                    
                    # 결과물 저장
                    buf = io.BytesIO()
                    final_img.save(buf, format="JPEG", quality=95)
                    st.download_button("📥 완성된 사진 저장하기", buf.getvalue(), "manual_mosaic_final.jpg")
            else:
                st.warning("먼저 회색 판 위에 모자이크할 부분을 칠해 주세요🌸")
                
                
# --- Tab 3: 캔바 & 에픽 ---
with tabs[2]:
    st.subheader("🎨 예쁜 상세페이지와 영상 만들기")
    st.write("작품 사진을 예쁜 배경에 넣거나, 음악이 흐르는 홍보 영상을 만드는 방법을 알려드릴게요. 🌸")
    st.markdown("### 1️⃣ 사진을 잡지처럼! '캔바(Canva)'")
    if st.button("🪄 AI가 추천하는 페이지 구성 보기"):
        if not name: st.warning("위쪽 '1️⃣ 작품 정보'를 먼저 입력해 주시면 더 정확하게 짜드려요🌸")
        else:
            with st.spinner("작가님을 위해 기획안을 작성 중입니다..."):
                prompt = f"핸드메이드 전문가로서 {name} 작품의 상세페이지 5장 구성안을 다정하게 써줘."
                st.info(process_mog_ai({"name": "상세페이지 기획", "desc": prompt}))
    st.link_button("✨ 캔바 앱 바로가기", "https://www.canva.com/templates/?query=상세페이지")
    st.divider()
    st.markdown("### 2️⃣ 음악이 흐르는 영상 만들기! '에픽(EPIK)'")
    with st.expander("📺 천천히 따라해보세요 (에픽 사용법)", expanded=True):
        st.markdown("1. 앱 실행 후 [템플릿] 누르기\n2. '감성' 검색\n3. 사진 넣고 저장! 🌸")
    st.write("<p style='text-align: center; color: #7d6e63;'>오늘도 작가님의 따뜻한 손길을 응원합니다. 화이팅! 🕯️</p>", unsafe_allow_html=True)
