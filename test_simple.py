#!/usr/bin/env python3
"""
Version de test très simple de l'application MyXploit
"""

from flask import Flask, jsonify, render_template
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_simple.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialisation de Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'

@app.route('/')
def index():
    """Page d'accueil de test"""
    return """
    <html>
    <head><title>Test MyXploit</title></head>
    <body>
        <h1>Test MyXploit - Application fonctionnelle</h1>
        <p>Si vous voyez cette page, l'application Flask fonctionne correctement.</p>
        <p><a href="/health">Test Health</a></p>
        <p><a href="/test">Test Route</a></p>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """Endpoint de santé"""
    return jsonify({
        'status': 'healthy',
        'message': 'Application de test fonctionnelle',
        'version': '1.0.0'
    })

@app.route('/test')
def test():
    """Route de test"""
    return jsonify({
        'message': 'Route de test fonctionnelle',
        'timestamp': '2025-09-10T10:00:00Z'
    })

if __name__ == '__main__':
    logger.info("Demarrage de l'application de test simple...")
    try:
        app.run(host='127.0.0.1', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Erreur au demarrage: {e}")
        raise