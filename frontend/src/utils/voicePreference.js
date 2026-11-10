/**
 * voicePreference — which Gnani Timbre voice (and speed) the app speaks with.
 *
 * Stored per browser in localStorage and applied centrally in synthesizeVoiceSpeech(),
 * so the Slate companion, Oracle read-aloud and every spoken confirmation use it.
 *
 * Catalog: Gnani timbre-v2.5 voices (the model backend/server.js calls), grouped by
 * the language each voice was built for.
 */

export const GNANI_VOICE_GROUPS = [
  {
    language: 'en-IN', label: 'English',
    voices: ['Kaveri', 'Trupti', 'Devika', 'Pranav', 'Shlok', 'Girish'],
    sample: (name) => `Hello, my name is ${name}. How are you feeling today?`,
  },
  {
    language: 'hi-IN', label: 'Hindi (हिंदी)',
    voices: ['Nalini', 'Bhavna', 'Yashvi', 'Urmila', 'Jwala', 'Chitra', 'Ambuja', 'Deepak', 'Roopesh', 'Vikrant', 'Hemraj', 'Jalaj', 'Omkar'],
    sample: (name) => `नमस्ते, मेरा नाम ${name} है। आज आप कैसे हैं?`,
  },
  {
    language: 'hi-IN', label: 'Hinglish', id: 'hinglish',
    voices: ['Poorvi'],
    sample: (name) => `Hello, main ${name} hoon. Aaj aap kaise feel kar rahe ho?`,
  },
  {
    language: 'ta-IN', label: 'Tamil (தமிழ்)',
    voices: ['Asmita', 'Trisha', 'Brinda', 'Vedika', 'Noopur'],
    sample: (name) => `வணக்கம், என் பெயர் ${name}. இன்று நீங்கள் எப்படி இருக்கிறீர்கள்?`,
  },
  {
    language: 'te-IN', label: 'Telugu (తెలుగు)',
    voices: ['Suhana', 'Lehara', 'Lavanya', 'Yukti', 'Varuni'],
    sample: (name) => `నమస్కారం, నా పేరు ${name}. ఈ రోజు మీరు ఎలా ఉన్నారు?`,
  },
  {
    language: 'kn-IN', label: 'Kannada (ಕನ್ನಡ)',
    voices: ['Saanvi', 'Kavin'],
    sample: (name) => `ನಮಸ್ಕಾರ, ನನ್ನ ಹೆಸರು ${name}. ಇಂದು ನೀವು ಹೇಗಿದ್ದೀರಿ?`,
  },
  {
    language: 'ml-IN', label: 'Malayalam (മലയാളം)',
    voices: ['Reshma', 'Riyaan'],
    sample: (name) => `നമസ്കാരം, എന്റെ പേര് ${name}. ഇന്ന് നിങ്ങൾക്ക് എങ്ങനെയുണ്ട്?`,
  },
  {
    language: 'mr-IN', label: 'Marathi (मराठी)',
    voices: ['Zahira', 'Ishaan'],
    sample: (name) => `नमस्कार, माझे नाव ${name} आहे. आज तुम्ही कसे आहात?`,
  },
  {
    language: 'bn-IN', label: 'Bengali (বাংলা)',
    voices: ['Kirra', 'Dhruva'],
    sample: (name) => `নমস্কার, আমার নাম ${name}। আজ আপনি কেমন আছেন?`,
  },
  {
    language: 'gu-IN', label: 'Gujarati (ગુજરાતી)',
    voices: ['Falak', 'Veera'],
    sample: (name) => `નમસ્તે, મારું નામ ${name} છે. આજે તમે કેમ છો?`,
  },
  {
    language: 'pa-IN', label: 'Punjabi (ਪੰਜਾਬੀ)',
    voices: ['Mehuli', 'Zayan'],
    sample: (name) => `ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ਮੇਰਾ ਨਾਮ ${name} ਹੈ। ਅੱਜ ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ?`,
  },
];

export const SPEED_OPTIONS = [
  { value: 0.8, label: 'Slow' },
  { value: 0.9, label: 'Gentle' },
  { value: 1.0, label: 'Normal' },
  { value: 1.15, label: 'Brisk' },
];

const STORAGE_KEY = 'deja_gnani_voice_pref';
const CHANGE_EVENT = 'deja:voice-pref-change';
const DEFAULT_PREF = { voice: '', speed: 1.0 }; // '' = server default (GNANI_TTS_VOICE)

export function groupForVoice(voice) {
  return GNANI_VOICE_GROUPS.find((g) => g.voices.includes(voice)) || null;
}

export function getVoicePreference() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_PREF };
    const parsed = JSON.parse(raw);
    const voice = typeof parsed.voice === 'string' && groupForVoice(parsed.voice) ? parsed.voice : '';
    const speed = SPEED_OPTIONS.some((s) => s.value === parsed.speed) ? parsed.speed : 1.0;
    return { voice, speed };
  } catch {
    return { ...DEFAULT_PREF };
  }
}

export function setVoicePreference(next) {
  const merged = { ...getVoicePreference(), ...next };
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
  } catch {
    /* storage unavailable — preference lasts for this page only */
  }
  window.dispatchEvent(new CustomEvent(CHANGE_EVENT, { detail: merged }));
  return merged;
}

export function onVoicePreferenceChange(callback) {
  const handler = (e) => callback(e.detail);
  window.addEventListener(CHANGE_EVENT, handler);
  return () => window.removeEventListener(CHANGE_EVENT, handler);
}
