import streamlit as st
import streamlit.components.v1 as components
import re
from fpdf import FPDF
from database import init_db
import auth_lib
from ai_engine import generate_learning_stream
import services
from models import is_admin, save_topic

# Initialize Database
init_db()

st.set_page_config(page_title="Nutrition Learning Platform", page_icon="🥗", layout="wide")

# --- HYBRID TTS ENGINE (Browser-Based) ---
def speak_text(text, voice_index=0, volume=1.0, rate=1.0):
    # Clean markdown and quotes for JS safety
    clean_text = re.sub(r'[*#_]', '', text).replace("'", "\\'").replace("\n", " ")
    
    components.html(f"""
        <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance('{clean_text}');
        var voices = window.speechSynthesis.getVoices();
        msg.voice = voices[{voice_index}]; 
        msg.volume = {volume};
        msg.rate = {rate};
        window.speechSynthesis.speak(msg);
        </script>
    """, height=0)

# --- STYLING ---
def apply_custom_style():
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); }
        .login-card {
            background: white; padding: 50px; border-radius: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center;
            max-width: 500px; margin: 100px auto; border: 2px solid #2e7d32;
        }
        .stButton>button { border-radius: 8px; }
        </style>
    """, unsafe_allow_html=True)

# Auth Callback
auth_lib.handle_callback()

# --- LOGIN GATE ---
if "user" not in st.session_state:
    apply_custom_style()
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<h1 style="color: #1b5e20;">🥗 NutritionAI</h1>', unsafe_allow_html=True)
    st.write("### Welcome to the Learning Portal")
    st.write("Please sign in to access lessons and earn certificates.")
    st.divider()
    auth_lib.login()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

user = st.session_state["user"]
services.register_user_if_not_exists(user)

# --- SIDEBAR & SETTINGS ---
st.sidebar.title("🥗 Menu")
options = ["Generate", "My Topics", "Global Quizzes"]
if is_admin(user["email"]): options.append("Admin Panel")
menu = st.sidebar.selectbox("Navigation", options)

st.sidebar.divider()
st.sidebar.header("🔊 Voice Settings")
voice_opt = st.sidebar.selectbox("Voice Tone", ["Default (Male)", "Alternative (Female)"])
v_idx = 0 if voice_opt == "Default (Male)" else 1
vol = st.sidebar.slider("Volume", 0.0, 1.0, 0.8)
spd = st.sidebar.slider("Speed", 0.5, 2.0, 1.0)

st.sidebar.divider()
st.sidebar.write(f"👤 **{user['name']}**")
if st.sidebar.button("🔓 Logout / Switch User"):
    auth_lib.logout()

# --- UTILS ---
def create_pdf(user_name, topic):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_line_width(2); pdf.rect(10, 10, 277, 190)
    pdf.set_font('Arial', 'B', 30)
    pdf.cell(0, 60, 'Certificate of Achievement', ln=True, align='C')
    pdf.set_font('Arial', '', 20)
    pdf.cell(0, 20, f'Awarded to {user_name}', ln=True, align='C')
    pdf.cell(0, 20, f'for {topic}', ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1')

def render_quiz(content, topic_name, topic_id):
    # This Regex handles: A), A., **A)**, spaces, and case-sensitivity
    q_blocks = re.findall(
        r"Q[:\s]*(.*?)\n"           # Match Question text
        r"(?:\*+)?A[\)\.](.*?)\n"   # Match Option A
        r"(?:\*+)?B[\)\.](.*?)\n"   # Match Option B
        r"(?:\*+)?C[\)\.](.*?)\n"   # Match Option C
        r"(?:\*+)?D[\)\.](.*?)\n"   # Match Option D
        r"Answer[:\s]*([A-D])",     # Match the Answer letter
        content, 
        re.DOTALL | re.IGNORECASE
    )
    
    if q_blocks:
        st.divider()
        st.subheader("📝 Practice Quiz")
        score_key = f"score_{topic_id}"
        if score_key not in st.session_state: 
            st.session_state[score_key] = {}

        for i, (q, a, b, c, d, ans) in enumerate(q_blocks):
            st.write(f"**Question {i+1}:** {q.strip()}")
            options = [f"A) {a.strip()}", f"B) {b.strip()}", f"C) {c.strip()}", f"D) {d.strip()}"]
            
            u_choice = st.radio("Select your answer:", options, key=f"radio_{topic_id}_{i}")
            
            # Use columns to keep the UI tight
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button(f"Submit Q{i+1}", key=f"btn_{topic_id}_{i}"):
                    if u_choice.startswith(ans.upper()):
                        st.success(f"Correct! ({ans.upper()})")
                        st.session_state[score_key][i] = True
                    else:
                        st.error("Try again!")
                        st.session_state[score_key][i] = False

        # Completion Logic
        correct_count = sum(st.session_state[score_key].values())
        if correct_count == len(q_blocks) and len(q_blocks) > 0:
            st.balloons()
            st.success("🎉 Perfect Score! Your certificate is ready.")
            cert = create_pdf(user['name'], topic_name)
            st.download_button("🎓 Download Certificate", cert, f"{topic_name}_cert.pdf")
    else:
        # This helps you catch IF the AI actually generated a quiz or not
        if "QUIZ_SECTION" in content:
            st.info("💡 Quiz detected but format is slightly off. Trying to recover...")
            # Fallback: simpler search if the complex regex fails
            simple_qs = re.findall(r"Q:.*?\nAnswer: [A-D]", content, re.S)
            if not simple_qs:
                st.warning("The AI lesson didn't include a properly formatted quiz this time. Try clicking 'Generate' again.")

# --- PAGES ---
if menu == "Generate":
    st.title("🌱 Lesson Generator")
    c1, c2 = st.columns(2)
    country = c1.text_input("Region")
    topic = c2.text_input("Subject")
    if st.button("Generate"):
        full_text = ""
        placeholder = st.empty()
        for chunk in generate_learning_stream(country, topic):
            full_text += chunk
            placeholder.markdown(full_text)
        services.save_user_topic(user["email"], country, topic, full_text)
        if st.button("🔊 Play Lesson"):
            speak_text(full_text.split("QUIZ_SECTION")[0], v_idx, vol, spd)
        render_quiz(full_text, topic, "new")

elif menu == "My Topics":
    st.title("📚 Saved Lessons")
    for idx, t in enumerate(services.get_user_topics_list(user["email"])):
        if not t[3]:
            with st.expander(f"📖 {t[0]} ({t[2]})"):
                st.markdown(t[1])
                if st.button("🔊 Play", key=f"sp_{idx}"):
                    speak_text(t[1].split("QUIZ_SECTION")[0], v_idx, vol, spd)
                render_quiz(t[1], t[0], f"saved_{idx}")

elif menu == "Global Quizzes":
    st.title("🌟 Official Quizzes")
    for idx, t in enumerate([x for x in services.get_user_topics_list(user["email"]) if x[3]]):
        with st.expander(f"⭐ {t[0]} ({t[2]})"):
            st.markdown(t[1])
            if st.button("🔊 Play", key=f"g_sp_{idx}"):
                speak_text(t[1].split("QUIZ_SECTION")[0], v_idx, vol, spd)
            render_quiz(t[1], t[0], f"global_{idx}")

elif menu == "Admin Panel":
    st.title("🛡️ Admin")
    with st.form("admin"):
        a_c = st.text_input("Region"); a_t = st.text_input("Title"); a_b = st.text_area("Content", height=200)
        if st.form_submit_button("Publish"):
            save_topic("admin", a_c, a_t, a_b, is_global=1)
            st.success("Published!")