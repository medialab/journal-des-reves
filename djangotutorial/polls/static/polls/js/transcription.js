/**
 * AudioTranscriber - Transcription locale via Whisper Web (transformers.js)
 * ✨ Utilise @xenova/transformers pour une transcription 100% côté navigateur
 * 🔒 Aucune donnée n'est envoyée au serveur - tout reste LOCAL
 * 🚀 Supporte WebGPU (GPU) si disponible, sinon fallback CPU
 */

class AudioTranscriber {
    constructor(options = {}) {
        this.pipeline = null;
        this.isReady = false;
        this.isTranscribing = false;
        this.modelLoaded = false;
        
        // Configuration du modèle
        this.modelName = options.modelName || 'Xenova/whisper-tiny';  // distil-whisper-small pour plus rapide
        this.language = options.language || 'fr';
        
        // Callbacks
        this.onReadyCallback = options.onReady || (() => {});
        this.onProgressCallback = options.onProgress || (() => {});
        this.onCompleteCallback = options.onComplete || (() => {});
        this.onErrorCallback = options.onError || (() => {});
    }

    /**
     * Initialiser Whisper WASM via transformers.js
     */
    async initialize() {
        try {
            console.log('📦 Initialisation de Whisper Web (transformers.js)...');
            console.log(`   Modèle: ${this.modelName}`);
            console.log(`   Langue: ${this.language}`);
            
            // Charger transformers.js dynamiquement depuis CDN
            await this.loadTransformersLibrary();
            
            this.onProgressCallback('Chargement du modèle Whisper tiny...');
            
            // Créer le pipeline Whisper
            // La libraire transformers.js auto-télécharge le modèle ONNX
            console.log('🧠 Initialisation du pipeline ASR (Automatic Speech Recognition)...');
            
            const { pipeline } = window.TransformersJS;
            
            this.pipeline = await pipeline(
                'automatic-speech-recognition',
                this.modelName,
                {
                    device: this.getDevice(),  // 'webgpu' ou 'wasm'
                    quantized: true,            // Optimisé pour le navigateur
                    progress_callback: (progress) => {
                        const percent = Math.round(progress.status === 'progress' ? progress.progress : 0);
                        console.log(`   ⬇️ Téléchargement: ${percent}%`);
                        this.onProgressCallback(`Téléchargement modèle: ${percent}%`);
                    }
                }
            );
            
            this.isReady = true;
            this.modelLoaded = true;
            
            console.log('✅ Whisper Web prêt pour la transcription');
            this.onProgressCallback('✓ Whisper Web chargé');
            this.onReadyCallback();
            
            return true;
            
        } catch (error) {
            console.error('❌ Erreur initialisation Whisper:', error);
            this.onErrorCallback(`Initialisation échouée: ${error.message}`);
            return false;
        }
    }

    /**
     * Détecter le device (WebGPU ou WASM)
     */
    getDevice() {
        // Vérifier si WebGPU est disponible (GPU accélération)
        if (navigator.gpu !== undefined) {
            console.log('🚀 WebGPU détecté - utilisation GPU');
            return 'webgpu';
        }
        
        console.log('⚙️ WebGPU non disponible - fallback CPU');
        return 'wasm';
    }

    /**
     * Charger transformers.js depuis CDN Hugging Face
     */
    async loadTransformersLibrary() {
        return new Promise((resolve, reject) => {
            // Vérifier si déjà chargée
            if (window.TransformersJS) {
                console.log('✓ transformers.js déjà chargée');
                resolve();
                return;
            }

            console.log('📥 Chargement transformers.js depuis CDN...');
            
            // Créer un script tag
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/@xenova/transformers@2.11.0';
            script.type = 'text/javascript';
            script.async = true;
            
            script.onload = () => {
                console.log('✓ Script transformers.js chargé');
                
                // Attendre que la libraire soit prête globalement
                const checkInterval = setInterval(() => {
                    if (window.transformers) {
                        clearInterval(checkInterval);
                        // Exporter au namespace global
                        window.TransformersJS = window.transformers;
                        console.log('✓ window.TransformersJS disponible');
                        resolve();
                    }
                }, 100);
                
                // Timeout après 30s
                setTimeout(() => {
                    clearInterval(checkInterval);
                    if (window.transformers) {
                        window.TransformersJS = window.transformers;
                        resolve();
                    } else {
                        reject(new Error('Timeout: transformers.js ne s\'est pas chargée'));
                    }
                }, 30000);
            };
            
            script.onerror = () => {
                reject(new Error('Impossible de charger transformers.js depuis CDN'));
            };
            
            // Ajouter au DOM
            document.head.appendChild(script);
        });
    }

