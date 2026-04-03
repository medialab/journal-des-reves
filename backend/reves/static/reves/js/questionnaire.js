let currentSection = 1;
const totalSections = 3;
let questionnaireStarted = false;
const REQUIRED_QUESTION_MESSAGE = 'Vous avez oublié de remplir cette question.';

let startTime = null;
let sectionStartTime = null;
const sectionTimings = {};
let isSavingSection = false;  // Flag pour éviter les appels multiples

document.addEventListener('DOMContentLoaded', function() {
	setFormActionsVisibility(false);

	document.getElementById('startBtn').addEventListener('click', startQuestionnaire);

	document.getElementById('nextBtn').addEventListener('click', function(e) {
		e.preventDefault();
		saveCurrentSectionAndContinue(1);
	});
	document.getElementById('prevBtn').addEventListener('click', function(e) {
		e.preventDefault();
		changeSection(-1);
	});

	document.getElementById('questionnaireForm').addEventListener('submit', submitQuestionnaire);

	document.getElementById('id_travail_statut').addEventListener('change', updateConditionalFields);
	document.querySelectorAll('input[name="a_deja_travaille"]').forEach(radio => {
		radio.addEventListener('change', updateConditionalFields);
	});
	document.getElementById('id_profession').addEventListener('change', updateManagementFieldVisibility);

	const questionnaireModal = document.getElementById('questionnaireLoginModal');
	if (questionnaireModal) {
		const originalOpenModal = window.openLoginModal;
		window.openLoginModal = function(event) {
			questionnaireModal.style.display = 'none';
			if (originalOpenModal) originalOpenModal(event);
		};
	}

	updateConditionalFields();
	updateSocialConditionsFields();
	updateSectionTwoFields();
	updateSectionThreeFields();
	bindSocialConditionsListeners();
	addRequiredAsterisks();
	normalizeServerValidationMessages();

	const besoinSomInput = document.getElementById('id_besoin_som');
	if (besoinSomInput) {
		besoinSomInput.addEventListener('focus', function() {
			if (!this.value) {
				this.value = '00:00';
			}
		});
	}

	updateChoiceStyles();
});

function getQuestionnaireSaveUrl() {
	const form = document.getElementById('questionnaireForm');
	return form?.dataset.saveUrl || '';
}

function setFormActionsVisibility(isVisible) {
	const formActions = document.getElementById('formActions');
	if (!formActions) return;

	if (isVisible) {
		formActions.classList.remove('hidden');
		formActions.style.removeProperty('display');
		formActions.style.removeProperty('border-top');
		formActions.style.removeProperty('padding-top');
		formActions.style.removeProperty('margin-top');
		return;
	}

	formActions.classList.add('hidden');
	formActions.style.display = 'none';
	formActions.style.borderTop = 'none';
	formActions.style.paddingTop = '0';
	formActions.style.marginTop = '0';
}

function startQuestionnaire() {
	if (questionnaireStarted) return;

	questionnaireStarted = true;
	startTime = Date.now();
	sectionStartTime = Date.now();

	const intro = document.getElementById('introScreen');
	intro.classList.add('hidden');

	const questionnairePage = document.getElementById('questionnairePage');
	questionnairePage.classList.remove('questionnaire-intro-active');

	document.getElementById('stepIndicator').classList.remove('hidden');
	setFormActionsVisibility(true);

	currentSection = 1;
	showSection(currentSection);

	updateUI();
	window.scrollTo({ top: 0, behavior: 'smooth' });
}

