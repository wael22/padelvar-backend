"""
Service de capture vidéo - Enregistrement des flux caméra vers stockage local
Optimisé pour la performance, la fiabilité et la gestion des erreurs
"""

import cv2
import threading
import time
import os
import logging
import signal
import queue
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Tuple
import uuid
import subprocess
import requests
from pathlib import Path
import shutil
from concurrent.futures import ThreadPoolExecutor

from ..models.database import db
from ..models.user import Video, Court, User
from .bunny_storage_service import bunny_storage_service

# Configuration du logger
logger = logging.getLogger(__name__)

class CameraStream:
    """Gestion de flux vidéo depuis caméras IP"""
    
    def __init__(self, camera_url: str, buffer_size: int = 10):
        """
        Initialise une connexion à un flux caméra.
        
        Args:
            camera_url: URL de la caméra (RTSP, HTTP, etc.)
            buffer_size: Taille du buffer de frames
        """
        self.camera_url = camera_url
        self.is_running = False
        self.frame_buffer = queue.Queue(maxsize=buffer_size)
        self.lock = threading.RLock()
        self.capture = None
        self.thread = None
        self.last_frame = None
        self.last_error = None
        self.reconnect_delay = 5  # secondes
        self.max_reconnect_attempts = 5
        
    def start(self) -> bool:
        """
        Démarre la capture du flux caméra dans un thread séparé.
        
        Returns:
            True si démarré avec succès, False sinon
        """
        with self.lock:
            if self.is_running:
                return True
                
            self.is_running = True
            self.thread = threading.Thread(
                target=self._capture_loop,
                daemon=True
            )
            self.thread.start()
            
            # Attendre que le premier frame soit disponible ou qu'une erreur survienne
            timeout = 5  # secondes
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if not self.frame_buffer.empty() or self.last_error:
                    break
                time.sleep(0.1)
                
            return not self.frame_buffer.empty()
    
    def stop(self):
        """Arrête la capture du flux caméra"""
        with self.lock:
            self.is_running = False
            
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2)
                
            if self.capture:
                self.capture.release()
                self.capture = None
                
            # Vider le buffer
            while not self.frame_buffer.empty():
                try:
                    self.frame_buffer.get_nowait()
                except queue.Empty:
                    break
    
    def get_frame(self) -> Tuple[bool, Optional[Any]]:
        """
        Récupère le dernier frame du buffer.
        
        Returns:
            (success, frame): Tuple indiquant si un frame est disponible et le frame lui-même
        """
        try:
            if not self.frame_buffer.empty():
                frame = self.frame_buffer.get_nowait()
                self.last_frame = frame
                return True, frame
            elif self.last_frame is not None:
                return True, self.last_frame
            else:
                return False, None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du frame: {e}")
            return False, None
    
    def _capture_loop(self):
        """Boucle principale de capture des frames"""
        reconnect_attempts = 0
        
        while self.is_running:
            try:
                if self.capture is None or not self.capture.isOpened():
                    # Initialiser ou réinitialiser la capture
                    if self.capture:
                        self.capture.release()
                        
                    self.capture = cv2.VideoCapture(self.camera_url)
                    
                    if not self.capture.isOpened():
                        reconnect_attempts += 1
                        self.last_error = f"Impossible d'ouvrir la caméra: {self.camera_url}"
                        logger.warning(f"{self.last_error} (tentative {reconnect_attempts}/{self.max_reconnect_attempts})")
                        
                        if reconnect_attempts >= self.max_reconnect_attempts:
                            logger.error(f"Abandon après {reconnect_attempts} tentatives")
                            self.is_running = False
                            break
                            
                        time.sleep(self.reconnect_delay)
                        continue
                    else:
                        reconnect_attempts = 0
                        logger.info(f"Connexion établie au flux: {self.camera_url}")
                
                # Lire un frame
                ret, frame = self.capture.read()
                
                if not ret:
                    logger.warning(f"Erreur de lecture du frame depuis {self.camera_url}")
                    time.sleep(0.5)
                    continue
                
                # Mettre le frame dans le buffer (en écrasant le plus ancien si plein)
                if self.frame_buffer.full():
                    try:
                        self.frame_buffer.get_nowait()
                    except queue.Empty:
                        pass
                        
                self.frame_buffer.put(frame)
                
            except Exception as e:
                logger.error(f"Erreur dans la boucle de capture: {e}")
                time.sleep(1)
        
        # Nettoyage final
        if self.capture:
            self.capture.release()
            self.capture = None

