"""
Service de capture vidéo PadelVar - SOLUTION DIRECTE QUI MARCHE
Version avec arrêt propre FFmpeg pour éviter la corruption
"""
import os
import time
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class DirectVideoCaptureService:
    """Service qui reproduit EXACTEMENT la méthode qui marche"""
    
    def __init__(self):
        self.active_recordings = {}
        # Configuration FFmpeg validée
        ffmpeg_dir = r"C:\ffmpeg\ffmpeg-7.1.1-essentials_build\bin"
        self.ffmpeg_path = os.path.join(ffmpeg_dir, "ffmpeg.exe")
        
    def start_recording(self, session_id, camera_url, output_path,
                        max_duration, user_id, court_id,
                        session_name="Enregistrement",
                        video_quality="direct"):
        """Lance l'enregistrement CONTINU dès le start"""
        try:
            # Forcer extension .mp4
            if not output_path.endswith('.mp4'):
                output_path = os.path.splitext(output_path)[0] + '.mp4'
                
            # Assurer que le dossier existe
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # URL validée qui marche
            default_camera = "http://212.231.225.55:88/axis-cgi/mjpg/video.cgi"
            camera_url = camera_url or default_camera
            
            # COMMANDE FFmpeg pour enregistrement (5 minutes max)
            # FFmpeg s'arrêtera naturellement après 5 minutes
            recording_duration = 300  # 5 minutes maximum
            
            cmd = [
                self.ffmpeg_path,
                "-nostdin",
                "-y",
                "-i", camera_url,
                "-t", str(recording_duration),
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-profile:v", "baseline",
                "-level", "3.0",
                "-pix_fmt", "yuv420p",
                "-crf", "28",
                "-maxrate", "1000k",
                "-bufsize", "2000k",
                "-g", "30",
                "-r", "15",
                "-f", "mp4",
                "-movflags", "+faststart",
                output_path
            ]
            
            logger.info(f"🎬 DÉBUT enregistrement CONTINU: {session_id}")
            logger.info(f"📁 Fichier: {output_path}")
            
            # ➡️ LANCER FFmpeg IMMÉDIATEMENT
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 💾 Stocker les infos de session
            self.active_recordings[session_id] = {
                'process': process,
                'output_path': output_path,
                'start_time': time.time(),
                'user_id': user_id,
                'court_id': court_id,
                'session_name': session_name,
                'max_duration': max_duration,
                'camera_url': camera_url
            }
            
            logger.info(f"✅ FFmpeg PID: {process.pid}")
            
            return {
                'success': True,
                'session_id': session_id,
                'quality': video_quality,
                'message': f'Enregistrement CONTINU {video_quality} démarré'
            }
            
        except Exception as e:
            logger.error(f"Erreur start_recording CONTINU: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }

    def stop_recording(self, session_id):
        """Arrête l'enregistrement et attend que FFmpeg termine"""
        if session_id not in self.active_recordings:
            return {'success': False, 'error': 'Session non trouvée'}
            
        recording_info = self.active_recordings[session_id]
        
        try:
            # 🕐 Calculer la durée RÉELLE
            real_duration = int(time.time() - recording_info['start_time'])
            logger.info(f"🕐 Durée réelle: {real_duration} secondes")
            
            # 🎯 Récupérer le processus FFmpeg
            process = recording_info.get('process')
            if process and process.poll() is None:  # Si encore en cours
                logger.info(f"⏰ Arrêt propre FFmpeg: {session_id}")
                
                # 🛑 Envoyer signal d'arrêt PROPRE à FFmpeg
                try:
                    # Sur Windows, terminate() envoie SIGTERM
                    process.terminate()
                    logger.info("📨 Signal SIGTERM envoyé à FFmpeg")
                    
                    # ⏳ Attendre que FFmpeg termine proprement (max 30s)
                    process.wait(timeout=30)
                    logger.info("✅ FFmpeg terminé proprement")
                    
                except subprocess.TimeoutExpired:
                    logger.warning(
                        "⚠️ FFmpeg ne répond pas au SIGTERM, kill forcé"
                    )
                    process.kill()
                    process.wait()
                except Exception as e:
                    logger.error(f"❌ Erreur arrêt FFmpeg: {e}")
                    try:
                        process.kill()
                        process.wait()
                    except Exception:
                        pass
            
            # 🔄 Attendre que le fichier soit complètement écrit
            logger.info("⏳ Attente finalisation fichier...")
            time.sleep(3)  # Plus de temps pour la finalisation
            
            # ✅ Vérifier que le fichier existe et a du contenu
            output_path = recording_info['output_path']
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info(f"📁 Fichier final: {file_size:,} bytes")
                
                if file_size > 1000:  # Plus de 1KB
                    message = (f"Vidéo créée: {real_duration}s, "
                               f"{file_size:,} bytes")
                    result = {
                        'success': True,
                        'file_path': output_path,
                        'output_file': output_path,
                        'session_id': session_id,
                        'duration': real_duration,
                        'file_size': file_size,
                        'quality': recording_info.get('quality', 'direct'),
                        'file_exists': True,
                        'message': message
                    }
                else:
                    logger.error(f"❌ Fichier trop petit: {file_size} bytes")
                    result = {
                        'success': False,
                        'error': f'Fichier corrompu: {file_size} bytes',
                        'session_id': session_id
                    }
            else:
                logger.error(f"❌ Fichier non trouvé: {output_path}")
                result = {
                    'success': False,
                    'error': 'Fichier vidéo non créé',
                    'session_id': session_id
                }
            
            # 🧹 Nettoyer la session
            del self.active_recordings[session_id]
            return result
            
        except Exception as e:
            logger.error(f"Erreur stop_recording: {e}")
            # Nettoyage d'urgence
            if session_id in self.active_recordings:
                del self.active_recordings[session_id]
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    def get_active_recordings(self):
        """Retourne la liste des enregistrements actifs"""
        return list(self.active_recordings.keys())
    
    def is_recording(self, session_id):
        """Vérifie si une session est en cours d'enregistrement"""
        return session_id in self.active_recordings
        
    def cleanup_finished_recordings(self):
        """Nettoie les enregistrements terminés"""
        to_remove = []
        for session_id, info in self.active_recordings.items():
            process = info.get('process')
            if process and process.poll() is not None:
                logger.info(f"🧹 Nettoyage session terminée: {session_id}")
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del self.active_recordings[session_id]
            
        return len(to_remove)
