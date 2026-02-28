import streamlit as st
from Groq import run_agent

st.set_page_config(
    page_title="Agent",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg:       #F5F3EE;
    --surface:  #EDEAE2;
    --border:   #DEDAD0;
    --olive:    #6B7A3E;
    --olive-bg: #EEF0E4;
    --text:     #2C2C27;
    --muted:    #8C8B7E;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main { background: var(--bg) !important; }

#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

.block-container {
    max-width: 720px !important;
    padding: 0 1.5rem 130px !important;
    margin: 0 auto !important;
}

.top-bar {
    position: sticky;
    top: 0;
    z-index: 10;
    background: var(--bg);
    border-bottom: 1px solid var(--border);
    padding: 0.85rem 0;
    margin-bottom: 1.75rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.top-bar-title {
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    font-size: 0.95rem;
    color: var(--text);
}

.top-bar-pill {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.06em;
    color: var(--olive);
    background: var(--olive-bg);
    border: 1px solid #C8D0A0;
    border-radius: 100px;
    padding: 3px 10px;
}

.msg-row {
    display: flex;
    gap: 10px;
    margin-bottom: 1.2rem;
    align-items: flex-start;
}

.msg-row.user { flex-direction: row-reverse; }

.avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    font-weight: 500;
    margin-top: 3px;
}

.avatar.user  { background: var(--olive); color: #fff; }
.avatar.agent { background: var(--surface); border: 1px solid var(--border); color: var(--olive); }

.bubble {
    max-width: 78%;
    padding: 0.7rem 1rem;
    border-radius: 14px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    line-height: 1.65;
    color: var(--text);
}

.bubble.user {
    background: var(--olive);
    color: #F5F3EE;
    border-radius: 14px 4px 14px 14px;
}

.bubble.agent {
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 4px 14px 14px 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.empty-state {
    text-align: center;
    padding: 5rem 1rem 2rem;
    color: var(--muted);
}

.empty-icon { font-size: 1.6rem; margin-bottom: 0.65rem; opacity: 0.4; }
.empty-text { font-family: 'DM Sans', sans-serif; font-size: 0.85rem; font-style: italic; font-weight: 300; }

.fixed-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 100;
    background: var(--bg);
    border-top: 1px solid var(--border);
    padding: 0.85rem 0 1rem;
}

.fixed-bar-inner {
    max-width: 720px;
    margin: 0 auto;
    padding: 0 1.5rem;
    display: flex;
    gap: 0.6rem;
    align-items: center;
}

[data-testid="stTextInput"] { flex: 1; margin: 0 !important; }
[data-testid="stTextInput"] label { display: none !important; }
[data-testid="stTextInput"] > div { flex: 1; }

[data-testid="stTextInput"] input {
    background: #FFFFFF !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.7rem 1rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    transition: border-color 0.15s !important;
    caret-color: #000000 !important;
}

[data-testid="stTextInput"] input:focus {
    border-color: #A8B46A !important;
    box-shadow: 0 0 0 3px rgba(107,122,62,0.09) !important;
    outline: none !important;
}

[data-testid="stTextInput"] input::placeholder { color: #C0BEB4 !important; }

[data-testid="stButton"] > button {
    background: var(--olive) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #F5F3EE !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 0.7rem 1.4rem !important;
    white-space: nowrap !important;
    cursor: pointer !important;
    transition: background 0.15s !important;
    height: 42px !important;
}

[data-testid="stButton"] > button:hover { background: #596832 !important; }

[data-testid="stSpinner"] > div {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    color: var(--muted) !important;
}

::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

if "pending" not in st.session_state:
    st.session_state.pending = None

if "input_key" not in st.session_state:
    st.session_state.input_key = 0

st.markdown("""
<div class="top-bar">
    <span class="top-bar-title">Agent</span>
    <span class="top-bar-pill">WEBLLM</span>
</div>
""", unsafe_allow_html=True)

if not st.session_state.history:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">◌</div>
        <div class="empty-text">Ask anything. Web search is enabled.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for q, a in st.session_state.history:
        st.markdown(f"""
        <div class="msg-row user">
            <div class="avatar user">you</div>
            <div class="bubble user">{q}</div>
        </div>
        <div class="msg-row agent">
            <div class="avatar agent">ai</div>
            <div class="bubble agent">{a}</div>
        </div>
        """, unsafe_allow_html=True)

if st.session_state.pending:
    with st.spinner("Thinking…"):
        answer = run_agent(st.session_state.pending)
    st.session_state.history.append((st.session_state.pending, answer))
    st.session_state.pending = None
    st.rerun()

spinner_slot = st.empty()

st.markdown('<div class="fixed-bar"><div class="fixed-bar-inner">', unsafe_allow_html=True)

col_input, col_btn = st.columns([5, 1])
with col_input:
    question = st.text_input(
        "q",
        placeholder="Message Agent…",
        label_visibility="hidden",
        key=f"chat_input_{st.session_state.input_key}"
    )
with col_btn:
    send = st.button("Send")

st.markdown('</div></div>', unsafe_allow_html=True)

if (send or question) and question.strip():
    if question.strip() not in [h[0] for h in st.session_state.history[-1:]] or not st.session_state.history:
        st.session_state.pending = question.strip()
        st.session_state.input_key += 1
        st.rerun()