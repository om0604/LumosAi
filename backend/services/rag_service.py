import os
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from config import config

# Load embedding model
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def build_index(chunks, index_path=None, meta_path=None):
    """Generate embeddings and build FAISS index"""
    print("Generating embeddings...")
    texts = [chunk['content'] for chunk in chunks]
    embeddings = embedder.encode(texts, show_progress_bar=True)
    embeddings = np.array(embeddings).astype('float32')
    
    metadata = {i: chunk for i, chunk in enumerate(chunks)}
    
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    i_path = index_path or os.path.join(config.BASE_DIR, config.INDEX_FILE)
    m_path = meta_path or os.path.join(config.BASE_DIR, config.METADATA_FILE)
    faiss.write_index(index, i_path)
    with open(m_path, 'wb') as f:
        pickle.dump(metadata, f)
        
    print(f"Saved {len(chunks)} chunks to {i_path} and {m_path}")
    return index, metadata

def load_index(index_path=None, meta_path=None):
    i_path = index_path or os.path.join(config.BASE_DIR, config.INDEX_FILE)
    m_path = meta_path or os.path.join(config.BASE_DIR, config.METADATA_FILE)
    
    if not os.path.exists(i_path) or not os.path.exists(m_path):
        return None, None
    index = faiss.read_index(i_path)
    with open(m_path, 'rb') as f:
        metadata = pickle.load(f)
    return index, metadata

def retrieve(query, top_k=5, index_path=None, meta_path=None):
    index, metadata = load_index(index_path, meta_path)
    if index is None:
        raise ValueError("FAISS index not found. Please build the index first.")
        
    query_embedding = embedder.encode([query]).astype('float32')
    distances, indices = index.search(query_embedding, top_k)
    
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx != -1:
            chunk = metadata[idx].copy()
            chunk['score'] = float(dist)
            results.append(chunk)
            
    return results

def generate_answer(query, contexts):
    prompt_template = """You are an AI Document Assistant.

Answer the question ONLY using the provided context.
If the answer is not found in the context, respond:
"The answer is not available in the provided document."

Context:
{context}

Question:
{question}

Answer:"""
    
    context_text = "\n\n".join([f"Page {c['page']}:\n{c['content']}" for c in contexts])
    formatted_prompt = prompt_template.format(context=context_text, question=query)
    
    try:
        from groq import Groq
        # Initialize Groq client
        client = Groq(api_key=config.GROQ_API_KEY)
        
        # Call Groq API with configured model
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": formatted_prompt}],
            model=config.GROQ_MODEL,
            temperature=0,
            max_tokens=500,
        )
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        return f"Error connecting to Groq API: {str(e)}"
