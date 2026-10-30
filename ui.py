import html
import json
import os
import re
import time
import uuid
from datetime import datetime
import markdown as mdlib
import streamlit as st
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")
# History is per user id; the local app has a single user by default.
USER_ID = os.getenv("NYAYASETU_USER_ID", "anonymous")

st.set_page_config(
    page_title="NyayaSetu · Legal Advisor",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="expanded",  # toggled with the ☰ icon; the browser remembers the choice
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600&family=Geist+Mono:wght@400;500&display=swap');

/* ── CSS Variables ── */
:root {
    --bg-base:        #0c0d10;
    --bg-surface:     #141519;
    --bg-elevated:    #1b1c21;
    --border-subtle:  #25262d;
    --accent-gold:    #d4b062;
    --accent-gold-dim:#a88a45;
    --text-primary:   #eeece6;
    --text-body:      #d9d6ce;
    --text-secondary: #a3a3ab;
    --text-muted:     #686872;
    --danger:         #e55757;
    --font-display:   'Instrument Serif', Georgia, serif;
    --font-body:      'Geist', system-ui, sans-serif;
    --font-mono:      'Geist Mono', ui-monospace, monospace;
}

/* One body font everywhere — except Streamlit's icon glyphs, which need their icon font */
.stApp, .stApp *:not([data-testid="stIconMaterial"]):not(.material-icons):not(code):not(pre) {
    font-family: var(--font-body);
}
.stApp { -webkit-font-smoothing: antialiased; }

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
}

#MainMenu, footer, [data-testid="stDecoration"],
[data-testid="stToolbarActions"], [data-testid="stMainMenu"], [data-testid="stAppDeployButton"] { visibility: hidden; }
/* Streamlit's "Running… / Stop" indicator: the thinking dots already show progress */
[data-testid="stStatusWidget"] { display: none !important; }
/* While an answer is fetched, leftovers from the previous screen (e.g. the landing
   disclaimer) would linger under the thinking dots; hide them until redrawn */
[data-testid="stMainBlockContainer"] [data-testid="stElementContainer"][data-stale="true"] { display: none !important; }

/* Sidebar open/close: one ☰ icon in the same top-left spot whether open or closed */
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapseButton"] { visibility: visible !important; }
[data-testid="stSidebarCollapseButton"] { display: block !important; opacity: 1 !important; }
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"] button {
    width: 38px !important;
    height: 38px !important;
    border-radius: 10px !important;
    background: transparent !important;
    border: none !important;
    color: var(--text-secondary) !important;
    transition: background 0.15s, color 0.15s !important;
}
[data-testid="stExpandSidebarButton"]:hover,
[data-testid="stSidebarCollapseButton"] button:hover {
    background: var(--bg-elevated) !important;
    color: var(--text-primary) !important;
}
[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"],
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"] { font-size: 0 !important; }
[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"]::before,
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"]::before {
    content: "menu";
    font-size: 22px;
}
[data-testid="stSidebarHeader"] { justify-content: flex-start !important; padding: 0 !important; }
[data-testid="stSidebarCollapseButton"] { margin: -15px 0 0 -9px !important; }
header[data-testid="stHeader"] { background: transparent !important; }

[data-testid="stMainBlockContainer"] {
    max-width: 780px !important;
    padding: 2.5rem 1.25rem 2rem !important;
    margin: 0 auto !important;
}

/* ── Landing (new chat) ── */
.landing {
    padding: 11vh 0 1.75rem;
}
.landing-greeting {
    font-size: 0.74rem;
    font-weight: 500;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--accent-gold);
    margin-bottom: 0.6rem;
}
.landing-title {
    font-family: var(--font-display) !important;
    font-size: 2.4rem;
    font-weight: 400;
    line-height: 1.08;
    letter-spacing: -0.01em;
    color: var(--text-primary);
    margin-bottom: 0.75rem;
}
.landing-title em {
    font-family: var(--font-display) !important;
    font-style: italic;
    color: var(--accent-gold);
}
.landing-sub {
    font-size: 0.95rem;
    font-weight: 300;
    color: var(--text-secondary);
    line-height: 1.6;
}
.landing-note {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-top: 1.25rem;
}

