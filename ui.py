import streamlit as st
import requests

st.set_page_config(layout="wide")

API_URL = "http://localhost:8000"

st.title("📄 RAG Chat + Notes System")

# ================= STATE =================
if "sessions" not in st.session_state:
    st.session_state.sessions = {
        "Chat 1": {"messages": []}
    }

if "active_chat" not in st.session_state:
    st.session_state.active_chat = "Chat 1"

if "notes" not in st.session_state:
    st.session_state.notes = []

if "pinned" not in st.session_state:
    st.session_state.pinned = []

if "reset_note" not in st.session_state:
    st.session_state.reset_note = False

# ================= LAYOUT =================
col1, col2 = st.columns([2, 1])

# ==================================================
# LEFT → UPLOAD + CHAT + CHAT SESSIONS
# ==================================================
with col1:

    st.subheader("📤 Upload PDF")

    file = st.file_uploader("Choose a PDF", type=["pdf"])

    if file:
        if st.button("Upload & Process"):
            with st.spinner("Processing..."):
                res = requests.post(
                    f"{API_URL}/upload",
                    files={"file": file}
                )
            st.success(res.json()["message"])

    st.divider()

    # ================= CHAT SESSIONS =================
    st.subheader("💬 Chats")

    col_new, col_del = st.columns(2)

    with col_new:
        if st.button("➕ New Chat"):
            chat_name = f"Chat {len(st.session_state.sessions) + 1}"
            st.session_state.sessions[chat_name] = {"messages": []}
            st.session_state.active_chat = chat_name
            st.rerun()

    with col_del:
        if st.button("🗑 Delete Chat"):
            if len(st.session_state.sessions) > 1:
                del st.session_state.sessions[st.session_state.active_chat]
                st.session_state.active_chat = list(st.session_state.sessions.keys())[0]
                st.rerun()

    for chat_name in st.session_state.sessions.keys():
        if st.button(chat_name):
            st.session_state.active_chat = chat_name
            st.rerun()

    st.divider()

    # ================= CHAT =================
    chat = st.session_state.sessions[st.session_state.active_chat]["messages"]

    st.subheader(f"💬 {st.session_state.active_chat}")

    for i, msg in enumerate(chat):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

            if st.button("🗑 Delete", key=f"del_msg_{i}"):
                chat.pop(i)
                st.rerun()

    user_input = st.chat_input("Ask something...")

    if user_input:
        chat.append({"role": "user", "content": user_input})

        res = requests.post(
            f"{API_URL}/chat",
            json={"question": user_input}
        ).json()

        chat.append({"role": "assistant", "content": res["answer"]})

        st.rerun()


# ==================================================
# RIGHT → NOTES SYSTEM (FIXED)
# ==================================================
with col2:

    st.subheader("📝 Notes")

    if "notes" not in st.session_state:
        st.session_state.notes = []

    if "pinned" not in st.session_state:
        st.session_state.pinned = []

    # ================= INPUT =================
    with st.form("note_form", clear_on_submit=True):
        note_input = st.text_area("Write notes here")
        submitted = st.form_submit_button("➕ Add Note")

        if submitted and note_input.strip():
            st.session_state.notes.append(note_input)

    st.divider()

    # ================= PINNED =================
    header_p, btn_p = st.columns([3, 1])

    with header_p:
        st.subheader("📌 Pinned")

    with btn_p:
        if st.button("🧹 Clear Pinned"):
            st.session_state.pinned = []
            st.rerun()

    if st.session_state.pinned:
        for i, p in enumerate(st.session_state.pinned):
            c1, c2 = st.columns([4, 1])

            with c1:
                st.write(f"{i+1}. {p}")

            with c2:
                if st.button("🗑", key=f"unpin_{i}"):
                    st.session_state.pinned.pop(i)
                    st.rerun()
    else:
        st.caption("No pinned notes")

    st.divider()

    # ================= NOTES HEADER =================
    header_n, btn_n = st.columns([3, 1])

    with header_n:
        st.subheader("📒 All Notes")

    with btn_n:
        if st.button("🧼 Clear All"):
            st.session_state.notes = []
            st.rerun()

    # ================= NOTES LIST =================
    for i, n in enumerate(st.session_state.notes):
        c1, c2, c3 = st.columns([4, 1, 1])

        with c1:
            st.write(f"{i+1}. {n}")

        with c2:
            if st.button("🗑", key=f"del_note_{i}"):
                st.session_state.notes.pop(i)
                st.rerun()

        with c3:
            if st.button("📌", key=f"pin_note_{i}"):
                st.session_state.pinned.append(n)
                st.rerun()
