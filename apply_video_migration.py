#!/usr/bin/env python3
"""
Migration pour ajouter les champs de gestion vidéo
"""

from src.main import create_app
from src.models.database import db
from src.models.user import User, Video, Court, Club
import logging

def apply_video_system_migration():
    """Appliquer la migration pour le système vidéo"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Application de la migration pour le système vidéo...")
            
            # Ajouter les nouvelles colonnes à Court si elles n'existent pas
            print("📝 Ajout des champs d'enregistrement aux terrains...")
            
            # Utiliser raw SQL pour ajouter les colonnes si elles n'existent pas
            db.engine.execute("""
                ALTER TABLE court 
                ADD COLUMN IF NOT EXISTS recording_session_id VARCHAR(100);
            """)
            
            # Ajouter le champ file_size à Video si il n'existe pas
            print("📝 Ajout du champ file_size aux vidéos...")
            
            db.engine.execute("""
                ALTER TABLE video 
                ADD COLUMN IF NOT EXISTS file_size INTEGER;
            """)
            
            # Mettre à jour les URLs des vidéos existantes pour utiliser le nouveau format
            print("🔄 Mise à jour des URLs des vidéos existantes...")
            
            videos = Video.query.all()
            for video in videos:
                if video.file_url and not video.file_url.startswith('/api/videos/'):
                    # Convertir l'ancienne URL vers le nouveau format
                    if video.file_url.startswith('/videos/'):
                        filename = video.file_url.replace('/videos/', '')
                        video.file_url = f'/api/videos/stream/{filename}'
                    
                    # Ajouter une thumbnail URL si elle n'existe pas
                    if not video.thumbnail_url:
                        video.thumbnail_url = f'/api/videos/thumbnail/{video.id}'
                        
                    # Estimer une taille de fichier si elle n'existe pas
                    if not video.file_size:
                        # Estimation basée sur la durée (approximation)
                        if video.duration:
                            # ~10MB par minute de vidéo (estimation)
                            video.file_size = video.duration * 60 * 10 * 1024 * 1024
            
            # S'assurer que tous les terrains ont une camera_url
            print("📹 Configuration des URLs de caméra pour les terrains...")
            
            courts = Court.query.all()
            for court in courts:
                if not court.camera_url:
                    # URL de simulation pour les tests
                    court.camera_url = f"http://localhost:5000/api/courts/{court.id}/camera_stream"
            
            # Commit des changements
            db.session.commit()
            print("✅ Migration du système vidéo appliquée avec succès!")
            
            # Afficher un résumé
            total_videos = Video.query.count()
            total_courts = Court.query.count()
            
            print(f"📊 Résumé:")
            print(f"   - {total_videos} vidéos mises à jour")
            print(f"   - {total_courts} terrains configurés")
            print(f"   - Système de capture vidéo prêt")
            
        except Exception as e:
            print(f"❌ Erreur lors de la migration: {e}")
            db.session.rollback()
            raise e

if __name__ == "__main__":
    apply_video_system_migration()
