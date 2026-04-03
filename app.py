import streamlit as st
from google import genai

st.set_page_config(
    page_title="AI Status Synthesis Assistant",
    page_icon="📌",
    layout="wide"
)

st.markdown("""
    <style>
    .main {
        padding-top: 1.5rem;
    }
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
        border: 1px solid #c8e6c9;
    }
    .status-atrisk {
        background-color: #fff8e1;
        color: #8d6e00;
        border: 1px solid #ffecb3;
    }
    .status-offtrack {
        background-color: #ffebee;
        color: #b71c1c;
        border: 1px solid #ffcdd2;
    }
    .section-card {
        background: #ffffff;
        padding: 1rem 1rem 0.8rem 1rem;
        border-radius: 16px;
        border: 1px solid #eaeaea;
        box-shadow: 0 1px 6px rgba(0,0,0,0.04);
        margin-bottom: 1rem;
        height: 100%;
    }
    .section-title {
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .subtle-label {
        font-size: 0.82rem;
        font-weight: 700;
        color: #666;
        margin-bottom: 0.35rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    </style>
""", unsafe_allow_html=True)

st.title("AI Status Synthesis Assistant")
st.caption("Turn scattered project updates into a structured PMO summary with blockers, risks, and next steps.")

sample_updates = """Program Lead: Training content is almost complete.
HR: Participant list finalized.
IT: Meeting link and access setup pending.
Trainer: Confirmed availability.
PM notes: If IT setup is delayed, training may need to be postponed."""

raw_updates = st.text_area(
    "Paste raw project updates",
    value=sample_updates,
    height=220,
    placeholder="Paste updates from different teams or stakeholders here."
)

view = st.radio("Select output view", ["Leadership View", "Team View"], horizontal=True)

def parse_response(text: str, expected_sections: list[str]):
    sections = {section: "" for section in expected_sections}
    current_key = None

    for line in text.splitlines():
        stripped = line.strip()
        matched_key = None

        for section in expected_sections:
            prefix = f"{section}:"
            if stripped.startswith(prefix):
                matched_key = section
                current_key = section
                sections[current_key] = stripped.replace(prefix, "").strip()
                break

        if matched_key is None and current_key and stripped:
            sections[current_key] += ("\n" if sections[current_key] else "") + stripped

    return sections

def render_status_badge(status: str):
    status_lower = status.lower()
    if "on track" in status_lower:
        css_class = "status-pill status-ontrack"
    elif "at risk" in status_lower:
        css_class = "status-pill status-atrisk"
    else:
        css_class = "status-pill status-offtrack"

    st.markdown(
        f'<div class="{css_class}">Overall Status: {status if status else "Unknown"}</div>',
        unsafe_allow_html=True
    )

def render_card(title: str, content: str):
    safe_content = content.replace("\n", "<br>") if content else "—"
    st.markdown(
        f"""
        <div class="section-card">
            <div class="section-title">{title}</div>
            <div>{safe_content}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

if st.button("Generate Status Summary", use_container_width=True):
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

    if view == "Leadership View":
        expected_sections = [
            "Overall Status",
            "Executive Summary",
            "Top Risks",
            "Decisions Needed"
        ]

        prompt = f"""
You are helping a program manager create a leadership-ready status summary.

Given the raw project updates below, generate:
1. Overall Status: On Track, At Risk, or Off Track
2. Executive Summary: a short, high-level summary focused on business impact and current situation
3. Top Risks: the 2-4 most important risks or concerns
4. Decisions Needed: any escalations, approvals, or decisions leadership should be aware of

Keep the tone crisp, high-level, and decision-oriented.
Do not go too deep into operational detail.
Keep the output easy to scan.

Raw updates:
{raw_updates}

Return the response in this exact format:

Overall Status:
Executive Summary:
Top Risks:
Decisions Needed:
"""
    else:
        expected_sections = [
            "Overall Status",
            "Detailed Summary",
            "Blockers",
            "Risks",
            "Next Steps",
            "Missing Information"
        ]

        prompt = f"""
You are helping a program manager create an execution-focused team summary.

Given the raw project updates below, generate:
1. Overall Status: On Track, At Risk, or Off Track
2. Detailed Summary: a concise operational summary
3. Blockers: current blockers affecting progress
4. Risks: possible issues that may affect timeline or execution
5. Next Steps: the most important action items
6. Missing Information: anything unclear, missing, or lacking ownership

Keep the tone practical, action-oriented, and easy for a working team to use.

Raw updates:
{raw_updates}

Return the response in this exact format:

Overall Status:
Detailed Summary:
Blockers:
Risks:
Next Steps:
Missing Information:
"""

    try:
        with st.spinner("Generating summary..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

        parsed = parse_response(response.text, expected_sections)

        st.markdown("---")
        render_status_badge(parsed.get("Overall Status", ""))

        if view == "Leadership View":
            st.markdown('<div class="subtle-label">Leadership Summary</div>', unsafe_allow_html=True)
            render_card("Executive Summary", parsed.get("Executive Summary", ""))

            col1, col2 = st.columns(2)
            with col1:
                render_card("Top Risks", parsed.get("Top Risks", ""))
            with col2:
                render_card("Decisions Needed", parsed.get("Decisions Needed", ""))

        else:
            st.markdown('<div class="subtle-label">Execution Summary</div>', unsafe_allow_html=True)
            render_card("Detailed Summary", parsed.get("Detailed Summary", ""))

            col1, col2, col3 = st.columns(3)
            with col1:
                render_card("Blockers", parsed.get("Blockers", ""))
            with col2:
                render_card("Risks", parsed.get("Risks", ""))
            with col3:
                render_card("Next Steps", parsed.get("Next Steps", ""))

            render_card("Missing Information", parsed.get("Missing Information", ""))

        with st.expander("View raw project updates"):
            st.code(raw_updates)

    except Exception as e:
        st.error("The model request failed. Please try again.")
        st.exception(e)
