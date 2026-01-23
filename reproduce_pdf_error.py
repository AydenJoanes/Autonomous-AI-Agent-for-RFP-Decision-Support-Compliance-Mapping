
import sys
import os
import traceback
try:
    import pypdf
    print("pypdf imported successfully")
except ImportError:
    print("pypdf NOT installed")

file_path = r"c:\Emplay-task\RFP_bid\Autonomous-AI-Agent-for-RFP-Decision-Support-Compliance-Mapping\data\sample_rfps\smol_rfp.pdf"

def test_pypdf():
    print(f"Testing pypdf on {file_path}")
    try:
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            print(f"Pages: {len(reader.pages)}")
            for i, page in enumerate(reader.pages):
                print(f"Extracting page {i}...")
                text = page.extract_text()
                print(f"Page {i} len: {len(text)}")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    test_pypdf()
