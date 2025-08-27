"""
Service de stockage vidéo Bunny CDN - Version corrigée
====================================================

Service pour l'upload et la gestion des vidéos vers Bunny Stream CDN
- API HTTP optimisée
- Gestion d'erreurs robuste
- Upload asynchrone
- Retry automatique
"""

import os
import logging
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import requests

# Configuration du logger
logger = logging.getLogger(__name__)


class BunnyStorageService:
    """Service de gestion du stockage vidéo sur Bunny Stream CDN"""
    
    def __init__(self):
        """Initialise le service de stockage Bunny Stream"""
        self.upload_queue = []
        self.is_uploading = False
        self.upload_thread = None
        self.lock = threading.RLock()
        
        # Configuration depuis les variables d'environnement
        self.api_key = os.environ.get(
            'BUNNY_API_KEY', 
            'dea74bd3-cb95-40f6-8b25e0cb6901-c108-4bf1'
        )
        self.library_id = os.environ.get('BUNNY_LIBRARY_ID', '475694')
        self.cdn_hostname = os.environ.get(
            'BUNNY_CDN_HOSTNAME', 
            'vz-f2c97d0e-5d4.b-cdn.net'
        )
        
        # Configuration de l'API
        self.api_base_url = (
            f"https://video.bunnycdn.com/library/{self.library_id}"
        )
        
        # Configuration des headers API
        self.headers = {
            "AccessKey": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Configuration de service
        self.config = {
            "api_key": self.api_key,
            "library_id": self.library_id,
            "storage_zone": self.cdn_hostname,
            "api_base_url": self.api_base_url
        }
        
        logger.info("✅ BunnyStorageService initialisé")
        logger.info(f"📚 Library ID: {self.library_id}")
        logger.info(f"🌐 CDN Hostname: {self.cdn_hostname}")

    def upload_file(self, local_path: str, title: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Upload un fichier vidéo vers Bunny Stream CDN
        
        Args:
            local_path: Chemin du fichier local
            title: Titre de la vidéo (optionnel)
            
        Returns:
            Tuple (success, video_url)
        """
        
        try:
            if not os.path.exists(local_path):
                logger.error(f"Fichier non trouvé: {local_path}")
                return False, None
            
            if not title:
                title = os.path.basename(local_path)
            
            logger.info(f"🚀 Début upload vers Bunny: {title}")
            
            # Étape 1: Créer la vidéo dans Bunny Stream
            create_data = {
                "title": title
                # NOTE: Ne pas inclure collectionId - cause l'erreur
                # "Collection does not exist"
            }
            
            response = requests.post(
                f"{self.api_base_url}/videos",
                headers=self.headers,
                json=create_data,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f"Erreur création vidéo: {response.status_code}"
                logger.error(f"{error_msg} - {response.text}")
                return False, None
            
            video_data = response.json()
            video_id = video_data.get("guid")
            
            if not video_id:
                logger.error(f"Pas d'ID vidéo: {video_data}")
                return False, None
            
            logger.info(f"✅ Vidéo créée: {video_id}")
            
            # Étape 2: Upload du fichier vidéo
            upload_url = f"{self.api_base_url}/videos/{video_id}"
            
            with open(local_path, 'rb') as video_file:
                upload_headers = {
                    "AccessKey": self.api_key,
                    "Content-Type": "video/mp4"
                }
                
                logger.info(f"📤 Upload du fichier...")
                
                upload_response = requests.put(
                    upload_url,
                    headers=upload_headers,
                    data=video_file,
                    timeout=300  # 5 minutes timeout pour l'upload
                )
                
                if upload_response.status_code in [200, 201]:
                    # Générer l'URL de la vidéo
                    video_url = f"https://{self.cdn_hostname}/{video_id}/play.mp4"
                    
                    logger.info(f"✅ Upload réussi: {video_id}")
                    logger.info(f"🔗 URL: {video_url}")
                    
                    return True, video_url
                else:
                    error_msg = f"Erreur upload: {upload_response.status_code}"
                    logger.error(f"{error_msg} - {upload_response.text}")
                    return False, None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur API upload {local_path}: {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Erreur inattendue upload {local_path}: {str(e)}")
            return False, None

    def queue_upload(self, local_path: str, title: Optional[str] = None, 
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Ajouter un fichier à la queue d'upload
        
        Args:
            local_path: Chemin du fichier
            title: Titre de la vidéo
            metadata: Métadonnées additionnelles
            
        Returns:
            ID de la tâche d'upload
        """
        
        task_id = f"upload_{int(time.time())}_{id(local_path)}"
        
        upload_task = {
            'task_id': task_id,
            'local_path': local_path,
            'title': title or os.path.basename(local_path),
            'metadata': metadata or {},
            'created_at': datetime.now(),
            'status': 'queued',
            'attempts': 0,
            'max_attempts': 3
        }
        
        with self.lock:
            self.upload_queue.append(upload_task)
            logger.info(f"📝 Tâche ajoutée à la queue: {task_id}")
            
            # Démarrer le worker si pas déjà actif
            if not self.is_uploading:
                self._start_upload_worker()
        
        return task_id

    def _start_upload_worker(self):
        """Démarrer le worker d'upload en arrière-plan"""
        
        if self.upload_thread and self.upload_thread.is_alive():
            return
        
        self.is_uploading = True
        self.upload_thread = threading.Thread(
            target=self._upload_worker,
            name="BunnyUploadWorker"
        )
        self.upload_thread.daemon = True
        self.upload_thread.start()
        
        logger.info("🏃 Worker d'upload démarré")

    def _upload_worker(self):
        """Worker pour traiter la queue d'upload"""
        
        try:
            while True:
                with self.lock:
                    if not self.upload_queue:
                        self.is_uploading = False
                        logger.info("💤 Queue vide, worker en pause")
                        break
                    
                    task = self.upload_queue.pop(0)
                
                # Traiter la tâche
                self._process_upload_task(task)
                
                # Pause entre les uploads
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Erreur dans le worker d'upload: {e}")
            self.is_uploading = False

    def _process_upload_task(self, task: Dict[str, Any]):
        """Traiter une tâche d'upload"""
        
        task_id = task['task_id']
        local_path = task['local_path']
        title = task['title']
        
        try:
            logger.info(f"🔄 Traitement tâche: {task_id}")
            
            task['status'] = 'uploading'
            task['attempts'] += 1
            
            # Tenter l'upload
            success, video_url = self.upload_file(local_path, title)
            
            if success:
                task['status'] = 'completed'
                task['video_url'] = video_url
                task['completed_at'] = datetime.now()
                
                logger.info(f"✅ Tâche terminée: {task_id}")
                
                # Optionnel: supprimer le fichier local après upload
                if task.get('delete_after_upload', False):
                    try:
                        os.remove(local_path)
                        logger.info(f"🗑️ Fichier local supprimé: {local_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur suppression: {e}")
                        
            else:
                # Retry si possible
                if task['attempts'] < task['max_attempts']:
                    task['status'] = 'retry'
                    
                    # Remettre en queue avec délai
                    with self.lock:
                        self.upload_queue.append(task)
                    
                    logger.warning(f"🔄 Retry tâche: {task_id} (tentative {task['attempts']})")
                    time.sleep(5)  # Délai avant retry
                    
                else:
                    task['status'] = 'failed'
                    task['failed_at'] = datetime.now()
                    
                    logger.error(f"❌ Tâche échouée: {task_id}")
                    
        except Exception as e:
            task['status'] = 'error'
            task['error'] = str(e)
            
            logger.error(f"❌ Erreur traitement tâche {task_id}: {e}")

    def get_queue_status(self) -> Dict[str, Any]:
        """Obtenir le statut de la queue d'upload"""
        
        with self.lock:
            return {
                'queue_size': len(self.upload_queue),
                'is_uploading': self.is_uploading,
                'worker_active': (self.upload_thread and 
                                self.upload_thread.is_alive()),
                'tasks': [
                    {
                        'task_id': task['task_id'],
                        'title': task['title'],
                        'status': task['status'],
                        'attempts': task['attempts'],
                        'created_at': task['created_at'].isoformat()
                    }
                    for task in self.upload_queue
                ]
            }

    def test_connection(self) -> Dict[str, Any]:
        """Tester la connexion à l'API Bunny"""
        
        try:
            logger.info("🔍 Test de connexion Bunny CDN...")
            
            response = requests.get(
                f"{self.api_base_url}/videos",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                video_count = len(data.get('items', []))
                
                logger.info(f"✅ Connexion OK - {video_count} vidéos")
                
                return {
                    'success': True,
                    'message': 'Connexion réussie',
                    'video_count': video_count,
                    'library_id': self.library_id,
                    'api_status': 'operational'
                }
            else:
                logger.error(f"❌ Erreur API: {response.status_code}")
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code}",
                    'message': 'Échec de connexion'
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur test connexion: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Erreur de connexion'
            }

    def list_videos(self, limit: int = 50) -> Dict[str, Any]:
        """Lister les vidéos sur Bunny CDN"""
        
        try:
            params = {
                'page': 1,
                'itemsPerPage': limit,
                'orderBy': 'date'
            }
            
            response = requests.get(
                f"{self.api_base_url}/videos",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                videos = data.get('items', [])
                
                video_list = []
                for video in videos:
                    video_info = {
                        'id': video.get('guid'),
                        'title': video.get('title'),
                        'status': video.get('status'),
                        'duration': video.get('length'),
                        'created': video.get('dateUploaded'),
                        'url': f"https://{self.cdn_hostname}/{video.get('guid')}/play.mp4"
                    }
                    video_list.append(video_info)
                
                return {
                    'success': True,
                    'videos': video_list,
                    'total_count': data.get('totalItems', len(videos)),
                    'current_page': data.get('currentPage', 1)
                }
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur liste vidéos: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def delete_video(self, video_id: str) -> bool:
        """Supprimer une vidéo de Bunny CDN"""
        
        try:
            response = requests.delete(
                f"{self.api_base_url}/videos/{video_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"✅ Vidéo supprimée: {video_id}")
                return True
            else:
                logger.error(f"❌ Erreur suppression {video_id}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur suppression vidéo {video_id}: {e}")
            return False

    def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Obtenir les informations d'une vidéo"""
        
        try:
            response = requests.get(
                f"{self.api_base_url}/videos/{video_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                video_data = response.json()
                return {
                    'id': video_data.get('guid'),
                    'title': video_data.get('title'),
                    'status': video_data.get('status'),
                    'duration': video_data.get('length'),
                    'file_size': video_data.get('storageSize'),
                    'created': video_data.get('dateUploaded'),
                    'url': f"https://{self.cdn_hostname}/{video_id}/play.mp4"
                }
            else:
                logger.error(f"❌ Vidéo non trouvée: {video_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur info vidéo {video_id}: {e}")
            return None


# Instance globale du service
bunny_storage_service = BunnyStorageService()
