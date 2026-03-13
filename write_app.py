import streamlit as st
from eligibility import ELIGIBILITY_QUESTIONS, build_eligibility_prompt, get_rag_chain
from dotenv import load_dotenv
import boto3, json, os, requests
load_dotenv()

st.set_page_config(page_title='BridgeAI', page_icon='🌉', layout='wide')
st.title('🌉 BridgeAI — Find Your Benefits')
st.caption('Ask questions in any language | 以任何语言提问')

# Session state init
if 'mode' not in st.session_state:
    st.session_state.mode = 'home'
if 'profile' not in st.session_state:
    st.session_state.profile = {}
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'q_index' not in st.session_state:
    st.session_state.q_index = 0

# ── HOME SCREEN ──
if st.session_state.mode == 'home':
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('🔍 Discover your benefits')
        st.write('Answer 5 quick questions and we find everything you qualify for.')
        if st.button('Start Discovery', type='primary', use_container_width=True):
            st.session_state.mode = 'discovery'
            st.rerun()
    with col2:
        st.subheader('💬 Ask a question')
        st.write('Type any question about social services, legal aid, food or shelter.')
        if st.button('Open Chat', use_container_width=True):
            st.session_state.mode = 'chat'
            st.rerun()

# ── ELIGIBILITY DISCOVERY FLOW ──
elif st.session_state.mode == 'discovery':
    qi = st.session_state.q_index
    if qi < len(ELIGIBILITY_QUESTIONS):
        q = ELIGIBILITY_QUESTIONS[qi]
        st.progress((qi) / len(ELIGIBILITY_QUESTIONS))
        st.subheader(f'Question {qi+1} of {len(ELIGIBILITY_QUESTIONS)}')
        st.write(q['question'])
        if q.get('zh'): st.caption(q['zh'])
        if 'options' in q:
            ans = st.radio('Select one:', q['options'], key=f'q_{qi}')
        else:
            ans = st.text_input('Your answer:', key=f'q_{qi}')
        if st.button('Next →'):
            st.session_state.profile[q['key']] = ans
            st.session_state.q_index += 1
            st.rerun()
    else:
        st.success('✅ Profile complete! Finding your benefits...')
        with st.spinner('Searching schemes...'):
            chain = get_rag_chain()
            prompt = build_eligibility_prompt(st.session_state.profile)
            result = chain.invoke(prompt)
        st.subheader('📋 Benefits You May Qualify For')
        st.write(result['result'])
        st.divider()
        if st.button('💬 Ask a follow-up question'):
            st.session_state.mode = 'chat'
            st.rerun()

# ── FREE CHAT ──
elif st.session_state.mode == 'chat':
    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            st.write(msg['content'])
    if prompt := st.chat_input('Type your question in any language...'):
        st.session_state.messages.append({'role': 'user', 'content': prompt})
        with st.chat_message('assistant'):
            with st.spinner('Searching...'):
                chain = get_rag_chain()
                result = chain.invoke(prompt)
                answer = result['result']
            st.write(answer)
            st.session_state.messages.append({'role': 'assistant', 'content': answer})