class RecordingTask:
    """Représente une tâche d'enregistrement vidéo"""
    
    def __init__(self, session_id: str, camera_url: str, output_path: str, 
                 max_duration: int, user_id: int, court_id: int,
                 session_name: str, video_quality: Dict[str, Any]):
        """
        Initialise une tâche d'enregistrement.
        
        Args:
            session_id: Identifiant unique de la session
            camera_url: URL de la caméra
            output_path: Chemin du fichier de sortie
            max_duration: Durée maximale en secondes
            user_id: ID de l'utilisateur
            court_id: ID du terrain
            session_name: Nom de la session
            video_quality: Paramètres de qualité vidéo
        """
        self.session_id = session_id
        self.camera_url = camera_url
        self.output_path = output_path
        self.max_duration = max_duration
        self.user_id = user_id
        self.court_id = court_id
        self.session_name = session_name
        self.video_quality = video_quality
        
        self.start_time = datetime.now()
        self.status = 'created'
        self.process = None
        self.camera_stream = None
        self.error = None
        self.file_size = 0
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'objet en dictionnaire.
        
        Returns:
            Dictionnaire des attributs de la tâche
        """
        duration = int((datetime.now() - self.start_time).total_seconds())
        
        return {
            'session_id': self.session_id,
            'camera_url': self.camera_url,
            'output_path': self.output_path,
            'status': self.status,
            'start_time': self.start_time.isoformat(),
            'duration': duration,
            'user_id': self.user_id,
            'court_id': self.court_id,
            'session_name': self.session_name,
            'file_size': self.file_size,
            'error': self.error
        }

class VideoCaptureService:
    """Service optimisé de capture vidéo pour caméras IP et enregistrements fiables"""
    
    def __init__(self, base_path: str = "static/videos"):
        """
        Initialise le service de capture vidéo.
        
        Args:
            base_path: Chemin de base pour le stockage des vidéos
        """
        # Configuration des chemins
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.thumbnails_path = Path("static/thumbnails")
        self.thumbnails_path.mkdir(parents=True, exist_ok=True)
        
        self.temp_path = Path("static/temp")
        self.temp_path.mkdir(parents=True, exist_ok=True)
        
        # Gestion des enregistrements
        self.recordings: Dict[str, RecordingTask] = {}
        self.recording_processes: Dict[str, subprocess.Popen] = {}
        self.camera_streams: Dict[str, CameraStream] = {}
        
        # Verrou pour la synchronisation des accès concurrents
        self.lock = threading.RLock()
        
        # Configuration d'encodage
        self.max_recording_duration = 3600  # 1 heure max
        self.video_quality = {
            'fps': 25,
            'width': 1280,
            'height': 720,
            'bitrate': '2M',
            'preset': 'veryfast',  # Options: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
            'tune': 'zerolatency'  # Optimisé pour le streaming temps réel
        }
        
        # Pool de threads pour les tâches asynchrones
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Démarrer le thread de surveillance
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        
        logger.info("✅ Service de capture vidéo initialisé avec succès")
    
    def start_recording(self, court_id: int, user_id: int, session_name: str = None) -> Dict[str, Any]:
        """
        Démarre l'enregistrement d'un terrain.
        
        Args:
            court_id: ID du terrain à enregistrer
            user_id: ID de l'utilisateur qui démarre l'enregistrement
            session_name: Nom de la session (optionnel)
            
        Returns:
            Informations sur la session d'enregistrement démarrée
        
        Raises:
            ValueError: Si les paramètres sont invalides
            RuntimeError: Si l'enregistrement ne peut pas démarrer
        """
        with self.lock:
            try:
                # Vérifications préliminaires
                court = self._validate_court(court_id)
                user = self._validate_user(user_id)
                
                # Générer ID unique pour la session
                session_id = f"rec_{court_id}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
                
                # Nom de la session
                if not session_name:
                    session_name = f"Match du {datetime.now().strftime('%d/%m/%Y')}"
                
                # Chemin du fichier vidéo
                video_filename = f"{session_id}.mp4"
                video_path = str(self.base_path / video_filename)
                
                # URL de la caméra
                camera_url = self._get_camera_url(court)
                
                # Créer la tâche d'enregistrement
                recording_task = RecordingTask(
                    session_id=session_id,
                    camera_url=camera_url,
                    output_path=video_path,
                    max_duration=self.max_recording_duration,
                    user_id=user_id,
                    court_id=court_id,
                    session_name=session_name,
                    video_quality=self.video_quality
                )
                
                # Démarrer l'enregistrement selon la méthode appropriée
                if self._is_rtsp_url(camera_url):
                    # RTSP: Utiliser FFmpeg directement
                    success = self._start_ffmpeg_recording(recording_task)
                else:
                    # HTTP/autre: Utiliser notre capture personnalisée
                    success = self._start_opencv_recording(recording_task)
                
                if not success:
                    raise RuntimeError(f"Impossible de démarrer l'enregistrement pour le terrain {court_id}")
                
                # Ajouter à la liste des enregistrements actifs
                self.recordings[session_id] = recording_task
                
                logger.info(f"🎬 Enregistrement démarré: {session_id} pour terrain {court_id}")
                
                return {
                    'session_id': session_id,
                    'status': 'started',
                    'message': f"Enregistrement démarré pour {session_name}",
                    'video_filename': video_filename,
                    'camera_url': camera_url
                }
                
            except Exception as e:
                logger.error(f"❌ Erreur lors du démarrage de l'enregistrement: {e}")
                # Nettoyage en cas d'erreur
                if 'session_id' in locals():
                    self._cleanup_recording(session_id)
                raise
    
    def stop_recording(self, session_id: str) -> Dict[str, Any]:
        """
        Arrête l'enregistrement d'une session.
        
        Args:
            session_id: Identifiant de la session à arrêter
            
        Returns:
            Informations sur la session arrêtée
            
        Raises:
            ValueError: Si la session n'existe pas
        """
        with self.lock:
            if session_id not in self.recordings:
                return {
                    'status': 'error',
                    'error': f"Session {session_id} non trouvée",
                    'message': "Enregistrement introuvable ou déjà terminé"
                }
            
            recording = self.recordings[session_id]
            recording.status = 'stopping'
            
            # Arrêter le processus approprié selon le type d'enregistrement
            if session_id in self.recording_processes:
                process = self.recording_processes[session_id]
                try:
                    # Envoyer un signal SIGTERM au processus
                    process.terminate()
                    process.wait(timeout=5)
                except (subprocess.TimeoutExpired, ProcessLookupError):
                    # Forcer l'arrêt si nécessaire
                    try:
                        process.kill()
                    except:
                        pass
                        
                del self.recording_processes[session_id]
            
            # Arrêter le flux caméra si utilisé
            if session_id in self.camera_streams:
                self.camera_streams[session_id].stop()
                del self.camera_streams[session_id]
            
            # Finaliser l'enregistrement (BDD, miniature, etc.)
            result = self._finalize_recording(session_id)
            
            # Supprimer de la liste des enregistrements actifs
            del self.recordings[session_id]
            
            logger.info(f"⏹️ Enregistrement arrêté: {session_id}")
            return result
    
    def get_recording_status(self, session_id: str = None) -> Dict[str, Any]:
        """
        Récupère le statut d'un ou tous les enregistrements.
        
        Args:
            session_id: Identifiant de la session (optionnel)
            
        Returns:
            Statut de l'enregistrement ou liste de tous les enregistrements
        """
        with self.lock:
            try:
                if session_id:
                    if session_id in self.recordings:
                        recording = self.recordings[session_id]
                        # Mettre à jour la taille du fichier
                        recording.file_size = self._get_file_size(recording.output_path)
                        return recording.to_dict()
                    else:
                        return {'error': f'Session {session_id} non trouvée'}
                else:
                    # Retourner tous les enregistrements actifs
                    all_recordings = {}
                    for sid, recording in self.recordings.items():
                        # Mettre à jour la taille du fichier
                        recording.file_size = self._get_file_size(recording.output_path)
                        all_recordings[sid] = recording.to_dict()
                    
                    return {
                        'active_recordings': all_recordings,
                        'total_active': len(all_recordings)
                    }
                    
            except Exception as e:
                logger.error(f"❌ Erreur lors de la récupération du statut: {e}")
                return {'error': str(e)}
    
    def cleanup_old_recordings(self, days_old: int = 30) -> Dict[str, Any]:
        """
        Nettoie les anciens enregistrements.
        
        Args:
            days_old: Âge en jours des enregistrements à supprimer
            
        Returns:
            Résultat du nettoyage
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            deleted_videos = 0
            deleted_thumbnails = 0
            
            # Supprimer les anciens fichiers vidéo
            for video_file in self.base_path.glob("*.mp4"):
                if os.path.getctime(video_file) < cutoff_date.timestamp():
                    os.remove(video_file)
                    deleted_videos += 1
                    logger.info(f"🗑️ Fichier vidéo ancien supprimé: {video_file}")
            
            # Supprimer les anciennes miniatures
            for thumb_file in self.thumbnails_path.glob("*.jpg"):
                if os.path.getctime(thumb_file) < cutoff_date.timestamp():
                    os.remove(thumb_file)
                    deleted_thumbnails += 1
                    logger.info(f"🗑️ Miniature ancienne supprimée: {thumb_file}")
            
            # Mettre à jour la base de données
            with db.session.begin():
                old_videos = Video.query.filter(Video.recorded_at < cutoff_date).all()
                updated_videos = 0
                
                for video in old_videos:
                    video.file_url = None  # Marquer comme non disponible
                    updated_videos += 1
            
            logger.info(f"🧹 Nettoyage terminé: {deleted_videos} vidéos, {deleted_thumbnails} miniatures, {updated_videos} entrées DB mises à jour")
            
            return {
                'status': 'success',
                'deleted_videos': deleted_videos,
                'deleted_thumbnails': deleted_thumbnails,
                'updated_db_entries': updated_videos,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du nettoyage: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def test_camera_connection(self, camera_url: str) -> Dict[str, Any]:
        """
        Teste la connexion à une caméra.
        
        Args:
            camera_url: URL de la caméra à tester
            
        Returns:
            Résultat du test
        """
        try:
            logger.info(f"🔍 Test de connexion à la caméra: {camera_url}")
            
            # Créer un stream de caméra temporaire
            camera = CameraStream(camera_url)
            
            # Essayer de démarrer et récupérer un frame
            start_success = camera.start()
            frame_success = False
            resolution = None
            
            if start_success:
                # Attendre un peu pour avoir des frames
                time.sleep(1)
                
                # Essayer de récupérer un frame
                success, frame = camera.get_frame()
                frame_success = success
                
                if success and frame is not None:
                    height, width = frame.shape[:2]
                    resolution = {"width": width, "height": height}
            
            # Arrêter proprement
            camera.stop()
            
            return {
                'status': 'success' if start_success and frame_success else 'error',
                'connection': start_success,
                'frames_available': frame_success,
                'resolution': resolution,
                'error': camera.last_error,
                'url': camera_url
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du test de la caméra: {e}")
            return {
                'status': 'error',
                'connection': False,
                'frames_available': False,
                'error': str(e),
                'url': camera_url
            }
    
    # ------ Méthodes privées ------
    
    def _validate_court(self, court_id: int) -> Court:
        """Valide et récupère un terrain"""
        court = Court.query.get(court_id)
        if not court:
            raise ValueError(f"Terrain {court_id} non trouvé")
        return court
    
    def _validate_user(self, user_id: int) -> User:
        """Valide et récupère un utilisateur"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"Utilisateur {user_id} non trouvé")
        return user
    
    def _get_camera_url(self, court: Court) -> str:
        """Récupère l'URL de la caméra pour un terrain"""
        if hasattr(court, 'camera_url') and court.camera_url:
            return court.camera_url
        else:
            # URL de simulation pour les tests
            return f"http://localhost:5000/api/courts/{court.id}/camera_stream"
    
    def _is_rtsp_url(self, url: str) -> bool:
        """Détermine si l'URL est un flux RTSP"""
        return url.lower().startswith(('rtsp://', 'rtsps://'))
    
    def _start_ffmpeg_recording(self, recording: RecordingTask) -> bool:
        """Démarre un enregistrement avec FFmpeg"""
        try:
            # Configuration optimisée pour RTSP
            ffmpeg_cmd = [
                'ffmpeg',
                '-rtsp_transport', 'tcp',  # Plus stable que UDP pour RTSP
                '-i', recording.camera_url,
                '-c:v', 'libx264',
                '-preset', self.video_quality['preset'],
                '-tune', self.video_quality['tune'],
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-f', 'mp4',
                '-movflags', '+faststart',
                '-t', str(self.max_recording_duration),
                recording.output_path
            ]
            
            # Créer le processus
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Vérifier que le processus a démarré
            if process.poll() is not None:
                stderr = process.stderr.read() if process.stderr else "Pas d'erreur disponible"
                raise RuntimeError(f"FFmpeg n'a pas pu démarrer: {stderr}")
            
            # Enregistrer le processus
            self.recording_processes[recording.session_id] = process
            
            # Mettre à jour le statut
            recording.status = 'recording'
            recording.process = process
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du démarrage de FFmpeg: {e}")
            recording.status = 'error'
            recording.error = str(e)
            return False
    
    def _start_opencv_recording(self, recording: RecordingTask) -> bool:
        """Démarre un enregistrement avec OpenCV"""
        try:
            # Créer un stream caméra
            camera = CameraStream(recording.camera_url)
            
            # Démarrer la capture
            if not camera.start():
                raise RuntimeError(f"Impossible de démarrer la capture pour {recording.camera_url}")
            
            # Enregistrer le stream
            self.camera_streams[recording.session_id] = camera
            
            # Lancer le thread d'enregistrement OpenCV
            record_thread = threading.Thread(
                target=self._opencv_recording_thread,
                args=(recording.session_id, recording),
                daemon=True
            )
            record_thread.start()
            
            # Mettre à jour le statut
            recording.status = 'recording'
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du démarrage d'OpenCV: {e}")
            recording.status = 'error'
            recording.error = str(e)
            return False
    
    def _opencv_recording_thread(self, session_id: str, recording: RecordingTask):
        """Thread d'enregistrement vidéo avec OpenCV"""
        try:
            camera = self.camera_streams.get(session_id)
            if not camera:
                raise RuntimeError(f"Stream caméra non trouvé pour {session_id}")
            
            # Récupérer un premier frame pour obtenir les dimensions
            success, frame = camera.get_frame()
            if not success or frame is None:
                raise RuntimeError("Impossible d'obtenir le premier frame")
            
            height, width = frame.shape[:2]
            fps = self.video_quality['fps']
            
            # Configuration de l'encodeur
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(recording.output_path, fourcc, fps, (width, height))
            
            start_time = time.time()
            frame_count = 0
            last_frame_time = start_time
            
            while True:
                # Vérifier si on doit s'arrêter
                with self.lock:
                    if session_id not in self.recordings or self.recordings[session_id].status == 'stopping':
                        break
                
                # Vérifier la durée maximale
                if time.time() - start_time > self.max_recording_duration:
                    break
                
                # Récupérer un frame
                success, frame = camera.get_frame()
                
                if not success or frame is None:
                    time.sleep(0.01)  # Pause courte pour éviter CPU 100%
                    continue
                
                # Écrire le frame
                out.write(frame)
                frame_count += 1
                
                # Respecter le FPS cible
                current_time = time.time()
                target_time = last_frame_time + (1.0 / fps)
                if current_time < target_time:
                    time.sleep(target_time - current_time)
                
                last_frame_time = time.time()
            
            # Nettoyer les ressources
            out.release()
            
            logger.info(f"✅ Enregistrement OpenCV terminé: {session_id}, {frame_count} frames")
            
        except Exception as e:
            logger.error(f"❌ Erreur dans le thread OpenCV pour {session_id}: {e}")
            with self.lock:
                if session_id in self.recordings:
                    self.recordings[session_id].status = 'error'
                    self.recordings[session_id].error = str(e)
    
    def _finalize_recording(self, session_id: str) -> Dict[str, Any]:
        """Finalise l'enregistrement et crée l'entrée en base"""
        try:
            recording = self.recordings[session_id]
            
            # Vérifier que le fichier existe
            if not os.path.exists(recording.output_path):
                return {
                    'status': 'error',
                    'error': f"Fichier vidéo non trouvé: {recording.output_path}",
                    'message': "Erreur lors de la finalisation de l'enregistrement"
                }
            
            # Calculer la durée et la taille
            duration = int((datetime.now() - recording.start_time).total_seconds())
            file_size = self._get_file_size(recording.output_path)
            
            # Générer une miniature
            thumbnail_path = self._generate_thumbnail(recording.output_path, recording.session_id)
            
            # Préparer le nom de fichier pour Bunny CDN
            filename_for_bunny = f"video_{recording.session_id}.mp4"
            
            # Créer l'entrée vidéo en base de données
            with db.session.begin():
                # D'abord créer la vidéo avec URL temporaire locale
                video = Video(
                    title=recording.session_name,
                    file_url=f"/videos/{os.path.basename(recording.output_path)}",
                    thumbnail_url=f"/thumbnails/{recording.session_id}.jpg" if thumbnail_path else None,
                    duration=duration,
                    court_id=recording.court_id,
                    user_id=recording.user_id,
                    recorded_at=recording.start_time,
                    is_unlocked=False,  # Nécessite des crédits pour débloquer
                    credits_cost=10,    # Coût par défaut
                    file_size=file_size
                )
                
                db.session.add(video)
                # Flush pour obtenir l'ID
                db.session.flush()
                
                # Mettre à jour le nom du fichier avec l'ID de la vidéo
                filename_for_bunny = f"video_{video.id}.mp4"
                
                # Upload vers Bunny CDN
                try:
                    # Vérifier que le fichier existe
                    if os.path.exists(recording.output_path):
                        # Mise à jour immédiate pour petits fichiers, queue pour gros fichiers
                        file_size_mb = os.path.getsize(recording.output_path) / (1024 * 1024)
                        
                        if file_size_mb < 5:  # Moins de 5MB, upload immédiat
                            success, bunny_url = bunny_storage_service.upload_video_immediately(
                                video.id,
                                recording.output_path,
                                f"Video {video.id}"  # Titre pour Bunny Stream
                            )
                            if success:
                                logger.info(f"✅ Vidéo {video.id} uploadée immédiatement vers Bunny Stream: {bunny_url}")
                            else:
                                logger.error(f"❌ Erreur lors de l'upload immédiat vers Bunny Stream")
                        else:
                            # Pour les fichiers plus grands, on utilise la queue
                            # On définira l'URL quand l'upload sera terminé via le processus en arrière-plan
                            video.file_url = f"En cours d'upload... (ID: {video.id})"
                            
                            # Queue l'upload en arrière-plan avec plus de logs
                            logger.info(f"🔄 Ajout de la vidéo {video.id} à la queue d'upload vers Bunny Stream")
                            upload_id = bunny_storage_service.queue_upload(
                                local_path=recording.output_path,
                                title=f"Video {video.id}",
                                collection=f"video_{video.id}",
                                metadata={'video_id': video.id}
                            )
                            logger.info(f"✅ Vidéo {video.id} en cours d'upload vers Bunny Stream (ID: {upload_id})")
                    else:
                        logger.error(f"❌ Fichier vidéo non trouvé pour upload: {recording.output_path}")
                except Exception as e:
                    logger.error(f"❌ Erreur lors de la préparation de l'upload Bunny CDN: {str(e)}")
                    # Garder l'URL locale en cas d'erreur
                    logger.info(f"ℹ️ Conservation de l'URL locale pour la vidéo {video.id}: {video.file_url}")
                
                # Upload également la miniature si disponible
                if thumbnail_path:
                    try:
                        # Pour les miniatures, on garde un nom de fichier simple pour Bunny Stream
                        thumbnail_title = f"Thumbnail {video.id}"
                        bunny_storage_service.queue_upload(
                            local_path=thumbnail_path,
                            title=thumbnail_title,
                            collection=f"thumbnails"
                        )
                        # L'URL de la miniature sera mise à jour automatiquement par le processus d'upload
                        # On garde l'URL locale en attendant
                        video.thumbnail_url = f"/static/thumbnails/thumbnail_{video.id}.jpg"
                    except Exception as e:
                        logger.error(f"❌ Erreur lors de l'upload de la miniature: {e}")
                        # Garder l'URL locale en cas d'erreur
            
            logger.info(f"📊 Vidéo enregistrée en base: {video.id} - Durée: {duration}s - Taille: {file_size} octets")
            
            return {
                'status': 'completed',
                'video_id': video.id,
                'video_filename': os.path.basename(recording.output_path),
                'duration': duration,
                'file_size': file_size,
                'thumbnail_url': video.thumbnail_url,
                'message': f"Enregistrement terminé: {recording.session_name}"
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la finalisation: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': "Erreur lors de la finalisation de l'enregistrement"
            }
    
    def _generate_thumbnail(self, video_path: str, session_id: str) -> Optional[str]:
        """Génère une miniature pour la vidéo"""
        try:
            thumbnail_filename = f"{session_id}.jpg"
            thumbnail_path = str(self.thumbnails_path / thumbnail_filename)
            
            # Utiliser FFmpeg pour générer la miniature (plus fiable)
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', '00:00:01',  # Prendre une frame à 1 seconde
                '-vframes', '1',
                '-q:v', '2',        # Haute qualité
                thumbnail_path
            ]
            
            try:
                result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, timeout=10)
                if os.path.exists(thumbnail_path):
                    logger.info(f"🖼️ Miniature générée: {thumbnail_path}")
                    return thumbnail_path
            except Exception as e:
                logger.warning(f"⚠️ Erreur FFmpeg pour miniature: {e}, fallback vers OpenCV")
                return self._generate_thumbnail_opencv(video_path, thumbnail_path)
                
        except Exception as e:
            logger.error(f"❌ Erreur génération miniature: {e}")
            return None
    
    def _generate_thumbnail_opencv(self, video_path: str, thumbnail_path: str) -> Optional[str]:
        """Génère une miniature avec OpenCV (fallback)"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise RuntimeError(f"Impossible d'ouvrir la vidéo: {video_path}")
            
            # Aller à 1 seconde
            cap.set(cv2.CAP_PROP_POS_MSEC, 1000)
            
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(thumbnail_path, frame)
                cap.release()
                logger.info(f"🖼️ Miniature OpenCV générée: {thumbnail_path}")
                return thumbnail_path
            else:
                cap.release()
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur miniature OpenCV: {e}")
            return None
    
    def _get_file_size(self, file_path: str) -> int:
        """Obtient la taille du fichier en octets"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0
    
    def _cleanup_recording(self, session_id: str):
        """Nettoie les ressources d'un enregistrement"""
        with self.lock:
            # Arrêter le processus FFmpeg si présent
            if session_id in self.recording_processes:
                try:
                    self.recording_processes[session_id].terminate()
                except:
                    pass
                del self.recording_processes[session_id]
            
            # Arrêter le stream caméra si présent
            if session_id in self.camera_streams:
                try:
                    self.camera_streams[session_id].stop()
                except:
                    pass
                del self.camera_streams[session_id]
            
            # Supprimer l'enregistrement si présent
            if session_id in self.recordings:
                del self.recordings[session_id]
    
    def _monitoring_loop(self):
        """Boucle de surveillance des enregistrements actifs"""
        while True:
            try:
                time.sleep(30)  # Vérifier toutes les 30 secondes
                
                with self.lock:
                    # Vérifier les enregistrements actifs
                    sessions_to_check = list(self.recordings.keys())
                
                for session_id in sessions_to_check:
                    try:
                        with self.lock:
                            if session_id not in self.recordings:
                                continue
                                
                            recording = self.recordings[session_id]
                            
                            # Vérifier si l'enregistrement dure depuis trop longtemps
                            current_duration = (datetime.now() - recording.start_time).total_seconds()
                            if current_duration > self.max_recording_duration:
                                logger.warning(f"⚠️ Enregistrement {session_id} a dépassé la durée maximale, arrêt automatique")
                                # Arrêter de façon asynchrone pour ne pas bloquer le monitoring
                                self.thread_pool.submit(self.stop_recording, session_id)
                            
                            # Vérifier si le processus FFmpeg est encore en vie
                            if session_id in self.recording_processes:
                                process = self.recording_processes[session_id]
                                if process.poll() is not None:
                                    logger.warning(f"⚠️ Le processus FFmpeg pour {session_id} s'est terminé prématurément")
                                    recording.status = 'error'
                                    recording.error = "Processus FFmpeg terminé prématurément"
                                    # Finaliser et nettoyer
                                    self.thread_pool.submit(self.stop_recording, session_id)
                            
                    except Exception as e:
                        logger.error(f"❌ Erreur lors de la surveillance de {session_id}: {e}")
                
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle de surveillance: {e}")

# Instance globale du service
video_capture_service = VideoCaptureService()
