# streamlit run ui.py
import streamlit as st
import requests
import os
import json
import shutil
import base64


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="RAG Chat + Notes",
    layout="wide"
)

API_URL = "http://localhost:8000"

LIBRARY_DIR = "document_library"

LIBRARY_FILE = os.path.join(
    LIBRARY_DIR,
    "library.json"
)

os.makedirs(
    LIBRARY_DIR,
    exist_ok=True
)


# =========================================================
# DOCUMENT LIBRARY FUNCTIONS
# =========================================================

def load_library():

    if not os.path.exists(LIBRARY_FILE):

        library = {
            "folders": {
                "Root": []
            }
        }

        save_library(library)

        return library

    try:

        with open(
            LIBRARY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            library = json.load(f)

        # Make sure folders key exists
        if "folders" not in library:

            library["folders"] = {
                "Root": []
            }

        # Make sure Root exists
        if "Root" not in library["folders"]:

            library["folders"]["Root"] = []

        return library

    except Exception:

        return {
            "folders": {
                "Root": []
            }
        }


def save_library(library):

    os.makedirs(
        LIBRARY_DIR,
        exist_ok=True
    )

    with open(
        LIBRARY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            library,
            f,
            indent=4
        )


# =========================================================
# REFRESH LIBRARY FROM ACTUAL FILESYSTEM
# =========================================================

def refresh_library_from_filesystem():

    """
    Scans document_library and updates library.json.

    This allows you to manually put PDFs inside:

        document_library/
        ├── Machine Learning/
        │   ├── regression.pdf
        │   └── svm.pdf
        │
        └── DBMS/
            └── dbms.pdf

    and Streamlit will detect them.
    """

    library = {
        "folders": {
            "Root": []
        }
    }

    # -----------------------------------------------------
    # PDFs directly inside document_library
    # -----------------------------------------------------

    for file_name in os.listdir(LIBRARY_DIR):

        file_path = os.path.join(
            LIBRARY_DIR,
            file_name
        )

        if os.path.isfile(file_path):

            if file_name.lower().endswith(".pdf"):

                library["folders"]["Root"].append(
                    file_name
                )


    # -----------------------------------------------------
    # FOLDERS
    # -----------------------------------------------------

    for folder_name in os.listdir(LIBRARY_DIR):

        folder_path = os.path.join(
            LIBRARY_DIR,
            folder_name
        )

        if not os.path.isdir(folder_path):
            continue

        # Don't include hidden folders
        if folder_name.startswith("."):
            continue

        pdf_files = []

        for file_name in os.listdir(folder_path):

            file_path = os.path.join(
                folder_path,
                file_name
            )

            if os.path.isfile(file_path):

                if file_name.lower().endswith(".pdf"):

                    pdf_files.append(
                        file_name
                    )

        # Don't duplicate Root
        if folder_name != "Root":

            library["folders"][folder_name] = sorted(
                pdf_files
            )


    # Sort Root
    library["folders"]["Root"] = sorted(
        library["folders"]["Root"]
    )


    save_library(
        library
    )

    return library


def create_folder(folder_name):

    library = load_library()

    folder_name = folder_name.strip()

    if not folder_name:

        return False

    if folder_name in library["folders"]:

        return False

    library["folders"][folder_name] = []

    folder_path = os.path.join(
        LIBRARY_DIR,
        folder_name
    )

    os.makedirs(
        folder_path,
        exist_ok=True
    )

    save_library(
        library
    )

    return True


def save_uploaded_document(
    uploaded_file,
    folder_name
):

    library = load_library()

    if folder_name not in library["folders"]:

        create_folder(
            folder_name
        )

        library = load_library()


    # -----------------------------------------------------
    # ROOT
    # -----------------------------------------------------

    if folder_name == "Root":

        folder_path = LIBRARY_DIR

    else:

        folder_path = os.path.join(
            LIBRARY_DIR,
            folder_name
        )


    os.makedirs(
        folder_path,
        exist_ok=True
    )


    file_path = os.path.join(
        folder_path,
        uploaded_file.name
    )


    with open(
        file_path,
        "wb"
    ) as f:

        f.write(
            uploaded_file.getbuffer()
        )


    # -----------------------------------------------------
    # UPDATE LIBRARY JSON
    # -----------------------------------------------------

    if uploaded_file.name not in library["folders"][folder_name]:

        library["folders"][folder_name].append(
            uploaded_file.name
        )


    save_library(
        library
    )


    return file_path


def delete_document(
    folder_name,
    file_name
):

    library = load_library()


    # -----------------------------------------------------
    # ROOT
    # -----------------------------------------------------

    if folder_name == "Root":

        file_path = os.path.join(
            LIBRARY_DIR,
            file_name
        )

    else:

        file_path = os.path.join(
            LIBRARY_DIR,
            folder_name,
            file_name
        )


    if os.path.exists(file_path):

        os.remove(
            file_path
        )


    if folder_name in library["folders"]:

        if file_name in library["folders"][folder_name]:

            library["folders"][folder_name].remove(
                file_name
            )


    save_library(
        library
    )


def delete_folder(folder_name):

    if folder_name == "Root":

        return


    library = load_library()


    folder_path = os.path.join(
        LIBRARY_DIR,
        folder_name
    )


    if os.path.exists(folder_path):

        shutil.rmtree(
            folder_path
        )


    if folder_name in library["folders"]:

        del library["folders"][folder_name]


    save_library(
        library
    )


# =========================================================
# GET FILE PATH
# =========================================================

def get_document_path(
    folder_name,
    file_name
):

    if folder_name == "Root":

        return os.path.join(
            LIBRARY_DIR,
            file_name
        )

    return os.path.join(
        LIBRARY_DIR,
        folder_name,
        file_name
    )


# =========================================================
# SEND EXISTING LOCAL PDF TO FASTAPI
# =========================================================

def process_existing_pdf(
    file_path
):

    """
    Takes an existing PDF from document_library
    and sends it to the FastAPI /upload endpoint.

    The user does NOT have to manually upload it again.
    """

    if not os.path.exists(file_path):

        return (
            False,
            "PDF file not found."
        )


    try:

        with open(
            file_path,
            "rb"
        ) as pdf_file:

            pdf_bytes = pdf_file.read()


        response = requests.post(
            f"{API_URL}/upload",
            files={
                "file": (
                    os.path.basename(file_path),
                    pdf_bytes,
                    "application/pdf"
                )
            },
            timeout=300
        )


        if response.status_code != 200:

            return (
                False,
                f"Backend upload failed:\n{response.text}"
            )


        try:

            data = response.json()

            message = data.get(
                "message",
                "PDF processed successfully."
            )

        except Exception:

            message = (
                "PDF processed successfully."
            )


        return (
            True,
            message
        )


    except requests.exceptions.ConnectionError:

        return (
            False,
            "❌ Cannot connect to FastAPI.\n\n"
            "Make sure the backend is running on:\n"
            "http://localhost:8000"
        )


    except requests.exceptions.Timeout:

        return (
            False,
            "❌ Request timed out while "
            "processing the PDF."
        )


    except Exception as e:

        return (
            False,
            f"❌ Error: {str(e)}"
        )


# =========================================================
# SEND NEW UPLOADED PDF TO FASTAPI
# =========================================================

def process_uploaded_pdf(
    uploaded_file
):

    try:

        response = requests.post(
            f"{API_URL}/upload",
            files={
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "application/pdf"
                )
            },
            timeout=300
        )


        if response.status_code != 200:

            return (
                False,
                f"Backend upload failed:\n{response.text}"
            )


        try:

            data = response.json()

            message = data.get(
                "message",
                "PDF processed successfully."
            )

        except Exception:

            message = (
                "PDF processed successfully."
            )


        return (
            True,
            message
        )


    except requests.exceptions.ConnectionError:

        return (
            False,
            "❌ Cannot connect to FastAPI.\n\n"
            "Make sure the backend is running on:\n"
            "http://localhost:8000"
        )


    except requests.exceptions.Timeout:

        return (
            False,
            "❌ Request timed out."
        )


    except Exception as e:

        return (
            False,
            f"❌ Error: {str(e)}"
        )


