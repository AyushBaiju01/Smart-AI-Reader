import fitz

def pdf_to_markdown(pdf_path, md_path):
    doc = fitz.open(pdf_path)
    with open(md_path, 'w', encoding='utf-8') as md_file:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            md_file.write(f"# Page {page_num + 1}\n\n")
            md_file.write(text)
            md_file.write("\n\n---\n\n")

    print(f"✅ Conversion complete. Markdown saved to: {md_path}")

pdf_path = r"C:\Users\ayush\Downloads\Pride&Prejudice.pdf"
md_path = r"C:\Users\ayush\Downloads\Pride&Prejudice.md"

pdf_to_markdown(pdf_path, md_path)
