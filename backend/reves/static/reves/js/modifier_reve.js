document.addEventListener('DOMContentLoaded', function() {
	initFormHandlers();
});

function initFormHandlers() {
	const form = document.getElementById('reve-form');
	const submitBtn = document.getElementById('submitBtn');
	const successMessage = document.getElementById('successMessage');
	const emotionsGroup = document.getElementById('emotionsGroup');
	const addEmotionBtn = document.getElementById('addEmotionBtn');
	const customEmotionInput = document.getElementById('customEmotionInput');
	const elementsGroup = document.getElementById('elementsGroup');
	const addElementBtn = document.getElementById('addElementBtn');
	const customElementInput = document.getElementById('customElementInput');

	if (!form) {
		return;
	}

	const submitUrl = form.dataset.submitUrl;
	const redirectUrl = form.dataset.redirectUrl;

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
			updateChoiceStyles();
		});
	});

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
		if (!customEmotionInput || !emotionsGroup) {
			return;
		}

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
		label.className = 'checkbox-label choice-label custom-emotion is-selected';
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

		const formData = new FormData(form);
		const formActions = document.getElementById('formActions');

		try {
			form.style.display = 'none';
			if (formActions) {
				formActions.style.display = 'none';
			}

			const loadingMessage = document.createElement('div');
			loadingMessage.id = 'loadingMessage';
			loadingMessage.className = 'success-card';
			loadingMessage.innerHTML = `
				<div class="success-icon success-icon-loading">\u23f3</div>
				<h2 class="success-title">Enregistrement en cours...</h2>
				<p class="success-text">Veuillez patienter un instant.</p>
			`;
			form.parentElement.appendChild(loadingMessage);

			const response = await fetch(submitUrl, {
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
					successMessage.style.display = 'block';
				}, 100);

				setTimeout(() => {
					window.location.href = redirectUrl;
				}, 3000);
			} else {
				if (loadingMessage && loadingMessage.parentNode) {
					loadingMessage.parentNode.removeChild(loadingMessage);
				}
				form.style.display = 'block';
				if (formActions) {
					formActions.style.display = 'flex';
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
				formActions.style.display = 'flex';
			}
			alert('Une erreur est survenue');
		}
	});

	updateChoiceStyles();
}
