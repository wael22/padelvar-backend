# Migration - Nouveau Système Vidéo PadelVar

## 🎯 Objectif

Remplacer complètement l'ancien système d'enregistrement vidéo par une architecture **100% stable** basée sur un pipeline unique :

```
Caméra IP → video_proxy_server.py → FFmpeg → Fichier MP4 unique
```

---

## 🔥 Changements Majeurs

### ✅ Ce qui est NOUVEAU

1. **Proxy Universel Unique** (`video_proxy_server.py`)
   - Un seul type de proxy pour TOUS les flux (MJPEG, RTSP, HTTP)
   - Support multi-clients
   - Reconnection automatique
   - Buffer frames stabilisé

2. **Architecture Modulaire**
   - `session_manager.py` : Gestion sessions caméra
   - `proxy_manager.py` : Gestion proxies vidéo
   - `recording.py` : Enregistrement FFmpeg (un seul MP4)
   - `preview.py` : Preview en temps réel
   - `config.py` : Configuration centralisée

3. **Un Seul Fichier MP4**
   - Pas de segmentation
   - Fichier unique stable
   - Arrêt propre (SIGINT/terminate)

4. **Routes API Complètes**
   - `/api/video/session/*` : Gestion sessions
   - `/api/video/record/*` : Enregistrement
   - `/api/video/files/*` : Gestion fichiers
   - `/api/preview/<session_id>/*` : Preview temps réel

5. **Sécurité & Permissions**
   - Contrôle d'accès par rôle (SUPER_ADMIN, CLUB_ADMIN, PLAYER)
   - Un utilisateur ne peut stopper que ses enregistrements
   - Admin club peut gérer les enregistrements de son club

---

### ❌ Ce qui est SUPPRIMÉ

1. **go2rtc** : Plus utilisé
2. **MediaMTX** : Plus utilisé
3. **Segmentation vidéo** : Remplacé par fichier MP4 unique
4. **Multiples services proxy** : Remplacé par `video_proxy_server.py` unique

---

## 📁 Structure des Fichiers

### Nouveaux Modules (src/video_system/)

```
src/video_system/
├── __init__.py               # Exports principaux
├── config.py                 # Configuration centralisée
├── session_manager.py        # Gestion sessions caméra
├── proxy_manager.py          # Gestion proxies vidéo
├── video_proxy_server.py     # Proxy interne universel
├── recording.py              # Enregistrement FFmpeg
└── preview.py                # Preview WebSocket/HTTP
```

### Nouvelles Routes (src/routes/)

```
src/routes/
├── video.py                  # Routes principales (sessions, recording, files)
└── video_preview.py          # Routes preview (stream, snapshot)
```

### Fichiers Vidéo Générés

```
static/videos/
└── <club_id>/
    ├── <session_id>.mp4
    └── <session_id>.ffmpeg.log
```

---

## 🚀 API Endpoints

### Sessions Caméra

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/video/session/create` | POST | Créer une session caméra + proxy |
| `/api/video/session/close` | POST | Fermer une session |
| `/api/video/session/list` | GET | Lister sessions actives |
| `/api/video/session/<id>` | GET | Détails d'une session |

### Enregistrement

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/video/record/start` | POST | Démarrer enregistrement |
| `/api/video/record/stop` | POST | Arrêter enregistrement |
| `/api/video/record/status/<id>` | GET | Statut enregistrement |

### Fichiers Vidéo

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/video/files/list` | GET | Lister vidéos d'un club |
| `/api/video/files/<id>/download` | GET | Télécharger une vidéo |
| `/api/video/files/<id>/delete` | DELETE | Supprimer une vidéo |

### Preview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/preview/<id>/stream.mjpeg` | GET | Stream MJPEG continu |
| `/api/preview/<id>/snapshot.jpg` | GET | Snapshot JPEG unique |
| `/api/preview/<id>/info` | GET | Infos preview |

### Health & Maintenance

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/video/health` | GET | Santé système vidéo |
| `/api/video/cleanup` | POST | Nettoyer sessions orphelines |

---

## 🔧 Utilisation

### 1. Créer une Session & Démarrer Enregistrement

```python
# Frontend/Client
import requests

