#!/usr/bin/env python3
"""
Script pour corriger les erreurs de frappe dans les imports Flask
"""

import os
import re

def fix_typos_in_file(file_path):
    """Corrige les erreurs de frappe dans un fichier"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corriger les erreurs de frappe communes
    corrections = [
        ('Bluepri, current_appnt', 'Blueprint, current_app'),
        ('from flask import Bluepri', 'from flask import Blueprint'),
        ('current_appnt', 'current_app'),
        ('Bluepri', 'Blueprint'),
        ('Blueprint, current_appnt', 'Blueprint, current_app'),
    ]
    
    original_content = content
    for old, new in corrections:
        content = content.replace(old, new)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ {file_path} corrigé")
        return True
    else:
        print(f"✅ {file_path} déjà correct")
        return False

def main():
    """Corrige tous les fichiers blueprints"""
    blueprints_dir = 'blueprints'
    
    if not os.path.exists(blueprints_dir):
        print(f"❌ Dossier {blueprints_dir} non trouvé")
        return
    
    corrected_files = 0
    for filename in os.listdir(blueprints_dir):
        if filename.endswith('.py'):
            file_path = os.path.join(blueprints_dir, filename)
            try:
                if fix_typos_in_file(file_path):
                    corrected_files += 1
            except Exception as e:
                print(f"❌ Erreur lors de la correction de {file_path}: {e}")
    
    print(f"\n✅ {corrected_files} fichiers corrigés")

if __name__ == '__main__':
    main()
