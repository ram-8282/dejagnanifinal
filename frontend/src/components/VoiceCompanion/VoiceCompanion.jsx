import { useState } from 'react';
import './VoiceCompanion.css';

function toInputValue(date) {
  const d = date || new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/**
 * VoiceCompanion — the speech bubble Gnani uses to talk with the person after they speak.
 * Every spoken question also has large tap targets, so voice is never required to answer.
 *
 * companion: { step: 'day' | 'pickDate' | 'more' | 'adding' | 'saving' | 'done' | 'info', message }
 */
export default function VoiceCompanion({
  companion,
  orbState,
  isSubmitting,
  onToday,
  onYesterday,
  onAnotherDay,
  onPickDate,
  onAddMore,
  onSaveNow,
  onClose,
  variant = 'inline',
}) {
  const [pickedDate, setPickedDate] = useState(() => toInputValue());
  if (!companion) return null;

  const { step, message } = companion;
  const isListeningForReply = orbState === 'listening' && ['day', 'pickDate', 'more'].includes(step);
  const isSpeaking = orbState === 'speaking';

  return (
    <div className={`voice-companion voice-companion--${variant}`} role="status" aria-live="polite">
      <div className="voice-companion__row">
        <span className={`voice-companion__avatar${isSpeaking ? ' voice-companion__avatar--speaking' : ''}`} aria-hidden="true">
          <span /><span /><span />
        </span>
        <p className="voice-companion__message">{message}</p>
        {step !== 'saving' && (
          <button className="voice-companion__close" onClick={onClose} aria-label="Dismiss voice assistant">✕</button>
        )}
      </div>

      {isListeningForReply && (
        <p className="voice-companion__hint">
          <span className="voice-companion__pulse" aria-hidden="true" /> Listening for your answer… or tap below
        </p>
      )}

      {step === 'day' && (
        <div className="voice-companion__choices">
          <button className="voice-companion__btn voice-companion__btn--primary" onClick={onToday}>Yes, today</button>
          <button className="voice-companion__btn" onClick={onYesterday}>Yesterday</button>
          <button className="voice-companion__btn" onClick={onAnotherDay}>Another day</button>
        </div>
      )}

      {step === 'pickDate' && (
        <div className="voice-companion__choices">
          <input
            type="date"
            className="voice-companion__date"
            value={pickedDate}
            max={toInputValue()}
            onChange={(e) => setPickedDate(e.target.value)}
            aria-label="Which day is this entry about?"
          />
          <button
            className="voice-companion__btn voice-companion__btn--primary"
            disabled={!pickedDate}
            onClick={() => {
              const [y, m, d] = pickedDate.split('-').map(Number);
              onPickDate(new Date(y, m - 1, d));
            }}
          >
            Use this day
          </button>
        </div>
      )}

      {step === 'more' && (
        <div className="voice-companion__choices">
          <button className="voice-companion__btn" onClick={onAddMore}>Yes, add more</button>
          <button
            className="voice-companion__btn voice-companion__btn--primary"
            onClick={onSaveNow}
            disabled={isSubmitting}
          >
            No, save it
          </button>
        </div>
      )}
    </div>
  );
}
