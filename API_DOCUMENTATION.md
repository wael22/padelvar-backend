# 🎾 API PadelVar - Documentation Complète

## 📋 Vue d'ensemble

**PadelVar** est une API REST complète pour la gestion de clubs de padel avec système d'enregistrement vidéo intelligent. L'API gère trois types d'utilisateurs avec des permissions granulaires et un workflow d'enregistrement vidéo automatisé.

### Informations générales
- **URL de base** : `http://localhost:5000/api`
- **Format** : JSON
- **Authentification** : Session-based + Google OAuth (optionnel)
- **Codes de statut** : Standards HTTP
- **Versioning** : v3 pour le système d'enregistrement

---

## 🔐 Authentification

### Système d'authentification
L'API utilise un système de sessions basé sur les cookies avec support optionnel pour Google OAuth.

#### Types d'utilisateurs
```json
{
  "roles": {
    "SUPER_ADMIN": "Accès complet au système",
    "CLUB": "Gestion d'un club spécifique", 
    "PLAYER": "Fonctionnalités joueur"
  }
}
```

### Endpoints d'authentification

#### POST /auth/register
Inscription d'un nouveau joueur.

**Corps de la requête:**
```json
{
  "email": "joueur@example.com",
  "password": "password123",
  "name": "Nom Joueur",
  "phone_number": "+216 12 345 678"
}
```

**Réponse (201):**
```json
{
  "message": "Utilisateur créé avec succès",
  "user": {
    "id": 1,
    "email": "joueur@example.com",
    "name": "Nom Joueur",
    "role": "PLAYER",
    "credits_balance": 5
  }
}
```

#### POST /auth/login
Connexion utilisateur.

**Corps de la requête:**
```json
{
  "email": "joueur@example.com",
  "password": "password123"
}
```

**Réponse (200):**
```json
{
  "message": "Connexion réussie",
  "user": {
    "id": 1,
    "email": "joueur@example.com",
    "name": "Nom Joueur",
    "role": "PLAYER",
    "credits_balance": 5
  }
}
```

#### POST /auth/logout
Déconnexion utilisateur.

**Réponse (200):**
```json
{
  "message": "Déconnexion réussie"
}
```

#### GET /auth/me
Récupérer le profil de l'utilisateur connecté.

**Réponse (200):**
```json
{
  "id": 1,
  "email": "joueur@example.com",
  "name": "Nom Joueur",
  "role": "PLAYER",
  "credits_balance": 5,
  "created_at": "2025-08-14T10:00:00Z"
}
```

#### PUT /auth/update-profile
Mettre à jour le profil utilisateur.

**Corps de la requête:**
```json
{
  "name": "Nouveau Nom",
  "phone_number": "+216 98 765 432"
}
```

#### POST /auth/change-password
Changer le mot de passe.

**Corps de la requête:**
```json
{
  "current_password": "ancien_mdp",
  "new_password": "nouveau_mdp"
}
```

---

## 👑 Administration Super Admin

### Gestion des utilisateurs

#### GET /admin/users
Récupérer tous les utilisateurs.

**Paramètres de requête:**
- `role` (optionnel): Filtrer par rôle
- `page` (optionnel): Numéro de page
- `limit` (optionnel): Nombre d'éléments par page

**Réponse (200):**
```json
{
  "users": [
    {
      "id": 1,
      "email": "joueur@example.com",
      "name": "Nom Joueur",
      "role": "PLAYER",
      "credits_balance": 5,
      "created_at": "2025-08-14T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1
}
```

#### POST /admin/users
Créer un nouvel utilisateur.

**Corps de la requête:**
```json
{
  "email": "nouveau@example.com",
  "password": "password123",
  "name": "Nouveau Utilisateur",
  "role": "PLAYER",
  "phone_number": "+216 12 345 678"
}
```

#### PUT /admin/users/{user_id}
Modifier un utilisateur.

**Corps de la requête:**
```json
{
  "name": "Nom Modifié",
  "role": "CLUB",
  "credits_balance": 10
}
```

#### DELETE /admin/users/{user_id}
Supprimer un utilisateur.

**Réponse (200):**
```json
{
  "message": "Utilisateur supprimé avec succès"
}
```

#### POST /admin/users/{user_id}/credits
Ajouter des crédits à un utilisateur.

**Corps de la requête:**
```json
{
  "credits": 10
}
```

### Gestion des clubs

#### GET /admin/clubs
Récupérer tous les clubs.

