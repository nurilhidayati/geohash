import streamlit as st
from PIL import Image
import base64
from io import BytesIO

# Helper: Convert image to base64 string
def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Public Slack icon URL (white background)
SLACK_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/7/76/Slack_Icon.png"

# CSS for layout and icon
st.markdown(f"""
    <style>
    .profile-container {{
        text-align: center;
        margin-bottom: 20px;
    }}
    .profile-container img.profile {{
        border-radius: 15px;
        object-fit: cover;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
    .slack-icon {{
        height: 16px;
        vertical-align: middle;
        margin-right: 4px;
    }}
    </style>
""", unsafe_allow_html=True)

st.title("About Us")
st.subheader("Meet the Team")

# Team members
team_members = [
    {
        "name": "Nuril Hidayati",
        "username": "@nuril.hidayati",
        "slack": "https://grab.enterprise.slack.com/team/U07L4CFDP4G",
        "photo": Image.open('pages/nuril.png')
    },
    {
        "name": "Annisa Dwi Maiikhsantiani",
        "username": "@ms.annisaa.dwi",
        "slack": "https://grab.enterprise.slack.com/team/U05B3JW5494",
        "photo": Image.open('pages/santi.png')
    },
    {
        "name": "Mochammad Fachri",
        "username": "@ms.muhammad.fachri",
        "slack": "https://grab.enterprise.slack.com/team/U06E347FP7E",
        "photo": Image.open('pages/fachri.png')
    },
]

# Mentors
mentors = [
    {
        "name": "Qitfirul",
        "username": "@qithfirul.q",
        "slack": "https://grab.enterprise.slack.com/team/WS6CPUTS8",
        "photo": Image.open('pages/qitfirul.jpg')
    },
    {
        "name": "Mahardi Pratomo",
        "username": "@mahardi.pratomo",
        "slack": "https://grab.enterprise.slack.com/team/WS6S9CENR",
        "photo": Image.open('pages/mahardi.jpg')
    },
]

# Display Core Team
st.markdown("### 👩‍💻 Core Team")
cols = st.columns(len(team_members))
for col, member in zip(cols, team_members):
    with col:
        img_b64 = image_to_base64(member["photo"])
        st.markdown(f"""
            <div class="profile-container">
                <img class="profile" src="data:image/png;base64,{img_b64}" width="200"><br>
                <strong>{member['name']}</strong><br>
                <a href="{member['slack']}" target="_blank">
                    <img class="slack-icon" src="{SLACK_ICON_URL}" />
                    {member['username']}
                </a>
            </div>
        """, unsafe_allow_html=True)

# Display Mentors Centered
st.markdown("### 👨‍🏫 Mentors")
col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 2, 1])
for col, mentor in zip([col2, col4], mentors):
    with col:
        img_b64 = image_to_base64(mentor["photo"])
        st.markdown(f"""
            <div class="profile-container">
                <img class="profile" src="data:image/png;base64,{img_b64}" width="200"><br>
                <strong>{mentor['name']}</strong><br>
                <a href="{mentor['slack']}" target="_blank">
                    <img class="slack-icon" src="{SLACK_ICON_URL}" />
                    {mentor['username']}
                </a>
            </div>
        """, unsafe_allow_html=True)

# Documentation
st.subheader("📘 Documentation")
st.write("Here’s the guideline to help you understand and work on the project smoothly!")


# Footer
st.markdown(
    """
    <hr style="margin-top: 2rem; margin-bottom: 1rem;">
    <div style='text-align: center; color: grey; font-size: 0.9rem;'>
        © 2025 ID Karta IoT Team
    </div>
    """,
    unsafe_allow_html=True
)
