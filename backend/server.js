const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '.env') });
const express = require('express');
const cors = require('cors');
const { createClient } = require('@supabase/supabase-js');
const crypto = require('crypto');
const multer = require('multer');

const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: 25 * 1024 * 1024 } // 25 MB limit
});

const app = express();
const PORT = process.env.PORT || 5051;
// Pointing to the new memory_bridge_3.py FastAPI server which still runs on 8000 by default
const FASTAPI_URL = 'http://127.0.0.1:8000';

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;

// Gnani Voice AI Config
const GNANI_BASE_URL = process.env.GNANI_BASE_URL || 'https://api.vachana.ai';
const GNANI_API_KEY = process.env.GNANI_API_KEY || '';
const GNANI_STT_MODEL = process.env.GNANI_STT_MODEL || 'prisma-v3.0';
const GNANI_DEFAULT_LANG = process.env.GNANI_DEFAULT_LANG || 'indic-auto';
const GNANI_TTS_VOICE = process.env.GNANI_TTS_VOICE || 'Nalini';


// Create an authenticated client if token provided, otherwise fallback to Anon
const getSupabase = (req) => {
    if (!supabaseUrl || !supabaseKey) {
        console.warn("WARNING: Supabase credentials missing. Database operations will fail.");
        return null;
    }
    if (req.userToken) {
        return createClient(supabaseUrl, supabaseKey, {
            global: { headers: { Authorization: `Bearer ${req.userToken}` } }
        });
    }
    return createClient(supabaseUrl, supabaseKey);
};

// Global Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Multi-Tenancy Engine Middleware
app.use((req, res, next) => {
    const profile = req.headers['x-user-profile'] || req.query.user;
    req.userProfile = profile || 'default_user';
    req.userToken = req.headers['x-user-token'] || req.query.token || null;
    next();
});

// Proxy Fetch Helper to forward requests to the Python microservice
const proxyFetch = async (url, method, body = null, signal = null) => {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (body) {
        options.body = JSON.stringify(body);
    }
    if (signal) {
        options.signal = signal;
    }

    try {
        const response = await fetch(url, options);
        let data;
        try {
            data = await response.json();
        } catch (e) {
            const text = await response.text();
            throw new Error(`Failed to parse JSON response from Python Bridge: ${text}`);
        }

        if (!response.ok) {
            throw data;
        }
        return data;
    } catch (error) {
        throw error;
    }
};

app.get('/', (req, res) => {
    res.json({ status: 'online', app: 'Déjà Gateway Engine v2', mode: 'strict_determinism' });
});

app.get('/api/health', async (req, res) => {
    try {
        const params = new URLSearchParams({ profile: req.userProfile });
        const result = await proxyFetch(`${FASTAPI_URL}/api/health?${params}`, 'GET');
        res.json({
            status: 'success',
            message: 'Gateway is healthy and v3 bridge is connected.',
            bridgeResponse: result
        });
    } catch (error) {
        res.status(500).json({ status: 'error', message: 'Bridge disconnected.', details: error });
    }
});

