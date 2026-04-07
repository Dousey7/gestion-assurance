import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
import plotly.express as px

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
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------
# CSS PERSONNALISÉ
# ------------------------------
st.markdown("""
<style>
    .card-client {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin-bottom: 15px;
        transition: transform 0.3s;
    }
    .card-client:hover {
        transform: translateY(-5px);
    }
    .stat-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        margin: 10px;
    }
    .badge-expired {
        background-color: #dc2626;
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
    }
    .badge-warning {
        background-color: #f59e0b;
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
    }
    .badge-ok {
        background-color: #10b981;
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
    }
    .search-box {
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# FONCTIONS DE CONNEXION
# ------------------------------
def verifier_connexion():
    return st.session_state.get("authentifie", False)

def afficher_ecran_connexion():
    st.markdown("""
    <div style="text-align: center; padding: 80px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px;">
        <h1 style="color: white;">📋 Gestion Clients Assurance</h1>
        <p style="color: white; font-size: 18px;">Connectez-vous pour accéder à l'application</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        email = st.text_input("📧 Email", placeholder="exemple@email.com")
        password = st.text_input("🔒 Mot de passe", type="password")
        
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
    if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
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

def get_echeance_status(date_echeance):
    """Retourne le statut et la couleur d'une échéance"""
    if not date_echeance or pd.isna(date_echeance):
        return {"status": "Non renseignée", "color": "gray", "icon": "❓", "days": None, "badge": "badge-ok"}
    
    try:
        echeance = pd.to_datetime(date_echeance).date()
        aujourdhui = datetime.now().date()
        jours_restants = (echeance - aujourdhui).days
        
        if jours_restants < 0:
            return {"status": "Expiré", "color": "red", "icon": "🔴", "days": jours_restants, "badge": "badge-expired"}
        elif jours_restants <= 30:
            return {"status": "Échéance imminente", "color": "orange", "icon": "🟠", "days": jours_restants, "badge": "badge-warning"}
        elif jours_restants <= 60:
            return {"status": "À surveiller", "color": "yellow", "icon": "🟡", "days": jours_restants, "badge": "badge-warning"}
        else:
            return {"status": "OK", "color": "green", "icon": "🟢", "days": jours_restants, "badge": "badge-ok"}
    except:
        return {"status": "Erreur", "color": "gray", "icon": "❓", "days": None, "badge": "badge-ok"}

def afficher_fiche_client(client, compagnies_df):
    """Affiche la fiche détaillée d'un client"""
    st.markdown("---")
    
    # En-tête avec statut
    echeance_info = get_echeance_status(client.get('date_echeance'))
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"## 📄 {client.get('nom_complet', '')}")
    with col2:
        st.markdown(f"<span class='{echeance_info['badge']}'>{echeance_info['icon']} {echeance_info['status']}</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 👤 Informations personnelles")
        st.write(f"**📧 Email :** {client.get('email', '')}")
        st.write(f"**📞 Téléphone :** {client.get('telephone', 'Non renseigné')}")
        st.write(f"**📝 Notes :** {client.get('notes', 'Aucune')}")
    
    with col2:
        st.markdown("### 📄 Informations contrat")
        st.write(f"**🏷️ Type de contrat :** {client.get('type_contrat', '')}")
        st.write(f"**🔢 Numéro de contrat :** {client.get('numero_contrat', 'Non renseigné')}")
        
        compagnie_id = client.get('compagnie_id')
        if compagnie_id and not compagnies_df.empty:
            compagnie = compagnies_df[compagnies_df['id'] == compagnie_id]
            if not compagnie.empty:
                st.write(f"**🏢 Compagnie :** {compagnie.iloc[0]['nom']}")
        else:
            st.write(f"**🏢 Compagnie :** Non renseignée")
    
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("### 📅 Dates clés")
        st.write(f"**📆 Date mise en assurance :** {client.get('date_mise_assurance', '')}")
        st.write(f"**⏱️ Durée :** {client.get('duree_mois', '')} mois")
        st.write(f"**⚠️ Date d'échéance :** {client.get('date_echeance', '')}")
        if echeance_info['days'] is not None:
            if echeance_info['days'] < 0:
                st.write(f"**📉 Dépassé depuis :** {abs(echeance_info['days'])} jours")
            elif echeance_info['days'] > 0:
                st.write(f"**📈 Jours restants :** {echeance_info['days']} jours")
    
    with col4:
        st.markdown("### 💰 Finances")
        st.write(f"**💶 Montant versé :** {client.get('montant_verse', 0):,.0f} €")
        st.write(f"**🚗 Nom carte grise :** {client.get('nom_carte_grise', 'Non renseigné')}")

