# Frontend Integration - PadelVar Video System

## 🎯 Guide d'Intégration Frontend

Ce document explique comment intégrer le nouveau système vidéo dans votre frontend (React, Vue, Angular, etc.).

---

## 📡 Workflow Complet

```
1. Joueur clique "Start Match Recording"
   ↓
2. Frontend → POST /api/video/session/create
   ↓
3. Backend crée session + démarre proxy
   ↓
4. Frontend reçoit session_id + local_url
   ↓
5. Frontend → POST /api/video/record/start
   ↓
6. Backend démarre FFmpeg
   ↓
7. Frontend affiche preview + statut
   ↓
8. Joueur clique "Stop Recording"
   ↓
9. Frontend → POST /api/video/record/stop
   ↓
10. Backend arrête FFmpeg + ferme session
   ↓
11. Frontend affiche lien de téléchargement
```

---

## 🔧 Exemples de Code

### React/TypeScript

```typescript
// types.ts
interface VideoSession {
  session_id: string;
  terrain_id: number;
  club_id: number;
  user_id: number;
  local_url: string;
  proxy_port: number;
  recording_active: boolean;
  verified: boolean;
}

interface RecordingStatus {
  session_id: string;
  active: boolean;
  elapsed_seconds: number;
  duration_seconds: number;
  progress_percent: number;
}

// videoApi.ts
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

// Créer une session caméra
export async function createSession(terrainId: number): Promise<VideoSession> {
  const response = await axios.post(`${API_BASE}/video/session/create`, {
    terrain_id: terrainId
  }, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  });
  
  return response.data.session;
}

// Démarrer enregistrement
export async function startRecording(
  sessionId: string, 
  durationMinutes: number = 90
): Promise<void> {
  await axios.post(`${API_BASE}/video/record/start`, {
    session_id: sessionId,
    duration_minutes: durationMinutes
  }, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  });
}

// Arrêter enregistrement
export async function stopRecording(sessionId: string): Promise<string> {
  const response = await axios.post(`${API_BASE}/video/record/stop`, {
    session_id: sessionId
  }, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  });
  
  return response.data.video_path;
}

// Obtenir le statut
export async function getRecordingStatus(sessionId: string): Promise<RecordingStatus> {
  const response = await axios.get(`${API_BASE}/video/record/status/${sessionId}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  });
  
  return response.data.status;
}

// Fermer session
export async function closeSession(sessionId: string): Promise<void> {
  await axios.post(`${API_BASE}/video/session/close`, {
    session_id: sessionId
  }, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  });
}
```

### Composant React - Enregistrement Match

```typescript
// MatchRecorder.tsx
import React, { useState, useEffect } from 'react';
import { 
  createSession, 
  startRecording, 
  stopRecording, 
  getRecordingStatus,
  closeSession 
} from './videoApi';

interface Props {
  terrainId: number;
  durationMinutes?: number;
}

