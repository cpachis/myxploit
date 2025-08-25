import os
import json
import base64
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required, logout_user, current_user
)
from datetime import datetime, timedelta

print('=== DEMARRAGE APP.PY ===')
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-moi")
DATA_DIR = os.path.join(app.root_path, "data")

# --- Flask-Login Setup ---
login_manager = LoginManager(app)
login_manager.login_view = "login"  # type: ignore

class User(UserMixin):
    def __init__(self, username):
        self.id = username

    @property
    def is_active(self):
        return True

@login_manager.user_loader
def load_user(username):
    users = load_json("users.json")
    return User(username) if username in users else None

# --- JSON Helpers ---
def load_json(fname):
    path = os.path.join(DATA_DIR, fname)
    print(f"DEBUG load_json: tentative de chargement de {path}")
    if os.path.exists(path):
        print(f"DEBUG load_json: fichier trouvé, chargement...")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            print(f"DEBUG load_json: {len(data)} éléments chargés depuis {fname}")
            return data
    else:
        print(f"DEBUG load_json: fichier non trouvé: {path}")
        return {}

def save_json(fname, data):
    path = os.path.join(DATA_DIR, fname)
    print(f"DEBUG save_json: sauvegarde de {len(data)} éléments dans {path}")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"DEBUG save_json: fichier {fname} sauvegardé avec succès")
    except Exception as e:
        print(f"DEBUG save_json: erreur lors de la sauvegarde de {fname}: {e}")

# --- Data Normalization ---
def normalize_data():
    clients       = load_json("clients.json")
    energies      = load_json("energies.json")  # Recharge à chaque appel
    
    # Essayer de charger les transports simplifiés d'abord
    try:
        transports = load_json("transports_simple.json")
        # Pas de normalisation nécessaire pour les transports simplifiés
    except:
        # Fallback vers l'ancien format si le fichier simplifié n'existe pas
        transports = load_json("transports.json")
        # Normalisation pour l'ancien format
        norm_trans = {}
        for ref, t in transports.items():
            norm_trans[ref] = {
                **t,
                "client":       t.get("client", "").upper(),
                "proprietaire": t.get("proprietaire", "").upper()
            }
        transports = norm_trans
    
    vehicules     = load_json("vehicules.json")

    # Unify keys to uppercase
    clients       = {cid.upper(): v for cid, v in clients.items()}

    return clients, energies, transports, vehicules

# Cache pour les énergies (optionnel, pour améliorer les performances)
_energies_cache = None
_energies_cache_time = 0
CACHE_DURATION = 5  # 5 secondes

def normalize_data_simple():
    """Version simplifiée de normalize_data pour les nouveaux transports"""
    clients = load_json("clients.json")
    energies = load_json("energies.json")
    
    # Charger les transports simplifiés
    try:
        transports = load_json("transports_simple.json")
        print(f"DEBUG normalize_data_simple: {len(transports)} transports chargés")
        print(f"DEBUG normalize_data_simple: clés des transports: {list(transports.keys())}")
    except Exception as e:
        print(f"DEBUG normalize_data_simple: erreur lors du chargement: {e}")
        transports = {}
    
    # Normaliser les clients en majuscules
    clients = {cid.upper(): v for cid, v in clients.items()}
    
    # Normaliser les transports
    norm_trans = {}
    for ref, t in transports.items():
        norm_trans[ref] = {
            **t,
            "client": t.get("client", "").upper(),
            # Calculer les émissions si elles ne sont pas présentes
            "emis_kg": t.get("emis_kg") or 0,
            "emis_tkm": t.get("emis_tkm") or 0
        }
    
    return clients, energies, norm_trans

def get_energies_fresh():
    """Récupère les énergies avec un cache de 5 secondes"""
    global _energies_cache, _energies_cache_time
    current_time = datetime.now().timestamp()
    
    if (_energies_cache is None or 
        current_time - _energies_cache_time > CACHE_DURATION):
        _energies_cache = load_json("energies.json")
        _energies_cache_time = current_time
    
    return _energies_cache

def clear_energies_cache():
    """Force le rechargement du cache des énergies"""
    global _energies_cache, _energies_cache_time
    _energies_cache = None
    _energies_cache_time = 0

