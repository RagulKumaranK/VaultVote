import asyncio
import os
import edge_tts  # type: ignore

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'static', 'audio')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Exact announcements required by the user
# With phonetic tuning for 'Valut Vote', 'Q R', 'Voter ID' for crystal-clear Indian English pronunciation
ANNOUNCEMENTS = {
    'welcome.mp3': "Welcome to Valut Vote. Please scan your Voter ID, Q R code.",
    'qr_success.mp3': "Q R code verified successfully.",
    'qr_invalid.mp3': "Invalid Q R code. Please try again.",
    'already_voted.mp3': "Alert! This voter has already cast their vote.",
    'face_prompt.mp3': "Please look at the camera for face verification.",
    'face_success.mp3': "Face verification successful.",
    'face_failed.mp3': "Face verification failed. Please try again.",
    'candidate_prompt.mp3': "Identity verified. Please select your preferred candidate.",
    'vote_recorded.mp3': "Your vote has been recorded successfully. Thank you for voting."
}

VOICE = "en-IN-NeerjaNeural"  # High-quality Indian English Female Neural Voice

async def generate():
    print(f"Generating announcements using {VOICE}...")
    for filename, text in ANNOUNCEMENTS.items():
        out_path = os.path.join(OUTPUT_DIR, filename)
        # Moderate speaking speed, natural pitch, dignified government-service cadence
        communicate = edge_tts.Communicate(text, VOICE, rate="-4%", pitch="+0Hz")
        await communicate.save(out_path)
        file_size = os.path.getsize(out_path)
        print(f"  [OK] {filename} -> {file_size} bytes: '{text}'")
    print("All announcements generated successfully!")

if __name__ == '__main__':
    asyncio.run(generate())
