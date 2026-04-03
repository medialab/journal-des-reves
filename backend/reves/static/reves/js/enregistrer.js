const recorderForm = document.getElementById('reve-form');
const RECORDING_MODE = recorderForm?.dataset.recordingMode || 'audio_recording';
const IS_SAFARI = document.documentElement.classList.contains('is-safari');
const SAFARI_AUDIO_RECORDER = window.AudioRecorder;

document.addEventListener('DOMContentLoaded', function() {
	setRecorderEntryLayout(RECORDING_MODE === 'audio_recording');
	applyRecordingModeUI();
	if (RECORDING_MODE === 'audio_recording') {
		initRecorder();
	}
	initFormHandlers();
});

let mediaRecorder = null;
let audioChunks = [];
let recordingStartTime = null;
let recordingTimerInterval = null;
let currentAudioBlob = null;

function showElement(element, displayValue = 'block') {
	if (!element) return;
	element.classList.remove('is-hidden-inline');
	element.style.display = displayValue;
}

function hideElement(element) {
	if (!element) return;
	element.classList.add('is-hidden-inline');
	element.style.display = 'none';
}

function applyRecordingModeUI() {
	const sectionAudio = document.querySelector('.section-audio');
	const sectionTextDream = document.getElementById('sectionTextDream');
	const textChoiceButtons = document.getElementById('textChoiceButtons');
	const textDreamComposer = document.getElementById('textDreamComposer');
	const noMemoryBtn = document.getElementById('noMemoryBtn');
	const noMemoryBtnText = document.getElementById('noMemoryBtnText');
	const questionsGrid = document.getElementById('questionsGrid');
	const audioInput = document.getElementById('audioInput');

	if (RECORDING_MODE === 'text_only') {
		hideElement(sectionAudio);
		showElement(sectionTextDream, 'block');
		showElement(textChoiceButtons, 'flex');
		hideElement(textDreamComposer);
		hideElement(noMemoryBtn);
		showElement(noMemoryBtnText, 'block');
		hideElement(questionsGrid);
		if (audioInput) audioInput.removeAttribute('required');
		setRecorderEntryLayout(true);
	} else {
		showElement(sectionAudio, 'block');
		hideElement(sectionTextDream);
		showElement(noMemoryBtn, 'block');
		hideElement(noMemoryBtnText);
	}
}

function setRecorderEntryLayout(isInitial) {
	const form = document.getElementById('reve-form');
	const formActions = document.getElementById('formActions');
	if (!form || !formActions) {
		return;
	}

	form.classList.toggle('initial-recorder-view', isInitial);
	formActions.style.display = isInitial ? 'none' : 'grid';
}