# --- Auth Routes ---
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        users = load_json("users.json")
        u, p = request.form["username"], request.form["password"]
        if u in users and users[u]["password"] == p:
            login_user(User(u), remember="remember" in request.form)
            return redirect(url_for("index"))
        flash("Identifiants invalides", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# --- Main Routes ---
@app.route("/accueil")
@login_required
def accueil():
    """Page d'accueil avec vue d'ensemble et actions rapides"""
    clients, energies, transports = normalize_data_simple()
    
    # Statistiques rapides
    total_clients = len(clients)
    total_energies = len(energies)
    total_transports = len(transports)
    
    # Calcul des émissions totales
    sum_kg = 0.0
    sum_tkm = 0.0
    for t in transports.values():
        sum_kg += float(t.get("emis_kg", 0) or 0)
        sum_tkm += float(t.get("emis_tkm", 0) or 0)
    
    return render_template("accueil.html",
                           clients=clients,
                           energies=energies,
                           transports=transports,
                           total_clients=total_clients,
                           total_energies=total_energies,
                           total_transports=total_transports,
                           sum_kg=sum_kg,
                           sum_tkm=sum_tkm)

@app.route("/")
@login_required
def index():
    clients, energies, transports = normalize_data_simple()

    # Calcul des totaux côté Python
    sum_kg = 0.0
    sum_tkm = 0.0
    for t in transports.values():
        sum_kg += float(t.get("emis_kg", 0) or 0)
        sum_tkm += float(t.get("emis_tkm", 0) or 0)

    return render_template("home.html",
                           clients=clients,
                           transports=transports,
                           sum_kg=sum_kg,
                           sum_tkm=sum_tkm)

@app.route("/dashboard")
@login_required
def dashboard():
    view = request.args.get("view", "global")
    clients, energies, transports = normalize_data_simple()

    # Calcul des totaux côté Python
    sum_kg = 0.0
    sum_tkm = 0.0
    
    # Métriques opérationnelles
    transports_en_cours = []
    transports_termines = []
    transports_ce_mois = []
    transports_cette_semaine = []
    emissions_ce_mois = 0.0
    emissions_cette_semaine = 0.0
    
    # Date actuelle pour les calculs
    from datetime import datetime, timedelta
    now = datetime.now()
    debut_mois = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    debut_semaine = now - timedelta(days=now.weekday())
    debut_semaine = debut_semaine.replace(hour=0, minute=0, second=0, microsecond=0)
    

    
    # Statistiques par client
    stats_clients = {}
    for cid in clients:
        stats_clients[cid] = {
            'transports': 0,
            'emissions_kg': 0.0,
            'poids_total': 0.0,
            'derniere_activite': None
        }
    
    for ref, t in transports.items():
        # Calcul des émissions totales
        t_emis_kg = 0.0
        t_emis_tkm = 0.0
        if t.get("phases"):
            for p in t["phases"]:
                t_emis_kg += float(p.get("emis_kg", 0) or 0)
                t_emis_tkm += float(p.get("emis_tkm", 0) or 0)
        else:
            t_emis_kg = float(t.get("emis_kg", 0) or 0)
            t_emis_tkm = float(t.get("emis_tkm", 0) or 0)
        
        sum_kg += t_emis_kg
        sum_tkm += t_emis_tkm
        
        # Déterminer le statut opérationnel basé sur les phases
        has_distribution = False
        if t.get("phases"):
            for p in t["phases"]:
                if p.get("type") == "distribution":
                    has_distribution = True
                    break
        
        # Ajouter aux listes appropriées
        transport_info = {
            'ref': ref,
            'client': t.get("client", ""),
            'date': t.get("date", ""),
            'emis_kg': t_emis_kg,
            'emis_tkm': t_emis_tkm,
            'poids': t.get("poids", 0)
        }
        
        if has_distribution:
            transports_termines.append(transport_info)
        else:
            transports_en_cours.append(transport_info)
        
        # Analyse de la date pour les statistiques temporelles
        t_date = t.get("date", "")
        if t_date:
            try:
                t_datetime = datetime.strptime(t_date, "%Y-%m-%d")
                
                # Transports ce mois
                if t_datetime >= debut_mois:
                    transports_ce_mois.append(transport_info)
                    emissions_ce_mois += t_emis_kg
                
                # Transports cette semaine
                if t_datetime >= debut_semaine:
                    transports_cette_semaine.append(transport_info)
                    emissions_cette_semaine += t_emis_kg
                    
            except ValueError:
                pass
        
        # Statistiques par client
        client_id = t.get("client", "")
        if client_id in stats_clients:
            stats_clients[client_id]['transports'] += 1
            stats_clients[client_id]['emissions_kg'] += t_emis_kg
            stats_clients[client_id]['poids_total'] += float(t.get("poids", 0) or 0)
            if t_date:
                try:
                    t_datetime = datetime.strptime(t_date, "%Y-%m-%d")
                    if (stats_clients[client_id]['derniere_activite'] is None or 
                        t_datetime > stats_clients[client_id]['derniere_activite']):
                        stats_clients[client_id]['derniere_activite'] = t_datetime
                except ValueError:
                    pass

    return render_template("dashboard.html",
                           view=view,
                           clients=clients,
                           transports=transports,
                           sum_kg=sum_kg,
                           sum_tkm=sum_tkm,
                           # Nouvelles métriques opérationnelles
                           transports_en_cours=transports_en_cours,
                           transports_termines=transports_termines,
                           transports_ce_mois=transports_ce_mois,
                           transports_cette_semaine=transports_cette_semaine,
                           emissions_ce_mois=emissions_ce_mois,
                           emissions_cette_semaine=emissions_cette_semaine,

                           stats_clients=stats_clients,
                           now=now)


@app.route("/transport", methods=["GET","POST"])
@login_required
def transport():
    clients, energies, transports, vehicules = normalize_data()
    
    # Paramètres de filtrage pour les transports importés
    client_filter = request.args.get('client', '')
    date_debut = request.args.get('date_debut', '')
    date_fin = request.args.get('date_fin', '')
    statut_filter = request.args.get('statut', '')
    tri = request.args.get('tri', 'date')  # date, reference, client, poids
    ordre = request.args.get('ordre', 'desc')  # asc, desc
    
    if request.method == "POST":
        ref = request.form["ref"]
        client_id = request.form["client"].upper()
        type_transport = request.form.get("type_transport", "direct")
        date = request.form.get("date", "")
        ville_depart = request.form.get("ville_depart", "")
        ville_arrivee = request.form.get("ville_arrivee", "")
        distance_km = float(request.form.get("distance_km", "0") or 0)
        poids_tonnes = float(request.form.get("poids_tonnes", "0") or 0)
        energie = request.form.get("energie", "")
        
        # Calcul des émissions basé sur l'énergie et la distance
        emis_kg = 0
        emis_tkm = 0
        
        if energie and distance_km > 0 and poids_tonnes > 0:
            # Récupérer le facteur d'émission de l'énergie
            energie_data = energies.get(energie)
            if energie_data and energie_data.get("facteur"):
                facteur = float(energie_data["facteur"])
                emis_kg = distance_km * poids_tonnes * facteur
                emis_tkm = facteur
        
        transports[ref] = {
            "ref": ref,
            "client": client_id,
            "type_transport": type_transport,
            "date": date,
            "ville_depart": ville_depart,
            "ville_arrivee": ville_arrivee,
            "distance_km": distance_km,
            "poids_tonnes": poids_tonnes,
            "energie": energie,
            "emis_kg": emis_kg,
            "emis_tkm": emis_tkm,
            "phases": []
        }
        save_json("transports.json", transports)
        flash(f"Transport {ref} créé avec succès !", "success")
        return redirect(url_for("liste_transports"))

    # Filtrer les transports pour l'affichage
    transports_filtres = {}
    for ref, t in transports.items():
        # Filtre par client
        if client_filter and client_filter not in t.get('client', ''):
            continue
            
        # Filtre par date
        if date_debut and t.get('date', '') < date_debut:
            continue
        if date_fin and t.get('date', '') > date_fin:
            continue
            
        # Filtre par statut
        if statut_filter and t.get('statut', '') != statut_filter:
            continue
            
        transports_filtres[ref] = t
    
    # Trier les transports
    def tri_key(item):
        ref, t = item
        if tri == 'date':
            return t.get('date', '')
        elif tri == 'reference':
            return ref
        elif tri == 'client':
            return t.get('client', '')
        elif tri == 'poids':
            return float(t.get('poids', 0))
        return t.get('date', '')
    
    transports_tries = sorted(transports_filtres.items(), key=tri_key, reverse=(ordre == 'desc'))
    
    # Statistiques
    total_transports = len(transports_tries)
    total_poids = sum(float(t.get('poids', 0)) for _, t in transports_tries)
    total_emissions = sum(float(t.get('emis_kg', 0)) for _, t in transports_tries)
    
    # Clients uniques pour le filtre
    clients_uniques = list(set(t.get('client', '') for _, t in transports_tries))
    clients_uniques.sort()
    
    # Statuts uniques pour le filtre
    statuts_uniques = list(set(t.get('statut', '') for _, t in transports_tries if t.get('statut')))
    statuts_uniques.sort()

    return render_template("transport.html",
                           clients=clients,
                           energies=energies,
                           transports=dict(transports_tries),
                           date_selected="",
                           # Paramètres de filtrage
                           client_filter=client_filter,
                           date_debut=date_debut,
                           date_fin=date_fin,
                           statut_filter=statut_filter,
                           tri=tri,
                           ordre=ordre,
                           clients_uniques=clients_uniques,
                           statuts_uniques=statuts_uniques,
                           # Statistiques
                           total_transports=total_transports,
                           total_poids=total_poids,
                           total_emissions=total_emissions)

@app.route("/transports")
@login_required
def liste_transports():
    clients, energies, transports = normalize_data_simple()
    
    # Paramètres de filtrage
    date_filter = request.args.get('date', '')
    client_filter = request.args.get('client', '')
    energie_filter = request.args.get('energie', '')
    type_transport_filter = request.args.get('type_transport', '')
    tri = request.args.get('tri', 'date')  # date, reference, client, poids
    ordre = request.args.get('ordre', 'desc')  # asc, desc
    
    # Filtrer les transports
    transports_list = []
    for ref, t in transports.items():
        # Filtre par date
        if date_filter and t.get('date', '') != date_filter:
            continue
            
        # Filtre par client
        if client_filter and client_filter not in t.get('client', ''):
            continue
        
        # Filtre par énergie
        if energie_filter and t.get('energie', '') != energie_filter:
            continue
            
        # Filtre par type de transport
        if type_transport_filter and t.get('type_transport', '') != type_transport_filter:
            continue
            
        transports_list.append({**t})
    
    # Trier les transports
    def tri_key(t):
        if tri == 'date':
            return t.get('date', '')
        elif tri == 'reference':
            return t.get('ref', '')
        elif tri == 'client':
            return t.get('client', '')
        elif tri == 'poids':
            return float(t.get('poids', 0))
        elif tri == 'distance':
            # Calculer la distance totale des phases
            total_distance = 0.0
            if t.get('phases'):
                for phase in t['phases']:
                    total_distance += float(phase.get('distance', 0) or 0)
            return total_distance
        return t.get('date', '')
    
    transports_list.sort(key=tri_key, reverse=(ordre == 'desc'))
    
    # Clients uniques pour le filtre
    clients_uniques = list(set(t.get('client', '') for t in transports_list))
    clients_uniques.sort()
    


    
    return render_template(
        "liste_transports.html",
        transports=transports_list,
        clients=clients,
        energies=energies,
        date_selected=date_filter,
        client_filter=client_filter,
        energie_filter=energie_filter,
        type_transport_filter=type_transport_filter,
        tri=tri,
        ordre=ordre,
        clients_uniques=clients_uniques,
    )

@app.route("/transports/date/<date>")
@login_required
def transports_par_date(date):
    clients, energies, transports, vehicules = normalize_data()
    transports_list = [
        {"ref": ref, **t}
        for ref, t in transports.items()
        if t.get("date") == date
    ]
    
    # Paramètres de tri
    tri = request.args.get('tri', 'date')
    ordre = request.args.get('ordre', 'desc')
    
    # Trier les transports
    def tri_key(t):
        if tri == 'date':
            return t.get('date', '')
        elif tri == 'reference':
            return t.get('ref', '')
        elif tri == 'client':
            return t.get('client', '')
        elif tri == 'poids':
            return float(t.get('poids', 0))
        elif tri == 'distance':
            # Calculer la distance totale des phases
            total_distance = 0.0
            if t.get('phases'):
                for phase in t['phases']:
                    total_distance += float(phase.get('distance', 0) or 0)
            return total_distance
        return t.get('date', '')
    
    transports_list.sort(key=tri_key, reverse=(ordre == 'desc'))
    
    return render_template(
        "liste_transports.html",
        transports=transports_list,
        clients=clients,
        titre=f"Transports du {date}",
        date_selected=date,
        client_filter="",
        tri=tri,
        ordre=ordre,
        clients_uniques=[]
    )

@app.route("/transports/client/<client_id>")
@login_required
def transports_par_client(client_id):
    clients, energies, transports, vehicules = normalize_data()
    transports_list = [
        {"ref": ref, **t}
        for ref, t in transports.items()
        if t.get("client") == client_id.upper()
    ]
    
    # Paramètres de tri
    tri = request.args.get('tri', 'date')
    ordre = request.args.get('ordre', 'desc')
    
    # Trier les transports
    def tri_key(t):
        if tri == 'date':
            return t.get('date', '')
        elif tri == 'reference':
            return t.get('ref', '')
        elif tri == 'client':
            return t.get('client', '')
        elif tri == 'poids':
            return float(t.get('poids', 0))
        elif tri == 'distance':
            # Calculer la distance totale des phases
            total_distance = 0.0
            if t.get('phases'):
                for phase in t['phases']:
                    total_distance += float(phase.get('distance', 0) or 0)
            return total_distance
        return t.get('date', '')
    
    transports_list.sort(key=tri_key, reverse=(ordre == 'desc'))
    
    return render_template(
        "liste_transports.html",
        transports=transports_list,
        clients=clients,
        titre=f"Transports du client {client_id}",
        date_selected="",
        client_filter=client_id.upper(),
        tri=tri,
        ordre=ordre,
        clients_uniques=[]
    )

@app.route("/transports/<ref>", methods=["GET", "POST"])
@login_required
def transport_detail(ref):
    clients, energies, transports, vehicules = normalize_data()
    t = transports.get(ref)
    if not t:
        flash(f"Transport {ref} introuvable", "warning")
        return redirect(url_for("liste_transports"))
    
    # Déterminer le facteur d'émission du véhicule
    vehicule_facteur = 0
    if t.get("phases"):
        # Chercher dans les phases pour trouver un véhicule_id
        for phase in t["phases"].values() if isinstance(t["phases"], dict) else t["phases"]:
            if isinstance(phase, dict) and phase.get("vehicule_id"):
                vehicule_id = phase["vehicule_id"]
                if vehicule_id in vehicules:
                    vehicule_facteur = vehicules[vehicule_id].get("emissions", 0)
                    break
    
    # Si pas de véhicule trouvé dans les phases, essayer de déterminer par l'énergie
    if vehicule_facteur == 0:
        energie_transport = t.get("energie", "").lower()
        for vehicule_id, vehicule_data in vehicules.items():
            if vehicule_data.get("energie", "").lower() == energie_transport:
                vehicule_facteur = vehicule_data.get("emissions", 0)
                break
    
    if request.method == "POST":
        phases_json = request.form.get("phases", "[]")
        try:
            import json
            phases = json.loads(phases_json)
        except Exception:
            phases = []
        t["phases"] = phases
        save_json("transports.json", transports)
        flash("Phases modifiées avec succès !", "success")
        return redirect(url_for("transport_detail", ref=ref))
    
    # Ajouter le facteur du véhicule au transport pour le template
    t["vehicule_facteur"] = vehicule_facteur
    
    return render_template(
        "transport_detail.html",
        ref=ref,
        transport=t,
        client=clients.get(t.get("client")),
        soustraitant=clients.get(t.get("proprietaire")),
        energies=energies
    )

@app.route("/api/transport/<ref>")
@login_required
def api_transport_detail(ref):
    print("API TRANSPORT DETAIL appelée pour ref :", ref)
    try:
        clients, energies, transports, vehicules = normalize_data()
        t = transports.get(ref)
        if not t:
            return jsonify({"error": "Transport introuvable"}), 404
    
        # Générer le HTML pour la sidebar
        html = f"""
        <div class="transport-detail">
          <div class="detail-info">
            <div class="info-row">
              <span class="label">Date :</span>
              <span class="value">{format_date_fr(t.get('date', ''))}</span>
            </div>
            <div class="info-row">
              <span class="label">Client :</span>
              <span class="value">{clients.get(t.get('client', ''), {}).get('nom', t.get('client', ''))}</span>
            </div>
            <div class="info-row">
              <span class="label">Poids transporté (t) :</span>
              <span class="value">{t.get('poids', '-')}</span>
            </div>
            <div class="info-row">
              <span class="label">CO₂e (kg) :</span>
              <span class="value">{t.get('emis_kg', 0):.2f}</span>
            </div>
            <div class="info-row">
              <span class="label">CO₂e/t.km :</span>
              <span class="value">{t.get('emis_tkm', 0):.3f}</span>
            </div>
          </div>
        </div>
        
        <!-- Section des phases -->
        <div class="phases-section">
          <div class="phases-header">
            <h3>Détail des phases</h3>
            <button class="btn-add-phase" id="btn-add-phase">+ Ajouter une phase</button>
          </div>
          <form id="edit-phases-form" data-transport-ref="{ref}">
                          <input type="hidden" name="phases" id="phases_edit_input" value="">
              <table class="phases-table" id="phases-table-edit">
                <thead>
                  <tr>
                    <th>Phase</th>
                    <th>Énergie</th>
                    <th>Ville départ</th>
                    <th>Ville arrivée</th>
                    <th>Conso / 100 km</th>
                    <th>Distance (km)</th>
                    <th>Date</th>
                    <th>Émissions (kg)</th>
                    <th>Émissions (kg/t.km)</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
        """
        
        if t.get('phases') and len(t['phases']) > 0:
            for i, p in enumerate(t['phases']):
                selected_collecte = 'selected' if p.get('type') == 'collecte' else ''
                selected_traction = 'selected' if p.get('type') == 'traction' else ''
                selected_distribution = 'selected' if p.get('type') == 'distribution' else ''
                
                # Nettoyer et valider les valeurs numériques
                conso_value = p.get('conso', '')
                if isinstance(conso_value, str) and conso_value.strip() in ['+', '-', '', 'N/A', 'n/a']:
                    conso_value = ''
                elif isinstance(conso_value, (int, float)) and (conso_value <= 0 or conso_value > 1000):
                    conso_value = ''
                
                distance_value = p.get('distance', '')
                if isinstance(distance_value, str) and distance_value.strip() in ['+', '-', '', 'N/A', 'n/a']:
                    distance_value = ''
                elif isinstance(distance_value, (int, float)) and (distance_value <= 0 or distance_value > 10000):
                    distance_value = ''
                
                # Nettoyer la date
                date_value = p.get('date', '')
                if isinstance(date_value, str) and date_value.strip() in ['+', '-', '', 'N/A', 'n/a']:
                    date_value = ''
                
                # Valeur d'énergie par défaut
                energie_value = p.get('energie', 'gazole')
                
                # Générer dynamiquement les options d'énergie à partir des vraies données
                energie_options = ""
                for energie_id, energie_data in energies.items():
                    selected = 'selected' if energie_id == energie_value else ''
                    nom = energie_data.get('nom', energie_id)
                    facteur = energie_data.get('facteur', '0')
                    unite = energie_data.get('unite', energie_data.get('unit', ''))
                    
                    # Formater l'affichage selon l'unité
                    if unite.lower() in ['l', 'litre', 'litres']:
                        display_text = f"{nom} ({facteur} kg/L)"
                    elif unite.lower() in ['kg', 'kilos']:
                        display_text = f"{nom} ({facteur} kg/kg)"
                    elif unite.lower() in ['kwh']:
                        display_text = f"{nom} ({facteur} kg/kWh)"
                    else:
                        display_text = f"{nom} ({facteur})"
                    
                    energie_options += f'<option value="{energie_id}" {selected}>{display_text}</option>'
                
                html += f"""
                <tr class="phase-row" data-index="{i}">
                  <td>
                    <select class="phase-type">
                      <option value="collecte" {selected_collecte}>collecte</option>
                      <option value="traction" {selected_traction}>traction</option>
                      <option value="distribution" {selected_distribution}>distribution</option>
                    </select>
                  </td>
                  <td>
                    <select class="edit-phase-energie">
                      {energie_options}
                    </select>
                  </td>
                  <td><input type="text" class="edit-phase-ville-depart" placeholder="Ville départ" value="{p.get('ville_depart', '')}"></td>
                  <td><input type="text" class="edit-phase-ville-arrivee" placeholder="Ville arrivée" value="{p.get('ville_arrivee', '')}"></td>
                  <td><input type="number" step="0.01" class="edit-phase-conso" value="{conso_value}"></td>
                  <td><input type="number" step="0.01" class="edit-phase-distance" value="{distance_value}"></td>
                  <td><input type="date" class="edit-phase-date" value="{date_value}"></td>
                  <td class="emis-kg">{p.get('emis_kg', 0):.2f}</td>
                  <td class="emis-tkm">{p.get('emis_tkm', 0):.3f}</td>
                  <td><button type="button" class="btn-remove-phase" onclick="removePhase(this.closest('tr'))" title="Supprimer cette phase">🗑️</button></td>
                </tr>
                """
        else:
                        html += """
                <tr class="no-phases">
                  <td colspan="10" style="text-align: center; color: #888; font-style: italic;">
                    Aucune phase définie. Cliquez sur "Ajouter une phase" pour commencer.
                  </td>
                </tr>
                """
        
        html += """
                </tbody>
              </table>
              <div class="form-actions">
                <button type="submit" class="btn-primary">Enregistrer les phases</button>
              </div>
            </form>
          </div>
        </div>
        <script>
          // Variables globales pour les phases
          let energiesData = """ + json.dumps(energies) + """;
          let transportPoids = """ + str(t.get('poids', 1)) + """;
          
          console.log('Données chargées:', energiesData, transportPoids);
          
          // Ajout d'une nouvelle phase
          function addNewPhase() {
              console.log('Fonction addNewPhase appelée');
              const table = document.getElementById('phases-table-edit');
              if (!table) {
                  console.error('Tableau des phases non trouvé');
                  return;
              }
              
              const tbody = table.querySelector('tbody');
              if (!tbody) {
                  console.error('Tbody non trouvé');
                  return;
              }
              
              // Supprimer le message "aucune phase" s'il existe
              const noPhases = tbody.querySelector('.no-phases');
              if (noPhases) {
                  noPhases.remove();
              }
              
              // Générer les options d'énergies
              const energieOptions = Object.entries(energiesData).map(([e_id, e]) => {
                  const unite = e.unite || '';
                  return '<option value="' + e_id + '">' + e.nom + ' (' + e.facteur + ' ' + unite + ')</option>';
              }).join('');
              
              // Date du jour par défaut
              const today = new Date().toISOString().split('T')[0];
              
              // Créer la nouvelle ligne
              const tr = document.createElement('tr');
              tr.className = 'phase-row';
              tr.setAttribute('data-index', Date.now());
              
              tr.innerHTML = '<td>' +
                  '<select class="edit-phase-type">' +
                      '<option value="collecte">collecte</option>' +
                      '<option value="traction">traction</option>' +
                      '<option value="distribution">distribution</option>' +
                  '</select>' +
                  '</td>' +
                  '<td>' +
                      '<select class="edit-phase-energie">' + energieOptions + '</select>' +
                  '</td>' +
                  '<td><input type="text" class="edit-phase-ville-depart" placeholder="Ville départ" value=""></td>' +
                  '<td><input type="text" class="edit-phase-ville-arrivee" placeholder="Ville arrivée" value=""></td>' +
                  '<td><input type="number" step="0.01" class="edit-phase-conso" value="0.00" min="0"></td>' +
                  '<td><input type="number" step="0.01" class="edit-phase-distance" value="0.00" min="0"></td>' +
                  '<td><input type="date" class="edit-phase-date" value="' + today + '"></td>' +
                  '<td class="emis-kg">0.00</td>' +
                  '<td class="emis-tkm">0.000</td>' +
                  '<td>' +
                      '<button type="button" class="btn-remove-phase" onclick="removePhase(this.closest(\'tr\'))" title="Supprimer cette phase">🗑️</button>' +
                  '</td>';
              
              tbody.appendChild(tr);
              console.log('Nouvelle phase ajoutée');
          }
          
          // Suppression d'une phase
          function removePhase(tr) {
              if (confirm('Êtes-vous sûr de vouloir supprimer cette phase ?')) {
                  tr.remove();
                  
                  // Vérifier s'il reste des phases
                  const tbody = document.querySelector('#phases-table-edit tbody');
                  if (tbody && tbody.querySelectorAll('.phase-row').length === 0) {
                      tbody.innerHTML = '<tr class="no-phases"><td colspan="10" style="text-align: center; color: #888; font-style: italic;">Aucune phase définie. Cliquez sur "Ajouter une phase" pour commencer.</td></tr>';
                  }
              }
          }
          
          // Initialisation au chargement
          document.addEventListener('DOMContentLoaded', function() {
              console.log('DOM chargé dans la modal');
              
              // Bouton d'ajout de phase
              const addButton = document.getElementById('btn-add-phase');
              console.log('Bouton trouvé:', addButton);
              
              if (addButton) {
                  addButton.addEventListener('click', function(e) {
                      console.log('Clic sur le bouton d\'ajout de phase');
                      e.preventDefault();
                      addNewPhase();
                  });
                  console.log('Event listener ajouté sur le bouton');
              } else {
                  console.log('Bouton d\'ajout de phase non trouvé');
              }
          });
        </script>
        <style>
          .transport-detail {
            font-size: 1rem;
            color: #222;
            font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
          }
          .detail-info {
            margin-bottom: 2.2rem;
            background: #f7fafd;
            border-radius: 10px;
            padding: 1.2rem 1.5rem 1.2rem 1.5rem;
            box-shadow: 0 1px 4px rgba(42,125,225,0.04);
          }
          .info-row {
            display: flex;
            justify-content: flex-start;
            align-items: center;
            padding: 0.7rem 0;
            border-bottom: 1px solid #e6eaf2;
            gap: 2.5rem;
          }
          .info-row:last-child {
            border-bottom: none;
          }
          .info-row .label {
            font-weight: 600;
            color: #2a7de1;
            min-width: 180px;
            flex-shrink: 0;
            font-size: 1.01em;
          }
          .info-row .value {
            color: #222;
            font-size: 1.01em;
            word-break: break-word;
          }
          .phases-section {
            margin-top: 2.5rem;
          }
          .phases-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.2rem;
          }
          .phases-header h3 {
            color: #2a7de1;
            margin: 0;
            font-size: 1.13rem;
            font-weight: 600;
            letter-spacing: 0.01em;
          }
          .btn-add-phase {
            background: linear-gradient(90deg,#2a7de1 60%,#4fd1c5 100%);
            color: #fff;
            border: none;
            border-radius: 5px;
            padding: 0.5em 1.2em;
            font-size: 1em;
            font-weight: 500;
            cursor: pointer;
            box-shadow: 0 1px 4px rgba(42,125,225,0.07);
            transition: background 0.2s, box-shadow 0.2s;
          }
          .btn-add-phase:hover {
            background: linear-gradient(90deg,#1e5bb8 60%,#38b2ac 100%);
            box-shadow: 0 2px 8px rgba(42,125,225,0.13);
          }
          .phases-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 4px rgba(42,125,225,0.04);
          }
          .phases-table th,
          .phases-table td {
            padding: 0.7rem 0.6rem;
            border-bottom: 1px solid #e6eaf2;
            text-align: left;
          }
          .phases-table th {
            background: #eaf2fb;
            font-weight: 600;
            color: #2a7de1;
            font-size: 0.9rem;
            border-bottom: 2px solid #d0e2fa;
            text-align: left;
          }
          .phases-table td {
            background: #f7fafd;
            vertical-align: middle;
          }
          .phases-table tr:last-child td {
            border-bottom: none;
          }
          .phases-table input,
          .phases-table select {
            width: 100%;
            min-width: 80%;
            max-width: 100%;
            height: 2.2em;
            vertical-align: middle;
          }
          .phases-table input:focus,
          .phases-table select:focus {
            border-color: #2a7de1;
            outline: none;
          }
          .phases-table td:nth-child(3) {
            text-align: right;
            font-variant-numeric: tabular-nums;
            min-width: 120px;
            max-width: 140px;
          }
          .phases-table td:nth-child(4) {
            text-align: right;
            font-variant-numeric: tabular-nums;
            min-width: 120px;
            max-width: 140px;
          }
          .phases-table td:nth-child(5) {
            min-width: 120px;
            max-width: 140px;
          }
          .phases-table td:nth-child(6),
          .phases-table td:nth-child(7) {
            text-align: right;
            font-variant-numeric: tabular-nums;
            min-width: 100px;
            max-width: 120px;
          }
          .btn-delete {
            background: #dc3545;
            color: #fff;
            border: none;
            border-radius: 4px;
            width: 2rem;
            height: 2rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          .btn-delete:hover {
            background: #b91c1c;
          }
          .form-actions {
            text-align: right;
            margin-top: 1.5rem;
          }
          .btn-save {
            background: linear-gradient(90deg,#2a7de1 60%,#4fd1c5 100%);
            color: #fff;
            border: none;
            border-radius: 5px;
            padding: 0.5em 1.2em;
            font-size: 1em;
            font-weight: 500;
            cursor: pointer;
            box-shadow: 0 1px 4px rgba(42,125,225,0.07);
            transition: background 0.2s, box-shadow 0.2s;
          }
          .btn-save:hover {
            background: linear-gradient(90deg,#1e5bb8 60%,#38b2ac 100%);
            box-shadow: 0 2px 8px rgba(42,125,225,0.13);
          }
          
          .highlight-row {
            background: #fff3cd !important;
            border-left: 4px solid #ffc107 !important;
            animation: highlight-pulse 2s ease-in-out;
          }
          
          @keyframes highlight-pulse {
            0%, 100% { background: #fff3cd; }
            50% { background: #ffeaa7; }
          }
          
          .phases-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 4px rgba(42,125,225,0.04);
          }
          .phases-table th,
          .phases-table td {
            padding: 0.7rem 0.6rem;
            border-bottom: 1px solid #e6eaf2;
            text-align: left;
          }
          .phases-table th {
            background: #eaf2fb;
            font-weight: 600;
            color: #2a7de1;
            font-size: 0.9rem;
            border-bottom: 2px solid #d0e2fa;
            text-align: left;
          }
          .phases-table td {
            background: #f7fafd;
            vertical-align: middle;
          }
          .phases-table tr:last-child td {
            border-bottom: none;
          }
          .phases-table input,
          .phases-table select {
            width: 100%;
            min-width: 80%;
            max-width: 100%;
            height: 2.2em;
            vertical-align: middle;
          }
          .phases-table input:focus,
          .phases-table select:focus {
            border-color: #2a7de1;
            outline: none;
          }
          .phases-table td:nth-child(3) {
            text-align: right;
            font-variant-numeric: tabular-nums;
            min-width: 120px;
            max-width: 140px;
          }
          .phases-table td:nth-child(4) {
            text-align: right;
            font-variant-numeric: tabular-nums;
            min-width: 120px;
            max-width: 140px;
          }
          .phases-table td:nth-child(5) {
            min-width: 120px;
            max-width: 140px;
          }
          .phases-table td:nth-child(6),
          .phases-table td:nth-child(7) {
            text-align: right;
            font-variant-numeric: tabular-nums;
            min-width: 100px;
            max-width: 120px;
          }
          .btn-delete {
            background: #dc3545;
            color: #fff;
            border: none;
            border-radius: 4px;
            width: 2rem;
            height: 2rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
          }
          .btn-delete:hover {
            background: #b91c1c;
          }
          .form-actions {
            text-align: right;
            margin-top: 1.5rem;
          }
          .btn-save {
            background: linear-gradient(90deg,#2a7de1 60%,#4fd1c5 100%);
            color: #fff;
            border: none;
            border-radius: 5px;
            padding: 0.5em 1.2em;
            font-size: 1em;
            font-weight: 500;
            cursor: pointer;
            box-shadow: 0 1px 4px rgba(42,125,225,0.07);
            transition: background 0.2s, box-shadow 0.2s;
          }
          .btn-save:hover {
            background: linear-gradient(90deg,#1e5bb8 60%,#38b2ac 100%);
            box-shadow: 0 2px 8px rgba(42,125,225,0.13);
          }
          .highlight-row {
            background: #ffe3ef !important;
            transition: background 0.5s;
          }
          .no-phases td {
            color: #aaa;
            font-style: italic;
            background: #f7fafd;
            text-align: center;
          }
          .phases-table td:nth-child(1) {
            min-width: 120px;
            max-width: 150px;
          }
          .phases-table td:nth-child(2) {
            min-width: 200px;
            max-width: 250px;
          }
          .phases-table select {
            min-width: 100px;
            max-width: 100%;
            height: 2.2em;
            vertical-align: middle;
            font-size: 0.95rem;
          }
        </style>
        """
        
        return jsonify({"html": html})
    except Exception as e:
        print("ERREUR API TRANSPORT :", e)
        return jsonify({"error": str(e)}), 500



# Route supprimée - conflit avec la nouvelle API des phases
# Cette route sauvegardait dans transports.json au lieu de transports_simple.json

@app.route("/import-csv", methods=["POST"])
@login_required
def import_csv():
    import csv
    import io
    from werkzeug.utils import secure_filename
    from datetime import datetime
    
    if 'csv_file' not in request.files:
        flash('Aucun fichier sélectionné', 'error')
        return redirect(url_for('transport'))
    
    file = request.files['csv_file']
    if file.filename == '':
        flash('Aucun fichier sélectionné', 'error')
        return redirect(url_for('transport'))
    
    if not file.filename or not file.filename.lower().endswith('.csv'):
        flash('Le fichier doit être au format CSV', 'error')
        return redirect(url_for('transport'))

    try:
        # Lire le fichier CSV
        content = file.read().decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))

        # Charger les données existantes
        clients, energies, transports, vehicules = normalize_data()

        # Options d'import
        skip_duplicates = 'skip_duplicates' in request.form
        validate_data = 'validate_data' in request.form

        imported_count = 0
        skipped_count = 0
        errors = []

        # Ignorer la première ligne (en-têtes) et commencer à la ligne 2
        next(csv_reader, None)  # Ignorer la première ligne
        
        for row_num, row in enumerate(csv_reader, start=2):  # Commencer à 2 car ligne 1 = en-têtes
            try:
                # Format attendu: PCH,"PAL","1051","GF#000478","","07/07/25","ETS-FELIX","10/07/25","PROVENCE VRD","21/07/25","216","1","0","71.5"
                if len(row) < 11:  # Au minimum les 11 premières colonnes
                    errors.append(f"Ligne {row_num}: Format invalide - colonnes manquantes")
                    continue

                # Mapping selon le format spécifié
                statut = row[0].strip() if len(row) > 0 else ""  # PCH
                type_marchandise = row[1].strip() if len(row) > 1 else ""  # PAL
                reference = row[2].strip() if len(row) > 2 else ""  # 1051
                numero_client = row[3].strip() if len(row) > 3 else ""  # GF#000478
                champ_vide = row[4].strip() if len(row) > 4 else ""  # (ignoré)
                date_saisie = row[5].strip() if len(row) > 5 else ""  # 07/07/25
                nom_client_commande = row[6].strip() if len(row) > 6 else ""  # ETS-FELIX (ignoré)
                date_collecte = row[7].strip() if len(row) > 7 else ""  # 10/07/25
                nom_client_destinataire = row[8].strip() if len(row) > 8 else ""  # PROVENCE VRD
                date_livraison = row[9].strip() if len(row) > 9 else ""  # 21/07/25
                poids_str = row[10].strip() if len(row) > 10 else "0"  # 216
                nb_palettes = row[11].strip() if len(row) > 11 else "0"  # 1
                nb_km = row[12].strip() if len(row) > 12 else "0"  # 0
                montant_transport = row[13].strip() if len(row) > 13 else "0"  # 71.5

                # Validation des données obligatoires
                if not reference or not numero_client:
                    errors.append(f"Ligne {row_num}: Référence et numéro client obligatoires")
                    continue

                # Ne traiter que les transports avec le statut PCH (Pris en charge)
                if statut.upper() != "PCH":
                    skipped_count += 1
                    continue

                # Créer une référence unique (sans préfixe TR)
                ref = reference  # Utiliser directement la référence sans préfixe

                # Convertir le poids (en kg vers tonnes)
                try:
                    poids_kg = float(poids_str.replace(',', '.')) if poids_str else 0
                    poids_tonnes = poids_kg / 1000  # Conversion kg vers tonnes
                except ValueError:
                    poids_tonnes = 0

                # Convertir les dates (format DD/MM/YY vers YYYY-MM-DD)
                def convert_date(date_str):
                    if not date_str:
                        return ""
                    try:
                        # Format attendu: DD/MM/YY
                        if len(date_str.split('/')) == 3:
                            day, month, year = date_str.split('/')
                            # Ajouter 20 pour les années 20xx
                            if len(year) == 2:
                                year = f"20{year}"
                            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        return date_str
                    except:
                        return date_str

                # Déterminer la date du transport (utiliser la date de collecte si disponible, sinon date de saisie)
                date_transport = convert_date(date_collecte) if date_collecte else convert_date(date_saisie)

                # Recherche automatique du client destinataire
                client_destinataire = numero_client  # Par défaut, utiliser le numéro client
                
                # Si on a un nom de client destinataire, essayer de le trouver dans la base
                if nom_client_destinataire:
                    # Rechercher par nom dans les clients existants
                    for cid, client_data in clients.items():
                        if client_data.get('nom', '').upper() == nom_client_destinataire.upper():
                            client_destinataire = cid
                            break
                    
                    # Si pas trouvé, ne pas créer de nouveau client - utiliser l'émetteur
                    if client_destinataire == numero_client:
                        # Le client destinataire n'est pas notre client, utiliser l'émetteur
                        client_destinataire = numero_client

                # Créer le client émetteur s'il n'existe pas (seulement les clients GF#000000)
                if numero_client not in clients and numero_client.startswith('GF#'):
                    clients[numero_client] = {
                        "nom": nom_client_commande if nom_client_commande else f"Client {numero_client}",
                        "adresse": "",
                        "contact": "",
                        "email": "",
                        "telephone": ""
                    }



                # Vérifier les doublons
                if ref in transports:
                    if skip_duplicates:
                        skipped_count += 1
                        continue
                    else:
                        errors.append(f"Ligne {row_num}: Référence '{ref}' déjà existante")
                        continue

                # Créer les phases selon le statut
                phases = []
                
                # Si statut = "PCH" et qu'on a une date de collecte, créer une phase de collecte
                if statut.upper() == "PCH" and date_collecte:
                    phases.append({
                        "type": "collecte",
                        "date": convert_date(date_collecte),
                        "lieu": nom_client_commande if nom_client_commande else numero_client,
                        "emis_kg": 0,  # À calculer plus tard
                        "emis_tkm": 0  # À calculer plus tard
                    })

                # Créer le transport
                transports[ref] = {
                    "client": client_destinataire.upper(),
                    "proprietaire": "",
                    "poids": poids_tonnes,
                    "date": date_transport,
                    "emis_kg": 0,  # À calculer plus tard
                    "emis_tkm": 0,  # À calculer plus tard
                    "phases": phases,
                    # Données spécifiques au format
                    "statut": statut,
                    "type_marchandise": type_marchandise,
                    "numero_client_emetteur": numero_client,
                    "nom_client_commande": nom_client_commande,
                    "date_saisie": convert_date(date_saisie),
                    "date_collecte": convert_date(date_collecte),
                    "date_livraison": convert_date(date_livraison),
                    "palettes": int(nb_palettes) if nb_palettes.isdigit() else 0,
                    "km": float(nb_km.replace(',', '.')) if nb_km else 0,
                    "montant_transport": float(montant_transport.replace(',', '.')) if montant_transport else 0
                }

                imported_count += 1

            except ValueError as e:
                errors.append(f"Ligne {row_num}: Erreur de format - {str(e)}")
            except Exception as e:
                errors.append(f"Ligne {row_num}: Erreur inattendue - {str(e)}")

        # Sauvegarder les données
        if imported_count > 0:
            save_json("transports.json", transports)
            save_json("clients.json", clients)

        # Préparer le message de résultat et rediriger
        if imported_count > 0:
            # Message de succès avec détails
            message = f"✅ Import réussi ! {imported_count} transport(s) importé(s)"
            if skipped_count > 0:
                message += f", {skipped_count} transport(s) ignoré(s) (statut non PCH)"
            if errors:
                message += f", {len(errors)} erreur(s) rencontrée(s)"
            
            flash(message, 'success')
            
            # Rediriger vers la page des opérations
            return redirect(url_for('transport'))
        else:
            # Aucun transport importé
            if errors:
                error_message = f"❌ Import échoué : {len(errors)} erreur(s)"
                if len(errors) <= 3:
                    error_message += " - " + "; ".join(errors)
                else:
                    error_message += f" - {errors[0]}; {errors[1]}; ... et {len(errors)-2} autres"
                flash(error_message, 'error')
            else:
                flash("❌ Aucun transport importé. Vérifiez le format du fichier CSV.", 'warning')
            
            return redirect(url_for('transport'))

    except Exception as e:
        flash(f"❌ Erreur lors de la lecture du fichier CSV : {str(e)}", 'error')
        return redirect(url_for('transport'))

