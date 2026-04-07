import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

# ------------------------------
# CONFIGURATION SUPABASE (SÉCURISÉE)
# ------------------------------
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
# SYSTÈME DE CONNEXION
# ------------------------------

def verifier_connexion():
    return st.session_state.get("authentifie", False)

def afficher_ecran_connexion():
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
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state["authentifie"] = True
                st.session_state["user_email"] = email
                st.session_state["user_id"] = response.user.id
                st.rerun()
            except Exception as e:
                st.error("❌ Email ou mot de passe incorrect")

def deconnexion():
    if st.sidebar.button("🚪 Se déconnecter"):
        supabase.auth.sign_out()
        st.session_state["authentifie"] = False
        st.session_state["user_id"] = None
        st.session_state["user_email"] = None
        st.rerun()

# ------------------------------
# FONCTIONS SUPABASE
# ------------------------------

def load_data():
    try:
        response = supabase.table("clients").select("*").eq("user_id", st.session_state["user_id"]).execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur de chargement : {e}")
        return pd.DataFrame()

def ajouter_client(client_data):
    try:
        client_data["user_id"] = st.session_state["user_id"]
        response = supabase.table("clients").insert(client_data).execute()
        return response
    except Exception as e:
        st.error(f"Erreur détaillée : {e}")
        return None

def modifier_client(client_id, client_data):
    response = supabase.table("clients").update(client_data).eq("id", client_id).eq("user_id", st.session_state["user_id"]).execute()
    return response

