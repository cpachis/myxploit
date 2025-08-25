#!/usr/bin/env python3
"""
Script de démarrage pour l'application MyXploit
"""

from app import app

if __name__ == "__main__":
    print("🚀 Démarrage de MyXploit...")
    print("📱 Application accessible sur: http://localhost:5000")
    print("🔑 Identifiants par défaut dans data/users.json")
    print("⏹️  Arrêter avec Ctrl+C")
    print("-" * 50)
    
    app.run(
        host="0.0.0.0", 
        port=5000, 
        debug=True
    ) 