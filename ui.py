import streamlit as st
import requests

st.title("Simple RAG App")

file = st.file_uploader("Upload PDF")

if file:
    res = requests.post("http://localhost:8000/upload", files={"file": file})
    st.write(res.json())


question = st.text_input("Ask question")

if st.button("Ask"):
    res = requests.post(
        "http://localhost:8000/chat",
        json={"question": question}
    )

    data = res.json()

    st.write("### Answer")
    st.write(data["answer"])

    st.write("### Sources")
    for s in data["sources"]:
        st.write("-", s)
