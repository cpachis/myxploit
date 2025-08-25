import json
import random
from datetime import datetime, timedelta

# Energies disponibles
ENERGIES = [
    "gazole", "gnv", "electrique", "BGNV", "BIOGNC", "BIODIESEL", "BIOTRUC", "BIOTRUC2", "dzd"
]
ENERGIE_LABELS = {
    "gazole": "Gazole",
    "gnv": "GNV",
    "electrique": "Électrique",
    "BGNV": "BioGNV",
    "BIOGNC": "BioGNC",
    "BIODIESEL": "Biodiesel",
    "BIOTRUC": "Biotruc",
    "BIOTRUC2": "Biotruc2",
    "dzd": "DZD"
}

# 1. Générer 20 sous-traitants
soustraitants = {}
for i in range(1, 21):
    sid = f"ST{i:03d}"
    soustraitants[sid] = {
        "nom": f"Sous-traitant {i}",
        "contact": f"contact{i}@soustraitant.fr"
    }

# 2. Générer 5 clients
clients = {}
for i in range(1, 6):
    cid = f"CL{i:03d}"
    # Associer chaque client à un sous-traitant (en boucle)
    sid = f"ST{((i-1)%20)+1:03d}"
    nom = f"Client {i}"
    nom_email = nom.lower().replace(' ', '').replace('é','e').replace('è','e').replace('ê','e').replace('à','a').replace('ç','c')
    clients[cid] = {
        "nom": nom,
        "adresse": f"{i} rue de la Logistique, 750{i%20+1} Paris",
        "email": f"{nom_email}.{sid.lower()}@myx.com"
    }



# 4. Générer 25 transports par client (500 transports)
transports = {}
start_date = datetime(2025, 6, 1)
end_date = datetime(2025, 7, 10)
delta_days = (end_date - start_date).days

for i, cid in enumerate(clients.keys()):
    # Associer chaque client à un sous-traitant (en boucle)
    sid = list(soustraitants.keys())[i % len(soustraitants)]
    for j in range(25):
        t_id = f"T{(i*25)+j+1:04d}"
        date = start_date + timedelta(days=random.randint(0, delta_days))
        poids = round(random.uniform(0.5, 20.0), 2)
        phases = []
        phase_types = ["collecte", "traction", "distribution"]
        phase_dates = [date + timedelta(days=offset) for offset in [0, 0, 0]]
        for k, ptype in enumerate(phase_types):
            conso = round(random.uniform(8.0, 35.0), 1)
            dist = round(random.uniform(10, 500), 1)
            # Emissions fictives
            emis_kg = round(conso * dist / 100 * random.uniform(0.5, 3.5), 2)
            emis_tkm = round(emis_kg / (poids * dist) if poids * dist > 0 else 0, 3)
            phases.append({
                "type": ptype,
                "conso": conso,
                "distance": dist,
                "date": phase_dates[k].strftime("%Y-%m-%d"),
                "emis_kg": emis_kg,
                "emis_tkm": emis_tkm
            })
        total_kg = sum(p["emis_kg"] for p in phases)
        total_tkm = sum(p["emis_tkm"] for p in phases)
        transports[t_id] = {
            "client": cid,
            "proprietaire": sid,
            "poids": poids,
            "date": date.strftime("%Y-%m-%d"),
            "emis_kg": total_kg,
            "emis_tkm": total_tkm,
            "phases": phases
        }

# Écriture des fichiers
with open("soustraitants.json", "w", encoding="utf-8") as f:
    json.dump(soustraitants, f, ensure_ascii=False, indent=2)
with open("clients.json", "w", encoding="utf-8") as f:
    json.dump(clients, f, ensure_ascii=False, indent=2)

with open("transports.json", "w", encoding="utf-8") as f:
    json.dump(transports, f, ensure_ascii=False, indent=2)

print("Jeu de données massives généré avec succès !") 