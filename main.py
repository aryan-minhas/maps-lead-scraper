import os
from dotenv import load_dotenv  # pyrefly: ignore [missing-import]

# Load environment variables from .env
load_dotenv()

def main():
    print("Initializing Maps Lead Scraper...")
    
    # Retrieve configuration keys as placeholders/examples
    places_key = os.getenv("GOOGLE_PLACES_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    supabase_url = os.getenv("SUPABASE_URL")
    
    print(f"Google Places API Key: {'Loaded' if places_key else 'Not Loaded'}")
    print(f"Gemini API Key: {'Loaded' if gemini_key else 'Not Loaded'}")
    print(f"Supabase URL: {'Loaded' if supabase_url else 'Not Loaded'}")

if __name__ == "__main__":
    main()
