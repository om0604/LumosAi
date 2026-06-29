from database import get_supabase
from config import config

def test_connection():
    try:
        print("URL:", config.SUPABASE_URL)
        print("Key starts with:", config.SUPABASE_SERVICE_ROLE_KEY[:20])

        supabase = get_supabase()

        response = supabase.table("documents").select("*").limit(1).execute()

        print("✅ Successfully connected!")
        print(response.data)

    except Exception as e:
        print(type(e))
        print(e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()