/* Suggestion cards */
[class*="st-key-pill_"] [data-testid^="stBaseButton"] {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 12px !important;
    padding: 0.9rem 1rem !important;
    min-height: 3.4rem !important;
    justify-content: flex-start !important;
    transition: border-color 0.15s, background 0.15s !important;
}
[class*="st-key-pill_"] [data-testid^="stBaseButton"] * {
    justify-content: flex-start !important;
    text-align: left !important;
}
[class*="st-key-pill_"] [data-testid^="stBaseButton"] > div { width: 100% !important; }
[class*="st-key-pill_"] [data-testid^="stBaseButton"] p {
    font-family: var(--font-body) !important;
    font-size: 0.85rem !important;
    color: var(--text-secondary) !important;
    text-align: left !important;
}
[class*="st-key-pill_"] [data-testid^="stBaseButton"]:hover {
    border-color: rgba(201,168,76,0.5) !important;
    background: var(--bg-elevated) !important;
}
[class*="st-key-pill_"] [data-testid^="stBaseButton"]:hover p { color: var(--text-primary) !important; }

/* ── Message rows ── */
.msg-row {
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
    margin-bottom: 1.2rem;
    animation: fadeUp 0.22s ease;
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Avatars ── */
.avatar {
    width: 34px;
    height: 34px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 3px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    font-family: var(--font-body);
}
.avatar.agent {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, rgba(212,176,98,0.18), rgba(212,176,98,0.04));
    border: 1px solid rgba(212,176,98,0.35);
    color: var(--accent-gold);
    font-size: 0.85rem;
}

/* ── Bubbles ── */
.bubble {
    word-break: break-word;
}
.msg-row.user { justify-content: flex-end; margin: 1.6rem 0 1.4rem; }
.msg-row.user .bubble { margin-left: auto; }
.bubble.user {
    max-width: 75%;
    width: fit-content;
    background: var(--bg-elevated);
    color: var(--text-primary);
    border-radius: 18px 18px 4px 18px;
    padding: 0.6rem 1.05rem;
    font-size: 0.95rem;
    line-height: 1.55;
}
.bubble.agent {
    color: var(--text-body);
    font-size: 0.97rem;
    font-weight: 400;
    line-height: 1.75;
    padding: 0.1rem 0;
}

/* ── Markdown inside agent bubble ── */
.bubble.agent h1,
.bubble.agent h2,
.bubble.agent h3 {
    font-family: var(--font-display) !important;
    color: var(--text-primary);
    font-weight: 400;
    margin: 1.2rem 0 0.4rem;
    line-height: 1.2;
}
.bubble.agent h1 { font-size: 1.7rem; }
.bubble.agent h2 { font-size: 1.45rem; }
.bubble.agent h3 { font-size: 1.25rem; color: var(--accent-gold); }
.bubble.agent p  { margin-bottom: 0.8rem; }
.bubble.agent p:last-child { margin-bottom: 0; }
.bubble.agent strong { color: var(--text-primary); font-weight: 600; }
.bubble.agent em { color: var(--text-primary); font-style: italic; }
.bubble.agent hr {
    border: none;
    border-top: 1px solid var(--border-subtle);
    margin: 0.8rem 0;
}
.bubble.agent ul,
.bubble.agent ol {
    padding-left: 1.5rem;
    margin-bottom: 0.7rem;
}
.bubble.agent li { margin-bottom: 0.3rem; }
.bubble.agent li > p { margin-bottom: 0.25rem; }
.bubble.agent li > ul, .bubble.agent li > ol { margin: 0.2rem 0 0.6rem; }
.bubble.agent ol > li::marker { font-weight: 600; }
.bubble.agent li::marker { color: var(--accent-gold); }
.bubble.agent code {
    background: var(--bg-elevated);
    border: 1px solid var(--border-subtle);
    border-radius: 4px;
    padding: 0.12rem 0.4rem;
    font-size: 0.85em;
    color: var(--accent-gold);
    font-family: var(--font-mono);
}
.bubble.agent pre {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-left: 3px solid var(--accent-gold);
    border-radius: 8px;
    padding: 0.9rem 1.1rem;
    overflow-x: auto;
    margin-bottom: 0.7rem;
}
.bubble.agent pre code {
    background: transparent;
    border: none;
    padding: 0;
    color: var(--text-primary);
    font-size: 0.88rem;
}
.bubble.agent blockquote {
    border-left: 3px solid var(--accent-gold);
    padding-left: 1rem;
    color: var(--text-secondary);
    margin: 0.6rem 0;
    font-style: italic;
    font-family: var(--font-display) !important;
    font-size: 1.15rem;
}
.bubble.agent table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 0.7rem;
    font-size: 0.88rem;
}
.bubble.agent th {
    background: var(--bg-elevated);
    color: var(--accent-gold);
    padding: 0.5rem 0.9rem;
    border: 1px solid var(--border-subtle);
    text-align: left;
    font-weight: 500;
    letter-spacing: 0.06em;
    font-size: 0.72rem;
    text-transform: uppercase;
}
.bubble.agent td {
    padding: 0.45rem 0.9rem;
    border: 1px solid var(--border-subtle);
    color: var(--text-primary);
}
.bubble.agent tr:nth-child(even) td { background: rgba(255,255,255,0.02); }

