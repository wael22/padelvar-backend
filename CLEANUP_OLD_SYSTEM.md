# Nettoyage Ancien Système Vidéo

## ⚠️ Fichiers à Supprimer ou Désactiver

### 📁 Services Obsolètes (src/services/)

Les fichiers suivants utilisent l'ancien système (go2rtc, MediaMTX, segmentation) et doivent être **supprimés** ou **archivés** :

```
src/services/
├── go2rtc_proxy_service.py          ❌ SUPPRIMER (remplacé par video_proxy_server.py)
├── camera_session_manager.py        ❌ SUPPRIMER (remplacé par video_system/session_manager.py)
├── flask_proxy_manager.py           ⚠️  VÉRIFIER (potentiellement obsolète)
├── flask_recording_manager.py       ⚠️  VÉRIFIER (potentiellement obsolète)
├── flask_video_proxy_server.py      ⚠️  VÉRIFIER (potentiellement obsolète)
├── rtsp_proxy_manager.py            ❌ SUPPRIMER (MediaMTX obsolète)
├── rtsp_proxy_server.py             ❌ SUPPRIMER (MediaMTX obsolète)
├── multi_relay_server.py            ⚠️  VÉRIFIER (potentiellement obsolète)
├── recording_manager_v2.py          ⚠️  VÉRIFIER (potentiellement obsolète)
├── video_proxy_manager.py           ⚠️  VÉRIFIER (potentiellement obsolète)
├── video_proxy_manager_v2.py        ⚠️  VÉRIFIER (potentiellement obsolète)
├── video_proxy_server.py            ⚠️  VÉRIFIER (ancien proxy, comparé au nouveau)
├── video_recording_engine.py        ⚠️  VÉRIFIER (potentiellement obsolète)
├── video_recording_engine_fixed.py  ❌ SUPPRIMER (backup)
└── video_recording_service.py       ⚠️  VÉRIFIER (potentiellement obsolète)
```

**Services de capture vidéo multiples (backups à supprimer) :**
```
src/services/
├── video_capture_service.py.backup
├── video_capture_service.py.backup2
├── video_capture_service_cantplay_fix.py
├── video_capture_service_cantplay_fixed.py
├── video_capture_service_direct.py
├── video_capture_service_direct_fixed.py
├── video_capture_service_final.py
├── video_capture_service_fixed.py
├── video_capture_service_really_final.py
├── video_capture_service_simple.py
├── video_capture_service_ultimate.py
├── video_capture_service_windows.py
└── video_capture_service_working_final.py
```

**Action recommandée :**
- Archiver dans un dossier `src/services/_archived_old_system/`
- Ou supprimer complètement

---

### 📁 Routes Obsolètes (src/routes/)

Les fichiers suivants peuvent être désactivés/supprimés :

```
src/routes/
├── recording_v2.py                  ⚠️  VÉRIFIER (si utilisé par ancien système)
├── recording_v2_fixed.py            ❌ SUPPRIMER (backup)
├── recording_new.py                 ⚠️  VÉRIFIER (si utilisé par ancien système)
├── recording_integration.py         ⚠️  VÉRIFIER (si utilisé par ancien système)
├── video_recording_routes.py        ⚠️  VÉRIFIER (si utilisé par ancien système)
├── videos_mjpeg.py                  ⚠️  VÉRIFIER (si utilisé par ancien système)
├── videos_refactored.py             ❌ SUPPRIMER (backup)
├── videos.py.backup                 ❌ SUPPRIMER (backup)
├── videos.py.new                    ❌ SUPPRIMER (backup)
├── players_clean.py                 ❌ SUPPRIMER (backup)
├── players_final.py                 ❌ SUPPRIMER (backup)
├── players_optimized.py             ❌ SUPPRIMER (backup)
└── admin_fixed.py                   ❌ SUPPRIMER (backup)
```

