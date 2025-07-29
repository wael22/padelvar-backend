"""
Service de capture vidéo - Enregistrement des flux caméra vers stockage local
Optimisé pour la performance et gestion des erreurs
"""

import cv2
import threading
import time
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import uuid
import subprocess
import requests
from pathlib import Path

from ..models.database import db
from ..models.user import Video, Court, User

logger = logging.getLogger(__name__)

class VideoCaptureService:
    """Service de capture vidéo optimisé pour haute performance"""
    
    def __init__(self, base_path: str = "static/videos"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.thumbnails_path = Path("static/thumbnails")
        self.thumbnails_path.mkdir(parents=True, exist_ok=True)
        
        # Sessions d'enregistrement actives
        self.active_recordings: Dict[str, Dict[str, Any]] = {}
        self.recording_threads: Dict[str, threading.Thread] = {}
        
        # Configuration
        self.max_recording_duration = 3600  # 1 heure max
        self.video_quality = {
            'fps': 25,
            'width': 1280,
            'height': 720,
            'bitrate': '2M'
        }
        
        logger.info("Service de capture vidéo initialisé")
    
    def start_recording(self, court_id: int, user_id: int, session_name: str = None) -> Dict[str, Any]:
        """Démarrer l'enregistrement d'un terrain"""
        try:
            # Vérifier que le terrain existe
            court = Court.query.get(court_id)
            if not court:
                raise ValueError(f"Terrain {court_id} non trouvé")
            
            # Vérifier que l'utilisateur existe
            user = User.query.get(user_id)
            if not user:
                raise ValueError(f"Utilisateur {user_id} non trouvé")
            
            # Générer un ID unique pour la session
            session_id = f"rec_{court_id}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Nom du fichier vidéo
            if not session_name:
                session_name = f"Match du {datetime.now().strftime('%d/%m/%Y')}"
            
            video_filename = f"{session_id}.mp4"
            video_path = self.base_path / video_filename
            
            # URL de la caméra du terrain
            camera_url = self._get_camera_url(court_id)
            
            # Configuration de la session
            recording_config = {
                'session_id': session_id,
                'court_id': court_id,
                'user_id': user_id,
                'session_name': session_name,
                'video_filename': video_filename,
                'video_path': str(video_path),
                'camera_url': camera_url,
                'start_time': datetime.now(),
                'status': 'starting',
                'duration': 0,
                'file_size': 0
            }
            
            # Ajouter à la liste des enregistrements actifs
            self.active_recordings[session_id] = recording_config
            
            # Démarrer le thread d'enregistrement
            recording_thread = threading.Thread(
                target=self._record_video_thread,
                args=(session_id, recording_config),
                daemon=True
            )
            recording_thread.start()
            self.recording_threads[session_id] = recording_thread
            
            logger.info(f"Enregistrement démarré: {session_id} pour terrain {court_id}")
            
            return {
                'session_id': session_id,
                'status': 'started',
                'message': f"Enregistrement démarré pour {session_name}",
                'video_filename': video_filename,
                'camera_url': camera_url
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de l'enregistrement: {e}")
            raise e
    
    def stop_recording(self, session_id: str) -> Dict[str, Any]:
        """Arrêter l'enregistrement d'une session"""
        try:
            if session_id not in self.active_recordings:
                raise ValueError(f"Session {session_id} non trouvée")
            
            recording = self.active_recordings[session_id]
            recording['status'] = 'stopping'
            
            # Attendre que le thread se termine (max 10 secondes)
            if session_id in self.recording_threads:
                thread = self.recording_threads[session_id]
                thread.join(timeout=10)
                del self.recording_threads[session_id]
            
            # Finaliser l'enregistrement
            result = self._finalize_recording(session_id)
            
            # Supprimer de la liste active
            del self.active_recordings[session_id]
            
            logger.info(f"Enregistrement arrêté: {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt de l'enregistrement: {e}")
            raise e
    
    def get_recording_status(self, session_id: str = None) -> Dict[str, Any]:
        """Obtenir le statut des enregistrements"""
        try:
            if session_id:
                if session_id in self.active_recordings:
                    recording = self.active_recordings[session_id].copy()
                    recording['duration'] = self._calculate_duration(recording['start_time'])
                    recording['file_size'] = self._get_file_size(recording['video_path'])
                    return recording
                else:
                    return {'error': f'Session {session_id} non trouvée'}
            else:
                # Retourner tous les enregistrements actifs
                all_recordings = {}
                for sid, recording in self.active_recordings.items():
                    recording_copy = recording.copy()
                    recording_copy['duration'] = self._calculate_duration(recording['start_time'])
                    recording_copy['file_size'] = self._get_file_size(recording['video_path'])
                    all_recordings[sid] = recording_copy
                
                return {
                    'active_recordings': all_recordings,
                    'total_active': len(all_recordings)
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {e}")
            return {'error': str(e)}
    
    def _record_video_thread(self, session_id: str, config: Dict[str, Any]):
        """Thread d'enregistrement vidéo"""
        try:
            camera_url = config['camera_url']
            video_path = config['video_path']
            
            logger.info(f"Démarrage capture vidéo: {camera_url} -> {video_path}")
            
            # Mettre à jour le statut
            self.active_recordings[session_id]['status'] = 'recording'
            
            # Utiliser FFmpeg pour capturer et encoder
            # Plus stable et performant que OpenCV pour les flux réseau
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', camera_url,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-f', 'mp4',
                '-movflags', '+faststart',
                '-t', str(self.max_recording_duration),  # Durée max
                video_path
            ]
            
            # Alternative avec OpenCV si FFmpeg n'est pas disponible
            try:
                # Essayer avec FFmpeg d'abord
                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                # Surveiller le processus
                while process.poll() is None:
                    if self.active_recordings[session_id]['status'] == 'stopping':
                        process.terminate()
                        break
                    time.sleep(1)
                
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    logger.info(f"Enregistrement FFmpeg terminé avec succès: {session_id}")
                else:
                    logger.warning(f"FFmpeg terminé avec code {process.returncode}: {stderr}")
                    # Fallback vers OpenCV
                    self._record_with_opencv(session_id, config)
                    
            except FileNotFoundError:
                logger.warning("FFmpeg non trouvé, utilisation d'OpenCV")
                self._record_with_opencv(session_id, config)
            except Exception as e:
                logger.error(f"Erreur FFmpeg: {e}, fallback vers OpenCV")
                self._record_with_opencv(session_id, config)
            
        except Exception as e:
            logger.error(f"Erreur dans le thread d'enregistrement {session_id}: {e}")
            self.active_recordings[session_id]['status'] = 'error'
            self.active_recordings[session_id]['error'] = str(e)
    
    def _record_with_opencv(self, session_id: str, config: Dict[str, Any]):
        """Enregistrement avec OpenCV comme fallback"""
        try:
            camera_url = config['camera_url']
            video_path = config['video_path']
            
            # Ouvrir la capture vidéo
            cap = cv2.VideoCapture(camera_url)
            
            if not cap.isOpened():
                raise Exception(f"Impossible d'ouvrir la caméra: {camera_url}")
            
            # Configuration de l'enregistreur
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = self.video_quality['fps']
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
            
            start_time = time.time()
            frame_count = 0
            
            while True:
                # Vérifier si on doit arrêter
                if self.active_recordings[session_id]['status'] == 'stopping':
                    break
                
                # Vérifier la durée maximale
                if time.time() - start_time > self.max_recording_duration:
                    break
                
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Impossible de lire le frame de {camera_url}")
                    time.sleep(0.1)
                    continue
                
                # Écrire le frame
                out.write(frame)
                frame_count += 1
                
                # Pause pour maintenir le FPS
                time.sleep(1.0 / fps)
            
            # Nettoyer
            cap.release()
            out.release()
            
            logger.info(f"Enregistrement OpenCV terminé: {session_id}, {frame_count} frames")
            
        except Exception as e:
            logger.error(f"Erreur OpenCV pour {session_id}: {e}")
            self.active_recordings[session_id]['status'] = 'error'
            self.active_recordings[session_id]['error'] = str(e)
    
    def _finalize_recording(self, session_id: str) -> Dict[str, Any]:
        """Finaliser l'enregistrement et créer l'entrée en base"""
        try:
            recording = self.active_recordings[session_id]
            video_path = recording['video_path']
            
            # Vérifier que le fichier existe
            if not os.path.exists(video_path):
                raise Exception(f"Fichier vidéo non trouvé: {video_path}")
            
            # Calculer la durée et la taille
            duration = self._calculate_duration(recording['start_time'])
            file_size = self._get_file_size(video_path)
            
            # Générer une miniature
            thumbnail_path = self._generate_thumbnail(video_path, recording['session_id'])
            
            # Créer l'entrée vidéo en base de données
            video = Video(
                title=recording['session_name'],
                file_url=f"/videos/{recording['video_filename']}",
                thumbnail_url=f"/thumbnails/{recording['session_id']}.jpg" if thumbnail_path else None,
                duration=duration,
                court_id=recording['court_id'],
                user_id=recording['user_id'],
                recorded_at=recording['start_time'],
                is_unlocked=False,  # Nécessite des crédits pour débloquer
                credits_cost=10,  # Coût par défaut
                file_size=file_size
            )
            
            db.session.add(video)
            db.session.commit()
            
            logger.info(f"Vidéo enregistrée en base: {video.id}")
            
            return {
                'status': 'completed',
                'video_id': video.id,
                'video_filename': recording['video_filename'],
                'duration': duration,
                'file_size': file_size,
                'thumbnail_url': video.thumbnail_url,
                'message': f"Enregistrement terminé: {recording['session_name']}"
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la finalisation: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': "Erreur lors de la finalisation de l'enregistrement"
            }
    
    def _generate_thumbnail(self, video_path: str, session_id: str) -> Optional[str]:
        """Générer une miniature pour la vidéo"""
        try:
            thumbnail_filename = f"{session_id}.jpg"
            thumbnail_path = self.thumbnails_path / thumbnail_filename
            
            # Utiliser FFmpeg pour générer la miniature
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', '00:00:01',  # Prendre une frame à 1 seconde
                '-vframes', '1',
                '-q:v', '2',  # Haute qualité
                str(thumbnail_path)
            ]
            
            try:
                subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
                logger.info(f"Miniature générée: {thumbnail_path}")
                return str(thumbnail_path)
            except (FileNotFoundError, subprocess.CalledProcessError):
                # Fallback avec OpenCV
                return self._generate_thumbnail_opencv(video_path, thumbnail_path)
                
        except Exception as e:
            logger.error(f"Erreur génération miniature: {e}")
            return None
    
    def _generate_thumbnail_opencv(self, video_path: str, thumbnail_path: str) -> Optional[str]:
        """Générer miniature avec OpenCV"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            # Aller à 1 seconde
            cap.set(cv2.CAP_PROP_POS_MSEC, 1000)
            
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(str(thumbnail_path), frame)
                cap.release()
                logger.info(f"Miniature OpenCV générée: {thumbnail_path}")
                return str(thumbnail_path)
            else:
                cap.release()
                return None
                
        except Exception as e:
            logger.error(f"Erreur miniature OpenCV: {e}")
            return None
    
    def _get_camera_url(self, court_id: int) -> str:
        """Obtenir l'URL de la caméra pour un terrain"""
        try:
            court = Court.query.get(court_id)
            if court and hasattr(court, 'camera_url') and court.camera_url:
                return court.camera_url
            else:
                # URL de simulation pour les tests
                return f"http://localhost:5000/api/courts/{court_id}/camera_stream"
                
        except Exception as e:
            logger.error(f"Erreur récupération URL caméra: {e}")
            # URL de fallback
            return f"http://localhost:5000/api/courts/{court_id}/camera_stream"
    
    def _calculate_duration(self, start_time: datetime) -> int:
        """Calculer la durée en secondes"""
        return int((datetime.now() - start_time).total_seconds())
    
    def _get_file_size(self, file_path: str) -> int:
        """Obtenir la taille du fichier en octets"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0
    
    def cleanup_old_recordings(self, days_old: int = 30):
        """Nettoyer les anciens enregistrements"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Supprimer les anciens fichiers vidéo
            for video_file in self.base_path.glob("*.mp4"):
                if os.path.getctime(video_file) < cutoff_date.timestamp():
                    os.remove(video_file)
                    logger.info(f"Fichier vidéo ancien supprimé: {video_file}")
            
            # Supprimer les anciennes miniatures
            for thumb_file in self.thumbnails_path.glob("*.jpg"):
                if os.path.getctime(thumb_file) < cutoff_date.timestamp():
                    os.remove(thumb_file)
                    logger.info(f"Miniature ancienne supprimée: {thumb_file}")
            
            # Mettre à jour la base de données
            old_videos = Video.query.filter(Video.recorded_at < cutoff_date).all()
            for video in old_videos:
                video.file_url = None  # Marquer comme non disponible
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")

# Instance globale du service
video_capture_service = VideoCaptureService()
