import supabase
from app.config import settings

supabase_key = settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY
supabase_client = supabase.create_client(settings.SUPABASE_URL, supabase_key)
