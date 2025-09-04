"""
Migration pour ajouter le champ vehicule_dedie à la table transports
"""

def upgrade():
    """Ajouter le champ vehicule_dedie"""
    # Cette migration sera exécutée manuellement via SQL
    pass

def downgrade():
    """Supprimer le champ vehicule_dedie"""
    # Cette migration sera exécutée manuellement via SQL
    pass

# SQL à exécuter manuellement :
# ALTER TABLE transports ADD COLUMN vehicule_dedie BOOLEAN DEFAULT FALSE;