@app.route("/download-csv-template")
@login_required
def download_csv_template():
    from flask import send_file
    import io

    # Créer le contenu du modèle CSV basé sur le format spécifié
    csv_content = """Statut,Type Marchandise,Référence,Numéro Client,Champ Vide,Date Saisie,Nom Client Commande,Date Collecte,Nom Client Destinataire,Date Livraison,Poids (kg),Nombre Palettes,Nombre Km,Montant Transport
PCH,PAL,1051,GF#000478,,07/07/25,ETS-FELIX,10/07/25,PROVENCE VRD,21/07/25,216,1,0,71.5
PCH,PAL,1052,GF#000479,,08/07/25,ETS-MARTIN,11/07/25,PROVENCE VRD,22/07/25,150,1,0,65.0
"""

    # Créer un fichier en mémoire
    output = io.BytesIO()
    output.write(csv_content.encode('utf-8'))
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='modele_import_transports.csv'
    )

# --- Redirect /parametrage to default ---
@app.route("/parametrage")
@login_required
def parametrage():
    return redirect(url_for("parametrage_clients"))

# --- Paramétrage Handlers ---
def handle_param(section):
    fname     = f"{section}.json"
    data      = load_json(fname)
    edit_id   = request.args.get("edit_id","")
    edit_data = data.get(edit_id, {}) if edit_id else {}

    if request.method == "POST":
        form = dict(request.form)
        _id  = form.pop("id","").upper()
        if not _id:
            flash("L'ID est requis.", "warning")
        else:
            data[_id] = form
            save_json(fname, data)
            # Retourner un indicateur de succès au lieu de rediriger directement
            return data, edit_id, edit_data, True  # True indique qu'il faut rediriger

    return data, edit_id, edit_data, False  # False indique qu'il ne faut pas rediriger

