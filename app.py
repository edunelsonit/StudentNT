import streamlit as st
import re
import pyttsx3
from fpdf import FPDF
from database import init_db
from ai_engine import generate_learning_stream
from services import register_user_if_not_exists, save_user_topic, get_user_topics_list
from models import is_admin, save_topic

init_db()
st.set_page_config(page_title="Nutrition Platform", layout="wide")

if "user" not in st.session_state:
    st.info("Please login to continue.")
    st.stop()

user = st.session_state["user"]
register_user_if_not_exists(user)

# --- Offline TTS Helper ---
def speak_text(text):
    # Note: On some servers/headless environments, TTS might require a virtual display
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# --- Certificate Logic ---
def create_pdf_certificate(user_name, topic_name):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_line_width(2)
    pdf.rect(10, 10, 277, 190)
    pdf.set_font('Arial', 'B', 30)
    pdf.cell(0, 60, 'Certificate of Completion', ln=True, align='C')
    pdf.set_font('Arial', '', 20)
    pdf.cell(0, 20, f'Awarded to {user_name}', ln=True, align='C')
    pdf.cell(0, 20, f'for {topic_name}', ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1')

# --- Quiz Engine (Hides answers until button click) ---
def render_quiz(content, topic_name, topic_id):
    q_blocks = re.findall(r"Q: (.*?)\nA\) (.*?)\nB\) (.*?)\nC\) (.*?)\nD\) (.*?)\nAnswer: ([A-D])", content, re.S)
    if q_blocks:
        st.divider()
        st.subheader("📝 Hidden Quiz")
        score_key = f"score_{topic_id}"
        if score_key not in st.session_state: st.session_state[score_key] = {}

        for i, (q, a, b, c, d, ans) in enumerate(q_blocks):
            st.write(f"**Question {i+1}:** {q}")
            options = [f"A) {a}", f"B) {b}", f"C) {c}", f"D) {d}"]
            u_choice = st.radio("Select your answer:", options, key=f"r_{topic_id}_{i}")
            
            # Answer is hidden until this button is pressed
            if st.button(f"Check Answer for Q{i+1}", key=f"btn_{topic_id}_{i}"):
                if u_choice.startswith(ans):
                    st.success(f"Correct! The answer is {ans}.")
                    st.session_state[score_key][i] = True
                else:
                    st.error(f"Incorrect. Try reviewing the lesson again!")
                    st.session_state[score_key][i] = False

        if sum(st.session_state[score_key].values()) == len(q_blocks):
            st.balloons()
            cert = create_pdf_certificate(user['name'], topic_name)
            st.download_button("🎓 Download Certificate", cert, f"{topic_name}_cert.pdf")

# --- UI Navigation ---
menu_options = ["Generate", "My Topics", "Global Quizzes"]
if is_admin(user["email"]): menu_options.append("Admin Panel")
menu = st.sidebar.selectbox("Navigation", menu_options)

if menu == "Generate":
    st.title("🥗 Localized Learning")
    c1, c2 = st.columns(2)
    country = c1.text_input("Country")
    topic = c2.text_input("Topic")
    
    if st.button("Generate"):
        full_text = ""
        p = st.empty()
        for chunk in generate_learning_stream(country, topic):
            full_text += chunk
            p.markdown(full_text)
        
        save_user_topic(user, country, topic, full_text)
        
        if st.button("🔊 Listen to Lesson"):
            speak_text(full_text.split("QUIZ_SECTION")[0]) # Speak only lesson, not quiz
            
        render_quiz(full_text, topic, "new")

elif menu == "My Topics":
    st.title("📚 Saved Lessons")
    for idx, t in enumerate(get_user_topics_list(user)):
        if not t[3]: # Show only personal topics
            with st.expander(f"📖 {t[0]} ({t[2]})"):
                st.markdown(t[1])
                if st.button("🔊 Speak", key=f"sp_{idx}"):
                    speak_text(t[1].split("QUIZ_SECTION")[0])
                if "Answer:" in t[1]:
                    render_quiz(t[1], t[0], f"saved_{idx}")

elif menu == "Global Quizzes":
    st.title("🌟 Admin Recommended Quizzes")
    topics = get_user_topics_list(user)
    global_topics = [t for t in topics if t[3]]
    
    if not global_topics:
        st.info("No global quizzes available yet.")
    else:
        for idx, t in enumerate(global_topics):
            with st.expander(f"⭐ {t[0]} - {t[2]}"):
                st.markdown(t[1])
                render_quiz(t[1], t[0], f"global_{idx}")

elif menu == "Admin Panel":
    st.title("🛡️ Admin Panel")
    with st.form("admin_form"):
        t_country = st.text_input("Target Region")
        t_topic = st.text_input("Title")
        t_content = st.text_area("Lesson & Quiz (Use standard Q: Answer: format)", height=300)
        if st.form_submit_button("Publish Global Quiz"):
            save_topic("admin-system", t_country, t_topic, t_content, is_global=1)
            st.success("Global quiz published!")