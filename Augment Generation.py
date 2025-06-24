def generate_augmented_prompt(user_prompt, md_text):
    prompt = f"""
You are an AI assistant. Use the following context information to answer the user's question.

--- Start of Context ---

{md_text}

--- End of Context ---

User's Question: {user_prompt}
Answer:
"""
    return prompt
def load_markdown_file(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        return f.read()

md_path = r"C:\Users\ayush\Downloads\Pride&Prejudice.md"
md_text = load_markdown_file(md_path)

user_prompt = "Give me the summary of this book?"
augmented_prompt = generate_augmented_prompt(user_prompt, md_text)

print(augmented_prompt)
