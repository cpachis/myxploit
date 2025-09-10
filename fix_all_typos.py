#!/usr/bin/env python3
"""
Script pour corriger toutes les erreurs de frappe dans les blueprints
"""

import os
import re

def fix_file(file_path):
    """Corrige les erreurs de frappe dans un fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Corriger les erreurs de frappe
        content = content.replace('Blueprintntntntnt', 'Blueprint')
        content = content.replace('current_appnt', 'current_app')
        content = content.replace('Bluepri', 'Blueprint')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {file_path} corrigé")
        return True
    except Exception as e:
        print(f"❌ Erreur {file_path}: {e}")
        return False

def main():
    """Corrige tous les fichiers blueprints"""
    blueprints_dir = 'blueprints'
    
    if not os.path.exists(blueprints_dir):
        print(f"❌ Dossier {blueprints_dir} non trouvé")
        return
    
    corrected = 0
    for filename in os.listdir(blueprints_dir):
        if filename.endswith('.py'):
            file_path = os.path.join(blueprints_dir, filename)
            if fix_file(file_path):
                corrected += 1
    
    print(f"\n✅ {corrected} fichiers corrigés")

if __name__ == '__main__':
    main()