@app.route("/parametrage/clients", methods=["GET","POST"])
@login_required
def parametrage_clients():
    clients, energies, transports = normalize_data_simple()
    data, edit_id, edit_data, redirect_needed = handle_param("clients")
    if redirect_needed:
        return redirect(url_for("parametrage_clients"))
    return render_template("clients.html",
                           clients=clients,
                           form_data=data,
                           edit_id=edit_id,
                           edit_data=edit_data)



@app.route("/parametrage/impact", methods=["GET", "POST"])
@login_required
def parametrage_impact():
    if request.method == "POST":
        try:
            # Récupérer les données du formulaire
            seuils_data = request.get_json()
            
            # Valider les données
            if not seuils_data or 'seuils' not in seuils_data:
                return jsonify({"success": False, "error": "Données invalides"}), 400
            
            # Sauvegarder la configuration
            save_json("impact_config.json", seuils_data)
            
            return jsonify({"success": True, "message": "Configuration sauvegardée"})
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    # GET : afficher la configuration actuelle
    impact_config = load_json("impact_config.json")
    return render_template("impact_config.html", impact_config=impact_config)

@app.route("/parametrage/energies/<code>/delete", methods=["POST"])
@login_required
def supprimer_energie(code):
    try:
        # Charger les données actuelles
        energies = load_json("energies.json")
        
        # Vérifier que l'énergie existe
        if code not in energies:
            flash(f"Énergie {code} introuvable", "warning")
            return redirect(url_for("parametrage_energies"))
        
        # Vérifier si l'énergie est utilisée dans des transports
        clients, energies, transports = normalize_data_simple()
        energie_utilisee = False
        
        for ref, t in transports.items():
            if t.get("energie") == code:
                energie_utilisee = True
                break
        
        if energie_utilisee:
            flash(f"Impossible de supprimer l'énergie {code} : elle est utilisée dans des transports", "warning")
            return redirect(url_for("parametrage_energies"))
        
        # Supprimer l'énergie
        del energies[code]
        save_json("energies.json", energies)
        
        flash(f"Énergie {code} supprimée avec succès", "success")
        
    except Exception as e:
        flash(f"Erreur lors de la suppression : {str(e)}", "error")
    
    return redirect(url_for("parametrage_entretien"))





