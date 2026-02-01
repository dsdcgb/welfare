import streamlit as st
from google import genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from PyPDF2 import PdfReader
import os

# 1. 페이지 설정 및 디자인 (이전의 소프트 모던 스타일 유지)
st.set_page_config(page_title="Dalseo AI Manual", page_icon="✨", layout="wide")

# CSS 스타일 (가독성을 위해 핵심 부분만 유지)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; color: #212529; }
    /* 1. Pretendard 웹 폰트 불러오기 */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    /* 2. 앱 전체 및 타이틀에 폰트 적용 */
    html, body, [class*="css"], .stApp, .main-title {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif !important;
    }
    .main-title {
        /* 1. 요청하신 글자 크기 및 두께 설정 */
        font-size: 2rem !important;
        font-weight: 700 !important;
        
        /* 2. 그라데이션 효과 (신뢰감 있는 블루 계열) */
        background: linear-gradient(90deg, #0d6efd 0%, #00d2ff 100%);
        -webkit-background-clip: text; /* 글자 모양대로 배경 자르기 */
        -webkit-text-fill-color: transparent !important; /* 글자 내부 색상을 투명하게 하여 배경 노출 */
        
        /* 3. 정렬 및 간격 조절 */
        text-align: center;
        margin-top: -1rem;
        margin-bottom: 2rem;
        letter-spacing: -0.02em; /* 폰트를 더 세련되게 만드는 자간 조절 */
        
        /* 4. 애니메이션 효과 (선택 사항: 부드러운 느낌 추가) */
        transition: all 0.3s ease;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 인덱스 로드 함수 (캐싱 적용으로 속도 극대화)
@st.cache_resource
def load_vectorstore():
    # create_index.py에서 사용한 것과 동일한 임베딩 모델 설정
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004", 
        google_api_key=st.secrets["GOOGLE_API_KEY"]
    )
    # 로컬에 저장된 faiss_index 폴더 로드
    if os.path.exists("faiss_index"):
        return FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    return None

# 인덱스 불러오기
vectorstore = load_vectorstore()

# 2. 클라이언트 및 모델 설정 (Gemini 2.5 Flash)
client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown('<p class="main-title">✨달서 복지서비스 도우미</p>', unsafe_allow_html=True)

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 기록 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 질문 처리 로직
if prompt := st.chat_input("문서 내용에 대해 질문하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if vectorstore:
            # A. 문서에서 질문과 가장 관련 있는 조각 k개 검색 (RAG 핵심)
            with st.spinner("관련 내용을 찾는 중..."):
                docs = vectorstore.similarity_search(prompt, k=4)
                context_text = "\n\n".join([doc.page_content for doc in docs])

            # B. 검색된 내용만 시스템 지침으로 전달 (토큰 절약)
            system_instruction = f"""
	    당신은 대구광역시 달서구의 사회복지업무 전문가입니다.
	    1. 제공된 문서 내용을 바탕으로 답변하세요.
	    2. 문서에 없는 정보는 지어내지 말고 "죄송합니다. 정보가 없어 답변을 할 수 없습니다. 달서구청(053-667-2000)으로 문의하시기 바랍니다."라고 안내하세요.
    
	    ## 출력
	    1. 복지 서비스(사업) 종류가 많으면 다음 순서로 정보를 출력합니다.
	      - 서비스명
	      - 서비스 내용 요약
	    2. 복지 서비스(사업) 종류가 많지 않으면 서비스(사업)별 상세 정보를 출력합니다.
            {context_text}
            """

            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"system_instruction": system_instruction}
                )
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"답변 생성 중 오류가 발생했습니다: {e}")
        else:
            st.error("FAISS 인덱스 파일을 찾을 수 없습니다. faiss_index 폴더를 업로드했는지 확인해주세요.")
