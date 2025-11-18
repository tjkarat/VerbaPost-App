from fpdf import FPDF
import os

def create_pdf(text_content, recipient_info, filename="output_letter.pdf"):
    print("📄 Formatting PDF...")
    
    pdf = FPDF(orientation='P', unit='mm', format='Letter')
    pdf.add_page()
    
    # --- FONT SETUP ---
    font_path = 'IndieFlower-Regular.ttf'
    
    if os.path.exists(font_path):
        # Load the custom font
        pdf.add_font('IndieFlower', '', font_path)
        has_cursive = True
    else:
        print(f"⚠️ Warning: {font_path} not found. Using Helvetica.")
        has_cursive = False

    # --- 1. HEADER (The Logo) ---
    if has_cursive:
        pdf.set_font('IndieFlower', size=24)
    else:
        pdf.set_font("Helvetica", 'B', 16)
        
    pdf.cell(0, 10, "VerbaPost", ln=1, align='C')
    pdf.ln(20) # Add a nice gap after the logo
    
    # --- 2. RECIPIENT ADDRESS (Standard Font) ---
    # We use Helvetica here so the postman can read it easily
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 6, recipient_info)
    pdf.ln(15) # Gap between address and the letter body
    
    # --- 3. BODY TEXT (Handwritten) ---
    if has_cursive:
        pdf.set_font('IndieFlower', size=14)
    else:
        pdf.set_font("Helvetica", size=12)
    
    pdf.multi_cell(0, 8, text_content)
    
    # --- 4. FOOTER ---
    # Position at 30mm from bottom
    pdf.set_y(-30)
    pdf.set_font("Helvetica", 'I', 10)
    pdf.cell(0, 10, "Dictated via VerbaPost - verbapost.com", ln=1, align='C')
    
    pdf.output(filename)
    print(f"✅ PDF generated: {filename}")
    return os.path.abspath(filename)

# --- THE SAFETY GUARD ---
# This block ONLY runs if you run 'python3 letter_format.py' directly.
# It will NOT run when 'app.py' imports this file.
if __name__ == "__main__":
    dummy_address = "Tarak Robbana\n123 Test Lane\nMt Juliet, TN 37122"
    create_pdf("This is a test. The address should be above this text.", dummy_address)