# --- Client Detail Route ---
@app.route("/clients/<client_id>")
@login_required
def client_detail(client_id):
    clients, energies, transports = normalize_data_simple()
    client = clients.get(client_id.upper())
    if not client:
        flash(f"Client {client_id} introuvable", "warning")
        return redirect(url_for("parametrage_clients"))

    ct = []
    for ref, t in transports.items():
        if t.get("client") == client_id.upper():
            ct.append({
                "ref":      ref,
                "date":     t.get("date",""),
                "emis_kg":  t.get("emis_kg", 0),
                "emis_tkm": t.get("emis_tkm",0)
            })

    return render_template("client_detail.html",
                           client_id=client_id.upper(),
                           client=client,
                           transports=ct)

# --- Administration Route ---
@app.route("/administration")
@login_required
def administration():
    users = load_json("users.json")
    return render_template("administration.html", users=users)



@app.route("/api/energies", methods=["GET", "POST"])
@login_required
def api_energies():
    """API pour gérer les énergies"""
    if request.method == "GET":
        # Utiliser le cache pour de meilleures performances
        energies = get_energies_fresh()
        return jsonify(energies)
    
    elif request.method == "POST":
        try:
            # Recharger les données fraîches directement depuis le fichier
            energies = load_json("energies.json")
            
            # Mettre à jour l'énergie
            data = request.get_json()
            energie_id = data.get('id')
            energie_data = data.get('data')
            
            if energie_id and energie_data:
                # Préserver les facteurs existants s'ils existent
                if energie_id in energies:
                    existing_facteurs = {
                        "phase_amont": energies[energie_id].get("phase_amont", 0),
                        "phase_fonctionnement": energies[energie_id].get("phase_fonctionnement", 0),
                        "total": energies[energie_id].get("total", 0)
                    }
                    energie_data.update(existing_facteurs)
                
                energies[energie_id] = energie_data
                save_json("energies.json", energies)
                
                # Forcer le rechargement du cache
                clear_energies_cache()
                
                return jsonify({"success": True, "message": "Énergie mise à jour avec succès"})
            else:
                return jsonify({"success": False, "error": "Données manquantes"}), 400
                
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/energies/reload")
@login_required
def api_energies_reload():
    """API pour forcer le rechargement des énergies"""
    try:
        # Forcer le rechargement du cache
        clear_energies_cache()
        return jsonify({"success": True, "message": "Rechargement des énergies effectué"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/energies/<energie_id>/facteurs", methods=["PUT"])
@login_required
def api_energie_facteurs(energie_id):
    """API pour mettre à jour les facteurs d'émission d'une énergie"""
    try:
        energies = load_json("energies.json")
        
        if energie_id not in energies:
            return jsonify({"success": False, "error": "Énergie non trouvée"})
        
        data = request.get_json()
        
        # Mettre à jour les facteurs d'émission
        energies[energie_id].update({
            "phase_amont": data.get('phase_amont', 0),
            "phase_fonctionnement": data.get('phase_fonctionnement', 0),
            "total": data.get('total', 0),
            "facteur": data.get('total', 0)  # Synchroniser le facteur global avec le total
        })
        
        # Sauvegarder
        save_json("energies.json", energies)
        
        # Forcer le rechargement du cache
        clear_energies_cache()
        
        return jsonify({"success": True, "message": f"Facteurs d'émission de {energie_id} mis à jour avec succès"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/clients", methods=["GET"])
@login_required
def api_clients():
    """API pour récupérer la liste des clients"""
    try:
        clients, _, _ = normalize_data_simple()
        return jsonify({"success": True, "clients": clients})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/transport/update-client", methods=["POST"])
@login_required
def update_transport_client():
    """API pour mettre à jour le client d'un transport"""
    try:
        data = request.get_json()
        transport_ref = data.get('transport_ref')
        new_client = data.get('new_client')
        
        if not transport_ref or not new_client:
            return jsonify({"success": False, "error": "Données manquantes"})
        
        # Charger les transports
        clients, energies, transports = normalize_data_simple()
        
        # Vérifier que le transport existe
        if transport_ref not in transports:
            return jsonify({"success": False, "error": "Transport non trouvé"})
        
        # Vérifier que le nouveau client existe
        if new_client not in clients:
            return jsonify({"success": False, "error": f"Client non trouvé: {new_client}. Clients disponibles: {list(clients.keys())}"})
        
        # Mettre à jour le client
        transports[transport_ref]['client'] = new_client.upper()
        
        # Sauvegarder dans le fichier
        save_json("transports_simple.json", transports)
        
        return jsonify({
            "success": True, 
            "message": f"Client du transport {transport_ref} mis à jour vers {new_client}"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})









def format_date_fr(date_str):
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        mois_fr = [
            "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        return f"{d.day} {mois_fr[d.month]} {d.year}"
    except Exception:
        return date_str

def get_impact_classification(facteur, impact_config):
    """
    Détermine la classification d'impact environnemental d'une énergie
    basée sur son facteur d'émission et la configuration des seuils
    """
    try:
        facteur = float(facteur)
        
        # Trier les seuils par ordre croissant
        seuils_tries = sorted(impact_config['seuils'], key=lambda x: x['min'])
        
        # Chercher le seuil approprié
        for seuil in seuils_tries:
            if facteur >= seuil['min'] and facteur <= seuil['max']:
                return {
                    'nom': seuil['nom'],
                    'couleur': seuil['couleur'],
                    'texte': seuil['texte'],
                    'emoji': seuil['emoji']
                }
        
        # Si aucun seuil trouvé, essayer de trouver le plus proche
        if facteur < seuils_tries[0]['min']:
            # En dessous du seuil minimum
            return {
                'nom': 'Très faible',
                'couleur': '#dcfce7',
                'texte': '#166534',
                'emoji': '🟢'
            }
        elif facteur > seuils_tries[-1]['max']:
            # Au-dessus du seuil maximum
            return {
                'nom': 'Très élevé',
                'couleur': '#fecaca',
                'texte': '#991b1b',
                'emoji': '⚫'
            }
        else:
            # Entre deux seuils, prendre le plus proche
            for i in range(len(seuils_tries) - 1):
                if seuils_tries[i]['max'] < facteur < seuils_tries[i + 1]['min']:
                    # Calculer la distance aux deux seuils
                    dist_prev = facteur - seuils_tries[i]['max']
                    dist_next = seuils_tries[i + 1]['min'] - facteur
                    
                    if dist_prev <= dist_next:
                        return {
                            'nom': seuils_tries[i]['nom'],
                            'couleur': seuils_tries[i]['couleur'],
                            'texte': seuils_tries[i]['texte'],
                            'emoji': seuils_tries[i]['emoji']
                        }
                    else:
                        return {
                            'nom': seuils_tries[i + 1]['nom'],
                            'couleur': seuils_tries[i + 1]['couleur'],
                            'texte': seuils_tries[i + 1]['texte'],
                            'emoji': seuils_tries[i + 1]['emoji']
                        }
        
        # Fallback
        return {
            'nom': 'Inconnu',
            'couleur': '#e5e7eb',
            'texte': '#6b7280',
            'emoji': '❓'
        }
        
    except (ValueError, TypeError, KeyError):
        return {
            'nom': 'Inconnu',
            'couleur': '#e5e7eb',
            'texte': '#6b7280',
            'emoji': '❓'
        }

@app.route("/parametrage_vehicules")
@login_required
def parametrage_vehicules():
    """Page de gestion des véhicules"""
    return render_template("parametrage_vehicules.html")

@app.route("/parametrage_energies")
@login_required
def parametrage_energies():
    """Page de gestion des énergies"""
    return render_template("parametrage_energies.html")

@app.route("/api/vehicules", methods=["GET", "POST"])
@login_required
def api_vehicules():
    """API pour gérer les véhicules"""
    try:
        if request.method == "GET":
            # Charger les véhicules depuis le fichier
            vehicules = load_json("vehicules.json")
            # Convertir l'objet en tableau pour le frontend
            vehicules_list = list(vehicules.values())
            return jsonify({"success": True, "vehicules": vehicules_list})
            
        elif request.method == "POST":
            # Ajouter un nouveau véhicule
            data = request.get_json()
            vehicule_id = data.get('id')
            
            if not vehicule_id:
                return jsonify({"success": False, "error": "ID du véhicule requis"})
            
            # Charger les véhicules existants
            vehicules = load_json("vehicules.json")
            
            # Vérifier que l'ID n'existe pas déjà
            if vehicule_id in vehicules:
                return jsonify({"success": False, "error": f"Un véhicule avec l'ID {vehicule_id} existe déjà"})
            
            # Ajouter le nouveau véhicule
            vehicules[vehicule_id] = {
                "id": vehicule_id,
                "nom": data.get('nom', ''),
                "energie": data.get('energie', ''),
                "capacite": data.get('capacite', 0),
                "consommation": data.get('consommation', 0),
                "emissions": data.get('emissions', 0),
                "description": data.get('description', '')
            }
            
            # Sauvegarder
            save_json("vehicules.json", vehicules)
            return jsonify({"success": True, "message": f"Véhicule {vehicule_id} ajouté avec succès"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/vehicules/<vehicule_id>", methods=["PUT", "DELETE"])
@login_required
def api_vehicule_operations(vehicule_id):
    """API pour modifier ou supprimer un véhicule spécifique"""
    try:
        vehicules = load_json("vehicules.json")
        
        if vehicule_id not in vehicules:
            return jsonify({"success": False, "error": "Véhicule non trouvé"})
        
        if request.method == "PUT":
            # Modifier le véhicule
            data = request.get_json()
            
            vehicules[vehicule_id].update({
                "nom": data.get('nom', ''),
                "energie": data.get('energie', ''),
                "capacite": data.get('capacite', 0),
                "consommation": data.get('consommation', 0),
                "emissions": data.get('emissions', 0),
                "description": data.get('description', '')
            })
            
            save_json("vehicules.json", vehicules)
            return jsonify({"success": True, "message": f"Véhicule {vehicule_id} modifié avec succès"})
            
        elif request.method == "DELETE":
            # Supprimer le véhicule
            del vehicules[vehicule_id]
            save_json("vehicules.json", vehicules)
            return jsonify({"success": True, "message": f"Véhicule {vehicule_id} supprimé avec succès"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/transport/<transport_ref>/phases", methods=["GET", "POST", "PUT", "DELETE"])
@login_required
def api_transport_phases(transport_ref):
    """API pour gérer les phases d'un transport"""
    try:
        clients, energies, transports = normalize_data_simple()
        
        print(f"DEBUG API phases: transport_ref reçu: '{transport_ref}'")
        print(f"DEBUG API phases: clés disponibles dans transports: {list(transports.keys())}")
        print(f"DEBUG API phases: transport_ref in transports: {transport_ref in transports}")
        
        if transport_ref not in transports:
            return jsonify({"success": False, "error": f"Transport non trouvé: '{transport_ref}'. Transports disponibles: {list(transports.keys())}"})
        
        if request.method == "GET":
            # Récupérer les phases du transport
            print(f"DEBUG API GET: transport {transport_ref} trouvé")
            print(f"DEBUG API GET: contenu du transport: {transports[transport_ref]}")
            print(f"DEBUG API GET: phases du transport: {transports[transport_ref].get('phases', {})}")
            phases = transports[transport_ref].get('phases', {})
            return jsonify({"success": True, "phases": phases})
            
        elif request.method == "POST":
            try:
                print(f"DEBUG API POST: début de l'ajout de phase pour le transport {transport_ref}")
                
                # Ajouter une nouvelle phase
                data = request.get_json()
                print(f"DEBUG API POST: données reçues: {data}")
                phase_id = f"P{len(transports[transport_ref].get('phases', {})) + 1:03d}"
                print(f"DEBUG API POST: phase_id généré: {phase_id}")
                
                if 'phases' not in transports[transport_ref]:
                    transports[transport_ref]['phases'] = {}
                    print(f"DEBUG API POST: création de la section phases pour le transport {transport_ref}")
                
                print(f"DEBUG API POST: avant ajout - phases existantes: {list(transports[transport_ref].get('phases', {}).keys())}")
                
                # Créer la phase étape par étape pour identifier le problème
                # Fonction helper pour convertir en float en gérant None
                def safe_float(value, default=0.0):
                    if value is None or value == '':
                        return default
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                # Fonction helper pour les entiers
                def safe_int(value, default=1):
                    if value is None or value == '':
                        return default
                    try:
                        return int(value)
                    except (ValueError, TypeError):
                        return default
                
                phase_data = {
                    "id": phase_id,
                    "type": data.get('type_phase'),
                    "ordre": safe_int(data.get('ordre'), 1),
                    "ville_depart": data.get('ville_depart'),
                    "ville_arrivee": data.get('ville_arrivee'),
                    "distance_km": safe_float(data.get('distance_km'), 0),
                    "vehicule_id": data.get('vehicule_id'),
                    "poids_tonnes": safe_float(data.get('poids_tonnes'), 0),
                    "poids_vehicule": safe_float(data.get('poids_vehicule'), 0),
                    "energie": data.get('energie'),
                    "consommation": safe_float(data.get('consommation'), 0),
                    "unite_consommation": data.get('unite_consommation'),
                    "emis_vehicule": safe_float(data.get('emis_vehicule'), 0),
                    "emis_transport": safe_float(data.get('emis_transport'), 0),
                    "emis_total": safe_float(data.get('emis_total'), 0),
                    "emis_tkm": safe_float(data.get('emis_tkm'), 0),
                    "date_collecte": data.get('date_collecte'),
                    "date_distribution": data.get('date_distribution')
                }
                
                print(f"DEBUG API POST: phase_data créé: {phase_data}")
                
                transports[transport_ref]['phases'][phase_id] = phase_data
                
                print(f"DEBUG API POST: après ajout - phases du transport: {list(transports[transport_ref].get('phases', {}).keys())}")
                print(f"DEBUG API POST: contenu complet du transport après ajout: {transports[transport_ref]}")
                
                print(f"DEBUG API POST: phase {phase_id} ajoutée au transport {transport_ref}")
                print(f"DEBUG API POST: phases du transport après ajout: {transports[transport_ref].get('phases', {})}")
                
                print(f"DEBUG API POST: appel de save_json...")
                save_json("transports_simple.json", transports)
                print(f"DEBUG API POST: save_json terminé")
                
                # Forcer le rechargement des données pour vérifier la sauvegarde
                print(f"DEBUG API POST: vérification de la sauvegarde...")
                transports_verif = load_json("transports_simple.json")
                print(f"DEBUG API POST: transport {transport_ref} après sauvegarde: {transports_verif.get(transport_ref, {})}")
                print(f"DEBUG API POST: phases du transport après sauvegarde: {transports_verif.get(transport_ref, {}).get('phases', {})}")
                
                return jsonify({"success": True, "phase_id": phase_id, "message": "Phase ajoutée avec succès"})
                
            except Exception as e:
                print(f"DEBUG API POST: ERREUR lors de l'ajout de la phase: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({"success": False, "error": f"Erreur lors de l'ajout de la phase: {str(e)}"})
            
        elif request.method == "PUT":
            # Modifier une phase existante
            data = request.get_json()
            phase_id = data.get('phase_id')
            
            if 'phases' not in transports[transport_ref] or phase_id not in transports[transport_ref]['phases']:
                return jsonify({"success": False, "error": "Phase non trouvée"})
            
            # Mettre à jour la phase
            # Utiliser la même fonction helper safe_float
            def safe_float(value, default=0.0):
                if value is None or value == '':
                    return default
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default
            
            # Fonction helper pour les entiers
            def safe_int(value, default=1):
                if value is None or value == '':
                    return default
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return default
            
            # Debug: afficher les données reçues
            print(f"DEBUG API PUT: données reçues pour modification: {data}")
            print(f"DEBUG API PUT: phase_id: {phase_id}")
            print(f"DEBUG API PUT: type_phase reçu: {data.get('type_phase')}")
            print(f"DEBUG API PUT: type reçu: {data.get('type')}")
            
            # Utiliser le bon champ pour le type (type_phase ou type)
            type_phase = data.get('type_phase') or data.get('type')
            print(f"DEBUG API PUT: type_phase final utilisé: {type_phase}")
            
            transports[transport_ref]['phases'][phase_id].update({
                "type": type_phase,
                "ordre": safe_int(data.get('ordre'), 1),
                "ville_depart": data.get('ville_depart'),
                "ville_arrivee": data.get('ville_arrivee'),
                "distance_km": safe_float(data.get('distance_km'), 0),
                "vehicule_id": data.get('vehicule_id'),
                "poids_tonnes": safe_float(data.get('poids_tonnes'), 0),
                "poids_vehicule": safe_float(data.get('poids_vehicule'), 0),
                "energie": data.get('energie'),
                "consommation": safe_float(data.get('consommation'), 0),
                "unite_consommation": data.get('unite_consommation'),
                "emis_vehicule": safe_float(data.get('emis_vehicule'), 0),
                "emis_transport": safe_float(data.get('emis_transport'), 0),
                "emis_total": safe_float(data.get('emis_total'), 0),
                "emis_tkm": safe_float(data.get('emis_tkm'), 0),
                "date_collecte": data.get('date_collecte'),
                "date_distribution": data.get('date_distribution')
            })
            
            # Debug: afficher la phase après modification
            print(f"DEBUG API PUT: phase après modification: {transports[transport_ref]['phases'][phase_id]}")
            
            save_json("transports_simple.json", transports)
            
            # Vérifier la sauvegarde
            transports_verif = load_json("transports_simple.json")
            print(f"DEBUG API PUT: vérification - phase après sauvegarde: {transports_verif.get(transport_ref, {}).get('phases', {}).get(phase_id, {})}")
            
            return jsonify({"success": True, "message": "Phase modifiée avec succès"})
            
        elif request.method == "DELETE":
            # Supprimer une phase
            data = request.get_json()
            phase_id = data.get('phase_id')
            
            if 'phases' not in transports[transport_ref] or phase_id not in transports[transport_ref]['phases']:
                return jsonify({"success": False, "error": "Phase non trouvée"})
            
            del transports[transport_ref]['phases'][phase_id]
            save_json("transports_simple.json", transports)
            return jsonify({"success": True, "message": "Phase supprimée avec succès"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

app.jinja_env.filters['date_fr'] = format_date_fr
app.jinja_env.globals['get_impact_classification'] = get_impact_classification

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
