import streamlit as st
from google import genai  # 변경된 임포트 방식
from PyPDF2 import PdfReader

# 1. 페이지 설정
st.set_page_config(page_title="PDF AI Insight", page_icon="📄", layout="wide")

# 가독성 중심의 CSS 커스텀 스타일링
st.markdown("""
    <style>
    /* 메인 배경: 아주 밝은 그레이 */
    .stApp {
        background-color: #f8f9fa;
        color: #212529;
    }
    
    /* 사이드바: 깔끔한 화이트 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #dee2e6;
    }

    /* 채팅 메시지 박스: 명확한 구분 */
    .stChatMessage {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        padding: 15px !important;
        margin-bottom: 10px !important;
        border: 1px solid #e9ecef !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }

    /* 타이틀: 신뢰감을 주는 딥 블루 */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0d6efd;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    /* 사용자/AI 텍스트 색상 강제 지정 (가독성) */
    .stMarkdown p {
        color: #212529 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 클라이언트 설정 (secrets.toml 기반)
# 기존: genai.configure(api_key=...)
# 변경: Client 객체 생성
client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown('<p class="main-title">📄 PDF 스마트 분석기 (v2.0)</p>', unsafe_allow_html=True)

# 세션 상태 관리
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# 3. 사이드바 - PDF 업로드
with st.sidebar:
    st.markdown("### 📂 문서 업로드")
    uploaded_file = st.file_uploader("PDF 파일을 선택하세요", type="pdf")
    
    if uploaded_file:
        with st.spinner("문서 분석 중..."):
            reader = PdfReader(uploaded_file)
            st.session_state.pdf_text = "".join([page.extract_text() for page in reader.pages])
            st.success("분석 완료!")

# 4. 채팅 영역 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 사용자 질문 처리
if prompt := st.chat_input("문서에 대해 질문하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 6. Gemini 2.5 Flash 호출 (최신 문법)
    with st.chat_message("assistant"):
        # 시스템 지침(Gems 지침) 설정
        system_instruction = f"당신은 문서 전문가입니다. 아래 내용을 바탕으로 답하세요.\n\n{st.session_state.pdf_text}"
        
        # 최신 모델 호출 방식
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                # 대화 맥락 유지를 위한 히스토리 (선택 사항)
            }
        )
        
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})