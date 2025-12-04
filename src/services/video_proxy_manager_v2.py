"""
Video Proxy Manager - Production Ready
Gestion robuste des proxies RTSP avec allocation dynamique de ports
"""
import logging
import threading
import time
import socket
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import cv2

from src.recording_config.recording_config import config

logger = logging.getLogger(__name__)


class ProxyInstance:
    """Instance d'un proxy RTSP pour un terrain"""
    
    def __init__(self, terrain_id: int, camera_url: str, port: int):
        self.terrain_id = terrain_id
        self.camera_url = camera_url
        self.port = port
        self.rtsp_url = config.get_proxy_url(port, terrain_id)
        
        self.running = False
        self.capture_thread = None
        self.cap = None
        
        self.frames_captured = 0
        self.last_frame_time = None
        self.start_time = datetime.now()
        self.errors_count = 0
        
        # Lock pour thread-safety
        self.lock = threading.Lock()
    
    def validate_camera(self) -> Tuple[bool, str]:
        """
        Valider que la caméra est accessible et retourne des frames
        Lit VALIDATION_FRAMES_COUNT frames en moins de VALIDATION_TIMEOUT
        secondes
        
        Returns:
            (success: bool, message: str)
        """
        try:
            logger.info(
                f"🔍 Validation caméra terrain {self.terrain_id}: "
                f"{self.camera_url}"
            )
            
            # Tenter d'ouvrir le flux
            test_cap = cv2.VideoCapture(self.camera_url)
            
            if not test_cap.isOpened():
                return False, "Impossible d'ouvrir le flux caméra"
            
            # Lire N frames pour valider
            frames_read = 0
            start_time = time.time()
            
            for i in range(config.VALIDATION_FRAMES_COUNT):
                if time.time() - start_time > config.VALIDATION_TIMEOUT:
                    test_cap.release()
                    return (
                        False,
                        f"Timeout: {i} frames lues en "
                        f"{config.VALIDATION_TIMEOUT}s"
                    )
                
                ret, frame = test_cap.read()
                
                if ret and frame is not None:
                    frames_read += 1
                    logger.debug(
                        f"✓ Frame {i+1}/{config.VALIDATION_FRAMES_COUNT} "
                        f"lue: {frame.shape}"
                    )
                else:
                    test_cap.release()
                    return (
                        False,
                        f"Échec lecture frame {i+1}"
                    )
            
            test_cap.release()
            
            elapsed = time.time() - start_time
            logger.info(
                f"✅ Caméra validée: {frames_read} frames en "
                f"{elapsed:.1f}s"
            )
            
            return True, f"Validé: {frames_read} frames"
            
        except Exception as e:
            logger.error(
                f"❌ Erreur validation caméra terrain {self.terrain_id}: "
                f"{e}"
            )
            return False, f"Exception: {str(e)}"
    
    def start(self) -> bool:
        """
        Démarrer le proxy après validation
        
        Returns:
            success: bool
        """
        if self.running:
            logger.warning(
                f"⚠️ Proxy terrain {self.terrain_id} déjà actif"
            )
            return True
        
        # 1. Valider la caméra avant de démarrer
        success, message = self.validate_camera()
        
        if not success:
            logger.error(
                f"❌ Validation échouée terrain {self.terrain_id}: "
                f"{message}"
            )
            return False
        
        # 2. Ouvrir le flux de capture
        try:
            self.cap = cv2.VideoCapture(self.camera_url)
            
            if not self.cap.isOpened():
                logger.error(
                    f"❌ Échec ouverture capture terrain "
                    f"{self.terrain_id}"
                )
                return False
            
            # 3. Configurer le flux
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # 4. Démarrer le thread de capture
            self.running = True
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                daemon=True,
                name=f"Proxy-Terrain-{self.terrain_id}"
            )
            self.capture_thread.start()
            
            logger.info(
                f"✅ Proxy démarré terrain {self.terrain_id} sur port "
                f"{self.port}"
            )
            logger.info(f"📡 RTSP URL: {self.rtsp_url}")
            
            return True
            
        except Exception as e:
            logger.error(
                f"❌ Erreur démarrage proxy terrain {self.terrain_id}: "
                f"{e}"
            )
            self.running = False
            return False
    
    def _capture_loop(self):
        """Boucle de capture avec reconnexion automatique"""
        consecutive_failures = 0
        max_failures = 30  # 30 échecs = ~30s sans frame
        
        logger.info(
            f"🎬 Thread capture démarré: terrain {self.terrain_id}"
        )
        
        while self.running:
            try:
                # Lire une frame
                ret, frame = self.cap.read()
                
                if ret and frame is not None:
                    # Succès
                    with self.lock:
                        self.frames_captured += 1
                        self.last_frame_time = datetime.now()
                    
                    consecutive_failures = 0
                    
                    # Throttling FPS
                    time.sleep(1.0 / config.PROXY_CAPTURE_FPS)
                    
                else:
                    # Échec de lecture
                    consecutive_failures += 1
                    
                    if consecutive_failures >= max_failures:
                        logger.error(
                            f"❌ Trop d'échecs consécutifs terrain "
                            f"{self.terrain_id}: {consecutive_failures}"
                        )
                        
                        # Tenter reconnexion
                        if self._reconnect():
                            consecutive_failures = 0
                        else:
                            logger.critical(
                                f"💥 Impossible de reconnecter terrain "
                                f"{self.terrain_id}, arrêt du proxy"
                            )
                            self.running = False
                            break
                    
                    time.sleep(1.0)
                
            except Exception as e:
                logger.error(
                    f"❌ Erreur capture terrain {self.terrain_id}: {e}"
                )
                self.errors_count += 1
                time.sleep(1.0)
        
        logger.info(
            f"🛑 Thread capture arrêté: terrain {self.terrain_id}"
        )
    
    def _reconnect(self) -> bool:
        """
        Tenter de reconnecter à la caméra
        
        Returns:
            success: bool
        """
        logger.warning(
            f"🔄 Tentative reconnexion terrain {self.terrain_id}"
        )
        
        try:
            # Fermer l'ancien flux
            if self.cap:
                self.cap.release()
            
            # Attendre un peu
            time.sleep(2)
            
            # Rouvrir
            self.cap = cv2.VideoCapture(self.camera_url)
            
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                logger.info(
                    f"✅ Reconnexion réussie terrain {self.terrain_id}"
                )
                return True
            else:
                logger.error(
                    f"❌ Reconnexion échouée terrain {self.terrain_id}"
                )
                return False
                
        except Exception as e:
            logger.error(
                f"❌ Erreur reconnexion terrain {self.terrain_id}: {e}"
            )
            return False
    
    def stop(self):
        """Arrêter le proxy proprement"""
        logger.info(f"🛑 Arrêt proxy terrain {self.terrain_id}")
        
        self.running = False
        
        # Attendre la fin du thread
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5)
        
        # Libérer la capture
        if self.cap:
            self.cap.release()
            self.cap = None
        
        logger.info(
            f"✅ Proxy arrêté terrain {self.terrain_id}: "
            f"{self.frames_captured} frames capturées"
        )
    
    def get_stats(self) -> dict:
        """Obtenir les statistiques du proxy"""
        with self.lock:
            uptime = (datetime.now() - self.start_time).total_seconds()
            fps = (
                self.frames_captured / uptime
                if uptime > 0
                else 0
            )
            
            return {
                'terrain_id': self.terrain_id,
                'port': self.port,
                'rtsp_url': self.rtsp_url,
                'camera_url': self.camera_url,
                'running': self.running,
                'frames_captured': self.frames_captured,
                'last_frame_time': (
                    self.last_frame_time.isoformat()
                    if self.last_frame_time
                    else None
                ),
                'uptime_seconds': uptime,
                'fps': round(fps, 2),
                'errors_count': self.errors_count
            }