def exporter_csv(df):
    """Exporte les données en CSV"""
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    return csv

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
    # ==================== SIDEBAR ====================
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 10px;">
        <h3>📋 Assurance Pro</h3>
        <p style="font-size: 14px;">👤 {st.session_state.get('user_email', 'Admin')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    deconnexion()
    st.sidebar.markdown("---")
    
    # Menu principal
    menu = st.sidebar.radio(
        "📌 Navigation",
        ["🏠 Dashboard", "👥 Clients", "➕ Nouveau client", "🏢 Compagnies", "⚙️ Paramètres"]
    )
    
    # Chargement des données
    df_clients = load_clients()
    df_compagnies = load_compagnies()
    
    # ==================== DASHBOARD ====================
    if menu == "🏠 Dashboard":
        st.markdown("# 🏠 Tableau de bord")
        st.markdown(f"Bienvenue **{st.session_state.get('user_email', 'Admin')}** ! Voici un résumé de votre activité.")
        
        st.markdown("---")
        
        # Cartes de statistiques
        col1, col2, col3, col4 = st.columns(4)
        
        total_clients = len(df_clients)
        clients_actifs = len(df_clients[df_clients["statut"] == "Actif"]) if not df_clients.empty else 0
        montant_total = df_clients["montant_verse"].sum() if not df_clients.empty and "montant_verse" in df_clients else 0
        
        # Compter les échéances critiques
        echeances_critiques = 0
        if not df_clients.empty and "date_echeance" in df_clients:
            for _, row in df_clients.iterrows():
                status = get_echeance_status(row.get("date_echeance"))
                if status["status"] in ["Expiré", "Échéance imminente"]:
                    echeances_critiques += 1
        
        with col1:
            st.metric("👥 Total clients", total_clients, delta=None)
        with col2:
            st.metric("✅ Clients actifs", clients_actifs, delta=None)
        with col3:
            st.metric("💰 Chiffre d'affaires", f"{montant_total:,.0f} €", delta=None)
        with col4:
            st.metric("⚠️ Échéances critiques", echeances_critiques, delta=None if echeances_critiques == 0 else "attention")
        
        st.markdown("---")
        
        # Graphiques
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Répartition par type de contrat")
            if not df_clients.empty and "type_contrat" in df_clients:
                repartition = df_clients["type_contrat"].value_counts()
                fig = px.pie(values=repartition.values, names=repartition.index, title="")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucune donnée")
        
        with col2:
            st.markdown("#### 📅 Échéances à venir")
            if not df_clients.empty and "date_echeance" in df_clients:
                df_echeances = df_clients.dropna(subset=['date_echeance']).copy()
                if not df_echeances.empty:
                    df_echeances['mois'] = pd.to_datetime(df_echeances['date_echeance']).dt.strftime('%Y-%m')
                    echeances_par_mois = df_echeances['mois'].value_counts().sort_index()
                    fig = px.bar(x=echeances_par_mois.index, y=echeances_par_mois.values, title="")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Aucune échéance renseignée")
            else:
                st.info("Aucune donnée")
        
        st.markdown("---")
        
        # Alertes échéances
        st.markdown("#### ⚠️ Alertes échéances (30 jours)")
        if not df_clients.empty:
            alertes = []
            for _, row in df_clients.iterrows():
                status = get_echeance_status(row.get("date_echeance"))
                if status["status"] in ["Expiré", "Échéance imminente"]:
                    jours = abs(status["days"]) if status["days"] else 0
                    if status["status"] == "Expiré":
                        alertes.append(f"🔴 **{row['nom_complet']}** : Contrat expiré depuis {jours} jours")
                    else:
                        alertes.append(f"🟠 **{row['nom_complet']}** : Échéance dans {status['days']} jours")
            
            if alertes:
                for alerte in alertes:
                    st.warning(alerte)
            else:
                st.success("✅ Aucune échéance critique dans les 30 jours")
        else:
            st.info("Aucun client enregistré")
    
    # ==================== LISTE DES CLIENTS ====================
    elif menu == "👥 Clients":
        st.markdown("# 👥 Gestion des clients")
        
        # Barre de recherche et filtres
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            recherche = st.text_input("🔍 Rechercher un client", placeholder="Nom, email ou téléphone...")
        
        with col2:
            filtre_statut = st.selectbox("📊 Statut", ["Tous", "Actif", "En relance", "Expiré"])
        
        with col3:
            filtre_echeance = st.selectbox("📅 Échéance", ["Tous", "Expirés", "< 30 jours", "< 60 jours", "Pas d'échéance"])
        
        # Application des filtres
        df_filtre = df_clients.copy() if not df_clients.empty else pd.DataFrame()
        
        if not df_filtre.empty:
            # Filtre recherche
            if recherche:
                df_filtre = df_filtre[
                    df_filtre["nom_complet"].str.contains(recherche, case=False, na=False) |
                    df_filtre["email"].str.contains(recherche, case=False, na=False) |
                    df_filtre["telephone"].astype(str).str.contains(recherche, case=False, na=False)
                ]
            
            # Filtre statut
            if filtre_statut != "Tous":
                df_filtre = df_filtre[df_filtre["statut"] == filtre_statut]
            
            # Filtre échéance
            if filtre_echeance != "Tous":
                if filtre_echeance == "Expirés":
                    df_filtre = df_filtre[df_filtre["date_echeance"].apply(lambda x: get_echeance_status(x)["status"] == "Expiré")]
                elif filtre_echeance == "< 30 jours":
                    df_filtre = df_filtre[df_filtre["date_echeance"].apply(lambda x: get_echeance_status(x)["status"] == "Échéance imminente")]
                elif filtre_echeance == "< 60 jours":
                    df_filtre = df_filtre[df_filtre["date_echeance"].apply(lambda x: get_echeance_status(x)["status"] in ["Échéance imminente", "À surveiller"])]
                elif filtre_echeance == "Pas d'échéance":
                    df_filtre = df_filtre[df_filtre["date_echeance"].isna()]
        
        st.markdown(f"📊 **{len(df_filtre)}** client(s) trouvé(s) sur **{len(df_clients)}** total")
        
        # Export
        col_export, _ = st.columns([1, 3])
        with col_export:
            if not df_filtre.empty:
                csv_data = exporter_csv(df_filtre)
                st.download_button(
                    label="📥 Exporter en CSV",
                    data=csv_data,
                    file_name=f"clients_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        st.markdown("---")
        
        # Affichage des clients
        if df_filtre.empty:
            st.info("Aucun client trouvé")
        else:
            for _, row in df_filtre.iterrows():
                echeance_info = get_echeance_status(row.get('date_echeance'))
                
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1.5, 1])
                    
                    with col1:
                        st.markdown(f"**{row['nom_complet']}**")
                        st.caption(row['email'])
                    
                    with col2:
                        st.write(f"🏷️ {row['type_contrat']}")
                        st.caption(f"💰 {row.get('montant_verse', 0):,.0f} €")
                    
                    with col3:
                        st.write(f"📅 {row.get('date_echeance', 'Non renseignée')}")
                        st.markdown(f"<span class='{echeance_info['badge']}'>{echeance_info['icon']} {echeance_info['status']}</span>", unsafe_allow_html=True)
                    
                    with col4:
                        statut = row['statut']
                        if statut == "Actif":
                            st.success(statut)
                        elif statut == "En relance":
                            st.warning(statut)
                        else:
                            st.error(statut)
                    
                    with col5:
                        if st.button("📄 Fiche", key=f"view_{row['id']}"):
                            st.session_state["client_a_voir"] = row.to_dict()
                            st.session_state["afficher_fiche"] = True
                    
                    st.markdown("---")
        
        # Afficher la fiche si demandée
        if st.session_state.get("afficher_fiche", False):
            afficher_fiche_client(st.session_state.get("client_a_voir", {}), df_compagnies)
            if st.button("🔙 Fermer la fiche"):
                st.session_state["afficher_fiche"] = False
                st.rerun()
    
    # ==================== NOUVEAU CLIENT ====================
    elif menu == "➕ Nouveau client":
        st.markdown("# ➕ Nouveau client")
        
        with st.form("client_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                nom = st.text_input("Nom complet*", placeholder="Jean Dupont")
                email = st.text_input("Email*", placeholder="jean@exemple.com")
                telephone = st.text_input("Téléphone", placeholder="06 12 34 56 78")
                type_contrat = st.selectbox("Type contrat", ["Auto", "Habitation", "Santé", "Prévoyance"])
                numero_contrat = st.text_input("Numéro de contrat", placeholder="ASS-2024-001")
            
            with col2:
                date_mise = st.date_input("Date mise en assurance", datetime.now().date())
                duree = st.number_input("Durée (mois)", 1, 60, 12)
                montant = st.number_input("Montant versé (€)", 0.0, step=50.0)
                
                compagnie_options = ["-- Aucune --"] + df_compagnies["nom"].tolist() if not df_compagnies.empty else ["-- Aucune --"]
                compagnie_nom = st.selectbox("Compagnie d'assurance", compagnie_options)
                
                nom_carte_grise = st.text_input("Nom sur carte grise", placeholder="Uniquement pour auto")
                statut = st.selectbox("Statut", ["Actif", "En relance", "Expiré"])
                notes = st.text_area("Notes", height=100, placeholder="Informations complémentaires...")
            
            # Aperçu échéance
            echeance_apercu = calculer_echeance(date_mise, duree)
            if echeance_apercu:
                st.info(f"📅 **Date d'échéance automatique :** {echeance_apercu.strftime('%d/%m/%Y')}")
            
            if st.form_submit_button("✅ Enregistrer le client", use_container_width=True):
                if not nom or not email:
                    st.error("Le nom et l'email sont obligatoires")
                else:
                    echeance = calculer_echeance(date_mise, duree)
                    
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
                    
                    ajouter_client(client_data)
                    st.success(f"✅ Client {nom} ajouté avec succès !")
                    st.balloons()
                    st.rerun()
    
    # ==================== COMPAGNIES ====================
    elif menu == "🏢 Compagnies":
        st.markdown("# 🏢 Gestion des compagnies")
        
        tab1, tab2 = st.tabs(["📋 Liste des compagnies", "➕ Ajouter une compagnie"])
        
        with tab1:
            if df_compagnies.empty:
                st.info("Aucune compagnie. Ajoutez-en une !")
            else:
                for _, row in df_compagnies.iterrows():
                    with st.expander(f"🏛️ {row['nom']}"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if row.get('adresse'):
                                st.write(f"📍 **Adresse :** {row['adresse']}")
                            if row.get('telephone'):
                                st.write(f"📞 **Téléphone :** {row['telephone']}")
                            if row.get('email'):
                                st.write(f"📧 **Email :** {row['email']}")
                            if row.get('notes'):
                                st.write(f"📝 **Notes :** {row['notes']}")
                        with col2:
                            if st.button("🗑️ Supprimer", key=f"del_comp_{row['id']}"):
                                supprimer_compagnie(row['id'])
                                st.success(f"Compagnie {row['nom']} supprimée")
                                st.rerun()
        
        with tab2:
            with st.form("add_compagnie_form"):
                nom = st.text_input("Nom de la compagnie*")
                adresse = st.text_input("Adresse")
                telephone = st.text_input("Téléphone")
                email_comp = st.text_input("Email")
                notes = st.text_area("Notes", height=100)
                
                if st.form_submit_button("✅ Ajouter la compagnie", use_container_width=True):
                    if not nom:
                        st.error("Le nom est obligatoire")
                    else:
                        ajouter_compagnie({
                            "nom": nom,
                            "adresse": adresse if adresse else None,
                            "telephone": telephone if telephone else None,
                            "email": email_comp if email_comp else None,
                            "notes": notes if notes else None
                        })
                        st.success(f"✅ Compagnie {nom} ajoutée !")
                        st.rerun()
    
    # ==================== PARAMÈTRES ====================
    elif menu == "⚙️ Paramètres":
        st.markdown("# ⚙️ Paramètres")
        
        st.markdown("### 📊 Statistiques générales")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**👥 Nombre total de clients :** {len(df_clients)}")
            st.markdown(f"**🏢 Nombre de compagnies :** {len(df_compagnies)}")
        
        with col2:
            if not df_clients.empty:
                st.markdown(f"**💰 Montant total :** {df_clients['montant_verse'].sum():,.0f} €")
                st.markdown(f"**📊 Moyenne par client :** {df_clients['montant_verse'].mean():,.0f} €")
        
        st.markdown("---")
        st.markdown("### 🗑️ Zone dangereuse")
        
        if st.button("⚠️ Supprimer TOUTES les données (irréversible)", use_container_width=True):
            st.error("🔴 Action irréversible !")
            confirmation = st.text_input("Tapez 'CONFIRMER' pour supprimer toutes les données")
            if confirmation == "CONFIRMER":
                # Supprimer tous les clients
                if not df_clients.empty:
                    for _, row in df_clients.iterrows():
                        supprimer_client(row['id'])
                # Supprimer toutes les compagnies
                if not df_compagnies.empty:
                    for _, row in df_compagnies.iterrows():
                        supprimer_compagnie(row['id'])
                st.success("Toutes les données ont été supprimées")
                st.rerun()