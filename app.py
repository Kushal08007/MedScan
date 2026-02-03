import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import pandas as pd
import re
import datetime
import base64
from deep_translator import GoogleTranslator 
import streamlit.components.v1 as components 


#PWA STYLE CODE
st.markdown("""
<link rel="manifest" href="/
manifest.json">
<link rel="apple-touch-icon" href="/applogo.png">
 <meta name="theme-color"
  content="#0B0B0B">          
            """, unsafe_allow_html=True)

#BACKGROUND ANIMATION
st.markdown("""
<style>
.stApp {
    background: linear-gradient(
        -45deg,
        #0B0B0B,
        #070A12,
        #0A0F1C,
        #121522 
    );
    background-size: 600% 600%;
    animation: deepOcean 15s ease-in-out infinite;
}

@keyframes deepOcean {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
</style>
""", unsafe_allow_html=True)



#declares
med_name = ""
expiry_display = ""
display_uses = ""
display_effects = ""
speech_text = ""
speech_lang = "en-US" 
language = "English" 

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(page_title="MedScan", page_icon="logo.jpeg", layout="centered")

# ===============================
# NETFLIX-STYLE LOGO (TOP-LEFT)
# ===============================
with open("logo.jpeg", "rb") as f:
    logo_base64 = base64.b64encode(f.read()).decode()

st.markdown (f"""
<style>
.fixed-logo {{
    position: fixed;
    top: 48px;
    left: 48px; 
    z-index: 1000;
    max-height: 70px;
}} 
.fixed-logo img {{
    max-height: 70px;
    width: auto; 
}}
.fixed-logo {{
    display: flex;
    align-items: center;
    gap: 10px;
}}
.welcome-text {{
    font-size: 25px;
    font-weight: 600;
    color: #94a3b8;
    letter-spacing; 1px;
}}
.scan-box {{
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 22px;
    margin-top: 25px;
}}
.scan-title {{
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 16px;
}}
.safe-bar {{
    margin-top: 16px;
    background: linear-gradient(90deg,#10b981,#22c55e);
    padding: 12px;
    border-radius: 10px;
    color: black;
    font-weight: 600;
    text-align: center;
}}
</style>

<div class="fixed-logo">
    <img src="data:image/png;base64,{logo_base64}" width="90">
    <span class="welcome-text"> WELCOME, </span>
</div>
""", unsafe_allow_html=True)

# ===============================
# LOAD OCR
# ===============================
@st.cache_resource
def load_ocr():
    return easyocr.Reader(["en"], gpu=False)

reader = load_ocr()

# ===============================
# LOAD DATABASE
# ===============================
@st.cache_data
def load_db():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTqzT7rc1BTGEoUdba7IREg3-AmYxX-aleDsxvJDMSDRkqIDSWqWXkuIfre9wAyBoBVtc_pc--VEZlI/pub?gid=0&single=true&output=csv"
    df = pd.read_csv(url)
    df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_")
    df["name"] = df["name"].astype(str).str.lower().str.strip()
    return df

medicine_db = load_db()
medicine_names = medicine_db["name"].tolist()

# ===============================
# HELPERS
# ===============================
def resize_for_ocr(img, max_width=700):
    w, h = img.size
    if w > max_width:
        ratio = max_width / w
        return img.resize((int(w * ratio), int(h * ratio)))
    return img

def extract_expiry(text):
    text = text.upper()

    # 1️⃣ Numeric formats: MM/YYYY, MM-YYYY, MM.YYYY, MM YYYY
    m1 = re.search(
        r"(0[1-9]|1[0-2])[\s\/\.\-](20\d{2})",
        text
    )
    if m1:
        return f"{m1.group(1)}/{m1.group(2)}"

    # 2️⃣ Month name + full year: OCT 2027, OCT.2027, OCT-2027, OCT/2027
    m2 = re.search(
        r"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)[\s\/\.\-]*(20\d{2})",
        text
    )
    if m2:
        return f"{m2.group(1)} {m2.group(2)}"

    # 3️⃣ Month name + short year: OCT'27, OCT.27, OCT-27, OCT27
    m3 = re.search(
        r"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)[\s\/\.\-']*(\d{2})",
        text
    )
    if m3:
        return f"{m3.group(1)} 20{m3.group(2)}"

    return "UNKNOWN"

def detect_medicine_name(ocr_text):
    text = ocr_text.lower()
    for name in medicine_names:
        if name in text:
            return name
    return None

def get_medicine_info(input_name):
    input_name = input_name.lower().strip()
    row = medicine_db[medicine_db["name"] == input_name]
    if row.empty:
        return None, None
    return row.iloc[0]["uses"], row.iloc[0]["side_effects"]



def translate_if_needed(text, language):
    if not text or language == "English":
        return text
    try:
        return GoogleTranslator(source="en", target="kn").translate(text)
    except:
         return text #safety : fallback to english

