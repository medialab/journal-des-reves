#!/usr/bin/env python
"""
Script de vérification du système de backup.
Affiche l'état du système et les statistiques.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Setup Django
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.chdir(backend_path)

import django
django.setup()

from django.db import connection


def get_table_stats():
    """Retourne les statistiques des tables principales."""
    with connection.cursor() as cursor:
        tables = [
            ('reves_reve', 'Rêves'),
            ('reves_profil', 'Profils'),
            ('reves_questionnaire', 'Questionnaires'),
            ('reves_reveemotion', 'Émotions'),
            ('reves_tag', 'Tags'),
        ]
        
        stats = {}
        for table, label in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[label] = count
            except Exception as e:
                stats[label] = 0  # Table n'existe pas ou erreur
        
        return stats


def check_backups():
    """Vérifie les sauvegardes disponibles."""
    # Après os.chdir(backend_path), on est dans le répertoire backend
    # donc le chemin relatif doit être juste 'backups'
    backup_path = Path('backups')
    
    if not backup_path.exists():
        return []
    
    backups = list(backup_path.glob('*_backup_*.json*'))
    backups.sort(reverse=True)
    
    return backups


def main():
    print("\n" + "=" * 60)
    print("🔍 SYSTÈME DE BACKUP - VÉRIFICATION".center(60))
    print("=" * 60 + "\n")
    
    # 1. État de la base de données
    print("📊 État de la base de données:")
    print("-" * 60)
    stats = get_table_stats()
    total_records = sum(stats.values())
    
    for label, count in stats.items():
        status = "✅" if count > 0 else "⚠️ "
        print(f"{status} {label:20} : {count:6} enregistrement(s)")
    
    print(f"\n📈 Total: {total_records} enregistrement(s)")
    
    # 2. Sauvegardes disponibles
    print("\n📦 Sauvegardes disponibles:")
    print("-" * 60)
    backups = check_backups()
    
    if not backups:
        print("❌ Aucune sauvegarde trouvée dans 'backend/backups'")
    else:
        total_size = 0
        for i, backup in enumerate(backups, 1):
            size = backup.stat().st_size / (1024 * 1024)
            total_size += size
            mod_time = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"{i}. {backup.name:50} {size:8.3f} MB ({mod_time.strftime('%Y-%m-%d %H:%M')})")
        
        print(f"\n💾 Espace utilisé: {total_size:.2f} MB")
        print(f"📁 Nombre de backups: {len(backups)}")
    
    # 3. Configuration recommandée
    print("\n⚙️  Configuration recommandée:")
    print("-" * 60)
    print("📌 Pour installer les sauvegardes automatiques:")
    print("   crontab -e")
    print("")
    print("   # Sauvegarde complète à 02:00")
    print("   0 2 * * * cd /home/maudyaiche/dev/site_reves && source mon_env/bin/activate && python scripts/backup_database.py >> logs/backup.log 2>&1")
    print("")
    print("   # Sauvegarde rêves seuls à 14:00 (rapide)")
    print("   0 14 * * * cd /home/maudyaiche/dev/site_reves && source mon_env/bin/activate && python scripts/backup_database.py --reves-only >> logs/backup.log 2>&1")
    
    # 4. Commandes utiles
    print("\n🚀 Commandes utiles:")
    print("-" * 60)
    print("# Créer un backup")
    print("python scripts/backup_database.py")
    print("")
    print("# Lister les backups")
    print("python scripts/restore_backup.py list")
    print("")
    print("# Restaurer un backup (données complètes)")
    print("python scripts/restore_backup.py restore backend/backups/db_backup_2026-04-01_18-54-04.json.gz")
    print("")
    print("# Restaurer un backup rêves seuls")
    print("python scripts/restore_backup.py restore backend/backups/reves_backup_2026-04-01_18-54-14.json.gz")
    
    print("\n" + "=" * 60 + "\n")


if __name__ == '__main__':
    main()
