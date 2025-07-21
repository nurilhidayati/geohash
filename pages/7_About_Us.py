import streamlit as st
from PIL import Image

st.title("About Us")
st.subheader("Meet the Team")

# Sample team members
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

# Display team members
st.markdown("### 👩‍💻 Core Team")
cols = st.columns(len(team_members))
for col, member in zip(cols, team_members):
    with col:
        st.image(member["photo"], width=150)
        st.markdown(f"**{member['name']}**")
        st.markdown(f"💬 [{member['username']}]({member['slack']})")

# Display mentors centered
st.markdown("### 👨‍🏫 Mentors")
col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 1])
for col, mentor in zip([col2, col4], mentors):
    with col:
        st.image(mentor["photo"], width=150)
        st.markdown(f"**{mentor['name']}**")
        st.markdown(f"💬 [{mentor['username']}]({mentor['slack']})")

# Documentation section
st.subheader("📘 Documentation")
st.write("Here’s the guideline to help you understand and work on the project smoothly!")
