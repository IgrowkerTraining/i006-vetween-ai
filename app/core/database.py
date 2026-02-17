from supabase import create_client , Client
from app.config.settings import settings

# Creacion cliente supabase
supabase : Client = create_client(
    settings.supabase_url,
    settings.supabase_key
)