**Réponse (200):**
```json
{
  "clubs": [
    {
      "id": 1,
      "name": "Club de Padel Tunis",
      "address": "Rue de la République, Tunis",
      "phone_number": "+216 71 123 456",
      "email": "contact@clubtunis.tn",
      "created_at": "2025-08-14T10:00:00Z",
      "courts_count": 4,
      "players_count": 25
    }
  ]
}
```

#### POST /admin/clubs
Créer un nouveau club.

**Corps de la requête:**
```json
{
  "name": "Nouveau Club",
  "address": "Adresse du club",
  "phone_number": "+216 71 123 456",
  "email": "contact@nouveauclub.tn",
  "password": "password123"
}
```

#### PUT /admin/clubs/{club_id}
Modifier un club.

**Corps de la requête:**
```json
{
  "name": "Nom Modifié",
  "address": "Nouvelle adresse",
  "phone_number": "+216 71 987 654"
}
```

#### DELETE /admin/clubs/{club_id}
Supprimer un club (suppression en cascade).

**Réponse (200):**
```json
{
  "message": "Club supprimé avec succès",
  "summary": {
    "courts_deleted": 4,
    "videos_orphaned": 12,
    "users_affected": 3,
    "recording_sessions_deleted": 2
  }
}
```

### Gestion des terrains

#### GET /admin/clubs/{club_id}/courts
Récupérer les terrains d'un club.

**Réponse (200):**
```json
{
  "courts": [
    {
      "id": 1,
      "name": "Terrain 1",
      "qr_code": "QR_COURT_001",
      "camera_url": "http://camera.example.com/stream1",
      "club_id": 1,
      "is_recording": false,
      "available": true
    }
  ]
}
```

#### POST /admin/clubs/{club_id}/courts
Créer un nouveau terrain.

**Corps de la requête:**
```json
{
  "name": "Terrain 5",
  "camera_url": "http://camera.example.com/stream5"
}
```

#### PUT /admin/courts/{court_id}
Modifier un terrain.

**Corps de la requête:**
```json
{
  "name": "Terrain Central",
  "camera_url": "http://new-camera.example.com/stream"
}
```

#### DELETE /admin/courts/{court_id}
Supprimer un terrain.

### Monitoring et statistiques

#### GET /admin/dashboard
Dashboard administrateur global.

**Réponse (200):**
```json
{
  "overview": {
    "total_users": 150,
    "total_clubs": 12,
    "total_courts": 48,
    "total_videos": 1250,
    "active_recordings": 3
  },
  "recent_activity": [
    {
      "action": "user_registration",
      "details": "Nouveau joueur inscrit",
      "timestamp": "2025-08-14T10:30:00Z"
    }
  ],
  "system_health": {
    "database_status": "healthy",
    "ffmpeg_status": "available",
    "disk_space": "85% free"
  }
}
```

#### GET /admin/videos
Récupérer toutes les vidéos du système.

**Réponse (200):**
```json
{
  "videos": [
    {
      "id": 1,
      "title": "Match du 14/08/2025",
      "duration": 3600,
      "file_size": 524288000,
      "player_name": "Nom Joueur",
      "club_name": "Club de Padel Tunis",
      "court_name": "Terrain 1",
      "recorded_at": "2025-08-14T10:00:00Z"
    }
  ]
}
```

#### GET /admin/clubs/history/all
Historique global des actions.

**Réponse (200):**
```json
{
  "history": [
    {
      "id": 1,
      "action_type": "create_user",
      "user_name": "Nom Joueur",
      "club_name": "Club de Padel Tunis",
      "performed_by": "Admin",
      "performed_at": "2025-08-14T10:00:00Z",
      "details": "Création d'un nouveau joueur"
    }
  ]
}
```

---

## 🏢 Gestion Club

### Dashboard club

#### GET /clubs/dashboard
Dashboard du club connecté.

**Réponse (200):**
```json
{
  "club_info": {
    "id": 1,
    "name": "Club de Padel Tunis",
    "total_courts": 4,
    "total_players": 25,
    "total_followers": 40
  },
  "courts": [
    {
      "id": 1,
      "name": "Terrain 1",
      "occupation_status": "Disponible",
      "is_recording": false,
      "recording_player": null,
      "recording_remaining": null
    },
    {
      "id": 2,
      "name": "Terrain 2", 
      "occupation_status": "En cours d'enregistrement",
      "is_recording": true,
      "recording_player": {
        "name": "Joueur Actif",
        "email": "joueur@example.com"
      },
      "recording_remaining": 45
    }
  ],
  "recent_videos": [
    {
      "id": 1,
      "title": "Match du 14/08/2025",
      "player_name": "Nom Joueur",
      "court_name": "Terrain 1",
      "duration": 3600,
      "recorded_at": "2025-08-14T10:00:00Z"
    }
  ],
  "statistics": {
    "videos_today": 5,
    "videos_this_week": 23,
    "average_session_duration": 65
  }
}
```

