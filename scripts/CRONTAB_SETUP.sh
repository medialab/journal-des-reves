#!/bin/bash
#
# Crontab configuration pour sauvegardes automatiques
# 
# Copier et coller la ligne appropriée dans: crontab -e
#

# ========== SAUVEGARDES QUOTIDIENNES ==========
# Chaque jour à 02:00 (2 heures du matin)
0 2 * * * cd /home/maudyaiche/dev/site_reves && source mon_env/bin/activate && python scripts/backup_database.py --dir backups >> logs/backup.log 2>&1

# Chaque jour à 14:00 (2 heures de l'après-midi)
0 14 * * * cd /home/maudyaiche/dev/site_reves && source mon_env/bin/activate && python scripts/backup_database.py --dir backups >> logs/backup.log 2>&1


# ========== SAUVEGARDES HEBDOMADAIRES COMPLÈTES ==========
# Chaque lundi à 03:00 (backup complet)
0 3 * * 1 cd /home/maudyaiche/dev/site_reves && source mon_env/bin/activate && python scripts/backup_database.py --dir backups/weekly >> logs/backup.log 2>&1


# ========== EXEMPLE NOTES ==========
# Format cron: minute heure jour_du_mois mois jour_de_la_semaine
# 
# Jour de la semaine: 0=Dimanche, 1=Lundi ... 6=Samedi
# Exemples:
#   0 */6 * * * = Toutes les 6 heures
#   0 0 1 * *   = Le 1er de chaque mois à minuit
#   0 0 * * 0   = Chaque dimanche à minuit


# ========== INSTRUCTIONS D'INSTALLATION ==========
# 1. Ouvrir crontab:
#    crontab -e
#
# 2. Ajouter les lignes de sauvegarde ci-dessus
#
# 3. Vérifier l'installation:
#    crontab -l
#
# 4. Vérifier les logs:
#    tail -f logs/backup.log
