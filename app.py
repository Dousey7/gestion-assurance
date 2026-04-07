import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

# ------------------------------
# CONFIGURATION SUPABASE
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
# FONCTIONS DE CONNEXION
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
# FONCTIONS CLIENTS
# ------------------------------
def load_clients():
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
        st.error(f"Erreur : {e}")
        return None

def modifier_client(client_id, client_data):
    response = supabase.table("clients").update(client_data).eq("id", client_id).eq("user_id", st.session_state["user_id"]).execute()
    return response

def supprimer_client(client_id):
    response = supabase.table("clients").delete().eq("id", client_id).eq("user_id", st.session_state["user_id"]).execute()
    return response

# ------------------------------
# FONCTIONS COMPAGNIES
# ------------------------------
def load_compagnies():
    try:
        response = supabase.table("compagnies").select("*").eq("user_id", st.session_state["user_id"]).execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def ajouter_compagnie(data):
    data["user_id"] = st.session_state["user_id"]
    response = supabase.table("compagnies").insert(data).execute()
    return response

def modifier_compagnie(compagnie_id, data):
    response = supabase.table("compagnies").update(data).eq("id", compagnie_id).eq("user_id", st.session_state["user_id"]).execute()
    return response

def supprimer_compagnie(compagnie_id):
    response = supabase.table("compagnies").delete().eq("id", compagnie_id).eq("user_id", st.session_state["user_id"]).execute()
    return response

# ------------------------------
# FONCTIONS UTILITAIRES
# ------------------------------
def calculer_echeance(date_mise, duree_mois):
    if not date_mise or not duree_mois:
        return None
    try:
        date = pd.to_datetime(date_mise)
        duree = int(duree_mois)
        return (date + timedelta(days=30 * duree)).date()
    except:
        return None

