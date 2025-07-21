import streamlit as st
from PIL import Image

# Inject CSS styling
st.markdown("""
    <style>
    .team-photo-container {
        text-align: center;
        margin-bottom: 20px;
    }
    .team-photo-container img {
        border-radius: 15px;
        object-fit: cover;
        width: 180px;
        height: 180px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .team-photo-container .name {
        margin: 8px 0 2px 0;
        font-weight: bold;
        font-size: 16px;
    }
    .team-photo-container .username {
        margin: 0;
        font-size: 14px;
        color: #aaa;
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

# Show Core Team
st.markdown("### 👩‍💻 Core Team")
cols = st.columns(len(team_members))
for col, member in zip(cols, team_members):
    with col:
        st.markdown(f"""
            <div class="team-photo-container">
                <img src="data:image/png;base64,{st.image(member['photo'], output_format='png').data.decode()}" alt="{member['name']}">
                <div class="name">{member['name']}</div>
                <div class="username">💬 <a href="{member['slack']}" target="_blank">{member['username']}</a></div>
            </div>
        """, unsafe_allow_html=True)

# Show Mentors
st.markdown("### 👨‍🏫 Mentors")
col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 2, 1])
for col, mentor in zip([col2, col4], mentors):
    with col:
        st.markdown(f"""
            <div class="team-photo-container">
                <img src="data:image/jpeg;base64,{st.image(mentor['photo'], output_format='jpeg').data.decode()}" alt="{mentor['name']}">
                <div class="name">{mentor['name']}</div>
                <div class="username">💬 <a href="{mentor['slack']}" target="_blank">{mentor['username']}</a></div>
            </div>
        """, unsafe_allow_html=True)

# Documentation
st.subheader("📘 Documentation")
st.write("Here’s the guideline to help you understand and work on the project smoothly!")