### Gestion des followers

#### GET /clubs/followers
Récupérer les followers du club.

**Réponse (200):**
```json
{
  "followers": [
    {
      "id": 5,
      "name": "Nom Follower",
      "email": "follower@example.com",
      "credits_balance": 8,
      "videos_count": 12,
      "last_activity": "2025-08-14T09:30:00Z"
    }
  ]
}
```

#### PUT /clubs/{player_id}
Modifier un follower.

**Corps de la requête:**
```json
{
  "name": "Nouveau Nom",
  "phone_number": "+216 98 765 432"
}
```

#### POST /clubs/{player_id}/add-credits
Ajouter des crédits à un follower.

**Corps de la requête:**
```json
{
  "credits": 5,
  "reason": "Bonus fidélité"
}
```

### Gestion des enregistrements

#### POST /clubs/courts/{court_id}/stop-recording
Arrêter un enregistrement en cours.

**Réponse (200):**
```json
{
  "message": "Enregistrement arrêté avec succès",
  "recording_info": {
    "duration_recorded": "01:23:45",
    "file_size": "2.1 GB",
    "player": "Nom Joueur"
  }
}
```

#### POST /clubs/cleanup-expired-sessions
Nettoyer les sessions expirées.

**Réponse (200):**
```json
{
  "message": "Nettoyage terminé",
  "sessions_cleaned": 3,
  "courts_freed": 2
}
```

---

## 🎮 Fonctionnalités Joueur

### Dashboard joueur

#### GET /players/dashboard
Dashboard personnel du joueur.

**Réponse (200):**
```json
{
  "player_info": {
    "name": "Nom Joueur",
    "credits_balance": 8,
    "total_videos": 15,
    "followed_clubs": 3
  },
  "recent_videos": [
    {
      "id": 1,
      "title": "Match du 14/08/2025",
      "club_name": "Club de Padel Tunis",
      "court_name": "Terrain 1",
      "duration": 3600,
      "is_unlocked": true,
      "recorded_at": "2025-08-14T10:00:00Z"
    }
  ],
  "active_recording": {
    "id": "rec_123",
    "court_name": "Terrain 2",
    "club_name": "Club Carthage",
    "start_time": "2025-08-14T11:00:00Z",
    "planned_duration": 90,
    "remaining_minutes": 45
  },
  "statistics": {
    "total_play_time": 7200,
    "average_session": 72,
    "credits_spent": 12
  }
}
```

### Gestion des clubs

#### GET /players/clubs/available
Récupérer les clubs disponibles.

**Réponse (200):**
```json
{
  "clubs": [
    {
      "id": 1,
      "name": "Club de Padel Tunis",
      "address": "Rue de la République, Tunis",
      "courts_count": 4,
      "followers_count": 40,
      "is_followed": false
    }
  ]
}
```

#### GET /players/clubs/followed
Récupérer les clubs suivis.

**Réponse (200):**
```json
{
  "clubs": [
    {
      "id": 1,
      "name": "Club de Padel Tunis",
      "address": "Rue de la République, Tunis",
      "courts_count": 4,
      "available_courts": 2,
      "last_visit": "2025-08-14T09:00:00Z"
    }
  ]
}
```

#### POST /players/clubs/{club_id}/follow
Suivre un club.

**Réponse (200):**
```json
{
  "message": "Club suivi avec succès",
  "club": {
    "id": 1,
    "name": "Club de Padel Tunis"
  }
}
```

#### POST /players/clubs/{club_id}/unfollow
Arrêter de suivre un club.

### Gestion des vidéos

#### GET /players/videos
Récupérer les vidéos du joueur.

**Paramètres de requête:**
- `status`: `locked` ou `unlocked`
- `club_id`: Filtrer par club
- `limit`: Nombre d'éléments

