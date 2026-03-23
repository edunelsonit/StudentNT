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
def apply_login_style():
    st.markdown("""
        <style>
        /* Modern Gradient Background */
        .stApp {
            background: linear-gradient(135deg, #1d976c 0%, #93f9b9 100%);
        }
        /* Hide the sidebar on the login page for a cleaner look */
        [data-testid="stSidebar"] {
            display: none;
        }
        /* Center the main container */
        .main .block-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 90vh;
        }
        </style>
    """, unsafe_allow_html=True)

# --- LOGIN GATE ---
if "user" not in st.session_state:
    apply_login_style()
    
    # Using a native Streamlit Container for the "Card"
    with st.container(border=True):
        st.title("🥗 NutritionAI")
        st.subheader("Regional Learning Portal")
        
        # Using columns to center the descriptive text and image
        col1, col2 = st.columns([1, 2])
        with col1:
            # Native icon or image
            st.write("## 🌍") 
        with col2:
            st.write("**Empowering West African Examination Centers** with localized nutritional data.")
        
        st.divider()
        
        # Using a status object to guide the user
        with st.status("Authentication Required", expanded=True) as status:
            st.write("Please use your authorized credentials to access the dashboard.")
            
            # The Login Button from auth_lib
            auth_lib.login()
            
            status.update(label="Awaiting Login...", state="running", expanded=False)

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

# Inside the "My Topics" section of app.py

elif menu == "My Topics":
    st.title("📚 Your Learning History")
    topics = services.get_user_topics_list(user["email"])
    personal = [t for t in topics if not t[3]]
    
    for idx, t in enumerate(personal):
        with st.expander(f"📖 {t[0]} ({t[2]})"):
            st.markdown(t[1])
            
            col1, col2, col3 = st.columns([1,1,2])
            with col1:
                if st.button("🔊 Play", key=f"sp_{idx}"):
                    speak_text(t[1].split("QUIZ_SECTION")[0], v_idx, vol, spd)
            with col2:
                # REGENERATE LOGIC
                if st.button("🔄 Refresh", key=f"regen_{idx}"):
                    with st.spinner("Regenerating lesson..."):
                        new_text = ""
                        for chunk in generate_learning_stream(t[2], t[0]):
                            new_text += chunk
                        # Update database with new content (you'll need an update_topic function in models.py)
                        services.save_user_topic(user["email"], t[2], t[0], new_text)
                        st.rerun() # Refresh page to show new content
            
            render_quiz(t[1], t[0], f"saved_{idx}")
elif menu == "Global Quizzes":
    st.title("🌟 Official Quizzes")
    for idx, t in enumerate([x for x in services.get_user_topics_list(user["email"]) if x[3]]):
        with st.expander(f"⭐ {t[0]} ({t[2]})"):
            st.markdown(t[1])
            if st.button("🔊 Play", key=f"g_sp_{idx}"):
                speak_text(t[1].split("QUIZ_SECTION")[0], v_idx, vol, spd)
            render_quiz(t[1], t[0], f"global_{idx}")

# Inside the Admin Panel section of app.py

elif menu == "Admin Panel":
    st.title("🛡️ Admin Content Creator")
    st.subheader("Create & Publish Global Lessons")
    
    # 1. AI Drafting Tool
    with st.expander("🪄 AI Drafting Assistant (Fast Generation)"):
        col_a, col_b = st.columns(2)
        draft_country = col_a.text_input("Target Region", key="admin_country")
        draft_topic = col_b.text_input("Core Subject", key="admin_topic")
        
        if st.button("Generate Draft Content"):
            if draft_country and draft_topic:
                with st.status("AI is drafting the lesson..."):
                    draft_text = ""
                    # We use the same engine but collect it all at once for the text area
                    for chunk in generate_learning_stream(draft_country, draft_topic):
                        draft_text += chunk
                    st.session_state["admin_draft"] = draft_text
                st.success("Draft ready! See 'Lesson Content' below.")
            else:
                st.error("Please provide a region and subject first.")

    # 2. Final Review and Publishing Form
    with st.form("admin_publish_form"):
        # We pre-fill the form with the AI draft if it exists
        final_country = st.text_input("Confirm Region", value=draft_country)
        final_topic = st.text_input("Confirm Title", value=draft_topic)
        
        current_draft = st.session_state.get("admin_draft", "")
        final_content = st.text_area("Lesson Content & Quiz", value=current_draft, height=400)
        
        submitted = st.form_submit_button("🚀 Publish to All Students")
        
        if submitted:
            if final_country and final_topic and final_content:
                save_topic("admin-system", final_country, final_topic, final_content, is_global=1)
                st.success(f"Successfully published '{final_topic}' to the Global Quiz tab!")
                # Clear draft after success
                if "admin_draft" in st.session_state: del st.session_state["admin_draft"]
            else:
                st.error("All fields are required to publish.")