# =========================================================
# RESET RAG MEMORY
# =========================================================

def reset_document_memory():

    try:

        response = requests.post(
            f"{API_URL}/reset-vectorstore",
            timeout=60
        )


        if response.status_code == 200:

            try:

                return (
                    True,
                    response.json().get(
                        "message",
                        "Document memory reset."
                    )
                )

            except Exception:

                return (
                    True,
                    "Document memory reset."
                )


        return (
            False,
            response.text
        )


    except requests.exceptions.ConnectionError:

        return (
            False,
            "❌ Cannot connect to FastAPI."
        )


    except Exception as e:

        return (
            False,
            str(e)
        )


# =========================================================
# CREATE CHAT FOR FILE
# =========================================================

def create_chat_for_file(
    file_name
):

    # -----------------------------------------------------
    # REMOVE EMPTY DEFAULT CHAT
    # -----------------------------------------------------

    default_chat = "Chat - Default"


    if default_chat in st.session_state.sessions:

        default_messages = (
            st.session_state
            .sessions[default_chat]["messages"]
        )


        if len(default_messages) == 0:

            del st.session_state.sessions[
                default_chat
            ]


    # -----------------------------------------------------
    # CREATE UNIQUE CHAT NAME
    # -----------------------------------------------------

    base_name = (
        f"Chat - {file_name}"
    )


    chat_name = base_name

    counter = 1


    while chat_name in st.session_state.sessions:

        chat_name = (
            f"{base_name} ({counter})"
        )

        counter += 1


    # -----------------------------------------------------
    # CREATE CHAT
    # -----------------------------------------------------

    st.session_state.sessions[
        chat_name
    ] = {
        "messages": []
    }


    st.session_state.active_chat = (
        chat_name
    )


