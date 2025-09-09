"""
Blueprint pour la gestion des transports par les transporteurs
Permet de voir les bons de transport, les assigner et gérer les états
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Créer le blueprint
transport_management_bp = Blueprint('transport_management', __name__)

# Import des modèles (sera fait dynamiquement depuis app.py)
def get_models():
    """Récupère les modèles depuis l'application Flask"""
    from models import create_models
    from flask import current_app
    models = create_models(current_app.extensions['sqlalchemy'].db)
    models['db'] = current_app.extensions['sqlalchemy'].db
    return models

@transport_management_bp.route('/transport-management')
@login_required
def dashboard():
    """Tableau de bord pour la gestion des transports"""
    try:
        models = get_models()
        TransportOrder = models['TransportOrder']
        Transport = models['Transport']
        db = models['db']
        
        # Les tables sont créées automatiquement par app.py
        
        # Récupérer tous les bons de transport
        orders = TransportOrder.query.order_by(TransportOrder.created_at.desc()).all()
        
        # Statistiques
        total_orders = len(orders)
        orders_en_attente = len([o for o in orders if o.statut == 'en_attente'])
        orders_assignes = len([o for o in orders if o.statut == 'assigne'])
        orders_en_cours = len([o for o in orders if o.statut == 'en_cours'])
        orders_livres = len([o for o in orders if o.statut == 'livre'])
        
        return render_template('transport_management/dashboard.html',
                             orders=orders,
                             total_orders=total_orders,
                             orders_en_attente=orders_en_attente,
                             orders_assignes=orders_assignes,
                             orders_en_cours=orders_en_cours,
                             orders_livres=orders_livres)
    
    except Exception as e:
        logger.error(f"Erreur dashboard gestion transports: {str(e)}")
        flash('Erreur lors du chargement du tableau de bord', 'error')
        return redirect(url_for('main.index'))

@transport_management_bp.route('/transport-management/assigner/<int:order_id>')
@login_required
def assigner_transport(order_id):
    """Page d'assignation d'un transport"""
    try:
        models = get_models()
        TransportOrder = models['TransportOrder']
        Transporteur = models['Transporteur']
        
        order = TransportOrder.query.get_or_404(order_id)
        transporteurs = Transporteur.query.filter_by(statut='actif').all()
        
        return render_template('transport_management/assigner.html', 
                             order=order, 
                             transporteurs=transporteurs)
    
    except Exception as e:
        logger.error(f"Erreur assignation transport: {str(e)}")
        flash('Erreur lors du chargement de l\'assignation', 'error')
        return redirect(url_for('transport_management.dashboard'))

@transport_management_bp.route('/transport-management/assigner/<int:order_id>', methods=['POST'])
@login_required
def assigner_transport_post(order_id):
    """Assigner un transport à un transporteur"""
    try:
        models = get_models()
        TransportOrder = models['TransportOrder']
        Transport = models['Transport']
        db = models['db']
        
        order = TransportOrder.query.get_or_404(order_id)
        transporteur_id = request.form.get('transporteur_id')
        
        if not transporteur_id:
            flash('Veuillez sélectionner un transporteur', 'error')
            return redirect(url_for('transport_management.assigner_transport', order_id=order_id))
        
        # Créer un transport à partir du bon de commande
        transport = Transport(
            ref=order.numero_bon,
            date=order.date_enlevement,
            lieu_collecte=order.expediteur_adresse,
            lieu_livraison=order.destinataire_adresse,
            poids_tonnes=order.poids_kg / 1000,  # Convertir kg en tonnes
            type_transport='direct',
            client=order.client_nom,
            transporteur_id=int(transporteur_id),
            description=f"Transport depuis {order.expediteur_nom} vers {order.destinataire_nom}"
        )
        
        db.session.add(transport)
        
        # Mettre à jour le bon de commande
        order.statut = 'assigne'
        order.transporteur_id = int(transporteur_id)
        order.assigne_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Transport {order.numero_bon} assigné avec succès !', 'success')
        return redirect(url_for('transport_management.dashboard'))
    
    except Exception as e:
        logger.error(f"Erreur assignation transport: {str(e)}")
        flash('Erreur lors de l\'assignation du transport', 'error')
        return redirect(url_for('transport_management.dashboard'))

