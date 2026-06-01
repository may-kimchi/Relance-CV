import os
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client

# Connexion sécurisée à Supabase grâce aux secrets cachés
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# Configuration du mail automatique en français
SUJET_TEMPLATE = "Suivi de ma candidature - {entreprise}"
MESSAGE_TEMPLATE = """Bonjour l'équipe de {entreprise},

Je me permets de vous recontacter concernant la candidature que je vous ai adressée le {date}. Le délai de {jours} jours étant passé, je souhaitais simplement m'assurer que mon dossier vous était bien parvenu et savoir si vous aviez des retours à me faire.

Je reste extrêmement motivé par l'idée de vous rejoindre et je me tiens à votre entière disposition pour tout échange ou entretien.

En vous souhaitant une excellente journée.

Cordialement,
[Ton Prénom] [Ton Nom]
[Ton Téléphone]"""

def envoyer_email_relance(destinataire, entreprise, date_envoi, delai):
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    
    msg = MIMEMultipart()
    # Le mail partira avec ton adresse d'envoi configurée sur Brevo
    msg['From'] = "ton.email@gmail.com" # 👈 REMPLACE PAR TON PROPRE EMAIL SI TU VEUX
    msg['To'] = destinataire
    
    # Formatage de la date en version française (JJ/MM/AAAA)
    date_obj = datetime.datetime.strptime(date_envoi, "%Y-%m-%d")
    date_formatee = date_obj.strftime("%d/%m/%Y")
    
    msg['Subject'] = SUJET_TEMPLATE.format(entreprise=entreprise)
    corps = MESSAGE_TEMPLATE.format(entreprise=entreprise, date=date_formatee, jours=delai)
    msg.attach(MIMEText(corps, 'plain', 'utf-8'))
    
    try:
        # Connexion au serveur sécurisé de Brevo
        server = smtplib.SMTP("smtp-relay.brevo.com", 587)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(msg['From'], destinataire, msg.as_string())
        server.quit()
        print(f"✅ Mail envoyé avec succès à {entreprise} ({destinataire})")
        return True
    except Exception as e:
        print(f"❌ Échec de l'envoi pour {entreprise}: {str(e)}")
        return False

def main():
    # Le robot interroge ta base de données Supabase
    print("🤖 Le robot analyse la base Supabase...")
    response = supabase.table("candidatures").select("*").execute()
    candidatures = response.data
    
    aujourdhui = datetime.date.today()
    
    for app in candidatures:
        date_cv = datetime.datetime.strptime(app['date_envoi'], "%Y-%m-%d").date()
        # Calcul de la date exacte de relance : Date d'envoi + Délai (5 ou 7 jours)
        date_cible = date_cv + datetime.timedelta(days=int(app['delai']))
        
        print(f"🔍 Vérification {app['nom_entreprise']} : Requis le {date_cible} | Aujourd'hui : {aujourdhui}")
        
        # Le robot compare si la date cible est passée ou correspond à aujourd'hui
        if aujourdhui >= date_cible:
            print(f"⏰ Alerte ! Le délai est atteint pour {app['nom_entreprise']}. Envoi du mail...")
            succes = envoyer_email_relance(app['email_contact'], app['nom_entreprise'], app['date_envoi'], app['delai'])
            
            # Si le mail est parti, on supprime la ligne de Supabase pour ne pas la relancer demain !
            if succes:
                supabase.table("candidatures").delete().eq("id", app['id']).execute()
                print(f"🗑️ {app['nom_entreprise']} nettoyé de la base de données.")

if __name__ == "__main__":
    main()
