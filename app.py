# --- Tab 3: 고민 상담소 (로그 기반 & 현실 조언 강화) ---
with tabs[2]:
    st.header("💬 모그 작가님 전용 상담소")
    st.write("작품 이름 짓기부터 손님 응대까지, 선배 작가에게 물어보듯 편하게 말씀하세요. 🌸")

    # 1. 대화 로그 저장 금고 (session_state)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 2. 채팅 로그 출력 (카카오톡 스타일)
    chat_display = st.container()
    with chat_display:
        for m in st.session_state.chat_history:
            # 프로필 아이콘 설정 (엄마는 꽃, AI는 등불)
            avatar = "🌸" if m["role"] == "user" else "🕯️"
            with st.chat_message(m["role"], avatar=avatar):
                st.write(m["content"])

    # 3. 채팅 입력창 (상세 답변 로직 포함)
    if prompt := st.chat_input("작가님, 오늘 어떤 고민이 있으신가요?"):
        
        # 엄마 메시지 화면 표시 및 로그 저장
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🌸"):
            st.write(prompt)

        # AI의 상세 답변 생성
        with st.chat_message("assistant", avatar="🕯️"):
            with st.spinner("작가님의 고민을 꼼꼼히 읽고 있어요..."):
                try:
                    client = openai.OpenAI(api_key=api_key)
                    
                    # [상세 답변을 위한 강력한 지침]
                    system_instruction = f"""
                    당신은 핸드메이드 시장에서 10년 넘게 활동한 베테랑 선배 작가 '모그 AI'입니다.
                    다음 규칙에 따라 50대 여성 작가님께 현실적이고 구체적인 조언을 하세요.

                    1. 말투: 친근한 동료처럼 다정하게 (~이지요^^, ~해요, ~답니다)
                    2. 답변 수준: '열심히 하세요' 같은 뻔한 말 금지. 
                       - 가격 고민 시: 원가, 공임비, 플랫폼 수수료를 고려한 구체적 계산법 제안
                       - 응대 고민 시: 바로 복사해서 보낼 수 있는 '실제 문구'를 2~3가지 버전으로 제시
                       - 이름 고민 시: 작품의 특징을 살린 감성적인 이름 5가지 이상 추천
                    3. 연속성: 이전 대화 내용을 참고하여 맥락에 맞는 대답을 하세요.
                    4. 금기: 특수기호 * 나 ** 는 절대 쓰지 마세요.
                    """

                    # 대화 로그(전체 맥락) 전달
                    messages = [{"role": "system", "content": system_instruction}]
                    # 최근 10개의 대화 로그를 전달하여 흐름 유지
                    for m in st.session_state.chat_history[-10:]:
                        messages.append(m)
                        
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages
                    )
                    
                    full_answer = response.choices[0].message.content.replace("**", "").replace("*", "").strip()
                    
                    # 답변 표시 및 저장
                    st.write(full_answer)
                    st.session_state.chat_history.append({"role": "assistant", "content": full_answer})
                    
                    # 화면 즉시 갱신
                    st.rerun()
                    
                except:
                    st.error("앗, 잠시 연결이 고르지 않아요. 다시 말씀해 주셔요🌸")

    # 4. 관리 도구
    st.write("---")
    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("♻️ 대화 지우기"):
            st.session_state.chat_history = []
            st.rerun()
    with c2:
        st.caption("💡 팁: '요즘 유행하는 뜨개 색감 알려줘'나 '진상 손님 답장 써줘'라고 물어보세요.")
