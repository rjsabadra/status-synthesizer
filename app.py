import streamlit as st
from google import genai
import re

st.set_page_config(
    page_title="AI Status Synthesis Assistant",
    page_icon="📌",
    layout="wide"
)

# ---------- STYLES ----------
st.markdown("""
    <style>
    .status-pill {
        display: inline-block;
        padding: 0.45rem 0.9rem;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 0.75rem;
    }
    .status-ontrack {
        background-color: #e8f5e9;
        color: #1b5e20;
    }
    .status-atrisk {
        background-color: #fff8e1;
        color: #8d6e00;
    }
    .status-offtrack {
        background-color: #ffebee;
        color: #b71c1c;
    }
    .card {
        background: #ffffff;
        padding: 1rem;
        border-radius: 14px;
        border: 1px solid #eaeaea;
        margin-bottom: 1rem;
    }
    .card-title {
        font-weight: 700;
        margin-bottom: 0.4rem;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("AI Status Synthesis Assistant")
st.caption("Convert scattered updates into structured PM summaries")

# ---------- DEFAULT INPUT ----------
sample_updates = """Program Lead: Training content is almost complete.
HR: Participant list finalized.
IT: Meeting link and access setup pending.
Trainer: Confirmed availability.
PM notes: If IT setup is delayed, training may need to be postponed."""

raw_updates = st.text_area(
    "Paste raw project updates",
    value=sample_updates,
    height=200
)

view = st.radio("Select View", ["Leadership View", "Team View"], horizontal=True)

# ---------- CLEAN FUNCTION ----------
def clean_text(text: str):
    if not text:
        return ""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = text.replace("*", "")
    return text.strip()

# ---------- PARSER ----------
def parse_response(text, keys):
    sections = {k: "" for k in keys}
    current = None

    for line in text.splitlines():
        line = line.strip()

        for key in keys:
            if line.startswith(f"{key}:"):
                current = key
                sections[key] = line.replace(f"{key}:", "").strip()
                break
        else:
            if current and line:
                sections[current] += "\n" + line

    return sections

# ---------- RENDER ----------
def render_status(status):
    status = clean_text(status).lower()

    if "on track" in status:
        cls = "status-ontrack"
    elif "risk" in status:
        cls = "status-atrisk"
    else:
        cls = "status-offtrack"

    st.markdown(
        f'<div class="status-pill {cls}">{status.title()}</div>',
        unsafe_allow_html=True
    )

def render_card(title, content):
    content = clean_text(content)
    content = content.replace("\n", "<br>") if content else "—"

    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">{title}</div>
            <div>{content}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------- BUTTON ----------
if st.button("Generate Status Summary"):

    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

    if view == "Leadership View":
        keys = ["Overall Status", "Executive Summary", "Top Risks", "Decisions Needed"]

        prompt = f"""
Summarize updates for leadership.

Do not use markdown symbols like *, **.

Return:

Overall Status:
Executive Summary:
Top Risks:
Decisions Needed:

Updates:
{raw_updates}
"""

    else:
        keys = ["Overall Status", "Detailed Summary", "Blockers", "Risks", "Next Steps", "Missing Information"]

        prompt = f"""
Summarize updates for execution teams.

Do not use markdown symbols like *, **.

Return:

Overall Status:
Detailed Summary:
Blockers:
Risks:
Next Steps:
Missing Information:

Updates:
{raw_updates}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        parsed = parse_response(response.text, keys)

        st.markdown("---")

        render_status(parsed.get("Overall Status", ""))

        if view == "Leadership View":
            render_card("Executive Summary", parsed.get("Executive Summary", ""))

            col1, col2 = st.columns(2)
            with col1:
                render_card("Top Risks", parsed.get("Top Risks", ""))
            with col2:
                render_card("Decisions Needed", parsed.get("Decisions Needed", ""))

        else:
            render_card("Detailed Summary", parsed.get("Detailed Summary", ""))

            col1, col2, col3 = st.columns(3)
            with col1:
                render_card("Blockers", parsed.get("Blockers", ""))
            with col2:
                render_card("Risks", parsed.get("Risks", ""))
            with col3:
                render_card("Next Steps", parsed.get("Next Steps", ""))

            render_card("Missing Information", parsed.get("Missing Information", ""))

        with st.expander("Raw Input"):
            st.code(raw_updates)

    except Exception as e:
        st.error("Something went wrong. Please try again.")
        st.exception(e)
