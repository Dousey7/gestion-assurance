from supabase import create_client

# TES vraies informations Supabase
SUPABASE_URL = "https://tkouvrwpljbyfddmsxmv.supabase.co"
SUPABASE_KEY = "sb_publishable_2xIkWATenKBZeT8lJYOOVg_d0ig21Yg"

# ⚠️ REMPLACE CES VALEURS PAR CE QUE TU AS CRÉÉ DANS SUPABASE AUTH ⚠️
# Va dans Supabase → Authentication → Users
EMAIL = "admin@assurance.fr"  # L'email que tu as créé
PASSWORD = "monmotdepasse123"  # Le mot de passe correspondant

print(f"URL: {SUPABASE_URL}")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Client Supabase créé avec succès !")
    
    # Connexion avec Supabase
    response = supabase.auth.sign_in_with_password({
        "email": EMAIL,
        "password": PASSWORD
    })
    print(f"✅ Connexion réussie !")
    print(f"User ID : {response.user.id}")
    
except Exception as e:
    print(f"❌ Erreur : {e}")