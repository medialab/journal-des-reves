#!/usr/bin/env python
"""
Script de restauration de sauvegarde Django.

Charge un fichier .json (.gz) créé avec backup_database.py
"""

import os
import sys
import gzip
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


def restore_backup(backup_file, interactive=True):
    """
    Restaure une sauvegarde.
    
    Args:
        backup_file: Chemin vers le fichier de sauvegarde (.json ou .json.gz)
        interactive: Demander confirmation avant de restaurer
    """
    filepath = Path(backup_file)
    
    if not filepath.exists():
        print(f"❌ Fichier non trouvé: {filepath}")
        sys.exit(1)
    
    # Vérifier si compressé
    is_compressed = filepath.suffix == '.gz'
    
    print(f"📂 Fichier: {filepath}")
    print(f"📊 Taille: {filepath.stat().st_size / (1024 * 1024):.2f} MB")
    print(f"📦 Compressé: {'Oui' if is_compressed else 'Non'}")
    
    if interactive:
        response = input("\n⚠️  ATTENTION: Cela va restaurer TOUTES les données! Continuez? (y/N) ")
        if response.lower() != 'y':
            print("❌ Restauration annulée")
            sys.exit(0)
    
    try:
        print(f"\n🔄 Restauration en cours... ({filepath.name})")
        
        # Si compressé, décompresser d'abord
        if is_compressed:
            print("📦 Décompression...")
            with gzip.open(filepath, 'rb') as f_in:
                temp_file = filepath.parent / f"{filepath.stem}_temp.json"
                with open(temp_file, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            call_command('loaddata', str(temp_file), verbosity=1)
            # Nettoyer le fichier temporaire
            temp_file.unlink()
        else:
            call_command('loaddata', str(filepath), verbosity=1)
        
        print("\n✅ Restauration réussie!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la restauration: {e}")
        sys.exit(1)


def list_backups(backup_dir='backend/backups'):
    """
    Liste les sauvegardes disponibles.
    """
    backup_path = Path(backup_dir)
    
    if not backup_path.exists():
        print(f"❌ Dossier {backup_dir} n'existe pas")
        return
    
    backups = sorted([f for f in backup_path.glob('*_backup_*.json*') if os.path.isfile(f)], reverse=True)
    
    if not backups:
        print(f"📭 Aucune sauvegarde trouvée dans {backup_dir}")
        return
    
    print(f"\n📦 Sauvegardes disponibles ({len(backups)}):\n")
    for i, backup in enumerate(backups, 1):
        size = backup.stat().st_size / (1024 * 1024)
        print(f"  {i}. {backup.name} ({size:.2f} MB)")
    
    print()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Restaurer une sauvegarde Django')
    subparsers = parser.add_subparsers(dest='command', help='Commandes')
    
    # Commande: restore
    restore_parser = subparsers.add_parser('restore', help='Restaurer une sauvegarde')
    restore_parser.add_argument('file', help='Chemin vers le fichier de sauvegarde')
    restore_parser.add_argument('--no-confirm', action='store_true', help='Ne pas demander confirmation')
    
    # Commande: list
    list_parser = subparsers.add_parser('list', help='Lister les sauvegardes')
    list_parser.add_argument('--dir', default='backups', help='Dossier de sauvegardes')
    
    args = parser.parse_args()
    
    if args.command == 'restore':
        restore_backup(args.file, interactive=not args.no_confirm)
    elif args.command == 'list':
        list_backups(args.dir)
    else:
        parser.print_help()
