#!/usr/bin/env python3
"""
Script pour identifier les endpoints manquants
"""

import os
import re
from pathlib import Path

def find_missing_endpoints():
    """Trouver tous les endpoints utilisés dans les templates"""
    
    templates_dir = Path("templates")
    endpoints_used = set()
    
    # Patterns pour trouver les endpoints
    patterns = [
        r"url_for\('([^']+)'\)",  # url_for('endpoint')
        r"fetch\('([^']+)'\)",    # fetch('/api/endpoint')
        r"action=\"([^\"]+)\"",   # action="/endpoint"
        r"href=\"([^\"]+)\"",     # href="/endpoint"
    ]
    
    print("🔍 Recherche des endpoints dans les templates...")
    
    for template_file in templates_dir.rglob("*.html"):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if match.startswith('/'):
                        endpoints_used.add(match)
                    elif '.' in match:  # blueprint.endpoint
                        endpoints_used.add(match)
                    else:
                        endpoints_used.add(match)
                        
        except Exception as e:
            print(f"❌ Erreur lecture {template_file}: {e}")
    
    print(f"📋 {len(endpoints_used)} endpoints trouvés dans les templates")
    
    # Endpoints existants dans les blueprints
    existing_endpoints = set()
    blueprints_dir = Path("blueprints")
    
    for blueprint_file in blueprints_dir.glob("*.py"):
        if blueprint_file.name == "__init__.py":
            continue
            
        try:
            with open(blueprint_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Trouver les routes
            route_matches = re.findall(r"@\w+\.route\('([^']+)'", content)
            for route in route_matches:
                # Extraire le nom de la fonction
                func_matches = re.findall(r"@\w+\.route\('" + re.escape(route) + r"'.*?\ndef (\w+)", content, re.DOTALL)
                if func_matches:
                    func_name = func_matches[0]
                    # Deviner le nom du blueprint
                    blueprint_name = blueprint_file.stem
                    if blueprint_name.endswith('_bp'):
                        blueprint_name = blueprint_name[:-3]
                    existing_endpoints.add(f"{blueprint_name}.{func_name}")
                    
        except Exception as e:
            print(f"❌ Erreur lecture {blueprint_file}: {e}")
    
    print(f"📋 {len(existing_endpoints)} endpoints existants dans les blueprints")
    
    # Trouver les manquants
    missing_endpoints = set()
    
    for endpoint in endpoints_used:
        if endpoint.startswith('/'):
            # Endpoint absolu - vérifier s'il existe
            if not any(endpoint in existing for existing in existing_endpoints):
                missing_endpoints.add(endpoint)
        elif '.' in endpoint:
            # blueprint.endpoint - vérifier directement
            if endpoint not in existing_endpoints:
                missing_endpoints.add(endpoint)
        else:
            # endpoint simple - chercher dans tous les blueprints
            found = False
            for existing in existing_endpoints:
                if existing.endswith(f".{endpoint}"):
                    found = True
                    break
            if not found:
                missing_endpoints.add(endpoint)
    
    print(f"\n❌ {len(missing_endpoints)} endpoints manquants:")
    for endpoint in sorted(missing_endpoints):
        print(f"   - {endpoint}")
    
    return missing_endpoints

if __name__ == "__main__":
    print("🔍 Vérification des endpoints manquants...")
    print("=" * 60)
    missing = find_missing_endpoints()
    print("=" * 60)
    if missing:
        print("❌ Des endpoints manquent !")
    else:
        print("✅ Tous les endpoints existent !")
