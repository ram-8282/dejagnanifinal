/**
 * voiceCompanion — the conversational layer Gnani uses around a spoken diary entry.
 *
 * Pure helpers only (no React): understanding short spoken replies ("yes", "yesterday",
 * "nahi", "నిన్న"), choosing a warm reaction to what was said, and phrasing the
 * questions / goodbyes. Kept deliberately simple and gentle for elderly users.
 */

const YES_WORDS = [
  'yes', 'yeah', 'yep', 'yup', 'yah', 'sure', 'correct', 'right', 'ok', 'okay', 'of course',
  'please', 'go ahead', 'haan', 'han', 'haa', 'ha', 'ji', 'theek', 'avunu', 'aamaa', 'aama', 'howdu',
  'हाँ', 'हां', 'जी', 'ठीक', 'అవును', 'ఔను', 'సరే', 'ஆமாம்', 'ஆமா', 'சரி', 'ಹೌದು', 'ಸರಿ',
];

const NO_WORDS = [
  'no', 'nope', 'nah', 'not', 'nothing', 'done', "that's all", 'thats all', 'that is all', 'finished',
  'save it', 'save', 'nahi', 'nahin', 'illa', 'illai', 'ledu', 'vaddu', 'beda', 'bas',
  'नहीं', 'नही', 'बस', 'లేదు', 'వద్దు', 'இல்லை', 'வேண்டாம்', 'ಇಲ್ಲ', 'ಬೇಡ',
];

const WEEKDAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
const NUMBER_WORDS = { one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, a: 1 };

function normalize(text) {
  return ` ${(text || '').toLowerCase().replace(/[.,!?।]/g, ' ').replace(/\s+/g, ' ').trim()} `;
}