def afficher_fiche_client(client, compagnies_df):
    """Affiche la fiche détaillée d'un client"""
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Informations personnelles")
        st.write(f"**Nom complet :** {client.get('nom_complet', '')}")
        st.write(f"**Email :** {client.get('email', '')}")
        st.write(f"**Téléphone :** {client.get('telephone', 'Non renseigné')}")
    
    with col2:
        st.markdown("### 📄 Informations contrat")
        st.write(f"**Type de contrat :** {client.get('type_contrat', '')}")
        st.write(f"**Numéro de contrat :** {client.get('numero_contrat', 'Non renseigné')}")
        
        # Afficher le nom de la compagnie
        compagnie_id = client.get('compagnie_id')
        if compagnie_id and not compagnies_df.empty:
            compagnie = compagnies_df[compagnies_df['id'] == compagnie_id]
            if not compagnie.empty:
                st.write(f"**Compagnie :** {compagnie.iloc[0]['nom']}")
        else:
            st.write(f"**Compagnie :** Non renseignée")
    
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("### 📅 Dates")
        st.write(f"**Date mise en assurance :** {client.get('date_mise_assurance', '')}")
        st.write(f"**Durée :** {client.get('duree_mois', '')} mois")
        st.write(f"**Date d'échéance :** {client.get('date_echeance', '')}")
    
    with col4:
        st.markdown("### 💰 Finances & Statut")
        st.write(f"**Montant versé :** {client.get('montant_verse', 0):,.0f} €")
        st.write(f"**Nom carte grise :** {client.get('nom_carte_grise', 'Non renseigné')}")
        
        statut = client.get('statut', '')
        if statut == "Actif":
            st.success(f"**Statut :** {statut}")
        elif statut == "En relance":
            st.warning(f"**Statut :** {statut}")
        else:
            st.error(f"**Statut :** {statut}")
    
    if client.get('notes'):
        st.markdown("---")
        st.markdown("### 📝 Notes")
        st.info(client.get('notes'))

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
    
    # Menu principal
    menu = st.sidebar.radio(
        "Navigation",
        ["📋 Clients", "➕ Ajouter client", "📊 Tableau de bord", "🏢 Compagnies", "➕ Ajouter compagnie"]
    )
    
    df_clients = load_clients()
    df_compagnies = load_compagnies()
    
    st.sidebar.markdown(f"📊 **Clients :** {len(df_clients)}")
    st.sidebar.markdown(f"🏢 **Compagnies :** {len(df_compagnies)}")
    
    # --------------------------
    # LISTE DES CLIENTS
    # --------------------------
    if menu == "📋 Clients":
        st.subheader("📋 Liste des clients")
        
        if df_clients.empty:
            st.info("Aucun client. Cliquez sur 'Ajouter client'")
        else:
            # Afficher la liste
            for idx, row in df_clients.iterrows():
                with st.expander(f"📌 {row['nom_complet']} - {row['type_contrat']} - {row['statut']}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Email :** {row['email']}")
                        st.write(f"**Téléphone :** {row.get('telephone', 'Non renseigné')}")
                        st.write(f"**Échéance :** {row.get('date_echeance', 'Non renseignée')}")
                    with col2:
                        if st.button("📄 Voir la fiche", key=f"view_{row['id']}"):
                            st.session_state["client_a_voir"] = row.to_dict()
                            st.session_state["afficher_fiche"] = True
                    
                    col3, col4, col5 = st.columns(3)
                    with col3:
                        if st.button("✏️ Modifier", key=f"edit_{row['id']}"):
                            st.session_state["client_a_modifier"] = row.to_dict()
                            st.session_state["menu"] = "➕ Ajouter client"
                    with col4:
                        if st.button("🗑️ Supprimer", key=f"del_{row['id']}"):
                            supprimer_client(row['id'])
                            st.success(f"Client {row['nom_complet']} supprimé")
                            st.rerun()
            
            # Afficher la fiche si demandée
            if st.session_state.get("afficher_fiche", False):
                st.markdown("---")
                st.markdown("## 📄 Fiche client détaillée")
                afficher_fiche_client(st.session_state.get("client_a_voir", {}), df_compagnies)
                if st.button("🔙 Fermer la fiche"):
                    st.session_state["afficher_fiche"] = False
                    st.rerun()
    
    # --------------------------
    # AJOUTER/MODIFIER CLIENT
    # --------------------------
    elif menu == "➕ Ajouter client":
        client_a_modifier = st.session_state.get("client_a_modifier", None)
        
        if client_a_modifier:
            st.subheader("✏️ Modifier un client")
        else:
            st.subheader("➕ Nouveau client")
        
        with st.form("client_form"):
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("Nom complet*", value=client_a_modifier.get("nom_complet", "") if client_a_modifier else "")
                email = st.text_input("Email*", value=client_a_modifier.get("email", "") if client_a_modifier else "")
                telephone = st.text_input("Téléphone", value=client_a_modifier.get("telephone", "") if client_a_modifier else "")
                type_contrat = st.selectbox("Type contrat", ["Auto", "Habitation", "Santé", "Prévoyance"],
                    index=["Auto", "Habitation", "Santé", "Prévoyance"].index(client_a_modifier.get("type_contrat", "Auto")) if client_a_modifier else 0)
                numero_contrat = st.text_input("Numéro de contrat", value=client_a_modifier.get("numero_contrat", "") if client_a_modifier else "")
                
            with col2:
                date_mise = st.date_input("Date mise en assurance", 
                    value=pd.to_datetime(client_a_modifier.get("date_mise_assurance")).date() if client_a_modifier and client_a_modifier.get("date_mise_assurance") else datetime.now().date())
                duree = st.number_input("Durée (mois)", 1, 60, 
                    value=int(client_a_modifier.get("duree_mois", 12)) if client_a_modifier else 12)
                montant = st.number_input("Montant versé (€)", 0.0, step=50.0,
                    value=float(client_a_modifier.get("montant_verse", 0)) if client_a_modifier else 0.0)
                
                # Sélection de la compagnie
                compagnie_options = ["-- Aucune --"] + df_compagnies["nom"].tolist() if not df_compagnies.empty else ["-- Aucune --"]
                compagnie_selectionnee = ""
                if client_a_modifier and client_a_modifier.get("compagnie_id"):
                    comp = df_compagnies[df_compagnies["id"] == client_a_modifier["compagnie_id"]]
                    if not comp.empty:
                        compagnie_selectionnee = comp.iloc[0]["nom"]
                
                compagnie_nom = st.selectbox("Compagnie d'assurance", compagnie_options,
                    index=compagnie_options.index(compagnie_selectionnee) if compagnie_selectionnee in compagnie_options else 0)
                
                nom_carte_grise = st.text_input("Nom sur carte grise", value=client_a_modifier.get("nom_carte_grise", "") if client_a_modifier else "")
                statut = st.selectbox("Statut", ["Actif", "En relance", "Expiré"],
                    index=["Actif", "En relance", "Expiré"].index(client_a_modifier.get("statut", "Actif")) if client_a_modifier else 0)
                notes = st.text_area("Notes", value=client_a_modifier.get("notes", "") if client_a_modifier else "", height=68)
            
            if st.form_submit_button("✅ Enregistrer", use_container_width=True):
                if not nom or not email:
                    st.error("Le nom et l'email sont obligatoires")
                else:
                    echeance = calculer_echeance(date_mise, duree)
                    
                    # Récupérer l'ID de la compagnie
                    compagnie_id = None
                    if compagnie_nom != "-- Aucune --" and not df_compagnies.empty:
                        comp = df_compagnies[df_compagnies["nom"] == compagnie_nom]
                        if not comp.empty:
                            compagnie_id = int(comp.iloc[0]["id"])
                    
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
                        "compagnie_id": compagnie_id,
                        "nom_carte_grise": nom_carte_grise if nom_carte_grise else None,
                        "statut": statut,
                        "notes": notes if notes else None
                    }
                    
                    if client_a_modifier:
                        modifier_client(client_a_modifier["id"], client_data)
                        st.success("✅ Client modifié avec succès !")
                        st.session_state["client_a_modifier"] = None
                    else:
                        ajouter_client(client_data)
                        st.success("✅ Client ajouté avec succès !")
                    
                    st.rerun()
        
        if st.button("🔙 Annuler"):
            st.session_state["client_a_modifier"] = None
            st.rerun()
    
    # --------------------------
    # LISTE DES COMPAGNIES
    # --------------------------
    elif menu == "🏢 Compagnies":
        st.subheader("🏢 Liste des compagnies d'assurance")
        
        if df_compagnies.empty:
            st.info("Aucune compagnie. Cliquez sur 'Ajouter compagnie'")
        else:
            for idx, row in df_compagnies.iterrows():
                with st.expander(f"🏛️ {row['nom']}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if row.get('adresse'):
                            st.write(f"**Adresse :** {row['adresse']}")
                        if row.get('telephone'):
                            st.write(f"**Téléphone :** {row['telephone']}")
                        if row.get('email'):
                            st.write(f"**Email :** {row['email']}")
                        if row.get('notes'):
                            st.write(f"**Notes :** {row['notes']}")
                    
                    col3, col4 = st.columns(2)
                    with col3:
                        if st.button("✏️ Modifier", key=f"edit_comp_{row['id']}"):
                            st.session_state["compagnie_a_modifier"] = row.to_dict()
                            st.session_state["menu"] = "➕ Ajouter compagnie"
                            st.rerun()
                    with col4:
                        if st.button("🗑️ Supprimer", key=f"del_comp_{row['id']}"):
                            supprimer_compagnie(row['id'])
                            st.success(f"Compagnie {row['nom']} supprimée")
                            st.rerun()
    
    # --------------------------
    # AJOUTER/MODIFIER COMPAGNIE
    # --------------------------
    elif menu == "➕ Ajouter compagnie":
        compagnie_a_modifier = st.session_state.get("compagnie_a_modifier", None)
        
        if compagnie_a_modifier:
            st.subheader("✏️ Modifier une compagnie")
        else:
            st.subheader("➕ Nouvelle compagnie d'assurance")
        
        with st.form("compagnie_form"):
            nom = st.text_input("Nom de la compagnie*", value=compagnie_a_modifier.get("nom", "") if compagnie_a_modifier else "")
            adresse = st.text_input("Adresse", value=compagnie_a_modifier.get("adresse", "") if compagnie_a_modifier else "")
            telephone = st.text_input("Téléphone", value=compagnie_a_modifier.get("telephone", "") if compagnie_a_modifier else "")
            email_comp = st.text_input("Email", value=compagnie_a_modifier.get("email", "") if compagnie_a_modifier else "")
            notes = st.text_area("Notes", value=compagnie_a_modifier.get("notes", "") if compagnie_a_modifier else "", height=100)
            
            if st.form_submit_button("✅ Enregistrer", use_container_width=True):
                if not nom:
                    st.error("Le nom de la compagnie est obligatoire")
                else:
                    compagnie_data = {
                        "nom": nom,
                        "adresse": adresse if adresse else None,
                        "telephone": telephone if telephone else None,
                        "email": email_comp if email_comp else None,
                        "notes": notes if notes else None
                    }
                    
                    if compagnie_a_modifier:
                        modifier_compagnie(compagnie_a_modifier["id"], compagnie_data)
                        st.success("✅ Compagnie modifiée avec succès !")
                        st.session_state["compagnie_a_modifier"] = None
                    else:
                        ajouter_compagnie(compagnie_data)
                        st.success("✅ Compagnie ajoutée avec succès !")
                    
                    st.rerun()
        
        if st.button("🔙 Annuler"):
            st.session_state["compagnie_a_modifier"] = None
            st.rerun()
    
    # --------------------------
    # TABLEAU DE BORD
    # --------------------------
    elif menu == "📊 Tableau de bord":
        st.subheader("📊 Tableau de bord")
        
        if not df_clients.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("📊 Clients actifs", len(df_clients[df_clients["statut"] == "Actif"]) if "statut" in df_clients else 0)
            col2.metric("💰 Total versé", f"{df_clients['montant_verse'].sum():,.0f} €" if "montant_verse" in df_clients else "0 €")
            col3.metric("👥 Total clients", len(df_clients))
            
            st.markdown("---")
            st.markdown("#### 📈 Répartition par type de contrat")
            if "type_contrat" in df_clients:
                repartition = df_clients["type_contrat"].value_counts()
                st.bar_chart(repartition)
            
            st.markdown("---")
            st.markdown("#### 🏢 Répartition par compagnie")
            if "compagnie_id" in df_clients and not df_compagnies.empty:
                # Joindre pour avoir les noms des compagnies
                df_with_comp = df_clients.merge(df_compagnies[['id', 'nom']], left_on='compagnie_id', right_on='id', how='left')
                repartition_comp = df_with_comp['nom'].value_counts()
                st.bar_chart(repartition_comp)
        else:
            st.info("Aucune donnée à afficher")