/* ── Section label above agent reply ── */
.agent-label {
    font-size: 0.8rem;
    color: var(--text-secondary);
    font-weight: 500;
    margin: 0.3rem 0 0.35rem;
}

/* ── Streaming cursor ── */
.bubble.agent.streaming > :last-child:not(ul):not(ol):not(table)::after,
.bubble.agent.streaming > ul:last-child > li:last-child::after,
.bubble.agent.streaming > ol:last-child > li:last-child::after {
    content: "";
    display: inline-block;
    width: 0.5em;
    height: 1.05em;
    margin-left: 3px;
    vertical-align: text-bottom;
    border-radius: 2px;
    background: var(--accent-gold);
    animation: cursorBlink 1s steps(1) infinite;
}
@keyframes cursorBlink { 50% { opacity: 0; } }

/* ── Thinking dots ── */
.thinking {
    display: flex;
    gap: 5px;
    align-items: center;
    padding: 0.55rem 0;
}
.dot {
    width: 6px;
    height: 6px;
    background: var(--accent-gold);
    border-radius: 50%;
    animation: pulse 1.5s infinite ease-in-out;
    opacity: 0.35;
}
.dot:nth-child(1) { animation-delay: 0s; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes pulse {
    0%, 80%, 100% { transform: scale(0.7); opacity: 0.35; }
    40%            { transform: scale(1.2); opacity: 1; }
}

/* ── Divider ── */
.msg-divider {
    height: 1px;
    background: var(--border-subtle);
    margin: 0.25rem 0 1.2rem;
    opacity: 0.5;
}

/* ══════════════════════════════════════
   ── INPUT AREA — HIGH CONTRAST FIX ──
   ══════════════════════════════════════ */

/* Bottom bar: Streamlit pins it to the main column (keeps it aligned with the sidebar open) */
[data-testid="stBottomBlockContainer"], [data-testid="stBottom"] > div {
    background: var(--bg-base) !important;
}

/* Outer wrapper — the rounded box */
[data-testid="stChatInput"] > div {
    background: #1e2028 !important;
    border: 1.5px solid #3a3d52 !important;
    border-radius: 14px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--accent-gold) !important;
    box-shadow: 0 0 0 3px rgba(201,168,76,0.12) !important;
}

/* The actual textarea — MUST be bright white on dark bg */
[data-testid="stChatInput"] textarea {
    background-color: #1e2028 !important;
    color: #ffffff !important;                    /* ← full white text */
    caret-color: var(--accent-gold) !important;   /* ← gold cursor */
    font-size: 0.95rem !important;
    font-weight: 400 !important;
    line-height: 1.6 !important;
    padding: 0.75rem 1rem !important;
    border: none !important;
    outline: none !important;
    resize: none !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #6b6e85 !important;                    /* ← visible but dim placeholder */
        font-size: 0.87rem !important;
}
/* Remove any inner box-shadow / outline Streamlit injects */
[data-testid="stChatInput"] textarea:focus {
    box-shadow: none !important;
    outline: none !important;
    border: none !important;
}

/* Send button */
[data-testid="stChatInput"] button[kind="primaryFormSubmit"],
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, var(--accent-gold), var(--accent-gold-dim)) !important;
    border: none !important;
    border-radius: 9px !important;
    color: var(--bg-base) !important;
    font-weight: 600 !important;
    transition: opacity 0.15s, transform 0.1s !important;
}
[data-testid="stChatInput"] button:hover {
    opacity: 0.88 !important;
    transform: scale(1.04) !important;
}