# Étape 1 : Créer session caméra
response = requests.post('/api/video/session/create', json={
    'terrain_id': 1
})
session = response.json()['session']
session_id = session['session_id']

# Étape 2 : Démarrer enregistrement
requests.post('/api/video/record/start', json={
    'session_id': session_id,
    'duration_minutes': 90
})

# Étape 3 : Vérifier le statut
status = requests.get(f'/api/video/record/status/{session_id}')
print(status.json())
```

### 2. Preview en Temps Réel

```html
<!-- HTML : Afficher le stream MJPEG -->
<img src="/api/preview/<session_id>/stream.mjpeg" alt="Live Preview" />

<!-- Ou avec JavaScript pour polling de snapshots -->
<img id="preview" />
<script>
  const sessionId = "sess_1_123456";
  setInterval(() => {
    document.getElementById('preview').src = 
      `/api/preview/${sessionId}/snapshot.jpg?t=${Date.now()}`;
  }, 200); // 5 FPS
</script>
```

### 3. Arrêter Enregistrement

```python
# Arrêter proprement
response = requests.post('/api/video/record/stop', json={
    'session_id': session_id
})

if response.json()['success']:
    video_path = response.json()['video_path']
    print(f"Vidéo créée : {video_path}")
    
# Fermer la session (optionnel, automatique après stop)
requests.post('/api/video/session/close', json={
    'session_id': session_id
})
```

---

## 🛡️ Sécurité & Permissions

### Matrice de Permissions

| Action | SUPER_ADMIN | CLUB_ADMIN | PLAYER |
|--------|-------------|------------|--------|
| Créer session | ✅ | ✅ | ✅ (son club) |
| Démarrer recording | ✅ | ✅ (son club) | ✅ (sa session) |
| Arrêter recording | ✅ | ✅ (son club) | ✅ (sa session) |
| Voir preview | ✅ | ✅ (son club) | ✅ (sa session) |
| Lister vidéos | ✅ | ✅ (son club) | ❌ |
| Télécharger vidéo | ✅ | ✅ (son club) | ❌ |
| Supprimer vidéo | ✅ | ✅ (son club) | ❌ |
| Cleanup sessions | ✅ | ✅ | ❌ |

### Protection des Enregistrements

```python
# Un joueur ne peut stopper QUE ses propres enregistrements
# Sauf admin qui peut stopper n'importe quel enregistrement de son club
```

---

## 🐛 Robustesse & Gestion d'Erreurs

### Arrêt Propre FFmpeg

```python
# Windows : process.terminate()
# Linux : SIGINT (process.send_signal(signal.SIGINT))
# Wait timeout : 10 secondes
# Fallback : kill forcé si timeout
```

### Reconnection Automatique

- Le proxy se reconnecte automatiquement si la caméra coupe
- FFmpeg continue d'enregistrer via le proxy stable
- Logging complet dans `<session_id>.ffmpeg.log`

### Cleanup Automatique

- Sessions orphelines (plus d'activité depuis 2h)
- Proxy sans enregistrement actif
- Fichiers vidéo vides (<1KB)

---

## 📊 Monitoring

### Vérifier la Santé du Système

```bash
curl http://localhost:5000/api/video/health
```

**Réponse :**
```json
{
  "status": "healthy",
  "ffmpeg_available": true,
  "ffmpeg_path": "ffmpeg",
  "active_sessions": 3,
  "active_recordings": 2,
  "max_concurrent": 10,
  "proxy_type": "video_proxy_server.py (internal)",
  "pipeline": "Camera → video_proxy_server.py → FFmpeg → MP4"
}
```

### Nettoyer Sessions Orphelines

```bash
curl -X POST http://localhost:5000/api/video/cleanup \
  -H "Authorization: Bearer <token>"
