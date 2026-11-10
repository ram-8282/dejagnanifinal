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

// Convert audio chunks into valid WAV Blob with 44-byte RIFF header
async function convertChunksToWav(chunks, recorderMime) {
  try {
    const rawBlob = new Blob(chunks, { type: recorderMime || 'audio/webm' });
    const AudioCtx = typeof window !== 'undefined' && (window.AudioContext || window.webkitAudioContext);
    if (!AudioCtx) {
      return new Blob(chunks, { type: 'audio/wav' });
    }
    const audioCtx = new AudioCtx();
    const arrayBuf = await rawBlob.arrayBuffer();
    const audioBuf = await audioCtx.decodeAudioData(arrayBuf);
    await audioCtx.close();

    const sampleRate = audioBuf.sampleRate || 16000;
    const numChannels = 1;
    const bitDepth = 16;
    
    // Mix to mono PCM
    let samples;
    if (audioBuf.numberOfChannels === 1) {
      samples = audioBuf.getChannelData(0);
    } else {
      const ch0 = audioBuf.getChannelData(0);
      const ch1 = audioBuf.getChannelData(1);
      samples = new Float32Array(ch0.length);
      for (let i = 0; i < ch0.length; i++) {
        samples[i] = (ch0[i] + ch1[i]) / 2;
      }
    }

    const bytesPerSample = bitDepth / 8;
    const blockAlign = numChannels * bytesPerSample;
    const byteRate = sampleRate * blockAlign;
    const dataSize = samples.length * bytesPerSample;
    const wavBuffer = new ArrayBuffer(44 + dataSize);
    const view = new DataView(wavBuffer);

    const writeString = (offset, str) => {
      for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
    };

    writeString(0, 'RIFF');
    view.setUint32(4, 36 + dataSize, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, byteRate, true);
    view.setUint16(32, blockAlign, true);
    view.setUint16(34, bitDepth, true);
    writeString(36, 'data');
    view.setUint32(40, dataSize, true);

    let offset = 44;
    for (let i = 0; i < samples.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }

    return new Blob([wavBuffer], { type: 'audio/wav' });
  } catch (err) {
    console.warn('[useGnaniVoice] AudioContext WAV conversion fallback:', err);
    return new Blob(chunks, { type: 'audio/wav' });
  }
}

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
  const fallbackTextRef = useRef('');
  // When set, the next transcript resolves this promise (listenOnce) instead of calling onTranscript.
  const onceResolverRef = useRef(null);
  // Resolves the promise returned by speak() when playback is interrupted.
  const speakResolverRef = useRef(null);

  const settleOnce = useCallback((text) => {
    const resolve = onceResolverRef.current;
    if (!resolve) return false;
    onceResolverRef.current = null;
    resolve(text || '');
    return true;
  }, []);

  const finishSpeaking = useCallback(() => {
    const resolve = speakResolverRef.current;
    speakResolverRef.current = null;
    if (resolve) resolve();
  }, []);

  const setLanguage = useCallback((langCode) => {
    console.log('[useGnaniVoice] setLanguage called with:', langCode);
    setSelectedLanguage(langCode);
  }, []);

  // Synchronize selectedLanguage whenever initialLanguage prop changes
  useEffect(() => {
    if (initialLanguage) {
      setSelectedLanguage(initialLanguage);
    }
  }, [initialLanguage]);

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
      settleOnce('');
      return;
    }

    try {
      fallbackTextRef.current = '';
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
        fallbackTextRef.current = text;
        setTranscript(text);
        if (onTranscriptUpdate && !onceResolverRef.current) onTranscriptUpdate(text);
      };

      rec.onerror = (e) => {
        console.error('Fallback SpeechRecognition error:', e.error);
        if (settleOnce('')) {
          setOrbState('idle');
          return;
        }
        setError(`Microphone error: ${e.error}`);
        setOrbState('error');
      };

      rec.onend = () => {
        fallbackRecognitionRef.current = null;
        setOrbState((s) => (s === 'error' ? s : 'idle'));
        const finalText = fallbackTextRef.current.trim();
        if (settleOnce(finalText)) return;
        if (finalText) {
          if (onTranscript) onTranscript(finalText);
          if (onFinalResult) onFinalResult(finalText);
        }
      };

      fallbackRecognitionRef.current = rec;
      rec.start();
    } catch (err) {
      setError(err.message || 'Speech recognition failed.');
      setOrbState('error');
      settleOnce('');
    }
  }, [selectedLanguage, onTranscriptUpdate, onFinalResult, onTranscript, settleOnce]);

  // Start recording using MediaRecorder for Gnani REST STT
  const startListening = useCallback(async ({ maxDurationMs: durationOverride } = {}) => {
    setError(null);
    setInterimText('Recording audio…');
    console.log('[useGnaniVoice] startListening invoked. Language:', selectedLanguage, 'Gnani configured:', isGnaniConfigured);

    // If Gnani is explicitly not configured, fallback to browser Web Speech
    if (!isGnaniConfigured) {
      console.warn('[useGnaniVoice] Gnani is not configured, redirecting to browser Web Speech fallback.');
      startBrowserFallback();
      return;
    }

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('MediaDevices microphone API is not supported in this browser.');
      }

      console.log('[useGnaniVoice] Requesting microphone access with navigator.mediaDevices.getUserMedia...');
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      console.log('[useGnaniVoice] getUserMedia stream acquired successfully. Stream ID:', stream.id, 'Tracks:', stream.getAudioTracks().map(t => `${t.label} (enabled: ${t.enabled})`));
      streamRef.current = stream;
      audioChunksRef.current = [];

      let options = {};
      if (typeof MediaRecorder !== 'undefined') {
        if (MediaRecorder.isTypeSupported('audio/wav')) {
          options = { mimeType: 'audio/wav' };
        } else if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
          options = { mimeType: 'audio/webm;codecs=opus' };
        } else if (MediaRecorder.isTypeSupported('audio/webm')) {
          options = { mimeType: 'audio/webm' };
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
          options = { mimeType: 'audio/mp4' };
        }
      }
      console.log('[useGnaniVoice] Initializing MediaRecorder with options:', options);

      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.onstart = () => {
        console.log('[useGnaniVoice] MediaRecorder onstart. State:', mediaRecorder.state, 'MimeType:', mediaRecorder.mimeType);
        setOrbState('listening');
        setInterimText('Listening… (Gnani Indic ASR)');
      };

      mediaRecorder.ondataavailable = (event) => {
        console.log('[useGnaniVoice] MediaRecorder ondataavailable. Chunk size:', event.data?.size, 'bytes, type:', event.data?.type);
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onerror = (event) => {
        console.error('[useGnaniVoice] MediaRecorder error event:', event.error);
        setError(`MediaRecorder error: ${event.error?.message || event.error}`);
        setOrbState('error');
      };

      mediaRecorder.start(250); // Slice every 250ms
      console.log('[useGnaniVoice] MediaRecorder started with 250ms slices.');

      // Guard: automatically stop recording before max duration threshold
      if (maxTimerRef.current) clearTimeout(maxTimerRef.current);
      maxTimerRef.current = setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          console.log('[useGnaniVoice] Max duration reached, stopping recording automatically...');
          stopListening();
        }
      }, durationOverride || maxDurationMs);
    } catch (err) {
      console.error('[useGnaniVoice] getUserMedia error:', {
        name: err.name,
        message: err.message,
        stack: err.stack,
      });
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('Microphone access was denied. Please allow microphone permissions in browser settings.');
        setOrbState('error');
        settleOnce('');
      } else {
        setError(`Microphone error: ${err.message || err.name}`);
        setOrbState('error');
        console.warn('[useGnaniVoice] getUserMedia failed, attempting browser fallback...');
        startBrowserFallback();
      }
    }
  }, [isGnaniConfigured, maxDurationMs, startBrowserFallback, selectedLanguage, settleOnce]);

  // Stop recording and send audio to Gnani STT REST API
  const stopListening = useCallback(async () => {
    console.log('[useGnaniVoice] stopListening invoked. Current orbState:', orbState);
    if (maxTimerRef.current) {
      clearTimeout(maxTimerRef.current);
      maxTimerRef.current = null;
    }

    // If browser fallback is running
    if (fallbackRecognitionRef.current) {
      console.log('[useGnaniVoice] Stopping active fallback speech recognition...');
      try {
        fallbackRecognitionRef.current.stop();
      } catch (e) {}
      fallbackRecognitionRef.current = null;
      setOrbState('idle');
      return;
    }

    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === 'inactive') {
      console.log('[useGnaniVoice] MediaRecorder is not recording or already inactive.');
      setOrbState('idle');
      return;
    }

    return new Promise((resolve) => {
      let isHandled = false;

      const cleanupRecorder = () => {
        if (recorder) {
          recorder.onstop = null;
          recorder.ondataavailable = null;
          recorder.onerror = null;
        }
      };

      recorder.onstop = async () => {
        if (isHandled) return;
        isHandled = true;
        cleanupRecorder();

        console.log('[useGnaniVoice] MediaRecorder onstop event fired. State:', recorder.state);
        setOrbState('processing');
        setInterimText('Transcribing with Gnani AI…');

        // Stop all mic tracks
        if (streamRef.current) {
          console.log('[useGnaniVoice] Stopping microphone audio stream tracks...');
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }

        let audioBlob;
        try {
          audioBlob = await convertChunksToWav(audioChunksRef.current, recorder.mimeType);
        } catch (e) {
          audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        }
        console.log('[useGnaniVoice] MediaRecorder onstop complete. Total audio chunks:', audioChunksRef.current.length, 'Aggregated WAV Blob size:', audioBlob.size, 'bytes, MIME:', audioBlob.type);

        if (audioBlob.size < 100) {
          console.warn('[useGnaniVoice] Audio blob too small (< 100 bytes). Aborting STT transcription.');
          setOrbState('idle');
          setInterimText('');
          settleOnce('');
          resolve('');
          return;
        }

        try {
          console.log('[useGnaniVoice] Dispatching STT request to /api/voice/stt:', {
            language: selectedLanguage,
            model: 'prisma-v3.0',
            blobSize: audioBlob.size,
            blobType: audioBlob.type,
          });

          const result = await transcribeVoiceAudio(audioBlob, selectedLanguage, 'prisma-v3.0');
          console.log('[useGnaniVoice] /api/voice/stt returned response:', result);

          const finalStr = (result.transcript || '').trim();
          console.log('[useGnaniVoice] Extracted transcript text:', finalStr);

          setInterimText('');
          setOrbState('idle');

          // A short spoken reply (listenOnce) goes back to its caller, not into the draft.
          if (settleOnce(finalStr)) {
            resolve(finalStr);
            return;
          }

          setTranscript(finalStr);
          if (onTranscript) {
            console.log('[useGnaniVoice] Calling onTranscript callback once with:', finalStr);
            onTranscript(finalStr);
          }

          resolve(finalStr);
        } catch (err) {
          console.error('[useGnaniVoice] STT transcription failed with error:', err);
          setInterimText('');
          if (settleOnce('')) {
            setOrbState('idle');
          } else {
            setError(err.message || 'Gnani transcription failed');
            setOrbState('error');
          }
          resolve('');
        }
      };

      console.log('[useGnaniVoice] Calling mediaRecorder.stop()...');
      recorder.stop();
    });
  }, [selectedLanguage, onTranscript, onTranscriptUpdate, onFinalResult, orbState, settleOnce]);

  /**
   * Record a short spoken reply (e.g. "yes", "yesterday") and resolve with its text.
   * Does not touch the draft / onTranscript. Resolves '' on silence, error or abort.
   */
  const listenOnce = useCallback((durationMs = 6000) => {
    settleOnce('');
    return new Promise((resolve) => {
      onceResolverRef.current = resolve;
      startListening({ maxDurationMs: durationMs });
    });
  }, [startListening, settleOnce]);

  /** Stop any recording immediately and discard the audio. */
  const abortListening = useCallback(() => {
    if (maxTimerRef.current) {
      clearTimeout(maxTimerRef.current);
      maxTimerRef.current = null;
    }
    if (fallbackRecognitionRef.current) {
      const rec = fallbackRecognitionRef.current;
      fallbackRecognitionRef.current = null;
      rec.onend = null;
      rec.onerror = null;
      try { rec.abort(); } catch (e) {}
    }
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      recorder.onstop = null;
      recorder.ondataavailable = null;
      recorder.onerror = null;
      try { recorder.stop(); } catch (e) {}
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setInterimText('');
    setOrbState('idle');
    settleOnce('');
  }, [settleOnce]);

  // Reset transcript state
  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimText('');
    setError(null);
  }, []);

  const speakTokenRef = useRef(0);

  // Stop whatever is currently playing and release anyone awaiting speak().
  const stopAudio = useCallback(() => {
    if (activeAudioRef.current) {
      activeAudioRef.current.pause();
      activeAudioRef.current = null;
    }
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    finishSpeaking();
  }, [finishSpeaking]);

  // Fallback browser speech synthesis — resolves when the utterance ends.
  const fallbackSpeak = useCallback((text, lang) => new Promise((resolve) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setOrbState('idle');
      resolve();
      return;
    }
    speakResolverRef.current = resolve;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    if (lang) utterance.lang = lang;
    const done = () => {
      setOrbState((s) => (s === 'speaking' ? 'idle' : s));
      finishSpeaking();
    };
    utterance.onend = done;
    utterance.onerror = done;
    window.speechSynthesis.speak(utterance);
  }), [finishSpeaking]);

  /**
   * Text-to-Speech: Gnani Timbre REST with HTML5 Audio playback.
   * Returns a promise that resolves once the speech has finished (or was cancelled),
   * so callers can listen for a reply right after asking a question.
   */
  const speak = useCallback(
    async (text, langOverride) => {
      if (!text || !text.trim()) return;

      stopAudio();
      const token = ++speakTokenRef.current;

      setOrbState('speaking');
      const lang = langOverride || (selectedLanguage === 'indic-auto' ? 'en-IN' : selectedLanguage);

      // 1. Try Gnani Timbre TTS
      if (isGnaniConfigured) {
        try {
          const audioBlob = await synthesizeVoiceSpeech({
            text: text.slice(0, 1000), // Protect payload size
            language: lang,
          });
          if (token !== speakTokenRef.current) return; // cancelled while synthesizing

          const audioUrl = URL.createObjectURL(audioBlob);
          const audio = new Audio(audioUrl);
          activeAudioRef.current = audio;

          const played = await new Promise((resolve) => {
            speakResolverRef.current = () => resolve(true);
            audio.onended = () => resolve(true);
            audio.onerror = (e) => {
              console.warn('Gnani audio playback failed, falling back to browser speech:', e);
              resolve(false);
            };
            audio.play().catch(() => resolve(false));
          });

          URL.revokeObjectURL(audioUrl);
          if (activeAudioRef.current === audio) activeAudioRef.current = null;
          speakResolverRef.current = null;
          if (played || token !== speakTokenRef.current) {
            if (token === speakTokenRef.current) setOrbState((s) => (s === 'speaking' ? 'idle' : s));
            return;
          }
        } catch (err) {
          console.warn('Gnani TTS failed, falling back to window.speechSynthesis:', err);
          if (token !== speakTokenRef.current) return;
        }
      }

      // 2. Fallback to Browser Speech Synthesis
      await fallbackSpeak(text, lang);
    },
    [isGnaniConfigured, selectedLanguage, fallbackSpeak, stopAudio]
  );

  const cancelSpeech = useCallback(() => {
    speakTokenRef.current++;
    stopAudio();
    setOrbState((s) => (s === 'speaking' ? 'idle' : s));
  }, [stopAudio]);

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
    listenOnce,
    abortListening,
    resetTranscript,
    speak,
    cancelSpeech,
    isSupported: typeof window !== 'undefined' && Boolean(navigator.mediaDevices || window.SpeechRecognition),
  };
}