/* Input hint below bar */
.input-hint {
    text-align: center;
    font-size: 0.65rem;
    color: var(--text-muted);
    margin-top: 0.35rem;
    letter-spacing: 0.04em;
}

/* ── Clear button ── */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-muted) !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    font-family: var(--font-body) !important;
    padding: 0.35rem 0.9rem !important;
    letter-spacing: 0.03em !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    border-color: var(--danger) !important;
    color: var(--danger) !important;
    background: rgba(229,87,87,0.06) !important;
}

/* ── Sidebar: chat history ── */
[data-testid="stSidebar"] {
    background: var(--bg-surface) !important;
    border-right: 1px solid var(--border-subtle) !important;
}
[data-testid="stSidebarContent"] { padding-top: 0.5rem; }

[data-testid="stSidebarUserContent"] { padding: 0 0.9rem 1.5rem !important; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.1rem !important; }
.stApp .sidebar-brand, .stApp .sidebar-brand * { font-family: var(--font-display) !important; }
.sidebar-brand {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
    margin-top: -1.9rem;
    padding: 0 0 1rem;
}
.sidebar-brand .brand-mark {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.35rem;
    font-style: normal;
    color: var(--accent-gold);
    background: radial-gradient(circle at 30% 30%, rgba(212,176,98,0.2), rgba(212,176,98,0.04));
    border: 1px solid rgba(212,176,98,0.4);
}
.sidebar-brand .brand-word {
    font-size: 2rem;
    line-height: 1;
    letter-spacing: 0.01em;
    color: var(--text-primary);
}
.sidebar-brand .brand-ai { color: var(--accent-gold); font-style: italic; }
.history-heading {
    font-size: 0.62rem;
    color: var(--text-muted);
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 1.1rem 0.6rem 0.4rem;
    margin-bottom: 0.3rem;
}
.sidebar-footer {
    font-size: 0.68rem;
    line-height: 1.5;
    color: var(--text-muted);
    border-top: 1px solid var(--border-subtle);
    margin-top: 1.5rem;
    padding: 0.9rem 0.6rem 0;
}
.history-empty { font-size: 0.78rem; color: var(--text-muted); padding: 0.5rem 0.6rem; }
[data-testid="stSidebar"] [data-testid^="stBaseButton"] {
    width: 100% !important;
    justify-content: flex-start !important;
    background: transparent !important;
    color: var(--text-secondary) !important;
    border: 1px solid transparent !important;
    border-radius: 8px !important;
    padding: 0.35rem 0.6rem !important;
    min-height: 0 !important;
    font-size: 0.8rem !important;
}
[data-testid="stSidebar"] [data-testid^="stBaseButton"] p {
    text-align: left !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    font-size: 0.8rem !important;
}
[data-testid="stSidebar"] [data-testid^="stBaseButton"] * {
    justify-content: flex-start !important;
    text-align: left !important;
}
[data-testid="stSidebar"] [data-testid^="stBaseButton"] > div { width: 100% !important; }
[data-testid="stSidebar"] [data-testid^="stBaseButton"] > div,
[data-testid="stSidebar"] [data-testid^="stBaseButton"] [data-testid="stMarkdownContainer"] {
    min-width: 0 !important;
    max-width: 100% !important;
    overflow: hidden !important;
}
[data-testid="stSidebar"] .stTooltipIcon,
[data-testid="stSidebar"] .stTooltipHoverTarget { display: block !important; width: 100% !important; }
[data-testid="stSidebar"] [data-testid^="stBaseButton"]:hover {
    border-color: var(--accent-gold) !important;
    color: var(--accent-gold) !important;
    background: rgba(201,168,76,0.06) !important;
}
.st-key-new_chat { margin-top: 1.1rem !important; }
.st-key-new_chat [data-testid^="stBaseButton"] {
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-primary) !important;
    padding: 0.5rem 0.75rem !important;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
    background: rgba(201,168,76,0.12) !important;
    border-color: rgba(201,168,76,0.35) !important;
    color: var(--text-primary) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-subtle); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-gold-dim); }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex


