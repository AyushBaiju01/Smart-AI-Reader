import google.generativeai as genai

# Set your Gemini API key
genai.configure(api_key="AIzaSyC7xNMObXQ16LlnorwnYhxxm8NfbA8txl8")

# Load your markdown file
def load_markdown_file(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        return f.read()

# Build the prompt by injecting the markdown context
def create_augmented_prompt(user_question, markdown_content):
    prompt = f"""
You are an AI assistant. Use the following timetable information to answer the user's question.

--- Start of Context ---

{markdown_content}

--- End of Context ---

User's Question: {user_question}
Answer:"""
    return prompt

# Your file path (replace with your actual file path)
md_path = r"C:\Users\ayush\Downloads\Pride&Prejudice.md"
markdown_content = load_markdown_file(md_path)

# The user's question
user_question = "Which is the oldest Veda?"

# Create the prompt
augmented_prompt = create_augmented_prompt(user_question, markdown_content)

# Use Gemini Flash 2.0 model
model = genai.GenerativeModel('gemini-1.5-flash')  # Or 'gemini-1.5-pro' for more powerful but slower

# Send the prompt
response = model.generate_content(augmented_prompt)

# Output the response
print(response.text)
