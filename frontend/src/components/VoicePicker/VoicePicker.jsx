import { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { synthesizeVoiceSpeech } from '../../utils/api';
import {
  GNANI_VOICE_GROUPS, SPEED_OPTIONS,
  getVoicePreference, setVoicePreference, onVoicePreferenceChange, groupForVoice,
} from '../../utils/voicePreference';
import './VoicePicker.css';

const groupKey = (g) => g.id || g.language;

function SpeakerIcon({ size = 16 }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
    </svg>
  );
}

/** Live view of the saved voice preference. */
export function useVoicePreference() {
  const [pref, setPref] = useState(getVoicePreference);
  useEffect(() => onVoicePreferenceChange(setPref), []);
  return pref;
}

/* ── Modal ─────────────────────────────────────────────────── */
function VoicePickerModal({ onClose }) {
  const pref = useVoicePreference();
  const [activeGroup, setActiveGroup] = useState(() => {
    const g = groupForVoice(pref.voice);
    return g ? groupKey(g) : groupKey(GNANI_VOICE_GROUPS[0]);
  });
  const [previewing, setPreviewing] = useState(null);   // voice name currently loading/playing
  const [previewError, setPreviewError] = useState(null);
  const audioRef = useRef(null);
  const dialogRef = useRef(null);

  const stopPreview = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setPreviewing(null);
  }, []);

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onKey);
    dialogRef.current?.focus();
    return () => { document.removeEventListener('keydown', onKey); stopPreview(); };
  }, [onClose, stopPreview]);

  const group = GNANI_VOICE_GROUPS.find((g) => groupKey(g) === activeGroup) || GNANI_VOICE_GROUPS[0];

  const preview = async (voice) => {
    stopPreview();
    setPreviewError(null);
    setPreviewing(voice);
    try {
      const blob = await synthesizeVoiceSpeech({
        text: group.sample(voice),
        language: group.language,
        voice,
        speed: pref.speed,
      });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => { URL.revokeObjectURL(url); if (audioRef.current === audio) stopPreview(); };
      await audio.play();
    } catch (err) {
      console.warn('[VoicePicker] preview failed:', err);
      setPreviewError(`Couldn't play ${voice} — check that the Gnani API key is set and the backend is running.`);
      setPreviewing(null);
    }
  };

  return createPortal(
    <div className="voice-picker__backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div
        className="voice-picker"
        role="dialog"
        aria-modal="true"
        aria-labelledby="voice-picker-title"
        tabIndex={-1}
        ref={dialogRef}
      >
        <header className="voice-picker__header">
          <div>
            <h2 id="voice-picker-title" className="voice-picker__title">Choose a voice</h2>
            <p className="voice-picker__subtitle">
              The voice Déjà uses to talk with you. Press ▶ to hear one, then choose it.
            </p>
          </div>
          <button className="voice-picker__close" onClick={onClose} aria-label="Close voice picker">✕</button>
        </header>

        <div className="voice-picker__groups" role="tablist" aria-label="Voice language">
          {GNANI_VOICE_GROUPS.map((g) => (
            <button
              key={groupKey(g)}
              role="tab"
              aria-selected={groupKey(g) === activeGroup}
              className={`voice-picker__group${groupKey(g) === activeGroup ? ' voice-picker__group--active' : ''}`}
              onClick={() => { stopPreview(); setActiveGroup(groupKey(g)); }}
            >
              {g.label}
              <span className="voice-picker__group-count">{g.voices.length}</span>
            </button>
          ))}
        </div>

        <ul className="voice-picker__list" role="tabpanel" aria-label={`${group.label} voices`}>
          {group.voices.map((voice) => {
            const selected = pref.voice === voice;
            const isPlaying = previewing === voice;
            return (
              <li key={voice} className={`voice-picker__item${selected ? ' voice-picker__item--selected' : ''}`}>
                <button
                  className={`voice-picker__play${isPlaying ? ' voice-picker__play--active' : ''}`}
                  onClick={() => (isPlaying ? stopPreview() : preview(voice))}
                  aria-label={isPlaying ? `Stop ${voice} preview` : `Hear ${voice}`}
                >
                  {isPlaying ? '■' : '▶'}
                </button>
                <span className="voice-picker__name">{voice}</span>
                <button
                  className="voice-picker__choose"
                  onClick={() => setVoicePreference({ voice })}
                  aria-pressed={selected}
                >
                  {selected ? '✓ Selected' : 'Choose'}
                </button>
              </li>
            );
          })}
        </ul>

        {previewError && <p className="voice-picker__error" role="alert">{previewError}</p>}

        <div className="voice-picker__speed">
          <span className="voice-picker__speed-label">Speaking speed</span>
          <div className="voice-picker__speed-options" role="radiogroup" aria-label="Speaking speed">
            {SPEED_OPTIONS.map((s) => (
              <button
                key={s.value}
                role="radio"
                aria-checked={pref.speed === s.value}
                className={`voice-picker__speed-btn${pref.speed === s.value ? ' voice-picker__speed-btn--active' : ''}`}
                onClick={() => setVoicePreference({ speed: s.value })}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        <footer className="voice-picker__footer">
          <button className="voice-picker__reset" onClick={() => setVoicePreference({ voice: '', speed: 1.0 })}>
            Reset to default
          </button>
          <span className="voice-picker__current">
            Using: <strong>{pref.voice || 'Default voice'}</strong>
          </span>
          <button className="voice-picker__done" onClick={onClose}>Done</button>
        </footer>
      </div>
    </div>,
    document.body
  );
}

/* ── Trigger ───────────────────────────────────────────────── */
/**
 * VoicePicker — opens the Gnani voice chooser.
 *   variant="row"  → sidebar row ("Voice · Nalini" + button)
 *   variant="icon" → compact header icon button
 */
export default function VoicePicker({ variant = 'icon' }) {
  const [open, setOpen] = useState(false);
  const pref = useVoicePreference();
  const close = useCallback(() => setOpen(false), []);
  const label = pref.voice || 'Default';

  return (
    <>
      {variant === 'row' ? (
        <div className="voice-picker-row">
          <div className="voice-picker-row__info">
            <span className="voice-picker-row__label">Voice</span>
            <span className="voice-picker-row__value">{label}</span>
          </div>
          <button
            className="voice-picker-trigger"
            onClick={() => setOpen(true)}
            aria-label={`Change voice (currently ${label})`}
            title="Choose Gnani voice"
          >
            <SpeakerIcon />
          </button>
        </div>
      ) : (
        <button
          className="voice-picker-trigger"
          onClick={() => setOpen(true)}
          aria-label={`Change voice (currently ${label})`}
          title={`Voice: ${label}`}
        >
          <SpeakerIcon />
        </button>
      )}
      {open && <VoicePickerModal onClose={close} />}
    </>
  );
}
