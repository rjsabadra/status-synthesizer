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
    }
    .section-title {
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .muted {
        color: #666;
        font-size: 0.92rem;
    }
    </style>
""", unsafe_allow_html=True)

st.title("AI Status Synthesis Assistant")
st.caption("Turn scattered project updates into a structured PMO summary with blockers, risks, and next steps.")

sample_updates = """Engineering: API integration is 80% complete, but blocked on auth review.
Design: Final mocks approved and handed off.
Ops: Vendor onboarding delayed by 3 days.
PM notes: Launch date may slip if auth review is not completed this week.
QA: Test plan is ready, execution starts after API handoff."""

raw_updates = st.text_area(
    "Paste raw project updates",
    value=sample_updates,
    height=220,
    placeholder="Paste updates from engineering, design, operations, PM notes, etc."
)

view = st.radio("Select output view", ["Leadership View", "Team View"], horizontal=True)

def parse_response(text: str):
    sections = {
        "Overall Status": "",
        "Summary": "",
        "Blockers": "",
        "Risks": "",
        "Next Steps": ""
    }

    current_key = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Overall Status:"):
            current_key = "Overall Status"
            sections[current_key] = stripped.replace("Overall Status:", "").strip()
        elif stripped.startswith("Summary:"):
            current_key = "Summary"
            sections[current_key] = stripped.replace("Summary:", "").strip()
        elif stripped.startswith("Blockers:"):
            current_key = "Blockers"
            sections[current_key] = stripped.replace("Blockers:", "").strip()
        elif stripped.startswith("Risks:"):
            current_key = "Risks"
            sections[current_key] = stripped.replace("Risks:", "").strip()
        elif stripped.startswith("Next Steps:"):
            current_key = "Next Steps"
            sections[current_key] = stripped.replace("Next Steps:", "").strip()
        elif current_key and stripped:
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
        f'<div class="{css_class}">Overall Status: {status}</div>',
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

    prompt = f"""
You are helping a program manager synthesize project updates.

Given the raw updates below, generate:
1. Overall status: On Track, At Risk, or Off Track
2. A concise summary
3. Key blockers
4. Key risks
5. Next steps

If the selected mode is Leadership View, keep the summary high-level and decision-oriented.
If the selected mode is Team View, make it slightly more operational and action-oriented.

Keep each section crisp and practical.

Mode: {view}

Raw updates:
{raw_updates}

Return the response in this exact format:

Overall Status:
Summary:
Blockers:
Risks:
Next Steps:
"""

    try:
        with st.spinner("Generating summary..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

        parsed = parse_response(response.text)

        st.markdown("---")
        render_status_badge(parsed["Overall Status"])
        render_card("Summary", parsed["Summary"])

        col1, col2, col3 = st.columns(3)
        with col1:
            render_card("Blockers", parsed["Blockers"])
        with col2:
            render_card("Risks", parsed["Risks"])
        with col3:
            render_card("Next Steps", parsed["Next Steps"])

        with st.expander("View raw project updates"):
            st.code(raw_updates)

    except Exception as e:
        st.error("The model request failed. Please try again.")
        st.exception(e)
