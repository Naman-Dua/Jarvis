import os
from pypdf import PdfReader
from storage import init_db, store_document_chunk

def ingest_file(file_path):
    init_db()
    filename = os.path.basename(file_path)
    text = ""
    
    if file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() + " "
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    # Split text into manageable chunks (approx 1000 chars) for the LLM
    chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
    for chunk in chunks:
        store_document_chunk(filename, chunk.strip())
    
    print(f"Successfully ingested {len(chunks)} sections from {filename}.")
    return len(chunks)

def is_ingest_request(text):
    import re
    patterns = [
        r"learn from (?:this |the )?(?:file|pdf|document) (.+)$",
        r"ingest (?:this |the )?(?:file|pdf|document) (.+)$",
        r"read (?:this |the )?(?:file|pdf|document) (.+)$",
    ]
    normalized = text.lower().strip()
    for p in patterns:
        if re.search(p, normalized):
            return True
    return False

def handle_ingest_command(text):
    import re
    patterns = [
        r"learn from (?:this |the )?(?:file|pdf|document) (.+)$",
        r"ingest (?:this |the )?(?:file|pdf|document) (.+)$",
        r"read (?:this |the )?(?:file|pdf|document) (.+)$",
    ]
    normalized = text.lower().strip()
    for p in patterns:
        match = re.search(p, normalized)
        if match:
            path = match.group(1).strip().strip("'\"")
            if not os.path.isabs(path):
                # Assume relative to current dir or user home
                path = os.path.abspath(path)
            
            if os.path.exists(path):
                try:
                    count = ingest_file(path)
                    return {"action": "ingest_file", "reply": f"I've learned from {os.path.basename(path)}. I processed {count} sections."}
                except Exception as e:
                    return {"action": "ingest_file", "reply": f"Error ingesting file: {e}"}
            else:
                return {"action": "ingest_file", "reply": f"I couldn't find the file at {path}."}
    return None

if __name__ == "__main__":
    import re
    path = input("Enter path to PDF or TXT file to teach Kora: ").strip('"')
    if os.path.exists(path):
        ingest_file(path)
    else:
        print("File not found.")