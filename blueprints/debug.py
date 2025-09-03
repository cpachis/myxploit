"""
Blueprint pour les routes de debug et utilitaires
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
import logging
from sqlalchemy import text

# Créer le blueprint
debug_bp = Blueprint('debug', __name__)

logger = logging.getLogger(__name__)

# Import des modèles (sera fait dynamiquement depuis app.py)
def get_models():
    """Récupère les modèles depuis l'application principale"""
    from app import db, Invitation
    return db, Invitation

@debug_bp.route('/')
@debug_bp.route('/debug')
def debug_page():
    """Page de debug pour diagnostiquer la base de données"""
    return render_template('debug.html')

@debug_bp.route('/database')
def debug_database():
    """Route de diagnostic pour la structure de la base de données"""
    db, Invitation = get_models()
    
    try:
        # Vérifier la structure des tables
        tables_info = {}
        
        # Vérifier les tables principales
        tables = ['users', 'clients', 'transports', 'vehicules', 'energies', 'invitations', 'transporteurs']
        
        for table in tables:
            try:
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                tables_info[table] = {
                    'exists': True,
                    'count': count
                }
            except Exception as e:
                tables_info[table] = {
                    'exists': False,
                    'error': str(e)
                }
        
        return jsonify({
            'success': True,
            'tables': tables_info,
            'database_url': 'Database configured'  # On ne montre pas l'URL complète pour la sécurité
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du diagnostic de la base: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@debug_bp.route('/invitations')
def debug_invitations():
    """Debug spécifique pour les invitations"""
    db, Invitation = get_models()
    
    try:
        invitations = Invitation.query.all()
        invitations_data = []
        
        for inv in invitations:
            invitations_data.append({
                'id': inv.id,
                'email': inv.email,
                'statut': inv.statut,
                'created_at': inv.created_at.isoformat() if inv.created_at else None,
                'token': inv.token[:20] + '...' if inv.token else None
            })
        
        return jsonify({
            'success': True,
            'invitations': invitations_data,
            'total': len(invitations_data)
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du debug des invitations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@debug_bp.route('/test-invitations')
def test_invitations_page():
    """Page de test pour diagnostiquer les problèmes d'invitations"""
    return render_template('test_invitations.html')

@debug_bp.route('/vehicules')
def debug_vehicules_page():
    """Page de debug spécifique pour les véhicules"""
    return render_template('debug_vehicules.html')

@debug_bp.route('/migrate')
def force_migration():
    """Route pour forcer la migration des colonnes manquantes"""
    db, Invitation = get_models()
    
    try:
        # Vérifier et ajouter les colonnes manquantes
        with db.engine.connect() as conn:
            # Vérifier si la colonne type_transport existe dans la table transports
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'transports' AND column_name = 'type_transport'
            """))
            
            if not result.fetchone():
                # Ajouter la colonne type_transport
                conn.execute(text("ALTER TABLE transports ADD COLUMN type_transport VARCHAR(50)"))
                conn.commit()
                logger.info("✅ Colonne type_transport ajoutée à la table transports")
            
            # Vérifier si la colonne niveau_calcul existe dans la table transports
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'transports' AND column_name = 'niveau_calcul'
            """))
            
            if not result.fetchone():
                # Ajouter la colonne niveau_calcul
                conn.execute(text("ALTER TABLE transports ADD COLUMN niveau_calcul VARCHAR(50)"))
                conn.commit()
                logger.info("✅ Colonne niveau_calcul ajoutée à la table transports")
        
        return jsonify({
            'success': True,
            'message': 'Migration terminée avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la migration: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@debug_bp.route('/health')
def health_check():
    """Point de contrôle de santé pour le déploiement"""
    db, Invitation = get_models()
    
    try:
        # Test de connexion à la base de données
        db.session.execute(text('SELECT 1'))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'version': '1.0.0'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500


