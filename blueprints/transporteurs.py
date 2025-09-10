"""
Blueprint pour les routes liées aux transporteurs
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
import logging

# Créer le blueprint
transporteurs_bp = Blueprint('transporteurs', __name__)

logger = logging.getLogger(__name__)

# Import des modèles (sera fait dynamiquement depuis app.py)
def get_models():
    """Récupère les modèles depuis l'application principale"""
    from app import db, Transporteur
    return db, Transporteur

@transporteurs_bp.route('/')
@transporteurs_bp.route('/transporteurs')
def transporteurs():
    """Page de gestion des transporteurs (côté client)"""
    try:
        return render_template('transporteurs.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des transporteurs: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@transporteurs_bp.route('/api', methods=['GET', 'POST'])
def api_transporteurs():
    """API pour gérer les transporteurs"""
    db, Transporteur = get_models()
    
    if request.method == 'GET':
        try:
            transporteurs = Transporteur.query.all()
            transporteurs_data = []
            
            for transporteur in transporteurs:
                transporteurs_data.append({
                    'id': transporteur.id,
                    'nom': transporteur.nom,
                    'email': transporteur.email,
                    'telephone': transporteur.telephone,
                    'adresse': transporteur.adresse,
                    'siret': transporteur.siret,
                    'statut': transporteur.statut,
                    'created_at': transporteur.created_at.strftime('%Y-%m-%d %H:%M:%S') if transporteur.created_at else None
                })
            
            return jsonify({
                'success': True,
                'transporteurs': transporteurs_data
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des transporteurs: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validation des données
            if not data.get('nom') or not data.get('email'):
                return jsonify({'success': False, 'error': 'Nom et email sont obligatoires'}), 400
            
            # Vérifier si l'email existe déjà
            if Transporteur.query.filter_by(email=data['email']).first():
                return jsonify({'success': False, 'error': 'Un transporteur avec cet email existe déjà'}), 400
            
            # Créer le nouveau transporteur
            nouveau_transporteur = Transporteur(
                nom=data.get('nom'),
                email=data.get('email'),
                telephone=data.get('telephone'),
                adresse=data.get('adresse'),
                siret=data.get('siret'),
                statut='actif'
            )
            
            db.session.add(nouveau_transporteur)
            db.session.commit()
            
            logger.info(f"✅ Nouveau transporteur créé: {nouveau_transporteur.nom} ({nouveau_transporteur.email})")
            
            return jsonify({
                'success': True,
                'message': 'Transporteur créé avec succès',
                'transporteur': {
                    'id': nouveau_transporteur.id,
                    'nom': nouveau_transporteur.nom,
                    'email': nouveau_transporteur.email,
                    'telephone': nouveau_transporteur.telephone,
                    'adresse': nouveau_transporteur.adresse,
                    'statut': nouveau_transporteur.statut
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du transporteur: {str(e)}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

@transporteurs_bp.route('/api/<int:transporteur_id>', methods=['PUT', 'DELETE'])
def api_transporteur_individual(transporteur_id):
    """API pour modifier ou supprimer un transporteur spécifique"""
    db, Transporteur = get_models()
    
    try:
        transporteur = Transporteur.query.get(transporteur_id)
        if not transporteur:
            return jsonify({'success': False, 'error': 'Transporteur non trouvé'}), 404
        
        if request.method == 'PUT':
            data = request.get_json()
            
            # Mettre à jour les champs
            if data.get('nom'):
                transporteur.nom = data['nom']
            if data.get('email'):
                # Vérifier si l'email existe déjà pour un autre transporteur
                existing_transporteur = Transporteur.query.filter_by(email=data['email']).first()
                if existing_transporteur and existing_transporteur.id != transporteur_id:
                    return jsonify({'success': False, 'error': 'Un autre transporteur utilise déjà cet email'}), 400
                transporteur.email = data['email']
            if data.get('telephone'):
                transporteur.telephone = data['telephone']
            if data.get('adresse'):
                transporteur.adresse = data['adresse']
            if data.get('siret'):
                transporteur.siret = data['siret']
            if data.get('statut'):
                transporteur.statut = data['statut']
            
            transporteur.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"✅ Transporteur modifié: {transporteur.nom}")
            
            return jsonify({
                'success': True,
                'message': 'Transporteur modifié avec succès',
                'transporteur': {
                    'id': transporteur.id,
                    'nom': transporteur.nom,
                    'email': transporteur.email,
                    'telephone': transporteur.telephone,
                    'adresse': transporteur.adresse,
                    'statut': transporteur.statut
                }
            })
            
        elif request.method == 'DELETE':
            nom_transporteur = transporteur.nom
            db.session.delete(transporteur)
            db.session.commit()
            
            logger.info(f"✅ Transporteur supprimé: {nom_transporteur} (ID: {transporteur_id})")
            
            return jsonify({
                'success': True,
                'message': 'Transporteur supprimé avec succès'
            })
            
    except Exception as e:
        logger.error(f"Erreur lors de la gestion du transporteur {transporteur_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@transporteurs_bp.route('/api/invite', methods=['POST'])
def invite_transporteur():
    """API pour inviter un transporteur par email"""
    db, Transporteur = get_models()
    
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('nom'):
            return jsonify({'success': False, 'error': 'Email et nom sont obligatoires'}), 400
        
        # Vérifier si le transporteur existe déjà
        existing_transporteur = Transporteur.query.filter_by(email=data['email']).first()
        if existing_transporteur:
            return jsonify({'success': False, 'error': 'Un transporteur avec cet email existe déjà'}), 400
        
        # Créer le transporteur avec statut "en_attente"
        nouveau_transporteur = Transporteur(
            nom=data.get('nom'),
            email=data.get('email'),
            telephone=data.get('telephone'),
            adresse=data.get('adresse'),
            siret=data.get('siret'),
            statut='en_attente'
        )
        
        db.session.add(nouveau_transporteur)
        db.session.commit()
        
        logger.info(f"✅ Transporteur invité: {nouveau_transporteur.nom} ({nouveau_transporteur.email})")
        
        return jsonify({
            'success': True,
            'message': 'Invitation envoyée avec succès',
            'transporteur': {
                'id': nouveau_transporteur.id,
                'nom': nouveau_transporteur.nom,
                'email': nouveau_transporteur.email,
                'statut': nouveau_transporteur.statut
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de l'invitation du transporteur: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500





