import streamlit as st
import pandas as pd
import io
import openai
import json
import base64
from PIL import Image, ImageEnhance

# ... (상단 설정 및 글쓰기 탭은 동일) ...

# --- [Tab 2: 이미지 & 상세페이지] ---
with tabs[1]:
    col_img1, col_img2 = st.columns([1, 1.2]) # 캔바 쪽을 조금 더 넓게 배치
    
    with col_img1:
        st.subheader("📸 지능형 사진 보정")
        uploaded_files = st.file_uploader("보정할 사진 선택", type=["jpg", "png"], accept_multiple_files=True)
        if uploaded_files and api_key and st.button("🚀 사진 자동 보정"):
            client = openai.OpenAI(api_key=api_key)
            cols = st.columns(2)
            for idx, file in enumerate(uploaded_files):
                img_bytes = file.getvalue()
                encoded = base64.b64encode(img_bytes).decode('utf-8')
                res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": [{"type": "text", "text": "화사한 보정 수치 JSON."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}}]}],
                    response_format={"type": "json_object"}
                )
                vals = json.loads(res.choices[0].message.content)
                img = Image.open(io.BytesIO(img_bytes))
                img = ImageEnhance.Brightness(img).enhance(vals.get('b', 1.1))
                img = ImageEnhance.Color(img).enhance(vals.get('c', 1.1))
                with cols[idx % 2]:
                    st.image(img, use_container_width=True)

    with col_img2:
        st.subheader("🎨 캔바(Canva) 상세페이지 제작")
        
        # 1. 캔바 바로가기 버튼 (따님이 만든 템플릿 주소를 따옴표 안에 넣으세요)
        canva_url = "https://www.canva.com/" # 여기에 실제 템플릿 주소 입력
        st.link_button("✨ 모그 전용 캔바 작업실 열기", canva_url, use_container_width=True)
        
        st.divider()
        
        st.write("아래 버튼을 누르면 캔바에 한 번에 넣을 수 있는 파일을 만들어드려요.")
        if st.button("🪄 캔바 대량 제작용 파일 만들기"):
            if not name:
                st.warning("상단의 작품 정보를 먼저 입력해주세요.")
            else:
                client = openai.OpenAI(api_key=api_key)
                prompt = f"""
                브랜드 '모그'의 {name} 상세페이지 5장을 기획하세요.
                반드시 아래 구조의 JSON 배열로만 답변하세요.
                [
                  {{"순서": "1", "메인문구": "문구", "설명": "설명", "사진제안": "구도"}},
                  ... 5번까지
                ]
                별표(**) 금지, 다정한 말투.
                """
                with st.spinner("캔바 레시피를 굽고 있어요..."):
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        response_format={ "type": "json_object" }
                    )
                    data = json.loads(response.choices[0].message.content)
                    df = pd.DataFrame(list(data.values())[0])
                    
                    # 화면에 표로 보여주기
                    st.table(df)
                    
                    # CSV 다운로드 버튼
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 캔바 업로드용 파일 받기",
                        data=csv,
                        file_name=f"moog_canva_{name}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    st.caption("💡 캔바의 '대량 제작' 기능을 사용하면 위 내용이 자동으로 채워집니다!")

# ... (Tab 3: 영상 제작 팁은 동일) ...