```

---

## 🔄 Migration depuis l'Ancien Système

### Étapes de Migration

1. **Installer les dépendances**
   ```bash
   pip install flask requests pillow opencv-python-headless
   ```

2. **Vérifier FFmpeg**
   ```bash
   ffmpeg -version
   ```

3. **Supprimer les anciens services** (optionnel)
   ```bash
   # Arrêter go2rtc / MediaMTX s'ils tournent
   pkill go2rtc
   pkill mediamtx
   ```

4. **Tester le nouveau système**
   ```bash
   # Démarrer le backend
   python -m flask run
   
   # Tester la santé
   curl http://localhost:5000/api/video/health
   ```

5. **Adapter le frontend**
   - Remplacer les appels à l'ancien système par les nouvelles routes
   - Utiliser `/api/video/session/create` au lieu de l'ancien endpoint
   - Utiliser `/api/preview/<id>/stream.mjpeg` pour le preview

---

## ⚙️ Configuration

### Variables d'Environnement

```bash
# FFmpeg
export FFMPEG_PATH=/usr/bin/ffmpeg
export FFPROBE_PATH=/usr/bin/ffprobe

# Ports (optionnel, par défaut : 8080+)
export PROXY_BASE_PORT=8080
```

### Fichier config.py

```python
# src/video_system/config.py

class VideoConfig:
    # Chemins
    VIDEOS_DIR = Path("static/videos")
    LOGS_DIR = Path("logs/video")
    
    # FFmpeg
    VIDEO_CODEC = "libx264"
    VIDEO_PRESET = "veryfast"
    VIDEO_CRF = 23
    VIDEO_FPS = 25
    
    # Proxy
    PROXY_BASE_PORT = 8080
    
    # Enregistrement
    DEFAULT_DURATION_SECONDS = 90 * 60  # 90 minutes
    MAX_CONCURRENT_RECORDINGS = 10
```

---

## 🧪 Tests

### Test Manuel Complet

```bash
# 1. Créer session
curl -X POST http://localhost:5000/api/video/session/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"terrain_id": 1}'

# 2. Démarrer enregistrement
curl -X POST http://localhost:5000/api/video/record/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"session_id": "sess_1_123456", "duration_minutes": 5}'

# 3. Vérifier preview
curl http://localhost:5000/api/preview/sess_1_123456/snapshot.jpg \
  -H "Authorization: Bearer <token>" \
  --output snapshot.jpg

# 4. Vérifier statut
curl http://localhost:5000/api/video/record/status/sess_1_123456 \
  -H "Authorization: Bearer <token>"

# 5. Arrêter enregistrement
curl -X POST http://localhost:5000/api/video/record/stop \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"session_id": "sess_1_123456"}'

# 6. Télécharger vidéo
curl http://localhost:5000/api/video/files/sess_1_123456/download?club_id=1 \
  -H "Authorization: Bearer <token>" \
  --output video.mp4
```

---

## 📝 Logs

### Logs FFmpeg

```bash
# Chaque enregistrement génère un log détaillé
cat logs/video/sess_1_123456.ffmpeg.log
```

### Logs Applicatifs

```python
import logging
logger = logging.getLogger('video_system')
logger.setLevel(logging.INFO)
```

---

## 🎉 Résumé

✅ **Pipeline stable** : Caméra → Proxy → FFmpeg → MP4  
✅ **Un seul fichier MP4** (pas de segmentation)  
✅ **Proxy universel** pour tous les flux  
✅ **Multi-terrains / Multi-enregistrements** simultanés  
✅ **Preview temps réel** (MJPEG stream ou snapshots)  
✅ **Sécurité & Permissions** par rôle  
✅ **Arrêt propre** et robuste  
✅ **API complète** et documentée  

---

## 🆘 Support

En cas de problème :

1. Vérifier les logs : `logs/video/<session_id>.ffmpeg.log`
2. Tester la santé : `GET /api/video/health`
3. Nettoyer les sessions : `POST /api/video/cleanup`
4. Vérifier FFmpeg : `ffmpeg -version`
5. Vérifier le proxy : `curl http://127.0.0.1:8080/health`

---

**Migration complétée** ✅  
**Ancien système supprimé** ❌ go2rtc, MediaMTX, segmentation  
**Nouveau système opérationnel** ✅ video_proxy_server.py + FFmpeg
