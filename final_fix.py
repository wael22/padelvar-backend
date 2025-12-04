#!/usr/bin/env python3
"""Réparation finale de clubs.py - suppression des lignes dupliquées"""

path = 'src/routes/clubs.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Suppression des lignes 1567-1570 (indexation 0-based = 1566-1569)
# Ces lignes sont la duplication de new_video = Video(
del lines[1566:1570]

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Removed duplicate new_video = Video( lines 1567-1570")