def new_chat():
    st.session_state.messages = []
    st.session_state.pending = None
    st.session_state.session_id = uuid.uuid4().hex


def open_chat(session_id: str):
    """Load a previous conversation from the backend into the chat view."""
    try:
        res = requests.get(f"{BACKEND_URL}/sessions/{session_id}",
                           params={"user_id": USER_ID}, timeout=10)
        res.raise_for_status()
        rows = res.json()["messages"]
    except Exception as e:
        st.sidebar.error(f"Could not load conversation: {e}")
        return
    messages = []
    for row in rows:
        messages.append({"role": "user", "content": row["query"]})
        messages.append({"role": "assistant", "content": row["response"]})
    st.session_state.messages = messages
    st.session_state.pending = None
    st.session_state.session_id = session_id


def fetch_sessions() -> list:
    try:
        res = requests.get(f"{BACKEND_URL}/sessions", params={"user_id": USER_ID}, timeout=5)
        res.raise_for_status()
        return res.json()["sessions"]
    except Exception:
        return []


def day_group(ts: str) -> str:
    try:
        day = datetime.fromisoformat(ts).date()
    except (TypeError, ValueError):
        return "Earlier"
    delta = (datetime.now().date() - day).days
    return "Today" if delta == 0 else "Yesterday" if delta == 1 else "Earlier"


def render_sidebar():
    """Drawn last, so a just-answered question's chat is already in the history
    without re-running the whole page."""
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand"><span class="brand-mark">⚖</span>'
            '<span class="brand-word">Nyaya<span class="brand-ai">Setu</span></span></div>',
            unsafe_allow_html=True,
        )
        st.button("＋  New chat", key="new_chat", on_click=new_chat, use_container_width=True)
        sessions = fetch_sessions()
        if not sessions:
            st.markdown('<div class="history-heading">Chats</div>'
                        '<div class="history-empty">No conversations yet.</div>', unsafe_allow_html=True)
        current_group = None
        for sess in sessions:
            group = day_group(sess["updated_at"])
            if group != current_group:
                st.markdown(f'<div class="history-heading">{group}</div>', unsafe_allow_html=True)
                current_group = group
            title = " ".join(sess["title"].split())
            st.button(
                title,
                key=f"sess_{sess['session_id']}",
                on_click=open_chat,
                args=(sess["session_id"],),
                type="primary" if sess["session_id"] == st.session_state.session_id else "secondary",
                use_container_width=True,
            )
        st.markdown(
            '<div class="sidebar-footer">Covers the Constitution, BNS, BNSS, CrPC, CPC, Evidence Act, '
            'Negotiable Instruments Act, Divorce Act and Motor Vehicles Act.</div>',
            unsafe_allow_html=True,
        )


def submit(query: str):
    """Show the user's message right away, then fetch the answer on the next run."""
    clean_query = query.lstrip("📜🏛⚖🔒 ")
    st.session_state.messages.append({"role": "user", "content": clean_query})
    st.session_state.pending = clean_query
    st.rerun()

SUGGESTIONS = [
    "What replaced IPC Section 302 for murder?",
    "Explain Article 21, the right to life",
    "How do I apply for bail?",
    "What are my rights if I'm arrested?",
]


def greeting() -> str:
    hour = datetime.now().hour
    return "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"


# ── Landing (new chat) ─────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown(f"""
    <div class="landing">
        <div class="landing-greeting">{greeting()}</div>
        <div class="landing-title">Ask anything about <em>Indian law</em> with <em>NyayaSetu</em></div>
        <div class="landing-sub">Answers grounded in Indian statutes, with the sections cited.</div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(2, gap="small")
    for i, s in enumerate(SUGGESTIONS):
        if cols[i % 2].button(s, key=f"pill_{i}", use_container_width=True):
            submit(s)

    st.markdown(
        '<div class="landing-note">General legal information, not legal advice. '
        'For your specific situation, consult a qualified advocate.</div>',
        unsafe_allow_html=True,
    )

LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+")


