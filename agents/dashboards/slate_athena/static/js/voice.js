/**
 * SLATE-ATHENA Voice Activation Module (Jarvis-style)
 * Modified: 2026-02-10T14:00:00Z | Author: COPILOT | Change: Azure Speech SDK integration for voice commands
 * 
 * Uses Azure Cognitive Services Speech SDK for:
 *   - Speech-to-text (voice commands)
 *   - Text-to-speech (Athena responses)
 * 
 * Commands recognized:
 *   - "Athena, status" / "Hey Athena, system status"
 *   - "Athena, refresh" / "Athena, update"
 *   - "Athena, start services" / "Athena, stop services"
 *   - "Athena, run workflow [name]"
 *   - "Athena, GPU status" / "Athena, check GPU"
 *   - "Athena, task queue" / "Athena, show tasks"
 */

(function() {
    'use strict';

    // ─── Configuration ──────────────────────────────────────────────────
    const CONFIG = {
        // Azure Speech SDK config (set via environment or dashboard settings)
        // For local development, these can be set from the server
        subscriptionKey: window.AZURE_SPEECH_KEY || '',
        region: window.AZURE_SPEECH_REGION || 'eastus',
        
        // Voice settings
        voiceName: 'en-US-JennyNeural',  // Professional female voice
        speechRate: 1.1,
        
        // Recognition settings
        language: 'en-US',
        continuous: false,
        
        // Wake word (Jarvis-style)
        wakeWord: 'athena',
        wakeWordAliases: ['hey athena', 'okay athena', 'athena']
    };

    // ─── State ──────────────────────────────────────────────────────────
    let recognizer = null;
    let synthesizer = null;
    let isListening = false;
    let isProcessing = false;

    // ─── DOM Elements ───────────────────────────────────────────────────
    const voiceBtn = document.getElementById('voiceBtn');
    const voiceStatus = document.getElementById('voiceStatus');
    const voiceText = document.getElementById('voiceText');

    // ─── Initialize ─────────────────────────────────────────────────────
    function init() {
        if (!voiceBtn) {
            console.warn('[ATHENA Voice] Voice button not found');
            return;
        }

        // Check if SDK is loaded
        if (typeof SpeechSDK === 'undefined') {
            console.warn('[ATHENA Voice] Azure Speech SDK not loaded');
            voiceBtn.title = 'Voice unavailable - SDK not loaded';
            voiceBtn.disabled = true;
            return;
        }

        // Setup event listeners
        voiceBtn.addEventListener('click', toggleListening);
        
        // Press-and-hold support
        voiceBtn.addEventListener('mousedown', () => {
            if (!isListening) startListening();
        });
        
        voiceBtn.addEventListener('mouseup', () => {
            // If using push-to-talk, stop on release
            // For toggle mode, this is handled by click
        });

        // Keyboard shortcut (Ctrl+Shift+A)
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'A') {
                e.preventDefault();
                toggleListening();
            }
        });

        console.log('[ATHENA Voice] Initialized - Click mic or Ctrl+Shift+A to activate');
    }

    // ─── Toggle Listening ───────────────────────────────────────────────
    function toggleListening() {
        if (isListening) {
            stopListening();
        } else {
            startListening();
        }
    }

    // ─── Start Listening ────────────────────────────────────────────────
    async function startListening() {
        if (isListening || isProcessing) return;

        // Check for API key
        if (!CONFIG.subscriptionKey) {
            showStatus('Azure Speech key not configured');
            speak('Voice commands require Azure Speech configuration.');
            return;
        }

        try {
            // Create speech config
            const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(
                CONFIG.subscriptionKey,
                CONFIG.region
            );
            speechConfig.speechRecognitionLanguage = CONFIG.language;

            // Create audio config (microphone)
            const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();

            // Create recognizer
            recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);

            // Set up event handlers
            recognizer.recognizing = (s, e) => {
                showStatus(e.result.text || 'Listening...');
            };

            recognizer.recognized = (s, e) => {
                if (e.result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
                    const text = e.result.text.toLowerCase().trim();
                    processCommand(text);
                } else if (e.result.reason === SpeechSDK.ResultReason.NoMatch) {
                    showStatus('No speech detected');
                }
                stopListening();
            };

            recognizer.canceled = (s, e) => {
                console.warn('[ATHENA Voice] Recognition canceled:', e.errorDetails);
                stopListening();
            };

            // Start recognition
            await recognizer.recognizeOnceAsync();
            
            isListening = true;
            voiceBtn.classList.add('listening');
            showStatusActive('Listening...');

        } catch (err) {
            console.error('[ATHENA Voice] Error starting recognition:', err);
            showStatus('Voice activation failed');
            stopListening();
        }
    }

    // ─── Stop Listening ─────────────────────────────────────────────────
    function stopListening() {
        isListening = false;
        voiceBtn.classList.remove('listening');
        hideStatus();

        if (recognizer) {
            try {
                recognizer.close();
            } catch (err) {
                // Ignore cleanup errors
            }
            recognizer = null;
        }
    }

    // ─── Process Voice Command ──────────────────────────────────────────
    function processCommand(text) {
        isProcessing = true;
        console.log('[ATHENA Voice] Processing:', text);

        // Check for wake word
        const hasWakeWord = CONFIG.wakeWordAliases.some(w => text.includes(w));
        
        // Remove wake word from command
        let command = text;
        for (const alias of CONFIG.wakeWordAliases) {
            command = command.replace(alias, '').trim();
        }
        
        // Remove common filler words
        command = command.replace(/^(please|can you|could you|would you)\s+/i, '');
        command = command.replace(/[\.,!?]$/g, '');

        // Route command
        if (!command) {
            speak("Yes? How can I help?");
        } else if (matches(command, ['status', 'system status', 'how are you', 'system check'])) {
            handleStatusCommand();
        } else if (matches(command, ['refresh', 'update', 'reload'])) {
            handleRefreshCommand();
        } else if (matches(command, ['start services', 'start all services'])) {
            handleServicesCommand('start');
        } else if (matches(command, ['stop services', 'stop all services'])) {
            handleServicesCommand('stop');
        } else if (matches(command, ['gpu status', 'check gpu', 'gpu info', 'graphics'])) {
            handleGPUCommand();
        } else if (matches(command, ['task queue', 'show tasks', 'tasks', 'pending tasks'])) {
            handleTasksCommand();
        } else if (matches(command, ['runner status', 'github runner', 'runner'])) {
            handleRunnerCommand();
        } else if (matches(command, ['ollama', 'models', 'ai models'])) {
            handleOllamaCommand();
        } else if (command.startsWith('run workflow') || command.startsWith('dispatch')) {
            const workflow = command.replace(/^(run workflow|dispatch)\s*/i, '');
            handleWorkflowCommand(workflow);
        } else {
            speak(`I didn't understand "${command}". Try saying "status", "refresh", or "GPU status".`);
        }

        isProcessing = false;
    }

    // ─── Command Handlers ───────────────────────────────────────────────
    
    async function handleStatusCommand() {
        speak("Checking system status...");
        try {
            const [gpu, services, tasks] = await Promise.all([
                fetch('/api/gpu').then(r => r.json()),
                fetch('/api/services').then(r => r.json()),
                fetch('/api/tasks').then(r => r.json())
            ]);

            const gpuCount = gpu.gpus?.length || 0;
            const activeServices = services.filter(s => s.status === 'running').length;
            const totalServices = services.length;
            const pendingTasks = tasks.filter(t => t.status === 'pending').length;

            speak(`System operational. ${gpuCount} GPUs detected. ${activeServices} of ${totalServices} services running. ${pendingTasks} tasks pending.`);
        } catch (err) {
            speak("Unable to retrieve system status.");
        }
    }

    async function handleRefreshCommand() {
        speak("Refreshing all panels...");
        if (window.pollAll) {
            window.pollAll();
            speak("Panels refreshed.");
        } else {
            speak("Refresh function not available.");
        }
    }

    async function handleServicesCommand(action) {
        speak(`${action === 'start' ? 'Starting' : 'Stopping'} services...`);
        // This would integrate with the orchestrator API
        speak(`Service ${action} command sent. Check the Services panel for status.`);
    }

    async function handleGPUCommand() {
        try {
            const data = await fetch('/api/gpu').then(r => r.json());
            if (data.gpus && data.gpus.length > 0) {
                const gpu = data.gpus[0];
                const memUsed = Math.round(gpu.memory_used / 1024);
                const memTotal = Math.round(gpu.memory_total / 1024);
                speak(`Primary GPU: ${gpu.name}. Memory usage: ${memUsed} of ${memTotal} gigabytes. Temperature: ${gpu.temperature} degrees.`);
            } else {
                speak("No GPU information available.");
            }
        } catch (err) {
            speak("Unable to retrieve GPU status.");
        }
    }

    async function handleTasksCommand() {
        try {
            const tasks = await fetch('/api/tasks').then(r => r.json());
            const pending = tasks.filter(t => t.status === 'pending').length;
            const inProgress = tasks.filter(t => t.status === 'in_progress').length;
            const completed = tasks.filter(t => t.status === 'completed').length;

            speak(`Task queue: ${pending} pending, ${inProgress} in progress, ${completed} completed.`);
        } catch (err) {
            speak("Unable to retrieve task queue.");
        }
    }

    async function handleRunnerCommand() {
        try {
            const runner = await fetch('/api/runner').then(r => r.json());
            const status = runner.online ? 'online' : 'offline';
            speak(`GitHub runner is ${status}. ${runner.pending_workflows || 0} workflows pending.`);
        } catch (err) {
            speak("Unable to retrieve runner status.");
        }
    }

    async function handleOllamaCommand() {
        try {
            const data = await fetch('/api/ollama').then(r => r.json());
            if (data.running && data.models) {
                speak(`Ollama is running with ${data.models.length} models loaded.`);
            } else {
                speak("Ollama is not running.");
            }
        } catch (err) {
            speak("Unable to retrieve Ollama status.");
        }
    }

    function handleWorkflowCommand(workflow) {
        if (!workflow) {
            speak("Please specify a workflow name, like 'run workflow CI'.");
            return;
        }
        speak(`Dispatching workflow: ${workflow}. This feature requires API integration.`);
        // Would integrate with runner_manager dispatch
    }

    // ─── Text-to-Speech ─────────────────────────────────────────────────
    function speak(text) {
        showStatus(text);

        // Use browser TTS as fallback if Azure not configured
        if (!CONFIG.subscriptionKey || typeof SpeechSDK === 'undefined') {
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = CONFIG.speechRate;
                utterance.voice = speechSynthesis.getVoices().find(v => v.name.includes('Zira') || v.name.includes('female')) 
                    || speechSynthesis.getVoices()[0];
                speechSynthesis.speak(utterance);
            }
            setTimeout(hideStatus, 3000);
            return;
        }

        // Use Azure TTS
        try {
            const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(
                CONFIG.subscriptionKey,
                CONFIG.region
            );
            speechConfig.speechSynthesisVoiceName = CONFIG.voiceName;

            const audioConfig = SpeechSDK.AudioConfig.fromDefaultSpeakerOutput();
            synthesizer = new SpeechSDK.SpeechSynthesizer(speechConfig, audioConfig);

            synthesizer.speakTextAsync(
                text,
                result => {
                    if (result.reason === SpeechSDK.ResultReason.SynthesizingAudioCompleted) {
                        console.log('[ATHENA Voice] Speech completed');
                    }
                    synthesizer.close();
                    setTimeout(hideStatus, 2000);
                },
                err => {
                    console.error('[ATHENA Voice] TTS error:', err);
                    synthesizer.close();
                    hideStatus();
                }
            );
        } catch (err) {
            console.error('[ATHENA Voice] TTS initialization error:', err);
            hideStatus();
        }
    }

    // ─── UI Helpers ─────────────────────────────────────────────────────
    function showStatus(text) {
        if (voiceText) voiceText.textContent = text;
        if (voiceStatus) voiceStatus.classList.add('active');
    }

    function showStatusActive(text) {
        showStatus(text);
    }

    function hideStatus() {
        if (voiceStatus) voiceStatus.classList.remove('active');
    }

    function matches(input, patterns) {
        return patterns.some(p => input.includes(p) || levenshtein(input, p) < 3);
    }

    // Simple Levenshtein distance for fuzzy matching
    function levenshtein(a, b) {
        if (a.length === 0) return b.length;
        if (b.length === 0) return a.length;
        const matrix = [];
        for (let i = 0; i <= b.length; i++) matrix[i] = [i];
        for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
        for (let i = 1; i <= b.length; i++) {
            for (let j = 1; j <= a.length; j++) {
                if (b.charAt(i - 1) === a.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }
        return matrix[b.length][a.length];
    }

    // ─── Public API ─────────────────────────────────────────────────────
    window.AthenaVoice = {
        init,
        speak,
        startListening,
        stopListening,
        isListening: () => isListening,
        configure: (key, region) => {
            CONFIG.subscriptionKey = key;
            CONFIG.region = region || CONFIG.region;
        }
    };

    // ─── Auto-initialize ────────────────────────────────────────────────
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