@transport_management_bp.route('/transport-management/gerer/<int:order_id>')
@login_required
def gerer_transport(order_id):
    """Page de gestion d'un transport (mise à jour des états, émissions, etc.)"""
    try:
        models = get_models()
        TransportOrder = models['TransportOrder']
        Transport = models['Transport']
        Vehicule = models['Vehicule']
        Energie = models['Energie']
        
        order = TransportOrder.query.get_or_404(order_id)
        transport = Transport.query.filter_by(ref=order.numero_bon).first()
        
        # Récupérer les véhicules et énergies pour les calculs
        vehicules = Vehicule.query.filter_by(statut='actif').all()
        energies = Energie.query.filter_by(statut='actif').all()
        
        return render_template('transport_management/gerer.html', 
                             order=order, 
                             transport=transport,
                             vehicules=vehicules,
                             energies=energies)
    
    except Exception as e:
        logger.error(f"Erreur gestion transport: {str(e)}")
        flash('Erreur lors du chargement de la gestion du transport', 'error')
        return redirect(url_for('transport_management.dashboard'))

@transport_management_bp.route('/transport-management/gerer/<int:order_id>', methods=['POST'])
@login_required
def gerer_transport_post(order_id):
    """Mettre à jour les informations d'un transport"""
    try:
        models = get_models()
        TransportOrder = models['TransportOrder']
        Transport = models['Transport']
        db = models['db']
        
        order = TransportOrder.query.get_or_404(order_id)
        transport = Transport.query.filter_by(ref=order.numero_bon).first()
        
        if not transport:
            flash('Transport non trouvé', 'error')
            return redirect(url_for('transport_management.dashboard'))
        
        # Mettre à jour le statut
        nouveau_statut = request.form.get('statut')
        if nouveau_statut:
            order.statut = nouveau_statut
            if nouveau_statut == 'livre':
                order.livre_at = datetime.utcnow()
        
        # Mettre à jour les informations du transport
        transport.distance_km = float(request.form.get('distance_km', 0))
        transport.emis_kg = float(request.form.get('emis_kg', 0))
        transport.emis_tkm = float(request.form.get('emis_tkm', 0))
        
        # Mettre à jour les informations du bon de commande
        order.distance_km = transport.distance_km
        order.emis_kg = transport.emis_kg
        order.emis_tkm = transport.emis_tkm
        order.cout_transport = float(request.form.get('cout_transport', 0))
        
        db.session.commit()
        
        flash('Transport mis à jour avec succès !', 'success')
        return redirect(url_for('transport_management.gerer_transport', order_id=order_id))
    
    except Exception as e:
        logger.error(f"Erreur mise à jour transport: {str(e)}")
        flash('Erreur lors de la mise à jour du transport', 'error')
        return redirect(url_for('transport_management.dashboard'))

@transport_management_bp.route('/api/transport-management/orders')
@login_required
def api_orders():
    """API pour récupérer les bons de transport"""
    try:
        models = get_models()
        TransportOrder = models['TransportOrder']
        
        orders = TransportOrder.query.order_by(TransportOrder.created_at.desc()).all()
        
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'numero_bon': order.numero_bon,
                'expediteur_nom': order.expediteur_nom,
                'destinataire_nom': order.destinataire_nom,
                'poids_kg': order.poids_kg,
                'date_enlevement': order.date_enlevement.isoformat() if order.date_enlevement else None,
                'statut': order.statut,
                'created_at': order.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'orders': orders_data
        })
    
    except Exception as e:
        logger.error(f"Erreur API orders gestion: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
