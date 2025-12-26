import os
import PyPDF2
from pathlib import Path

# Get all PDF files in current directory
pdf_files = list(Path('.').glob('*.pdf'))

print(f"Found {len(pdf_files)} PDF files")

for pdf_file in pdf_files:
    try:
        txt_file = pdf_file.with_suffix('.txt')
        print(f"Processing: {pdf_file.name}")
        
        with open(pdf_file, 'rb') as pdf:
            pdf_reader = PyPDF2.PdfReader(pdf)
            text_content = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    text_content.append(f"=== Page {page_num + 1} ===\n{text}\n")
                except Exception as e:
                    text_content.append(f"=== Page {page_num + 1} ===\n[Error extracting text: {e}]\n")
            
            full_text = "\n".join(text_content)
            
            with open(txt_file, 'w', encoding='utf-8') as txt:
                txt.write(full_text)
            
            print(f"  Extracted {len(pdf_reader.pages)} pages -> {txt_file.name}")
    except Exception as e:
        print(f"  Error processing {pdf_file.name}: {e}")

print("\nExtraction complete!")

