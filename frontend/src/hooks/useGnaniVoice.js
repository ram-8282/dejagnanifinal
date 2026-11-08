import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchVoiceStatus, transcribeVoiceAudio, synthesizeVoiceSpeech } from '../utils/api';

export const GNANI_LANGUAGES = [
  { code: 'indic-auto', label: 'Auto Detect', flag: '🇮🇳' },
  { code: 'en-IN', label: 'English', flag: '🇬🇧' },
  { code: 'hi-IN', label: 'Hindi (हिंदी)', flag: '🇮🇳' },
  { code: 'te-IN', label: 'Telugu (తెలుగు)', flag: '🇮🇳' },
  { code: 'ta-IN', label: 'Tamil (தமிழ்)', flag: '🇮🇳' },
  { code: 'kn-IN', label: 'Kannada (ಕನ್ನಡ)', flag: '🇮🇳' },
];

/**
 * useGnaniVoice — React Hook for Gnani.ai Voice Integration (REST API mode)
 *
 * Requirements:
 *   - States: selectedLanguage, orbState ('idle'|'listening'|'processing'|'speaking'|'error'), error
 *   - Methods: startListening(), stopListening(), speak(text, lang), setLanguage(langCode)
 *   - MediaRecorder audio/webm capture -> POST /api/voice/stt
 *   - Audio playback -> POST /api/voice/tts with orbState update
 */
