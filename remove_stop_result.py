#!/usr/bin/env python3
"""Supprimer la référence à stop_result dans clubs.py"""

path = 'src/routes/clubs.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Trouver et supprimer le bloc stop_result (lignes 1462-1481 environ)
new_lines = []
skip_until = -1

for i, line in enumerate(lines):
    line_num = i + 1
    
    # Si on est dans le bloc à skip
    if skip_until > 0 and line_num <= skip_until:
        continue
    
    # Détecter le début du bloc problématique
    if 'stop_result' in line and 'if stop_result:' in line:
        # Remplacer tout le bloc par un commentaire simple
        indent = ' ' * 8
        new_lines.append(f"{indent}# video_file_url déjà défini plus haut (ligne ~1449)\n")
        new_lines.append(f"{indent}# Vérifier que le fichier existe\n")
        new_lines.append(f"{indent}if not video_file_url or not os.path.exists(video_file_url):\n")
        new_lines.append(f"{indent}    possible_paths = [\n")
        new_lines.append(f"{indent}        f\"static/videos/{{court.club_id}}/{{active_recording.recording_id}}.mp4\",\n")
        new_lines.append(f"{indent}        f\"static/videos/{{active_recording.recording_id}}.mp4\"\n")
        new_lines.append(f"{indent}    ]\n")
        new_lines.append(f"{indent}    for path in possible_paths:\n")
        new_lines.append(f"{indent}        if os.path.exists(path):\n")
        new_lines.append(f"{indent}            video_file_url = path\n")
        new_lines.append(f"{indent}            logger.info(f\"Fichier vidéo trouvé: {{path}}\")\n")
        new_lines.append(f"{indent}            break\n")
        new_lines.append(f"{indent}    else:\n")
        new_lines.append(f"{indent}        logger.warning(f\"Fichier vidéo introuvable pour {{active_recording.recording_id}}\")\n")
        new_lines.append(f"{indent}\n")
        
        # Skip jusqu'à la ligne "new_video = Video("
        skip_until = line_num + 20  # approximatif
        continue
    
    # Si on voit "new_video = Video(", on arrête de skip
    if 'new_video = Video(' in line:
        skip_until = -1
    
    new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"✅ Removed stop_result from {path}")
