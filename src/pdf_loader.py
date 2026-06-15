import pdfplumber
import os

def load_pdf(file_path):
    """Extract all text from a PDF file"""
    text = ""
    
    with pdfplumber.open(file_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"  📄 {os.path.basename(file_path)} — {total_pages} pages")
        
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:  # some pages may be empty
                text += page_text + "\n"
    
    return text


def load_all_pdfs(data_folder="data"):
    """Load all PDFs and TXT files from the data folder"""
    all_texts = {}

    # Get all PDF and TXT files
    all_files = [
        f for f in os.listdir(data_folder)
        if f.endswith(".pdf") or f.endswith(".txt")
    ]

    if not all_files:
        print("❌ No files found in data/ folder")
        return {}

    print(f"📁 Found {len(all_files)} file(s):\n")

    for filename in all_files:
        file_path = os.path.join(data_folder, filename)

        if filename.endswith(".pdf"):
            text = load_pdf(file_path)
        else:
            # Load txt file directly
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            print(f"  📄 {filename} — text file")

        all_texts[filename] = text
        print(f"  ✅ Loaded: {len(text)} characters extracted\n")

    return all_texts


def chunk_text(text, chunk_size=400, overlap=50):
    """
    Split text into overlapping chunks
    
    chunk_size = how many words per chunk
    overlap    = how many words to repeat between chunks
                 (so context is not lost at boundaries)
    """
    words = text.split()
    chunks = []
    start = 0
    
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        
        # Only add if chunk has meaningful content
        if len(chunk.strip()) > 50:
            chunks.append(chunk)
        
        # Move forward by chunk_size minus overlap
        start += chunk_size - overlap
    
    return chunks


if __name__ == "__main__":
    # Test the loader
    print("=" * 50)
    print("Testing PDF Loader")
    print("=" * 50 + "\n")
    
    all_texts = load_all_pdfs("data")
    
    if all_texts:
        print("\n--- Chunking Results ---\n")
        total_chunks = 0
        
        for filename, text in all_texts.items():
            chunks = chunk_text(text)
            total_chunks += len(chunks)
            print(f"📄 {filename}")
            print(f"   Characters: {len(text)}")
            print(f"   Chunks: {len(chunks)}")
            print(f"   First chunk preview:")
            print(f"   '{chunks[0][:150]}...'\n")
        
        print(f"✅ Total chunks across all PDFs: {total_chunks}")