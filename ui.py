import streamlit as st
import requests

st.title("📄 AI Document Assistant")

# Upload file
uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file:
    files = {"file": uploaded_file.getvalue()}
    res = requests.post("http://127.0.0.1:8000/upload", files=files)
    st.success("File uploaded!")

# Ask question
question = st.text_input("Ask a question")

if st.button("Ask"):
    res = requests.post(
        "http://127.0.0.1:8000/chat",
        json={"question": question}
    )

    data = res.json()

    st.subheader("Answer")
    st.write(data.get("answer", ""))

    if "sources" in data and data["sources"]:
        st.subheader("Sources")
        for s in data["sources"]:
            st.write("- ", s[:200])  # trim long text