def supprimer_client(client_id):
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
# INITIALISATION
# ------------------------------
if "authentifie" not in st.session_state:
    st.session_state["authentifie"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None

# ------------------------------
# AFFICHAGE PRINCIPAL
# ------------------------------

if not verifier_connexion():
    afficher_ecran_connexion()
else:
    st.sidebar.markdown(f"👤 Connecté : **{st.session_state.get('user_email', 'Admin')}**")
    deconnexion()
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio(
        "Navigation",
        ["📋 Liste des clients", "➕ Ajouter un client", "✏️ Modifier un client", "🗑️ Supprimer un client", "📊 Tableau de bord"]
    )
    
    df = load_data()
    st.sidebar.markdown(f"📊 **Total :** {len(df)} clients")
    
    # --------------------------
    # LISTE DES CLIENTS
    # --------------------------
    if menu == "📋 Liste des clients":
        st.subheader("📋 Liste des clients")
        if df.empty:
            st.info("Aucun client. Cliquez sur 'Ajouter'")
        else:
            colonnes_affichees = ["nom_complet", "email", "type_contrat", "statut", "date_echeance"]
            st.dataframe(df[colonnes_affichees], use_container_width=True)
    
    # --------------------------
    # AJOUTER UN CLIENT (CORRIGÉ)
    # --------------------------
    elif menu == "➕ Ajouter un client":
        st.subheader("➕ Nouveau client")
        with st.form("add_form"):
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("Nom complet*")
                email = st.text_input("Email*")
                telephone = st.text_input("Téléphone")
                type_contrat = st.selectbox("Type contrat", ["Auto", "Habitation", "Santé", "Prévoyance"])
                numero_contrat = st.text_input("Numéro de contrat")
            with col2:
                date_mise = st.date_input("Date mise en assurance", datetime.now().date())
                duree = st.number_input("Durée (mois)", 1, 60, 12)
                montant = st.number_input("Montant versé (FCFA)", 0.0, step=50.0)
                nom_carte_grise = st.text_input("Nom sur carte grise")
                statut = st.selectbox("Statut", ["Actif", "En relance", "Expiré"])
                notes = st.text_area("Notes", height=68)
            
            if st.form_submit_button("✅ Ajouter", use_container_width=True):
                if not nom:
                    st.error("Le nom complet est obligatoire")
                elif not email:
                    st.error("L'email est obligatoire")
                else:
                    echeance = calculer_echeance(date_mise, duree)
                    
                    client_data = {
                        "nom_complet": nom,
                        "email": email,
                        "telephone": telephone if telephone else None,
                        "type_contrat": type_contrat,
                        "numero_contrat": numero_contrat if numero_contrat else None,
                        "date_mise_assurance": str(date_mise),
                        "duree_mois": duree,
                        "date_echeance": str(echeance) if echeance else None,
                        "montant_verse": float(montant),
                        "nom_carte_grise": nom_carte_grise if nom_carte_grise else None,
                        "statut": statut,
                        "notes": notes if notes else None
                    }
                    
                    result = ajouter_client(client_data)
                    if result:
                        st.success(f"✅ Client {nom} ajouté avec succès !")
                        st.rerun()
    
    # --------------------------
    # MODIFIER UN CLIENT
    # --------------------------
    elif menu == "✏️ Modifier un client":
        st.subheader("✏️ Modifier un client")
        
        if df.empty:
            st.warning("Aucun client à modifier")
        else:
            options = ["-- Choisir un client --"] + df["nom_complet"].tolist()
            selected = st.selectbox("Sélectionner un client", options)
            
            if selected != "-- Choisir un client --":
                client = df[df["nom_complet"] == selected].iloc[0]
                
                with st.form("edit_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nom = st.text_input("Nom complet", value=client["nom_complet"])
                        email = st.text_input("Email", value=client["email"])
                        telephone = st.text_input("Téléphone", value=client.get("telephone", ""))
                        type_contrat = st.selectbox("Type contrat", 
                            ["Auto", "Habitation", "Santé", "Prévoyance"],
                            index=["Auto", "Habitation", "Santé", "Prévoyance"].index(client["type_contrat"]) if client["type_contrat"] in ["Auto", "Habitation", "Santé", "Prévoyance"] else 0)
                        numero_contrat = st.text_input("Numéro de contrat", value=client.get("numero_contrat", ""))
                    with col2:
                        date_mise = pd.to_datetime(client["date_mise_assurance"]).date() if client.get("date_mise_assurance") else datetime.now().date()
                        date_mise = st.date_input("Date mise en assurance", value=date_mise)
                        duree = st.number_input("Durée (mois)", 1, 60, int(client["duree_mois"]) if client.get("duree_mois") else 12)
                        montant = st.number_input("Montant versé (FCFA)", value=float(client["montant_verse"]) if client.get("montant_verse") else 0.0, step=50.0)
                        nom_carte_grise = st.text_input("Nom sur carte grise", value=client.get("nom_carte_grise", ""))
                        statut = st.selectbox("Statut", ["Actif", "En relance", "Expiré"],
                            index=["Actif", "En relance", "Expiré"].index(client["statut"]))
                        notes = st.text_area("Notes", value=client.get("notes", ""), height=68)
                    
                    if st.form_submit_button("💾 Sauvegarder", use_container_width=True):
                        nouvelle_echeance = calculer_echeance(date_mise, duree)
                        
                        modifier_client(client["id"], {
                            "nom_complet": nom,
                            "email": email,
                            "telephone": telephone if telephone else None,
                            "type_contrat": type_contrat,
                            "numero_contrat": numero_contrat if numero_contrat else None,
                            "date_mise_assurance": str(date_mise),
                            "duree_mois": duree,
                            "date_echeance": str(nouvelle_echeance) if nouvelle_echeance else None,
                            "montant_verse": float(montant),
                            "nom_carte_grise": nom_carte_grise if nom_carte_grise else None,
                            "statut": statut,
                            "notes": notes if notes else None
                        })
                        st.success("✅ Client modifié avec succès !")
                        st.rerun()
    
    # --------------------------
    # SUPPRIMER UN CLIENT
    # --------------------------
    elif menu == "🗑️ Supprimer un client":
        st.subheader("🗑️ Supprimer un client")
        
        if df.empty:
            st.warning("Aucun client à supprimer")
        else:
            options = ["-- Choisir un client --"] + df["nom_complet"].tolist()
            selected = st.selectbox("Sélectionner un client", options)
            
            if selected != "-- Choisir un client --":
                client = df[df["nom_complet"] == selected].iloc[0]
                
                st.warning(f"⚠️ Êtes-vous sûr de vouloir supprimer **{selected}** ?")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Oui, supprimer", use_container_width=True):
                        supprimer_client(client["id"])
                        st.success(f"✅ Client {selected} supprimé !")
                        st.rerun()
                with col2:
                    if st.button("❌ Annuler", use_container_width=True):
                        st.rerun()
    
    # --------------------------
    # TABLEAU DE BORD
    # --------------------------
    elif menu == "📊 Tableau de bord":
        st.subheader("📊 Tableau de bord")
        
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("📊 Clients actifs", len(df[df["statut"] == "Actif"]) if "statut" in df else 0)
            col2.metric("💰 Total versé", f"{df['montant_verse'].sum():,.0f} FCFA" if "montant_verse" in df else "0 €")
            col3.metric("👥 Total clients", len(df))
            
            st.markdown("---")
            st.markdown("#### 📈 Répartition par type de contrat")
            if "type_contrat" in df:
                repartition = df["type_contrat"].value_counts()
                st.bar_chart(repartition)
        else:
            st.info("Aucune donnée à afficher")