import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

# ------------------------------
# CONFIGURATION SUPABASE (SÉCURISÉE)
# ------------------------------
# Les vraies valeurs sont lues depuis les "secrets" du cloud
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------
# CONFIGURATION DE LA PAGE
# ------------------------------
st.set_page_config(
    page_title="Gestion Clients Assurance",
    page_icon="📋",
    layout="wide"
)

# ------------------------------
# SYSTÈME DE CONNEXION (AVEC SUPABASE)
# ------------------------------

def verifier_connexion():
    """Vérifie si l'utilisateur est connecté"""
    return st.session_state.get("authentifie", False)

def afficher_ecran_connexion():
    """Affiche l'écran de connexion"""
    st.markdown("""
    <div style="text-align: center; padding: 50px;">
        <h1>📋 Gestion Clients Assurance</h1>
        <p>Connectez-vous pour accéder à l'application</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        email = st.text_input("Email", placeholder="exemple@email.com")
        password = st.text_input("Mot de passe", type="password")
        
        if st.button("🔐 Se connecter", use_container_width=True):
            try:
                # Connexion VIA SUPABASE
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                # Si succès
                st.session_state["authentifie"] = True
                st.session_state["user_email"] = email
                st.session_state["user_id"] = response.user.id
                st.rerun()
            except Exception as e:
                st.error(f"❌ Email ou mot de passe incorrect")
                # Pour debug : st.error(f"Erreur technique : {e}")

def deconnexion():
    """Déconnecte l'utilisateur"""
    if st.sidebar.button("🚪 Se déconnecter"):
        supabase.auth.sign_out()
        st.session_state["authentifie"] = False
        st.session_state["user_id"] = None
        st.rerun()

# ------------------------------
# FONCTIONS SUPABASE
# ------------------------------

def load_data():
    """Charge les clients depuis Supabase"""
    try:
        response = supabase.table("clients").select("*").eq("user_id", st.session_state["user_id"]).execute()
        if response.data:
            return pd.DataFrame(response.data)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur de chargement : {e}")
        return pd.DataFrame()

def ajouter_client(client_data):
    """Ajoute un client dans Supabase"""
    client_data["user_id"] = st.session_state["user_id"]
    response = supabase.table("clients").insert(client_data).execute()
    return response

def modifier_client(client_id, client_data):
    """Modifie un client dans Supabase"""
    response = supabase.table("clients").update(client_data).eq("id", client_id).eq("user_id", st.session_state["user_id"]).execute()
    return response

def supprimer_client(client_id):
    """Supprime un client de Supabase"""
    response = supabase.table("clients").delete().eq("id", client_id).eq("user_id", st.session_state["user_id"]).execute()
    return response

def calculer_echeance(date_mise, duree_mois):
    if not date_mise or not duree_mois:
        return None
    try:
        date = pd.to_datetime(date_mise)
        duree = int(duree_mois)
        return (date + timedelta(days=30 * duree)).date()
    except:
        return None

# ------------------------------
# INITIALISATION DE LA SESSION
# ------------------------------
if "authentifie" not in st.session_state:
    st.session_state["authentifie"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None

# ------------------------------
# AFFICHAGE
# ------------------------------

if not verifier_connexion():
    afficher_ecran_connexion()
else:
    # Barre latérale
    st.sidebar.markdown(f"👤 Connecté : **{st.session_state.get('user_email', 'Admin')}**")
    deconnexion()
    st.sidebar.markdown("---")
    
    # Menu
    menu = st.sidebar.radio(
        "Navigation",
        ["📋 Liste des clients", "➕ Ajouter un client", "📊 Tableau de bord"]
    )
    
    df = load_data()
    st.sidebar.markdown(f"📊 **Total :** {len(df)} clients")
    
    if menu == "📋 Liste des clients":
        st.subheader("Liste des clients")
        if df.empty:
            st.info("Aucun client. Cliquez sur 'Ajouter'")
        else:
            colonnes_affichees = ["nom_complet", "email", "type_contrat", "statut", "date_echeance"]
            st.dataframe(df[colonnes_affichees], use_container_width=True)
    
    elif menu == "➕ Ajouter un client":
        st.subheader("Nouveau client")
        with st.form("add_form"):
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("Nom complet*")
                email = st.text_input("Email*")
                telephone = st.text_input("Téléphone")
                type_contrat = st.selectbox("Type contrat", ["Auto", "Habitation", "Santé"])
            with col2:
                date_mise = st.date_input("Date mise en assurance", datetime.now().date())
                duree = st.number_input("Durée (mois)", 1, 60, 12)
                montant = st.number_input("Montant versé (€)", 0.0, step=50.0)
                statut = st.selectbox("Statut", ["Actif", "En relance", "Expiré"])
            
            if st.form_submit_button("Ajouter"):
                if nom and email:
                    echeance = calculer_echeance(date_mise, duree)
                    ajouter_client({
                        "nom_complet": nom,
                        "email": email,
                        "telephone": telephone,
                        "type_contrat": type_contrat,
                        "date_mise_assurance": str(date_mise),
                        "duree_mois": duree,
                        "date_echeance": str(echeance) if echeance else None,
                        "montant_verse": montant,
                        "statut": statut
                    })
                    st.success("Client ajouté !")
                    st.rerun()
    
    elif menu == "📊 Tableau de bord":
        st.subheader("Tableau de bord")
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Clients actifs", len(df[df["statut"] == "Actif"]) if "statut" in df else 0)
            col2.metric("Total versé", f"{df['montant_verse'].sum():,.0f} €" if "montant_verse" in df else "0 €")
            col3.metric("Total clients", len(df))
        else:
            st.info("Aucune donnée")