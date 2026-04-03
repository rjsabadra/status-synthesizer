import streamlit as st
from google import genai

st.set_page_config(page_title="AI Status Synthesis Assistant", page_icon="📌")
st.title("AI Status Synthesis Assistant")
st.caption("Paste scattered project updates and generate a structured PMO summary.")

sample_updates = """Engineering: API integration is 80% complete, but blocked on auth review.
Design: Final mocks approved and handed off.
Ops: Vendor onboarding delayed by 3 days.
PM notes: Launch date may slip if auth review is not completed this week.
QA: Test plan is ready, execution starts after API handoff."""

raw_updates = st.text_area(
    "Paste raw project updates",
    value=sample_updates,
    height=220
)

view = st.radio("View", ["Leadership View", "Team View"], horizontal=True)

if st.button("Generate Status Summary"):
    client = genai.Client(api_key=st.secrets["AIzaSyDbpzHj4_cZ8MyxsI75AETrXxGDyzACJyQ"])

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

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt
    )

    st.markdown(response.text)