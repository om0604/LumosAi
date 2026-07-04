from database import get_supabase
from config import config

def upload_bytes_to_storage(file_bytes: bytes, destination_name: str, content_type: str = "application/pdf") -> str:
    """
    Upload file bytes to Supabase Storage.
    Returns the public URL of the uploaded file.
    """
    supabase = get_supabase()
    
    response = supabase.storage.from_(config.SUPABASE_BUCKET).upload(
        path=destination_name,
        file=file_bytes,
        file_options={"upsert": "true", "content-type": content_type}
    )
    
    public_url = supabase.storage.from_(config.SUPABASE_BUCKET).get_public_url(destination_name)
    return public_url

def delete_file_from_storage(file_name: str):
    """
    Delete a file from Supabase Storage.
    """
    supabase = get_supabase()
    supabase.storage.from_(config.SUPABASE_BUCKET).remove([file_name])

def download_file_from_storage(file_name: str) -> bytes:
    """
    Download a file from Supabase Storage and return its bytes.
    """
    supabase = get_supabase()
    return supabase.storage.from_(config.SUPABASE_BUCKET).download(file_name)