function initRecorder() {
	const startBtn = document.getElementById('startBtn');
	const pauseBtn = document.getElementById('pauseBtn');
	const stopBtn = document.getElementById('stopBtn');
	const rerecordBtn = document.getElementById('rerecordBtn');
	const audioPreview = document.getElementById('audioPreview');
	const audioPlayer = document.getElementById('audioPlayer');
	const audioInput = document.getElementById('audioInput');
	const statusText = document.getElementById('statusText');
	const statusIndicator = document.getElementById('statusIndicator');
	const recordingTime = document.getElementById('recordingTime');
	let recordedAudioMimeType = null;

	function findSupportedMimeType() {
		const mimeTypes = [
			'audio/mp4',
			'audio/webm;codecs=opus',
			'audio/wav',
		];

		const supported = mimeTypes.find(type => MediaRecorder.isTypeSupported(type));
		return supported || '';
	}

	startBtn.addEventListener('click', async function() {
		try {
			if (IS_SAFARI && SAFARI_AUDIO_RECORDER?.isAvailable) {
				const availability = SAFARI_AUDIO_RECORDER.isAvailable();
				if (!availability.available) {
					throw new Error(availability.reason || 'Enregistrement audio indisponible sur Safari.');
				}
			} else {
				const isLoopbackHost = ['localhost', '127.0.0.1', '::1'].includes(location.hostname) || location.hostname.endsWith('.localhost');
				const isSecureContextForRecording = location.protocol === 'https:' || isLoopbackHost;
				if (!isSecureContextForRecording) {
					throw new Error('L\'enregistrement audio necessite HTTPS. Avec ngrok, ouvrez l\'URL en https://... (pas http://). En local, localhost/127.0.0.1 est autorise.');
				}
			}

			if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
				throw new Error('getUserMedia non supporte - utilisez Chrome, Firefox, Safari 14.1+ ou Edge');
			}

			const stream = await navigator.mediaDevices.getUserMedia({
				audio: {
					echoCancellation: true,
					noiseSuppression: true,
					autoGainControl: false
				}
			});

			const audioTracks = stream.getAudioTracks();
			if (audioTracks.length === 0) {
				throw new Error('Aucune piste audio disponible');
			}

			const mimeType = (IS_SAFARI && SAFARI_AUDIO_RECORDER?.findSupportedMimeType)
				? SAFARI_AUDIO_RECORDER.findSupportedMimeType()
				: findSupportedMimeType();
			const recorderOptions = {};
			if (mimeType) {
				recorderOptions.mimeType = mimeType;
			}

			mediaRecorder = new MediaRecorder(stream, recorderOptions);
			recordedAudioMimeType = mediaRecorder.mimeType;
			audioChunks = [];
			setRecorderEntryLayout(false);

			console.log(`MediaRecorder cree avec format: ${recordedAudioMimeType}`);

			const recorderStatus = document.getElementById('recorderStatus');
			const recorderSecondaryControls = document.getElementById('recorderSecondaryControls');
			const noMemoryBtn = document.getElementById('noMemoryBtn');
			const questionsGrid = document.getElementById('questionsGrid');
			showElement(recorderStatus, 'flex');
			showElement(recorderSecondaryControls, 'flex');
			hideElement(noMemoryBtn);
			startBtn.style.display = 'none';
			if (questionsGrid) {
				showElement(questionsGrid, 'flex');
			}

			mediaRecorder.addEventListener('dataavailable', function(event) {
				audioChunks.push(event.data);
			});

			mediaRecorder.addEventListener('stop', function() {
				currentAudioBlob = new Blob(audioChunks, { type: recordedAudioMimeType || 'audio/wav' });

				let filename = 'dream-recording.wav';
				let contentType = 'audio/wav';

				if (recordedAudioMimeType?.includes('mp4')) {
					filename = 'dream-recording.m4a';
					contentType = 'audio/mp4';
				} else if (recordedAudioMimeType?.includes('webm')) {
					filename = 'dream-recording.webm';
					contentType = 'audio/webm';
				}

				const audioFile = new File([currentAudioBlob], filename, { type: contentType });

				// Safari private mode may throw on DataTransfer constructor.
				try {
					const dataTransfer = new DataTransfer();
					dataTransfer.items.add(audioFile);
					audioInput.files = dataTransfer.files;
				} catch (_error) {
					console.warn('DataTransfer indisponible: fallback blob direct au submit.');
					audioInput.removeAttribute('required');
				}

				const audioUrl = URL.createObjectURL(currentAudioBlob);
				audioPlayer.src = audioUrl;
				showElement(audioPreview, 'block');

				document.getElementById('submitBtn').disabled = false;

				clearInterval(recordingTimerInterval);
				recordingTimerInterval = null;

				stream.getTracks().forEach(track => track.stop());

				pauseBtn.disabled = true;
				pauseBtn.textContent = 'Pause';
			});

			mediaRecorder.start();
			startBtn.disabled = true;
			pauseBtn.disabled = false;
			pauseBtn.textContent = 'Pause';
			stopBtn.disabled = false;
			statusText.textContent = 'Enregistrement en cours...';
			statusIndicator.classList.add('recording');

			recordingStartTime = Date.now();
			recordingTimerInterval = setInterval(updateRecordingTime, 100);
		} catch (error) {
			console.error('Erreur d\'acces au microphone:', error.name, error.message);

			let userMessage = 'Impossible d\'enregistrer le micro.';

			if (error.name === 'NotAllowedError') {
				userMessage = 'Permission refusee. Verifiez les permissions du microphone dans les parametres du navigateur.';
			} else if (error.name === 'NotFoundError') {
				userMessage = 'Aucun microphone detecte. Verifiez que votre appareil dispose d\'un microphone.';
			} else if (error.name === 'NotReadableError') {
				userMessage = 'Microphone occupe ou non accessible. Fermez les autres applications utilisant le microphone.';
			} else if (error.message?.includes('HTTPS')) {
				userMessage = error.message;
			}

			alert(userMessage);

			startBtn.disabled = false;
			startBtn.style.display = 'block';
		}
	});

	pauseBtn.addEventListener('click', function() {
		if (!mediaRecorder) {
			return;
		}

		if (mediaRecorder.state === 'recording') {
			mediaRecorder.pause();
			statusText.textContent = 'Enregistrement en pause';
			statusIndicator.classList.remove('recording');
			pauseBtn.textContent = 'Reprendre';
			if (recordingTimerInterval) {
				clearInterval(recordingTimerInterval);
				recordingTimerInterval = null;
			}
		} else if (mediaRecorder.state === 'paused') {
			mediaRecorder.resume();
			statusText.textContent = 'Enregistrement en cours...';
			statusIndicator.classList.add('recording');
			pauseBtn.textContent = 'Pause';
			if (!recordingTimerInterval) {
				recordingStartTime = Date.now() - (parseInt(recordingTime.textContent.split(':')[0], 10) * 60000 + parseInt(recordingTime.textContent.split(':')[1], 10) * 1000);
				recordingTimerInterval = setInterval(updateRecordingTime, 100);
			}
		}
	});

	stopBtn.addEventListener('click', function() {
		if (mediaRecorder && mediaRecorder.state !== 'inactive') {
			mediaRecorder.stop();
		}
		startBtn.disabled = false;
		pauseBtn.disabled = true;
		pauseBtn.textContent = 'Pause';
		stopBtn.disabled = true;
		statusText.textContent = 'Enregistrement termine';
		statusIndicator.classList.remove('recording');
	});

	rerecordBtn.addEventListener('click', function() {
		audioPreview.style.display = 'none';
		audioInput.value = '';
		currentAudioBlob = null;
		document.getElementById('submitBtn').disabled = true;
		pauseBtn.disabled = true;
		pauseBtn.textContent = 'Pause';
		statusText.textContent = 'Pret a enregistrer';
		statusIndicator.classList.remove('recording');
		recordingTime.textContent = '00:00';

		const recorderStatus = document.getElementById('recorderStatus');
		const recorderSecondaryControls = document.getElementById('recorderSecondaryControls');
		const noMemoryBtn = document.getElementById('noMemoryBtn');
		const questionsGrid = document.getElementById('questionsGrid');

		recorderStatus.style.display = 'none';
		recorderSecondaryControls.style.display = 'none';
		noMemoryBtn.style.display = 'block';
		startBtn.style.display = 'inline-flex';
		startBtn.disabled = false;
		if (questionsGrid) {
			questionsGrid.style.display = 'none';
		}
		setRecorderEntryLayout(true);
	});

	function updateRecordingTime() {
		const elapsed = Date.now() - recordingStartTime;
		const minutes = Math.floor(elapsed / 60000);
		const seconds = Math.floor((elapsed % 60000) / 1000);
		recordingTime.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
	}
}

