#!/usr/bin/env python3
"""Réparer complètement clubs.py en ajoutant la ligne manquante"""

path = 'src/routes/clubs.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    # Si on trouve la ligne "user_id=active_recording.user_id" sans "new_video = Video(" avant
    if i > 0 and 'user_id=active_recording.user_id,' in line:
        # Vérifier s'il manque "new_video = Video("
        prev_lines = ''.join(lines[max(0, i-10):i])
        if 'new_video = Video(' not in prev_lines:
            # Insérer "new_video = Video(" avant
            indent = ' ' * 8
            new_lines.append(f"{indent}new_video = Video(\n")
            new_lines.append(f"{indent}    title=video_title,\n")
            new_lines.append(f"{indent}    description=active_recording.description or f\"Enregistrement automatique sur {{court.name}}\",\n")
            new_lines.append(f"{indent}    duration=duration_minutes,  # ⚠️ TEMPORAIRE - sera corrigé ci-dessous\n")
    
    new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Added missing new_video = Video( line")
