document.addEventListener('DOMContentLoaded', function () {
	// 1) On attend que toute la page HTML soit chargée avant d'exécuter le script.
	//    Cela évite les erreurs du type "élément introuvable".
	const cards = Array.from(document.querySelectorAll('.js-dream-card'));
	const loadMoreContainer = document.getElementById('loadMoreContainer');
	const loadMoreButton = document.getElementById('loadMoreDreams');
	// Nombre de cartes à afficher à chaque étape.
	const step = 5;

	// Logs de debug (visibles dans la console du navigateur).
	// Utiles pendant le développement pour vérifier que tout est bien trouvé.
	console.log('🔍 Journal Load - Cartes trouvées:', cards.length);
	console.log('🔍 Container:', loadMoreContainer);
	console.log('🔍 Button:', loadMoreButton);

	// Sécurité : si le bouton ou son conteneur n'existe pas, on arrête ici.
	// Le "return" quitte la fonction immédiatement.
	if (!loadMoreButton || !loadMoreContainer) {
		console.log('❌ Erreur: Container ou Button manquant');
		return;
	}

	// S'il y a 5 cartes ou moins, pas besoin du bouton "Afficher plus".
	if (cards.length <= step) {
		console.log('📊 Nombre de cartes <= 5, bouton caché');
		loadMoreContainer.classList.add('is-hidden');
		return;
	}

	// S'il y a plus de 5 cartes, on affiche le bouton.
	console.log('✅ Affichage du bouton - Nombre total de cartes:', cards.length);
	loadMoreContainer.classList.remove('is-hidden');

	// Compteur du nombre de cartes actuellement visibles.
	// Au départ, on en montre 5.
	let visibleCount = step;

	// 2) On cache toutes les cartes après la 5e.
	//    index commence à 0, donc index 0..4 = 5 premières cartes visibles.
	cards.forEach((card, index) => {
		if (index >= visibleCount) {
			card.classList.add('is-hidden');
		}
	});

	// 3) Quand l'utilisateur clique sur "Afficher plus"...
	loadMoreButton.addEventListener('click', function () {
		// ...on calcule jusqu'où on doit afficher après ce clic.
		const nextVisible = visibleCount + step;

		// On prend la tranche de cartes à révéler,
		// puis on retire la classe qui les cachait.
		cards.slice(visibleCount, nextVisible).forEach((card) => {
			card.classList.remove('is-hidden');
		});

		// On met à jour le compteur de cartes visibles.
		visibleCount = nextVisible;

		// Si toutes les cartes sont maintenant affichées,
		// on masque le bouton "Afficher plus".
		if (visibleCount >= cards.length) {
			loadMoreContainer.classList.add('is-hidden');
		}
	});
});
