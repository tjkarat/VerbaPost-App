from fpdf import FPDF
import os

def create_pdf(text_content, recipient_info, return_address_info, is_heirloom, language="English", filename="output_letter.pdf", signature_path="temp_signature.png"):
    print(f"📄 Formatting PDF in {language}...")
    
    # Setup PDF (Standard US Letter)
    pdf = FPDF(orientation='P', unit='mm', format='Letter')
    pdf.add_page()
    
    # --- FONT SETUP ---
    font_family = "Helvetica"
    font_map = {
        "English": "IndieFlower-Regular.ttf",
        "Chinese": "MaShanZheng-Regular.ttf",
        "Japanese": "Yomogi-Regular.ttf"
    }
    target_font = font_map.get(language, "IndieFlower-Regular.ttf")
    
    if os.path.exists(target_font):
        pdf.add_font('Handwriting', '', target_font)
        font_family = 'Handwriting'

    # --- LAYOUT LOGIC ---
    if is_heirloom:
        # HEIRLOOM: Manual Fulfillment
        # Print everything normally since you are mailing it.
        
        # 1. Return Address (Top Left)
        pdf.set_font("Helvetica", size=10)
        pdf.set_xy(10, 10)
        if return_address_info:
            pdf.multi_cell(0, 5, return_address_info)
        
        # 2. Recipient Address (Window Position)
        pdf.set_y(45)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 6, recipient_info)
        
        # 3. Start Body below address
        pdf.set_y(80)
        
    else:
        # STANDARD (LOB): Automated Fulfillment
        # Lob needs the top 4 inches (approx 100mm) CLEAN for the address block.
        # We push the text start position down to 110mm to be safe.
        
        pdf.set_y(110) # <--- THE FIX (Moves text below the barcode area)

    # --- BODY TEXT ---
    body_size = 16 if language in ["Chinese", "Japanese"] else 14
    pdf.set_font(font_family, size=body_size)
    pdf.multi_cell(0, 8, text_content)
    
    # --- SIGNATURE ---
    pdf.ln(10)
    if os.path.exists(signature_path):
        try:
            # Ensure signature fits on page
            if pdf.get_y() > 250: pdf.add_page()
            pdf.image(signature_path, w=40) 
        except:
            pass
    
    # --- FOOTER ---
    if not is_heirloom:
        # Ensure footer is at bottom of current page
        pdf.set_y(-20) 
        pdf.set_font("Helvetica", 'I', 9)
        pdf.cell(0, 10, "Dictated via verbapost.com", ln=1, align='C')
    
    pdf.output(filename)
    return os.path.abspath(filename)