// Gateway Routing: Data Ingestion
app.post('/api/memory/ingest', async (req, res) => {
    try {
        const { text, timestamp, isSnippet, force_save } = req.body;
        if (!text) {
            return res.status(400).json({ error: "Missing 'text' in request body." });
        }

        // 1. Python Intent Router & Taxonomy Ingestion
        const result = await proxyFetch(`${FASTAPI_URL}/api/ingest`, 'POST', {
            profile: req.userProfile,
            text,
            timestamp,
            isSnippet,
            force_save: !!force_save,
            token: req.userToken
        });

        if (result && result.status === 'tripwire_alert') {
            return res.status(200).json(result);
        }

        // 2. Forget / Soft Delete Check from Intent
        if (result && result.status === 'forget_confirmation') {
            const topic = result.data?.topic || '';

            const supabase = getSupabase(req);
            if (supabase) {
                const { data, error } = await supabase
                    .from('journal_slates')
                    .select('*')
                    .eq('profile_id', req.userProfile)
                    .ilike('content', `%${topic}%`);

                if (error) {
                    console.error('Supabase Search Error:', error);
                    return res.status(500).json({ status: 'error', message: 'Database error during search.', details: error });
                }

                // If no exact UI rows matched, just purge it semantically in the python side vault
                if (data && data.length === 0) {
                    const forgetResult = await proxyFetch(`${FASTAPI_URL}/api/forget`, 'POST', {
                        profile: req.userProfile,
                        topic: topic,
                        token: req.userToken
                    });
                    return res.status(200).json({
                        status: 'success',
                        message: `No explicit Supabase rows found, but semantic amnesia vault updated for "${topic}".`,
                        bridgeResponse: forgetResult
                    });
                }

                return res.status(200).json({
                    status: 'verification_required',
                    topic: topic,
                    matches: data
                });
            } else {
                const forgetResult = await proxyFetch(`${FASTAPI_URL}/api/forget`, 'POST', {
                    profile: req.userProfile,
                    topic: topic,
                    token: req.userToken
                });
                return res.status(200).json({
                    status: 'success',
                    message: `Semantic Amnesia Vault locked for "${topic}".`,
                    bridgeResponse: forgetResult
                });
            }
        }

        // 3. Supabase Insert (Standard Journal Flow)
        let databaseRecord = null;
        const supabase = getSupabase(req);
        if (supabase) {
            const payload = { content: text, profile_id: req.userProfile };

            // Honour a client-supplied timestamp so entries about an earlier day
            // ("this happened yesterday") land on the right page of The Archives.
            // Ignore anything unparsable or in the future (5 min clock-skew allowance).
            const entryTime = timestamp ? new Date(timestamp) : null;
            if (entryTime && !isNaN(entryTime.getTime()) && entryTime.getTime() <= Date.now() + 5 * 60 * 1000) {
                payload.created_at = entryTime.toISOString();
            }

            const { data, error } = await supabase
                .from('journal_slates')
                .insert([payload])
                .select()
                .single();

            if (error) {
                console.error('Supabase Insert Error:', error);
                return res.status(500).json({ status: 'error', message: 'Database error during ingestion.', details: error });
            }
            databaseRecord = data;

            if (result && result.summary_snippet && databaseRecord) {
                const { error: updateError } = await supabase
                    .from('journal_slates')
                    .update({ summary_snippet: result.summary_snippet })
                    .eq('id', databaseRecord.id);

                if (!updateError) {
                    databaseRecord.summary_snippet = result.summary_snippet;
                }
            }
        }

        res.status(200).json({
            status: 'success',
            databaseRecord: databaseRecord,
            graphEngine: result
        });
    } catch (error) {
        console.error('Ingest Pipeline Error:', error);
        res.status(500).json({ status: 'error', message: 'Internal server error during ingestion.', details: error.message || error });
    }
});

// Gateway Routing: Timeline (Unchanged essentially, but modernized for safety)
app.get('/api/memory/timeline', async (req, res) => {
    try {
        const supabase = getSupabase(req);
        if (!supabase) {
            return res.status(500).json({ error: "Supabase connection is not initialized." });
        }

        const { data, error } = await supabase
            .from('journal_slates')
            .select('*')
            .eq('profile_id', req.userProfile)
            .order('created_at', { ascending: false });

        if (error) {
            console.error('Supabase Query Error:', error);
            return res.status(500).json({ status: 'error', message: 'Database error fetching timeline.', details: error });
        }

        res.status(200).json({ status: 'success', timeline: data });
    } catch (error) {
        console.error('Timeline Fetch Error:', error);
        res.status(500).json({ status: 'error', message: 'Internal server error during timeline fetch.', details: error.message || error });
    }
});

// Gateway Routing: Oracle Recovery
app.post('/api/memory/recover', async (req, res) => {
    try {
        const { question, state } = req.body || {};
        const query = question || state || "";

        const result = await proxyFetch(`${FASTAPI_URL}/api/recover`, 'POST', {
            profile: req.userProfile,
            query,
            token: req.userToken
        }, req.signal);
        res.status(200).json(result);
    } catch (error) {
        console.error('Oracle Pipeline Error:', error);
        // Graceful Degradation: return a structured fail state rather than outright breaking UI
        const reason = String((error && (error.detail || error.message)) || '');
        const busy = /503|429|high demand|unavailable|overloaded|rate limit/i.test(reason);
        res.status(busy ? 503 : 500).json({
            status: 'error',
            message: busy
                ? 'The AI model is busy (high demand). Please try again in a minute.'
                : `The Oracle bridge is temporarily unresponsive. Data remains safe. ${reason.slice(0, 160)}`,
            details: error.message || error
        });
    }
});

