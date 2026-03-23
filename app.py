import streamlit as st
import streamlit.components.v1 as components
import re
import platform
import os
from fpdf import FPDF
from database import init_db
from auth_lib import login, handle_callback
from ai_engine import generate_learning_stream
import services
from models import is_admin, save_topic

# Initialize Database
init_db()

st.set_page_config(page_title="Nutrition Learning Platform", page_icon="🥗", layout="wide")

# --- HYBRID TTS ENGINE (Environment Aware) ---
def speak_text(text, voice_index=0, volume=1.0, rate=1.0):
    clean_text = re.sub(r'[*#_]', '', text).replace("'", "\\'").replace("\n", " ")
    
    # This JS snippet fetches available voices and applies your settings
    components.html(f"""
        <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance('{clean_text}');
        var voices = window.speechSynthesis.getVoices();
        
        // Apply Settings
        msg.voice = voices[{voice_index}]; 
        msg.volume = {volume};
        msg.rate = {rate};
        
        window.speechSynthesis.speak(msg);
        </script>
    """, height=0)
    
    # Secondary Fallback: OS Detection (For specialized local logging or offline needs)
    current_os = platform.system()
    if current_os == "Linux":
        # Check if espeak is available before trying
        os.system(f"command -v espeak >/dev/null 2>&1 && espeak '{clean_text}' &")
    elif current_os == "Darwin": # macOS
        os.system(f"say '{clean_text}' &")

# --- CUSTOM CSS FOR LOGIN ---
def apply_login_style():
    st.markdown("""
        <style>
        /* App background */
        .stApp {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }

        /* Login card */
        .login-card {
            background: rgba(255, 255, 255, 0.97);
            padding: 60px 40px;
            border-radius: 30px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.25);
            text-align: center;
            max-width: 600px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .login-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 35px 60px rgba(0,0,0,0.35);
        }

        /* Title */
        .login-title {
            color: #000000;  /* Black text */
            font-weight: 900;
            font-size: 3rem;
            margin-bottom: 10px;
        }

        /* Subtitle */
        .login-subtitle {
            color: #000000;  /* Black text */
            font-size: 1.25rem;
            margin-bottom: 20px;
        }

        /* Body text */
        .login-body {
            color: #000000;  /* Black text */
            font-size: 1rem;
            margin-bottom: 20px;
        }

        /* Button styling */
        .stButton>button {
            background: linear-gradient(90deg, #00695c 0%, #004d40 100%);
            color: white;
            font-weight: 700;
            font-size: 1.1rem;
            padding: 10px 25px;
            border-radius: 12px;
            border: none;
            transition: background 0.3s ease, transform 0.2s ease;
        }

        .stButton>button:hover {
            background: linear-gradient(90deg, #004d40 0%, #00695c 100%);
            transform: scale(1.05);
        }

        /* Divider */
        .stDivider {
            border-top: 2px solid #000000;  /* Black divider */
            margin: 20px 0;
        }
        </style>
    """, unsafe_allow_html=True)


# --- LOGIN PAGE ---
if "user" not in st.session_state:
    apply_login_style()
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<h1 class="login-title">🥗 NutritionAI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="login-subtitle">Smart Registration & Learning</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-body">Welcome to the automated nutrition platform for regional exam centers.</p>', unsafe_allow_html=True)
    st.divider()
    login()  # your existing login function
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- APP LOGIC ---
user = st.session_state["user"]
services.register_user_if_not_exists(user)

def create_pdf_certificate(user_name, topic_name):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()

    # Background
    pdf.set_fill_color(245, 245, 255)
    pdf.rect(0, 0, 297, 210, 'F')

    # Border
    pdf.set_line_width(2)
    pdf.set_draw_color(0, 102, 204)
    pdf.rect(10, 10, 277, 190)

    # Header
    pdf.set_font('Arial', 'B', 36)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 50, 'Certificate of Achievement', ln=True, align='C')

    # Decorative line
    pdf.set_line_width(0.5)
    pdf.line(50, 60, 247, 60)

    # Body text
    pdf.set_font('Arial', '', 20)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 20, 'This certificate is proudly presented to', ln=True, align='C')

    # User name
    pdf.set_font('Arial', 'B', 28)
    pdf.set_text_color(204, 51, 0)
    pdf.cell(0, 20, f'{user_name}', ln=True, align='C')

    # Achievement statement
    pdf.set_font('Arial', '', 20)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 20, 'for successfully completing and demonstrating mastery in the topic of', ln=True, align='C')

    # Topic name
    pdf.set_font('Arial', 'B', 26)
    pdf.set_text_color(0, 102, 0)
    pdf.cell(0, 20, f'{topic_name}', ln=True, align='C')

    # Footer signature
    pdf.set_y(160)
    pdf.set_font('Arial', '', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, '_________________________', ln=True, align='R')
    pdf.cell(0, 10, 'Authorized Signature', ln=True, align='R')

    return pdf.output(dest='S').encode('latin-1')

