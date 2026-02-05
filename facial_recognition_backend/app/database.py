
import supabase
from app.config import settings

# Use only SUPABASE_URL and SUPABASE_KEY
supabase_client = supabase.create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