// Gateway Routing: Analytics / Blindspots
app.get('/api/memory/blindspots', async (req, res) => {
    try {
        const result = await proxyFetch(`${FASTAPI_URL}/api/blindspots`, 'POST', {
            profile: req.userProfile,
            force_refresh: req.query.force_refresh === 'true' || req.query.force_refresh === true,
            token: req.userToken
        });
        res.status(200).json(result);
    } catch (error) {
        console.error('Analytics Pipeline Error:', error);
        const reason = (error && (error.detail || error.message)) || 'Internal server error during blindspot lookup.';
        res.status(500).json({ status: 'error', message: String(reason).slice(0, 300), details: error });
    }
});

// Gateway Routing: Update Pipeline
app.put('/api/memory/update', async (req, res) => {
    try {
        const { entryId, originalText, newText } = req.body;
        if (!newText || typeof newText !== 'string' || !newText.trim()) {
            return res.status(400).json({ error: "Missing or empty 'newText' in request body." });
        }

        let databaseRecord = null;
        const supabase = getSupabase(req);
        if (supabase && entryId) {
            const { data, error } = await supabase
                .from('journal_slates')
                .update({ content: newText.trim() })
                .eq('id', entryId)
                .eq('profile_id', req.userProfile)
                .select()
                .single();

            if (error) {
                console.error('Supabase Update Error:', error);
                return res.status(500).json({ status: 'error', message: 'Database error during memory update.', details: error });
            }
            databaseRecord = data;
        }

        const result = await proxyFetch(`${FASTAPI_URL}/api/update`, 'PUT', {
            profile: req.userProfile,
            entryId: entryId || null,
            originalText: originalText || '',
            newText: newText.trim(),
            token: req.userToken
        });

        res.status(200).json({
            status: 'success',
            databaseRecord: databaseRecord,
            graphEngine: result
        });
    } catch (error) {
        console.error('Memory Update Pipeline Error:', error);
        res.status(500).json({ status: 'error', message: 'Internal server error during memory update.', details: error.message || error });
    }
});

// Gateway Routing: Amnesia Action
app.post('/api/memory/forget', async (req, res) => {
    try {
        const { topic, entryId } = req.body;
        if (!topic && !entryId) {
            return res.status(400).json({ error: "Missing 'topic' or 'entryId' in request body." });
        }

        const supabase = getSupabase(req);
        if (supabase && entryId) {
            const { error } = await supabase
                .from('journal_slates')
                .delete()
                .eq('id', entryId)
                .eq('profile_id', req.userProfile);

            if (error) {
                console.error('Supabase Delete Error:', error);
                return res.status(500).json({ status: 'error', message: 'Database error during memory deletion.', details: error });
            }
        }

        const result = await proxyFetch(`${FASTAPI_URL}/api/forget`, 'POST', {
            profile: req.userProfile,
            topic: topic || "",
            entryId: entryId || null,
            token: req.userToken
        });
        res.status(200).json(result);
    } catch (error) {
        console.error('Forget Pipeline Error:', error);
        res.status(500).json({ status: 'error', message: 'Internal server error during forget operation.', details: error.message || error });
    }
});

// Gateway Routing: Generate Feedback
app.post('/api/memory/generate_feedback', async (req, res) => {
    try {
        const { helpful, context, scenario } = req.body;
        const result = await proxyFetch(`${FASTAPI_URL}/api/generate_feedback`, 'POST', {
            profile: req.userProfile,
            helpful: !!helpful,
            context: context || "",
            scenario: scenario || "",
            token: req.userToken
        });
        res.status(200).json(result);
    } catch (error) {
        console.error('Generate Feedback Pipeline Error:', error);
        res.status(500).json({ status: 'error', message: 'Internal server error during generate feedback operation.', details: error });
    }
});

// Gateway Routing: Feedback / Improve
app.post('/api/memory/improve', async (req, res) => {
    try {
        const { helpful, context, lookup_token } = req.body;

        // Use crypto properly for hash generation in JS if token is missing
        const final_token = lookup_token || crypto.createHash('sha256').update(context || "").digest('hex');

        const result = await proxyFetch(`${FASTAPI_URL}/api/improve`, 'POST', {
            profile: req.userProfile,
            helpful: !!helpful,
            context: context || "",
            lookup_token: final_token,
            token: req.userToken
        });
        res.status(200).json(result);
    } catch (error) {
        console.error('Improve Pipeline Error:', error);
        res.status(500).json({ status: 'error', message: 'Internal server error during improve operation.', details: error });
    }
});

