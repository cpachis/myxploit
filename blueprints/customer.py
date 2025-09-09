"""
Blueprint pour l'interface client "My Customer Xploit"
Permet aux clients de créer des bons de transport
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, make_response
from flask_login import login_required, current_user
import logging
import uuid
import io
import base64
from datetime import datetime, date

# Import optionnel de qrcode
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    print("⚠️ Module qrcode non disponible. Les QR codes ne seront pas générés.")

logger = logging.getLogger(__name__)

# Créer le blueprint
customer_bp = Blueprint('customer', __name__)

# Import des modèles (sera fait dynamiquement depuis app.py)
def get_models():
    """Récupère les modèles depuis l'application Flask"""
    from models import create_models
    from app import db  # Import direct depuis app.py
    models = create_models(db)
    models['db'] = db
    return models

@customer_bp.route('/customer')
@login_required
def dashboard():
    """Tableau de bord client"""
    try:
        models = get_models()
        TransportOrder = models['TransportOrder']
        db = models['db']
        
        # Les tables sont créées automatiquement par app.py
        
        # Récupérer les bons de transport du client
        orders = TransportOrder.query.filter_by(client_id=current_user.id).order_by(TransportOrder.created_at.desc()).all()
        
        # Statistiques
        total_orders = len(orders)
        orders_en_attente = len([o for o in orders if o.statut == 'en_attente'])
        orders_assignes = len([o for o in orders if o.statut == 'assigne'])
        orders_livres = len([o for o in orders if o.statut == 'livre'])
        
        return render_template('customer/dashboard.html',
                             orders=orders,
                             total_orders=total_orders,
                             orders_en_attente=orders_en_attente,
                             orders_assignes=orders_assignes,
                             orders_livres=orders_livres)
    
    except Exception as e:
        logger.error(f"Erreur dashboard client: {str(e)}")
        flash('Erreur lors du chargement du tableau de bord', 'error')
        return redirect(url_for('main.index'))

@customer_bp.route('/customer/nouveau-bon')
@login_required
def nouveau_bon():
    """Formulaire de création d'un nouveau bon de transport"""
    return render_template('customer/nouveau_bon.html')

@customer_bp.route('/customer/nouveau-bon', methods=['POST'])
@login_required
def creer_bon():
    """Créer un nouveau bon de transport"""
    try:
        models = get_models()
        TransportOrder = models['TransportOrder']
        db = models['db']
        
        # Les tables sont créées automatiquement par app.py
        
        # Générer un numéro de bon unique
        numero_bon = f"TX{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        
        # Utiliser le code-barre fourni par le formulaire ou en générer un
        code_barre = request.form.get('code_barre')
        if not code_barre:
            code_barre = f"TX{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:6].upper()}"
        
        # Créer le bon de transport
        order = TransportOrder(
            numero_bon=numero_bon,
            code_barre=code_barre,
            client_id=current_user.id,
            client_nom=current_user.nom,
            client_email=current_user.email,
            client_telephone=current_user.telephone,
            client_adresse=current_user.adresse,
            
            # Informations expéditeur
            expediteur_nom=request.form.get('expediteur_nom'),
            expediteur_adresse=request.form.get('expediteur_adresse'),
            expediteur_contact=request.form.get('expediteur_contact'),
            expediteur_telephone=request.form.get('expediteur_telephone'),
            
            # Informations destinataire
            destinataire_nom=request.form.get('destinataire_nom'),
            destinataire_adresse=request.form.get('destinataire_adresse'),
            destinataire_contact=request.form.get('destinataire_contact'),
            destinataire_telephone=request.form.get('destinataire_telephone'),
            
            # Informations colis
            type_colis=request.form.get('type_colis'),
            nombre_colis=int(request.form.get('nombre_colis', 1)),
            poids_kg=float(request.form.get('poids_kg')),
            dimensions=request.form.get('dimensions'),
            description_colis=request.form.get('description_colis'),
            valeur_colis=float(request.form.get('valeur_colis', 0)) if request.form.get('valeur_colis') else None,
            
            # Informations transport
            date_enlevement=datetime.strptime(request.form.get('date_enlevement'), '%Y-%m-%d').date(),
            date_livraison_souhaitee=datetime.strptime(request.form.get('date_livraison_souhaitee'), '%Y-%m-%d').date() if request.form.get('date_livraison_souhaitee') else None,
            instructions_speciales=request.form.get('instructions_speciales'),
            urgence=request.form.get('urgence', 'normal')
        )
        
        db.session.add(order)
        db.session.commit()
        
        flash(f'Bon de transport {numero_bon} créé avec succès !', 'success')
        return redirect(url_for('customer.voir_bon', id=order.id))
    
    except Exception as e:
        logger.error(f"Erreur création bon: {str(e)}")
        flash('Erreur lors de la création du bon de transport', 'error')
        return redirect(url_for('customer.nouveau_bon'))

