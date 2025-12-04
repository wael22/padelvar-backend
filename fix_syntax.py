#!/usr/bin/env python3
"""Fix manually la ligne problématique dans clubs.py"""

path = 'src/routes/clubs.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Le problème: le script a supprimé trop de lignes et la déclaration new_video = Video( est incomplète
# On doit simplement supprimer le bloc stop_result et garder le reste

# Remplacer le bloc problématique
old_block = """        # Déterminer l'URL du fichier vidéo
        video_file_url = None
        # video_file_url déjà défini plus haut (ligne ~1449)
        # Vérifier que le fichier existe
        if not video_file_url or not os.path.exists(video_file_url):
            possible_paths = [
                f"static/videos/{court.club_id}/{active_recording.recording_id}.mp4",
                f"static/videos/{active_recording.recording_id}.mp4"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    video_file_url = path
                    logger.info(f"Fichier vidéo trouvé: {path}")
                    break
            else:
                logger.warning(f"Fichier vidéo introuvable pour {active_recording.recording_id}")

"""

new_block = """        # video_file_url déjà défini plus haut (ligne ~1449)
        # Vérifier que le fichier existe
        if not video_file_url or not os.path.exists(video_file_url):
            possible_paths = [
                f"static/videos/{court.club_id}/{active_recording.recording_id}.mp4",
                f"static/videos/{active_recording.recording_id}.mp4"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    video_file_url = path
                    logger.info(f"Fichier vidéo trouvé: {path}")
                    break
            else:
                logger.warning(f"Fichier vidéo introuvable pour {active_recording.recording_id}")
        
"""

content = content.replace(old_block, new_block)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed syntax error in club.py")