function initFormHandlers() {
	const form = document.getElementById('reve-form');
	const submitBtn = document.getElementById('submitBtn');
	const successMessageWithAudio = document.getElementById('successMessageWithAudio');
	const successMessageNoMemory = document.getElementById('successMessageNoMemory');
	const emotionsGroup = document.getElementById('emotionsGroup');
	const addEmotionBtn = document.getElementById('addEmotionBtn');
	const customEmotionInput = document.getElementById('customEmotionInput');
	const elementsGroup = document.getElementById('elementsGroup');
	const addElementBtn = document.getElementById('addElementBtn');
	const customElementInput = document.getElementById('customElementInput');
	const noMemoryBtn = document.getElementById('noMemoryBtn');
	const noMemoryBtnText = document.getElementById('noMemoryBtnText');
	const startTextBtn = document.getElementById('startTextBtn');
	const textChoiceButtons = document.getElementById('textChoiceButtons');
	const textDreamComposer = document.getElementById('textDreamComposer');
	const startBtn = document.getElementById('startBtn');
	const pauseBtn = document.getElementById('pauseBtn');
	const stopBtn = document.getElementById('stopBtn');
	const existenceSouvenirInput = document.getElementById('existenceSouvenir');
	const questionsGrid = document.getElementById('questionsGrid');
	const emotionsSection = document.getElementById('emotionsSection');
	const audioInput = document.getElementById('audioInput');
	const dreamTextarea = document.getElementById('dreamTextarea');

	if (!form) {
		return;
	}

	const submitUrl = form.dataset.submitUrl;
	const redirectUrl = form.dataset.redirectUrl;

	let noMemoryMode = false;
	let noMemorySubmitting = false;

	if (RECORDING_MODE === 'text_only' && startTextBtn) {
		startTextBtn.addEventListener('click', function() {
			if (textChoiceButtons) {
				hideElement(textChoiceButtons);
			}
			if (textDreamComposer) {
				showElement(textDreamComposer, 'block');
			}
			if (questionsGrid) {
				showElement(questionsGrid, 'flex');
			}
			setRecorderEntryLayout(false);
			if (dreamTextarea) {
				dreamTextarea.focus();
			}
			checkForm();
		});
	}

	const handleNoMemory = function() {
		if (noMemorySubmitting) {
			return;
		}

		noMemorySubmitting = true;
		noMemoryMode = true;
		existenceSouvenirInput.value = '0';
		audioInput.removeAttribute('required');

		if (questionsGrid) {
			hideElement(questionsGrid);
		}

		if (emotionsSection) {
			hideElement(emotionsSection);
		}

		if (noMemoryBtn) {
			noMemoryBtn.disabled = true;
		}
		if (noMemoryBtnText) {
			noMemoryBtnText.disabled = true;
		}
		if (startBtn) {
			startBtn.disabled = true;
		}
		if (pauseBtn) {
			pauseBtn.disabled = true;
		}
		if (stopBtn) {
			stopBtn.disabled = true;
		}

		form.requestSubmit();
	};

	if (noMemoryBtn) {
		noMemoryBtn.addEventListener('click', handleNoMemory);
	}
	if (noMemoryBtnText) {
		noMemoryBtnText.addEventListener('click', handleNoMemory);
	}

	const checkForm = () => {
		if (noMemoryMode) {
			submitBtn.disabled = false;
			return;
		}

		let isValid = true;

		if (RECORDING_MODE === 'text_only') {
			if (!dreamTextarea || !dreamTextarea.value.trim()) {
				isValid = false;
			}
		} else if (!currentAudioBlob) {
			isValid = false;
		}

		form.querySelectorAll('input[type="radio"][required]').forEach(radio => {
			const groupName = radio.name;
			if (!form.querySelector(`input[name="${groupName}"]:checked`)) {
				isValid = false;
			}
		});

		submitBtn.disabled = !isValid;
	};

	const updateChoiceStyles = () => {
		const groups = {};
		form.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach(input => {
			const groupName = input.name;
			if (!groups[groupName]) {
				groups[groupName] = [];
			}
			groups[groupName].push(input);
		});

		Object.values(groups).forEach(inputs => {
			const anyChecked = inputs.some(input => input.checked);
			inputs.forEach(input => {
				const label = input.closest('label');
				if (!label) {
					return;
				}
				label.classList.toggle('is-selected', input.checked);
				label.classList.toggle('is-dim', anyChecked && !input.checked);
			});
		});
	};

	form.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach(field => {
		field.addEventListener('change', () => {
			checkForm();
			updateChoiceStyles();
		});
	});

	if (dreamTextarea) {
		dreamTextarea.addEventListener('input', checkForm);
	}

	const normalizeEmotion = (value) => value.trim().toLowerCase().replace(/\s+/g, ' ');
	const existingEmotionValues = () => {
		if (!emotionsGroup) {
			return [];
		}
		// Récupère le TEXTE VISUEL des émotions, pas la valeur de l'input
		return Array.from(emotionsGroup.querySelectorAll('input[name="emotions_reve"], input[name="emotions_custom"]'))
			.map(input => {
				// Récupère le texte visuel du label frère
				const label = input.closest('label');
				const text = label ? label.textContent.trim() : input.value;
				return normalizeEmotion(text);
			});
	};

	const normalizeElement = (value) => value.trim().toLowerCase().replace(/\s+/g, ' ');
	const existingElementValues = () => {
		if (!elementsGroup) {
			return [];
		}
		// Récupère le TEXTE VISUEL des éléments, pas la valeur de l'input
		return Array.from(elementsGroup.querySelectorAll('input[name="elements_reve"], input[name="elements_custom"]'))
			.map(input => {
				// Récupère le texte visuel du label frère
				const label = input.closest('label');
				const text = label ? label.textContent.trim() : input.value;
				return normalizeElement(text);
			});
	};

	const addCustomEmotion = () => {
		const rawValue = customEmotionInput.value;
		const cleanedValue = rawValue.trim();
		if (!cleanedValue) {
			return;
		}

		const normalizedValue = normalizeEmotion(cleanedValue);
		if (existingEmotionValues().includes(normalizedValue)) {
			customEmotionInput.value = '';
			return;
		}

		const label = document.createElement('label');
		label.className = 'checkbox-label choice-label custom-emotion';
		const input = document.createElement('input');
		input.type = 'checkbox';
		input.name = 'emotions_custom';
		input.value = cleanedValue;
		input.checked = true;
		const text = document.createElement('span');
		text.className = 'checkbox-text';
		text.textContent = cleanedValue;
		label.appendChild(input);
		label.appendChild(text);
		emotionsGroup.appendChild(label);

		input.addEventListener('change', () => {
			checkForm();
			updateChoiceStyles();
		});

		customEmotionInput.value = '';
		updateChoiceStyles();
	};

	const addCustomElement = () => {
		if (!elementsGroup || !customElementInput) {
			return;
		}

		const rawValue = customElementInput.value;
		const cleanedValue = rawValue.trim();
		if (!cleanedValue) {
			return;
		}

		const normalizedValue = normalizeElement(cleanedValue);
		if (existingElementValues().includes(normalizedValue)) {
			customElementInput.value = '';
			return;
		}

		const label = document.createElement('label');
		label.className = 'checkbox-label choice-label custom-element is-selected';
		const input = document.createElement('input');
		input.type = 'checkbox';
		input.name = 'elements_custom';
		input.value = cleanedValue;
		input.checked = true;
		const text = document.createElement('span');
		text.className = 'checkbox-text';
		text.textContent = cleanedValue;
		label.appendChild(input);
		label.appendChild(text);
		elementsGroup.appendChild(label);

		input.addEventListener('change', () => {
			updateChoiceStyles();
		});

		customElementInput.value = '';
		updateChoiceStyles();
	};

	if (addEmotionBtn && customEmotionInput && emotionsGroup) {
		addEmotionBtn.addEventListener('click', addCustomEmotion);
		customEmotionInput.addEventListener('keydown', (event) => {
			if (event.key === 'Enter') {
				event.preventDefault();
				addCustomEmotion();
			}
		});
	}

	if (addElementBtn && customElementInput && elementsGroup) {
		addElementBtn.addEventListener('click', addCustomElement);
		customElementInput.addEventListener('keydown', (event) => {
			if (event.key === 'Enter') {
				event.preventDefault();
				addCustomElement();
			}
		});
	}

	form.addEventListener('submit', async function(e) {
		e.preventDefault();

		if (!noMemoryMode) {
			if (RECORDING_MODE === 'text_only') {
				if (!dreamTextarea || !dreamTextarea.value.trim()) {
					alert('Veuillez ecrire votre reve avant de soumettre.');
					return;
				}
			} else if (!currentAudioBlob) {
				// Vérification si enregistrement est en cours mais pas arrêté
				if (mediaRecorder && mediaRecorder.state !== 'inactive') {
					alert('Vous devez arrêter l\'enregistrement avant de soumettre.');
					return;
				}
				alert('Veuillez enregistrer un audio');
				return;
			}
		}

		const formData = new FormData(form);
		const formActions = document.getElementById('formActions');

		if (!noMemoryMode && RECORDING_MODE !== 'text_only' && currentAudioBlob) {
			const mime = currentAudioBlob.type || 'audio/wav';
			const ext = mime.includes('mp4') ? 'm4a' : mime.includes('webm') ? 'webm' : 'wav';
			formData.set('audio', currentAudioBlob, `dream-recording.${ext}`);
		}

		try {
			form.style.display = 'none';
			if (formActions) {
				formActions.style.display = 'none';
			}

			successMessageWithAudio.style.display = 'none';
			successMessageNoMemory.style.display = 'none';

			const loadingMessage = document.createElement('div');
			loadingMessage.id = 'loadingMessage';
			loadingMessage.className = 'success-card';
			loadingMessage.innerHTML = `
				<div class="success-icon success-icon-loading">\u23f3</div>
				<h2 class="success-title">${noMemoryMode ? 'Validation en cours...' : 'Enregistrement en cours...'}</h2>
				<p class="success-text">Veuillez patienter un instant.</p>
			`;
			form.parentElement.appendChild(loadingMessage);

			const response = await fetch(submitUrl || form.action || window.location.href, {
				method: 'POST',
				body: formData,
				headers: {
					'X-Requested-With': 'XMLHttpRequest',
				}
			});

			const data = await response.json();

			if (data.success) {
				if (loadingMessage && loadingMessage.parentNode) {
					loadingMessage.parentNode.removeChild(loadingMessage);
				}

				setTimeout(() => {
					if (noMemoryMode) {
						showElement(successMessageNoMemory, 'block');
					} else {
						showElement(successMessageWithAudio, 'block');
					}
				}, 100);

				setTimeout(() => {
					window.location.href = redirectUrl || '/journal/';
				}, 5000);
			} else {
				if (loadingMessage && loadingMessage.parentNode) {
					loadingMessage.parentNode.removeChild(loadingMessage);
				}
				form.style.display = 'block';
				if (formActions) {
					formActions.style.display = 'grid';
				}
				alert('Erreur: ' + data.message);
			}
		} catch (error) {
			console.error('Erreur:', error);
			const loadingMsg = document.getElementById('loadingMessage');
			if (loadingMsg && loadingMsg.parentNode) {
				loadingMsg.parentNode.removeChild(loadingMsg);
			}
			form.style.display = 'block';
			if (formActions) {
				formActions.style.display = 'grid';
			}
			alert('Une erreur est survenue');
		}
	});
}
