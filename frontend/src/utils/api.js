/**
 * Déjà API utility layer.
 * Profile is read from the Supabase session (user UUID).
 * Falls back to 'default_user' for unauthenticated contexts.
 */

import { supabase } from '../lib/supabase';
import { getVoicePreference } from './voicePreference';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5051';

/** Get the current user's ID to use as the profile key, plus access token */
async function getProfileAndToken() {
  const { data: { session } } = await supabase.auth.getSession();
  return {
    profile: session?.user?.id || 'default_user',
    token: session?.access_token || null
  };
}

function headers(profile, token) {
  const h = {
    'Content-Type': 'application/json',
    'x-user-profile': profile,
  };
  if (token) {
    h['x-user-token'] = token;
  }
  return h;
}

async function request(method, path, body, profileOverride, signal) {
  const { profile, token } = await getProfileAndToken();
  const finalProfile = profileOverride || profile;
  const options = {
    method,
    headers: headers(finalProfile, token),
    body: body ? JSON.stringify(body) : undefined,
  };
  if (signal) {
    options.signal = signal;
  }
  const res = await fetch(`${BASE_URL}${path}`, options);
  if (!res.ok) {
    let errPayload = { message: res.statusText };
    try {
      errPayload = await res.json();
    } catch (e) {
      // Non-JSON response
    }
    console.error('Frontend Network Rejection:', errPayload);
    throw new Error(errPayload.message || errPayload.error || `HTTP ${res.status}`);
  }
  return res.json();
}

/** Phase 2 — Ingest a journal entry into memory */
export async function ingestEntry({ text, isSnippet, timestamp, force_save }) {
  const entryTimestamp = timestamp || new Date().toISOString();
  return request('POST', '/api/memory/ingest', { text, isSnippet, timestamp: entryTimestamp, force_save });
}

/** Phase 3 — Oracle: semantic recovery query */
export async function recoverMemory({ question, state, signal }) {
  return request('POST', '/api/memory/recover', { question, state }, null, signal);
}

/** Phase 3 — Blindspots: fetch long-term analytics */
export async function fetchBlindspots({ force_refresh } = {}) {
  const path = force_refresh ? '/api/memory/blindspots?force_refresh=true' : '/api/memory/blindspots';
  return request('GET', path, null);
}

/** Phase 1 Overhaul — Update an existing journal entry in memory */
export async function updateEntry({ entryId, originalText, newText }) {
  return request('PUT', '/api/memory/update', { entryId, originalText, newText });
}

/** Phase 7B — Intentional Forgetting: Dissolve a semantic connection */
export async function forgetMemory({ topic, entryId }) {
  return request('POST', '/api/memory/forget', { topic, entryId });
}

/** Phase 7B — Oracle Optimization: Reinforce graph weights based on feedback */
export async function improveMemory({ helpful, context }) {
  return request('POST', '/api/memory/improve', { helpful, context });
}

/** Generate feedback text via LLM */
export async function generateFeedback({ helpful, context, scenario }) {
  return request('POST', '/api/memory/generate_feedback', { helpful, context, scenario });
}

/** Fetch historical timeline from Supabase */
export async function fetchTimeline() {
  return request('GET', '/api/memory/timeline', null);
}

/** Health check */
export async function healthCheck() {
  return request('GET', '/api/health');
}

/** ── Gnani Voice Engine Helpers ────────────────────────── */

/** Fetch Gnani voice status & supported languages */
export async function fetchVoiceStatus() {
  return request('GET', '/api/voice/status');
}

/** Transcribe an audio Blob via Gnani Prisma REST API */
export async function transcribeVoiceAudio(audioBlob, language = 'indic-auto', model = 'prisma-v3.0') {
  const { profile, token } = await getProfileAndToken();
  const formData = new FormData();
  
  // Ensure audio blob is sent as audio/wav with recording.wav filename
  const wavBlob = audioBlob.type === 'audio/wav' 
    ? audioBlob 
    : new Blob([audioBlob], { type: 'audio/wav' });

  const filename = 'recording.wav';
  formData.append('audio', wavBlob, filename);
  formData.append('language', language);
  formData.append('language_code', language);
  formData.append('model', model);

  const h = {
    'x-user-profile': profile,
  };
  if (token) {
    h['x-user-token'] = token;
  }

  console.log(`[API /api/voice/stt] Sending POST request. Filename: ${filename}, Size: ${audioBlob.size} B, Type: ${audioBlob.type}, Lang: ${language}, Model: ${model}`);

  const res = await fetch(`${BASE_URL}/api/voice/stt`, {
    method: 'POST',
    headers: h,
    body: formData,
  });

  console.log(`[API /api/voice/stt] Received response status: ${res.status} ${res.statusText}`);

  if (!res.ok) {
    let errPayload = { message: res.statusText };
    try {
      errPayload = await res.json();
    } catch (e) {
      // Non-JSON response
    }
    console.error('[API /api/voice/stt] Request failed with HTTP', res.status, errPayload);
    const errMsg = errPayload.error?.message || errPayload.message || (typeof errPayload.error === 'string' ? errPayload.error : JSON.stringify(errPayload.error)) || `HTTP ${res.status}`;
    throw new Error(errMsg);
  }

  const json = await res.json();
  console.log('[API /api/voice/stt] Response JSON payload:', json);
  return json;
}

/** Synthesize speech from text via Gnani Timbre REST API */
export async function synthesizeVoiceSpeech({ text, language, voice, speed }) {
  // Fall back to the voice/speed the person picked in the Voice picker.
  const pref = getVoicePreference();
  voice = voice || pref.voice || undefined;
  speed = typeof speed === 'number' ? speed : pref.speed;
  const { profile, token } = await getProfileAndToken();
  const h = {
    'Content-Type': 'application/json',
    'x-user-profile': profile,
  };
  if (token) {
    h['x-user-token'] = token;
  }

  const res = await fetch(`${BASE_URL}/api/voice/tts`, {
    method: 'POST',
    headers: h,
    body: JSON.stringify({ text, language, voice, speed }),
  });

  if (!res.ok) {
    let errPayload = { message: res.statusText };
    try {
      errPayload = await res.json();
    } catch (e) {
      // Non-JSON response
    }
    console.error('Gnani TTS Frontend Rejection:', errPayload);
    throw new Error(errPayload.message || errPayload.error || `HTTP ${res.status}`);
  }

  return res.blob();
}