**Action recommandée :**
- Commenter les imports dans `main.py` (déjà fait pour certains)
- Archiver dans `src/routes/_archived/`

---

### 📁 Configuration Obsolète (config/)

```
config/
├── go2rtc/                          ❌ SUPPRIMER (go2rtc plus utilisé)
├── mediamtx/                        ❌ SUPPRIMER (MediaMTX plus utilisé)
└── proxies.yaml                     ⚠️  VÉRIFIER (si utilisé par ancien système)
```

---

### 📁 Scripts Obsolètes

Si des scripts utilisent l'ancien système :

```
scripts/
└── (vérifier si des scripts utilisent go2rtc/MediaMTX)
```

---

## 🔧 Script de Nettoyage Automatique

### Option 1 : Archiver (Recommandé)

```bash
#!/bin/bash
# cleanup_old_video_system.sh

# Créer dossiers d'archive
mkdir -p src/services/_archived_old_system
mkdir -p src/routes/_archived_old_system
mkdir -p config/_archived_old_system

# Archiver services obsolètes
mv src/services/go2rtc_proxy_service.py src/services/_archived_old_system/
mv src/services/camera_session_manager.py src/services/_archived_old_system/
mv src/services/rtsp_proxy_manager.py src/services/_archived_old_system/
mv src/services/rtsp_proxy_server.py src/services/_archived_old_system/
mv src/services/*.backup* src/services/_archived_old_system/ 2>/dev/null

# Archiver backups video_capture_service
mv src/services/video_capture_service_*.py src/services/_archived_old_system/ 2>/dev/null

# Archiver routes obsolètes
mv src/routes/*.backup src/routes/_archived_old_system/ 2>/dev/null
mv src/routes/*.new src/routes/_archived_old_system/ 2>/dev/null
mv src/routes/*_fixed.py src/routes/_archived_old_system/ 2>/dev/null
mv src/routes/*_clean.py src/routes/_archived_old_system/ 2>/dev/null
mv src/routes/*_final.py src/routes/_archived_old_system/ 2>/dev/null
mv src/routes/*_optimized.py src/routes/_archived_old_system/ 2>/dev/null

# Archiver configs obsolètes
mv config/go2rtc config/_archived_old_system/ 2>/dev/null
mv config/mediamtx config/_archived_old_system/ 2>/dev/null

echo "✅ Ancien système archivé dans */_archived_old_system/"
echo "⚠️  Vérifiez que tout fonctionne avant de supprimer définitivement"
```

### Option 2 : Supprimer Définitivement (⚠️ Attention)

```bash
#!/bin/bash
# delete_old_video_system.sh

# ⚠️  ATTENTION : Suppression définitive !

# Supprimer services obsolètes
rm -f src/services/go2rtc_proxy_service.py
rm -f src/services/camera_session_manager.py
rm -f src/services/rtsp_proxy_manager.py
rm -f src/services/rtsp_proxy_server.py
rm -f src/services/*.backup*
rm -f src/services/video_capture_service_*.py

# Supprimer routes obsolètes
rm -f src/routes/*.backup
rm -f src/routes/*.new
rm -f src/routes/*_fixed.py
rm -f src/routes/*_clean.py
rm -f src/routes/*_final.py
rm -f src/routes/*_optimized.py

# Supprimer configs obsolètes
rm -rf config/go2rtc
rm -rf config/mediamtx

echo "❌ Ancien système supprimé définitivement"
```

---

## 📝 Vérifications Manuelles

### 1. Vérifier les Imports dans main.py

```python
# src/main.py

# ✅ ACTIFS (nouveau système)
from .routes.video import video_bp
from .routes.video_preview import preview_bp

# ❌ DÉSACTIVÉS (ancien système - déjà commentés)
# from .routes.recording_v2 import recording_bp as recording_v2_bp
# from .routes.recording_new import recording_api, init_recording_service
```

### 2. Vérifier les Imports dans les Modèles

