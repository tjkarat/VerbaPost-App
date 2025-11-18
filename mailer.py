import requests
import time
import os

# This is where we would put your API Key eventually
API_KEY = "TEST_API_KEY_12345"
API_URL = "https://api.lob.com/v1/letters"

def send_letter(pdf_path):
    print(f"📮 Preparing to mail: {os.path.basename(pdf_path)}")
    
    # 1. Check if file exists
    if not os.path.exists(pdf_path):
        print("❌ Error: PDF file not found.")
        return False

    # 2. Simulate the Network Delay
    print("☁️  Connecting to Postal API...")
    time.sleep(1.5) # Pausing to make it feel real
    print("📤 Uploading PDF document...")
    time.sleep(1.5)
    
    # 3. The "Mock" Response
    # (In the real world, we would use requests.post() here)
    print("✅ SUCCESS: API received the file.")
    print("🚚 Status: Queued for printing.")
    print("📍 Estimated Delivery: 4-6 business days.")
    
    return True

if __name__ == "__main__":
    # Test run
    send_letter("final_letter.pdf")