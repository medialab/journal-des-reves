/**
 * Notifications System
 * Gère l'affichage des notifications en temps réel et les modales
 */

class NotificationManager {
    constructor() {
        this.container = null;
        this.modalOverlay = null;
        this.panelOverlay = null;
        this.panel = null;
        this.notifications = [];
        this.isAdmin = false;  // Statut admin, défini par le template
        this.init();
    }

    init() {
        // Créer le container des notifications
        if (!document.getElementById('notifications-container')) {
            this.container = document.createElement('div');
            this.container.id = 'notifications-container';
            this.container.className = 'notifications-container';
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('notifications-container');
        }

        // Créer l'overlay modal
        if (!document.getElementById('modal-overlay')) {
            this.modalOverlay = document.createElement('div');
            this.modalOverlay.id = 'modal-overlay';
            this.modalOverlay.className = 'modal-overlay';
            document.body.appendChild(this.modalOverlay);
        } else {
            this.modalOverlay = document.getElementById('modal-overlay');
        }
        
        // Créer l'overlay pour le panel
        if (!document.getElementById('notifications-panel-overlay')) {
            this.panelOverlay = document.createElement('div');
            this.panelOverlay.id = 'notifications-panel-overlay';
            this.panelOverlay.className = 'notifications-panel-overlay';
            document.body.appendChild(this.panelOverlay);
            this.panelOverlay.addEventListener('click', () => this.closePanel());
        } else {
            this.panelOverlay = document.getElementById('notifications-panel-overlay');
        }
        
        // Créer le panel
        if (!document.getElementById('notifications-panel')) {
            this.panel = document.createElement('div');
            this.panel.id = 'notifications-panel';
            this.panel.className = 'notifications-panel';
            document.body.appendChild(this.panel);
        } else {
            this.panel = document.getElementById('notifications-panel');
        }

        // Charger les styles si pas déjà présent
        this.ensureStylesheet();
        
        // Attacher l'événement à la cloche
        this.attachBellListener();
    }
    
