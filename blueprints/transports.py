"""
Blueprint pour les routes liées aux transports
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
import logging
import os
import csv
from io import StringIO

# Créer le blueprint
transports_bp = Blueprint('transports', __name__)

logger = logging.getLogger(__name__)

# Import des modèles (sera fait dynamiquement depuis app.py)
def get_models():
    """Récupère les modèles depuis l'application principale"""
    from app import db, Transport, Vehicule, Energie
    return db, Transport, Vehicule, Energie

@transports_bp.route('/')
@transports_bp.route('/transports')
def transports():
    """Liste des transports (ancienne version)"""
    try:
        db, Transport, Vehicule, Energie = get_models()
        
        # Récupérer tous les transports
        transports = Transport.query.all()
        
        # Récupérer les véhicules et énergies pour l'affichage
        vehicules = {v.id: v for v in Vehicule.query.all()}
        energies = {e.id: e for e in Energie.query.all()}
        
        logger.info(f"Affichage de {len(transports)} transports")
        
        return render_template('liste_transports.html', 
                            transports=transports,
                            vehicules=vehicules,
                            energies=energies,
                            clients={})
                        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des transports: {str(e)}")
        # Rediriger vers la nouvelle page si erreur avec l'ancienne
        return redirect(url_for('transports.mes_transports'))

@transports_bp.route('/mes_transports')
def mes_transports():
    """Page de gestion des transports"""
    try:
        return render_template('mes_transports.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page mes_transports: {str(e)}")
        flash('Erreur lors du chargement de la page', 'error')
        return redirect(url_for('transports.mes_transports'))

@transports_bp.route('/nouveau_transport')
def nouveau_transport():
    """Page de sélection du mode de création de transport"""
    try:
        return render_template('nouveau_transport.html')
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du choix de création: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@transports_bp.route('/transport')
@transports_bp.route('/transport/<int:transport_id>')
def transport(transport_id=None):
    """Page de création/modification d'un transport"""
    try:
        db, Transport, Vehicule, Energie = get_models()
        
        transport = None
        if transport_id:
            transport = Transport.query.get_or_404(transport_id)
        
        # Récupérer les véhicules et énergies pour le formulaire
        vehicules = Vehicule.query.all()
        energies = Energie.query.all()
        
        return render_template('transport.html', 
                            transport=transport,
                            vehicules=vehicules,
                            energies=energies)
                            
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du transport: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@transports_bp.route('/<int:transport_id>')
def transport_detail(transport_id):
    """Page de détail d'un transport"""
    try:
        return render_template('transport_detail.html', transport_id=transport_id)
    except Exception as e:
        logger.error(f"Erreur lors du chargement du détail du transport {transport_id}: {str(e)}")
        flash('Erreur lors du chargement du transport', 'error')
        return redirect(url_for('transports.mes_transports'))

@transports_bp.route('/import_csv')
def import_csv():
    """Page d'import CSV des transports"""
    try:
        return render_template('import_csv.html')
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page import CSV: {str(e)}")
        flash('Erreur lors du chargement de la page', 'error')
        return redirect(url_for('transports.import_csv'))

@transports_bp.route('/import_transports_csv', methods=['POST'])
def import_transports_csv():
    """Import de transports depuis un fichier CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Aucun fichier sélectionné'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Aucun fichier sélectionné'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Le fichier doit être au format CSV'}), 400
        
        db, Transport, Vehicule, Energie = get_models()
        
        # Décoder le contenu du fichier
        content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(StringIO(content))
        
        transports_crees = 0
        erreurs = 0
        resultats = []
        
        for row in csv_reader:
            try:
                # Validation des données obligatoires
                if not row.get('ref') or not row.get('type_transport') or not row.get('niveau_calcul'):
                    erreurs += 1
                    resultats.append({'ref': row.get('ref', 'N/A'), 'error': 'Données obligatoires manquantes'})
                    continue
                
                # Vérifier si la référence existe déjà
                if Transport.query.filter_by(ref=row['ref']).first():
                    erreurs += 1
                    resultats.append({'ref': row['ref'], 'error': 'Référence déjà existante'})
                    continue
                
                # Créer le transport
                nouveau_transport = Transport(
                    ref=row['ref'],
                    type_transport=row['type_transport'],
                    niveau_calcul=row['niveau_calcul'],
                    type_vehicule=row.get('type_vehicule'),
                    energie=row.get('energie'),
                    conso_vehicule=float(row['conso_vehicule']) if row.get('conso_vehicule') else None,
                    poids_tonnes=float(row['poids_tonnes']) if row.get('poids_tonnes') else None,
                    distance_km=float(row['distance_km']) if row.get('distance_km') else None
                )
                
                db.session.add(nouveau_transport)
                transports_crees += 1
                resultats.append({'ref': row['ref'], 'success': True})
                
            except Exception as e:
                erreurs += 1
                resultats.append({'ref': row.get('ref', 'N/A'), 'error': str(e)})
        
        # Sauvegarder tous les transports créés
        try:
            db.session.commit()
            logger.info(f"✅ Import CSV terminé: {transports_crees} créés, {erreurs} erreurs")
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erreur lors de la sauvegarde: {str(e)}")
            return jsonify({'success': False, 'error': f'Erreur lors de la sauvegarde: {str(e)}'}), 500
        
        return jsonify({
            'success': True,
            'message': f'Import terminé: {transports_crees} créés, {erreurs} erreurs',
            'transports_crees': transports_crees,
            'erreurs': erreurs,
            'resultats': resultats
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'import CSV: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
