/**
 * Gestionnaire d'auto-complétion pour émotions et éléments dans les rêves
 * Interfacte avec les APIs d'auto-complétion du serveur
 */

class AutocompleteManager {
    constructor(emotionInputSelector, emotionButtonSelector, elementInputSelector, elementButtonSelector) {
        this.emotionInput = document.querySelector(emotionInputSelector);
        this.emotionButton = document.querySelector(emotionButtonSelector);
        this.elementInput = document.querySelector(elementInputSelector);
        this.elementButton = document.querySelector(elementButtonSelector);
        
        this.emotionSuggestions = [];
        this.elementSuggestions = [];
        
        this.emotionContainer = null;
        this.elementContainer = null;
        
        this.init();
    }
    
    init() {
        this.createContainers();
        
        if (this.emotionInput && this.emotionButton) {
            this.emotionInput.addEventListener('input', (e) => this.onEmotionInput(e));
            this.emotionInput.addEventListener('focus', (e) => this.showEmotionSuggestions(e));
            document.addEventListener('click', (e) => this.handleDocumentClick(e));
        }
        
        if (this.elementInput && this.elementButton) {
            this.elementInput.addEventListener('input', (e) => this.onElementInput(e));
            this.elementInput.addEventListener('focus', (e) => this.showElementSuggestions(e));
        }
    }
    
    createContainers() {
        // Créer le conteneur pour les émotions
        if (this.emotionInput) {
            this.emotionContainer = document.createElement('div');
            this.emotionContainer.className = 'autocomplete-suggestions autocomplete-suggestions-emotion';
            this.emotionContainer.style.cssText = `
                display: none;
                position: absolute;
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 4px;
                max-height: 200px;
                overflow-y: auto;
                z-index: 1000;
                min-width: 200px;
                top: 100%;
                left: 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            `;
            this.emotionInput.parentNode.style.position = 'relative';
            this.emotionInput.parentNode.appendChild(this.emotionContainer);
        }
        
        // Créer le conteneur pour les éléments
        if (this.elementInput) {
            this.elementContainer = document.createElement('div');
            this.elementContainer.className = 'autocomplete-suggestions autocomplete-suggestions-element';
            this.elementContainer.style.cssText = `
                display: none;
                position: absolute;
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 4px;
                max-height: 200px;
                overflow-y: auto;
                z-index: 1000;
                min-width: 200px;
                top: 100%;
                left: 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            `;
            this.elementInput.parentNode.style.position = 'relative';
            this.elementInput.parentNode.appendChild(this.elementContainer);
        }
    }
    
    async onEmotionInput(event) {
        const query = event.target.value.trim();
        if (query.length === 0) {
            this.hideSuggestionsList('emotion');
            return;
        }
        
        try {
            const response = await fetch(`/api/autocomplete/emotions/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            this.emotionSuggestions = data.suggestions || [];
            this.showSuggestionsList('emotion', this.emotionSuggestions);
        } catch (error) {
            console.error('Erreur lors de la récupération des suggestions d\'émotions:', error);
        }
    }
    
    async onElementInput(event) {
        const query = event.target.value.trim();
        if (query.length === 0) {
            this.hideSuggestionsList('element');
            return;
        }
        
        try {
            const response = await fetch(`/api/autocomplete/elements/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            this.elementSuggestions = data.suggestions || [];
            this.showSuggestionsList('element', this.elementSuggestions);
        } catch (error) {
            console.error('Erreur lors de la récupération des suggestions d\'éléments:', error);
        }
    }
    
    async showEmotionSuggestions(event) {
        const query = event.target.value.trim();
        if (query.length === 0) {
            try {
                const response = await fetch(`/api/autocomplete/emotions/?q=`);
                const data = await response.json();
                this.emotionSuggestions = data.suggestions || [];
                this.showSuggestionsList('emotion', this.emotionSuggestions.slice(0, 10));
            } catch (error) {
                console.error('Erreur:', error);
            }
        }
    }
    
    async showElementSuggestions(event) {
        const query = event.target.value.trim();
        if (query.length === 0) {
            try {
                const response = await fetch(`/api/autocomplete/elements/?q=`);
                const data = await response.json();
                this.elementSuggestions = data.suggestions || [];
                this.showSuggestionsList('element', this.elementSuggestions.slice(0, 10));
            } catch (error) {
                console.error('Erreur:', error);
            }
        }
    }
    
    showSuggestionsList(type, suggestions) {
        const container = type === 'emotion' ? this.emotionContainer : this.elementContainer;
        if (!container) return;
        
        // Limiter à 10 suggestions
        const limited = suggestions.slice(0, 10);
        container.innerHTML = '';
        
        if (limited.length === 0) {
            container.style.display = 'none';
            return;
        }
        
        limited.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'autocomplete-suggestion-item';
            item.textContent = suggestion;
            item.style.cssText = `
                padding: 10px 12px;
                cursor: pointer;
                border-bottom: 1px solid #eee;
                font-size: 14px;
                transition: background-color 0.2s;
            `;
            
            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = '#f5f5f5';
            });
            
            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = 'transparent';
            });
            
            item.addEventListener('click', () => {
                this.selectSuggestion(type, suggestion);
            });
            
            container.appendChild(item);
        });
        
        container.style.display = 'block';
    }
    
    hideSuggestionsList(type) {
        const container = type === 'emotion' ? this.emotionContainer : this.elementContainer;
        if (container) {
            container.style.display = 'none';
        }
    }
    
    selectSuggestion(type, suggestion) {
        if (type === 'emotion') {
            this.emotionInput.value = suggestion;
            this.hideSuggestionsList('emotion');
        } else if (type === 'element') {
            this.elementInput.value = suggestion;
            this.hideSuggestionsList('element');
        }
    }
    
    handleDocumentClick(event) {
        // Fermer les dropdowns si clic en dehors
        if (!event.target.closest('.custom-emotion-row') && 
            !event.target.closest('.autocomplete-suggestions')) {
            this.hideSuggestionsList('emotion');
            this.hideSuggestionsList('element');
        }
    }
}

// Initialiser l'auto-complétion quand le DOM est prêt
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initialisation de l\'auto-complétion...');
    const autocomplete = new AutocompleteManager(
        '#customEmotionInput',
        '#addEmotionBtn',
        '#customElementInput',
        '#addElementBtn'
    );
    console.log('Auto-complétion initialisée');
});