**Réponse (200):**
```json
{
  "videos": [
    {
      "id": 1,
      "title": "Match du 14/08/2025",
      "club_name": "Club de Padel Tunis",
      "court_name": "Terrain 1",
      "duration": 3600,
      "file_size": 524288000,
      "is_unlocked": true,
      "credits_cost": 1,
      "recorded_at": "2025-08-14T10:00:00Z",
      "file_url": "https://cdn.example.com/video1.mp4",
      "thumbnail_url": "https://cdn.example.com/thumb1.jpg"
    }
  ],
  "summary": {
    "total_videos": 15,
    "unlocked_videos": 12,
    "locked_videos": 3
  }
}
```

#### POST /players/videos/{video_id}/unlock
Débloquer une vidéo avec des crédits.

**Réponse (200):**
```json
{
  "message": "Vidéo débloquée avec succès",
  "credits_remaining": 7,
  "video_url": "https://cdn.example.com/video1.mp4"
}
```

### Gestion des crédits

#### POST /players/credits/buy
Acheter des crédits.

**Corps de la requête:**
```json
{
  "package": "standard",
  "payment_method": "card",
  "amount": 10.0
}
```

**Réponse (200):**
```json
{
  "message": "Achat effectué avec succès",
  "credits_added": 25,
  "new_balance": 33,
  "transaction_id": "txn_123456"
}
```

#### GET /players/credits/packages
Récupérer les packs de crédits disponibles.

**Réponse (200):**
```json
{
  "packages": [
    {
      "id": "starter",
      "name": "Pack Starter",
      "credits": 10,
      "price": 5.0,
      "currency": "TND",
      "bonus": 0
    },
    {
      "id": "premium",
      "name": "Pack Premium", 
      "credits": 50,
      "price": 18.0,
      "currency": "TND",
      "bonus": 5
    }
  ]
}
```

#### GET /players/credits/history
Historique des crédits.

**Réponse (200):**
```json
{
  "transactions": [
    {
      "id": 1,
      "type": "purchase",
      "amount": 25,
      "cost": 10.0,
      "description": "Achat Pack Standard",
      "created_at": "2025-08-14T10:00:00Z"
    },
    {
      "id": 2,
      "type": "spent",
      "amount": -1,
      "description": "Déblocage vidéo #123",
      "created_at": "2025-08-14T11:00:00Z"
    }
  ]
}
```

---

## 🎬 Système d'enregistrement V3

### Démarrage d'enregistrement

#### POST /recording/v3/start
Démarrer un nouvel enregistrement.

**Corps de la requête:**
```json
{
  "court_id": 1,
  "duration_minutes": 90,
  "title": "Match amical",
  "description": "Match du samedi matin"
}
```

**Réponse (200):**
```json
{
  "success": true,
  "recording": {
    "id": "rec_abc123",
    "court_id": 1,
    "court_name": "Terrain 1",
    "club_name": "Club de Padel Tunis",
    "planned_duration": 90,
    "max_duration": 200,
    "start_time": "2025-08-14T11:00:00Z",
    "expected_end_time": "2025-08-14T12:30:00Z",
    "status": "active"
  },
  "camera_info": {
    "url": "http://camera.example.com/stream1",
    "type": "mjpeg",
    "quality": "720p"
  }
}
```

**Erreurs possibles:**
```json
{
  "success": false,
  "error": "Terrain déjà en cours d'enregistrement",
  "code": "COURT_BUSY"
}
```

```json
{
  "success": false,
  "error": "Caméra non accessible",
  "code": "CAMERA_UNAVAILABLE"
}
```

### Consultation des enregistrements

#### GET /recording/v3/my-active
Récupérer l'enregistrement actif du joueur.

**Réponse (200) - Avec enregistrement:**
```json
{
  "active_recording": {
    "id": "rec_abc123",
    "court_id": 1,
    "court_name": "Terrain 1",
    "club_id": 1,
    "club_name": "Club de Padel Tunis",
    "title": "Match amical",
    "planned_duration": 90,
    "start_time": "2025-08-14T11:00:00Z",
    "elapsed_minutes": 23,
    "remaining_minutes": 67,
    "status": "active",
    "camera_url": "http://camera.example.com/stream1"
  }
}
```

**Réponse (200) - Sans enregistrement:**
```json
{
  "active_recording": null
}
```

#### GET /recording/v3/club/active
Récupérer les enregistrements actifs du club.

**Réponse (200):**
```json
{
  "active_recordings": [
    {
      "id": "rec_abc123",
      "court_id": 1,
      "court_name": "Terrain 1",
      "title": "Match amical",
      "player": {
        "id": 5,
        "name": "Nom Joueur",
        "email": "joueur@example.com"
      },
      "planned_duration": 90,
      "elapsed_minutes": 23,
      "remaining_minutes": 67,
      "start_time": "2025-08-14T11:00:00Z",
      "status": "active"
    }
  ],
  "total_active": 1
}
```

