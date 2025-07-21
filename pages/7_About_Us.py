import streamlit as st
from PIL import Image

# Custom CSS
st.markdown("""
    <style>
    .profile-container {
        text-align: center;
    }
    .profile-container img {
        border-radius: 15px;
        object-fit: cover;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
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
        st.markdown(f"""
            <div class="profile-container">
                <img src="data:image/png;base64,{st.image(member["photo"], width=200, output_format='PNG').image_to_url().split(",")[1]}" width="200"><br>
                <strong>{member['name']}</strong><br>
                💬 <a href="{member['slack']}">{member['username']}</a>
            </div>
        """, unsafe_allow_html=True)

# Display Mentors Centered
st.markdown("### 👨‍🏫 Mentors")
col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 2, 1])
for col, mentor in zip([col2, col4], mentors):
    with col:
        st.markdown(f"""
            <div class="profile-container">
                <img src="data:image/png;base64,{st.image(mentor["photo"], width=200, output_format='PNG').image_to_url().split(",")[1]}" width="200"><br>
                <strong>{mentor['name']}</strong><br>
                💬 <a href="{mentor['slack']}">{mentor['username']}</a>
            </div>
        """, unsafe_allow_html=True)

# Documentation
st.subheader("📘 Documentation")
st.write("Here’s the guideline to help you understand and work on the project smoothly!")