def render_quiz(content, topic_name, topic_id):
    q_blocks = re.findall(r"Q: (.*?)\nA\) (.*?)\nB\) (.*?)\nC\) (.*?)\nD\) (.*?)\nAnswer: ([A-D])", content, re.S)
    if q_blocks:
        st.divider()
        st.subheader("📝 Hidden Assessment")
        score_key = f"score_{topic_id}"
        if score_key not in st.session_state: st.session_state[score_key] = {}

        for i, (q, a, b, c, d, ans) in enumerate(q_blocks):
            st.write(f"**Q{i+1}: {q}**")
            u_choice = st.radio("Select Answer:", [f"A) {a}", f"B) {b}", f"C) {c}", f"D) {d}"], key=f"r_{topic_id}_{i}")
            
            if st.button(f"Submit Q{i+1}", key=f"btn_{topic_id}_{i}"):
                if u_choice.startswith(ans):
                    st.success(f"Correct! The answer is {ans}.")
                    st.session_state[score_key][i] = True
                else:
                    st.error("Incorrect. Review the text above and try again.")
                    st.session_state[score_key][i] = False

        if sum(st.session_state[score_key].values()) == len(q_blocks) and len(q_blocks) > 0:
            st.balloons()
            cert = create_pdf_certificate(user['name'], topic_name)
            st.download_button("🎓 Download Verified Certificate", cert, f"{topic_name}_cert.pdf")

# Sidebar
options = ["Generate", "My Topics", "Global Quizzes"]
if is_admin(user["email"]): options.append("Admin Panel")
menu = st.sidebar.selectbox("Navigate Platform", options)
st.sidebar.header("🔊 Voice Settings")
# Note: Voice index is a simple way to toggle, 
# but browsers load voices asynchronously. 
# 0 and 1 are usually the default Male/Female system voices.
voice_opt = st.sidebar.selectbox("Voice Tone", ["Default / Male", "Alternative / Female"], index=0)
v_idx = 0 if voice_opt == "Default / Male" else 1
vol_level = st.sidebar.slider("Volume", 0.0, 1.0, 0.8)
speed_level = st.sidebar.slider("Reading Speed", 0.5, 2.0, 1.0)

# --- PAGE: GENERATE ---
if menu == "Generate":
    st.title("🌱 Generate Personalized Lesson")
    c1, c2 = st.columns(2)
    country = c1.text_input("Region/Country", placeholder="e.g. Ghana")
    topic = c2.text_input("Nutritional Subject", placeholder="e.g. Balanced Diet")

    if st.button("Generate Learning Plan"):
        full_text = ""
        p = st.empty()
        for chunk in generate_learning_stream(country, topic):
            full_text += chunk
            p.markdown(full_text)
        services.save_user_topic(user["email"], country, topic, full_text)
        
        if st.button("🔊 Read Lesson Aloud"):
            speak_text(full_text.split("QUIZ_SECTION")[0])
            
        render_quiz(full_text, topic, "latest")

# --- PAGE: MY TOPICS ---
elif menu == "My Topics":
    st.title("📚 Personal Library")
    topics = services.get_user_topics_list(user["email"])
    personal = [t for t in topics if not t[3]]
    for idx, t in enumerate(personal):
        with st.expander(f"📖 {t[0]} ({t[2]})"):
            st.markdown(t[1])
            # In your Generate or My Topics pages, update the button logic:
            if st.button("🔊 Play Lesson", key=f"play_{idx}"):
                lesson_text = t[1].split("QUIZ_SECTION")[0]
                speak_text(lesson_text, voice_index=v_idx, volume=vol_level, rate=speed_level)

# --- PAGE: GLOBAL QUIZZES ---
elif menu == "Global Quizzes":
    st.title("🌟 Verified Admin Lessons")
    topics = services.get_user_topics_list(user["email"])
    globals = [t for t in topics if t[3]]
    for idx, t in enumerate(globals):
        with st.expander(f"⭐ {t[0]} ({t[2]})"):
            st.markdown(t[1])
            if st.button("🔊 Play", key=f"g_sp_{idx}"):
                speak_text(t[1].split("QUIZ_SECTION")[0])
            render_quiz(t[1], t[0], f"global_{idx}")

# --- PAGE: ADMIN PANEL ---
elif menu == "Admin Panel":
    st.title("🛡️ Admin Dashboard")
    with st.form("admin_form"):
        a_country = st.text_input("Region")
        a_topic = st.text_input("Lesson Title")
        a_content = st.text_area("Lesson & Quiz Content", height=300)
        if st.form_submit_button("Publish Global Lesson"):
            save_topic("admin-system", a_country, a_topic, a_content, is_global=1)
            st.success("Lesson successfully published to all students.")