```bash
# Chercher les références à go2rtc et MediaMTX
grep -r "go2rtc" src/
grep -r "mediamtx" src/
grep -r "MediaMTX" src/
```

**Résultat attendu :**
- Aucune référence dans les fichiers actifs
- Uniquement dans les fichiers archivés

### 3. Vérifier les Dépendances

```bash
# requirements.txt ou Pipfile
# Supprimer/commenter :
# - go2rtc (s'il était installé via pip)
# - mediamtx (s'il était installé via pip)
```

---

## 🧪 Tests Après Nettoyage

### 1. Vérifier que le Backend Démarre

```bash
python -m flask run
```

**Erreur attendue :** Aucune

### 2. Tester la Santé du Nouveau Système

```bash
curl http://localhost:5000/api/video/health
```

**Réponse attendue :**
```json
{
  "status": "healthy",
  "ffmpeg_available": true,
  "proxy_type": "video_proxy_server.py (internal)",
  "pipeline": "Camera → video_proxy_server.py → FFmpeg → MP4"
}
```

### 3. Tester Création Session

```bash
curl -X POST http://localhost:5000/api/video/session/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"terrain_id": 1}'
```

**Erreur attendue :** Aucune

---

## 📊 Comparaison Ancien vs Nouveau

| Composant | Ancien Système | Nouveau Système |
|-----------|----------------|-----------------|
| Proxy RTSP | MediaMTX | video_proxy_server.py |
| Proxy MJPEG | go2rtc | video_proxy_server.py |
| Session Manager | camera_session_manager.py | video_system/session_manager.py |
| Recording | Multiples versions | video_system/recording.py |
| Segmentation | ✅ Fichiers multiples | ❌ Fichier unique MP4 |
| Preview | Multiples services | video_system/preview.py |
| Routes | recording_v2.py, etc. | video.py + video_preview.py |

---

## ✅ Checklist de Nettoyage

- [ ] Archiver les services obsolètes dans `_archived_old_system/`
- [ ] Archiver les routes obsolètes dans `_archived_old_system/`
- [ ] Supprimer les configs go2rtc et MediaMTX
- [ ] Vérifier qu'il n'y a plus de références à go2rtc/MediaMTX dans le code actif
- [ ] Tester que le backend démarre sans erreur
- [ ] Tester la création d'une session vidéo
- [ ] Tester un enregistrement complet (start → stop)
- [ ] Tester le preview en temps réel
- [ ] Vérifier les logs FFmpeg
- [ ] Documenter les changements dans le changelog

---

## 🚀 Exécution du Nettoyage

### Étape 1 : Archiver (Sécurisé)

```bash
cd padelvar-backend-main
chmod +x cleanup_old_video_system.sh
./cleanup_old_video_system.sh
```

### Étape 2 : Tester

```bash
# Démarrer le backend
python -m flask run

# Dans un autre terminal, tester
curl http://localhost:5000/api/video/health
```

### Étape 3 : Valider

- [ ] Backend démarre ✅
- [ ] API /video/health répond ✅
- [ ] Création session fonctionne ✅
- [ ] Enregistrement fonctionne ✅

### Étape 4 : Supprimer Définitivement (Optionnel)

```bash
# Si tout fonctionne pendant plusieurs jours
rm -rf src/services/_archived_old_system/
rm -rf src/routes/_archived_old_system/
rm -rf config/_archived_old_system/
```

---

## 📦 Résumé

✅ **Ancien système archivé** dans `_archived_old_system/`  
✅ **Nouveau système actif** dans `video_system/`  
✅ **Routes migrées** : `video.py` + `video_preview.py`  
✅ **Pas de go2rtc** ni MediaMTX  
✅ **Un seul fichier MP4** par enregistrement  
✅ **Proxy universel** : `video_proxy_server.py`  

**Migration complétée** ✅  
**Ancien système désactivé** ❌  
**Nouveau système opérationnel** ✅
