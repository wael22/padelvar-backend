#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour appliquer les corrections aux fichiers PadelVar
"""

def fix_clubs_py():
    """Ajouter recording_active = False avant close_session"""
    path = 'src/routes/clubs.py'
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Chercher la ligne "session_manager.close_session(active_recording.recording_id)"
    for i, line in enumerate(lines):
        if 'session_manager.close_session(active_recording.recording_id)' in line:
            # Insérer les lignes avant
            indent = ' ' * 12  # 12 espaces d'indentation
            new_lines = [
                f"{indent}# CRITIQUE: Marquer comme inactif AVANT de fermer\n",
                f"{indent}session = session_manager.get_session(active_recording.recording_id)\n",
                f"{indent}if session:\n",
                f"{indent}    session.recording_active = False\n",
            ]
            lines[i:i] = new_lines
            break
    
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"✅ {path} fixed")

def fix_celery_app():
    """Désactiver Celery pour supprimer les erreurs Redis"""
    path = 'src/celery_app.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer la ligne d'initialisation
    content = content.replace(
        '# Instance globale Celery\ncelery_app = create_celery_app()',
        '# Instance globale Celery (DÉSACTIVÉ en développement)\ncelery_app = None  # create_celery_app()'
    )
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ {path} fixed - Redis disabled")

if __name__ == '__main__':
    fix_clubs_py()
    fix_celery_app()
    print("\n🎉 All fixes applied!")
