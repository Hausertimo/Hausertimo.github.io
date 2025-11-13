/**
 * Universal User Tracking Library
 *
 * A flexible, privacy-first tracking system that works on any website.
 * Features:
 * - Zero configuration needed for basic tracking
 * - GDPR-compliant cookie consent management
 * - Automatic page view, time spent, and scroll depth tracking
 * - Custom event tracking via data attributes or API
 * - Offline support with event queuing
 * - Portable across multiple sites
 *
 * Usage:
 *   <script src="/static/tracking.js"></script>
 *
 *   Optional configuration:
 *   <script>
 *     window.TRACKING_CONFIG = {
 *       apiEndpoint: '/api/tracking/event',
 *       batchSize: 10,
 *       batchInterval: 5000,
 *       enableScrollTracking: true,
 *       enableClickTracking: true,
 *       privacyPolicyUrl: '/privacy'
 *     };
 *   </script>
 */

(function() {
    'use strict';

    // ============================================================================
    // CONFIGURATION
    // ============================================================================

    const DEFAULT_CONFIG = {
        apiEndpoint: '/api/tracking/event',
        batchSize: 10,               // Send events in batches
        batchInterval: 5000,         // Send every 5 seconds
        enableScrollTracking: true,
        enableClickTracking: true,
        enableFormTracking: true,
        enableVisibilityTracking: true,
        scrollDepthThresholds: [25, 50, 75, 90, 100],
        privacyPolicyUrl: '/privacy',
        cookieName: 'user_tracking_consent',
        cookieExpiry: 365,           // Days
        sessionStorageKey: 'tracking_session_id',
        debug: false
    };

    const CONFIG = Object.assign({}, DEFAULT_CONFIG, window.TRACKING_CONFIG || {});

    // ============================================================================
    // UTILITY FUNCTIONS
    // ============================================================================

    function log(...args) {
        if (CONFIG.debug) {
            console.log('[Tracking]', ...args);
        }
    }

    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    function setCookie(name, value, days) {
        const expires = new Date();
        expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Strict`;
    }

    function deleteCookie(name) {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
    }

    // ============================================================================
    // CONSENT MANAGEMENT
    // ============================================================================

    class ConsentManager {
        constructor() {
            this.consentGiven = false;
            this.consentChecked = false;
            this.checkConsent();
        }

        checkConsent() {
            const consent = getCookie(CONFIG.cookieName);
            this.consentGiven = consent === 'true';
            this.consentChecked = consent !== null;
            log('Consent checked:', this.consentGiven, 'Already asked:', this.consentChecked);
            return this.consentGiven;
        }

        giveConsent(analytics = true) {
            setCookie(CONFIG.cookieName, analytics ? 'true' : 'false', CONFIG.cookieExpiry);
            this.consentGiven = analytics;
            this.consentChecked = true;
            log('Consent given:', analytics);

            // Dispatch custom event
            window.dispatchEvent(new CustomEvent('trackingConsentChanged', {
                detail: { consent: analytics }
            }));

            return analytics;
        }

        revokeConsent() {
            deleteCookie(CONFIG.cookieName);
            this.consentGiven = false;
            this.consentChecked = false;
            log('Consent revoked');

            // Clear stored session
            sessionStorage.removeItem(CONFIG.sessionStorageKey);

            window.dispatchEvent(new CustomEvent('trackingConsentChanged', {
                detail: { consent: false }
            }));
        }

        hasConsent() {
            return this.consentGiven;
        }

        needsPrompt() {
            return !this.consentChecked;
        }
    }

    // ============================================================================
    // TRACKING CORE
    // ============================================================================

    class UserTracker {
        constructor() {
            this.consent = new ConsentManager();
            this.sessionId = null;
            this.eventQueue = [];
            this.batchTimer = null;
            this.pageStartTime = Date.now();
            this.lastActivityTime = Date.now();
            this.scrollDepthReached = new Set();
            this.isVisible = !document.hidden;
            this.timeOnPage = 0;
            this.activeTime = 0;
            this.lastVisibilityChange = Date.now();

            // Initialize session if consent already given
            if (this.consent.hasConsent()) {
                this.initializeSession();
                this.startTracking();
            }

            // Listen for consent changes
            window.addEventListener('trackingConsentChanged', (e) => {
                if (e.detail.consent) {
                    this.initializeSession();
                    this.startTracking();
                } else {
                    this.stopTracking();
                }
            });

            // Send queued events before page unload
            window.addEventListener('beforeunload', () => this.flush(true));
        }

        initializeSession() {
            // Try to get existing session ID
            this.sessionId = sessionStorage.getItem(CONFIG.sessionStorageKey);

            // Create new session if doesn't exist
            if (!this.sessionId) {
                this.sessionId = generateUUID();
                sessionStorage.setItem(CONFIG.sessionStorageKey, this.sessionId);
                log('New session created:', this.sessionId);
            } else {
                log('Existing session resumed:', this.sessionId);
            }
        }

        startTracking() {
            if (!this.consent.hasConsent()) {
                log('Tracking not started - no consent');
                return;
            }

            log('Starting tracking...');

            // Track initial page view
            this.trackPageView();

            // Set up event listeners
            this.setupEventListeners();

            // Start batch timer
            this.startBatchTimer();
        }

        stopTracking() {
            log('Stopping tracking...');

            // Send final events
            this.flush(true);

            // Clear timer
            if (this.batchTimer) {
                clearInterval(this.batchTimer);
                this.batchTimer = null;
            }

            // Remove event listeners would go here if we stored references
            // For now, we'll just stop queuing new events (consent check prevents this)
        }

        setupEventListeners() {
            // Page visibility tracking
            if (CONFIG.enableVisibilityTracking) {
                document.addEventListener('visibilitychange', () => this.handleVisibilityChange());
            }

            // Scroll depth tracking
            if (CONFIG.enableScrollTracking) {
                let scrollTimeout;
                window.addEventListener('scroll', () => {
                    clearTimeout(scrollTimeout);
                    scrollTimeout = setTimeout(() => this.trackScrollDepth(), 100);
                }, { passive: true });
            }

            // Click tracking
            if (CONFIG.enableClickTracking) {
                document.addEventListener('click', (e) => this.handleClick(e), true);
            }

            // Form tracking
            if (CONFIG.enableFormTracking) {
                document.addEventListener('submit', (e) => this.handleFormSubmit(e), true);
            }

            // Track elements with data-track-visibility attribute
            this.setupVisibilityObservers();

            // Activity tracking (for engaged time)
            ['mousedown', 'keydown', 'scroll', 'touchstart'].forEach(event => {
                document.addEventListener(event, () => {
                    this.lastActivityTime = Date.now();
                }, { passive: true });
            });
        }

        handleVisibilityChange() {
            const now = Date.now();
            const wasVisible = this.isVisible;
            this.isVisible = !document.hidden;

            if (wasVisible && !this.isVisible) {
                // Page became hidden - record active time
                const sessionTime = now - this.lastVisibilityChange;
                this.activeTime += sessionTime;
                log('Page hidden. Session time:', sessionTime, 'Total active:', this.activeTime);
            } else if (!wasVisible && this.isVisible) {
                // Page became visible
                this.lastVisibilityChange = now;
                log('Page visible again');
            }

            this.queueEvent({
                event_type: 'visibility_change',
                is_visible: this.isVisible,
                active_time: Math.round(this.activeTime / 1000)
            });
        }

        trackPageView() {
            const pageData = {
                event_type: 'page_view',
                page: window.location.pathname,
                page_title: document.title,
                referrer: document.referrer || 'direct',
                viewport_width: window.innerWidth,
                viewport_height: window.innerHeight,
                screen_width: window.screen.width,
                screen_height: window.screen.height,
                user_agent: navigator.userAgent,
                language: navigator.language
            };

            this.queueEvent(pageData);
            log('Page view tracked:', pageData);
        }

        trackScrollDepth() {
            const windowHeight = window.innerHeight;
            const documentHeight = document.documentElement.scrollHeight;
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollPercent = Math.round((scrollTop / (documentHeight - windowHeight)) * 100);

            CONFIG.scrollDepthThresholds.forEach(threshold => {
                if (scrollPercent >= threshold && !this.scrollDepthReached.has(threshold)) {
                    this.scrollDepthReached.add(threshold);
                    this.queueEvent({
                        event_type: 'scroll_depth',
                        depth_percent: threshold,
                        page: window.location.pathname
                    });
                    log('Scroll depth reached:', threshold + '%');
                }
            });
        }

        handleClick(event) {
            const element = event.target;

            // Check for data-track attribute
            const trackLabel = element.getAttribute('data-track') ||
                             element.closest('[data-track]')?.getAttribute('data-track');

            if (trackLabel) {
                this.queueEvent({
                    event_type: 'click',
                    element_type: element.tagName.toLowerCase(),
                    track_label: trackLabel,
                    text: element.textContent?.trim().substring(0, 100),
                    page: window.location.pathname
                });
                log('Tracked click:', trackLabel);
                return;
            }

            // Auto-track important elements
            if (element.tagName === 'A') {
                this.queueEvent({
                    event_type: 'link_click',
                    href: element.href,
                    text: element.textContent?.trim().substring(0, 100),
                    external: !element.href.startsWith(window.location.origin),
                    page: window.location.pathname
                });
                log('Link clicked:', element.href);
            } else if (element.tagName === 'BUTTON') {
                this.queueEvent({
                    event_type: 'button_click',
                    button_id: element.id,
                    button_class: element.className,
                    text: element.textContent?.trim().substring(0, 100),
                    page: window.location.pathname
                });
                log('Button clicked:', element.id || element.className);
            }
        }

        handleFormSubmit(event) {
            const form = event.target;

            this.queueEvent({
                event_type: 'form_submit',
                form_id: form.id,
                form_action: form.action,
                form_method: form.method,
                page: window.location.pathname
            });
            log('Form submitted:', form.id);
        }

        setupVisibilityObservers() {
            if (!('IntersectionObserver' in window)) return;

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const element = entry.target;
                        const sectionName = element.getAttribute('data-track-section');

                        this.queueEvent({
                            event_type: 'section_visible',
                            section: sectionName,
                            page: window.location.pathname
                        });

                        log('Section visible:', sectionName);
                        observer.unobserve(element); // Track only once
                    }
                });
            }, { threshold: 0.5 });

            // Observe all elements with data-track-section
            document.querySelectorAll('[data-track-section]').forEach(el => {
                observer.observe(el);
            });
        }

        queueEvent(eventData) {
            if (!this.consent.hasConsent()) {
                log('Event not queued - no consent');
                return;
            }

            const event = {
                session_id: this.sessionId,
                timestamp: new Date().toISOString(),
                ...eventData
            };

            this.eventQueue.push(event);
            log('Event queued:', event);

            // Send immediately if batch size reached
            if (this.eventQueue.length >= CONFIG.batchSize) {
                this.flush();
            }
        }

        startBatchTimer() {
            this.batchTimer = setInterval(() => {
                if (this.eventQueue.length > 0) {
                    this.flush();
                }
            }, CONFIG.batchInterval);
        }

        flush(useBeacon = false) {
            if (this.eventQueue.length === 0) return;

            const events = [...this.eventQueue];
            this.eventQueue = [];

            // Add time on page to last event
            const timeOnPage = Math.round((Date.now() - this.pageStartTime) / 1000);
            const activeTime = Math.round(this.activeTime / 1000);

            if (events.length > 0) {
                events[events.length - 1].time_on_page = timeOnPage;
                events[events.length - 1].active_time = activeTime;
            }

            const payload = JSON.stringify({ events });

            if (useBeacon && navigator.sendBeacon) {
                // Use sendBeacon for reliable delivery on page unload
                navigator.sendBeacon(CONFIG.apiEndpoint, payload);
                log('Events sent via beacon:', events.length);
            } else {
                // Use fetch for normal sending
                fetch(CONFIG.apiEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: payload,
                    keepalive: true
                })
                .then(response => {
                    if (response.ok) {
                        log('Events sent successfully:', events.length);
                    } else {
                        log('Failed to send events:', response.status);
                        // Re-queue on failure
                        this.eventQueue.unshift(...events);
                    }
                })
                .catch(error => {
                    log('Error sending events:', error);
                    // Re-queue on error
                    this.eventQueue.unshift(...events);
                });
            }
        }

        // Public API for custom tracking
        trackCustomEvent(eventName, eventData = {}) {
            this.queueEvent({
                event_type: 'custom',
                event_name: eventName,
                ...eventData
            });
        }
    }

    // ============================================================================
    // COOKIE CONSENT BANNER
    // ============================================================================

    class ConsentBanner {
        constructor(tracker) {
            this.tracker = tracker;
            this.banner = null;
            this.modal = null;
        }

        show() {
            if (this.banner) return; // Already shown

            // Create banner HTML
            this.banner = document.createElement('div');
            this.banner.id = 'cookie-consent-banner';
            this.banner.innerHTML = `
                <div class="cookie-consent-content">
                    <div class="cookie-consent-text">
                        <span class="cookie-icon">🍪</span>
                        <p>We use cookies to improve your experience and understand how you use our site.
                        <a href="${CONFIG.privacyPolicyUrl}" target="_blank">Learn more</a></p>
                    </div>
                    <div class="cookie-consent-actions">
                        <button id="cookie-accept-all" class="cookie-btn cookie-btn-primary">Accept All</button>
                        <button id="cookie-essential-only" class="cookie-btn cookie-btn-secondary">Essential Only</button>
                        <button id="cookie-customize" class="cookie-btn cookie-btn-text">Customize</button>
                    </div>
                </div>
            `;

            // Add styles
            this.injectStyles();

            // Add to page
            document.body.appendChild(this.banner);

            // Animate in
            setTimeout(() => this.banner.classList.add('visible'), 100);

            // Add event listeners
            document.getElementById('cookie-accept-all').addEventListener('click', () => this.acceptAll());
            document.getElementById('cookie-essential-only').addEventListener('click', () => this.essentialOnly());
            document.getElementById('cookie-customize').addEventListener('click', () => this.showCustomize());
        }

        hide() {
            if (!this.banner) return;

            this.banner.classList.remove('visible');
            setTimeout(() => {
                this.banner.remove();
                this.banner = null;
            }, 300);
        }

        acceptAll() {
            this.tracker.consent.giveConsent(true);
            this.hide();
        }

        essentialOnly() {
            this.tracker.consent.giveConsent(false);
            this.hide();
        }

        showCustomize() {
            this.modal = document.createElement('div');
            this.modal.id = 'cookie-consent-modal';
            this.modal.innerHTML = `
                <div class="cookie-modal-overlay"></div>
                <div class="cookie-modal-content">
                    <h2>Cookie Preferences</h2>
                    <p>We use cookies to enhance your browsing experience. Choose which cookies you want to allow:</p>

                    <div class="cookie-category">
                        <div class="cookie-category-header">
                            <label>
                                <input type="checkbox" checked disabled>
                                <strong>Essential Cookies</strong>
                            </label>
                        </div>
                        <p class="cookie-category-description">
                            Required for the website to function. These cannot be disabled.
                        </p>
                    </div>

                    <div class="cookie-category">
                        <div class="cookie-category-header">
                            <label>
                                <input type="checkbox" id="analytics-toggle" checked>
                                <strong>Analytics Cookies</strong>
                            </label>
                        </div>
                        <p class="cookie-category-description">
                            Help us understand how visitors use our website, which pages are most popular,
                            and how people navigate through the site.
                        </p>
                    </div>

                    <div class="cookie-modal-actions">
                        <button id="cookie-save-preferences" class="cookie-btn cookie-btn-primary">Save Preferences</button>
                        <button id="cookie-modal-close" class="cookie-btn cookie-btn-secondary">Cancel</button>
                    </div>
                </div>
            `;

            document.body.appendChild(this.modal);
            setTimeout(() => this.modal.classList.add('visible'), 10);

            document.getElementById('cookie-save-preferences').addEventListener('click', () => {
                const analyticsEnabled = document.getElementById('analytics-toggle').checked;
                this.tracker.consent.giveConsent(analyticsEnabled);
                this.hideModal();
                this.hide();
            });

            document.getElementById('cookie-modal-close').addEventListener('click', () => this.hideModal());
            this.modal.querySelector('.cookie-modal-overlay').addEventListener('click', () => this.hideModal());
        }

        hideModal() {
            if (!this.modal) return;

            this.modal.classList.remove('visible');
            setTimeout(() => {
                this.modal.remove();
                this.modal = null;
            }, 300);
        }

        injectStyles() {
            if (document.getElementById('cookie-consent-styles')) return;

            const style = document.createElement('style');
            style.id = 'cookie-consent-styles';
            style.textContent = `
                #cookie-consent-banner {
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 1.5rem;
                    box-shadow: 0 -4px 20px rgba(0,0,0,0.15);
                    z-index: 9999;
                    transform: translateY(100%);
                    transition: transform 0.3s ease-out;
                }

                #cookie-consent-banner.visible {
                    transform: translateY(0);
                }

                .cookie-consent-content {
                    max-width: 1200px;
                    margin: 0 auto;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 2rem;
                    flex-wrap: wrap;
                }

                .cookie-consent-text {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                    flex: 1;
                    min-width: 300px;
                }

                .cookie-icon {
                    font-size: 2rem;
                    flex-shrink: 0;
                }

                .cookie-consent-text p {
                    margin: 0;
                    line-height: 1.5;
                }

                .cookie-consent-text a {
                    color: white;
                    text-decoration: underline;
                    font-weight: 600;
                }

                .cookie-consent-actions {
                    display: flex;
                    gap: 0.75rem;
                    flex-wrap: wrap;
                }

                .cookie-btn {
                    padding: 0.75rem 1.5rem;
                    border: none;
                    border-radius: 6px;
                    font-size: 0.95rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                    white-space: nowrap;
                }

                .cookie-btn-primary {
                    background: white;
                    color: #667eea;
                }

                .cookie-btn-primary:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                }

                .cookie-btn-secondary {
                    background: rgba(255,255,255,0.2);
                    color: white;
                    border: 2px solid white;
                }

                .cookie-btn-secondary:hover {
                    background: rgba(255,255,255,0.3);
                }

                .cookie-btn-text {
                    background: transparent;
                    color: white;
                    text-decoration: underline;
                }

                .cookie-btn-text:hover {
                    opacity: 0.8;
                }

                #cookie-consent-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    z-index: 10000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    opacity: 0;
                    transition: opacity 0.3s;
                }

                #cookie-consent-modal.visible {
                    opacity: 1;
                }

                .cookie-modal-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0,0,0,0.6);
                    backdrop-filter: blur(4px);
                }

                .cookie-modal-content {
                    position: relative;
                    background: white;
                    border-radius: 12px;
                    padding: 2rem;
                    max-width: 500px;
                    width: 90%;
                    max-height: 80vh;
                    overflow-y: auto;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                }

                .cookie-modal-content h2 {
                    margin: 0 0 1rem 0;
                    color: #333;
                }

                .cookie-modal-content > p {
                    color: #666;
                    margin-bottom: 1.5rem;
                }

                .cookie-category {
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 1rem;
                    margin-bottom: 1rem;
                }

                .cookie-category-header label {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    cursor: pointer;
                }

                .cookie-category-header input[type="checkbox"] {
                    width: 20px;
                    height: 20px;
                    cursor: pointer;
                }

                .cookie-category-header input[type="checkbox"]:disabled {
                    cursor: not-allowed;
                }

                .cookie-category-description {
                    margin: 0.5rem 0 0 0;
                    color: #666;
                    font-size: 0.9rem;
                    padding-left: 1.75rem;
                }

                .cookie-modal-actions {
                    margin-top: 1.5rem;
                    display: flex;
                    gap: 1rem;
                }

                .cookie-modal-actions .cookie-btn {
                    flex: 1;
                }

                .cookie-modal-actions .cookie-btn-primary {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }

                @media (max-width: 768px) {
                    .cookie-consent-content {
                        flex-direction: column;
                        align-items: stretch;
                    }

                    .cookie-consent-actions {
                        justify-content: stretch;
                    }

                    .cookie-btn {
                        flex: 1;
                    }

                    .cookie-modal-content {
                        padding: 1.5rem;
                    }

                    .cookie-modal-actions {
                        flex-direction: column;
                    }
                }
            `;

            document.head.appendChild(style);
        }
    }

    // ============================================================================
    // INITIALIZATION
    // ============================================================================

    // Wait for DOM to be ready
    function init() {
        log('Initializing tracking system...');

        // Create tracker instance
        const tracker = new UserTracker();

        // Show consent banner if needed
        if (tracker.consent.needsPrompt()) {
            const banner = new ConsentBanner(tracker);
            banner.show();
        }

        // Expose public API
        window.UserTracker = {
            track: (eventName, data) => tracker.trackCustomEvent(eventName, data),
            consent: {
                give: (analytics) => tracker.consent.giveConsent(analytics),
                revoke: () => tracker.consent.revokeConsent(),
                hasConsent: () => tracker.consent.hasConsent()
            },
            getSessionId: () => tracker.sessionId
        };

        log('Tracking system initialized');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
