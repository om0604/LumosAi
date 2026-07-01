import os
import re
from typing import Union, Tuple, List, Dict, Any
from io import BytesIO
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def clean_text(text: str) -> str:
    """
    Remove extra whitespace and clean up extracted text.
    """
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def process_pdf(pdf_source: Union[str, BytesIO]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Process a PDF file or stream, extract text, and chunk it for embeddings.
    
    Args:
        pdf_source: File path or BytesIO stream of the PDF.
        
    Returns:
        A tuple containing a list of chunk dictionaries and the total page count.
    """
    if isinstance(pdf_source, str):
        if not os.path.exists(pdf_source):
            raise FileNotFoundError("PDF file not found.")
        reader = PdfReader(pdf_source)
    else:
        reader = PdfReader(pdf_source)
        
    chunks = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        length_function=len
    )

    chunk_id = 0
    page_count = len(reader.pages)
    
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue
            
        cleaned_text = clean_text(text)
        page_chunks = text_splitter.split_text(cleaned_text)
        
        for chunk_text in page_chunks:
            chunks.append({
                "chunk_id": chunk_id,
                "page": page_num + 1,
                "content": chunk_text
            })
            chunk_id += 1
            
    return chunks, page_count