// ==========================================
// GNANI.AI VOICE ENGINE (REST API INTEGRATION)
// ==========================================

// 1. Status / Diagnostics
app.get('/api/voice/status', (req, res) => {
    const isConfigured = Boolean(GNANI_API_KEY && GNANI_API_KEY.trim().length > 0);
    res.json({
        provider: 'gnani',
        isConfigured,
        mode: 'rest',
        defaultLanguage: GNANI_DEFAULT_LANG,
        sttModel: GNANI_STT_MODEL,
        ttsVoice: GNANI_TTS_VOICE,
        supportedLanguages: [
            { code: 'indic-auto', label: 'Auto Detect (Indic)' },
            { code: 'en-IN', label: 'English (India)' },
            { code: 'hi-IN', label: 'Hindi (हिंदी)' },
            { code: 'ta-IN', label: 'Tamil (தமிழ்)' },
            { code: 'te-IN', label: 'Telugu (తెలుగు)' },
            { code: 'kn-IN', label: 'Kannada (ಕನ್ನಡ)' },
            { code: 'mr-IN', label: 'Marathi (मराठी)' },
            { code: 'bn-IN', label: 'Bengali (বাংলা)' },
            { code: 'gu-IN', label: 'Gujarati (ગુજરાતી)' },
            { code: 'ml-IN', label: 'Malayalam (മലയാളം)' },
            { code: 'pa-IN', label: 'Punjabi (ਪੰਜਾਬੀ)' }
        ]
    });
});

// 2. Speech-to-Text (STT) via Gnani Prisma v3 REST API
app.post('/api/voice/stt', upload.single('audio'), async (req, res) => {
    try {
        console.log('[GNANI STT] Incoming request to /api/voice/stt');
        console.log('[GNANI STT] req.file details:', req.file ? {
            fieldname: req.file.fieldname,
            originalname: req.file.originalname,
            mimetype: req.file.mimetype,
            size: req.file.size,
            bufferLength: req.file.buffer ? req.file.buffer.length : 0
        } : 'No file received in req.file');
        console.log('[GNANI STT] req.body:', req.body);

        if (!GNANI_API_KEY) {
            console.error('[GNANI STT] GNANI_API_KEY is missing from environment.');
            return res.status(500).json({
                error: 'GNANI_KEY_NOT_CONFIGURED: GNANI_API_KEY is not configured in backend/.env'
            });
        }

        if (!req.file || !req.file.buffer) {
            console.error('[GNANI STT] Error: No audio file provided in "audio" field.');
            return res.status(400).json({ error: "No audio file provided in 'audio' field." });
        }

        const language_code = req.body.language_code || req.body.language || req.query.language || GNANI_DEFAULT_LANG;
        const model = req.body.model || req.query.model || GNANI_STT_MODEL;
        // With indic-auto, Gnani renders output in the detected language's native script,
        // so Indian-accented English often comes back in Devanagari. 'codemix' (Prisma v3 only)
        // keeps English words in Latin script while leaving Indic words in their own script.
        const isV3 = model.startsWith('prisma-v3');
        const format = req.body.format || req.query.format || (isV3 ? 'codemix' : 'verbatim');

        const formData = new FormData();
        const audioBlob = new Blob([req.file.buffer], { type: 'audio/wav' });
        const filename = 'recording.wav';
        formData.append('audio_file', audioBlob, filename);
        formData.append('model', model);
        formData.append('language_code', language_code);
        formData.append('format', format);

        console.log(`[GNANI STT] Forwarding to Gnani STT API: ${GNANI_BASE_URL}/stt/v3 (model=${model}, lang=${language_code}, format=${format}, file=${filename}, size=${req.file.size} bytes, type=audio/wav)`);

        const response = await fetch(`${GNANI_BASE_URL}/stt/v3`, {
            method: 'POST',
            headers: {
                'X-API-Key-ID': GNANI_API_KEY
            },
            body: formData
        });

        console.log(`[GNANI STT] Gnani STT API response status: ${response.status}`);

        let data;
        try {
            data = await response.json();
        } catch (e) {
            const rawText = await response.text();
            console.error('[GNANI STT] Non-JSON response from Gnani STT API:', rawText);
            return res.status(500).json({ error: `Gnani STT returned non-JSON response: ${rawText}` });
        }

        if (!response.ok) {
            console.error('[GNANI STT] Gnani STT API non-200 Error:', response.status, data);
            return res.status(500).json({ error: data });
        }

        const transcript = data.transcript || data.text || (data.result && data.result[0]?.transcript) || '';
        const detectedLanguage = data.detected_language_code || language_code;
        console.log(`[GNANI STT] Transcription success! (detected=${data.detected_language_code || 'n/a'}) Transcript:`, transcript);

        return res.json({
            status: 'success',
            transcript: transcript.trim(),
            confidence: data.confidence || (data.result && data.result[0]?.confidence) || 1.0,
            language: detectedLanguage,
            requestedLanguage: language_code,
            raw: data
        });
    } catch (error) {
        console.error('[GNANI STT] Proxy exception:', error);
        return res.status(500).json({
            error: error.message || 'Internal error while calling Gnani STT API.',
            details: error
        });
    }
});

