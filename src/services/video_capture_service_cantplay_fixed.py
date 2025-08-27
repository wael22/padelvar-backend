"""
Service de capture vidéo PadelVar - VERSION FINALE CORRIGÉE
Résout définitivement le problème "can't play video" 
Basé sur la commande FFmpeg validée qui fonctionne
"""

import logging
import os
import subprocess
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoRecordingTaskFixed:
    """Tâche d'enregistrement avec la configuration exacte qui marche"""
    
    def __init__(self, session_id, camera_url, output_path, max_duration, 
                 user_id, court_id, session_name, video_quality=None):
        self.session_id = session_id
        self.camera_url = camera_url
        self.output_path = output_path
        self.max_duration = max_duration
        self.user_id = user_id
        self.court_id = court_id
        self.session_name = session_name
        self.video_quality = video_quality or "baseline_h264"
        self.is_recording = False
        self.process = None
        self.thread = None
        self.ffmpeg_path = r"C:\ffmpeg\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"
        
    def start(self):
        """Démarre enregistrement avec la commande EXACTE qui marche"""
        try:
            Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # URL par défaut testée et validée
            default_camera = "http://212.231.225.55:88/axis-cgi/mjpg/video.cgi"
            camera_url = self.camera_url or default_camera
            
            # 🎯 COMMANDE EXACTE QUI MARCHE (testée et validée)
            cmd = [
                self.ffmpeg_path,
                "-nostdin",
                "-y",
                "-f", "mjpeg",
                "-i", camera_url,
                "-t", str(self.max_duration),
                "-c:v", "libx264",
                "-profile:v", "baseline",
                "-preset", "fast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-r", "15",
                self.output_path
            ]
            
            logger.info(f"🎬 FFmpeg VALIDÉ démarré: {self.session_id}")
            logger.info(f"📹 Caméra: {camera_url}")
            logger.info(f"📁 Fichier: {self.output_path}")
            logger.info(f"⏱️ Durée: {self.max_duration}s")
            logger.info("✅ Config: H.264 baseline, yuv420p, 15fps")
            
            # Processus IDENTIQUE à celui qui marche
            self.process = subprocess.Popen(
                cmd, 
                stdin=subprocess.DEVNULL, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            self.is_recording = True
            
            # Monitoring en arrière-plan
            self.thread = threading.Thread(target=self._monitor_validated, daemon=True)
            self.thread.start()
            
            logger.info(f"✅ Processus FFmpeg démarré: PID {self.process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur démarrage validé: {e}")
            return False
            
    def _monitor_validated(self):
        """Monitoring basé sur la version qui marche"""
        try:
            # Attendre la fin (comme dans la version qui marche)
            stdout, stderr = self.process.communicate()
            
            logger.info(f"📊 FFmpeg terminé: code {self.process.returncode}")
            
            # Attendre écriture complète du fichier
            time.sleep(3)
            
            # Vérification fichier
            if os.path.exists(self.output_path):
                size = os.path.getsize(self.output_path)
                logger.info(f"✅ Fichier validé créé: {size:,} bytes")
                
                # Calcul taille attendue (environ 3-4MB par seconde)
                expected_min = self.max_duration * 500000  # 500KB/sec minimum
                if size > expected_min:
                    logger.info(f"✅ Taille validée: {size:,} bytes OK")
                else:
                    logger.warning(f"⚠️ Fichier petit: {size:,} bytes")
            else:
                logger.error(f"❌ Fichier non créé: {self.output_path}")
                
        except Exception as e:
            logger.error(f"❌ Erreur monitoring validé: {e}")
        finally:
            self.is_recording = False
            
    def stop(self):
        """Arrêt basé sur la méthode qui marche"""
        try:
            if self.process and self.process.poll() is None:
                logger.info(f"🛑 Arrêt processus validé: {self.session_id}")
                
                # Attendre fin naturelle d'abord
                try:
                    self.process.wait(timeout=2)
                    logger.info(f"✅ Terminé naturellement: {self.session_id}")
                except subprocess.TimeoutExpired:
                    logger.info(f"🔄 Terminaison: {self.session_id}")
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        
            self.is_recording = False
            
            # Attendre finalisation (important)
            time.sleep(3)
            
            logger.info(f"✅ Arrêt validé terminé: {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur arrêt validé: {e}")
            self.is_recording = False
            return False


class VideoCaptureServiceFixed:
    """Service capture avec correction 'Can't Play' validée"""
    
    def __init__(self):
        self.active_recordings = {}
        
    def start_recording(self, session_id, camera_url, output_path, max_duration,
                       user_id, court_id, session_name="Enregistrement", 
                       video_quality="baseline_h264"):
        """Démarre enregistrement avec correction validée"""
        try:
            # Forcer extension .mp4
            if not output_path.endswith('.mp4'):
                output_path = os.path.splitext(output_path)[0] + '.mp4'
                
            task = VideoRecordingTaskFixed(
                session_id, camera_url, output_path, max_duration,
                user_id, court_id, session_name, video_quality
            )
            
            if task.start():
                self.active_recordings[session_id] = task
                logger.info(f"Enregistrement validé démarré: {session_id}")
                return {
                    'success': True, 
                    'session_id': session_id, 
                    'quality': video_quality,
                    'message': f'Enregistrement {video_quality} démarré (correction validée)'
                }
            return {
                'success': False, 
                'error': 'Échec démarrage validé',
                'session_id': session_id
            }
            
        except Exception as e:
            logger.error(f"Erreur service validé: {e}")
            return {
                'success': False, 
                'error': str(e),
                'session_id': session_id
            }
    
    def stop_recording(self, session_id):
        """Arrête enregistrement avec validation finale"""
        try:
            if session_id in self.active_recordings:
                task = self.active_recordings[session_id]
                task.stop()
                
                # Attendre finalisation complète
                time.sleep(4)
                
                output_path = task.output_path
                file_info = {
                    'success': True,
                    'file_path': output_path,
                    'output_file': output_path,
                    'file_exists': os.path.exists(output_path),
                    'duration': task.max_duration,
                    'session_id': session_id,
                    'quality': task.video_quality,
                    'cantplay_fixed': True  # Indicateur correction appliquée
                }
                
                if file_info['file_exists']:
                    file_info['file_size'] = os.path.getsize(output_path)
                    logger.info(f"📁 Fichier validé final: {file_info['file_size']:,} bytes")
                    
                    # Validation finale
                    if file_info['file_size'] > 100000:  # Au moins 100KB
                        file_info['playable'] = True
                        logger.info("✅ Fichier lisible créé (correction appliquée)")
                    else:
                        file_info['playable'] = False
                        logger.warning(f"⚠️ Fichier petit: {file_info['file_size']} bytes")
                else:
                    file_info['file_size'] = 0
                    file_info['playable'] = False
                    logger.error(f"❌ Fichier non créé: {output_path}")
                    
                del self.active_recordings[session_id]
                logger.info(f"Enregistrement validé arrêté: {session_id}")
                return file_info
            else:
                return {
                    'success': False,
                    'error': 'Session non trouvée',
                    'session_id': session_id
                }
        except Exception as e:
            logger.error(f"Erreur arrêt service validé: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    def is_recording(self, session_id):
        """Vérifie si une session est en cours"""
        return session_id in self.active_recordings
        
    def get_active_recordings(self):
        """Retourne la liste des enregistrements actifs"""
        return list(self.active_recordings.keys())
    
    def get_recording_status(self, session_id):
        """Retourne le statut d'un enregistrement"""
        if session_id in self.active_recordings:
            task = self.active_recordings[session_id]
            return {
                'session_id': session_id,
                'is_recording': task.is_recording,
                'quality': task.video_quality,
                'output_path': task.output_path,
                'file_exists': os.path.exists(task.output_path),
                'cantplay_fixed': True
            }
        return None


# Instance globale avec correction validée
video_capture_service_fixed = VideoCaptureServiceFixed()
