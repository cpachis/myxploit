#!/usr/bin/env python3
"""
Script pour vérifier les transports via l'application Flask
"""

import os
import sys
from app import app, db
from models import create_models

def check_transports():
    """Vérifier les transports via l'application Flask"""
    
    with app.app_context():
        try:
            # Créer les modèles
            models = create_models(db)
            Transport = models['Transport']
            
            print("🔍 Vérification des transports via Flask...")
            print("=" * 50)
            
            # Compter les transports
            count = Transport.query.count()
            print(f"📊 Nombre total de transports: {count}")
            
            if count > 0:
                # Récupérer tous les transports
                transports = Transport.query.order_by(Transport.id.desc()).all()
                
                print(f"\n📋 Détails des {len(transports)} transports:")
                for transport in transports:
                    print(f"\n  🚛 Transport ID: {transport.id}")
                    print(f"     Référence: {transport.ref}")
                    print(f"     Date: {transport.date}")
                    print(f"     Collecte: {transport.lieu_collecte}")
                    print(f"     Livraison: {transport.lieu_livraison}")
                    print(f"     Poids: {transport.poids_tonnes} tonnes")
                    print(f"     Distance: {transport.distance_km} km")
                    print(f"     Émissions: {transport.emis_kg} kg CO₂e")
                    print(f"     Émissions/t.km: {transport.emis_tkm} kg CO₂e/t.km")
                    print(f"     Niveau: {transport.niveau_calcul}")
                    print(f"     Type véhicule: {transport.type_vehicule}")
                    print(f"     Énergie: {transport.energie}")
                    print(f"     Consommation: {transport.conso_vehicule} L/100km")
                    print(f"     Véhicule dédié: {transport.vehicule_dedie}")
                    print(f"     Client: {transport.client}")
            else:
                print("❌ Aucun transport trouvé dans la base de données")
            
            # Vérifier les autres modèles
            for model_name in ['Energie', 'Vehicule', 'Client', 'User']:
                if model_name in models:
                    model = models[model_name]
                    count = model.query.count()
                    print(f"📊 Table {model_name}: {count} enregistrements")
            
            print("\n✅ Vérification terminée avec succès")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la vérification: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = check_transports()
    if not success:
        sys.exit(1)