    attachBellListener() {
        // Attendre que le DOM soit prêt
        const attachListener = () => {
            const bell = document.querySelector('.nav-menu .notification-bell, li.notification-bell');
            if (bell) {
                bell.style.cursor = 'pointer';
                bell.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.togglePanel();
                });
            } else {
                // Réessayer après un court délai
                setTimeout(attachListener, 100);
            }
        };
        attachListener();
    }
    
    togglePanel() {
        if (this.panel.classList.contains('active')) {
            this.closePanel();
        } else {
            this.openPanel();
        }
    }
    
    openPanel() {
        this.panel.classList.add('active');
        this.panelOverlay.classList.add('active');
        this.renderPanelNotifications();
    }
    
    closePanel() {
        this.panel.classList.remove('active');
        this.panelOverlay.classList.remove('active');
    }
    
    renderPanelNotifications() {
        const content = this.panel.querySelector('.notifications-panel-content');
        if (content) {
            content.remove();
        }
        
        let panelHTML = `
            <div class="notifications-panel-header">
                <h3 class="notifications-panel-title">Notifications</h3>
                <button class="notifications-panel-close" onclick="notificationManager.closePanel()">&times;</button>
            </div>
            <div class="notifications-panel-content">
        `;
        
        if (this.notifications.length === 0) {
            panelHTML += `<div class="notifications-panel-empty">Aucune notification</div>`;
        } else {
            panelHTML += this.notifications.map(notif => `
                <div class="notification-item-panel ${notif.is_read ? '' : 'unread'}">
                    <div class="notification-item-panel-content">
                        <div class="notification-item-panel-type">${this.getNotificationType(notif.type)}</div>
                        <div class="notification-item-panel-title">${this.escapeHtml(notif.title)}</div>
                        <div class="notification-item-panel-message">${this.escapeHtml(notif.message)}</div>
                        <div class="notification-item-panel-time">${this.formatDateFull(new Date(notif.created_at))}</div>
                    </div>
                    <button class="notification-item-panel-delete" onclick="notificationManager.deleteNotification(${notif.id})">×</button>
                </div>
            `).join('');
        }
        
        panelHTML += `
            </div>
            <div class="notifications-panel-footer">
                ${this.isAdmin ? '<a href="/admin/polls/notification/" class="notifications-panel-footer-link">Gérer les notifications</a>' : ''}
            </div>
        `;
        
        this.panel.innerHTML = panelHTML;
        
        // Re-attach close button
        const closeBtn = this.panel.querySelector('.notifications-panel-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closePanel());
        }
    }
    
    getNotificationType(type) {
        const types = {
            'daily_reminder': '🌙 Rappel quotidien',
            'questionnaire_reminder': '📋 Questionnaire',
            'general': 'ℹ️ Information'
        };
        return types[type] || type;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    formatDateFull(date) {
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);
        
        if (diff < 60) return 'À l\'instant';
        if (diff < 3600) return `Il y a ${Math.floor(diff / 60)}m`;
        if (diff < 86400) return `Il y a ${Math.floor(diff / 3600)}h`;
        
        const days = Math.floor(diff / 86400);
        if (days === 1) return 'Hier';
        if (days < 7) return `Il y a ${days} jours`;
        
        return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    }
    
    async deleteNotification(notificationId) {
        try {
            const response = await fetch(`/polls/api/notifications/${notificationId}/delete/`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            if (response.ok) {
                // Retirer de la liste locale
                this.notifications = this.notifications.filter(n => n.id !== notificationId);
                // Re-render le panel
                this.renderPanelNotifications();
                // Mettre à jour le badge
                await this.updateUnreadCount();
            }
        } catch (error) {
            console.error('Erreur suppression notification:', error);
        }
    }

    ensureStylesheet() {
        if (!document.querySelector('link[href*="notifications.css"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = '/static/polls/notifications.css';
            document.head.appendChild(link);
        }
    }

    getDismissedNotificationIds() {
        try {
            const raw = localStorage.getItem('dismissed_notifications');
            const parsed = raw ? JSON.parse(raw) : [];
            return Array.isArray(parsed) ? parsed : [];
        } catch (error) {
            return [];
        }
    }

    saveDismissedNotificationId(notificationId) {
        if (!notificationId) return;
        const ids = this.getDismissedNotificationIds();
        if (!ids.includes(notificationId)) {
            ids.push(notificationId);
            localStorage.setItem('dismissed_notifications', JSON.stringify(ids));
        }
    }

    /**
     * Afficher une notification
     */
    showNotification(title, message, type = 'general', duration = 5000, notificationId = null) {
        const notification = document.createElement('div');
        notification.className = `notification-item ${type === 'questionnaire' ? 'questionnaire' : 'daily'} unread`;
        if (notificationId !== null && notificationId !== undefined) {
            notification.dataset.notificationId = String(notificationId);
        }
        
        const typeDisplay = type === 'questionnaire' ? '📋' : '🌙';
        
        notification.innerHTML = `
            <button class="notification-close">&times;</button>
            <div class="notification-title">${typeDisplay} ${title}</div>
            <div class="notification-message">${message}</div>
            <div class="notification-time">${this.formatTime(new Date())}</div>
        `;

        const closeBtn = notification.querySelector('.notification-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', (event) => {
                event.stopPropagation();
                this.saveDismissedNotificationId(notificationId);
                notification.remove();
            });
        }
        
        notification.onclick = (e) => {
            if (e.target.className !== 'notification-close') {
                notification.classList.remove('unread');
            }
        };
        
        this.container.appendChild(notification);
        
        // Auto-remove après duration
        if (duration > 0) {
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => notification.remove(), 300);
            }, duration);
        }
    }

    /**
     * Charger et afficher les notifications depuis l'API
     */
    async loadNotifications() {
        try {
            const response = await fetch('/polls/api/notifications/', {
                credentials: 'include'
            });
            
            if (!response.ok) return;
            
            const data = await response.json();
            if (data.success) {
                this.notifications = data.notifications;
                this.updateNotificationsBadge(data.unread_count);
                
                // Afficher les notifications non lues
                const dismissedIds = this.getDismissedNotificationIds();
                const unreadNotifications = data.notifications.filter(n => !n.is_read);
                unreadNotifications.forEach(notif => {
                    if (dismissedIds.includes(notif.id)) {
                        return;
                    }
                    if (!document.querySelector(`[data-notification-id="${notif.id}"]`)) {
                        this.showNotification(
                            notif.title,
                            notif.message,
                            notif.type.includes('questionnaire') ? 'questionnaire' : 'daily',
                            5000,
                            notif.id
                        );
                    }
                });
            }
        } catch (error) {
            console.error('Erreur chargement notifications:', error);
        }
    }

    /**
     * Marquer une notification comme lue
     */
    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/polls/api/notifications/${notificationId}/read/`, {
                method: 'POST',
                credentials: 'include'
            });
            
            if (response.ok) {
                // Mettre à jour le badge
                await this.updateUnreadCount();
            }
        } catch (error) {
            console.error('Erreur marquage notification:', error);
        }
    }

    /**
     * Mettre à jour le nombre de notifications non lues
     */
    async updateUnreadCount() {
        try {
            const response = await fetch('/polls/api/notifications/unread-count/', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateNotificationsBadge(data.unread_count);
            }
        } catch (error) {
            console.error('Erreur mise à jour count:', error);
        }
    }

    /**
     * Mettre à jour le badge du nombre de notifications
     */
    updateNotificationsBadge(count) {
        let badge = document.querySelector('.notification-badge');
        if (count > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'notification-badge';
                const bell = document.querySelector('.notification-bell');
                if (bell) bell.appendChild(badge);
            }
            badge.textContent = count > 9 ? '9+' : count;
        } else if (badge) {
            badge.remove();
        }
    }

    /**
     * Formater l'heure d'une notification
     */
    formatTime(date) {
        const now = new Date();
        const diff = Math.floor((now - date) / 1000); // secondes
        
        if (diff < 60) return 'À l\'instant';
        if (diff < 3600) return `Il y a ${Math.floor(diff / 60)}m`;
        if (diff < 86400) return `Il y a ${Math.floor(diff / 3600)}h`;
        
        return `Il y a ${Math.floor(diff / 86400)}j`;
    }

    /**
     * Afficher une modal
     */
    showModal(title, message, icon = '📋', options = {}) {
        const content = document.createElement('div');
        content.className = 'modal-content';
        content.innerHTML = `
            <button class="modal-close" onclick="document.getElementById('modal-overlay').classList.remove('active')">&times;</button>
            <div class="modal-header">
                <div class="modal-icon">${icon}</div>
                <h2 class="modal-title">${title}</h2>
                ${options.subtitle ? `<p class="modal-subtitle">${options.subtitle}</p>` : ''}
            </div>
            <div class="modal-body">
                ${options.progressInfo ? `<div class="progress-info">${options.progressInfo}</div>` : ''}
                <p class="modal-body-text">${message}</p>
            </div>
            <div class="modal-footer">
                ${options.buttons ? options.buttons.map(btn => `
                    <button class="modal-btn modal-btn-${btn.type || 'secondary'}" onclick="${btn.onclick}">
                        ${btn.label}
                    </button>
                `).join('') : `
                    <button class="modal-btn modal-btn-secondary" onclick="document.getElementById('modal-overlay').classList.remove('active')">
                        Fermer
                    </button>
                    <button class="modal-btn modal-btn-primary" onclick="${options.primaryAction || "document.getElementById('modal-overlay').classList.remove('active')"}">
                        ${options.primaryLabel || 'OK'}
                    </button>
                `}
            </div>
        `;
        
        this.modalOverlay.innerHTML = '';
        this.modalOverlay.appendChild(content);
        this.modalOverlay.classList.add('active');
        
        // Fermer au clic sur l'overlay
        this.modalOverlay.addEventListener('click', (e) => {
            if (e.target === this.modalOverlay) {
                this.modalOverlay.classList.remove('active');
            }
        });
    }

    /**
     * Afficher la modal de questionnaire (après 7 jours)
     */
    showQuestionnaireModal(daysEllapsed) {
        this.showModal(
            'Complétez votre profil !',
            'Cela nous aide à mieux comprendre votre contexte et d\'animer l\'étude. Cela ne prendra que 10-15 minutes.',
            '📋',
            {
                subtitle: 'Vous êtes inscrit depuis une semaine maintenant.',
                progressInfo: `Profil ${daysEllapsed === 7 ? 'complet' : 'en cours'} - Remplissage ${Math.min(100, Math.round((daysEllapsed / 7) * 100))}%`,
                primaryLabel: 'Remplir le questionnaire',
                primaryAction: `window.location.href = '/polls/questionnaire/'; document.getElementById('modal-overlay').classList.remove('active');`,
                buttons: [
                    {
                        label: 'Plus tard',
                        type: 'secondary',
                        onclick: "document.getElementById('modal-overlay').classList.remove('active'); localStorage.setItem('questionnaire_modal_dismissed', '1');"
                    },
                    {
                        label: 'Remplir maintenant',
                        type: 'primary',
                        onclick: "window.location.href = '/polls/questionnaire/';"
                    }
                ]
            }
        );
    }
}

// Initialiser le gestionnaire de notifications
const notificationManager = new NotificationManager();

// Charger les notifications au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    notificationManager.loadNotifications();
    
    // Recharger les notifications toutes les 30 secondes
    setInterval(() => {
        notificationManager.loadNotifications();
    }, 30000);
});

// Export pour utilisation globale
window.notificationManager = notificationManager;
