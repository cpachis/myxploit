#!/usr/bin/env python3
"""
Script de migration pour ajouter les colonnes manquantes à la base de données
"""

import os
import sys
from sqlalchemy import text, create_engine
from sqlalchemy.exc import OperationalError
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_url():
    """Récupère l'URL de la base de données depuis les variables d'environnement"""
    # En production (Render), utiliser DATABASE_URL
    if 'DATABASE_URL' in os.environ:
        db_url = os.environ['DATABASE_URL']
        # Remplacer postgres:// par postgresql:// pour SQLAlchemy 2.x
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url
    
    # En développement, utiliser la base SQLite locale
    return 'sqlite:///myxploit.db'

def migrate_database():
    """Exécute les migrations nécessaires"""
    try:
        # Connexion à la base de données
        db_url = get_database_url()
        logger.info(f"🔗 Connexion à la base de données: {db_url}")
        
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Vérifier si les colonnes existent déjà
            logger.info("🔍 Vérification de la structure de la table 'energies'...")
            
            # Pour PostgreSQL
            if 'postgresql' in db_url:
                # Vérifier si la colonne phase_amont existe
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'energies' 
                    AND column_name = 'phase_amont'
                """))
                
                if not result.fetchone():
                    logger.info("➕ Ajout de la colonne 'phase_amont'...")
                    conn.execute(text("ALTER TABLE energies ADD COLUMN phase_amont FLOAT DEFAULT 0.0"))
                    conn.commit()
                    logger.info("✅ Colonne 'phase_amont' ajoutée")
                else:
                    logger.info("✅ Colonne 'phase_amont' existe déjà")
                
                # Vérifier si la colonne phase_fonctionnement existe
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'energies' 
                    AND column_name = 'phase_fonctionnement'
                """))
                
                if not result.fetchone():
                    logger.info("➕ Ajout de la colonne 'phase_fonctionnement'...")
                    conn.execute(text("ALTER TABLE energies ADD COLUMN phase_fonctionnement FLOAT DEFAULT 0.0"))
                    conn.commit()
                    logger.info("✅ Colonne 'phase_fonctionnement' ajoutée")
                else:
                    logger.info("✅ Colonne 'phase_fonctionnement' existe déjà")
                
                # Vérifier si la colonne donnees_supplementaires existe
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'energies' 
                    AND column_name = 'donnees_supplementaires'
                """))
                
                if not result.fetchone():
                    logger.info("➕ Ajout de la colonne 'donnees_supplementaires'...")
                    conn.execute(text("ALTER TABLE energies ADD COLUMN donnees_supplementaires JSONB DEFAULT '{}'"))
                    conn.commit()
                    logger.info("✅ Colonne 'donnees_supplementaires' ajoutée")
                else:
                    logger.info("✅ Colonne 'donnees_supplementaires' existe déjà")
            
            # Pour SQLite
            else:
                logger.info("📱 Base SQLite détectée - pas de migration nécessaire")
            
            logger.info("🎉 Migration terminée avec succès !")
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la migration: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("🚀 Démarrage de la migration de la base de données...")
    
    if migrate_database():
        logger.info("✅ Migration réussie !")
        sys.exit(0)
    else:
        logger.error("❌ Migration échouée !")
        sys.exit(1)