@customer_bp.route('/customer/bon/<int:id>')
@login_required
def voir_bon(id):
    """Voir un bon de transport"""
    try:
        models = get_models()
        TransportOrder = models['TransportOrder']
        
        order = TransportOrder.query.filter_by(id=id, client_id=current_user.id).first()
        if not order:
            flash('Bon de transport non trouvé', 'error')
            return redirect(url_for('customer.dashboard'))
        
        return render_template('customer/voir_bon.html', order=order)
    
    except Exception as e:
        logger.error(f"Erreur affichage bon: {str(e)}")
        flash('Erreur lors du chargement du bon', 'error')
        return redirect(url_for('customer.dashboard'))

@customer_bp.route('/customer/bon/<int:id>/imprimer')
@login_required
def imprimer_bon(id):
    """Imprimer un bon de transport en A4"""
    try:
        models = get_models()
        TransportOrder = models['TransportOrder']
        
        order = TransportOrder.query.filter_by(id=id, client_id=current_user.id).first()
        if not order:
            flash('Bon de transport non trouvé', 'error')
            return redirect(url_for('customer.dashboard'))
        
        # Générer le QR code si disponible
        qr_data = None
        if QRCODE_AVAILABLE:
            try:
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(f"BON:{order.code_barre}")
                qr.make(fit=True)
                
                qr_img = qr.make_image(fill_color="black", back_color="white")
                
                # Convertir en base64 pour l'affichage
                buffer = io.BytesIO()
                qr_img.save(buffer, format='PNG')
                qr_data = base64.b64encode(buffer.getvalue()).decode()
            except Exception as e:
                logger.warning(f"Erreur génération QR code: {str(e)}")
                qr_data = None
        
        return render_template('customer/imprimer_bon.html', order=order, qr_data=qr_data)
    
    except Exception as e:
        logger.error(f"Erreur impression bon: {str(e)}")
        flash('Erreur lors de l\'impression du bon', 'error')
        return redirect(url_for('customer.dashboard'))

@customer_bp.route('/customer/bon/<int:id>/pdf')
@login_required
def telecharger_pdf(id):
    """Télécharger le bon de transport en PDF"""
    try:
        models = get_models()
        TransportOrder = models['TransportOrder']
        
        order = TransportOrder.query.filter_by(id=id, client_id=current_user.id).first()
        if not order:
            flash('Bon de transport non trouvé', 'error')
            return redirect(url_for('customer.dashboard'))
        
        # Pour l'instant, rediriger vers la page d'impression
        # TODO: Implémenter la génération PDF avec WeasyPrint ou ReportLab
        return redirect(url_for('customer.imprimer_bon', id=id))
    
    except Exception as e:
        logger.error(f"Erreur téléchargement PDF: {str(e)}")
        flash('Erreur lors du téléchargement du PDF', 'error')
        return redirect(url_for('customer.dashboard'))

@customer_bp.route('/api/customer/orders')
@login_required
def api_orders():
    """API pour récupérer les bons de transport du client"""
    try:
        models = get_models()
        TransportOrder = models['TransportOrder']
        
        orders = TransportOrder.query.filter_by(client_id=current_user.id).order_by(TransportOrder.created_at.desc()).all()
        
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
        logger.error(f"Erreur API orders: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
