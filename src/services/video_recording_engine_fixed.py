"""
SERVICE D'ENREGISTREMENT VIDÉO CORRIGÉ
====================================

Service principal pour la gestion des enregistrements vidéo avec:
- Support FFmpeg optimisé
- Upload automatique vers Bunny CDN 
- Gestion d'état robuste
- Logging intégré
- Nettoyage automatique
"""

import cv2
import threading
import time
import os
import logging
import subprocess
import shutil
from datetime import datetime
from typing import Dict, Optional, Any, List
from pathlib import Path
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import uuid

from ..models.database import db
from ..models.user import Video, Court, User
from .bunny_storage_service import bunny_storage_service
from .logging_service import get_logger, LogLevel

# Configuration du logger
logger = logging.getLogger(__name__)
system_logger = get_logger()

# Configuration FFmpeg robuste
FFMPEG_PATH = r"C:\ffmpeg\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"
if not Path(FFMPEG_PATH).exists():
    FFMPEG_PATH = 'ffmpeg'
    logger.warning("⚠️ FFmpeg non trouvé, utilisation PATH")
else:
    logger.info(f"✅ FFmpeg trouvé: {FFMPEG_PATH}")


class RecordingState(Enum):
    """États possibles d'un enregistrement"""
    STARTING = 'starting'
    RECORDING = 'recording'
    STOPPING = 'stopping'
    COMPLETED = 'completed'
    ERROR = 'error'
    FAILED = 'failed'


