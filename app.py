import streamlit as st
from io import BytesIO
import pandas as pd
import base64
import plotly.express as px
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu
from pymongo import MongoClient
from datetime import datetime, timedelta
from chatbot import get_exact_answer, save_unanswered_question
# ------------------- CONFIGURATION -------------------
st.set_page_config(page_title="Chatbot BP", page_icon="🤖", layout="wide")

# ------------------- CONSTANTES MONGODB -------------------
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "chatbot_db"
QUESTIONS_COLLECTION = "unanswered_questions"
USAGE_COLLECTION = "chat_usage"

# ------------------- LOGO EN HAUT À DROITE -------------------
with open("logo_bp.png", "rb") as file_:
    contents = file_.read()
    data_url = base64.b64encode(contents).decode("utf-8")

# ------------------- STYLE CSS -------------------
st.markdown(f"""
    <style>
        /* Styles généraux */
        .stApp {{
            margin-top: -1rem;
        }}
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #0C0F0A 0%, #1E2D24 100%) !important;
            padding: 20px 10px !important;
            border-right: 1px solid #B67332 !important;
        }}
        /* Chat */
        .chat-container {{
            height: 60vh !important;
            border-radius: 16px !important;
            background-color: #F8F5F0 !important;
        }}
        /* Admin */
        .admin-container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 10px;
        }}
        .stats-card {{
            background-color: white;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
    </style>
""", unsafe_allow_html=True)
# ------------------- MENU -------------------
with st.sidebar:
    st.markdown(f"""
        <div style="text-align:center; margin-bottom:30px;">
            <img src="data:image/png;base64,{data_url}" width="80%">
        </div>
    """, unsafe_allow_html=True)
    
    onglet = option_menu(
        menu_title=None,
        options=["💬 Chatbot", "🗂️ Cartographie", "💡 Bonnes pratiques", "🔐 Admin"],
        icons=["chat-dots", "map", "book", "shield-lock"],
        default_index=0,
        styles={
            "container": {"padding": "0!important"},
            "nav-link": {
                "font-size": "15px",
                "text-align": "left",
                "margin": "5px 0",
                "border-radius": "8px",
            },
            "nav-link-selected": {
                "background-color": "#B67332",
                "font-weight": "normal",
            },
        }
    )
    st.markdown("""
        <hr style="border:0.5px solid #B67332; opacity:0.3; margin:25px 0;">
        <div style="text-align:center; color:#aaa; font-size:14px;">
            <p>Connecté en tant que :</p>
            <p><b>Inviter</b></p>
        </div>
    """, unsafe_allow_html=True)

# ------------------- SESSION -------------------
if "question" not in st.session_state:
    st.session_state.question = ""
if "reponse" not in st.session_state:
    st.session_state.reponse = ""
if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False

# ------------------- FONCTIONS UTILITAIRES -------------------
@st.cache_resource
def get_mongo_client():
    return MongoClient(MONGO_URI)

def track_chat_usage():
    try:
        client = get_mongo_client()
        db = client[DB_NAME]
        db[USAGE_COLLECTION].insert_one({
            "user_id": "anonymous",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now()
        })
    except Exception as e:
        st.error(f"Erreur de tracking : {str(e)}")

