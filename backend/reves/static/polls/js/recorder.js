/**
 * AudioRecorder - Enregistrement audio WAV côté navigateur
 * Utilise Web Audio API pour capturer le micro et générer un fichier WAV
 */

class AudioRecorder {
    constructor(options = {}) {
        this.mediaStream = null;
        this.audioContext = null;
        this.processor = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        
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
     * Initialiser et demander l'accès au micro
     */
    async initialize() {
        try {
            // Demander l'accès au micro
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: false,
                    sampleRate: this.sampleRate
                }
            });

            // Créer le contexte audio
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: this.sampleRate
            });

            // Créer le MediaRecorder
            const options = {
                mimeType: 'audio/wav',
                audioBitsPerSecond: this.sampleRate * this.bitDepth * this.channelCount
            };

            // Vérifier si le format WAV est supporté
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                options.mimeType = '';
            }

            this.mediaRecorder = new MediaRecorder(this.mediaStream, options);
            
            // Gérer les données audio
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.handleRecordingStop();
            };

            console.log('✅ Enregistrement audio initialisé');
            return true;
        } catch (error) {
            console.error('❌ Erreur lors de l\'initialisation:', error);
            this.onErrorCallback(error.message);
            return false;
        }
    }

    /**
     * Démarrer l'enregistrement
     */
    start() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'inactive') {
            this.audioChunks = [];
            this.isRecording = true;
            this.mediaRecorder.start();
            this.onStartCallback();
            console.log('🎤 Enregistrement commencé');
        }
    }

    /**
     * Arrêter l'enregistrement
     */
    stop() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
            this.isRecording = false;
            console.log('⏹️ Enregistrement arrêté');
        }
    }

    /**
     * Gérer l'arrêt de l'enregistrement et générer le WAV
     */
    async handleRecordingStop() {
        try {
            // Créer un blob à partir des chunks audio
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
            
            // Si le blob n'est pas du WAV, le convertir
            if (!audioBlob.type.includes('wav')) {
                const wavBlob = await this.convertToWAV(audioBlob);
                this.onStopCallback(wavBlob);
            } else {
                this.onStopCallback(audioBlob);
            }

            console.log(`✅ Audio prêt (${(audioBlob.size / 1024).toFixed(2)} KB)`);
        } catch (error) {
            console.error('❌ Erreur lors de la conversion:', error);
            this.onErrorCallback(error.message);
        }
    }

    /**
     * Convertir blob audio en WAV si nécessaire
     */
    async convertToWAV(audioBlob) {
        const arrayBuffer = await audioBlob.arrayBuffer();
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        
        // Obtenir les données PCM
        const pcmData = audioBuffer.getChannelData(0);
        
        // Créer le WAV
        const wavData = this.encodeWAV(pcmData, audioBuffer.sampleRate);
        return new Blob([wavData], { type: 'audio/wav' });
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
        view.setUint16(20, 1, true); // PCM
        view.setUint16(22, 1, true); // Mono
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
        if (this.audioContext) {
            this.audioContext.close();
        }
        this.mediaRecorder = null;
        this.audioChunks = [];
        console.log('🧹 Ressources audio libérées');
    }

    /**
     * Obtenir les données audio en base64
     */
    getAudioAsDataURL() {
        if (this.audioChunks.length === 0) return null;
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        return URL.createObjectURL(audioBlob);
    }
}

// Exporter pour utilisation globale
window.AudioRecorder = AudioRecorder;
