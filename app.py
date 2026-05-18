import streamlit as st
import pandas as pd
from extractor import extract_text_from_pdf
from syllabus_parser import parse_syllabus_structure
from distribution import distribute_questions
from ai_engine import generate_questions
from pdf_export import generate_pdf
from utils import get_available_ollama_models
import os

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ExamForge - AI Question Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global styles ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Outfit', sans-serif; 
    }

    /* Background and gradients */
    .stApp {
        background: linear-gradient(135deg, #0f1117 0%, #151824 100%);
    }

    h1, h2, h3 {
        background: linear-gradient(90deg, #818cf8 0%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background-color: #1e2130;
        border-radius: 8px 8px 0 0;
        border: 1px solid #ffffff10;
        border-bottom: none;
    }
    
    /* Input and Cards styling */
    .stCard {
        background: rgba(30, 33, 48, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    .stCard:hover {
        border-color: rgba(129, 140, 248, 0.5);
        box-shadow: 0 8px 32px rgba(129, 140, 248, 0.1);
        transform: translateY(-2px);
    }

    /* Status Dots */
    .status-dot {
        display: inline-block;
        width: 9px; height: 9px;
        border-radius: 50%;
        margin-right: 6px;
        vertical-align: middle;
    }
    .dot-green { background:#10b981; box-shadow:0 0 8px #10b98188; }
    .dot-red   { background:#ef4444; box-shadow:0 0 8px #ef444488; }
    .dot-blue  { background:#6366f1; box-shadow:0 0 8px #6366f188; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: rgba(15, 17, 23, 0.95);
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
        border: none;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: opacity 0.2s;
    }
    .stButton > button:hover {
        opacity: 0.9;
        color: white;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ─────────────────────────────────────────────────────
DEFAULTS = {
    "syllabus_text": "",
    "topics": [],
    "generated_questions": [],
    "exam_name": "Midterm Examination",
    "subject_name": "Computer Science",
    "difficulty": "Medium",
    "marks_distribution": pd.DataFrame({"Marks": [5, 10], "Questions": [4, 2]}),
    "use_openai": False,
    "openai_key": "",
    "openai_model": "gpt-4o-mini",
    "ollama_model": "",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Rich UI: Display Logo
    if os.path.exists("logo.png"):
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.image("logo.png", use_container_width=True)
            
    st.markdown("<h2 style='text-align: center; margin-top: -10px;'>ExamForge</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>AI-Powered Question Generator</p>", unsafe_allow_html=True)
    st.divider()

    st.toggle(
        "Use OpenAI API Key",
        key="use_openai",
        help="Turn on to use the OpenAI cloud API instead of the local Ollama model."
    )

    if st.session_state.use_openai:
        st.markdown('<span class="status-dot dot-blue"></span>**OpenAI (Cloud)**', unsafe_allow_html=True)
        st.text_input(
            "OpenAI API Key",
            key="openai_key",
            type="password",
            placeholder="sk-...",
            help="Your key is never stored or sent anywhere except the OpenAI API."
        )
        st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], key="openai_model")
        
        if st.session_state.openai_key:
            st.success("API key entered.")
        else:
            st.warning("Enter your OpenAI API key to continue.")

    else:
        available_models = get_available_ollama_models()
        if available_models:
            st.markdown('<span class="status-dot dot-green"></span>**Ollama — Running**', unsafe_allow_html=True)
            if st.session_state.get("ollama_model") not in available_models:
                st.session_state["ollama_model"] = available_models[0]
                
            st.selectbox(
                "Local model",
                options=available_models,
                key="ollama_model",
                help="Models installed in your local Ollama instance."
            )
            st.caption(f"Using `{st.session_state.ollama_model}` locally.")
        else:
            st.markdown('<span class="status-dot dot-red"></span>**Ollama — Not detected**', unsafe_allow_html=True)
            st.error("Ollama is not reachable.\n\n`ollama serve`")
            st.session_state["ollama_model"] = ""

    st.divider()
    st.caption("v2.5 · Rich UI Edition")

# ── Guard: ensure a model is ready ────────────────────────────────────────────
_use_openai = st.session_state.use_openai
ready = (
    (_use_openai and st.session_state.get("openai_key"))
    or (not _use_openai and st.session_state.get("ollama_model"))
)

if not ready:
    st.title("Welcome to ExamForge")
    st.info("Welcome! Please configure your AI backend in the sidebar to begin.")
    st.stop()

# ── Helper: build shared AI kwargs ────────────────────────────────────────────
def ai_kwargs() -> dict:
    return {
        "use_openai":   st.session_state.use_openai,
        "openai_key":   st.session_state.get("openai_key", ""),
        "openai_model": st.session_state.get("openai_model", "gpt-4o-mini"),
        "ollama_model": st.session_state.get("ollama_model", ""),
    }

# ── Main content ───────────────────────────────────────────────────────────────
st.title("ExamForge")
st.markdown("#### Generate professional exam papers in seconds")

if _use_openai:
    st.caption(f"Backend: OpenAI ({st.session_state.get('openai_model')})")
else:
    st.caption(f"Backend: Local Ollama ({st.session_state.get('ollama_model')})")

tab1, tab2, tab3, tab4 = st.tabs(["1. Upload", "2. Configuration", "3. Generated Paper", "4. Export"])

with tab1:
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    st.header("Upload Syllabus PDF")
    st.markdown("Upload your syllabus to extract and analyze its topic structure automatically.")

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        st.success(f"File uploaded: **{uploaded_file.name}**")

        if st.button("Extract & Analyze Syllabus", type="primary"):
            with st.spinner("Extracting text from PDF..."):
                extracted_text = extract_text_from_pdf(uploaded_file)
                st.session_state.syllabus_text = extracted_text

            if not extracted_text.strip():
                st.error("No text could be extracted. The PDF may be scanned or image-based.")
            else:
                backend_label = f"OpenAI ({st.session_state.get('openai_model')})" if _use_openai else f"Ollama ({st.session_state.get('ollama_model')})"
                with st.spinner(f"Analyzing syllabus with {backend_label} — please wait..."):
                    try:
                        topics = parse_syllabus_structure(extracted_text, **ai_kwargs())
                        st.session_state.topics = topics
                        st.success(f"Done! Discovered **{len(topics)}** topic(s).")
                    except Exception as e:
                        st.error(f"AI analysis failed: {e}")

    if st.session_state.topics:
        with st.expander("View Discovered Topics", expanded=True):
            for i, t in enumerate(st.session_state.topics):
                st.markdown(f"**{i + 1}. {t.get('topic_name', 'Unknown')}**")
                st.caption(t.get("description", ""))
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    st.header("Exam Configuration")

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Exam Name", key="exam_name")
        st.text_input("Subject Name", key="subject_name")
        st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], key="difficulty")

    with col2:
        st.markdown("**Question Distribution**")
        st.caption("Add rows to define how many questions of each mark value.")
        edited_df = st.data_editor(
            st.session_state.marks_distribution,
            key="marks_editor",
            num_rows="dynamic",
            use_container_width=True
        )
        if not edited_df.equals(st.session_state.marks_distribution):
            st.session_state.marks_distribution = edited_df

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Generate Questions", type="primary"):
        if not st.session_state.topics:
            st.error("Please upload and analyze a syllabus first (Upload tab).")
        else:
            dist_list = [{"marks": int(row["Marks"]), "count": int(row["Questions"])} for _, row in st.session_state.marks_distribution.iterrows() if pd.notna(row["Marks"]) and pd.notna(row["Questions"])]
            question_plan = distribute_questions(dist_list, st.session_state.topics)

            if not question_plan:
                st.error("Invalid distribution configuration. Check your marks table.")
            else:
                backend_label = f"OpenAI" if _use_openai else f"Ollama"
                with st.spinner(f"Generating {len(question_plan)} question(s) with {backend_label}..."):
                    try:
                        questions = generate_questions(question_plan, difficulty=st.session_state.difficulty, **ai_kwargs())
                        st.session_state.generated_questions = questions
                        st.success(f"Generated **{len(questions)}** question(s). Check the 'Generated Paper' tab.")
                    except Exception as e:
                        st.error(f"Question generation failed: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    st.header("Generated Question Paper")

    if st.session_state.generated_questions:
        total_marks = sum(q.get("marks", 0) for q in st.session_state.generated_questions)
        
        st.markdown(f"### {st.session_state.exam_name}")
        st.markdown(f"**Subject:** {st.session_state.subject_name}")
        st.markdown(f"**Total Marks:** {total_marks} | **Difficulty:** {st.session_state.difficulty}")
        st.divider()

        for idx, q in enumerate(st.session_state.generated_questions, 1):
            col_q, col_m = st.columns([8, 1])
            with col_q:
                st.markdown(f"**Q{idx}.** {q.get('question_text', '')}")
                st.caption(f"Topic: {q.get('topic_name', 'Unknown')}")
            with col_m:
                st.markdown(f"**[{q.get('marks', 0)} Marks]**")
            st.markdown("<hr style='margin:8px 0;opacity:0.15;'>", unsafe_allow_html=True)
    else:
        st.info("No questions generated yet. Go to the 'Configuration' tab to generate.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    st.header("Export to PDF")

    if st.session_state.generated_questions:
        st.markdown("Your question paper is ready to be exported as a PDF.")
        pdf_buffer = generate_pdf(
            st.session_state.exam_name,
            st.session_state.subject_name,
            st.session_state.generated_questions
        )
        st.download_button(
            label="Download Question Paper PDF",
            data=pdf_buffer,
            file_name="QuestionPaper.pdf",
            mime="application/pdf",
            type="primary"
        )
    else:
        st.info("Generate questions first, then export here.")
    st.markdown('</div>', unsafe_allow_html=True)