# ===============================
# TITLE
# ===============================
st.markdown("""
<h1 style="margin-bottom:0;">MEDSCAN</h1>
<p style="color:#9aa4b2;margin-top:-8px;">Smart Medicine Scanner</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ===============================
# INPUT
# ===============================
tab1, tab2 = st.tabs(["📸 LIVE SCAN", "📁 UPLOAD FILE"])
img_file = None

with tab1:
    cam = st.camera_input("SCAN MEDICINE STRIP")
    if cam:
        img_file = cam

with tab2:
    file = st.file_uploader("UPLOAD IMAGE", type=["jpg", "jpeg", "png"])
    if file:
        img_file = file

# ===============================
# SESSION STATE
# ===============================
st.session_state.setdefault("ocr_text", "")
st.session_state.setdefault("auto_name", None)

# ===============================
# SCAN BUTTON
# ===============================
st.markdown ("""
<style>
    div.stButton > button {
        border: 1px solid rgba(0,0,0,0.35) ! important;
             box-shadow: 0 2px 6px
             rgba(0,0,0,0.25);
             }
             </style>
             """,unsafe_allow_html=True)
if st.button("SCAN MEDICINE") and img_file:
    img = resize_for_ocr(Image.open(img_file))
    with st.spinner("🔍 Reading medicine strip..."):
        text = reader.readtext(np.array(img), detail=0)
        st.session_state.ocr_text = " ".join(text)
        st.session_state.auto_name = detect_medicine_name(st.session_state.ocr_text)

# ===============================
# RESULTS (FIXED & BOXED)
# ===============================
if st.session_state.ocr_text:
    expiry = extract_expiry(st.session_state.ocr_text)

    st.subheader("Medicine Name")

    if st.session_state.auto_name:
        med_name = st.text_input(
            "Detected automatically (edit if needed)",
            value=st.session_state.auto_name
        )
    else:
        med_name = st.text_input(
            "Could not detect automatically. Please enter medicine name",
            placeholder="Example: Dolo / DOLO / dolo"
        )

    if med_name.strip():
        uses, effects = get_medicine_info(med_name)

        today = datetime.date.today()
        status = "UNKNOWN"

        # ✅ DEFAULT DISPLAY (ALWAYS EXISTS)
        expiry_display = (
            "Strip clarity is not clear for expiry scan. "
            "Please manually check the strip."
        )

        if expiry != "UNKNOWN":
            # Handle numeric formats like MM/YYYY, MM.YYYY, MM-YYYY
            parts = re.split(r"[./\-]", expiry)
            if len(parts) == 2:
                m, y = parts
                try:
                    exp_date = datetime.date(int(y), int(m), 1)
                    status = "EXPIRED" if exp_date < today else "SAFE"
                    expiry_display = expiry
                except:
                    pass  # keep fallback message

        language = st.radio(
            "Language",
            ["English", "ಕನ್ನಡ"],
            horizontal=True 
        )

        display_uses = translate_if_needed(uses,language)
        display_effects = translate_if_needed(effects, language)

    # RESULTS BOX (ALWAYS RENDERS)
        st.markdown(f"""
     <div class="scan-box">
     <div class="scan-title">
        {"SCAN RESULTS" if language == "English" else "ಸ್ಕ್ಯಾನ್ ಫಲಿತಾಂಶಗಳು"}
     </div>

     <b>{"MEDICINE NAME" if language == "English" else "ಔಷಧಿ ಹೆಸರು"}:</b> {med_name}<br><br>

     <b>{"EXPIRY" if language == "English" else "ಕಾಲಾವಧಿ ಮುಕ್ತಾಯ"}:</b>
     {expiry_display}<br><br>

     <b>{"USES" if language == "English" else "ಬಳಕೆಗಳು"}:</b>
     {display_uses if display_uses else "Not found"}<br><br>

     <b>{"SIDE EFFECTS" if language == "English" else "ಪರಿಣಾಮಗಳು"}:</b>
     {display_effects if display_effects else "Not found"}

     {"<div class='safe-bar'>SAFE</div>" if status == "SAFE" else ""}
     </div>
     """, unsafe_allow_html=True)
  
   # ---------- SPEECH TEXT ----------
speech_text_en = f"""
Medicine Name: {med_name}
Expiry: {expiry_display}
Uses: {display_uses if display_uses else "Not found"}
Side Effects: {display_effects if display_effects else "Not found"}
"""

speech_text_kn = f"""
ಔಷಧಿ ಹೆಸರು: {med_name}
ಕಾಲಾವಧಿ ಮುಕ್ತಾಯ: {expiry_display}
ಬಳಕೆಗಳು: {display_uses if display_uses else "ಲಭ್ಯವಿಲ್ಲ"}
ಪರಿಣಾಮಗಳು: {display_effects if display_effects else "ಲಭ್ಯವಿಲ್ಲ"}
"""


if language == "ಕನ್ನಡ":
    speech_text = speech_text_kn
    speech_lang = "kn-IN"
else:
    speech_text = speech_text_en
    speech_lang = "en-US"


components.html(
f"""
<button style="
padding: 12px 18px;
border-radius: 16px;
border:none;
background:#0E161B;
border: 1px solid rgba(0, 0, 0, 0.45);
box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
color:white;
font-weight:600;
cursor:pointer;"
onclick="
const msg = new SpeechSynthesisUtterance(`{speech_text}`);
msg.rate = 0.95;
msg.pitch = 1;
msg.lang = '{speech_lang}';
window.speechSynthesis.cancel();
window.speechSynthesis.speak(msg);
">
🔊 Read Aloud
</button>
""",
height=80
)


# ===============================
# FOOTER
# ===============================
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#9aa4b2;font-size:12px;">
<b>Data Source:</b> Curated Medicine Database (Google Sheets) made from reference with 
NIH.gov, CDC.gov, https://www.1mg.com and W.H.O<br>
Educational use only • Consume medicine only if Prescribed
</div>
""", unsafe_allow_html=True)

