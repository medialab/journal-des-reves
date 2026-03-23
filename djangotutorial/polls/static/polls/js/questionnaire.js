let currentSection = 1;
const totalSections = 3;
let questionnaireStarted = false;

let startTime = null;
let sectionStartTime = null;
const sectionTimings = {};

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
	if (!validateSection(currentSection)) {
		return;
	}

	const formData = new FormData(document.getElementById('questionnaireForm'));

	const sectionEndTime = Date.now();
	const sectionDuration = (sectionEndTime - sectionStartTime) / 1000;

	formData.append('section', currentSection);
	formData.append('section_duration', sectionDuration);

	const nextBtn = document.getElementById('nextBtn');
	const originalText = nextBtn.textContent;
	nextBtn.disabled = true;
	nextBtn.textContent = 'Enregistrement...';

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
			} else {
				throw new Error(data.message || 'Erreur lors de l\'enregistrement');
			}
		})
		.catch(error => {
			console.error('Error:', error);
			nextBtn.disabled = false;
			nextBtn.textContent = originalText;
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

	prevBtn.style.display = currentSection === 1 ? 'none' : 'inline-flex';
	nextBtn.style.display = currentSection === totalSections ? 'none' : 'inline-flex';
	submitBtn.style.display = currentSection === totalSections ? 'inline-flex' : 'none';
}

function validateSection(_section) {
	return true;
}

function submitQuestionnaire(_e) {
	const questEnd = Date.now();
	const totalDuration = (questEnd - startTime) / 1000;

	console.log('Questionnaire completed in', totalDuration, 'seconds');
	console.log('Section timings:', sectionTimings);
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
