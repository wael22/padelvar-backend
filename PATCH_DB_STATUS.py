# PATCH: Ajouter mise à jour DB dans start_recording_v3
# Fichier: src/routes/recording.py
# Après la ligne 630 (après video_recorder.start_recording)

# AJOUTER CE CODE:

# 3. 🆕 Mettre à jour l'état du terrain dans la DB
from src.models.database import db
from src.models.user import RecordingSession
from datetime import datetime

try:
    # Créer une entrée RecordingSession pour le suivi
    recording_session = RecordingSession(
        recording_id=session.session_id,
        court_id=court_id,
        user_id=user.id,
        start_time=datetime.utcnow(),
        status='recording'
    )
    db.session.add(recording_session)
    
    # Marquer le terrain comme occupé
    court.is_recording = True
    
    db.session.commit()
    logger.info(f"📊 État terrain mis à jour: {court.name} → En enregistrement")
    
except Exception as db_err:
    logger.error(f"⚠️ Erreur mise à jour DB: {db_err}")
    # Continue quand même, l'enregistrement fonctionne
    db.session.rollback()

# LOCALISATION:
# Dans src/routes/recording.py
# Fonction: start_recording_v3()
# Après la ligne:
#     if not success:
#         session_manager.close_session(session.session_id)
#         return jsonify(...)
#
# INSÉRER ce code AVANT la ligne:
#     logger.info(f"✅ Enregistrement démarré via nouveau système: {session.session_id}")