### Terrains disponibles

#### GET /recording/v3/clubs/{club_id}/courts
Récupérer les terrains disponibles d'un club.

**Réponse (200):**
```json
{
  "courts": [
    {
      "id": 1,
      "name": "Terrain 1",
      "club_id": 1,
      "available": true,
      "is_recording": false,
      "camera_url": "http://camera.example.com/stream1",
      "qr_code": "QR_COURT_001"
    },
    {
      "id": 2,
      "name": "Terrain 2",
      "club_id": 1,
      "available": false,
      "is_recording": true,
      "current_recording": {
        "player_name": "Autre Joueur",
        "remaining_minutes": 45
      }
    }
  ],
  "club_info": {
    "id": 1,
    "name": "Club de Padel Tunis",
    "total_courts": 4,
    "available_courts": 3
  }
}
```

### Arrêt d'enregistrement

#### POST /recording/v3/stop/{recording_id}
Arrêter un enregistrement (joueur).

**Réponse (200):**
```json
{
  "success": true,
  "message": "Enregistrement arrêté avec succès",
  "recording_summary": {
    "id": "rec_abc123",
    "duration_recorded": 68,
    "file_info": {
      "size_mb": 890,
      "format": "mp4",
      "resolution": "1280x720"
    },
    "video_created": {
      "id": 15,
      "title": "Match amical",
      "file_url": "https://cdn.example.com/rec_abc123.mp4"
    }
  }
}
```

#### POST /recording/v3/force-stop/{recording_id}
Arrêt forcé d'enregistrement (club/admin).

**Corps de la requête:**
```json
{
  "reason": "Maintenance terrain"
}
```

### Maintenance

#### POST /recording/v3/cleanup-expired
Nettoyer les sessions expirées.

**Réponse (200):**
```json
{
  "message": "Nettoyage terminé",
  "summary": {
    "sessions_cleaned": 5,
    "courts_freed": 3,
    "disk_space_freed": "1.2 GB"
  }
}
```

---

## 📹 Gestion des vidéos

### Consultation des vidéos

#### GET /videos/my-videos
Récupérer les vidéos personnelles.

**Paramètres de requête:**
- `page`: Numéro de page (défaut: 1)
- `limit`: Éléments par page (défaut: 20)
- `status`: `all`, `locked`, `unlocked`

**Réponse (200):**
```json
{
  "videos": [
    {
      "id": 1,
      "title": "Match du 14/08/2025",
      "description": "Match amical du samedi",
      "duration": 3600,
      "file_size": 524288000,
      "is_unlocked": true,
      "credits_cost": 1,
      "recorded_at": "2025-08-14T10:00:00Z",
      "file_url": "https://cdn.example.com/video1.mp4",
      "thumbnail_url": "https://cdn.example.com/thumb1.jpg",
      "court": {
        "id": 1,
        "name": "Terrain 1",
        "club_name": "Club de Padel Tunis"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 15,
    "pages": 1
  }
}
```

#### GET /videos/{video_id}
Récupérer les détails d'une vidéo.

**Réponse (200):**
```json
{
  "id": 1,
  "title": "Match du 14/08/2025",
  "description": "Match amical du samedi",
  "duration": 3600,
  "file_size": 524288000,
  "is_unlocked": true,
  "file_url": "https://cdn.example.com/video1.mp4",
  "thumbnail_url": "https://cdn.example.com/thumb1.jpg",
  "recorded_at": "2025-08-14T10:00:00Z",
  "court": {
    "id": 1,
    "name": "Terrain 1",
    "club": {
      "id": 1,
      "name": "Club de Padel Tunis"
    }
  },
  "stats": {
    "views": 0,
    "downloads": 0
  }
}
```

### Modification des vidéos

#### PUT /videos/{video_id}
Modifier une vidéo.

**Corps de la requête:**
```json
{
  "title": "Nouveau titre",
  "description": "Nouvelle description"
}
```

#### DELETE /videos/{video_id}
Supprimer une vidéo.

**Réponse (200):**
```json
{
  "message": "Vidéo supprimée avec succès"
}
```

### Fonctionnalités avancées

#### POST /videos/qr-scan
Scanner un QR code de terrain.

**Corps de la requête:**
```json
{
  "qr_code": "QR_COURT_001"
}
```