# ------------------- ONGLET CHATBOT -------------------
if onglet == "💬 Chatbot":
    # Style CSS personnalisé
    st.markdown(f"""
        <style>
            .chat-container {{  
                height: 50vh;
                overflow-y: auto;
                padding: 20px;
                background-color: #EEE6D8;
                border-radius: 30px;
                margin-bottom: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);}}
            .user-message {{
                background-color: #B67332;
                color: white;
                border-radius: 18px 18px 0 18px;
                padding: 12px 16px;
                margin: 8px 0;
                max-width: 70%;
                float: right;
                clear: both;
                box-shadow: 0 1px 3px rgba(0,0,0,0.2);}}
            .bot-message {{
                background-color: #0C0F0A;
                color: white;
                border-radius: 18px 18px 18px 0;
                padding: 12px 16px;
                margin: 8px 0;
                max-width: 70%;
                float: left;
                clear: both;
                box-shadow: 0 1px 3px rgba(0,0,0,0.2);}}
            .chat-input {{
                background-color: white;
                border-radius: 10px;
                padding: 5px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);}}
            .header {{
                text-align: center;
                margin-bottom: 20px;}}
            .logo-container {{
                position: absolute;
                top: 5px;
                right: 30px;
                z-index: 999;}}
        </style>
    """, unsafe_allow_html=True)
    # En-tête
    st.markdown("""
        <div class="header">
            <h1 style='color: #e5e7e6;'>💬 Chatbot Banque Populaire</h1>
            <p style='color: #e5e7e6; font-size: 20px;'>Je suis votre assistant bancaire Chatbot. Posez-moi vos questions ! 👇</p>
        </div>
    """, unsafe_allow_html=True)
    # Initialisation de la conversation
    if "chat" not in st.session_state:
        st.session_state.chat = []
        # Message de bienvenue initial
        st.session_state.chat.append({
            "role": "bot", 
            "msg": "Bonjour ! Je suis l'assistant virtuel de Banque Populaire. Comment puis-je vous aider aujourd'hui ?"})
    # Conteneur de chat avec défilement automatique
    chat_html = "<div class='chat-container' id='chat-container'>"
    for entry in st.session_state.chat:
        if entry["role"] == "user":
            chat_html += f"<div class='user-message'>{entry['msg']}</div>"
        else:
            chat_html += f"<div class='bot-message'>{entry['msg']}</div>"
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)
    components.html("""
    <script>
        const chatDiv = window.parent.document.querySelector('#chat-container');
        if (chatDiv) {
            chatDiv.scrollTop = chatDiv.scrollHeight;
        }
    </script>
""", height=0)
    # Zone de saisie
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        with col1:
            question = st.text_input(
                "Votre message",
                placeholder="Tapez votre question ici...",
                key="user_input",
                label_visibility="collapsed"
)
        with col2:
            send = st.form_submit_button("➤", help="Envoyer", use_container_width=True)
        if send and question.strip():
# Ajout du message utilisateur
            st.session_state.chat.append({"role": "user", "msg": question})    
  # Simulation de délai pour le bot
            with st.spinner("Je réfléchis..."):
    # Récupération de la réponse
                reponse = get_exact_answer(question.strip())
                if reponse:
                    st.session_state.chat.append({"role": "bot", "msg": reponse})
                else:
                    default_msg = "Je n'ai pas trouvé d'information précise sur ce sujet. La question est enregistrée pour des traitements futurs."
                    st.session_state.chat.append({"role": "bot", "msg": default_msg})
                    save_unanswered_question(question.strip())
            from chatbot import save_session
            save_session()
            st.rerun()
    # Bouton de réinitialisation stylisé
    if st.button("🔃 Nouvelle conversation"):
        st.session_state.chat = [{
            "role": "bot", 
            "msg": "Bonjour ! Je suis l'assistant virtuel de Banque Populaire. Comment puis-je vous aider aujourd'hui ?"
        }]
        st.rerun()

