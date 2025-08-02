#!/usr/bin/env python3
"""
Script pour migrer les vidéos existantes vers Bunny CDN
Ce script parcourt toutes les vidéos en base de données et les uploade vers Bunny CDN
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ajouter le répertoire parent au chemin Python pour pouvoir importer l'application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importer les modules de l'application
from src.models.database import db
from src.models.user import Video
from src import create_app
# Renommé pour clarifier que nous utilisons Bunny Stream API
from src.services.bunny_storage_service import bunny_storage_service as bunny_stream_service
import csv
from datetime import datetime

def migrate_videos_to_bunny_cdn(dry_run=False, force=False):
    """
    Migre toutes les vidéos vers Bunny Stream
    
    Args:
        dry_run: Si True, simule la migration sans faire d'upload réel
        force: Si True, force la remigration même si l'URL est déjà sur Bunny CDN
    """
    app = create_app()
    with app.app_context():
        # Récupérer toutes les vidéos
        videos = Video.query.all()
        logger.info(f"Trouvé {len(videos)} vidéos à migrer")
        
        # Base path pour les fichiers vidéo
        base_path = Path(os.environ.get('VIDEO_PATH', os.path.join(os.getcwd(), 'static', 'videos')))
        
        # Créer le dossier s'il n'existe pas
        if not base_path.exists():
            logger.warning(f"⚠️ Le dossier {base_path} n'existe pas. Création...")
            os.makedirs(base_path, exist_ok=True)
            
        # Initialiser le fichier de rapport CSV avec en-têtes si nécessaire
        report_path = "migration_report.csv"
        write_headers = not os.path.exists(report_path)
        if write_headers:
            with open(report_path, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["VideoID", "Titre", "URL Bunny", "Statut", "Horodatage"])
        
        migrated_count = 0
        failed_count = 0
        skipped_count = 0
        
        for video in videos:
            try:
                logger.info(f"📝 Traitement de la vidéo ID={video.id}, Titre={video.title}")
                
                # Vérifier si l'URL est déjà chez Bunny CDN
                if not force and video.file_url and ('bunnycdn.com' in video.file_url or 'bunny.net' in video.file_url):
                    logger.info(f"Vidéo {video.id} déjà sur Bunny CDN: {video.file_url}")
                    skipped_count += 1
                    
                    # Enregistrer le skip dans le rapport
                    with open("migration_report.csv", "a", newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([video.id, video.title, video.file_url, "SKIPPED - ALREADY ON CDN", datetime.now().isoformat()])
                    continue
                
                # Essayer plusieurs chemins possibles pour trouver le fichier local
                local_paths = []
                
                # 1. Chemin basé sur l'URL actuelle
                if video.file_url and video.file_url.startswith('/'):
                    filename = video.file_url.split('/')[-1]
                    local_paths.append(base_path / filename)
                
                # 2. Chemin basé sur l'ID (format standard) avec différentes extensions
                for ext in ['.mp4', '.mov', '.mkv', '.avi', '.webm']:
                    local_paths.append(base_path / f"video_{video.id}{ext}")
                
                # 3. Chemin avec titre formaté et différentes extensions
                if video.title:
                    safe_title = "".join(c for c in video.title if c.isalnum() or c in [' ', '_', '-']).strip()
                    safe_title = safe_title.replace(' ', '_').lower()
                    for ext in ['.mp4', '.mov', '.mkv', '.avi', '.webm']:
                        local_paths.append(base_path / f"{safe_title}_{video.id}{ext}")
                
                # Trouver le premier chemin qui existe
                local_path = None
                for path in local_paths:
                    if path.exists():
                        local_path = path
                        logger.info(f"Fichier trouvé: {local_path}")
                        break
                
                # Si aucun fichier n'est trouvé
                if not local_path:
                    paths_str = "\n - ".join([str(p) for p in local_paths])
                    logger.warning(f"⚠️ Aucun fichier trouvé pour la vidéo {video.id}. Chemins cherchés:\n - {paths_str}")
                    failed_count += 1
                    
                    # Enregistrer l'échec dans le rapport
                    with open("migration_report.csv", "a", newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([video.id, video.title, "", "FAILED - FILE NOT FOUND", datetime.now().isoformat()])
                    continue
                
                # Vérifier la taille du fichier pour détecter les fichiers corrompus ou vides
                file_size = local_path.stat().st_size
                if file_size < 1024 * 50:  # Moins de 50 Ko - probablement corrompu
                    logger.warning(f"⚠️ Fichier trop petit ou potentiellement corrompu: {local_path} ({file_size} octets)")
                    failed_count += 1
                    
                    # Enregistrer l'échec dans le rapport
                    with open("migration_report.csv", "a", newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([video.id, video.title, "", f"FAILED - FILE TOO SMALL ({file_size} bytes)", datetime.now().isoformat()])
                    continue
                
                # Nom du fichier sur Bunny CDN
                bunny_filename = f"video_{video.id}.mp4"
                
                if dry_run:
                    logger.info(f"[DRY RUN] Simulation d'upload: {local_path} -> Bunny Stream")
                    
                    # Enregistrer la simulation dans le rapport
                    with open("migration_report.csv", "a", newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([video.id, video.title, "", "DRY RUN - NO UPLOAD", datetime.now().isoformat()])
                    
                    migrated_count += 1
                    continue
                
                # Upload vers Bunny Stream avec la nouvelle fonction
                success, bunny_url = bunny_stream_service.upload_video_immediately(
                    video.id,
                    str(local_path),
                    f"Video {video.id}"  # Titre pour Bunny Stream
                )
                
                if success:
                    # Mettre à jour l'URL dans la base de données
                    video.file_url = bunny_url
                    # Ajouter un horodatage de migration
                    video.cdn_migrated_at = datetime.now()
                    db.session.commit()
                    logger.info(f"✅ Vidéo {video.id} migrée: {bunny_url}")
                    
                    # Écrire dans le rapport CSV
                    with open("migration_report.csv", "a", newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([video.id, video.title, bunny_url, "SUCCESS", datetime.now().isoformat()])
                    
                    migrated_count += 1
                else:
                    logger.error(f"❌ Échec de l'upload de la vidéo {video.id}")
                    
                    # Enregistrer l'échec dans le rapport
                    with open("migration_report.csv", "a", newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([video.id, video.title, "", "FAILED - UPLOAD ERROR", datetime.now().isoformat()])
                    
                    failed_count += 1
            
            except Exception as e:
                logger.error(f"❌ Erreur lors de la migration de la vidéo {video.id}: {str(e)}")
                
                # Enregistrer l'exception dans le rapport
                with open("migration_report.csv", "a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([video.id, video.title, "", f"FAILED - EXCEPTION: {str(e)}", datetime.now().isoformat()])
                
                failed_count += 1
        
        logger.info("=== Résumé de la migration ===")
        logger.info(f"Total des vidéos: {len(videos)}")
        logger.info(f"Migrées avec succès: {migrated_count}")
        logger.info(f"Déjà sur Bunny CDN: {skipped_count}")
        logger.info(f"Échecs: {failed_count}")
        logger.info(f"Rapport détaillé disponible dans: {os.path.abspath(report_path)}")
        
        return {
            'total': len(videos),
            'migrated': migrated_count,
            'skipped': skipped_count,
            'failed': failed_count,
            'report_path': os.path.abspath(report_path)
        }

def main():
    """Fonction principale avec parsing des arguments"""
    parser = argparse.ArgumentParser(description='Migrer les vidéos vers Bunny Stream')
    parser.add_argument('--dry-run', action='store_true', help='Simuler la migration sans faire d\'upload réel')
    parser.add_argument('--force', action='store_true', help='Forcer la remigration même si l\'URL est déjà sur Bunny CDN')
    parser.add_argument('--video-id', type=int, help='Migrer uniquement une vidéo spécifique par ID')
    parser.add_argument('--debug', action='store_true', help='Activer le mode debug pour plus de détails')
    parser.add_argument('--report', type=str, default="migration_report.csv", help='Chemin du fichier de rapport CSV')
    
    args = parser.parse_args()
    
    # Configurer le niveau de logging si debug est activé
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        for handler in logging.getLogger().handlers:
            handler.setLevel(logging.DEBUG)
    
    logger.info("=== Migration des vidéos vers Bunny Stream ===")
    logger.info(f"Mode: {'Simulation (dry run)' if args.dry_run else 'Production'}")
    logger.info(f"Force: {'Oui' if args.force else 'Non'}")
    logger.info(f"Rapport: {args.report}")
    
    # Initialiser le fichier de rapport CSV avec en-têtes si nécessaire
    report_path = args.report
    if not os.path.exists(report_path) or os.path.getsize(report_path) == 0:
        with open(report_path, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["VideoID", "Titre", "URL Bunny", "Statut", "Horodatage"])
    
    if args.video_id:
        logger.info(f"Migration d'une seule vidéo: ID = {args.video_id}")
        app = create_app()
        with app.app_context():
            video = Video.query.get(args.video_id)
            if not video:
                logger.error(f"❌ Vidéo ID={args.video_id} non trouvée dans la base de données")
                return 1
                
            base_path = Path(os.environ.get('VIDEO_PATH', os.path.join(os.getcwd(), 'static', 'videos')))
            local_path = base_path / f"video_{args.video_id}.mp4"
            
            # Vérifier d'autres extensions si le fichier n'existe pas
            if not local_path.exists():
                for ext in ['.mov', '.mkv', '.avi', '.webm']:
                    test_path = base_path / f"video_{args.video_id}{ext}"
                    if test_path.exists():
                        local_path = test_path
                        break
            
            if not local_path.exists():
                logger.error(f"❌ Fichier non trouvé: {local_path}")
                
                # Enregistrer l'échec dans le rapport
                with open(report_path, "a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([args.video_id, video.title if video else "Unknown", "", "FAILED - FILE NOT FOUND", datetime.now().isoformat()])
                
                return 1
                
            # Vérifier la taille du fichier
            file_size = local_path.stat().st_size
            if file_size < 1024 * 50:  # Moins de 50 Ko
                logger.warning(f"⚠️ Fichier trop petit ou potentiellement corrompu: {local_path} ({file_size} octets)")
                
                # Enregistrer l'avertissement dans le rapport
                with open(report_path, "a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([args.video_id, video.title if video else "Unknown", "", f"WARNING - FILE TOO SMALL ({file_size} bytes)", datetime.now().isoformat()])
                
                if not args.force:
                    logger.error("❌ Migration annulée. Utilisez --force pour ignorer cet avertissement.")
                    return 1
                
            if args.dry_run:
                logger.info(f"[DRY RUN] Simulation d'upload: {local_path}")
                return 0
                
            success, url = bunny_stream_service.upload_video_immediately(
                args.video_id,
                str(local_path),
                f"Video {args.video_id}"  # Titre pour Bunny Stream
            )
            
            if success:
                # Mettre à jour l'URL dans la base de données
                video.file_url = url
                video.cdn_migrated_at = datetime.now()
                db.session.commit()
                logger.info(f"✅ Vidéo {args.video_id} migrée: {url}")
                
                # Écrire dans le rapport CSV
                with open("migration_report.csv", "a", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([args.video_id, video.title, url, "SUCCESS", datetime.now().isoformat()])
            
            return 0 if success else 1
    else:
        # Migration complète
        result = migrate_videos_to_bunny_cdn(args.dry_run, args.force)
        return 0 if result['failed'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