def normalize_markdown(text: str) -> str:
    """LLMs indent nested lists by 2-3 spaces and start lists right under a line of
    text; Python-Markdown needs 4-space nesting and a blank line before a list."""
    out = []
    for line in text.replace("\r\n", "\n").split("\n"):
        m = LIST_ITEM.match(line)
        if m:
            indent = len(m.group(1).expandtabs(4))
            if indent:
                line = " " * (4 * max(1, round(indent / 2.5))) + line.lstrip()
            elif out and out[-1].strip() and not LIST_ITEM.match(out[-1]):
                out.append("")
        out.append(line)
    return "\n".join(out)


# ── Render chat history ────────────────────────────────────────────────────────
def agent_html(content: str, streaming: bool = False) -> str:
    rendered = mdlib.markdown(
        normalize_markdown(content),
        extensions=["sane_lists", "tables", "fenced_code"]
    )
    state = " streaming" if streaming else ""
    divider = "" if streaming else '<div class="msg-divider"></div>'
    return f"""
    <div class="msg-row agent">
        <div class="avatar agent">⚖</div>
        <div style="flex:1; min-width:0;">
            <div class="agent-label">NyayaSetu</div>
            <div class="bubble agent{state}">{rendered}</div>
        </div>
    </div>
    {divider}"""


def render_messages():
    for msg in st.session_state.messages:
        role    = msg["role"]
        content = msg["content"]

        if role == "user":
            safe_content = html.escape(content).replace("\n", "<br>")
            st.markdown(f"""
            <div class="msg-row user">
                <div class="bubble user">{safe_content}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(agent_html(content), unsafe_allow_html=True)

render_messages()

# ── Handle API call ────────────────────────────────────────────────────────────
THINKING_HTML = """
<div class="msg-row agent">
    <div class="avatar agent">⚖</div>
    <div style="flex:1;">
        <div class="agent-label">Searching the statutes…</div>
        <div class="thinking">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    </div>
</div>"""

# The LLM can deliver a whole answer in well under a second; reveal it at a steady
# typing pace (~500 chars/s), speeding up when far behind so long answers never drag.
REVEAL_CHARS = 8
REVEAL_DELAY = 0.015
MAX_REVEAL_FRAMES = 150


def stream_answer(clean_query: str, placeholder) -> str:
    """Stream the answer from the backend into `placeholder`; return the full text."""
    buffer, shown = "", 0
    with requests.post(
        f"{BACKEND_URL}/chat/stream",
        json={
            "message": clean_query,
            "user_id": USER_ID,
            "session_id": st.session_state.session_id,
        },
        stream=True,
        timeout=(5, 120),
    ) as res:
        if not res.ok:
            return f"⚠️ **Server error ({res.status_code}).** Please try again."
        for line in res.iter_lines(decode_unicode=True):
            if not line:
                continue
            event = json.loads(line)
            if event["type"] == "error":
                note = f"⚠️ {event.get('detail', 'Something went wrong. Please try again.')}"
                return f"{buffer}\n\n{note}" if buffer else note
            if event["type"] != "token":
                continue
            buffer += event["text"]
            while shown < len(buffer):
                step = max(REVEAL_CHARS, (len(buffer) - shown) // MAX_REVEAL_FRAMES)
                shown = min(len(buffer), shown + step)
                placeholder.markdown(agent_html(buffer[:shown], streaming=True), unsafe_allow_html=True)
                time.sleep(REVEAL_DELAY)
    return buffer or "Sorry, I could not get a response."


def ask(clean_query: str):
    placeholder = st.empty()
    placeholder.markdown(THINKING_HTML, unsafe_allow_html=True)

    try:
        answer = stream_answer(clean_query, placeholder)
    except requests.exceptions.ConnectionError:
        answer = "⚠️ **Cannot connect to backend.** Is the server running on port 8001?"
    except requests.exceptions.Timeout:
        answer = "⚠️ **The server took too long to respond.** Please try again."
    except ValueError:
        answer = "⚠️ **Invalid response from server.** Please try again."
    except Exception as e:
        answer = f"⚠️ **Unexpected error:** {str(e)}"

    placeholder.markdown(agent_html(answer), unsafe_allow_html=True)
    st.session_state.messages.append({"role": "assistant", "content": answer})

# ── Chat input ─────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask a legal question…"):
    submit(prompt)

# ── Answer the pending question (its message is already on screen) ─────────────
if st.session_state.pending:
    query = st.session_state.pending
    st.session_state.pending = None
    ask(query)

render_sidebar()
