from pathlib import Path
from docx import Document
import pandas as pd
import PyPDF2

def extract_text_from_file(file_path: str, chunk_size: int = 20) -> str:
    ext = Path(file_path).suffix.lower()

    try:
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        elif ext == ".pdf":
            text = ""
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
            return text

        elif ext == ".docx":
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])

        elif ext == ".csv":
            df = pd.read_csv(file_path)
            header = ", ".join(df.columns)
            chunks = []

            for start in range(0, len(df), chunk_size):
                chunk_df = df.iloc[start:start + chunk_size]
                chunk_text = chunk_df.to_string(index=False, header=False)
                chunks.append(f"{header}\n{chunk_text}")

            return chunks

        else:
            return ""
    except Exception as e:
        print(f"Failed to extract text from {file_path}: {e}")
        return ""
