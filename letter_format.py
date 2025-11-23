from fpdf import FPDF
import os
import requests
from datetime import datetime

# --- FONT SOURCES ---
FONTS = {
    "Caveat": "https://github.com/google/fonts/raw/main/ofl/caveat/Caveat-Regular.ttf",
    "Roboto": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf",
    "Roboto-Bold": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
}
CJK_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

def ensure_fonts():
    """Downloads necessary fonts if missing."""
    for name, url in FONTS.items():
        filename = f"{name}.ttf"
        
        # Cleanup corrupt files
        if os.path.exists(filename) and os.path.getsize(filename) < 10000:
            try: os.remove(filename)
            except: pass
            
        # Download
        if not os.path.exists(filename):
            try:
                print(f"⬇️ Downloading {name}...")
                r = requests.get(url, allow_redirects=True)
                if r.status_code == 200:
                    with open(filename, "wb") as f:
                        f.write(r.content)
            except Exception as e:
                print(f"❌ Font Error ({name}): {e}")

def create_pdf(content, recipient_addr, return_addr, is_heirloom, language, filename="letter.pdf", signature_path=None):
    ensure_fonts()
    
    pdf = FPDF()
    pdf.add_page()
    
    # --- REGISTER FONTS ---
    # We register them so FPDF knows they exist
    has_roboto = os.path.exists("Roboto.ttf")
    has_caveat = os.path.exists("Caveat.ttf")
    
    if has_roboto:
        pdf.add_font('Roboto', '', 'Roboto.ttf', uni=True)
        pdf.add_font('Roboto', 'B', 'Roboto-Bold.ttf', uni=True)
        main_font = 'Roboto'
    else:
        main_font = 'Helvetica' # Last resort fallback

    if has_caveat:
        pdf.add_font('Caveat', '', 'Caveat.ttf', uni=True)

    # --- DETERMINE BODY FONT ---
    body_font = main_font
    body_size = 12
    
    if language == "English":
        if has_caveat:
            body_font = 'Caveat'
            body_size = 16
    elif language in ["Japanese", "Chinese", "Korean"]:
        if os.path.exists(CJK_PATH):
            try:
                pdf.add_font('NotoCJK', '', CJK_PATH, uni=True)
                body_font = 'NotoCJK'
                main_font = 'NotoCJK' # Use CJK for headers too to prevent squares
            except: pass

    # --- LAYOUT ---
    
    # 1. Return Address (Top Left)
    pdf.set_font(main_font, '', 10)
    pdf.set_xy(10, 10)
    pdf.multi_cell(0, 5, return_addr)
    
    # 2. Recipient Address (Window Position)
    pdf.set_xy(20, 40)
    pdf.set_font(main_font, 'B' if main_font != 'NotoCJK' else '', 12) 
    pdf.multi_cell(0, 6, recipient_addr)
    
    # 3. Date
    pdf.set_xy(160, 10)
    pdf.set_font(main_font, '', 10)
    pdf.cell(0, 10, datetime.now().strftime("%Y-%m-%d"), ln=True, align='R')
    
    # 4. Body Content (Handwriting or CJK)
    pdf.set_xy(10, 80)
    pdf.set_font(body_font, '', body_size)
    pdf.multi_cell(0, 8, content)
    
    # 5. Signature
    if signature_path and os.path.exists(signature_path):
        pdf.ln(10)
        pdf.image(signature_path, w=40)
    
    # 6. Footer
    pdf.set_y(-20)
    pdf.set_font(main_font, '', 8) # No Italics for Roboto Regular to be safe
    pdf.cell(0, 10, 'Dictated via VerbaPost.com', 0, 0, 'C')

    # Save
    save_path = f"/tmp/{filename}"
    pdf.output(save_path)
    return save_path