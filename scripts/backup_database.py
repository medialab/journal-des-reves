#!/usr/bin/env python
"""
Script de sauvegarde automatique de la base de données Django.

Utilise 'dumpdata' pour exporter en JSON compressé.
À exécuter régulièrement (cron, scheduler, etc.)
"""

import os
import sys
import gzip
import json
from datetime import datetime
from pathlib import Path

# Setup Django
# Ajouter le chemin backend au path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.chdir(backend_path)

import django
django.setup()

from django.core.management import call_command
from io import StringIO


def backup_database(backup_dir='backend/backups', compress=True):
    """
    Sauvegarde la base de données complète.
    
    Args:
        backup_dir: Dossier de destination des backups (relatif au projet)
        compress: Si True, compresse en .gz (recommandé)
    """
    # Gérer les chemins absolus et relatifs
    if os.path.isabs(backup_dir):
        backup_path = Path(backup_dir)
    else:
        # Chemin relatif au répertoire backend (après os.chdir)
        backup_path = Path(backup_dir)
    
    backup_path.mkdir(parents=True, exist_ok=True)
    
    # Nom du fichier avec timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'db_backup_{timestamp}.json'
    if compress:
        filename += '.gz'
    
    filepath = backup_path / filename
    
    print(f"🔄 Démarrage de la sauvegarde... ({datetime.now().isoformat()})")
    print(f"📁 Destination: {filepath}")
    
    try:
        # Exporter les données avec dumpdata
        output = StringIO()
        call_command(
            'dumpdata',
            '--all',
            '--indent=2',
            stdout=output,
            verbosity=1
        )
        
        data = output.getvalue()
        
        # Compresser si demandé
        if compress:
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                f.write(data)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(data)
        
        file_size = filepath.stat().st_size / (1024 * 1024)  # En MB
        print(f"✅ Sauvegarde réussie!")
        print(f"📊 Taille: {file_size:.2f} MB")
        print(f"💾 Fichier: {filepath}")
        
        # Nettoyer les vieilles sauvegardes (garder les 10 dernières)
        cleanup_old_backups(backup_path, keep=10)
        
        return filepath
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        sys.exit(1)


def backup_reves_only(backup_dir='backups'):
    """
    Sauvegarde uniquement l'app 'reves' (rêves + questionnaires + profils).
    """
    backup_path = Path(backup_dir)
    backup_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filepath = backup_path / f'reves_backup_{timestamp}.json.gz'
    
    print(f"🔄 Sauvegarde de l'app 'reves'...")
    
    try:
        output = StringIO()
        call_command(
            'dumpdata',
            'reves',
            '--indent=2',
            stdout=output,
            verbosity=1
        )
        
        data = output.getvalue()
        
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            f.write(data)
        
        print(f"✅ Sauvegarde de 'reves' réussie: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)


def cleanup_old_backups(backup_dir, keep=10):
    """
    Supprime les anciennes sauvegardes, en conservant les N dernières.
    """
    backup_path = Path(backup_dir)
    backups = sorted(backup_path.glob('db_backup_*.json*'), reverse=True)
    
    if len(backups) > keep:
        for old_backup in backups[keep:]:
            old_backup.unlink()
            print(f"🗑️  Supprimé: {old_backup.name}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Sauvegarder la base de données Django')
    parser.add_argument('--dir', default='backups', help='Dossier de destination (default: backups)')
    parser.add_argument('--no-compress', action='store_true', help='Ne pas compresser')
    parser.add_argument('--reves-only', action='store_true', help='Sauvegarder uniquement l\'app reves')
    parser.add_argument('--keep', type=int, default=10, help='Nombre de backups à conserver')
    
    args = parser.parse_args()
    
    if args.reves_only:
        backup_reves_only(args.dir)
    else:
        backup_database(args.dir, compress=not args.no_compress)
