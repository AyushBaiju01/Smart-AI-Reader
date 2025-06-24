import requests
import json

api_key = "AIzaSyC7xNMObXQ16LlnorwnYhxxm8NfbA8txl8"

def call_gemini_flash_raw(augmented_prompt, api_key, model="gemini-1.5-flash"):
    """
    Calls Gemini 2.0 Flash using raw REST API (no SDK).

    Parameters:
    - augmented_prompt (str): Full prompt with context + user question.
    - api_key (str): Your Gemini API key.
    - model (str): Gemini model to use (default: gemini-1.5-flash).

    Returns:
    - str: The response text from Gemini.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": augmented_prompt}
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_json = response.json()
        return response_json['candidates'][0]['content']['parts'][0]['text']
    else:
        print(f"❌ API call failed: {response.status_code} {response.text}")
        return None


# ==========================
# NOW YOUR MAIN CODE STARTS:
# ==========================

# Dummy example just to test:
augmented_prompt = "You are an AI assistant. Answer: What is the capital of France?"

# Call your function
response_text = call_gemini_flash_raw(augmented_prompt, api_key)

# Print the response
if response_text:
    print("\n🧠 Gemini says:\n")
    print(response_text)