    /**
     * Transcrire un bloc audio (WAV, MP3, etc.)
     */
    async transcribe(audioBlob) {
        if (!this.isReady || !this.pipeline) {
            const error = 'Whisper Web n\'est pas prêt - attendez la fin du chargement';
            console.error('❌', error);
            this.onErrorCallback(error);
            return null;
        }

        if (this.isTranscribing) {
            const error = 'Transcription en cours... veuillez patienter';
            console.warn('⚠️', error);
            return null;
        }

        this.isTranscribing = true;

        try {
            console.log(`🎙️ Transcription audio (${(audioBlob.size / 1024).toFixed(2)} KB)`);
            this.onProgressCallback('Décodage audio...');
            
            // Convertir le blob en ArrayBuffer
            const arrayBuffer = await audioBlob.arrayBuffer();
            
            // Décoder le WAV/MP3
            console.log('📝 Décodage audio en PCM...');
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            
            console.log(`   ✓ Durée: ${audioBuffer.duration.toFixed(2)}s`);
            console.log(`   ✓ Sample rate: ${audioBuffer.sampleRate} Hz`);
            
            // Extraire les données PCM
            let pcm = audioBuffer.getChannelData(0);  // Prendre le premier canal
            
            // Si stéréo, moyenner les canaux
            if (audioBuffer.numberOfChannels > 1) {
                console.log('   ✓ Stéréo détecté → conversion en mono');
                const stereoData = new Float32Array(audioBuffer.getChannelData(0).length);
                for (let i = 0; i < stereoData.length; i++) {
                    stereoData[i] = (audioBuffer.getChannelData(0)[i] + audioBuffer.getChannelData(1)[i]) / 2;
                }
                pcm = stereoData;
            }
            
            // Rééchantillonner à 16kHz si nécessaire (Whisper utilise 16kHz)
            if (audioBuffer.sampleRate !== 16000) {
                console.log(`   ✓ Rééchantillonnage: ${audioBuffer.sampleRate} → 16000 Hz`);
                pcm = this.resampleAudio(pcm, audioBuffer.sampleRate, 16000);
            }
            
            // Démarrer la transcription
            this.onProgressCallback('Transcription en cours (peut prendre 1-3 min)...');
            console.log('⏳ Lancement du modèle Whisper...');
            
            const result = await this.pipeline(pcm, {
                language: this.language,
                top_k: 0,
                do_sample: false,
                max_new_tokens: 128,
                return_timestamps: false
            });
            
            const transcript = (result.text || '').trim();
            
            this.onProgressCallback('Transcription terminée ✓');
            this.onCompleteCallback(transcript);
            
            console.log(`✅ Transcription complétée:`);
            console.log(`   "${transcript.substring(0, 150)}${transcript.length > 150 ? '...' : ''}"`);
            
            return transcript;
            
        } catch (error) {
            console.error('❌ Erreur transcription:', error.message);
            console.error('   Stack:', error.stack);
            this.onErrorCallback(`Erreur: ${error.message}`);
            return null;
        } finally {
            this.isTranscribing = false;
        }
    }

    /**
     * Rééchantillonner l'audio à une nouvelle fréquence
     * Converti de N kHz vers 16 kHz (standard Whisper)
     */
    resampleAudio(audioData, fromRate, toRate) {
        if (fromRate === toRate || audioData.length === 0) {
            return audioData;
        }

        const ratio = fromRate / toRate;
        const newLength = Math.round(audioData.length / ratio);
        const result = new Float32Array(newLength);
        let pointerIn = 0;
        let pointerOut = 0;

        while (pointerIn < audioData.length) {
            const amountToRead = Math.min(ratio, audioData.length - pointerIn);
            let sum = 0;

            for (let i = 0; i < amountToRead; i++) {
                sum += audioData[Math.floor(pointerIn + i)];
            }

            result[pointerOut] = sum / amountToRead;
            pointerOut++;
            pointerIn += ratio;
        }

        return result;
    }

    /**
     * Changer le modèle Whisper
     * Modèles disponibles:
     * - Xenova/whisper-tiny (39 MB - ✅ Recommandé pour navigateur)
     * - Xenova/whisper-base (140 MB)
     * - distil-whisper-small (100 MB - plus rapide, moins précis)
     */
    async loadModel(modelName = 'Xenova/whisper-tiny') {
        try {
            if (this.modelLoaded && this.modelName === modelName) {
                console.log(`✓ Modèle ${modelName} déjà chargé`);
                return true;
            }

            this.isReady = false;
            this.pipeline = null;
            this.modelLoaded = false;
            this.modelName = modelName;
            
            console.log(`📥 Changement de modèle: ${modelName}`);
            
            // Réinitialiser avec le nouveau modèle
            return await this.initialize();
            
        } catch (error) {
            console.error('❌ Erreur chargement modèle:', error);
            this.onErrorCallback(error.message);
            return false;
        }
    }

    /**
     * Vérifier si Whisper est prêt
     */
    isAvailable() {
        return this.isReady && this.pipeline !== null;
    }

    /**
     * Vérifier si une transcription est en cours
     */
    isTranscribingNow() {
        return this.isTranscribing;
    }

    /**
     * Nettoyer les ressources
     */
    cleanup() {
        // transformers.js reste en mémoire pour les réutilisations
        // (optimisation de performance)
        console.log('🧹 AudioTranscriber cleanup');
        this.isTranscribing = false;
    }

    /**
     * Forcer le rechargement du modèle
     */
    clearCache() {
        console.log('🗑️ Effacement du cache du modèle...');
        // Forcer le rechargement du modèle
        this.pipeline = null;
        this.modelLoaded = false;
        this.isReady = false;
    }
}

// Exporter pour utilisation globale
window.AudioTranscriber = AudioTranscriber;

