#!/usr/bin/env python3
"""
Script pour corriger automatiquement les imports circulaires dans les blueprints
"""

import os
import re

def fix_blueprint_imports(file_path):
    """Corrige les imports circulaires dans un fichier blueprint"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si le fichier a déjà été corrigé
    if 'def get_models():' in content and 'current_app' in content and 'from app import' not in content:
        print(f"✅ {file_path} déjà corrigé")
        return
    
    # Ajouter current_app à l'import Flask si nécessaire
    if 'from flask import' in content and 'current_app' not in content:
        content = re.sub(
            r'(from flask import [^\\n]+)',
            r'\1, current_app',
            content
        )
    
    # Ajouter la fonction get_models si elle n'existe pas
    if 'def get_models():' not in content:
        # Trouver la position après les imports
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('logger = logging.getLogger'):
                insert_pos = i + 1
                break
        
        # Insérer la fonction get_models
        get_models_code = '''
# Import des modèles (sera fait dynamiquement depuis current_app)
def get_models():
    """Récupère les modèles depuis l'application principale"""
    from flask_sqlalchemy import SQLAlchemy
    db = current_app.extensions['sqlalchemy'].db
    
    # Récupérer les modèles depuis les modèles enregistrés
    from models import create_models
    models = create_models(db)
    return db, models.get('Client'), models.get('Invitation'), models.get('Transport'), models.get('Vehicule'), models.get('Energie')
'''
        lines.insert(insert_pos, get_models_code)
        content = '\n'.join(lines)
    
    # Remplacer les imports depuis app
    patterns = [
        (r'from app import ([^\\n]+)', r'# Import des modèles depuis current_app\\n        db, Client, Invitation, Transport, Vehicule, Energie = get_models()'),
        (r'        from app import ([^\\n]+)', r'        db, Client, Invitation, Transport, Vehicule, Energie = get_models()'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Écrire le fichier corrigé
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {file_path} corrigé")

def main():
    """Corrige tous les blueprints"""
    blueprints_dir = 'blueprints'
    
    if not os.path.exists(blueprints_dir):
        print(f"❌ Dossier {blueprints_dir} non trouvé")
        return
    
    for filename in os.listdir(blueprints_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            file_path = os.path.join(blueprints_dir, filename)
            try:
                fix_blueprint_imports(file_path)
            except Exception as e:
                print(f"❌ Erreur lors de la correction de {file_path}: {e}")

if __name__ == '__main__':
    main()