// 3. Text-to-Speech (TTS) via Gnani Timbre REST API
app.post('/api/voice/tts', async (req, res) => {
    try {
        if (!GNANI_API_KEY) {
            return res.status(503).json({
                status: 'error',
                code: 'GNANI_KEY_NOT_CONFIGURED',
                message: 'GNANI_API_KEY is not configured in backend/.env'
            });
        }

        const { text, voice, language, speed } = req.body || {};
        if (!text || !text.trim()) {
            return res.status(400).json({ status: 'error', message: "Missing 'text' in request body." });
        }

        const lang = language && language !== 'indic-auto' ? language : 'en-IN';
        // Voice comes from the in-app Voice picker; accept only a plain voice name.
        const safeVoice = typeof voice === 'string' && /^[A-Za-z]{2,24}$/.test(voice) ? voice : GNANI_TTS_VOICE;
        const safeSpeed = typeof speed === 'number' && speed >= 0.5 && speed <= 2 ? speed : 1.0;
        const payload = {
            text: text.trim(),
            voice: safeVoice,
            model: 'timbre-v2.5',
            language: lang,
            speed: safeSpeed,
            audio_config: {
                sample_rate: 48000,
                num_channels: 1,
                sample_width: 2,
                encoding: 'linear_pcm',
                container: 'wav'
            }
        };

        const response = await fetch(`${GNANI_BASE_URL}/api/v1/tts/inference`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key-ID': GNANI_API_KEY
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            let errorText = '';
            try {
                const errJson = await response.json();
                errorText = JSON.stringify(errJson);
            } catch (e) {
                errorText = await response.text();
            }
            console.error('Gnani TTS API Error:', response.status, errorText);
            return res.status(response.status).json({
                status: 'error',
                message: 'Gnani TTS synthesis failed',
                details: errorText
            });
        }

        const arrayBuffer = await response.arrayBuffer();
        const buffer = Buffer.from(arrayBuffer);

        res.set({
            'Content-Type': 'audio/wav',
            'Content-Length': buffer.length,
            'Cache-Control': 'no-cache'
        });
        return res.send(buffer);
    } catch (error) {
        console.error('Gnani TTS Proxy Failure:', error);
        return res.status(500).json({
            status: 'error',
            message: error.message || 'Internal server error while calling Gnani TTS.',
            details: error
        });
    }
});

const serverInstance = app.listen(PORT, '0.0.0.0', () => {
    console.log(`Déjà Gateway v2 running on port ${PORT} (0.0.0.0)`);
});

// Keep-alive timer to ensure Node event loop remains active across Windows background processes
const keepAliveTimer = setInterval(() => {}, 1000 * 60 * 60);

process.on('SIGINT', () => {
    clearInterval(keepAliveTimer);
    serverInstance.close();
    process.exit(0);
});
process.on('SIGTERM', () => {
    clearInterval(keepAliveTimer);
    serverInstance.close();
    process.exit(0);
});

process.on('unhandledRejection', (reason, promise) => { console.error('Unhandled Rejection:', reason); });
process.on('uncaughtException', (error) => { console.error('Uncaught Exception:', error); });
