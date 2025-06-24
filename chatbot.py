import requests

API_KEY = "AIzaSyC7xNMObXQ16LlnorwnYhxxm8NfbA8txl8"

# Use the v1 endpoint (the current stable one)
URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

headers = {
    "Content-Type": "application/json"
}

data = {
    "contents": [
        {
            "parts": [
                {"text": "Tell me a joke"}
            ]
        }
    ]
}

response = requests.post(URL, headers=headers, json=data)
print(response.json())
