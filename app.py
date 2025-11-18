import recorder
import ai_engine
import database
import letter_format
import mailer
import os

def get_address_from_user():
    print("\n--- 📬 Who is this letter for? ---")
    name = input("Recipient Name: ")
    street = input("Street Address: ")
    city = input("City: ")
    state = input("State: ")
    zip_code = input("Zip Code: ")
    
    # Format it as a single block string
    full_address = f"{name}\n{street}\n{city}, {state} {zip_code}"
    return full_address

def main():
    print("--- VERBAPOST CONTROLLER ---")
    print("1. Send a new letter")
    print("2. Exit")
    
    choice = input("Select an option: ")
    
    if choice == "1":
        audio_file = "temp_letter.wav"
        # We allow the generator to decide the name, or pass a specific one
        pdf_target = "final_letter.pdf" 
        
        # Step 1: Get Address
        recipient_data = get_address_from_user()
        
        # Step 2: Record
        print("\nStep 2: Recording...")
        input("Press ENTER when ready to record (10 seconds)...")
        recorder.record_audio(filename=audio_file, duration=10)
        
        # Step 3: Transcribe
        print("\nStep 3: Transcribing...")
        text_result = ai_engine.transcribe_audio(audio_file)
        
        # Step 4: Save to DB
        print("\nStep 4: Saving to Database...")
        database.create_letter(text_result)
        
        # Step 5: Generate PDF
        print("\nStep 5: Generating PDF...")
        # We capture the ACTUAL path created by the generator
        full_path = letter_format.create_pdf(text_result, recipient_data, pdf_target)
        
        # Step 6: Mail it
        print("\nStep 6: Sending to Post Office...")
        success = mailer.send_letter(full_path)
        
        if success:
            print("\n🎉 Process Complete!")
            print(f"   Find your letter here: {full_path}")
            
            # Use the returned path to open the file
            os.system(f"open '{full_path}'")

    else:
        print("Exiting.")

if __name__ == "__main__":
    database.init_db()
    main()