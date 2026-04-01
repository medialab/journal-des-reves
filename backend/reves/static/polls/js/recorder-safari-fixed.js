/**
 * AudioRecorder - Enregistrement audio cross-browser (Chrome, Firefox, Safari)
 * Support natif pour Safari iOS 14+ et Safari Mac 14.1+
 * Gère automatiquement les différences de MIME types entre navigateurs
 */

class AudioRecorder {
    constructor(options = {}) {
        this.mediaStream = null;
        this.audioContext = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.recordedMimeType = null;  // Track actual MIME type used
        
        // Configuration
        this.sampleRate = options.sampleRate || 16000;
        this.channelCount = options.channelCount || 1;
        this.bitDepth = options.bitDepth || 16;
        
        // Callbacks
        this.onStartCallback = options.onStart || (() => {});
        this.onStopCallback = options.onStop || (() => {});
        this.onErrorCallback = options.onError || (() => {});
        this.onDataCallback = options.onData || (() => {});
    }

    /**
     * Vérifier la disponibilité de l'enregistrement
     * IMPORTANT: getUserMedia ne fonctionne que sur HTTPS (ou localhost)
     */
    static isAvailable() {
        // Check for secure context
        const isLoopbackHost = ['localhost', '127.0.0.1', '::1'].includes(location.hostname) || location.hostname.endsWith('.localhost');
        const isSecureContextForRecording = location.protocol === 'https:' || isLoopbackHost;

        if (!isSecureContextForRecording) {
            return { 
                available: false, 
                reason: 'L\'enregistrement audio nécessite HTTPS. Avec ngrok, ouvrez l\'URL en https://... (pas http://). En local, localhost/127.0.0.1 est autorisé.' 
            };
        }
        
        // Check for mediaDevices
        if (!navigator.mediaDevices?.getUserMedia) {
            return { 
                available: false, 
                reason: 'getUserMedia non supporté par ce navigateur' 
            };
        }
        
        return { available: true };
    }

    /**
     * Trouver le MIME type supporté par le navigateur
     * Priorité: audio/mp4 (Safari) > audio/webm (Chrome/Firefox) > fallback
     */
    static findSupportedMimeType() {
        const mimeTypes = [
            'audio/mp4',           // Safari, iOS (BEST for Safari)
            'audio/webm;codecs=opus',  // Chrome, Firefox
            'audio/wav',
            'audio/ogg',
        ];
        
        const supported = mimeTypes.find(type => 
            MediaRecorder.isTypeSupported(type)
        );
        
        if (!supported) {
            console.warn('⚠️ Aucun format audio supporté trouvé, utilisation du format par défaut');
            return '';  // Let browser choose
        }
        
        return supported;
    }