class VideoProxyManager:
    """
    Gestionnaire de proxies RTSP multi-terrains
    Allocation dynamique de ports, validation, monitoring
    """
    
    def __init__(self):
        self.proxies: Dict[int, ProxyInstance] = {}
        self.port_allocations: Dict[int, int] = {}  # terrain_id -> port
        self.lock = threading.Lock()
        
        logger.info("🎬 VideoProxyManager initialisé")
    
    def _is_port_available(self, port: int) -> bool:
        """Vérifier si un port est disponible"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((config.PROXY_HOST, port))
            sock.close()
            return result != 0  # Port libre si connexion échoue
        except Exception:
            return False
    
    def _allocate_port(self, terrain_id: int) -> Optional[int]:
        """
        Allouer un port libre pour un terrain
        
        Returns:
            port: int ou None si aucun port disponible
        """
        with self.lock:
            # Vérifier si déjà alloué
            if terrain_id in self.port_allocations:
                return self.port_allocations[terrain_id]
            
            # Chercher un port libre
            for port in config.PROXY_PORT_RANGE:
                # Vérifier si pas déjà utilisé par un autre terrain
                if port in self.port_allocations.values():
                    continue
                
                # Vérifier si le port est libre au niveau système
                if self._is_port_available(port):
                    self.port_allocations[terrain_id] = port
                    logger.info(
                        f"🔓 Port {port} alloué au terrain {terrain_id}"
                    )
                    return port
            
            logger.error(
                f"❌ Aucun port disponible dans la plage "
                f"{config.PROXY_PORT_START}-{config.PROXY_PORT_END}"
            )
            return None
    
    def _release_port(self, terrain_id: int):
        """Libérer le port d'un terrain"""
        with self.lock:
            if terrain_id in self.port_allocations:
                port = self.port_allocations[terrain_id]
                del self.port_allocations[terrain_id]
                logger.info(
                    f"🔐 Port {port} libéré (terrain {terrain_id})"
                )
    
    def start_proxy(
        self,
        terrain_id: int,
        camera_url: str
    ) -> Tuple[bool, Optional[str], str]:
        """
        Démarrer un proxy pour un terrain
        
        Args:
            terrain_id: ID du terrain
            camera_url: URL de la caméra IP
        
        Returns:
            (success: bool, rtsp_url: str ou None, message: str)
        """
        with self.lock:
            # Vérifier si proxy déjà actif
            if terrain_id in self.proxies:
                proxy = self.proxies[terrain_id]
                if proxy.running:
                    logger.info(
                        f"♻️ Proxy déjà actif terrain {terrain_id}"
                    )
                    return True, proxy.rtsp_url, "Proxy déjà actif"
        
        # Allouer un port
        port = self._allocate_port(terrain_id)
        
        if port is None:
            return (
                False,
                None,
                "Aucun port disponible dans la plage configurée"
            )
        
        # Créer l'instance du proxy
        proxy = ProxyInstance(terrain_id, camera_url, port)
        
        # Démarrer le proxy (avec validation intégrée)
        success = proxy.start()
        
        if success:
            with self.lock:
                self.proxies[terrain_id] = proxy
            
            return True, proxy.rtsp_url, "Proxy démarré avec succès"
        else:
            # Échec: libérer le port
            self._release_port(terrain_id)
            return (
                False,
                None,
                "Échec démarrage proxy (validation ou capture)"
            )
    
    def stop_proxy(self, terrain_id: int, immediate: bool = False):
        """
        Arrêter un proxy
        
        Args:
            terrain_id: ID du terrain
            immediate: Si True, arrêt immédiat. Sinon, délai configuré.
        """
        with self.lock:
            if terrain_id not in self.proxies:
                logger.warning(
                    f"⚠️ Aucun proxy actif pour terrain {terrain_id}"
                )
                return
            
            proxy = self.proxies[terrain_id]
        
        # Arrêter le proxy
        proxy.stop()
        
        # Libérer les ressources
        with self.lock:
            del self.proxies[terrain_id]
        
        # Libérer le port (après délai optionnel)
        if not immediate:
            # Attendre avant de libérer (autres enregistrements peuvent
            # utiliser)
            threading.Timer(
                config.PORT_RELEASE_DELAY,
                lambda: self._release_port(terrain_id)
            ).start()
            logger.info(
                f"⏳ Port sera libéré dans "
                f"{config.PORT_RELEASE_DELAY}s"
            )
        else:
            self._release_port(terrain_id)
    
    def get_proxy_url(self, terrain_id: int) -> Optional[str]:
        """Obtenir l'URL RTSP d'un proxy actif"""
        with self.lock:
            if terrain_id in self.proxies:
                return self.proxies[terrain_id].rtsp_url
            return None
    
    def get_all_stats(self) -> dict:
        """Obtenir les statistiques de tous les proxies"""
        with self.lock:
            return {
                'total_proxies': len(self.proxies),
                'ports_allocated': len(self.port_allocations),
                'proxies': [
                    proxy.get_stats()
                    for proxy in self.proxies.values()
                ]
            }
    
    def stop_all(self):
        """Arrêter tous les proxies"""
        logger.info("🛑 Arrêt de tous les proxies...")
        
        terrain_ids = list(self.proxies.keys())
        
        for terrain_id in terrain_ids:
            self.stop_proxy(terrain_id, immediate=True)
        
        logger.info("✅ Tous les proxies arrêtés")


# Instance globale (singleton)
_proxy_manager = None


def get_proxy_manager() -> VideoProxyManager:
    """Obtenir l'instance globale du ProxyManager"""
    global _proxy_manager
    
    if _proxy_manager is None:
        _proxy_manager = VideoProxyManager()
    
    return _proxy_manager
