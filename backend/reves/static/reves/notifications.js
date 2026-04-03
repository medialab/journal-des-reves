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
                <button type="button" class="notifications-panel-close" onclick="notificationManager.closePanel()">&times;</button>
            </div>
            <div class="notifications-panel-content">
        `;
        
        if (this.notifications.length === 0) {
            panelHTML += `
                <div class="notifications-panel-empty">
                    <div class="notifications-panel-empty-icon">✓</div>
                    <div class="notifications-panel-empty-title">Vous etes a jour</div>
                    <div class="notifications-panel-empty-text">Aucune notification en attente pour le moment.</div>
                </div>
            `;
        } else {
            panelHTML += this.notifications.map(notif => {
                const meta = this.getNotificationMeta(notif.type);
                return `
                    <div class="notification-item-panel ${notif.is_read ? '' : 'unread'} tone-${meta.tone}">
                        <div class="notification-item-panel-icon" aria-hidden="true">${meta.icon}</div>
                        <div class="notification-item-panel-content">
                            <div class="notification-item-panel-meta">
                                <div class="notification-item-panel-type">${meta.label}</div>
                                <div class="notification-item-panel-time">${this.formatDateFull(new Date(notif.created_at))}</div>
                            </div>
                            <div class="notification-item-panel-title">${this.escapeHtml(notif.title)}</div>
                            <div class="notification-item-panel-message">${this.escapeHtml(notif.message)}</div>
                        </div>
                        <button type="button" class="notification-item-panel-delete" onclick="notificationManager.deleteNotification(${notif.id})" aria-label="Supprimer la notification">×</button>
                    </div>
                `;
            }).join('');
        }
        
        panelHTML += `
            </div>
            <div class="notifications-panel-footer">
                ${this.isAdmin ? '<a href="/admin/reves/notification/" class="notifications-panel-footer-link">Gérer les notifications</a>' : ''}
            </div>
        `;
        
        this.panel.innerHTML = panelHTML;
        
        // Re-attach close button
        const closeBtn = this.panel.querySelector('.notifications-panel-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closePanel());
        }
    }
    
    normalizeNotificationType(type) {
        if (!type) return 'general';
        if (type.includes('questionnaire')) return 'questionnaire_reminder';
        if (type.includes('daily')) return 'daily_reminder';
        return 'general';
    }

    getNotificationMeta(type) {
        const normalizedType = this.normalizeNotificationType(type);
        const types = {
            daily_reminder: {
                label: 'Rappel quotidien',
                icon: '🌙',
                tone: 'daily'
            },
            questionnaire_reminder: {
                label: 'Questionnaire',
                icon: '📋',
                tone: 'questionnaire'
            },
            general: {
                label: 'Information',
                icon: 'ℹ️',
                tone: 'general'
            }
        };
        return types[normalizedType] || types.general;
    }

    getNotificationType(type) {
        return this.getNotificationMeta(type).label;
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
            const response = await fetch(`/api/notifications/${notificationId}/delete/`, {
                method: 'DELETE',
                credentials: 'include',
                headers: { 'X-CSRFToken': this.getCsrfToken() }
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
            link.href = '/static/reves/notifications.css?v=20260316-notifs';
            document.head.appendChild(link);
        }
    }

    getCsrfToken() {
        const value = `; ${document.cookie}`;
        const parts = value.split('; csrftoken=');
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }

    dismissToast(notification, notificationId = null) {
        if (!notification || !notification.isConnected) return;

        notification.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => {
            if (notification.isConnected) {
                notification.remove();
            }
        }, 280);

        if (notificationId !== null && notificationId !== undefined) {
            this.saveDismissedNotificationId(notificationId);

            const notif = this.notifications.find(n => n.id === notificationId);
            if (notif && !notif.is_read) {
                notif.is_read = true;
                this.updateNotificationsBadge(this.notifications.filter(n => !n.is_read).length);
                if (this.panel.classList.contains('active')) {
                    this.renderPanelNotifications();
                }
            }

            this.markAsRead(notificationId);
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
        const meta = this.getNotificationMeta(type);
        notification.className = `notification-item ${meta.tone} unread`;
        if (notificationId !== null && notificationId !== undefined) {
            notification.dataset.notificationId = String(notificationId);
        }
        notification.setAttribute('role', 'status');
        notification.setAttribute('aria-live', 'polite');
        
        notification.innerHTML = `
            <div class="notification-icon" aria-hidden="true">${meta.icon}</div>
            <div class="notification-content">
                <div class="notification-meta-row">
                    <div class="notification-tag">${meta.label}</div>
                    <div class="notification-time">${this.formatTime(new Date())}</div>
                </div>
                <div class="notification-title">${this.escapeHtml(title)}</div>
                <div class="notification-message">${this.escapeHtml(message)}</div>
            </div>
            <button type="button" class="notification-close" aria-label="Marquer comme lue">&times;</button>
        `;

        const closeBtn = notification.querySelector('.notification-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
                if (notificationId !== null && notificationId !== undefined) {
                    this.dismissToast(notification, notificationId);
                } else {
                    this.dismissToast(notification);
                    this.saveDismissedNotificationId(notificationId);
                }
            });
        }
        
        notification.onclick = (e) => {
            if (!e.target.closest('.notification-close')) {
                notification.classList.remove('unread');
            }
        };
        
        this.container.appendChild(notification);
        
        // Auto-remove après duration
        if (duration > 0) {
            setTimeout(() => {
                if (notification.isConnected) {
                    if (notificationId !== null && notificationId !== undefined) {
                        this.saveDismissedNotificationId(notificationId);
                    }
                    this.dismissToast(notification);
                }
            }, duration);
        }
    }

    /**
     * Charger et afficher les notifications depuis l'API
     */
    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications/', {
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
            const response = await fetch(`/api/notifications/${notificationId}/read/`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'X-CSRFToken': this.getCsrfToken() }
            });

            if (response.ok) {
                // Mettre à jour le tableau local
                const notif = this.notifications.find(n => n.id === notificationId);
                if (notif) notif.is_read = true;
                // Re-render le panel si ouvert
                if (this.panel.classList.contains('active')) {
                    this.renderPanelNotifications();
                }
                // Calculer le badge localement (évite un aller-retour réseau)
                const unreadCount = this.notifications.filter(n => !n.is_read).length;
                this.updateNotificationsBadge(unreadCount);
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
            const response = await fetch('/api/notifications/unread-count/', {
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
            // Badge natif PWA sur l'icône de l'app (Chrome 81+, Safari 16.4+)
            if ('setAppBadge' in navigator) {
                navigator.setAppBadge(count).catch(() => {});
            }
        } else if (badge) {
            badge.remove();
            // Effacer le badge natif PWA
            if ('clearAppBadge' in navigator) {
                navigator.clearAppBadge().catch(() => {});
            }
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
                primaryAction: `window.location.href = '/questionnaire/'; document.getElementById('modal-overlay').classList.remove('active');`,
                buttons: [
                    {
                        label: 'Plus tard',
                        type: 'secondary',
                        onclick: "document.getElementById('modal-overlay').classList.remove('active'); localStorage.setItem('questionnaire_modal_dismissed', '1');"
                    },
                    {
                        label: 'Remplir maintenant',
                        type: 'primary',
                        onclick: "window.location.href = '/questionnaire/';"
                    }
                ]
            }
        );
    }
}


// Initialiser le gestionnaire de notifications
const notificationManager = new NotificationManager();

// Charger les notifications au chargement de la page SEULEMENT si authentifié
document.addEventListener('DOMContentLoaded', () => {
    // Vérifier si l'utilisateur est authentifié
    const isAuthenticated = document.documentElement.classList.contains('is-authenticated');
    
    if (isAuthenticated) {
        notificationManager.loadNotifications();
        
        // Recharger les notifications toutes les 30 secondes SEULEMENT si authentifié
        setInterval(() => {
            notificationManager.loadNotifications();
        }, 30000);
    }
});

// Export pour utilisation globale
window.notificationManager = notificationManager;