    /**
     * Initialiser et demander l'accès au micro
     * Gère les différences Safari automatiquement
     */
    async initialize() {
        try {
            // Vérifier la disponibilité
            const availability = AudioRecorder.isAvailable();
            if (!availability.available) {
                throw new Error(availability.reason);
            }

            // Demander l'accès au micro
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: false,
                    sampleRate: { ideal: this.sampleRate }
                }
            });

            // Vérifier que le track audio est enabled (important pour iOS)
            const audioTracks = this.mediaStream.getAudioTracks();
            if (audioTracks.length === 0) {
                throw new Error('Aucune piste audio obtenue');
            }
            audioTracks.forEach(track => {
                if (!track.enabled) track.enabled = true;
            });

            // Créer le contexte audio
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();

            // Trouver le MIME type supporté
            const mimeType = AudioRecorder.findSupportedMimeType();
            const options = {};
            
            if (mimeType) {
                options.mimeType = mimeType;
            }
            
            // Note: Safari n'aime pas les option audioBitsPerSecond avec audio/mp4
            if (mimeType !== 'audio/mp4') {
                options.audioBitsPerSecond = 128000;
            }

            this.mediaRecorder = new MediaRecorder(this.mediaStream, options);
            this.recordedMimeType = this.mediaRecorder.mimeType;  // Store actual type
            
            // Gérer les données audio
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.handleRecordingStop();
            };

            this.mediaRecorder.onerror = (event) => {
                console.error('❌ Erreur MediaRecorder:', event.error);
                this.onErrorCallback(`Erreur d'enregistrement: ${event.error}`);
            };

            console.log(`✅ Enregistrement audio initialisé (format: ${this.recordedMimeType || 'default'})`);
            return true;
        } catch (error) {
            console.error('❌ Erreur lors de l\'initialisation:', error.name, error.message);
            this.onErrorCallback(error.message);
            return false;
        }
    }

    /**
     * Démarrer l'enregistrement
     */
    start() {
        if (!this.mediaRecorder) {
            console.error('❌ MediaRecorder non initialisé');
            return false;
        }
        
        if (this.mediaRecorder.state !== 'inactive') {
            console.warn('⚠️ Enregistrement déjà en cours');
            return false;
        }

        this.audioChunks = [];
        this.isRecording = true;
        this.mediaRecorder.start();
        this.onStartCallback();
        console.log('🎤 Enregistrement commencé');
        return true;
    }

    /**
     * Pause l'enregistrement
     */
    pause() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.pause();
            console.log('⏸️ Enregistrement en pause');
            return true;
        }
        return false;
    }

    /**
     * Reprendre l'enregistrement
     */
    resume() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'paused') {
            this.mediaRecorder.resume();
            console.log('▶️ Enregistrement repris');
            return true;
        }
        return false;
    }

    /**
     * Arrêter l'enregistrement
     */
    stop() {
        if (!this.mediaRecorder) {
            console.error('❌ MediaRecorder non initialisé');
            return false;
        }

        if (this.mediaRecorder.state === 'inactive') {
            console.warn('⚠️ Enregistrement déjà arrêté');
            return false;
        }

        this.mediaRecorder.stop();
        this.isRecording = false;
        console.log('⏹️ Enregistrement arrêté');
        return true;
    }

    /**
     * Gérer l'arrêt de l'enregistrement et créer le blob
     * IMPORTANT: Utilise le MIME type réel enregistré par le navigateur
     */
    async handleRecordingStop() {
        try {
            // Créer un blob avec le MIME type réel utilisé
            // C'est crucial pour Safari qui peut utiliser audio/mp4 au lieu de audio/wav
            const actualMimeType = this.recordedMimeType || 'audio/wav';
            const audioBlob = new Blob(this.audioChunks, { type: actualMimeType });
            
            // Arrêter le flux audio
            this.mediaStream.getTracks().forEach(track => track.stop());

            console.log(`✅ Audio prêt (${(audioBlob.size / 1024).toFixed(2)} KB, format: ${actualMimeType})`);
            
            this.onStopCallback(audioBlob);
        } catch (error) {
            console.error('❌ Erreur lors de l\'arrêt de l\'enregistrement:', error);
            this.onErrorCallback(error.message);
        }
    }

    /**
     * Convertir audio en WAV si nécessaire (pour post-traitement)
     * Utile si vous besoin absolument d'un WAV côté serveur
     */
    async convertToWAV(audioBlob) {
        try {
            const arrayBuffer = await audioBlob.arrayBuffer();
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
            
            // Obtenir les données PCM
            const pcmData = audioBuffer.getChannelData(0);
            
            // Créer le WAV
            const wavData = this.encodeWAV(pcmData, audioBuffer.sampleRate);
            const wavBlob = new Blob([wavData], { type: 'audio/wav' });
            
            console.log(`✅ Conversion WAV complétée (${(wavBlob.size / 1024).toFixed(2)} KB)`);
            return wavBlob;
        } catch (error) {
            console.error('❌ Erreur lors de la conversion WAV:', error);
            throw error;
        }
    }

    /**
     * Encoder les données PCM en WAV
     */
    encodeWAV(samples, sampleRate) {
        const buffer = new ArrayBuffer(44 + samples.length * 2);
        const view = new DataView(buffer);

        // Write WAV header
        const writeString = (offset, string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };

        writeString(0, 'RIFF');
        view.setUint32(4, 36 + samples.length * 2, true);
        writeString(8, 'WAVE');
        writeString(12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);  // PCM
        view.setUint16(22, 1, true);  // Mono
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * 2, true);
        view.setUint16(32, 2, true);
        view.setUint16(34, 16, true);
        writeString(36, 'data');
        view.setUint32(40, samples.length * 2, true);

        // Write audio data
        let offset = 44;
        for (let i = 0; i < samples.length; i++, offset += 2) {
            const s = Math.max(-1, Math.min(1, samples[i]));
            view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        }

        return buffer;
    }

    /**
     * Arrêter complètement et libérer les ressources
     */
    cleanup() {
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
        }
        if (this.audioContext && this.audioContext.state !== 'closed') {
            this.audioContext.close();
        }
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        console.log('🧹 Ressources audio libérées');
    }

    /**
     * Obtenir les informations d'enregistrement
     */
    getRecordingInfo() {
        return {
            mimeType: this.recordedMimeType,
            isRecording: this.isRecording,
            chunksSize: this.audioChunks.length,
            state: this.mediaRecorder?.state || 'inactive'
        };
    }

    /**
     * Obtenir les données audio en URL blob
     * ATTENTION: À utiliser prudemment sur iOS (voir guide Safari)
     */
    getAudioAsDataURL() {
        if (this.audioChunks.length === 0) return null;
        const audioBlob = new Blob(this.audioChunks, { 
            type: this.recordedMimeType || 'audio/wav' 
        });
        return URL.createObjectURL(audioBlob);
    }
}

// Exporter pour utilisation globale
window.AudioRecorder = AudioRecorder;