function saveCurrentSectionAndContinue(direction) {
	console.log('=== CLICK SUR BOUTON SUIVANT ===');
	console.log('currentSection:', currentSection);
	
	// Empêcher les appels multiples simultanés
	if (isSavingSection) {
		console.warn('Sauvegarde déjà en cours');
		return;
	}

	console.log('Validation de la section:', currentSection);
	if (!validateSection(currentSection)) {
		console.warn('Validation échouée pour la section:', currentSection);
		console.warn('Vérifiez les éléments avec la classe "has-error"');
		return;
	}
	console.log('Validation réussie, procédure de sauvegarde...');

	const formData = new FormData(document.getElementById('questionnaireForm'));

	const sectionEndTime = Date.now();
	const sectionDuration = (sectionEndTime - sectionStartTime) / 1000;

	formData.append('section', currentSection);
	formData.append('section_duration', sectionDuration);

	const nextBtn = document.getElementById('nextBtn');
	const originalText = nextBtn.textContent;
	nextBtn.disabled = true;
	nextBtn.textContent = 'Enregistrement...';

	isSavingSection = true;  // Marquer comme en cours de sauvegarde

	// Sécurité : réinitialiser le flag après 10 secondes pour éviter les blocages
	const timeoutId = setTimeout(() => {
		if (isSavingSection) {
			console.warn('Timeout: réinitialisé le flag de sauvegarde après 10 secondes');
			isSavingSection = false;
			nextBtn.disabled = false;
			nextBtn.textContent = originalText;
		}
	}, 10000);

	fetch(getQuestionnaireSaveUrl(), {
		method: 'POST',
		body: formData,
		headers: {
			'X-Requested-With': 'XMLHttpRequest',
		}
	})
		.then(response => {
			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}
			return response.json();
		})
		.then(data => {
			clearTimeout(timeoutId);  // Annuler le timeout si on reçoit une réponse
			if (data.success) {
				sectionTimings[currentSection] = {
					startTime: sectionStartTime,
					endTime: sectionEndTime,
					duration: sectionDuration
				};

				nextBtn.disabled = false;
				nextBtn.textContent = originalText;

				changeSection(direction);

				sectionStartTime = Date.now();
				isSavingSection = false;  // Réinitialiser le flag
			} else {
				throw new Error(data.message || 'Erreur lors de l\'enregistrement');
			}
		})
		.catch(error => {
			clearTimeout(timeoutId);  // Annuler le timeout en cas d'erreur
			console.error('Error:', error);
			nextBtn.disabled = false;
			nextBtn.textContent = originalText;
			isSavingSection = false;  // Réinitialiser le flag en cas d'erreur
			alert('Erreur lors de l\'enregistrement. Veuillez reessayer.');
		});
}

