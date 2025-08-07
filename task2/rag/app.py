import os
import openai
import base64
from dotenv import load_dotenv

# 🔐 Charger les variables d'environnement (.env)
load_dotenv()

# 🔑 Initialiser le client OpenAI avec la clé de l'environnement
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 📷 Nom de l'image à analyser
image_path = "image1.PNG"

# 🧪 Vérification du fichier
if not os.path.exists(image_path):
    print(f"❌ Fichier introuvable : {image_path}")
    exit()

# 📥 Lire l'image et encoder en base64
with open(image_path, "rb") as image_file:
    base64_image = base64.b64encode(image_file.read()).decode("utf-8")

# 🧠 Envoyer la requête à GPT-4o pour extraire le texte
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                },
                {
                    "type": "text",
                    "text": "Peux-tu extraire le texte de cette image ?"
                }
            ]
        }
    ],
    max_tokens=1000
)

# 🖨️ Afficher la réponse
print("🧾 Texte extrait :\n")
print(response.choices[0].message.content.strip())
