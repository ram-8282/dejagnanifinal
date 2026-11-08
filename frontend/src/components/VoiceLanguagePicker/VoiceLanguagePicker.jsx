import React from 'react';
import { GNANI_LANGUAGES } from '../../hooks/useGnaniVoice';
import './VoiceLanguagePicker.css';

/**
 * VoiceLanguagePicker — Sleek dropdown / badge to select Indic voice language.
 *
 * Supported languages:
 *   - Auto Detect (indic-auto)
 *   - English (en-IN)
 *   - Hindi (hi-IN)
 *   - Telugu (te-IN)
 *   - Tamil (ta-IN)
 *   - Kannada (kn-IN)
 */
export default function VoiceLanguagePicker({
  selectedLanguage,
  onLanguageChange,
  isGnaniConfigured = true,
  disabled = false,
  compact = false,
}) {
  const currentLang = GNANI_LANGUAGES.find((l) => l.code === selectedLanguage) || GNANI_LANGUAGES[0];

  return (
    <div className={`voice-lang-picker ${compact ? 'voice-lang-picker--compact' : ''}`}>
      <label htmlFor="voice-lang-select" className="voice-lang-picker__label" title="Powered by Gnani Indic Voice AI">
        <span className="voice-lang-picker__badge">
          GNANI
        </span>
        <svg
          className="voice-lang-picker__icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="2" y1="12" x2="22" y2="12" />
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
      </label>

      <div className="voice-lang-picker__select-wrapper">
        <select
          id="voice-lang-select"
          className="voice-lang-picker__select"
          value={selectedLanguage}
          onChange={(e) => onLanguageChange && onLanguageChange(e.target.value)}
          disabled={disabled}
          aria-label="Select voice language"
        >
          {GNANI_LANGUAGES.map((lang) => (
            <option key={lang.code} value={lang.code}>
              {lang.flag} {lang.label}
            </option>
          ))}
        </select>
        <span className="voice-lang-picker__caret" aria-hidden="true">▾</span>
      </div>
    </div>
  );
}