# ------------------- ONGLET CARTOGRAPHIE -------------------
elif onglet == "🗂️ Cartographie":
    st.markdown(f"""
        <style>
            .header {{
                text-align: center;
                margin-bottom: 20px; }}
        </style>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div class="header">
            <h1 style='color: #e5e7e6;'>🗂️ Cartographie des incidents</h1>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
            <p style='color: #e5e7e6; font-size: 25px;'>🔎 Consultez rapidement et ciblez les incidents opérationnels pour identifier les causes de vos dysfonctionnements !</p>
            <p style='color: #e5e7e6; font-size: 20px;'>Rechercher un domaine 👇 :</p>
    """, unsafe_allow_html=True)
    search_term = st.text_input(
        "", 
        label_visibility="collapsed",
        placeholder="Saisissez un domaine...",
        key="search_input")
    df = pd.read_excel("cartographie_incidents.xlsx")
    if search_term:
        filtered_df = df[df["Domaine"].str.contains(search_term, case=False, na=False)]
        nb = len(filtered_df)
        st.success(f"✅ {nb} résultat(s) pour : {search_term}")
        if nb > 0:
            st.dataframe(filtered_df[["Transaction", "Nature d'Incident", "Mode Opératoire"]], 
                         use_container_width=True, height=600)
            def to_excel(data):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    data.to_excel(writer, index=False, sheet_name='Résultats')
                return output.getvalue()
            excel_bytes = to_excel(filtered_df)
            st.download_button("Télécharger les résultats", data=excel_bytes,
                file_name="resultats.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("💡 Entrez un domaine ou un mot-clé pour explorer la cartographie.")

# ------------------- ONGLET BONNES PRATIQUES -------------------
elif onglet == "💡 Bonnes pratiques":
    st.markdown(f"""
        <style>
            .header {{
                text-align: center;
                margin-bottom: 20px;
            }}
        </style>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div class="header">
            <h1 style='color: #e5e7e6;'>💡Bonnes pratiques opérationnelles</h1>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
           <p style='color: #e5e7e6; font-size: 25px;'>🔎 Consultez les bases de procédures opérationnelles et conseils métiers utilisés dans les agences Banque populaire </p>  
        <p style='color: #e5e7e6; font-size: 20px;'><strong>Voici un recueil de bonnes pratiques 👇 :</strong></p>
    """, unsafe_allow_html=True)
    bonnes_pratiques = {
       "Paiement des frais d'enregistrement de la carte de l'auto-entrepreneur : référence sur T24 13 chiffres au lieu de 12 (transaction PFA)": "Dérouler l'opération sur le Legacy en effectuant une opération d'encaissement sur T24",
  "Compte reçu par mutation affiche le message compte non géré par votre agence": "Le processus partagé sur la com Hello Sprint est a respecter en renseignant la demande : mutation Tiers ou mutation compte et en la communiquant au DGSI de la BPR",
  "Champ taille entreprise": "Ce champ n’est pas modifiable en agence, la gestion est centralisée à la BCP via une mise a jour automatisée par chargement de fichier",
  "Eligibilité compte/ packs": "L’éligibilité aux Comptes et packs est calculée à partir de la signalétique client, la première vérification à faire en cas de problème et de checker les données signalétiques.",
  "Retrait déplacé sans chèque au titulaire du compte": "L'agence doit faire un retrait MAD pour lui-même au lieu de Chaabi Cash sauf en cas d’un forçage sur le compte du client",
  "Pour éviter l'affichage du message \"MAD réglée\" lors du règlement des MAD": "Ne pas fermer la fenêtre avant l'aboutissement de l'opération",
  "Retraits sans chèques sans commissions": "Les frais des retraits sans chèques ne sont pas prélevés pour les deux cas suivants :\n1. Client nouvellement crée ne disposant pas de moyens de paiement (pendant un délai de 3 semaines)\n2. Client interdit de chéquiers jusqu'à régularisation de sa situation\n\nPour les cas normaux la commission est de 33DH quel que soit le montant.",
  "Accès à la caisse": "Le RA peut disposer de deux caisses (caisse secondaire et caisse principale), toutefois, pour y accéder une seule caisse peut être ouverte",
  "Chéquiers qui ne sont pas physiquement reçus et s'affichent sur le SI T24 pour réception": "Les anciennes commandes de chéquiers qui n’ont pas abouti et qui remontent à des dates très anciennes (Juin et juillet) dont les carnets ne sont pas physiquement reçus par l’agence peuvent être détruits sur T24 en utilisant le code : 16 = Annulation",
  "Pour permettre au CTN GC de lever la surveillance « dossier juridique en cours de validation »": "Il y a lieu de :\nS’assurer que les deux champs « Motif de levée de la surveillance » et « Commentaire désactivation/modification » sont à blanc et dénouer les opérations en instance de validation objet de « Pending Approval » au niveau de l’overview du compte.",
  "Paiement d'une opération RIA": "Le paiement d’une opération RIA n’est effectif qu’après édition du bordereau, si l’utilisateur n’arrive pas à l’étape de l’impression l’opération est considérée comme non autorisée et le client ne doit pas être servi.",
  "Mise à disposition": "Si la MAD a été topée P (statut payé) sur Host sans que l'opération ne soit retrouvée sur T24 par l'agence en charge du règlement, l'utilisateur doit d'abord sortir du menu règlement et refaire cette opération une nouvelle fois.",
  "Numéro GSM des sms": "En cas de non réplication du numéro GSM bloquant la création d'une carte sur Power card, il faut modifier la fiche et ajouter +212. \nLors de l'entrée en relation via DIGITALIS avec +212.",
  "La levée de la surveillance migrée « 79 : Autre motif migration » sur le compte est à opérer à l’instar des surveillances manuelles suivantes levées en Front office": "20 : opposition sur compte\n21 : opposition à tous mouvements\n22 : oppositions des héritiers\n33 : saisie gel judiciaire\nLa levée des surveillances précitées doit être appuyée par un justificatif conformément au dispositif réglementaire interne.",
  "Chemin de levée d’une surveillance manuelle": "1. Aller sur le menu \"Gestion des surveillances\" puis \"Lever de la surveillance\"\n2. Renseigner le numéro de compte en question\n3. Cliquer sur le \"+\" comme pour ajouter un nouveau motif de surveillance puis cliquer sur le \"-\" qui apparait en rouge\n4. Cliquer sur Approuver en sollicitant la validation d'un deuxième profil",
  "Etapes de levée d’une surveillance mixte dont l’habilitation est du ressort du Front office (Cf. Hello Sprint du 28/07)": "Cette levée doit être appuyée par un justificatif conformément au dispositif réglementaire interne.",
  "Chemin de levée d’une surveillance mixte de l'Overview compte": "1. Accès à l'Overview à travers la Recherche du compte\n2. Levée à travers le lien « Levée surveillances mixtes » et validation via un deuxième profil à travers le lien «Autorisat. levée surveillances mixtes » (cf. Hello Sprint du 28/07)",
  "Exécution d'une opération de caisse au débit (message bloquant : Le solde de la caisse est insuffisant)": "S'assurer de l'autorisation des transferts entre la caisse principale et la caisse secondaire au démarrage de la journée avant la saisie de toutes opérations de caisse afin d'éviter les écarts entre les coupures et le solde de la caisse.",
  "Levée de blocage manuel": "Lorsqu’on souhaite lever un blocage manuellement des deux systèmes (MANSOUR/T24), il faudrait commencer par la levée dans T24 dans un premier temps, et ensuite le lever dans MANSOUR PAP.",
  "Affectation d’une caisse à un nouvel agent": "Avant l’affectation d’un agent vers une nouvelle agence, toujours s’assurer au préalable qu’il n’a pas une caisse qui lui est encore affectée, … pour éviter tout blocage dans sa nouvelle affectation.",
  "Problème d’impression": "Ne pas quitter l’écran principal de l’impression avant la fin du traitement : sablier ou barre de progression en cours, ou alors édition non trouvée merci de réessayer. Dans ce dernier cas, il faut cliquer sur ok et redemander l’impression.",
  "Historique des comptes 13230 non consultables sur PAP mais consultables sur T24": "Changer le générique 13230 (PCI) par le correspondant 12131 (PCEC). Faire la consultation sur docubase",
  "Au moment de la clôture de compte, le message suivant s’affiche « Partiel payoff is not allowed »": "Vérifier au niveau de l’onglet Bills dans la rubrique Addional Details au niveau de l’over view du compte, l’existence d’impayés en instance de règlement",
  "Clôture compte sur carnet": "Le retrait pour la clôture du compte sur carnet à effectuer sur PAP au lieu de T24",
  "Incidents KYC": "Lors de l’élaboration du compte rendu d’entretien NE PAS UTILISER SUR LE BOUTON BROUILLON",
  "Clients de passage": "La modification de la mini signalétique clients de passage se fait EXCLUSIVEMENT au niveau des écrans référentiel, la modification effectuée sur les écrans des opérations n’est pas prise en charge.",
  "Souscription aux packages avec message d’erreur : Expiry date": "Si le message d’erreur est affiché lors de la souscription aux packages remonter le problème pour résolution en central par les équipes ATF.\nUne fausse manipulation est constatée pour contourner ce problème en supprimant la valeur UPDATE du champ Action en bas de l’écran, cette action débloque l’écran de souscription mais engendre des problèmes de comptabilisation et de réplication du pack en question au niveau du host.\n\nDe ce fait dès apparition de ce message la seule action à entreprendre est de contacter l’équipe ATF pour déblocage.",
  "Facilités de caisse": "En cas d’inexistence de la facilité de caisse au niveau de la capacité de paiement d’un client, envoyer un mail au CTN pour prise en charge de la saisie sur T24 (renouvellement ou nouvelle mise en place)",
  "Messages d’erreur": "Les messages d’erreur les plus fréquents ont été revus et traduits, le restant sera traduit au fur et à mesure",
  "Consultation des packs": "Il est désormais possible de consulter les packs liés à un compte via NACOM (par l’agence). Vous pouvez utiliser cette transaction Liste pack par compte dans le menu Offres Packagées pour vérifier la liste des packs par compte au niveau du HOST.",
  "Retrait et versement avec date de valeur préférentielle": "Le retrait et versement avec date de valeur préférentielle est à effectuer sur PAP au lieu de T24. Ceci dans l’attente du déploiement de la gestion automatique des dates de valeurs préférentielle\nProcéder par la suite à un encaissement/décaissement SUR T24 de la caisse secondaire de l’agent ayant effectué l’opération.",
  "Délivrance de l’Attestation de RIB": "L’attestation de RIB n’est à délivrer au client qu’une fois le dossier juridique validé par le Back -Office CTN Gestion des comptes et la surveillance levée par ce dernier. En effet, au cas où le client ferait prévaloir cette attestation auprès d’instances externes à la banque et que des opérations liées à cette démarche devraient donner lieu au débit du compte (domiciliation des titres d’importation, …), elles n’aboutiraient pas et se traduiraient par des préjudices à la relation.",
  "Ajout de cotitulaire sur un compte": "Avant de valider l’ajout de cotitulaire(s) sur un compte, il y a lieu de s’assurer que le champ produit affiche le compte attribué au client, à vérifier sur l'overview client. Si ce champ affiche un compte STD, il y a lieu de choisir sur la liste déroulante le bon produit pour éviter tout blocage",
  "RAPPEL : Clients de passage": "Nous rappelons que la mini signalétique client de passage présente au niveau des écrans de distribution est une contrainte réglementaire, les données saisies sont disponibles au niveau de la CIN du client obligatoire pour effectuer les opérations (la seule information à demander est la profession).\nCes données sont saisies une seule fois lors du premier passage du tiers et sont stockées au niveau de la base T24, au prochain passage il suffira de renseigner le numéro de la CIN et les informations saisies auparavant remonteront sur les écrans automatiquement et ceci quelque soit l’agence ou le tiers se présenterait.",
  "Time Out de 5min": "Le système a été paramétré de façon à purger les sessions qui dépassent 5 min d’inactivité.\nL’activité sur T24 est véhiculée via le déroulement d’une liste de valeur par exemple et non pas un clic sur la page, il est recommandé de cliquer sur une des listes déroulantes de la page en cours pour réinitialiser le compteur."
    }
    for sujet, solution in bonnes_pratiques.items():
        with st.expander(f"📌 {sujet}"):
            st.markdown(f"<div style='padding-left:1rem;'>{solution}</div>", unsafe_allow_html=True)
# ------------------- ONGLET ADMIN -------------------
elif onglet == "🔐 Admin":
    MONGO_URI = "mongodb://localhost:27017"
    DB_NAME = "chatbot_db"
    # Configuration du style
    st.markdown("""
        <style>
            .metric-card {
                background-color: #2c3e50;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
                color: white;}
            .header {
                text-align: center;
                margin-bottom: 20px;}
        </style>
    """, unsafe_allow_html=True)

    # En-tête de la page
    st.markdown("""
        <div class="header">
            <h1 style='color: #e5e7e6;'>🔐 Espace Administrateur</h1>
            <p style='color: #e5e7e6; font-size: 20px;'>Interface de gestion réservée aux administrateurs 👇</p>
        </div>
    """, unsafe_allow_html=True)
    # Authentification
    if not st.session_state.get('admin_logged'):
        with st.expander("🔑 Authentification Administrateur", expanded=True):
            username = st.text_input("Identifiant")
            password = st.text_input("Mot de passe", type="password")

            if st.button("Se connecter"):
                if username == "kenzabp" and password == "qwerty1234":  
                    st.session_state.admin_logged = True
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
    # Interface admin (si connecté)
    if st.session_state.get('admin_logged'):
        try:
            # Initialisation MongoDB
            QUESTIONS_COLLECTION = "qa"
            USAGE_COLLECTION = "usage_stats"
            FEEDBACK_COLLECTION = "feedback"
            @st.cache_resource
            def init_mongo():
                try:
                    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
                    client.admin.command('ping')
                    db = client[DB_NAME]
                    # Vérification des collections
                    for col in [USAGE_COLLECTION, QUESTIONS_COLLECTION, FEEDBACK_COLLECTION]:
                        if col not in db.list_collection_names():
                            db.create_collection(col)
                    return db
                except Exception as e:
                    st.error(f"Erreur MongoDB: {str(e)}")
                    return None
            db = init_mongo()           
            if db is None:
                st.error("Impossible de se connecter à la base de données")
                st.stop()
            # En-tête du dashboard
            st.markdown("""
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;'>
                    <h2 style='color: #FFFFFF;'>📊 Tableau de Bord Administrateur</h2>
                    <button onclick="window.location.reload()" style='padding: 8px 15px; background-color: #B67332; color: white; border: none; border-radius: 5px; cursor: pointer;'>
                        🔄 Rafraîchir
                    </button>
                </div>
            """, unsafe_allow_html=True)
            # ------------------- SECTION STATISTIQUES -------------------
            st.markdown("## 📈 Statistiques Globales")           
            # Fonction helper pour les métriques
            def display_metric(col, title, value, unit="", icon="📊"):
                with col:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 14px; margin-bottom: 5px;">{icon} {title}</div>
                            <div style="font-size: 24px; font-weight: bold;">{value} {unit}</div>
                        </div>
                    """, unsafe_allow_html=True)
            # Ligne 1 - Statistiques d'utilisation
            col1, col2, col3 = st.columns(3)
            try:
                # Utilisateurs uniques
                unique_users = len(db[USAGE_COLLECTION].distinct("user_id"))
                display_metric(col1, "Utilisateurs uniques", unique_users, icon="👥")
                # Sessions totales
                total_sessions = db[USAGE_COLLECTION].count_documents({})
                display_metric(col2, "Sessions totales", total_sessions, icon="💬")
                # Durée moyenne
                avg_duration = list(db[USAGE_COLLECTION].aggregate([
                    {"$group": {"_id": None, "avg": {"$avg": "$duration"}}}
                ]))[0]['avg'] if db[USAGE_COLLECTION].count_documents({}) > 0 else 0
                display_metric(col3, "Durée moyenne", f"{round(avg_duration, 1)}", "min", icon="⏱️")
            except Exception as e:
                st.error(f"Erreur lors du chargement des statistiques: {str(e)}")
            # Ligne 2 - Performance du chatbot
            col4, col5, col6 = st.columns(3)
            try:
                # Taux de résolution
                resolved = db[QUESTIONS_COLLECTION].count_documents({"resolved": True})
                total = db[QUESTIONS_COLLECTION].count_documents({})
                rate = round((resolved/total)*100, 1) if total > 0 else 0
                display_metric(col4, "Taux de résolution", rate, "%", icon="✅")
                # Questions sans réponse
                unanswered = db[QUESTIONS_COLLECTION].count_documents({"answer": ""})
                display_metric(col5, "Questions sans réponse", unanswered, icon="❌")
                # Temps de réponse
                avg_time_result = list(db[QUESTIONS_COLLECTION].aggregate([
                    {"$group": {"_id": None, "avg": {"$avg": "$response_time"}}}
                      ]))
                avg_time = avg_time_result[0]["avg"] if avg_time_result and avg_time_result[0]["avg"] is not None else 0
                display_metric(col6, "Temps de réponse", f"{round(avg_time, 2)}", "sec", icon="⚡")
            except Exception as e:
                st.error(f"Erreur lors du chargement des performances: {str(e)}")
            # ------------------- VISUALISATION GRAPHIQUE -------------------
            st.markdown("## 📊 Visualisations")
            try:
                # Top 10 des questions seulement
                top_questions = list(db[QUESTIONS_COLLECTION].aggregate([
                    {"$group": {"_id": "$question", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 10}]))
                if top_questions:
                    fig = px.bar(
                        x=[q["count"] for q in top_questions],
                        y=[q["_id"] for q in top_questions],
                        orientation='h',
                        labels={"x": "Nombre de demandes", "y": "Question"},
                        title="Top 10 des questions posées")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Aucune question enregistrée")
            except Exception as e:
                st.error(f"Erreur lors du chargement des questions: {str(e)}")
            # ------------------- DONNÉES DÉTAILLÉES -------------------
            st.markdown("## 🔍 Détails des données")
            with st.expander("📝 Dernières interactions"):
                try:
                    last_interactions = list(db[USAGE_COLLECTION].find(
                        {}, 
                        {"_id": 0, "date": 1, "user_id": 1, "duration": 1}
                    ).sort("date", -1).limit(10))
                    st.dataframe(last_interactions)
                except Exception as e:
                    st.error(f"Erreur lors du chargement des interactions: {str(e)}")
            with st.expander("❓ Dernières questions"):
                try:
                    last_questions = list(db[QUESTIONS_COLLECTION].find(
                        {},
                        {"_id": 0, "question": 1, "resolved": 1, "timestamp": 1}
                    ).sort("timestamp", -1).limit(10))
                    st.dataframe(last_questions)
                except Exception as e:
                    st.error(f"Erreur lors du chargement des questions: {str(e)}")
            # Déconnexion
            if st.button("🚪 Déconnexion", type="primary"):
                st.session_state.admin_logged = False
                st.rerun()
        except Exception as e:
            st.error(f"Une erreur critique est survenue: {str(e)}")
            st.error("Veuillez vérifier votre connexion et réessayer")