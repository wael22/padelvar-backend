# PadelVar - Système Vidéo Stable

## 🏗️ Architecture

```
┌─────────────┐
│  Caméras IP │ (MJPEG / RTSP / HTTP)
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│ video_proxy_server.py │ ← Proxy Universel (Port 8080+)
│  - Connexion caméra   │
│  - Buffer frames      │
│  - Re-streaming local │
└──────┬───────────────┘
       │
       ├──────────────────┐
       │                  │
       ▼                  ▼
┌─────────┐        ┌──────────┐
│  FFmpeg │        │ Preview  │
│  → MP4  │        │ (MJPEG)  │
└─────────┘        └──────────┘
```

---

## 🎯 Caractéristiques

✅ **Un seul fichier MP4** par enregistrement (pas de segmentation)  
✅ **Proxy universel** pour tous les types de flux  
✅ **Multi-terrains** : plusieurs enregistrements simultanés  
✅ **Preview temps réel** via MJPEG stream  
✅ **Arrêt propre** (SIGINT/terminate)  
✅ **Reconnection automatique** si caméra coupe  
✅ **Sécurité & Permissions** par rôle utilisateur  
✅ **API REST complète**  

---

## 🚀 Démarrage Rapide

### 1. Installation

```bash
# Dépendances Python
pip install flask requests pillow opencv-python-headless

# Vérifier FFmpeg
ffmpeg -version
```

### 2. Démarrer le Backend

```bash
cd padelvar-backend-main
python -m flask run
```

### 3. Tester

```bash
# Santé du système
curl http://localhost:5000/api/video/health

# Créer une session (nécessite authentification)
curl -X POST http://localhost:5000/api/video/session/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"terrain_id": 1}'
```

---

## 📚 Modules Principaux

### `session_manager.py`
Gestion des sessions caméra :
- Validation caméra (MJPEG/RTSP)
- Création session + proxy
- Fermeture propre

### `proxy_manager.py`
Gestion des proxies vidéo :
- Allocation ports dynamique
- Démarrage/arrêt proxy
- Health check

### `video_proxy_server.py`
Proxy universel :
- Support MJPEG, RTSP, HTTP
- Buffer frames stable
- Multi-clients

### `recording.py`
Enregistrement FFmpeg :
- Commande FFmpeg optimisée
- Un seul fichier MP4
- Arrêt propre (SIGINT/terminate)
- Logs complets

### `preview.py`
Preview temps réel :
- WebSocket (à implémenter)
- HTTP MJPEG stream
- Snapshots JPEG

---

## 🔌 API Endpoints

### Sessions

#### `POST /api/video/session/create`
Créer une session caméra avec proxy.

**Body:**
```json
{
  "terrain_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "session": {
    "session_id": "sess_1_1701234567",
    "local_url": "http://127.0.0.1:8080/stream.mjpg",
    "proxy_port": 8080,
    "verified": true
  }
}
```

