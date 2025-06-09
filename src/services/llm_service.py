# src/services/llm_service.py
from google import genai
from ..config.settings import load_settings

def get_response(prompt: str) -> str:
    try:
        settings = load_settings()
        api_key = settings.get('GOOGLE_API_KEY')

        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found. Please set it in your environment variables or settings.")

        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        
        return response.text

    except Exception as e:
        print(f"An error occurred while getting response from Gemini: {e}")
        return "Sorry, I couldn't process that."

if __name__ == '__main__':
    test_prompt = "What is the main purpose of a virtual assistant?"
    print(f"Testing Gemini API with prompt: '{test_prompt}'")
    response = get_response(test_prompt)
    print(f"Received response: {response}")