function changeSection(direction) {
	const nextSection = currentSection + direction;

	if (nextSection < 1 || nextSection > totalSections) {
		if (nextSection > totalSections) {
			document.getElementById('questionnaireForm').submit();
		}
		return;
	}

	currentSection = nextSection;
	showSection(currentSection);

	updateUI();
	window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showSection(sectionNumber) {
	document.querySelectorAll('#questionnaireForm .form-section').forEach(section => {
		section.classList.add('hidden');
		section.classList.remove('active');
	});

	const targetSections = document.querySelectorAll(`#questionnaireForm [data-section="${sectionNumber}"]`);
	if (targetSections.length > 0) {
		targetSections.forEach(section => {
			section.classList.remove('hidden');
			section.classList.add('active');
		});

		const firstFocusable = targetSections[0].querySelector('input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])');
		if (firstFocusable) {
			firstFocusable.focus({ preventScroll: true });
		}
	}

	// Afficher le groupe des parents en section 3
	const parentsInfoGroup = document.getElementById('parents_info_group');
	if (parentsInfoGroup) {
		parentsInfoGroup.style.display = sectionNumber === 3 ? 'block' : 'none';
	}
}

function updateUI() {
    const progress = (currentSection / totalSections) * 100;
    const progressFill = document.getElementById('progressFill');
    if (progressFill) {
        progressFill.style.width = progress + '%';
    }

    document.getElementById('stepNumber').textContent = currentSection;

	const prevBtn = document.getElementById('prevBtn');
	const nextBtn = document.getElementById('nextBtn');
	const submitBtn = document.getElementById('submitBtn');

	// submit uniquement visible à la dernière section
	if (submitBtn) {
		if (currentSection === totalSections) {
			submitBtn.classList.remove('is-hidden-inline');
		} else {
			submitBtn.classList.add('is-hidden-inline');
		}
	}

	// boutons prev/next : gestion via classe CSS au lieu de forcer le style inline
	if (prevBtn) {
		if (currentSection === 1) {
			prevBtn.classList.add('is-hidden-inline');
		} else {
			prevBtn.classList.remove('is-hidden-inline');
		}
	}
	if (nextBtn) {
		if (currentSection === totalSections) {
			nextBtn.classList.add('is-hidden-inline');
		} else {
			nextBtn.classList.remove('is-hidden-inline');
		}
	}

	// si on est sur la première section, appliquer une classe pour aligner
	// le bouton "Suivant" à droite et ajouter un contour blanc
	const formActions = document.getElementById('formActions');
	if (formActions) {
		if (currentSection === 1) {
			formActions.classList.add('first-page');
		} else {
			formActions.classList.remove('first-page');
		}
	}
}


function validateSection(sectionNumber) {
	console.log('=== VALIDATION DE LA SECTION', sectionNumber, '===');
	
	// Nettoyer les messages d'erreur précédents
	document.querySelectorAll('.field-error-message').forEach(msg => msg.remove());
	document.querySelectorAll('.form-group, .detresse-row').forEach(group => {
		group.classList.remove('has-error');
	});

	const sections = document.querySelectorAll(`#questionnaireForm [data-section="${sectionNumber}"]`);
	console.log('Nombre de sections trouvées:', sections.length);
	if (sections.length === 0) {
		console.log('Aucune section trouvée pour:', sectionNumber);
		return true;
	}

	const errors = new Set();
	let firstErrorElement = null;

	const addError = (element) => {
		if (!element) return;
		errors.add(element);
		if (!firstErrorElement) firstErrorElement = element;
	};

	// Vérifier tous les form-group visibles dans la section
	sections.forEach(section => {
		// ===== Vérifier les .form-group =====
		const formGroups = section.querySelectorAll('.form-group:not(.composition-logement-group)');
		console.log('Form groups dans cette section:', formGroups.length);
		
		formGroups.forEach((group, idx) => {
			// Les champs conditionnels (is-hidden-inline) NE SONT JAMAIS validés
			if (group.classList.contains('is-hidden-inline')) {
				console.log('  ❌ Groupe', idx, 'est is-hidden-inline (ignoré)');
				return;
			}

			// Vérifier si UN PARENT a is-hidden-inline (group conditionnel caché)
			if (group.closest('.is-hidden-inline')) {
				console.log('  ❌ Groupe', idx, 'a un parent is-hidden-inline (ignoré)');
				return;
			}

			// Sauter les groupes masqués (display: none)
			if (group.style.display === 'none') {
				console.log('  ❌ Groupe', idx, 'a display: none (ignoré)');
				return;
			}

			console.log('  ✓ Vérification du groupe', idx);

			// Chercher les inputs
			const radios = group.querySelectorAll('input[type="radio"]');
			const checkboxes = group.querySelectorAll('input[type="checkbox"]:not([disabled])');
			const textInputs = group.querySelectorAll('input[type="text"], input[type="time"], input[type="number"]');
			const selects = group.querySelectorAll('select');
			const textareas = group.querySelectorAll('textarea');

			// Vérifier les radios - OBLIGATOIRE
			if (radios.length > 0) {
				const isChecked = Array.from(radios).some(r => r.checked);
				console.log('    Radios:', radios.length, '| Coché:', isChecked ? 'OUI' : 'NON ❌');
				if (!isChecked) {
					addError(group);
				}
				return;
			}

			// Vérifier les checkboxes - OBLIGATOIRE
			if (checkboxes.length > 0) {
				const isChecked = Array.from(checkboxes).some(cb => cb.checked);
				console.log('    Checkboxes:', checkboxes.length, '| Coché:', isChecked ? 'OUI' : 'NON ❌');
				if (!isChecked) {
					addError(group);
				}
				return;
			}

			// Vérifier les selects - OBLIGATOIRE
			if (selects.length > 0) {
				const select = selects[0];
				const hasValue = select.value && select.value !== '';
				console.log('    Select:', select.name, '| Valeur:', select.value, '| Rempli:', hasValue ? 'OUI' : 'NON ❌');
				if (!hasValue) {
					addError(group);
				}
				return;
			}

			// Vérifier les inputs texte/time/number - OBLIGATOIRE
			if (textInputs.length > 0) {
				const input = textInputs[0];
				const hasValue = input.value && input.value.trim() !== '';
				console.log('    Input text:', input.name, input.type, '| Valeur:', input.value, '| Rempli:', hasValue ? 'OUI' : 'NON ❌');
				if (!hasValue) {
					addError(group);
				}
				return;
			}

			// Vérifier les textareas - OBLIGATOIRE
			if (textareas.length > 0) {
				const textarea = textareas[0];
				const hasValue = textarea.value && textarea.value.trim() !== '';
				console.log('    Textarea:', textarea.name, '| Rempli:', hasValue ? 'OUI' : 'NON ❌');
				if (!hasValue) {
					addError(group);
				}
			}
		});

		// ===== Vérifier le groupe composition_logement spécial (checkboxes) =====
		const compositionGroup = section.querySelector('.composition-logement-group');
		if (compositionGroup && compositionGroup.style.display !== 'none') {
			const checkboxes = compositionGroup.querySelectorAll('input[type="checkbox"]');
			const isChecked = Array.from(checkboxes).some(cb => cb.checked);
			console.log('  ✓ Composition logement:', checkboxes.length, 'checkboxes | Coché:', isChecked ? 'OUI' : 'NON ❌');
			if (!isChecked) {
				addError(compositionGroup);
			}
		}

		// ===== Vérifier les .detresse-row (pour les questions de détresse) =====
		const detresseRows = section.querySelectorAll('.detresse-row');
		console.log('  ✓ Detresse rows:', detresseRows.length);
		detresseRows.forEach((row, idx) => {
			// Vérifier si la row est visible (parent detresse-card visible)
			const detresseCard = row.closest('.detresse-card');
			if (detresseCard && (detresseCard.style.display === 'none')) {
				return;
			}

			const radios = row.querySelectorAll('input[type="radio"]');
			const isChecked = Array.from(radios).some(r => r.checked);
			console.log('    Detresse row', idx, '| Radios:', radios.length, '| Coché:', isChecked ? 'OUI' : 'NON ❌');
			if (radios.length > 0) {
				if (!isChecked) {
					addError(row);
				}
			}
		});
	});

	// Afficher les messages d'erreur
	if (errors.size > 0) {
		console.log('❌ ERREURS DE VALIDATION:', errors.size, 'champ(s) vide(s)');
		errors.forEach(element => {
			element.classList.add('has-error');
			const errorMsg = document.createElement('div');
			errorMsg.className = 'field-error-message';
			errorMsg.textContent = '⚠ ' + REQUIRED_QUESTION_MESSAGE;
			element.appendChild(errorMsg);
		});

		// Scroller vers le premier champ en erreur
		if (firstErrorElement) {
			firstErrorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
		}

		return false;
	}

	console.log('Section', sectionNumber, 'validée avec succès');
	return true;
}

function normalizeServerValidationMessages() {
	document.querySelectorAll('#questionnaireForm .error-message').forEach(errorNode => {
		errorNode.textContent = REQUIRED_QUESTION_MESSAGE;
	});
}

function addRequiredAsterisks() {
	const labels = document.querySelectorAll(
		'#questionnaireForm .form-group > .form-label, #questionnaireForm .detresse-row > .detresse-question'
	);

	labels.forEach(labelNode => {
		if (labelNode.querySelector('.required-asterisk')) return;
		if (labelNode.textContent.includes('*')) return;

		const marker = document.createElement('span');
		marker.className = 'required-asterisk';
		marker.setAttribute('aria-hidden', 'true');
		marker.textContent = ' *';
		labelNode.appendChild(marker);
	});
}

function submitQuestionnaire(_e) {
	const questEnd = Date.now();
	const totalDuration = (questEnd - startTime) / 1000;

	console.log('Questionnaire completed in', totalDuration, 'seconds');
	console.log('Section timings:', sectionTimings);
}

function submitAfterValidation() {
	console.log('Validation et soumission de la section:', currentSection);
	if (!validateSection(currentSection)) {
		console.warn('Validation échouée pour la section:', currentSection);
		return;
	}
	console.log('Validation réussie, soumission du formulaire...');
	document.getElementById('questionnaireForm').submit();
}

function updateConditionalFields() {
	const status = document.getElementById('id_travail_statut').value;
	const adejaTravauilleGroup = document.getElementById('a_deja_travaille_group');
	const professionGroup = document.getElementById('profession_group');
	const fonctionManagementGroup = document.getElementById('fonction_management_group');

	if (status === '2' || status === '3' || status === '4' || status === '5' || status === '6' || status === '7') {
		adejaTravauilleGroup.style.display = 'block';
	} else {
		adejaTravauilleGroup.style.display = 'none';
		document.querySelectorAll('input[name="a_deja_travaille"]').forEach(radio => {
			radio.checked = false;
		});
	}

	const adejaTravailled = document.querySelector('input[name="a_deja_travaille"]:checked');
	const showProfession = status === '1' || (adejaTravailled && adejaTravailled.value === 'True');
	professionGroup.style.display = showProfession ? 'block' : 'none';

	const profession = document.getElementById('id_profession').value.trim();
	fonctionManagementGroup.style.display = showProfession && profession ? 'block' : 'none';
}

function updateManagementFieldVisibility() {
	const profession = document.getElementById('id_profession').value.trim();
	const status = document.getElementById('id_travail_statut').value;
	const adejaTravailled = document.querySelector('input[name="a_deja_travaille"]:checked');
	const showProfession = status === '1' || (adejaTravailled && adejaTravailled.value === 'True');
	const fonctionManagementGroup = document.getElementById('fonction_management_group');
	fonctionManagementGroup.style.display = showProfession && profession ? 'block' : 'none';
}

function bindSocialConditionsListeners() {
	const modImg = document.getElementById('id_mod_img');
	if (modImg) {
		modImg.addEventListener('change', updateSocialConditionsFields);
	}

	document.querySelectorAll('input[name="reveil_nuit"]').forEach(radio => {
		radio.addEventListener('change', updateSocialConditionsFields);
	});

	document.querySelectorAll('input[name="aide_sommeil"]').forEach(radio => {
		radio.addEventListener('change', updateSocialConditionsFields);
	});

	const pensRien = document.getElementById('id_pens_rien');
	if (pensRien) {
		pensRien.addEventListener('change', function() {
			toggleExclusiveGroup('id_pens_rien', '.pens-option');
			updateSocialConditionsFields();
		});
	}

	const contRien = document.getElementById('id_cont_rien');
	if (contRien) {
		contRien.addEventListener('change', function() {
			toggleExclusiveGroup('id_cont_rien', '.cont-option');
		});
	}

	document.querySelectorAll('.pens-option').forEach(input => {
		input.addEventListener('change', function() {
			const pensRienCheckbox = document.getElementById('id_pens_rien');
			if (pensRienCheckbox && this.checked) {
				pensRienCheckbox.checked = false;
				pensRienCheckbox.disabled = false;
			}
			updateSocialConditionsFields();
		});
	});

	document.querySelectorAll('.cont-option').forEach(input => {
		input.addEventListener('change', function() {
			const contRienCheckbox = document.getElementById('id_cont_rien');
			if (contRienCheckbox && this.checked) {
				contRienCheckbox.checked = false;
				contRienCheckbox.disabled = false;
			}
		});
	});

	const pensAutre = document.getElementById('id_pens_autre');
	if (pensAutre) {
		pensAutre.addEventListener('change', updateSocialConditionsFields);
	}

	const compositionEnfants = document.getElementById('id_composition_logement_enfants');
	if (compositionEnfants) {
		compositionEnfants.addEventListener('change', updateSectionTwoFields);
	}

	const compositionConjoint = document.querySelector('input[name="composition_logement_conjoint"]');
	if (compositionConjoint) {
		compositionConjoint.addEventListener('change', updateSectionTwoFields);
	}

	document.querySelectorAll('input[name="statut_couple"]').forEach(radio => {
		radio.addEventListener('change', updateSectionTwoFields);
	});

	document.querySelectorAll('input[name="discri_presence"]').forEach(radio => {
		radio.addEventListener('change', updateSectionThreeFields);
	});

	const discriAutre = document.getElementById('id_discri_autre');
	if (discriAutre) {
		discriAutre.addEventListener('change', updateSectionThreeFields);
	}
}

function updateSectionTwoFields() {
	const compositionEnfants = document.getElementById('id_composition_logement_enfants');
	const enfantsGroup = document.getElementById('composition_enfants_group');
	if (!compositionEnfants || !enfantsGroup) {
		return;
	}

	const shouldShow = compositionEnfants.checked;
	enfantsGroup.style.display = shouldShow ? 'block' : 'none';

	if (!shouldShow) {
		const nbEnfants = document.getElementById('id_nb_enfants_cohabitants');
		const nbMoins14 = document.getElementById('id_nb_enfants_moins14');
		if (nbEnfants) nbEnfants.value = '';
		if (nbMoins14) nbMoins14.value = '';
	}

	const conjointGroup = document.getElementById('conjoint_mobilite_group');
	const compositionConjoint = document.querySelector('input[name="composition_logement_conjoint"]');
	if (conjointGroup && compositionConjoint) {
		const showConjoint = compositionConjoint.checked;
		conjointGroup.style.display = showConjoint ? 'block' : 'none';

		if (!showConjoint) {
			const conjNivDiplome = document.getElementById('id_conj_niv_diplome');
			const conjCsp = document.getElementById('id_conj_csp');
			if (conjNivDiplome) conjNivDiplome.value = '';
			if (conjCsp) conjCsp.value = '';
		}
	}
}

function updateSocialConditionsFields() {
	toggleExclusiveGroup('id_pens_rien', '.pens-option');
	toggleExclusiveGroup('id_cont_rien', '.cont-option');

	const modImg = document.getElementById('id_mod_img');
	const imagesGroup = document.getElementById('images_options_group');
	if (modImg && imagesGroup) {
		imagesGroup.style.display = modImg.checked ? 'block' : 'none';
		if (!modImg.checked) {
			['img_coul', 'img_nb', 'img_net', 'img_flou', 'img_ns'].forEach(name => {
				const el = document.querySelector(`input[name="${name}"]`);
				if (el) el.checked = false;
			});
		}
	}

	const reveilYes = document.querySelector('input[name="reveil_nuit"][value="True"]');
	const reveilDetails = document.getElementById('reveil_nuit_details');
	if (reveilDetails && reveilYes) {
		const shouldShow = reveilYes.checked;
		reveilDetails.style.display = shouldShow ? 'block' : 'none';
		if (!shouldShow) {
			const nuits = document.getElementById('id_nuits_reveil');
			const duree = document.getElementById('id_duree_eveil');
			if (nuits) nuits.value = '';
			if (duree) duree.value = '';
		}
	}

	const aideYes = document.querySelector('input[name="aide_sommeil"][value="True"]');
	const aideGroup = document.getElementById('aide_sommeil_options');
	if (aideGroup && aideYes) {
		const shouldShow = aideYes.checked;
		aideGroup.style.display = shouldShow ? 'block' : 'none';
		if (!shouldShow) {
			['aide_medic', 'aide_tisane', 'aide_autre'].forEach(name => {
				const el = document.querySelector(`input[name="${name}"]`);
				if (el) el.checked = false;
			});
		}
	}

	const pensAutre = document.getElementById('id_pens_autre');
	const pensAutreTxtGroup = document.getElementById('pens_autre_txt_group');
	if (pensAutre && pensAutreTxtGroup) {
		pensAutreTxtGroup.style.display = pensAutre.checked ? 'block' : 'none';
		if (!pensAutre.checked) {
			const txt = document.getElementById('id_pens_autre_txt');
			if (txt) txt.value = '';
		}
	}
}

function updateSectionThreeFields() {
	const discriDetailsGroup = document.getElementById('discri_details_group');
	const discriAutre = document.getElementById('id_discri_autre');
	const discriAutrePrecisionGroup = document.getElementById('discri_autre_precision_group');
	const discriAutrePrecision = document.getElementById('id_discri_autre_precision');

	const discriPresence = document.querySelector('input[name="discri_presence"]:checked');
	const showDiscriDetails = discriPresence && (discriPresence.value === '1' || discriPresence.value === '2');

	if (discriDetailsGroup) {
		discriDetailsGroup.style.display = showDiscriDetails ? 'block' : 'none';
	}

	if (!showDiscriDetails) {
		document.querySelectorAll('.discri-reason, .discri-context').forEach(input => {
			input.checked = false;
		});
		if (discriAutrePrecision) {
			discriAutrePrecision.value = '';
		}
	}

	const showAutrePrecision = showDiscriDetails && discriAutre && discriAutre.checked;
	if (discriAutrePrecisionGroup) {
		discriAutrePrecisionGroup.style.display = showAutrePrecision ? 'block' : 'none';
	}
	if (!showAutrePrecision && discriAutrePrecision) {
		discriAutrePrecision.value = '';
	}
}

function toggleExclusiveGroup(masterCheckboxId, optionsSelector) {
	const master = document.getElementById(masterCheckboxId);
	if (!master) return;

	const options = document.querySelectorAll(optionsSelector);
	if (master.checked) {
		options.forEach(input => {
			input.checked = false;
			input.disabled = true;
		});
	} else {
		options.forEach(input => {
			input.disabled = false;
		});
	}
}

function updateChoiceStyles() {
	const form = document.getElementById('questionnaireForm');
	if (!form) return;

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
			if (!label || !label.classList.contains('choice-label')) {
				return;
			}
			label.classList.toggle('is-selected', input.checked);
			label.classList.toggle('is-dim', anyChecked && !input.checked);
		});
	});
}

document.addEventListener('change', function(event) {
	const target = event.target;
	if (target.matches('#questionnaireForm input[type="radio"], #questionnaireForm input[type="checkbox"]')) {
		updateChoiceStyles();
	}
});