#### `POST /api/video/session/close`
Fermer une session (seulement si pas d'enregistrement actif).

#### `GET /api/video/session/list`
Lister toutes les sessions actives (filtrées selon le rôle).

---

### Enregistrement

#### `POST /api/video/record/start`
Démarrer un enregistrement.

**Body:**
```json
{
  "session_id": "sess_1_1701234567",
  "duration_minutes": 90
}
```

#### `POST /api/video/record/stop`
Arrêter un enregistrement.

**Body:**
```json
{
  "session_id": "sess_1_1701234567"
}
```

**Response:**
```json
{
  "success": true,
  "video_path": "/path/to/video.mp4"
}
```

#### `GET /api/video/record/status/<session_id>`
Obtenir le statut d'un enregistrement.

**Response:**
```json
{
  "success": true,
  "status": {
    "session_id": "sess_1_1701234567",
    "active": true,
    "elapsed_seconds": 120,
    "duration_seconds": 5400,
    "progress_percent": 2
  }
}
```

---

### Preview

#### `GET /api/preview/<session_id>/stream.mjpeg`
Stream MJPEG continu (pour `<img>` ou `<video>`).

```html
<img src="/api/preview/sess_1_1701234567/stream.mjpeg" />
```

#### `GET /api/preview/<session_id>/snapshot.jpg`
Snapshot JPEG unique.

```javascript
// Polling pour preview animée
setInterval(() => {
  document.getElementById('preview').src = 
    `/api/preview/${sessionId}/snapshot.jpg?t=${Date.now()}`;
}, 200); // 5 FPS
```

#### `GET /api/preview/<session_id>/info`
Informations sur le preview.

---

### Fichiers Vidéo

#### `GET /api/video/files/list?club_id=1`
Lister les vidéos d'un club.

#### `GET /api/video/files/<session_id>/download?club_id=1`
Télécharger une vidéo.

#### `DELETE /api/video/files/<session_id>/delete?club_id=1`
Supprimer une vidéo (admin uniquement).

---

### Health & Maintenance

#### `GET /api/video/health`
Santé du système vidéo.

#### `POST /api/video/cleanup`
Nettoyer les sessions orphelines (admin uniquement).

---

## 🔒 Sécurité & Permissions

### Rôles Utilisateur

- **SUPER_ADMIN** : Accès complet
- **CLUB_ADMIN** : Gestion de son club
- **PLAYER** : Gestion de ses propres sessions

### Règles de Protection

1. Un joueur ne peut créer des sessions que pour les terrains de son club
2. Un joueur ne peut arrêter que ses propres enregistrements
3. Un admin club peut arrêter tous les enregistrements de son club
4. Seuls les admins peuvent supprimer des vidéos
5. Seuls les admins peuvent nettoyer les sessions orphelines

---

## 🐛 Robustesse

### Arrêt Propre FFmpeg

```python
# Windows : process.terminate()
# Linux : SIGINT
# Wait timeout : 10s
# Fallback : kill si timeout
```

### Reconnection Automatique

- Le proxy se reconnecte automatiquement si la caméra coupe
- FFmpeg continue via le proxy stable
- Logging complet dans `<session_id>.ffmpeg.log`

### Cleanup Automatique

- Sessions orphelines (inactives depuis 2h sans enregistrement)
- Proxy sans enregistrement actif
- Fichiers vidéo vides (<1KB)

---

## 📁 Structure des Fichiers

```
padelvar-backend-main/
├── src/
│   ├── video_system/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── session_manager.py
│   │   ├── proxy_manager.py
│   │   ├── video_proxy_server.py
│   │   ├── recording.py
│   │   └── preview.py
│   └── routes/
│       ├── video.py
│       └── video_preview.py
├── static/
│   └── videos/
│       └── <club_id>/
│           └── <session_id>.mp4
└── logs/
    └── video/
        └── <session_id>.ffmpeg.log
```

---

## ⚙️ Configuration

### Fichier `config.py`

```python
class VideoConfig:
    # Chemins
    VIDEOS_DIR = Path("static/videos")
    LOGS_DIR = Path("logs/video")
    
    # FFmpeg
    FFMPEG_PATH = "ffmpeg"
    VIDEO_CODEC = "libx264"
    VIDEO_PRESET = "veryfast"
    VIDEO_CRF = 23
    VIDEO_FPS = 25
    
    # Proxy
    PROXY_BASE_PORT = 8080
    
    # Enregistrement
    DEFAULT_DURATION_SECONDS = 90 * 60  # 90 minutes
    MAX_CONCURRENT_RECORDINGS = 10
    
    # Session
    SESSION_TIMEOUT_SECONDS = 7200  # 2 heures
```

### Variables d'Environnement

```bash
export FFMPEG_PATH=/usr/bin/ffmpeg
export FFPROBE_PATH=/usr/bin/ffprobe
export PROXY_BASE_PORT=8080
```

---

## 🧪 Tests

### Test Complet

```python
import requests

BASE_URL = "http://localhost:5000"
TOKEN = "your_auth_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. Créer session
response = requests.post(
    f"{BASE_URL}/api/video/session/create",
    json={"terrain_id": 1},
    headers=headers
)
session = response.json()["session"]
session_id = session["session_id"]

# 2. Démarrer enregistrement
requests.post(
    f"{BASE_URL}/api/video/record/start",
    json={"session_id": session_id, "duration_minutes": 5},
    headers=headers
)

# 3. Vérifier statut
status = requests.get(
    f"{BASE_URL}/api/video/record/status/{session_id}",
    headers=headers
)
print(status.json())

# 4. Attendre un peu...
import time
time.sleep(10)

# 5. Arrêter enregistrement
result = requests.post(
    f"{BASE_URL}/api/video/record/stop",
    json={"session_id": session_id},
    headers=headers
)
print(result.json())
```

---

## 📊 Monitoring

### Métriques Disponibles

- Nombre de sessions actives
- Nombre d'enregistrements en cours
- Santé FFmpeg
- Ports proxy alloués
- Taille des fichiers vidéo

### Commandes Utiles

```bash
# Santé du système
curl http://localhost:5000/api/video/health

# Lister sessions actives
curl http://localhost:5000/api/video/session/list \
  -H "Authorization: Bearer <token>"

# Nettoyer sessions orphelines
curl -X POST http://localhost:5000/api/video/cleanup \
  -H "Authorization: Bearer <token>"

# Lister vidéos
curl http://localhost:5000/api/video/files/list?club_id=1 \
  -H "Authorization: Bearer <token>"
```

---

## 🔧 Dépannage

### Problème : FFmpeg non trouvé

```bash
# Vérifier FFmpeg
ffmpeg -version

# Si absent, installer
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Télécharger depuis https://ffmpeg.org/download.html
```

### Problème : Proxy ne démarre pas

```bash
# Vérifier les ports
netstat -tuln | grep 8080

# Libérer un port si nécessaire
sudo kill $(lsof -ti:8080)
```

### Problème : Caméra non accessible

```bash
# Tester connexion caméra MJPEG
curl -I http://192.168.1.100/mjpeg

# Tester connexion caméra RTSP
ffprobe rtsp://admin:password@192.168.1.100:554/stream
```

### Problème : Fichier vidéo vide

```bash
# Vérifier les logs FFmpeg
cat logs/video/<session_id>.ffmpeg.log

# Vérifier les permissions
ls -la static/videos/<club_id>/
```

---

## 📝 Logs

### Logs FFmpeg

```bash
# Chaque enregistrement génère un log détaillé
cat logs/video/sess_1_1701234567.ffmpeg.log
```

### Logs Applicatifs

```python
import logging

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('video_system')
```

---

## 🆘 Support

En cas de problème :

1. **Vérifier les logs** : `logs/video/<session_id>.ffmpeg.log`
2. **Tester la santé** : `GET /api/video/health`
3. **Nettoyer les sessions** : `POST /api/video/cleanup`
4. **Vérifier FFmpeg** : `ffmpeg -version`
5. **Vérifier le proxy** : `curl http://127.0.0.1:8080/health`

---

## 🎉 Résumé

Le système vidéo PadelVar est conçu pour être :

✅ **Stable** : Proxy protège FFmpeg des coupures caméra  
✅ **Simple** : Un seul fichier MP4 par enregistrement  
✅ **Scalable** : Multi-terrains, multi-enregistrements  
✅ **Sécurisé** : Permissions par rôle utilisateur  
✅ **Robuste** : Reconnection auto, arrêt propre, cleanup  

**Pipeline** : `Caméra → video_proxy_server.py → FFmpeg → MP4`

---

**Documentation complète** : `MIGRATION_VIDEO_SYSTEM.md`  
**Architecture** : 100% Python, pas de dépendances externes (go2rtc, MediaMTX)  
**Support** : Logs détaillés + API de monitoring
