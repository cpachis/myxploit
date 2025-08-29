#!/usr/bin/env python3
"""
Script de diagnostic pour la base de données MyXploit
Permet de vérifier l'état de la base et identifier les problèmes
"""

import os
import sys
from dotenv import load_dotenv

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Charger les variables d'environnement
load_dotenv('env.local')

def test_database_connection():
    """Test de connexion à la base de données"""
    print("🔍 Test de connexion a la base de donnees...")
    
    try:
        from app import app, db
        from sqlalchemy import text
        
        with app.app_context():
            # Test de connexion simple
            result = db.session.execute(text('SELECT 1'))
            print("✅ Connexion a la base reussie")
            
            # Vérifier la structure de la table energies
            print("\n🔍 Structure de la table 'energies'...")
            
            # Compter les énergies existantes
            from app import Energie
            energie_count = Energie.query.count()
            print(f"📊 Nombre d'energies en base: {energie_count}")
            
            # Vérifier les colonnes disponibles
            print("\n🔍 Colonnes disponibles dans le modele Energie:")
            energie_instance = Energie()
            for column in Energie.__table__.columns:
                print(f"   - {column.name}: {column.type} (nullable: {column.nullable})")
            
            # Vérifier la base de données réelle
            print("\n🔍 Verification de la base de donnees reelle...")
            
            if 'postgresql' in str(db.engine.url):
                print("🐘 Base PostgreSQL detectee")
                
                # Vérifier la structure réelle de la table
                with db.engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_name = 'energies'
                        ORDER BY ordinal_position
                    """))
                    
                    columns = []
                    for row in result:
                        columns.append({
                            'name': row[0],
                            'type': row[1],
                            'nullable': row[2],
                            'default': row[3]
                        })
                    
                    print(f"📋 Colonnes reelles en base ({len(columns)}):")
                    for col in columns:
                        print(f"   - {col['name']}: {col['type']} (nullable: {col['nullable']}, default: {col['default']})")
                    
                    # Vérifier les contraintes
                    result = conn.execute(text("""
                        SELECT constraint_name, constraint_type
                        FROM information_schema.table_constraints
                        WHERE table_name = 'energies'
                    """))
                    
                    constraints = []
                    for row in result:
                        constraints.append({
                            'name': row[0],
                            'type': row[1]
                        })
                    
                    print(f"\n🔒 Contraintes de la table:")
                    for const in constraints:
                        print(f"   - {const['name']}: {const['type']}")
                    
            else:
                print("📱 Base SQLite detectee")
                
            # Test de création d'une énergie
            print("\n🧪 Test de creation d'une energie...")
            
            try:
                # Créer une énergie de test
                test_energie = Energie(
                    nom="Test Diagnostic",
                    identifiant="test-diagnostic",
                    unite="L",
                    facteur=1.0,
                    description="Energie de test pour diagnostic"
                )
                
                print("✅ Objet Energie cree avec succes")
                print(f"   - nom: {test_energie.nom}")
                print(f"   - identifiant: {test_energie.identifiant}")
                print(f"   - unite: {test_energie.unite}")
                print(f"   - facteur: {test_energie.facteur}")
                
                # Ajouter à la session
                db.session.add(test_energie)
                print("✅ Objet ajoute a la session")
                
                # Flush pour validation
                db.session.flush()
                print("✅ Objet valide par la base de donnees")
                
                # Rollback pour ne pas sauvegarder
                db.session.rollback()
                print("✅ Rollback effectue (test non sauvegarde)")
                
            except Exception as e:
                print(f"❌ Erreur lors du test de creation: {str(e)}")
                print(f"❌ Type d'erreur: {type(e).__name__}")
                db.session.rollback()
                
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {str(e)}")
        print(f"❌ Type d'erreur: {type(e).__name__}")
        return False

def test_api_endpoint():
    """Test de l'endpoint API"""
    print("\n🌐 Test de l'endpoint API...")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Test avec des données valides
            test_data = {
                "identifiant": "test-api-diagnostic",
                "nom": "Test API Diagnostic",
                "facteur": 1.0,
                "description": "Test de l'API",
                "unite": "L"
            }
            
            print(f"📤 Donnees de test: {test_data}")
            
            response = client.post('/api/energies', 
                                json=test_data,
                                content_type='application/json')
            
            print(f"📥 Reponse HTTP: {response.status_code}")
            print(f"📥 Headers: {dict(response.headers)}")
            
            if response.data:
                try:
                    response_json = response.get_json()
                    print(f"📥 JSON de reponse: {response_json}")
                except Exception as json_error:
                    print(f"📥 Contenu brut: {response.data.decode('utf-8')}")
                    print(f"⚠️ Erreur parsing JSON: {str(json_error)}")
            
            if response.status_code == 200:
                print("✅ API fonctionne correctement")
            elif response.status_code == 400:
                print("⚠️ API retourne une erreur 400 (Bad Request)")
                if response.data:
                    try:
                        error_data = response.get_json()
                        print(f"❌ Details de l'erreur: {error_data}")
                    except:
                        print(f"❌ Erreur sans details: {response.data.decode('utf-8')}")
            else:
                print(f"⚠️ API retourne un code inattendu: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Erreur lors du test API: {str(e)}")
        print(f"❌ Type d'erreur: {type(e).__name__}")

def main():
    """Fonction principale"""
    print("🚀 Diagnostic de la base de donnees MyXploit")
    print("=" * 50)
    
    # Test de connexion
    if test_database_connection():
        # Test de l'API
        test_api_endpoint()
    else:
        print("\n❌ Impossible de continuer sans connexion a la base")
        sys.exit(1)
    
    print("\n✅ Diagnostic termine")

if __name__ == '__main__':
    main()
