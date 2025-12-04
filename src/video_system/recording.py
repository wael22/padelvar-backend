"""
Video Recorder - Enregistrement FFmpeg Stable (Reference Implementation)
========================================================================

Implémentation basée sur le code de référence 'camera-recorder':
- Threaded logging pour éviter blocages
- Gestion robuste des signaux (CTRL_BREAK_EVENT)
- Résolution intelligente du chemin FFmpeg
- Logique de fallback pour l'URL d'entrée (Source vs Proxy)
"""

import logging
import subprocess
import time
import signal
import sys
import os
import shutil
import threading
import io
import platform
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from .config import VideoConfig
from .session_manager import VideoSession

logger = logging.getLogger(__name__)


class VideoRecorder:
    """Enregistreur vidéo avec FFmpeg (Reference Implementation)"""
    
    def __init__(self):
        self.active_recordings: Dict[str, dict] = {}
        logger.info("🎬 VideoRecorder initialisé (Reference Logic)")
    
    def _resolve_ffmpeg(self) -> str:
        """Résoudre le chemin de l'exécutable FFmpeg de manière robuste"""
        ffmpeg_path = VideoConfig.FFMPEG_PATH
        try:
            if os.path.isabs(ffmpeg_path):
                if not Path(ffmpeg_path).exists():
                    # Essayer avec .exe sur Windows
                    if platform.system() == "Windows" and not Path(ffmpeg_path + ".exe").exists():
                        raise FileNotFoundError(ffmpeg_path)
                return ffmpeg_path
            else:
                resolved = shutil.which(ffmpeg_path)
                if not resolved and platform.system() == "Windows":
                    resolved = shutil.which(ffmpeg_path + ".exe")
                if not resolved:
                    raise FileNotFoundError(ffmpeg_path)
                return resolved
        except FileNotFoundError:
            logger.error(f"ffmpeg executable not found: '{ffmpeg_path}'")
            raise

    def start_recording(
        self,
        session: VideoSession,
        duration_seconds: int
    ) -> bool:
        """
        Démarrer un enregistrement en utilisant la logique de référence
        """
        session_id = session.session_id
        
        if session_id in self.active_recordings:
            logger.warning(f"⚠️ Enregistrement déjà actif pour {session_id}")
            return False
            
        logger.info(f"🎬 Démarrage enregistrement {session_id}")
        
        # 1. Déterminer l'URL d'entrée (Logique de référence)
        # On utilise le proxy local pour stabiliser le flux (FPS constant)
        input_url = session.local_url

            
        # Note: La référence tente ici de démarrer un proxy local dédié.
        # Dans notre architecture, le proxy est géré par SessionManager.
        # Si le proxy de session est prêt et stable, on pourrait l'utiliser,
        # mais pour l'instant on respecte la logique "MJPEG -> Direct".
        
        # 2. Préparer chemins
        video_dir = VideoConfig.get_video_dir(session.club_id)
        output_path = video_dir / f"{session_id}.mp4"
        log_path = VideoConfig.get_log_path(session_id)
        
        try:
            ffmpeg_exec = self._resolve_ffmpeg()
        except Exception as e:
            logger.error(f"❌ Erreur FFmpeg: {e}")
            return False

        # 3. Construire la commande (Style référence)
        cmd = [
            ffmpeg_exec,
            "-hide_banner",
            "-loglevel", "info",
            "-i", input_url,
            "-t", str(duration_seconds),
            "-c:v", "libx264",
            "-preset", VideoConfig.VIDEO_PRESET,
            "-crf", str(VideoConfig.VIDEO_CRF),
            "-c:a", "aac",  # Tenter d'inclure l'audio comme dans la référence
            "-y",
            str(output_path)
        ]
        
        logger.info(f"📝 Commande FFmpeg: {' '.join(cmd)}")
        
        try:
            # 4. Lancer le processus
            creationflags = 0
            if platform.system() == "Windows":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
                
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags
            )
            
            # 5. Threaded Logging (Logique de référence)
            # Permet de ne pas bloquer et de logger stderr/stdout en temps réel
            try:
                log_file = open(log_path, 'a', encoding='utf-8', errors='replace')
            except Exception:
                log_file = None
                
            def _log_stream(stream, log_fn, sid, fh=None):
                if not stream: return
                try:
                    text_stream = io.TextIOWrapper(stream, encoding='utf-8', errors='replace')
                    for line in text_stream:
                        line = line.rstrip('\n')
                        if line:
                            try:
                                if fh:
                                    fh.write(line + '\n')
                                    fh.flush()
                            except Exception: pass
                            # On ne loggue pas tout dans la console pour éviter le spam, juste dans le fichier
                            # Sauf erreurs ou infos importantes
                            if "Error" in line or "error" in line:
                                log_fn(f"[ffmpeg][{sid}] {line}")
                except Exception as e:
                    logger.debug(f"Error reading ffmpeg stream: {e}")

            threading.Thread(target=_log_stream, args=(process.stderr, logger.warning, session_id, log_file), daemon=True).start()
            threading.Thread(target=_log_stream, args=(process.stdout, logger.info, session_id, log_file), daemon=True).start()
            
            # Thread pour fermer le fichier log à la fin
            def _close_log_when_done(p, fh):
                try:
                    p.wait()
                finally:
                    if fh: fh.close()
            
            threading.Thread(target=_close_log_when_done, args=(process, log_file), daemon=True).start()
            
            # Enregistrer état
            self.active_recordings[session_id] = {
                'process': process,
                'output_path': output_path,
                'start_time': datetime.now(),
                'duration_seconds': duration_seconds,
                'pid': process.pid
            }
            
            session.recording_process = process
            session.recording_active = True
            session.recording_path = output_path
            
            logger.info(f"✅ Enregistrement démarré (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur démarrage enregistrement: {e}")
            return False

    def stop_recording(self, session_id: str) -> Optional[str]:
        """Arrêter l'enregistrement (Logique de référence)"""
        info = self.active_recordings.get(session_id)
        if not info:
            logger.warning(f"⚠️ Pas d'enregistrement actif pour {session_id}")
            return None
            
        process = info['process']
        output_path = info['output_path']
        
        logger.info(f"🛑 Arrêt enregistrement {session_id} (PID: {process.pid})")
        
        try:
            # Signal handling robuste (Reference logic)
            if platform.system() == "Windows":
                try:
                    # Envoyer CTRL_BREAK_EVENT
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    kernel32.GenerateConsoleCtrlEvent(1, process.pid)
                    logger.info(f"Sent CTRL_BREAK_EVENT to PID {process.pid}")
                except Exception as e:
                    logger.warning(f"Failed to send CTRL_BREAK_EVENT: {e}, using terminate()")
                    process.terminate()
            else:
                process.send_signal(signal.SIGINT)
                
            try:
                process.wait(timeout=10)
                logger.info(f"Recording process {process.pid} terminated gracefully")
            except subprocess.TimeoutExpired:
                logger.warning(f"Recording process did not stop, killing")
                process.kill()
                process.wait(timeout=5)
                
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            try: process.kill() 
            except: pass
            
        finally:
            if session_id in self.active_recordings:
                del self.active_recordings[session_id]
                
        # Vérification finale
        if output_path.exists() and output_path.stat().st_size > 1000:
            logger.info(f"✅ Enregistrement terminé: {output_path}")
            return str(output_path)
        else:
            logger.error(f"❌ Fichier vidéo vide ou manquant: {output_path}")
            return None

    def get_recording_status(self, session_id: str) -> Optional[dict]:
        info = self.active_recordings.get(session_id)
        if not info: return None
        
        process = info['process']
        elapsed = (datetime.now() - info['start_time']).total_seconds()
        is_active = process.poll() is None
        
        return {
            'session_id': session_id,
            'active': is_active,
            'pid': info['pid'],
            'elapsed_seconds': int(elapsed),
            'duration_seconds': info['duration_seconds'],
            'output_path': str(info['output_path'])
        }

    def cleanup_all(self):
        ids = list(self.active_recordings.keys())
        for sid in ids:
            self.stop_recording(sid)

# Instance globale
video_recorder = VideoRecorder()
