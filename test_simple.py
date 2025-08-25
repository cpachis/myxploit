# Test simple d'import Flask
try:
    import flask
    print("✅ Flask importé avec succès!")
    print(f"Version: {flask.__version__}")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Vérifiez que l'environnement virtuel est activé")