function hasWord(norm, word) {
  // Latin words need word boundaries ("no" must not match "know"); Indic scripts match as substrings.
  if (/^[a-z' ]+$/.test(word)) return norm.includes(` ${word} `);
  return norm.includes(word);
}

function firstWords(text, n) {
  return (text || '').trim().split(/\s+/).slice(0, n).join(' ');
}

/** 'yes' | 'no' | null */
export function parseYesNo(text) {
  const norm = normalize(text);
  if (NO_WORDS.some((w) => hasWord(norm, w))) return 'no';
  if (YES_WORDS.some((w) => hasWord(norm, w))) return 'yes';
  return null;
}

function daysAgo(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d;
}

/**
 * Understand an answer to "Is this about today?".
 * Returns { kind: 'today' } | { kind: 'date', date } | { kind: 'other' } | null (unclear).
 */
export function parseDayReply(text) {
  const norm = normalize(text);
  if (!norm.trim()) return null;

  if (/day before yesterday/.test(norm) || hasWord(norm, 'parson') || hasWord(norm, 'परसों') ||
      hasWord(norm, 'మొన్న') || hasWord(norm, 'முந்தாநேற்று') || hasWord(norm, 'ಮೊನ್ನೆ')) {
    return { kind: 'date', date: daysAgo(2) };
  }
  if (hasWord(norm, 'yesterday') || hasWord(norm, 'kal') || hasWord(norm, 'कल') ||
      hasWord(norm, 'నిన్న') || hasWord(norm, 'நேற்று') || hasWord(norm, 'ನಿನ್ನೆ')) {
    return { kind: 'date', date: daysAgo(1) };
  }

  const ago = norm.match(/ (\d+|one|two|three|four|five|six|seven|a) days? ago /);
  if (ago) {
    const n = NUMBER_WORDS[ago[1]] ?? parseInt(ago[1], 10);
    if (n >= 0 && n <= 60) return n === 0 ? { kind: 'today' } : { kind: 'date', date: daysAgo(n) };
  }

  const todayIdx = new Date().getDay();
  for (let i = 0; i < WEEKDAYS.length; i++) {
    if (hasWord(norm, WEEKDAYS[i])) {
      const back = (todayIdx - i + 7) % 7;
      return back === 0 ? { kind: 'today' } : { kind: 'date', date: daysAgo(back) };
    }
  }

  const yn = parseYesNo(firstWords(text, 4));
  if (yn === 'no') return { kind: 'other' };
  if (yn === 'yes' || hasWord(norm, 'today') || hasWord(norm, 'aaj') || hasWord(norm, 'आज') ||
      hasWord(norm, 'ఈరోజు') || hasWord(norm, 'இன்று') || hasWord(norm, 'ಇಂದು')) {
    return { kind: 'today' };
  }
  return null;
}

/**
 * Understand an answer to "Would you like to add anything else?".
 * Returns 'yes' | 'no' | 'content' (they just kept talking — treat it as more diary) | null.
 */
export function parseMoreReply(text) {
  const words = (text || '').trim().split(/\s+/).filter(Boolean);
  if (!words.length) return null;
  const lead = parseYesNo(words.slice(0, 3).join(' '));
  if (lead) return lead;
  if (words.length >= 5) return 'content';
  return parseYesNo(text);
}

const REACTIONS = [
  {
    test: /\b(forgot|forget|forgetting|can'?t remember|couldn'?t remember|don'?t remember|confused|misplaced)\b/i,
    say: "That's perfectly alright. That's exactly what this diary is for — I'll remember it for you.",
  },
  {
    test: /\b(sick|ill|unwell|fever|pain|hurt|hurts|ache|aching|headache|cough|cold|flu|hospital|doctor|dizzy|fell|fall|injur\w*|vomit\w*|bp|sugar|medicine)\b|बुखार|दर्द|बीमार|జ్వరం|నొప్పి|காய்ச்சல்|வலி|ಜ್ವರ|ನೋವು/i,
    say: "I'm sorry you're not feeling well. Please take it easy today, and I hope you feel better soon.",
  },
  {
    test: /\bnot (feeling )?(good|great|well|okay|fine|happy)\b|\b(sad|miss|missed|missing|lonely|alone|cry|cried|crying|upset|worried|worry|scared|afraid|angry|frustrated|anxious)\b|उदास|अकेला/i,
    say: 'That sounds hard. Thank you for trusting me with it. You are not alone.',
  },
  {
    test: /\b(birthday|anniversary|festival|diwali|deepavali|pongal|sankranti|holi|eid|christmas|onam|ugadi|navaratri|dussehra|party|celebrat\w*|wedding|married|congratulat\w*)\b/i,
    say: 'How wonderful! That sounds like a very special day.',
  },
  {
    test: /\b(grandson|granddaughter|grandchild\w*|daughter|son|wife|husband|visit\w*|family|friend\w*|neighbou?r)\b/i,
    say: 'How lovely that you spent time with people you care about.',
  },
  {
    test: /\b(happy|good|great|lovely|wonderful|fun|enjoy\w*|laugh\w*|nice|beautiful|peaceful|proud)\b|खुश|అందంగా|சந்தோஷம்/i,
    say: "That sounds lovely. I'm so glad to hear it.",
  },
  {
    test: /\b(walk\w*|garden\w*|park|temple|prayer|pray\w*|yoga|music|song|sang|read|reading|book)\b/i,
    say: 'That sounds very peaceful.',
  },
];

/** A short, warm reaction to what the person just said. */
export function reactionFor(text) {
  const hit = REACTIONS.find((r) => r.test.test(text || ''));
  return hit ? hit.say : 'Thank you for sharing that with me.';
}

export function isSameCalendarDay(a, b) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

/** "today", "yesterday" or "Monday, 9 November" — for speaking aloud. */
export function spokenDate(date) {
  const today = new Date();
  if (!date || isSameCalendarDay(date, today)) return 'today';
  if (isSameCalendarDay(date, daysAgo(1))) return 'yesterday';
  return date.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' });
}

/** A goodbye that fits the time of day. */
export function farewell(now = new Date()) {
  const h = now.getHours();
  if (h < 12) return 'Have a lovely morning.';
  if (h < 17) return 'Enjoy the rest of your afternoon.';
  if (h < 21) return 'Have a peaceful evening.';
  return 'Rest well, and sleep peacefully.';
}

/**
 * Timestamp for an entry about `date`: same clock time as now on that day,
 * so it lands on the right page of The Archives.
 */
export function timestampFor(date) {
  const now = new Date();
  if (!date || isSameCalendarDay(date, now)) return now.toISOString();
  const d = new Date(date);
  d.setHours(now.getHours(), now.getMinutes(), now.getSeconds(), 0);
  return d.toISOString();
}

export const PROMPTS = {
  askDay: (reaction) => `${reaction} Is this about today?`,
  askDayAgain: "Sorry, I didn't quite catch that. Is this about today? You can say yes, or yesterday, or tap a button.",
  askWhichDay: 'Which day is this about? You can say yesterday, or a day like Monday — or pick the date on the screen.',
  askWhichDayAgain: "I couldn't work out the day. Please pick the date on the screen.",
  dayConfirmed: (date) =>
    spokenDate(date) === 'today'
      ? 'Okay, I will keep it under today. Would you like to add anything else?'
      : `Okay, I will keep it under ${spokenDate(date)}. Would you like to add anything else?`,
  askMore: (reaction) => `${reaction} Would you like to add anything else?`,
  askMoreAgain: "Sorry, I didn't catch that. Would you like to add anything else, or shall I save it?",
  goAhead: "Go ahead, I'm listening. Tap the microphone when you're finished.",
  heardNothing: "I couldn't hear anything that time. Tap the microphone and try again whenever you're ready.",
  saving: 'Alright, saving it now.',
  saved: (date) =>
    spokenDate(date) === 'today'
      ? `It's safely saved in today's diary. ${farewell()}`
      : `It's safely saved under ${spokenDate(date)}. ${farewell()}`,
  saveFailed: "I'm sorry, something went wrong while saving. Your words are still here — please try again.",
};
