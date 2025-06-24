import google.generativeai as genai

def call_gemini_api(augmented_prompt, api_key, model_name="gemini-1.5-flash"):
    """
    Calls the Gemini LLM API with provided augmented prompt.

    Parameters:
    - augmented_prompt (str): The full prompt containing user input + context.
    - api_key (str): Your Gemini API key.
    - model_name (str): The Gemini model to use (default is 'gemini-1.5-flash').

    Returns:
    - str: The response text from Gemini.
    """

    # Configure Gemini client with provided API key
    genai.configure(api_key=api_key)

    # Load the model
    model = genai.GenerativeModel(model_name)

    # Send the prompt and get response
    response = model.generate_content(augmented_prompt)

    return response.text