# =========================================================
# PDF VIEWER
# =========================================================

def display_pdf(
    file_path
):

    if not os.path.exists(file_path):

        st.error(
            "PDF file not found."
        )

        return


    try:

        with open(
            file_path,
            "rb"
        ) as pdf_file:

            pdf_bytes = pdf_file.read()


        base64_pdf = base64.b64encode(
            pdf_bytes
        ).decode("utf-8")


        pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="750"
            style="border: 1px solid #ccc; border-radius: 8px;"
            type="application/pdf">
        </iframe>
        """


        st.markdown(
            pdf_display,
            unsafe_allow_html=True
        )


    except Exception as e:

        st.error(
            f"Unable to display PDF: {str(e)}"
        )


# =========================================================
# SESSION STATE
# =========================================================

if "sessions" not in st.session_state:

    st.session_state.sessions = {
        "Chat - Default": {
            "messages": []
        }
    }


if "active_chat" not in st.session_state:

    st.session_state.active_chat = (
        "Chat - Default"
    )


if "notes" not in st.session_state:

    st.session_state.notes = []


if "pinned" not in st.session_state:

    st.session_state.pinned = []


if "uploaded_file_name" not in st.session_state:

    st.session_state.uploaded_file_name = None


# =========================================================
# CURRENT SESSION DOCUMENT
# =========================================================

if "current_document" not in st.session_state:

    st.session_state.current_document = None


# =========================================================
# PDF VIEWER STATE
# =========================================================

if "viewing_file" not in st.session_state:

    st.session_state.viewing_file = None


if "viewing_file_name" not in st.session_state:

    st.session_state.viewing_file_name = None


# =========================================================
# PAGE TITLE
# =========================================================

st.title(
    "📄 RAG Chat + Notes System"
)


# =========================================================
# MAIN LAYOUT
# =========================================================

col1, col2 = st.columns(
    [2, 1]
)


# =========================================================
# LEFT COLUMN
# =========================================================

with col1:

    # =====================================================
    # DOCUMENT LIBRARY
    # =====================================================

    st.subheader(
        "📚 Document Library"
    )


    library = load_library()


    # =====================================================
    # REFRESH LIBRARY
    # =====================================================

    if st.button(
        "🔄 Refresh Library",
        key="refresh_library"
    ):

        refresh_library_from_filesystem()

        st.success(
            "Library refreshed."
        )

        st.rerun()


    st.caption(
        "Files already present inside "
        "`document_library/` can be used directly."
    )


    # =====================================================
    # CREATE FOLDER
    # =====================================================

    with st.expander(
        "➕ Create Folder"
    ):

        new_folder = st.text_input(
            "Folder name",
            placeholder="e.g. Machine Learning",
            key="new_folder_name"
        )


        if st.button(
            "Create Folder",
            key="create_folder"
        ):

            if not new_folder.strip():

                st.warning(
                    "Please enter a folder name."
                )

            else:

                success = create_folder(
                    new_folder
                )


                if success:

                    st.success(
                        f"Folder '{new_folder.strip()}' created."
                    )

                    st.rerun()

                else:

                    st.warning(
                        "A folder with this name already exists."
                    )


    st.divider()


    # =====================================================
    # DISPLAY DOCUMENT LIBRARY
    # =====================================================

    library = load_library()


    for folder_name, files in library[
        "folders"
    ].items():


        # -------------------------------------------------
        # FOLDER ICON
        # -------------------------------------------------

        if folder_name == "Root":

            icon = "📂"

        else:

            icon = "📁"


        with st.expander(
            f"{icon} {folder_name} ({len(files)})"
        ):


            # =================================================
            # FILES
            # =================================================

            if files:


                for file_name in files:


                    file_path = get_document_path(
                        folder_name,
                        file_name
                    )


                    # -----------------------------------------
                    # FILE ROW
                    # -----------------------------------------

                    file_col, view_col, use_col, download_col, delete_col = st.columns(
                        [3.3, 1.1, 1.1, 1.5, 0.7]
                    )


                    # -----------------------------------------
                    # FILE NAME
                    # -----------------------------------------

                    with file_col:

                        st.write(
                            f"📄 {file_name}"
                        )


                    # -----------------------------------------
                    # VIEW
                    # -----------------------------------------

                    with view_col:

                        if st.button(
                            "👁️",
                            key=f"view_{folder_name}_{file_name}",
                            help="View PDF"
                        ):


                            if os.path.exists(file_path):

                                st.session_state.viewing_file = (
                                    file_path
                                )

                                st.session_state.viewing_file_name = (
                                    file_name
                                )

                                st.rerun()

                            else:

                                st.error(
                                    "File not found."
                                )


                    # -----------------------------------------
                    # USE EXISTING FILE
                    # -----------------------------------------

                    with use_col:

                        if st.button(
                            "🧠 Use",
                            key=f"use_{folder_name}_{file_name}",
                            help="Use this existing PDF in current session"
                        ):


                            if not os.path.exists(
                                file_path
                            ):

                                st.error(
                                    "File not found."
                                )

                            else:

                                with st.spinner(
                                    f"Using {file_name}..."
                                ):


                                    # --------------------------------
                                    # RESET OLD RAG MEMORY
                                    # --------------------------------

                                    reset_success, reset_message = (
                                        reset_document_memory()
                                    )


                                    if not reset_success:

                                        st.error(
                                            reset_message
                                        )

                                        st.stop()


                                    # --------------------------------
                                    # PROCESS EXISTING FILE
                                    # --------------------------------

                                    success, message = (
                                        process_existing_pdf(
                                            file_path
                                        )
                                    )


                                    if success:


                                        # ----------------------------
                                        # CURRENT DOCUMENT
                                        # ----------------------------

                                        st.session_state.current_document = {
                                            "name": file_name,
                                            "folder": folder_name,
                                            "path": file_path,
                                            "temporary": False
                                        }


                                        st.session_state.uploaded_file_name = (
                                            file_name
                                        )


                                        # ----------------------------
                                        # CREATE CHAT
                                        # ----------------------------

                                        create_chat_for_file(
                                            file_name
                                        )


                                        st.success(
                                            f"📄 {file_name} "
                                            "is now being used."
                                        )


                                        st.rerun()


                                    else:

                                        st.error(
                                            message
                                        )


                    # -----------------------------------------
                    # DOWNLOAD
                    # -----------------------------------------

                    with download_col:

                        if os.path.exists(
                            file_path
                        ):

                            try:

                                with open(
                                    file_path,
                                    "rb"
                                ) as pdf_file:

                                    pdf_bytes = (
                                        pdf_file.read()
                                    )


                                st.download_button(
                                    label="⬇️ Download",
                                    data=pdf_bytes,
                                    file_name=file_name,
                                    mime="application/pdf",
                                    key=f"download_{folder_name}_{file_name}"
                                )


                            except Exception as e:

                                st.error(
                                    f"Error: {e}"
                                )

                        else:

                            st.warning(
                                "Missing"
                            )


                    # -----------------------------------------
                    # DELETE
                    # -----------------------------------------

                    with delete_col:

                        if st.button(
                            "🗑️",
                            key=f"delete_file_{folder_name}_{file_name}",
                            help="Delete PDF"
                        ):


                            # Close viewer if this file
                            # is currently being viewed

                            if (
                                st.session_state.viewing_file
                                == file_path
                            ):

                                st.session_state.viewing_file = (
                                    None
                                )

                                st.session_state.viewing_file_name = (
                                    None
                                )


                            # Remove current document
                            # if it is this file

                            current_document = (
                                st.session_state.current_document
                            )


                            if current_document:

                                if (
                                    current_document["path"]
                                    == file_path
                                ):

                                    st.session_state.current_document = (
                                        None
                                    )


                            delete_document(
                                folder_name,
                                file_name
                            )


                            st.rerun()


            else:

                st.caption(
                    "This folder is empty."
                )


            # =================================================
            # DELETE FOLDER
            # =================================================

            if folder_name != "Root":

                st.divider()


                if st.button(
                    "🗑️ Delete Folder",
                    key=f"delete_folder_{folder_name}"
                ):


                    # Close viewer if file belongs
                    # to this folder

                    viewing_file = (
                        st.session_state.viewing_file
                    )


                    if viewing_file:

                        folder_path = os.path.join(
                            LIBRARY_DIR,
                            folder_name
                        )


                        if viewing_file.startswith(
                            folder_path
                        ):

                            st.session_state.viewing_file = (
                                None
                            )

                            st.session_state.viewing_file_name = (
                                None
                            )


                    # Delete current document
                    current_document = (
                        st.session_state.current_document
                    )


                    if current_document:

                        if (
                            current_document["folder"]
                            == folder_name
                        ):

                            st.session_state.current_document = (
                                None
                            )


                    delete_folder(
                        folder_name
                    )


                    st.rerun()


    # =====================================================
    # CURRENT DOCUMENT
    # =====================================================

    st.divider()

    st.subheader(
        "🧠 Current Document"
    )


    current_document = (
        st.session_state.current_document
    )


    if current_document:

        if current_document["temporary"]:

            st.info(
                f"⚡ {current_document['name']}\n\n"
                "Current Session Only"
            )

        else:

            st.info(
                f"📚 {current_document['folder']} / "
                f"{current_document['name']}"
            )

    else:

        st.caption(
            "No document selected."
        )


    # =====================================================
    # PDF VIEWER
    # =====================================================

    if st.session_state.viewing_file:

        st.divider()


        viewer_header, viewer_close = st.columns(
            [5, 1]
        )


        with viewer_header:

            st.subheader(
                f"📖 {st.session_state.viewing_file_name}"
            )


        with viewer_close:

            if st.button(
                "✖ Close",
                key="close_pdf"
            ):

                st.session_state.viewing_file = None

                st.session_state.viewing_file_name = None

                st.rerun()


        display_pdf(
            st.session_state.viewing_file
        )


    st.divider()


    # =====================================================
    # UPLOAD PDF
    # =====================================================

    st.subheader(
        "📤 Upload New PDF"
    )


    file = st.file_uploader(
        "Choose a PDF",
        type=["pdf"],
        key="pdf_uploader"
    )


    if file:


        st.markdown(
            f"**Selected file:** `{file.name}`"
        )


        # =================================================
        # UPLOAD MODE
        # =================================================

        upload_mode = st.radio(
            "What do you want to do with this PDF?",
            [
                "💾 Save in Library + Use",
                "⚡ Use only in Current Session"
            ],
            key="upload_mode"
        )


        # =================================================
        # SAVE IN LIBRARY
        # =================================================

        if upload_mode == (
            "💾 Save in Library + Use"
        ):


            library = load_library()


            folder_options = list(
                library["folders"].keys()
            )


            selected_folder = st.selectbox(
                "Save document in",
                folder_options,
                key="upload_folder"
            )


            if st.button(
                "💾 Save & Use",
                key="save_and_use"
            ):


                with st.spinner(
                    "Processing PDF..."
                ):


                    # -------------------------------------
                    # RESET PREVIOUS RAG MEMORY
                    # -------------------------------------

                    reset_success, reset_message = (
                        reset_document_memory()
                    )


                    if not reset_success:

                        st.error(
                            reset_message
                        )

                        st.stop()


                    # -------------------------------------
                    # PROCESS PDF
                    # -------------------------------------

                    success, message = (
                        process_uploaded_pdf(
                            file
                        )
                    )


                    if not success:

                        st.error(
                            message
                        )

                        st.stop()


                    # -------------------------------------
                    # SAVE TO LIBRARY
                    # -------------------------------------

                    file_path = (
                        save_uploaded_document(
                            file,
                            selected_folder
                        )
                    )


                    # -------------------------------------
                    # CURRENT DOCUMENT
                    # -------------------------------------

                    st.session_state.current_document = {
                        "name": file.name,
                        "folder": selected_folder,
                        "path": file_path,
                        "temporary": False
                    }


                    st.session_state.uploaded_file_name = (
                        file.name
                    )


                    # -------------------------------------
                    # CREATE CHAT
                    # -------------------------------------

                    create_chat_for_file(
                        file.name
                    )


                    st.success(
                        "✅ PDF saved to library "
                        "and added to current session."
                    )


                    st.rerun()


        # =================================================
        # CURRENT SESSION ONLY
        # =================================================

        else:


            st.info(
                "This PDF will be used for the current "
                "session only. It will NOT be saved "
                "inside document_library."
            )


            if st.button(
                "⚡ Use in Current Session",
                key="use_current_session"
            ):


                with st.spinner(
                    "Processing PDF..."
                ):


                    # -------------------------------------
                    # RESET PREVIOUS RAG MEMORY
                    # -------------------------------------

                    reset_success, reset_message = (
                        reset_document_memory()
                    )


                    if not reset_success:

                        st.error(
                            reset_message
                        )

                        st.stop()


                    # -------------------------------------
                    # PROCESS PDF
                    # -------------------------------------

                    success, message = (
                        process_uploaded_pdf(
                            file
                        )
                    )


                    if not success:

                        st.error(
                            message
                        )

                        st.stop()


                    # -------------------------------------
                    # DO NOT SAVE FILE
                    # -------------------------------------

                    st.session_state.current_document = {
                        "name": file.name,
                        "folder": "Current Session",
                        "path": None,
                        "temporary": True
                    }


                    st.session_state.uploaded_file_name = (
                        file.name
                    )


                    # -------------------------------------
                    # CREATE CHAT
                    # -------------------------------------

                    create_chat_for_file(
                        file.name
                    )


                    st.success(
                        "⚡ PDF is being used only "
                        "in the current session."
                    )


                    st.rerun()


    st.divider()


    # =====================================================
    # MEMORY CONTROL
    # =====================================================

    st.subheader(
        "🧹 Memory Control"
    )


    if st.button(
        "🧹 Reset Document Memory",
        key="reset_memory"
    ):


        success, message = (
            reset_document_memory()
        )


        if success:

            st.session_state.current_document = None

            st.success(
                message
            )

        else:

            st.error(
                message
            )


    st.divider()


    # =====================================================
    # CHAT SESSIONS
    # =====================================================

    st.subheader(
        "💬 Chats"
    )


    col_new, col_del = st.columns(
        2
    )


    # =====================================================
    # NEW CHAT
    # =====================================================

    with col_new:

        if st.button(
            "➕ New Chat",
            key="new_chat"
        ):


            file_name = (
                st.session_state.uploaded_file_name
                or "No File"
            )


            base_name = (
                f"Chat - {file_name}"
            )


            counter = 1

            chat_name = base_name


            while chat_name in st.session_state.sessions:

                chat_name = (
                    f"{base_name} ({counter})"
                )

                counter += 1


            st.session_state.sessions[
                chat_name
            ] = {
                "messages": []
            }


            st.session_state.active_chat = (
                chat_name
            )


            st.rerun()


    # =====================================================
    # DELETE CHAT
    # =====================================================

    with col_del:

        if st.button(
            "🗑️ Delete Chat",
            key="delete_chat"
        ):


            if len(
                st.session_state.sessions
            ) > 1:


                del st.session_state.sessions[
                    st.session_state.active_chat
                ]


                st.session_state.active_chat = (
                    list(
                        st.session_state.sessions.keys()
                    )[0]
                )


                st.rerun()


            else:

                st.warning(
                    "At least one chat must remain."
                )


    # =====================================================
    # SWITCH CHATS
    # =====================================================

    for chat_name in list(
        st.session_state.sessions.keys()
    ):


        if st.button(
            chat_name,
            key=f"chat_button_{chat_name}"
        ):


            st.session_state.active_chat = (
                chat_name
            )


            st.rerun()


    st.divider()


    # =====================================================
    # ACTIVE CHAT
    # =====================================================

    chat = (
        st.session_state
        .sessions[
            st.session_state.active_chat
        ]["messages"]
    )


    st.subheader(
        f"💬 {st.session_state.active_chat}"
    )


    # =====================================================
    # DISPLAY CHAT MESSAGES
    # =====================================================

    for i, msg in enumerate(chat):


        with st.chat_message(
            msg["role"]
        ):


            st.write(
                msg["content"]
            )


            # ---------------------------------------------
            # DELETE MESSAGE
            # ---------------------------------------------

            if st.button(
                "🗑️ Delete",
                key=f"del_msg_{i}"
            ):


                chat.pop(i)

                st.rerun()


            # ---------------------------------------------
            # SAVE ASSISTANT MESSAGE TO NOTES
            # ---------------------------------------------

            if msg["role"] == "assistant":


                if st.button(
                    "📝 Save to Notes",
                    key=f"save_note_{i}"
                ):


                    question = None


                    # Find previous user question

                    for j in range(
                        i - 1,
                        -1,
                        -1
                    ):


                        if chat[j]["role"] == "user":

                            question = (
                                chat[j]["content"]
                            )

                            break


                    qa_note = (
                        f"Q: {question}\n"
                        f"A: {msg['content']}"
                    )


                    st.session_state.notes.append(
                        qa_note
                    )


                    st.success(
                        "Saved to notes ✔"
                    )


    # =====================================================
    # CHAT INPUT
    # =====================================================

    user_input = st.chat_input(
        "Ask something..."
    )


    if user_input:


        # ---------------------------------------------
        # CHECK DOCUMENT
        # ---------------------------------------------

        if st.session_state.current_document is None:

            st.warning(
                "Please select or upload a PDF first."
            )

            st.stop()


        # ---------------------------------------------
        # USER MESSAGE
        # ---------------------------------------------

        chat.append(
            {
                "role": "user",
                "content": user_input
            }
        )


        try:


            # -----------------------------------------
            # SEND QUESTION
            # -----------------------------------------

            res = requests.post(
                f"{API_URL}/chat",
                json={
                    "question": user_input
                },
                timeout=300
            )


            # -----------------------------------------
            # HANDLE ERROR
            # -----------------------------------------

            if res.status_code != 200:


                chat.append(
                    {
                        "role": "assistant",
                        "content": (
                            f"❌ Backend error:\n"
                            f"{res.text}"
                        )
                    }
                )


            else:


                response_data = (
                    res.json()
                )


                # -------------------------------------
                # ASSISTANT RESPONSE
                # -------------------------------------

                chat.append(
                    {
                        "role": "assistant",
                        "content": response_data[
                            "answer"
                        ]
                    }
                )


        except requests.exceptions.ConnectionError:


            chat.append(
                {
                    "role": "assistant",
                    "content": (
                        "❌ Cannot connect to FastAPI.\n"
                        "Make sure the backend is running."
                    )
                }
            )


        except requests.exceptions.Timeout:


            chat.append(
                {
                    "role": "assistant",
                    "content": (
                        "❌ Request timed out."
                    )
                }
            )


        except Exception as e:


            chat.append(
                {
                    "role": "assistant",
                    "content": (
                        f"❌ Error: {str(e)}"
                    )
                }
            )


        st.rerun()


# =========================================================
# RIGHT COLUMN → NOTES
# =========================================================

with col2:


    st.subheader(
        "📝 Notes"
    )


    # =====================================================
    # ADD MANUAL NOTE
    # =====================================================

    with st.form(
        "note_form",
        clear_on_submit=True
    ):


        note_input = st.text_area(
            "Write notes here"
        )


        submitted = st.form_submit_button(
            "➕ Add Note"
        )


        if submitted and note_input.strip():


            st.session_state.notes.append(
                note_input.strip()
            )


            st.success(
                "Note added ✔"
            )


    st.divider()


    # =====================================================
    # PINNED NOTES
    # =====================================================

    header_p, btn_p = st.columns(
        [3, 1]
    )


    with header_p:

        st.subheader(
            "📌 Pinned"
        )


    with btn_p:

        if st.button(
            "🧹 Clear Pinned",
            key="clear_pinned"
        ):

            st.session_state.pinned = []

            st.rerun()


    if st.session_state.pinned:


        for i, p in enumerate(
            st.session_state.pinned
        ):


            c1, c2 = st.columns(
                [4, 1]
            )


            with c1:

                st.write(
                    f"{i + 1}. {p}"
                )


            with c2:

                if st.button(
                    "🗑️",
                    key=f"unpin_{i}"
                ):


                    st.session_state.pinned.pop(
                        i
                    )

                    st.rerun()


    else:

        st.caption(
            "No pinned notes"
        )


    st.divider()


    # =====================================================
    # ALL NOTES
    # =====================================================

    header_n, btn_n = st.columns(
        [3, 1]
    )


    with header_n:

        st.subheader(
            "📒 All Notes"
        )


    with btn_n:

        if st.button(
            "🧼 Clear All",
            key="clear_notes"
        ):


            st.session_state.notes = []

            st.rerun()


    if st.session_state.notes:


        for i, n in enumerate(
            st.session_state.notes
        ):


            c1, c2, c3 = st.columns(
                [4, 1, 1]
            )


            with c1:

                st.write(
                    f"{i + 1}. {n}"
                )


            # -----------------------------------------
            # DELETE NOTE
            # -----------------------------------------

            with c2:

                if st.button(
                    "🗑️",
                    key=f"del_note_{i}"
                ):


                    st.session_state.notes.pop(
                        i
                    )

                    st.rerun()


            # -----------------------------------------
            # PIN NOTE
            # -----------------------------------------

            with c3:

                if st.button(
                    "📌",
                    key=f"pin_note_{i}"
                ):


                    if n not in st.session_state.pinned:

                        st.session_state.pinned.append(
                            n
                        )


                    st.rerun()


    else:

        st.caption(
            "No notes yet."
        )