export const MatchRecorder: React.FC<Props> = ({ 
  terrainId, 
  durationMinutes = 90 
}) => {
  const [session, setSession] = useState<VideoSession | null>(null);
  const [recording, setRecording] = useState(false);
  const [status, setStatus] = useState<RecordingStatus | null>(null);
  const [videoPath, setVideoPath] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Polling du statut toutes les 5 secondes
  useEffect(() => {
    if (!session || !recording) return;

    const interval = setInterval(async () => {
      try {
        const newStatus = await getRecordingStatus(session.session_id);
        setStatus(newStatus);
        
        // Si l'enregistrement est terminé automatiquement
        if (!newStatus.active) {
          setRecording(false);
        }
      } catch (err) {
        console.error('Error fetching status:', err);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [session, recording]);

  const handleStartRecording = async () => {
    try {
      setError(null);
      
      // 1. Créer session
      const newSession = await createSession(terrainId);
      setSession(newSession);
      
      // 2. Démarrer enregistrement
      await startRecording(newSession.session_id, durationMinutes);
      setRecording(true);
      
    } catch (err: any) {
      setError(err.response?.data?.error || 'Erreur lors du démarrage');
      console.error(err);
    }
  };

  const handleStopRecording = async () => {
    if (!session) return;
    
    try {
      setError(null);
      
      // Arrêter enregistrement
      const path = await stopRecording(session.session_id);
      setVideoPath(path);
      setRecording(false);
      
      // Fermer session
      await closeSession(session.session_id);
      setSession(null);
      
    } catch (err: any) {
      setError(err.response?.data?.error || 'Erreur lors de l\'arrêt');
      console.error(err);
    }
  };

  return (
    <div className="match-recorder">
      <h2>Enregistrement Match - Terrain {terrainId}</h2>
      
      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}
      
      {!recording && !videoPath && (
        <button 
          onClick={handleStartRecording}
          className="btn-start"
        >
          🎬 Démarrer Enregistrement ({durationMinutes} min)
        </button>
      )}
      
      {recording && status && (
        <div className="recording-status">
          <h3>🔴 Enregistrement en cours...</h3>
          
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${status.progress_percent}%` }}
            />
          </div>
          
          <p>
            Temps écoulé : {Math.floor(status.elapsed_seconds / 60)} min
            / {Math.floor(status.duration_seconds / 60)} min
          </p>
          
          <p>Progression : {status.progress_percent}%</p>
          
          <button 
            onClick={handleStopRecording}
            className="btn-stop"
          >
            ⏹️ Arrêter Enregistrement
          </button>
          
          {/* Preview */}
          {session && (
            <div className="preview">
              <h4>Preview en direct :</h4>
              <img 
                src={`/api/preview/${session.session_id}/stream.mjpeg`}
                alt="Live Preview"
                style={{ maxWidth: '100%', borderRadius: '8px' }}
              />
            </div>
          )}
        </div>
      )}
      
      {videoPath && (
        <div className="recording-complete">
          <h3>✅ Enregistrement Terminé !</h3>
          <p>Vidéo créée : {videoPath}</p>
          <a 
            href={`/api/video/files/${session?.session_id}/download?club_id=1`}
            download
            className="btn-download"
          >
            📥 Télécharger la Vidéo
          </a>
        </div>
      )}
    </div>
  );
};
```

### Composant React - Preview Snapshot (Polling)

```typescript
// SnapshotPreview.tsx
import React, { useState, useEffect } from 'react';

interface Props {
  sessionId: string;
  fps?: number; // Frames par seconde
}

export const SnapshotPreview: React.FC<Props> = ({ 
  sessionId, 
  fps = 5 
}) => {
  const [timestamp, setTimestamp] = useState(Date.now());
  const [error, setError] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setTimestamp(Date.now());
    }, 1000 / fps);

    return () => clearInterval(interval);
  }, [fps]);

  const handleError = () => {
    setError(true);
    console.error('Preview snapshot error');
  };

  const handleLoad = () => {
    setError(false);
  };

  return (
    <div className="snapshot-preview">
      {error ? (
        <div className="preview-error">
          ❌ Preview non disponible
        </div>
      ) : (
        <img
          src={`/api/preview/${sessionId}/snapshot.jpg?t=${timestamp}`}
          alt="Live Preview"
          onError={handleError}
          onLoad={handleLoad}
          style={{
            maxWidth: '100%',
            borderRadius: '8px',
            border: '2px solid #ccc'
          }}
        />
      )}
    </div>
  );
};
```

---

## 🎨 Exemples CSS

```css
/* MatchRecorder.css */
.match-recorder {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.error-message {
  background: #ff4444;
  color: white;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.btn-start, .btn-stop, .btn-download {
  padding: 15px 30px;
  font-size: 18px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s;
}

.btn-start {
  background: #4CAF50;
  color: white;
}

.btn-start:hover {
  background: #45a049;
}

.btn-stop {
  background: #f44336;
  color: white;
}

.btn-stop:hover {
  background: #da190b;
}

.btn-download {
  background: #2196F3;
  color: white;
  text-decoration: none;
  display: inline-block;
}

.btn-download:hover {
  background: #0b7dda;
}

.recording-status {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
}

.progress-bar {
  width: 100%;
  height: 30px;
  background: #e0e0e0;
  border-radius: 15px;
  overflow: hidden;
  margin: 20px 0;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #8BC34A);
  transition: width 0.5s ease;
}

.preview {
  margin-top: 20px;
  border-top: 2px solid #ddd;
  padding-top: 20px;
}

.recording-complete {
  background: #e8f5e9;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}
```

---

## 🔥 Vue.js 3 (Composition API)

```vue
<!-- MatchRecorder.vue -->
<template>
  <div class="match-recorder">
    <h2>Enregistrement Match - Terrain {{ terrainId }}</h2>
    
    <div v-if="error" class="error-message">
      ❌ {{ error }}
    </div>
    
    <button 
      v-if="!recording && !videoPath"
      @click="startRecording"
      class="btn-start"
    >
      🎬 Démarrer Enregistrement ({{ durationMinutes }} min)
    </button>
    
    <div v-if="recording && status" class="recording-status">
      <h3>🔴 Enregistrement en cours...</h3>
      
      <div class="progress-bar">
        <div 
          class="progress-fill" 
          :style="{ width: status.progress_percent + '%' }"
        />
      </div>
      
      <p>
        Temps écoulé : {{ Math.floor(status.elapsed_seconds / 60) }} min
        / {{ Math.floor(status.duration_seconds / 60) }} min
      </p>
      
      <p>Progression : {{ status.progress_percent }}%</p>
      
      <button @click="stopRecording" class="btn-stop">
        ⏹️ Arrêter Enregistrement
      </button>
      
      <!-- Preview -->
      <div v-if="session" class="preview">
        <h4>Preview en direct :</h4>
        <img 
          :src="`/api/preview/${session.session_id}/stream.mjpeg`"
          alt="Live Preview"
          style="max-width: 100%; border-radius: 8px;"
        />
      </div>
    </div>
    
    <div v-if="videoPath" class="recording-complete">
      <h3>✅ Enregistrement Terminé !</h3>
      <p>Vidéo créée : {{ videoPath }}</p>
      <a 
        :href="`/api/video/files/${session?.session_id}/download?club_id=1`"
        download
        class="btn-download"
      >
        📥 Télécharger la Vidéo
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue';
import axios from 'axios';

interface Props {
  terrainId: number;
  durationMinutes?: number;
}

const props = withDefaults(defineProps<Props>(), {
  durationMinutes: 90
});

const session = ref<any>(null);
const recording = ref(false);
const status = ref<any>(null);
const videoPath = ref<string | null>(null);
const error = ref<string | null>(null);

let statusInterval: any = null;

// Polling du statut
watch([session, recording], ([newSession, newRecording]) => {
  if (statusInterval) {
    clearInterval(statusInterval);
  }
  
  if (newSession && newRecording) {
    statusInterval = setInterval(async () => {
      try {
        const response = await axios.get(
          `/api/video/record/status/${newSession.session_id}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        );
        
        status.value = response.data.status;
        
        if (!response.data.status.active) {
          recording.value = false;
        }
      } catch (err) {
        console.error('Error fetching status:', err);
      }
    }, 5000);
  }
});

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval);
  }
});

