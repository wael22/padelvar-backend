#!/bin/bash
# cleanup_old_video_system.sh
# Script pour archiver l'ancien système vidéo PadelVar

set -e  # Arrêter en cas d'erreur

echo "🧹 Nettoyage de l'ancien système vidéo PadelVar..."
echo ""

# Créer dossiers d'archive
echo "📁 Création des dossiers d'archive..."
mkdir -p src/services/_archived_old_system
mkdir -p src/routes/_archived_old_system
mkdir -p config/_archived_old_system

# Archiver services obsolètes
echo ""
echo "📦 Archivage des services obsolètes..."

# Services go2rtc/MediaMTX
[ -f "src/services/go2rtc_proxy_service.py" ] && mv src/services/go2rtc_proxy_service.py src/services/_archived_old_system/ && echo "  ✅ go2rtc_proxy_service.py"
[ -f "src/services/camera_session_manager.py" ] && mv src/services/camera_session_manager.py src/services/_archived_old_system/ && echo "  ✅ camera_session_manager.py"
[ -f "src/services/rtsp_proxy_manager.py" ] && mv src/services/rtsp_proxy_manager.py src/services/_archived_old_system/ && echo "  ✅ rtsp_proxy_manager.py"
[ -f "src/services/rtsp_proxy_server.py" ] && mv src/services/rtsp_proxy_server.py src/services/_archived_old_system/ && echo "  ✅ rtsp_proxy_server.py"

# Services Flask obsolètes
[ -f "src/services/flask_proxy_manager.py" ] && mv src/services/flask_proxy_manager.py src/services/_archived_old_system/ && echo "  ✅ flask_proxy_manager.py"
[ -f "src/services/flask_recording_manager.py" ] && mv src/services/flask_recording_manager.py src/services/_archived_old_system/ && echo "  ✅ flask_recording_manager.py"
[ -f "src/services/flask_video_proxy_server.py" ] && mv src/services/flask_video_proxy_server.py src/services/_archived_old_system/ && echo "  ✅ flask_video_proxy_server.py"

# Services multiples versions
[ -f "src/services/recording_manager_v2.py" ] && mv src/services/recording_manager_v2.py src/services/_archived_old_system/ && echo "  ✅ recording_manager_v2.py"
[ -f "src/services/recording_manager_v2.py.backup" ] && mv src/services/recording_manager_v2.py.backup src/services/_archived_old_system/ && echo "  ✅ recording_manager_v2.py.backup"
[ -f "src/services/video_recording_engine_fixed.py" ] && mv src/services/video_recording_engine_fixed.py src/services/_archived_old_system/ && echo "  ✅ video_recording_engine_fixed.py"
[ -f "src/services/multi_relay_server.py" ] && mv src/services/multi_relay_server.py src/services/_archived_old_system/ && echo "  ✅ multi_relay_server.py"

# Archiver tous les backups
mv src/services/*.backup* src/services/_archived_old_system/ 2>/dev/null && echo "  ✅ Fichiers .backup" || true

# Archiver tous les video_capture_service_* (backups multiples)
mv src/services/video_capture_service_*.py src/services/_archived_old_system/ 2>/dev/null && echo "  ✅ video_capture_service_* (backups)" || true

# Archiver proxy managers obsolètes (vérifier si ancien)
[ -f "src/services/video_proxy_manager.py" ] && [ -f "src/video_system/proxy_manager.py" ] && mv src/services/video_proxy_manager.py src/services/_archived_old_system/ && echo "  ✅ video_proxy_manager.py (ancien)"
[ -f "src/services/video_proxy_manager_v2.py" ] && mv src/services/video_proxy_manager_v2.py src/services/_archived_old_system/ && echo "  ✅ video_proxy_manager_v2.py"

# Archiver ancien video_proxy_server.py si nouveau existe
[ -f "src/services/video_proxy_server.py" ] && [ -f "src/video_system/video_proxy_server.py" ] && mv src/services/video_proxy_server.py src/services/_archived_old_system/ && echo "  ✅ video_proxy_server.py (ancien dans services/)"
[ -f "src/services/video_proxy_server.py.old" ] && mv src/services/video_proxy_server.py.old src/services/_archived_old_system/ && echo "  ✅ video_proxy_server.py.old"

# Archiver routes obsolètes
echo ""
echo "📦 Archivage des routes obsolètes..."

# Backups
mv src/routes/*.backup src/routes/_archived_old_system/ 2>/dev/null && echo "  ✅ Fichiers .backup" || true
mv src/routes/*.new src/routes/_archived_old_system/ 2>/dev/null && echo "  ✅ Fichiers .new" || true

# Versions multiples
mv src/routes/*_fixed.py src/routes/_archived_old_system/ 2>/dev/null && echo "  ✅ Fichiers *_fixed.py" || true
mv src/routes/*_clean.py src/routes/_archived_old_system/ 2>/dev/null && echo "  ✅ Fichiers *_clean.py" || true
mv src/routes/*_final.py src/routes/_archived_old_system/ 2>/dev/null && echo "  ✅ Fichiers *_final.py" || true
mv src/routes/*_optimized.py src/routes/_archived_old_system/ 2>/dev/null && echo "  ✅ Fichiers *_optimized.py" || true

# Routes v2/integration potentiellement obsolètes (à vérifier manuellement)
# [ -f "src/routes/recording_v2.py" ] && mv src/routes/recording_v2.py src/routes/_archived_old_system/ && echo "  ✅ recording_v2.py"
# [ -f "src/routes/recording_new.py" ] && mv src/routes/recording_new.py src/routes/_archived_old_system/ && echo "  ✅ recording_new.py"
# [ -f "src/routes/recording_integration.py" ] && mv src/routes/recording_integration.py src/routes/_archived_old_system/ && echo "  ✅ recording_integration.py"

# Archiver configs obsolètes
echo ""
echo "📦 Archivage des configurations obsolètes..."

[ -d "config/go2rtc" ] && mv config/go2rtc config/_archived_old_system/ && echo "  ✅ config/go2rtc/"
[ -d "config/mediamtx" ] && mv config/mediamtx config/_archived_old_system/ && echo "  ✅ config/mediamtx/"

echo ""
echo "✅ Nettoyage terminé !"
echo ""
echo "📂 Fichiers archivés dans :"
echo "   - src/services/_archived_old_system/"
echo "   - src/routes/_archived_old_system/"
echo "   - config/_archived_old_system/"
echo ""
echo "⚠️  Vérifiez que tout fonctionne avant de supprimer définitivement :"
echo "   1. python -m flask run"
echo "   2. curl http://localhost:5000/api/video/health"
echo ""
echo "🗑️  Pour supprimer définitivement les archives (après validation) :"
echo "   rm -rf src/services/_archived_old_system/"
echo "   rm -rf src/routes/_archived_old_system/"
echo "   rm -rf config/_archived_old_system/"
echo ""