**Réponse (200):**
```json
{
  "message": "QR code scanné avec succès",
  "court": {
    "id": 1,
    "name": "Terrain 1",
    "available": true,
    "camera_url": "http://camera.example.com/stream1"
  },
  "club": {
    "id": 1,
    "name": "Club de Padel Tunis",
    "address": "Rue de la République, Tunis"
  }
}
```

#### GET /videos/courts/available
Récupérer tous les terrains disponibles.

**Réponse (200):**
```json
{
  "available_courts": [
    {
      "club": {
        "id": 1,
        "name": "Club de Padel Tunis",
        "address": "Rue de la République, Tunis"
      },
      "courts": [
        {
          "id": 1,
          "name": "Terrain 1",
          "available": true,
          "camera_url": "http://camera.example.com/stream1"
        }
      ]
    }
  ],
  "total_available": 12
}
```

---

## 🚨 Gestion des erreurs

### Codes de statut HTTP
- **200**: Succès
- **201**: Créé avec succès
- **400**: Requête invalide
- **401**: Non authentifié
- **403**: Accès refusé
- **404**: Ressource non trouvée
- **409**: Conflit (ex: email déjà utilisé)
- **500**: Erreur serveur

### Format des erreurs
```json
{
  "error": "Message d'erreur explicite",
  "code": "ERROR_CODE",
  "details": {
    "field": "Détails spécifiques"
  }
}
```

### Codes d'erreur spécifiques

#### Authentification
- `INVALID_CREDENTIALS`: Identifiants incorrects
- `EMAIL_ALREADY_EXISTS`: Email déjà utilisé
- `WEAK_PASSWORD`: Mot de passe trop faible
- `SESSION_EXPIRED`: Session expirée

#### Enregistrement
- `COURT_BUSY`: Terrain déjà occupé
- `CAMERA_UNAVAILABLE`: Caméra non accessible
- `DURATION_EXCEEDED`: Durée maximale dépassée
- `INSUFFICIENT_CREDITS`: Pas assez de crédits
- `CLUB_NOT_FOLLOWED`: Club non suivi

#### Permissions
- `UNAUTHORIZED`: Non autorisé
- `ADMIN_REQUIRED`: Droits administrateur requis
- `CLUB_ACCESS_REQUIRED`: Accès club requis

---

## 📊 Exemples d'usage

### Workflow d'enregistrement complet

1. **Connexion joueur**
```bash
POST /api/auth/login
{
  "email": "joueur@example.com",
  "password": "password123"
}
```

2. **Consulter clubs suivis**
```bash
GET /api/players/clubs/followed
```

3. **Voir terrains disponibles**
```bash
GET /api/recording/v3/clubs/1/courts
```

4. **Démarrer enregistrement**
```bash
POST /api/recording/v3/start
{
  "court_id": 1,
  "duration_minutes": 90,
  "title": "Match amical"
}
```

5. **Surveiller progression**
```bash
GET /api/recording/v3/my-active
```

6. **Arrêter enregistrement**
```bash
POST /api/recording/v3/stop/rec_abc123
```

### Workflow gestion club

1. **Connexion club**
```bash
POST /api/auth/login
{
  "email": "club@example.com",
  "password": "password123"
}
```

2. **Consulter dashboard**
```bash
GET /api/clubs/dashboard
```

3. **Voir enregistrements actifs**
```bash
GET /api/recording/v3/club/active
```

4. **Arrêter enregistrement si nécessaire**
```bash
POST /api/clubs/courts/2/stop-recording
```

---

## 🔧 Notes techniques

### Limitations système
- **Durée max enregistrement**: 200 minutes par session
- **Un enregistrement par terrain**: Exclusivité terrain
- **Arrêt automatique**: À la fin de la durée planifiée
- **Nettoyage automatique**: Sessions expirées supprimées

### Formats supportés
- **Vidéo**: MP4 (H.264)
- **Streaming**: MJPEG, RTSP
- **Résolution**: Jusqu'à 1920x1080
- **Thumbnails**: JPEG

### Configuration environnement
```bash
# Variables requises
SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
FFMPEG_PATH=/usr/bin/ffmpeg
DATABASE_URL=sqlite:///app.db

# Variables optionnelles
BUNNY_STORAGE_API_KEY=bunny-api-key
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 📞 Support

Pour toute question technique ou suggestion d'amélioration, consultez la documentation du code source ou contactez l'équipe de développement.

**Version API**: v3.0
**Dernière mise à jour**: 14 août 2025