class VideoRecordingEngine:
    """
    MOTEUR D'ENREGISTREMENT VIDÉO UNIFIÉ ET ROBUSTE
    ===============================================
    
    Fonctionnalités:
    - Enregistrement FFmpeg avec gestion d'erreurs
    - Upload automatique Bunny CDN (optionnel)
    - Monitoring des processus
    - Nettoyage automatique des enregistrements fantômes
    - Thread-safe et concurrent
    """

    def __init__(self, video_dir: str = "static/videos",
                 temp_dir: str = "temp_recordings"):
        """Initialiser le moteur d'enregistrement"""
        
        # Répertoires de stockage
        self.video_dir = Path(video_dir)
        self.temp_dir = Path(temp_dir)
        
        # Créer les répertoires si nécessaire
        self.video_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # État des enregistrements actifs
        self._active_recordings: Dict[str, Dict[str, Any]] = {}
        self._recordings_lock = threading.RLock()
        
        # Thread pool pour les opérations asynchrones
        self._thread_pool = ThreadPoolExecutor(
            max_workers=4, 
            thread_name_prefix="VideoEngine"
        )
        
        # Processus actifs (pour monitoring)
        self._active_processes: Dict[str, subprocess.Popen] = {}
        self._processes_lock = threading.Lock()
        
        # Configuration par défaut
        self.config = {
            'default_duration': 300,  # 5 minutes par défaut
            'max_duration': 3600,     # 1 heure maximum
            'video_quality': 'medium',
            'fps': 25,
            'resolution': '1280x720',
            'format': 'mp4',
            'process_check_interval': 5,  # Vérifier processus (5s)
            'upload_retry_count': 3,
            'upload_timeout': 300
        }
        
        # Variables d'état
        self._monitoring_active = False
        self._shutdown_requested = False
        
        # Initialiser le système
        self._initialize_system()
        
        # Logger de démarrage
        system_logger.log(
            LogLevel.INFO, 
            "🚀 VideoRecordingEngine - Moteur initialisé", 
            {}
        )

    def _initialize_system(self):
        """Initialiser le système d'enregistrement"""
        try:
            # Nettoyer les enregistrements fantômes au démarrage
            self._cleanup_phantom_recordings()
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation système: {e}")

    def _cleanup_phantom_recordings(self):
        """Nettoyer les enregistrements fantômes dans la base"""
        try:
            system_logger.log(
                LogLevel.INFO, 
                "🧹 Début nettoyage enregistrements fantômes", 
                {}
            )
            
            # Récupérer les terrains avec enregistrement actif
            from ..models.user import Court
            courts = Court.query.filter(
                Court.current_recording_id.isnot(None)
            ).all()
            
            for court in courts:
                system_logger.log(
                    LogLevel.WARNING, 
                    f"⚠️ Terrain fantôme détecté: {court.id}", 
                    {
                        "court_id": court.id, 
                        "recording_id": court.current_recording_id
                    }
                )
                court.current_recording_id = None
            
            db.session.commit()
            
            system_logger.log(
                LogLevel.INFO,
                f"✅ Nettoyage terminé: {len(courts)} terrains libérés",
                {"courts_cleaned": len(courts)}
            )
            
        except Exception as e:
            db.session.rollback()
            system_logger.log(
                LogLevel.ERROR, 
                f"❌ Erreur nettoyage fantômes: {e}", 
                {"error": str(e)}
            )

    def start_recording(self, court_id: int, user_id: int, 
                       session_name: str = None,
                       keep_local_files: bool = True, 
                       upload_to_bunny: bool = False) -> Dict[str, Any]:
        """
        Démarrer un enregistrement vidéo
        
        Args:
            court_id: ID du terrain
            user_id: ID de l'utilisateur
            session_name: Nom de la session (optionnel)
            keep_local_files: Garder les fichiers locaux
            upload_to_bunny: Upload automatique vers Bunny CDN
            
        Returns:
            Dict avec les détails de l'enregistrement
        """
        
        with self._recordings_lock:
            try:
                # Logger l'opération
                system_logger.log(
                    LogLevel.INFO, 
                    "📝 Demande d'enregistrement reçue", 
                    {"operation": "start_recording"}
                )
                
                # Générer un ID de session unique
                timestamp = int(time.time())
                session_id = f"rec_{court_id}_{timestamp}_{uuid.uuid4().hex[:8]}"
                
                # Nom de session par défaut
                if not session_name:
                    date_str = datetime.now().strftime('%d/%m/%Y %H:%M')
                    session_name = f"Match du {date_str}"
                
                # Récupérer les informations du terrain
                court = Court.query.get(court_id)
                if not court:
                    raise ValueError(f"Terrain {court_id} non trouvé")
                    
                camera_url = court.camera_url
                system_logger.log(
                    LogLevel.INFO, 
                    f"📹 URL caméra récupérée: {camera_url[:50]}...", 
                    {"session_id": session_id, "court_id": court_id}
                )
                
                # Vérifier si le terrain n'est pas déjà en cours d'enregistrement
                if court.current_recording_id:
                    raise ValueError(
                        f"Terrain {court_id} déjà en cours d'enregistrement"
                    )
                
                # Marquer le terrain comme en cours d'enregistrement
                court.current_recording_id = session_id
                db.session.commit()
                
                # État initial de l'enregistrement
                recording_state = {
                    'session_id': session_id,
                    'court_id': court_id,
                    'user_id': user_id,
                    'session_name': session_name,
                    'camera_url': camera_url,
                    'state': RecordingState.STARTING,
                    'start_time': datetime.now(),
                    'method': self._determine_recording_method(camera_url),
                    'process': None,
                    'video_path': None,
                    'keep_local_files': keep_local_files,  # Config upload
                    'upload_to_bunny': upload_to_bunny,  # Config Bunny CDN
                    'progress': {
                        'duration': 0,
                        'file_size': 0,
                        'status': 'starting',
                        'upload_status': 'pending' if upload_to_bunny else 'disabled'
                    }
                }
                
                # Enregistrer l'état
                self._active_recordings[session_id] = recording_state
                
                system_logger.log(
                    LogLevel.INFO, 
                    f"✅ Enregistrement démarré: {session_id}"
                )
                
                # Démarrer l'enregistrement en arrière-plan
                self._thread_pool.submit(
                    self._start_recording_background, 
                    recording_state
                )
                
                return {
                    'success': True,
                    'session_id': session_id,
                    'message': 'Enregistrement démarré avec succès',
                    'details': {
                        'court_id': court_id,
                        'user_id': user_id,
                        'session_name': session_name,
                        'method': recording_state['method'],
                        'upload_config': {
                            'keep_local': keep_local_files,
                            'upload_bunny': upload_to_bunny
                        }
                    }
                }
                
            except Exception as e:
                # Nettoyer en cas d'erreur
                try:
                    court = Court.query.get(court_id)
                    if court:
                        court.current_recording_id = None
                        db.session.commit()
                except:
                    pass
                
                error_msg = f"Erreur démarrage enregistrement terrain {court_id}"
                logger.error(f"❌ {error_msg}: {e}")
                
                return {
                    'success': False,
                    'error': str(e),
                    'message': error_msg
                }

    def stop_recording(self, session_id: str) -> Dict[str, Any]:
        """
        Arrêter un enregistrement
        
        Args:
            session_id: ID de la session à arrêter
            
        Returns:
            Dict avec le résultat de l'opération
        """
        
        with self._recordings_lock:
            try:
                if session_id not in self._active_recordings:
                    return {
                        'success': False,
                        'error': f'Session {session_id} non trouvée'
                    }
                
                recording = self._active_recordings[session_id]
                recording['state'] = RecordingState.STOPPING
                
                # Arrêter le processus s'il existe
                if recording.get('process'):
                    process = recording['process']
                    try:
                        process.terminate()
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                
                # Finaliser l'enregistrement
                result = self._finalize_recording(session_id)
                
                # Libérer le terrain
                court = Court.query.get(recording['court_id'])
                if court:
                    court.current_recording_id = None
                    db.session.commit()
                
                # Supprimer de la liste active
                del self._active_recordings[session_id]
                
                logger.info(f"✅ Enregistrement arrêté avec succès: {session_id}")
                
                return {
                    'success': True,
                    'session_id': session_id,
                    'message': 'Enregistrement arrêté avec succès',
                    'result': result
                }
                
            except Exception as e:
                logger.error(f"❌ Erreur arrêt enregistrement {session_id}: {e}")
                
                return {
                    'success': False,
                    'error': str(e),
                    'message': "Erreur lors de l'arrêt de l'enregistrement"
                }

    def get_recording_status(self, session_id: str) -> Dict[str, Any]:
        """Obtenir le statut d'un enregistrement"""
        
        with self._recordings_lock:
            if session_id not in self._active_recordings:
                return {
                    'success': False,
                    'error': 'Session non trouvée'
                }
            
            recording = self._active_recordings[session_id]
            
            # Calculer la durée
            duration = (datetime.now() - recording['start_time']).total_seconds()
            
            return {
                'success': True,
                'session_id': session_id,
                'state': recording['state'].value,
                'duration': duration,
                'progress': recording['progress'],
                'details': {
                    'court_id': recording['court_id'],
                    'user_id': recording['user_id'],
                    'session_name': recording['session_name'],
                    'method': recording['method'],
                    'start_time': recording['start_time'].isoformat()
                }
            }

    def _determine_recording_method(self, camera_url: str) -> str:
        """Déterminer la méthode d'enregistrement selon l'URL"""
        
        if not camera_url:
            return 'unknown'
        
        url_lower = camera_url.lower()
        
        if 'mjpeg' in url_lower or '.mjpg' in url_lower:
            return 'mjpeg_ffmpeg'
        elif 'rtsp://' in url_lower:
            return 'rtsp_ffmpeg'
        elif url_lower.startswith('http'):
            return 'http_ffmpeg'
        else:
            return 'generic_ffmpeg'

    def _start_recording_background(self, recording_state: Dict[str, Any]):
        """Démarrer l'enregistrement en arrière-plan"""
        
        session_id = recording_state['session_id']
        
        try:
            # Générer le nom du fichier de sortie
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"recording_{session_id}_{timestamp}.mp4"
            video_path = self.temp_dir / filename
            
            recording_state['video_path'] = str(video_path)
            recording_state['state'] = RecordingState.RECORDING
            
            # Construire la commande FFmpeg
            ffmpeg_cmd = self._build_ffmpeg_command(
                recording_state['camera_url'],
                video_path
            )
            
            logger.info(f"🎬 Démarrage FFmpeg: {session_id}")
            
            # Démarrer le processus FFmpeg
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            recording_state['process'] = process
            
            with self._processes_lock:
                self._active_processes[session_id] = process
            
            # Attendre la fin du processus ou l'arrêt
            try:
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    recording_state['state'] = RecordingState.COMPLETED
                    logger.info(f"✅ Enregistrement terminé: {session_id}")
                    
                    # Finaliser si pas encore fait
                    if recording_state['state'] != RecordingState.STOPPING:
                        self._finalize_recording(session_id)
                        
                else:
                    recording_state['state'] = RecordingState.ERROR
                    logger.error(f"❌ Erreur FFmpeg {session_id}: {stderr}")
                    
            except Exception as e:
                recording_state['state'] = RecordingState.ERROR
                logger.error(f"❌ Erreur processus {session_id}: {e}")
                
        except Exception as e:
            recording_state['state'] = RecordingState.FAILED
            logger.error(f"❌ Erreur enregistrement {session_id}: {e}")
        
        finally:
            # Nettoyer les références au processus
            with self._processes_lock:
                self._active_processes.pop(session_id, None)

    def _build_ffmpeg_command(self, input_url: str, output_path: Path) -> List[str]:
        """Construire la commande FFmpeg optimisée"""
        
        cmd = [
            FFMPEG_PATH,
            '-y',  # Overwrite output files
            '-i', input_url,
            
            # Encodage vidéo optimisé
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            
            # Paramètres audio
            '-c:a', 'aac',
            '-b:a', '128k',
            
            # Format de sortie
            '-f', 'mp4',
            '-movflags', '+faststart',
            
            # Gestion d'erreurs
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '5',
            
            str(output_path)
        ]
        
        return cmd

    def _finalize_recording(self, session_id: str) -> Dict[str, Any]:
        """Finaliser un enregistrement et créer l'entrée vidéo"""
        
        try:
            recording = self._active_recordings.get(session_id)
            if not recording:
                return {'success': False, 'error': 'Session non trouvée'}
            
            video_path = recording.get('video_path')
            if not video_path or not Path(video_path).exists():
                return {'success': False, 'error': 'Fichier vidéo non trouvé'}
            
            # Calculer la durée et la taille
            duration = (datetime.now() - recording['start_time']).total_seconds()
            file_size = Path(video_path).stat().st_size
            
            # Créer l'entrée vidéo en base
            video = Video(
                title=recording['session_name'],
                description=f"Enregistrement terrain {recording['court_id']}",
                file_url=f"/static/videos/{Path(video_path).name}",
                duration=int(duration),
                file_size=file_size,
                user_id=recording['user_id'],
                court_id=recording['court_id'],
                recorded_at=recording['start_time']
            )
            
            db.session.add(video)
            db.session.commit()
            
            # Déplacer le fichier vers le répertoire final
            final_path = self.video_dir / Path(video_path).name
            shutil.move(video_path, final_path)
            
            logger.info(f"✅ Vidéo finalisée: {video.id} ({duration:.1f}s)")
            
            # Upload automatique vers Bunny CDN si configuré
            if recording.get('upload_to_bunny', False):
                self._upload_to_bunny_async(video, str(final_path), recording)
            
            return {
                'success': True,
                'video_id': video.id,
                'duration': duration,
                'file_size': file_size,
                'file_path': str(final_path)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur finalisation {session_id}: {e}")
            return {'success': False, 'error': str(e)}

    def _upload_to_bunny_async(self, video: Video, video_path: str, 
                              recording_state: Dict[str, Any]):
        """Upload asynchrone vers Bunny CDN"""
        
        def upload_task():
            try:
                logger.info(f"🚀 Début upload Bunny: {video.id}")
                
                # Utiliser le service Bunny CDN
                success, bunny_url = bunny_storage_service.upload_file(
                    video_path,
                    f"video_{video.id}_{int(time.time())}.mp4"
                )
                
                if success and bunny_url:
                    # Mettre à jour l'URL de la vidéo
                    video.file_url = bunny_url
                    db.session.commit()
                    
                    logger.info(f"✅ Upload Bunny réussi: {video.id}")
                    
                    # Supprimer le fichier local si configuré
                    if not recording_state.get('keep_local_files', True):
                        try:
                            os.remove(video_path)
                            logger.info(f"🗑️ Fichier local supprimé: {video_path}")
                        except Exception as e:
                            logger.warning(f"⚠️ Erreur suppression: {e}")
                            
                else:
                    logger.error(f"❌ Échec upload Bunny: {video.id}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur upload async {video.id}: {e}")
        
        # Lancer l'upload en arrière-plan
        self._thread_pool.submit(upload_task)

    def get_active_recordings(self) -> Dict[str, Any]:
        """Obtenir la liste des enregistrements actifs"""
        
        with self._recordings_lock:
            active_list = []
            
            for session_id, recording in self._active_recordings.items():
                active_list.append({
                    'session_id': session_id,
                    'court_id': recording['court_id'],
                    'user_id': recording['user_id'],
                    'state': recording['state'].value,
                    'duration': (datetime.now() - recording['start_time']).total_seconds(),
                    'method': recording['method'],
                    'start_time': recording['start_time'].isoformat()
                })
            
            return {
                'active_recordings': active_list,
                'count': len(active_list)
            }

    def cleanup_old_files(self, max_age_hours: int = 24):
        """Nettoyer les anciens fichiers temporaires"""
        
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            
            cleaned_count = 0
            for file_path in self.temp_dir.glob('*'):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur suppression {file_path}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"🧹 Nettoyage: {cleaned_count} fichiers supprimés")
                
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage fichiers: {e}")

    def shutdown(self):
        """Arrêter proprement le moteur d'enregistrement"""
        
        self._shutdown_requested = True
        
        # Arrêter tous les enregistrements actifs
        with self._recordings_lock:
            for session_id in list(self._active_recordings.keys()):
                self.stop_recording(session_id)
        
        # Arrêter le thread pool
        self._thread_pool.shutdown(wait=True)
        
        logger.info("🛑 VideoRecordingEngine arrêté")


# Instance globale du moteur d'enregistrement
video_recording_engine = VideoRecordingEngine()
