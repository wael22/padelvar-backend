"""
Module vidéos (nettoyé). Les endpoints start/stop internes sont dépréciés.
Utiliser /api/recording/start et /api/recording/stop.
"""
from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Video, Court, Club
from functools import wraps
import logging

logger = logging.getLogger(__name__)
videos_bp = Blueprint('videos', __name__)

# Helpers

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if 'user_id' not in session:
            return jsonify({'error': 'Non authentifié'}), 401
        return f(*a, **k)
    return w


def get_current_user():
    uid = session.get('user_id')
    return User.query.get(uid) if uid else None


def api_response(data=None, message=None, status=200, error=None):
    resp = {}
    if data is not None:
        resp.update(data)
    if message:
        resp['message'] = message
    if error:
        resp['error'] = error
    return jsonify(resp), status

# ================= Vidéos =================
@videos_bp.route('/my-videos', methods=['GET'])
@login_required
def my_videos():
    user = get_current_user()
    videos = (Video.query.filter_by(user_id=user.id)
              .order_by(Video.recorded_at.desc()).all())
    return api_response({'videos': [
        {
            'id': v.id,
            'title': v.title,
            'description': v.description,
            'file_url': v.file_url,
            'thumbnail_url': v.thumbnail_url,
            'duration': v.duration,
            'recorded_at': v.recorded_at.isoformat() if v.recorded_at else None,
            'is_unlocked': v.is_unlocked
        } for v in videos
    ]})


@videos_bp.route('/<int:video_id>', methods=['GET'])
@login_required
def get_video(video_id):
    user = get_current_user()
    video = Video.query.get_or_404(video_id)
    if video.user_id != user.id and not video.is_unlocked:
        return api_response(error='Accès non autorisé', status=403)
    return api_response({'video': video.to_dict()})


@videos_bp.route('/<int:video_id>', methods=['PUT'])
@login_required
def update_video(video_id):
    user = get_current_user()
    video = Video.query.get_or_404(video_id)
    if video.user_id != user.id:
        return api_response(error='Accès non autorisé', status=403)
    data = request.get_json() or {}
    if 'title' in data:
        video.title = data['title']
    if 'description' in data:
        video.description = data['description']
    db.session.commit()
    return api_response({'video': video.to_dict()}, 'Vidéo mise à jour')


@videos_bp.route('/<int:video_id>', methods=['DELETE'])
@login_required
def delete_video(video_id):
    user = get_current_user()
    video = Video.query.get_or_404(video_id)
    if video.user_id != user.id:
        return api_response(error='Accès non autorisé', status=403)
    db.session.delete(video)
    db.session.commit()
    return api_response(message='Vidéo supprimée')


@videos_bp.route('/<int:video_id>/share', methods=['POST'])
@login_required
def share_video(video_id):
    user = get_current_user()
    video = Video.query.get_or_404(video_id)
    if video.user_id != user.id:
        return api_response(error='Accès non autorisé', status=403)
    if not video.is_unlocked:
        return api_response(error='Vidéo verrouillée', status=400)
    base = request.host_url
    video_url = f"{base}videos/{video_id}/watch"
    share = {
        'facebook': f"https://www.facebook.com/sharer/sharer.php?u={video_url}",
        'instagram': video_url,
        'youtube': video_url,
        'direct': video_url
    }
    return api_response({'share_urls': share, 'video_url': video_url}, 'Liens générés')


@videos_bp.route('/<int:video_id>/watch', methods=['GET'])
def watch_video(video_id):
    video = Video.query.get_or_404(video_id)
    if not video.is_unlocked:
        return api_response(error='Vidéo non disponible', status=403)
    stream = video.file_url or f"/api/videos/stream/video_{video_id}.mp4"
    return api_response({'video': {
        'id': video.id,
        'title': video.title,
        'description': video.description,
        'file_url': stream,
        'thumbnail_url': video.thumbnail_url,
        'duration': video.duration,
        'recorded_at': video.recorded_at.isoformat() if video.recorded_at else None
    }})


# Courts
@videos_bp.route('/courts/available', methods=['GET'])
@login_required
def available_courts():
    courts = Court.query.filter_by(is_recording=False).all()
    groups = {}
    for c in courts:
        club = Club.query.get(c.club_id)
        if club:
            groups.setdefault(club.id, {'club': club.to_dict(), 'courts': []})['courts'].append(c.to_dict())
    return api_response({'available_courts': list(groups.values()), 'total_available': len(courts)})


# Deprecated start/stop
@videos_bp.route('/record', methods=['POST'])
@login_required
def deprecated_start():
    return api_response(error='Endpoint remplacé. Utilisez /api/recording/start', status=410)


@videos_bp.route('/stop-recording', methods=['POST'])
@login_required
def deprecated_stop():
    return api_response(error='Endpoint remplacé. Utilisez /api/recording/stop', status=410)


# QR Scan
@videos_bp.route('/qr-scan', methods=['POST'])
@login_required
def scan_qr_code():
    data = request.get_json() or {}
    code = data.get('qr_code')
    if not code:
        return api_response(error='QR code requis', status=400)
    court = Court.query.filter_by(qr_code=code).first()
    if not court:
        return api_response(error='QR code invalide', status=404)
    club = Club.query.get(court.club_id)
    return api_response({'court': court.to_dict(), 'club': club.to_dict() if club else None, 'camera_url': court.camera_url, 'can_record': True}, 'QR scanné')

# Note: Ancien bloc dupliqué supprimé pour éviter conflits.
