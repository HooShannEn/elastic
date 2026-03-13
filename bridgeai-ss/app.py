import streamlit as st
from eligibility import ELIGIBILITY_QUESTIONS, build_eligibility_prompt, get_rag_chain
from dotenv import load_dotenv
import os, requests

load_dotenv()

st.set_page_config(page_title='BridgeAI', page_icon='🌉', layout='wide')

# ── FIX 4: Cache the RAG chain — build it once, reuse forever ──
@st.cache_resource
def load_rag_chain():
    return get_rag_chain()

# ── Session state init ──
for key, default in [
    ('mode', 'home'),
    ('profile', {}),
    ('messages', []),
    ('q_index', 0),
    ('case_code', None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── FIX 2: Sidebar — always visible regardless of mode ──
with st.sidebar:
    st.image("https://img.icons8.com/fluency/48/bridge.png", width=40)
    st.title("BridgeAI")
    st.caption("Unified Relief Ecosystem")
    st.divider()

    st.subheader("Navigate")
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.mode = 'home'
        st.rerun()
    if st.button("🔍 Eligibility Discovery", use_container_width=True):
        st.session_state.mode = 'discovery'
        st.session_state.q_index = 0
        st.session_state.profile = {}
        st.rerun()
    if st.button("💬 Chat", use_container_width=True):
        st.session_state.mode = 'chat'
        st.rerun()

    st.divider()
    st.subheader("Other Services")

    if st.button("⚖️ Legal & Gov Aid", use_container_width=True):
        st.session_state.mode = 'legal'
        st.rerun()
    if st.button("🍱 Food & Shelter", use_container_width=True):
        st.session_state.mode = 'food'
        st.rerun()

    st.divider()
    st.subheader("Returning User?")
    case_input = st.text_input("Enter your case code:", placeholder="e.g. 4829XK")
    if st.button("Load my case", use_container_width=True) and case_input:
        try:
            resp = requests.get(f"http://localhost:8000/case/{case_input}", timeout=3)
            if resp.ok:
                data = resp.json()
                if data.get("found"):
                    st.session_state.case_code = case_input
                    st.success(data["summary"])
                else:
                    st.warning("Case code not found.")
        except requests.exceptions.ConnectionError:
            st.info("Case service not connected yet.")  # graceful if Shaun's API isn't up

# ── Page header ──
st.title("🌉 BridgeAI — Find Your Benefits")
st.caption("Ask questions in any language | 以任何语言提问")

# ════════════════════════════════════
# HOME
# ════════════════════════════════════
if st.session_state.mode == 'home':
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.subheader("🔍 Discover benefits")
        st.write("Answer 5 questions and we find everything you qualify for.")
        if st.button("Start Discovery", type="primary", use_container_width=True):
            st.session_state.mode = 'discovery'
            st.session_state.q_index = 0
            st.session_state.profile = {}
            st.rerun()
    with col2:
        st.subheader("💬 Free chat")
        st.write("Ask anything about social services, legal aid, food or shelter.")
        if st.button("Open Chat", use_container_width=True):
            st.session_state.mode = 'chat'
            st.rerun()
    with col3:
        st.subheader("⚖️ Legal & Gov Aid")
        st.write("CPF, HDB, Legal Aid Bureau, employment schemes.")
        if st.button("Legal Questions", use_container_width=True):
            st.session_state.mode = 'legal'
            st.rerun()
    with col4:
        st.subheader("🍱 Food & Shelter")
        st.write("Food banks, emergency shelter, availability checks.")
        if st.button("Food & Shelter", use_container_width=True):
            st.session_state.mode = 'food'
            st.rerun()

# ════════════════════════════════════
# ELIGIBILITY DISCOVERY
# ════════════════════════════════════
elif st.session_state.mode == 'discovery':
    # FIX 3: Back button always visible
    if st.button("← Back to Home"):
        st.session_state.mode = 'home'
        st.session_state.q_index = 0
        st.session_state.profile = {}
        st.rerun()

    qi = st.session_state.q_index

    if qi < len(ELIGIBILITY_QUESTIONS):
        st.progress(qi / len(ELIGIBILITY_QUESTIONS))
        st.subheader(f"Question {qi + 1} of {len(ELIGIBILITY_QUESTIONS)}")

        q = ELIGIBILITY_QUESTIONS[qi]
        st.write(q['question'])
        if q.get('zh'):
            st.caption(q['zh'])

        if 'options' in q:
            ans = st.radio("Select one:", q['options'], key=f"q_{qi}")
        else:
            ans = st.text_input("Your answer:", key=f"q_{qi}")

        col_next, col_skip = st.columns([1, 5])
        with col_next:
            if st.button("Next →", type="primary"):
                if ans:
                    st.session_state.profile[q['key']] = ans
                    st.session_state.q_index += 1
                    st.rerun()
                else:
                    st.warning("Please answer before continuing.")

    else:
        st.success("✅ Profile complete! Searching for everything you qualify for...")
        with st.spinner("Searching schemes..."):
            chain = load_rag_chain()  # FIX 4: use cached chain
            prompt = build_eligibility_prompt(st.session_state.profile)
            result = chain.invoke(prompt)

        # FIX 5: Guard against empty/bad result
        answer = result.get('result', '').strip() if isinstance(result, dict) else str(result).strip()
        if not answer:
            answer = "I couldn't find specific schemes for your profile. Please visit your nearest Social Service Office or call ComCare at 1800-222-0000."

        st.subheader("📋 Benefits You May Qualify For")
        st.write(answer)
        st.divider()

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💬 Ask a follow-up question"):
                st.session_state.mode = 'chat'
                st.rerun()
        with col2:
            if st.button("🔁 Start over"):
                st.session_state.mode = 'discovery'
                st.session_state.q_index = 0
                st.session_state.profile = {}
                st.rerun()
        with col3:
            if st.button("🏠 Home"):
                st.session_state.mode = 'home'
                st.rerun()

# ════════════════════════════════════
# FREE CHAT
# ════════════════════════════════════
elif st.session_state.mode == 'chat':
    if st.button("← Back to Home"):
        st.session_state.mode = 'home'
        st.rerun()

    st.subheader("💬 Chat with BridgeAI")
    st.caption("Ask anything — social services, housing, food, legal aid.")

    # Render history
    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            st.write(msg['content'])

    if prompt := st.chat_input("Type your question in any language..."):
        st.session_state.messages.append({'role': 'user', 'content': prompt})
        with st.chat_message('user'):
            st.write(prompt)

        with st.chat_message('assistant'):
            with st.spinner('Searching...'):
                chain = load_rag_chain()  # FIX 4: cached
                result = chain.invoke(prompt)

            # FIX 1: Extract the answer string properly
            answer = result.get('result', '').strip() if isinstance(result, dict) else str(result).strip()

            # FIX 5: Fallback if nothing returned
            if not answer:
                answer = "I don't have specific information about that. For urgent needs, call ComCare at 1800-222-0000."

            st.write(answer)
            st.session_state.messages.append({'role': 'assistant', 'content': answer})

    if st.session_state.messages:
        if st.button("🗑️ Clear chat"):
            st.session_state.messages = []
            st.rerun()

# ════════════════════════════════════
# LEGAL (routes to Shaun's API)
# ════════════════════════════════════
elif st.session_state.mode == 'legal':
    if st.button("← Back to Home"):
        st.session_state.mode = 'home'
        st.rerun()

    st.subheader("⚖️ Legal & Government Aid")
    st.caption("CPF, HDB, Legal Aid Bureau, employment schemes, government grants.")

    if prompt := st.chat_input("Ask your legal or government aid question..."):
        with st.spinner("Checking legal resources..."):
            try:
                resp = requests.post(
                    "http://localhost:8000/legal/ask",
                    json={"question": prompt},
                    timeout=30
                )
                answer = resp.json().get("answer", "No answer returned.") if resp.ok else "Legal service unavailable."
            except requests.exceptions.ConnectionError:
                # Fallback to local RAG if Shaun's API isn't up yet
                chain = load_rag_chain()
                result = chain.invoke(prompt)
                answer = result.get('result', '') if isinstance(result, dict) else str(result)
                answer = answer or "I couldn't find information about that legal topic."

        st.write(answer)

# ════════════════════════════════════
# FOOD & SHELTER (routes to Alan's API)
# ════════════════════════════════════
elif st.session_state.mode == 'food':
    if st.button("← Back to Home"):
        st.session_state.mode = 'home'
        st.rerun()

    st.subheader("🍱 Food & Shelter")
    st.caption("Food banks, emergency shelters, and availability near you.")

    if prompt := st.chat_input("Ask about food assistance or emergency shelter..."):
        with st.spinner("Checking availability..."):
            try:
                resp = requests.post(
                    "http://localhost:8001/food/ask",
                    json={
                        "question": prompt,
                        "profile": st.session_state.profile,
                        "case_code": st.session_state.case_code
                    },
                    timeout=30
                )
                if resp.ok:
                    data = resp.json()
                    if data.get('escalated'):
                        st.error("🚨 " + data['answer'])  # crisis escalation — red box
                        if data.get('referral_summary'):
                            with st.expander("View referral summary sent to social worker"):
                                st.text(data['referral_summary'])
                    else:
                        st.write(data.get('answer', ''))
                        if data.get('availability'):
                            st.info(data['availability'])
                else:
                    st.warning("Food service unavailable.")
            except requests.exceptions.ConnectionError:
                # Fallback to local RAG
                chain = load_rag_chain()
                result = chain.invoke(prompt)
                answer = result.get('result', '') if isinstance(result, dict) else str(result)
                st.write(answer or "Please call ComCare at 1800-222-0000 for urgent food or shelter needs.")