async function startRecording() {
  try {
    error.value = null;
    
    // Créer session
    const sessionResponse = await axios.post(
      '/api/video/session/create',
      { terrain_id: props.terrainId },
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    );
    
    session.value = sessionResponse.data.session;
    
    // Démarrer enregistrement
    await axios.post(
      '/api/video/record/start',
      {
        session_id: session.value.session_id,
        duration_minutes: props.durationMinutes
      },
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    );
    
    recording.value = true;
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erreur lors du démarrage';
    console.error(err);
  }
}

async function stopRecording() {
  if (!session.value) return;
  
  try {
    error.value = null;
    
    const response = await axios.post(
      '/api/video/record/stop',
      { session_id: session.value.session_id },
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    );
    
    videoPath.value = response.data.video_path;
    recording.value = false;
    
    // Fermer session
    await axios.post(
      '/api/video/session/close',
      { session_id: session.value.session_id },
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    );
    
    session.value = null;
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erreur lors de l\'arrêt';
    console.error(err);
  }
}
</script>

<style scoped>
/* Import CSS depuis ci-dessus */
</style>
```

---

## 📱 Exemple Mobile (React Native)

```typescript
// MatchRecorder.native.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, Button, Image, Alert } from 'react-native';
import axios from 'axios';

export const MatchRecorder = ({ terrainId, durationMinutes = 90 }) => {
  const [session, setSession] = useState(null);
  const [recording, setRecording] = useState(false);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    if (!session || !recording) return;

    const interval = setInterval(async () => {
      try {
        const response = await axios.get(
          `http://localhost:5000/api/video/record/status/${session.session_id}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );
        
        setStatus(response.data.status);
        
        if (!response.data.status.active) {
          setRecording(false);
          Alert.alert('Terminé', 'Enregistrement terminé automatiquement');
        }
      } catch (err) {
        console.error(err);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [session, recording]);

  const handleStart = async () => {
    try {
      // Créer session
      const sessionRes = await axios.post(
        'http://localhost:5000/api/video/session/create',
        { terrain_id: terrainId },
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      setSession(sessionRes.data.session);
      
      // Démarrer enregistrement
      await axios.post(
        'http://localhost:5000/api/video/record/start',
        {
          session_id: sessionRes.data.session.session_id,
          duration_minutes: durationMinutes
        },
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      setRecording(true);
    } catch (err) {
      Alert.alert('Erreur', err.response?.data?.error || 'Erreur démarrage');
    }
  };

  const handleStop = async () => {
    try {
      await axios.post(
        'http://localhost:5000/api/video/record/stop',
        { session_id: session.session_id },
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      setRecording(false);
      Alert.alert('Succès', 'Enregistrement arrêté');
    } catch (err) {
      Alert.alert('Erreur', err.response?.data?.error || 'Erreur arrêt');
    }
  };

  return (
    <View style={{ padding: 20 }}>
      <Text style={{ fontSize: 20, marginBottom: 20 }}>
        Terrain {terrainId}
      </Text>
      
      {!recording ? (
        <Button
          title={`🎬 Démarrer (${durationMinutes} min)`}
          onPress={handleStart}
        />
      ) : (
        <>
          <Text style={{ fontSize: 18, color: 'red', marginBottom: 10 }}>
            🔴 Enregistrement en cours...
          </Text>
          
          {status && (
            <Text>
              Progression: {status.progress_percent}% 
              ({Math.floor(status.elapsed_seconds / 60)} min)
            </Text>
          )}
          
          {session && (
            <Image
              source={{
                uri: `http://localhost:5000/api/preview/${session.session_id}/snapshot.jpg?t=${Date.now()}`
              }}
              style={{ width: '100%', height: 200, marginVertical: 10 }}
            />
          )}
          
          <Button
            title="⏹️ Arrêter"
            onPress={handleStop}
            color="red"
          />
        </>
      )}
    </View>
  );
};
```

---

## 🚀 Résumé

**Workflow simplifié :**

1. `createSession(terrainId)` → obtenir `session_id`
2. `startRecording(session_id, duration)` → lancer FFmpeg
3. Polling `getRecordingStatus(session_id)` → afficher progression
4. Afficher preview : `<img src="/api/preview/{session_id}/stream.mjpeg" />`
5. `stopRecording(session_id)` → obtenir `video_path`
6. Télécharger vidéo : `/api/video/files/{session_id}/download`

**Support multi-plateformes :** React, Vue, Angular, React Native, etc.  
**Preview :** MJPEG stream ou polling de snapshots JPEG  
**Sécurité :** Token JWT dans tous les headers  
**Robustesse :** Gestion erreurs + cleanup automatique  

---

**Documentation complète** : `VIDEO_SYSTEM_README.md` + `MIGRATION_VIDEO_SYSTEM.md`
