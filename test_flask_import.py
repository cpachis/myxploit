#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier que Flask peut être importé correctement
"""

import sys
import os

# Ajouter le chemin de l'environnement virtuel
venv_path = os.path.join(os.path.dirname(__file__), 'venv', 'Lib', 'site-packages')
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

print("=== Test d'import Flask ===")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path[:3]}...")  # Afficher les 3 premiers chemins

try:
    import flask
    print(f"✅ Flask importé avec succès ! Version: {flask.__version__}")
    
    # Test d'autres imports Flask
    from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
    print("✅ Imports Flask spécifiques réussis !")
    
    # Test Flask-Login
    from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
    print("✅ Flask-Login importé avec succès !")
    
    print("\n🎉 Tous les imports Flask fonctionnent parfaitement !")
    
except ImportError as e:
    print(f"❌ Erreur d'import Flask: {e}")
    print(f"Vérifiez que Flask est installé dans: {venv_path}")
except Exception as e:
    print(f"❌ Erreur inattendue: {e}")

print("\n=== Fin du test ===")