export function useGnaniVoice({
  onTranscript,
  initialLanguage = 'indic-auto',
  defaultLanguage,
  onTranscriptUpdate,
  onFinalResult,
  maxDurationMs = 28000,
} = {}) {
  const startLang = initialLanguage || defaultLanguage || 'indic-auto';
  const [orbState, setOrbState] = useState('idle'); // 'idle' | 'listening' | 'processing' | 'speaking' | 'error'
  const [selectedLanguage, setSelectedLanguage] = useState(startLang);
  const [error, setError] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [interimText, setInterimText] = useState('');
  const [isGnaniConfigured, setIsGnaniConfigured] = useState(true);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const maxTimerRef = useRef(null);
  const activeAudioRef = useRef(null);
  const fallbackRecognitionRef = useRef(null);

  const setLanguage = useCallback((langCode) => {
    setSelectedLanguage(langCode);
  }, []);

  // Check backend Gnani capability on mount
  useEffect(() => {
    let isMounted = true;
    fetchVoiceStatus()
      .then((status) => {
        if (!isMounted) return;
        if (status && status.isConfigured !== undefined) {
          setIsGnaniConfigured(status.isConfigured);
        }
      })
      .catch((err) => {
        console.warn('Gnani voice status query failed, will fallback gracefully:', err);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (maxTimerRef.current) clearTimeout(maxTimerRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (activeAudioRef.current) {
        activeAudioRef.current.pause();
        activeAudioRef.current = null;
      }
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // Web Speech fallback recognition
  const startBrowserFallback = useCallback(() => {
    const SpeechRecognition =
      typeof window !== 'undefined'
        ? window.SpeechRecognition || window.webkitSpeechRecognition
        : null;

    if (!SpeechRecognition) {
      setError('Neither Gnani API nor Web Speech API is supported in this browser.');
      setOrbState('error');
      return;
    }

    try {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = true;
      rec.lang = selectedLanguage === 'indic-auto' ? 'en-IN' : selectedLanguage;

      rec.onstart = () => {
        setOrbState('listening');
        setError(null);
      };

      rec.onresult = (e) => {
        let text = '';
        for (let i = 0; i < e.results.length; i++) {
          text += e.results[i][0].transcript;
        }
        setTranscript(text);
        if (onTranscriptUpdate) onTranscriptUpdate(text);
      };

      rec.onerror = (e) => {
        console.error('Fallback SpeechRecognition error:', e.error);
        setError(`Microphone error: ${e.error}`);
        setOrbState('error');
      };

      rec.onend = () => {
        setOrbState('idle');
        if (transcript) {
          if (onTranscript) onTranscript(transcript);
          if (onFinalResult) onFinalResult(transcript);
        }
      };

      fallbackRecognitionRef.current = rec;
      rec.start();
    } catch (err) {
      setError(err.message || 'Speech recognition failed.');
      setOrbState('error');
    }
  }, [selectedLanguage, onTranscriptUpdate, onFinalResult, onTranscript, transcript]);

  // Start recording using MediaRecorder for Gnani REST STT
  const startListening = useCallback(async () => {
    setError(null);
    setInterimText('Recording audio…');

    // If Gnani is explicitly not configured, fallback to browser Web Speech
    if (!isGnaniConfigured) {
      startBrowserFallback();
      return;
    }

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('MediaDevices microphone API is not supported in this browser.');
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      streamRef.current = stream;
      audioChunksRef.current = [];

      let options = {};
      if (typeof MediaRecorder !== 'undefined') {
        if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
          options = { mimeType: 'audio/webm;codecs=opus' };
        } else if (MediaRecorder.isTypeSupported('audio/webm')) {
          options = { mimeType: 'audio/webm' };
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
          options = { mimeType: 'audio/mp4' };
        }
      }

      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstart = () => {
        setOrbState('listening');
        setInterimText('Listening… (Gnani Indic ASR)');
      };

      mediaRecorder.start(250); // Slice every 250ms

      // Guard: automatically stop recording before 30-second Gnani REST threshold
      if (maxTimerRef.current) clearTimeout(maxTimerRef.current);
      maxTimerRef.current = setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          stopListening();
        }
      }, maxDurationMs);
    } catch (err) {
      console.error('Failed to start microphone recording:', err);
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('Microphone access was denied. Please allow microphone permissions.');
        setOrbState('error');
      } else {
        startBrowserFallback();
      }
    }
  }, [isGnaniConfigured, maxDurationMs, startBrowserFallback]);

  // Stop recording and send audio to Gnani STT REST API
  const stopListening = useCallback(async () => {
    if (maxTimerRef.current) {
      clearTimeout(maxTimerRef.current);
      maxTimerRef.current = null;
    }

    // If browser fallback is running
    if (fallbackRecognitionRef.current) {
      try {
        fallbackRecognitionRef.current.stop();
      } catch (e) {}
      fallbackRecognitionRef.current = null;
      setOrbState('idle');
      return;
    }

    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === 'inactive') {
      setOrbState('idle');
      return;
    }

    return new Promise((resolve) => {
      recorder.onstop = async () => {
        setOrbState('processing');
        setInterimText('Transcribing with Gnani AI…');

        // Stop all mic tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }

        const mime = recorder.mimeType || 'audio/webm';
        const audioBlob = new Blob(audioChunksRef.current, { type: mime });

        if (audioBlob.size < 100) {
          setOrbState('idle');
          setInterimText('');
          resolve('');
          return;
        }

        try {
          const result = await transcribeVoiceAudio(audioBlob, selectedLanguage, 'prisma-v3.0');
          const finalStr = (result.transcript || '').trim();

          setTranscript(finalStr);
          setInterimText('');
          setOrbState('idle');

          if (onTranscript) onTranscript(finalStr);
          if (onTranscriptUpdate) onTranscriptUpdate(finalStr);
          if (onFinalResult) onFinalResult(finalStr);

          resolve(finalStr);
        } catch (err) {
          console.error('Gnani STT error, trying browser fallback:', err);
          setError(err.message || 'Gnani transcription failed');
          setOrbState('error');
          setInterimText('');
          resolve('');
        }
      };

      recorder.stop();
    });
  }, [selectedLanguage, onTranscript, onTranscriptUpdate, onFinalResult]);

  // Reset transcript state
  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimText('');
    setError(null);
  }, []);

  // Fallback browser speech synthesis
  const fallbackSpeak = useCallback((text) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setOrbState('idle');
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.onend = () => setOrbState('idle');
    utterance.onerror = () => setOrbState('idle');
    window.speechSynthesis.speak(utterance);
  }, []);

  // Text-to-Speech: Gnani Timbre REST with HTML5 Audio playback
  const speak = useCallback(
    async (text, langOverride) => {
      if (!text || !text.trim()) return;

      // Cancel any ongoing audio
      if (activeAudioRef.current) {
        activeAudioRef.current.pause();
        activeAudioRef.current = null;
      }
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }

      setOrbState('speaking');
      const lang = langOverride || (selectedLanguage === 'indic-auto' ? 'en-IN' : selectedLanguage);

      // 1. Try Gnani Timbre TTS
      if (isGnaniConfigured) {
        try {
          const audioBlob = await synthesizeVoiceSpeech({
            text: text.slice(0, 1000), // Protect payload size
            language: lang,
          });

          const audioUrl = URL.createObjectURL(audioBlob);
          const audio = new Audio(audioUrl);
          activeAudioRef.current = audio;

          audio.onended = () => {
            URL.revokeObjectURL(audioUrl);
            activeAudioRef.current = null;
            setOrbState('idle');
          };

          audio.onerror = (e) => {
            console.warn('Gnani audio playback failed, falling back to browser speech:', e);
            URL.revokeObjectURL(audioUrl);
            activeAudioRef.current = null;
            fallbackSpeak(text);
          };

          await audio.play();
          return;
        } catch (err) {
          console.warn('Gnani TTS failed, falling back to window.speechSynthesis:', err);
        }
      }

      // 2. Fallback to Browser Speech Synthesis
      fallbackSpeak(text);
    },
    [isGnaniConfigured, selectedLanguage, fallbackSpeak]
  );

  const cancelSpeech = useCallback(() => {
    if (activeAudioRef.current) {
      activeAudioRef.current.pause();
      activeAudioRef.current = null;
    }
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setOrbState('idle');
  }, []);

  return {
    orbState,
    transcript,
    interimText,
    selectedLanguage,
    setSelectedLanguage,
    setLanguage,
    isGnaniConfigured,
    error,
    errorMessage: error,
    startListening,
    stopListening,
    resetTranscript,
    speak,
    cancelSpeech,
    isSupported: typeof window !== 'undefined' && Boolean(navigator.mediaDevices || window.SpeechRecognition),
  };
}

