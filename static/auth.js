/**
 * NormScout Authentication Utilities
 * Handles user login state, modal management, and auth UI updates
 */

// Global auth state
let currentUser = null;
let authCheckComplete = false;

/**
 * Check if user is logged in
 * Calls /auth/me endpoint to verify session
 */
async function checkAuth() {
    try {
        const response = await fetch('/auth/me', {
            credentials: 'include' // Send cookies
        });

        if (response.ok) {
            currentUser = await response.json();
            authCheckComplete = true;
            updateAuthUI(true);
            return true;
        } else {
            currentUser = null;
            authCheckComplete = true;
            updateAuthUI(false);
            return false;
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        currentUser = null;
        authCheckComplete = true;
        updateAuthUI(false);
        return false;
    }
}

/**
 * Update UI based on auth state
 * Shows/hides login button vs user dropdown
 */
function updateAuthUI(isLoggedIn) {
    const loginBtn = document.getElementById('loginBtn');
    const userDropdown = document.getElementById('userDropdown');

    if (isLoggedIn && currentUser) {
        // Hide login button, show user dropdown
        if (loginBtn) loginBtn.style.display = 'none';
        if (userDropdown) {
            userDropdown.style.display = 'flex';
            updateUserDropdown();
        }
    } else {
        // Show login button, hide user dropdown
        if (loginBtn) loginBtn.style.display = 'inline-block';
        if (userDropdown) userDropdown.style.display = 'none';
    }
}

/**
 * Update user dropdown with current user info
 */
function updateUserDropdown() {
    if (!currentUser) return;

    const userEmail = document.getElementById('userEmail');
    const userAvatar = document.getElementById('userAvatar');

    if (userEmail) {
        userEmail.textContent = currentUser.email || 'User';
    }

    if (userAvatar) {
        // Get avatar from user metadata (OAuth providers usually provide this)
        const avatarUrl = currentUser.user_metadata?.avatar_url ||
                         currentUser.user_metadata?.picture ||
                         generateAvatarUrl(currentUser.email);
        userAvatar.src = avatarUrl;
    }
}

/**
 * Generate avatar URL from email (using Gravatar or placeholder)
 */
function generateAvatarUrl(email) {
    // Simple placeholder - could use Gravatar or other service
    const initial = email ? email.charAt(0).toUpperCase() : 'U';
    return `https://ui-avatars.com/api/?name=${initial}&background=2563eb&color=fff&size=32`;
}

/**
 * Show login modal
 */
function showLoginModal() {
    const modal = document.getElementById('loginModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    }
}

/**
 * Hide login modal
 */
function hideLoginModal() {
    const modal = document.getElementById('loginModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = ''; // Restore scrolling
    }
}

/**
 * Login with Google
 */
function loginWithGoogle() {
    const redirectTo = localStorage.getItem('redirectAfterLogin') || '/dashboard';
    window.location.href = `/auth/login/google?redirect_to=${encodeURIComponent(redirectTo)}`;
}

/**
 * Login with GitHub
 */
function loginWithGitHub() {
    const redirectTo = localStorage.getItem('redirectAfterLogin') || '/dashboard';
    window.location.href = `/auth/login/github?redirect_to=${encodeURIComponent(redirectTo)}`;
}

/**
 * Sign out user
 */
async function signOut() {
    try {
        const response = await fetch('/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });

        if (response.ok) {
            currentUser = null;
            updateAuthUI(false);
            // Redirect to homepage
            window.location.href = '/';
        } else {
            alert('Failed to sign out. Please try again.');
        }
    } catch (error) {
        console.error('Sign out failed:', error);
        alert('Failed to sign out. Please try again.');
    }
}

/**
 * Toggle user dropdown menu
 */
function toggleUserMenu() {
    const menu = document.getElementById('userMenu');
    if (menu) {
        menu.classList.toggle('show');
    }
}

/**
 * Close user menu when clicking outside
 */
document.addEventListener('click', function(event) {
    const userDropdown = document.getElementById('userDropdown');
    const userMenu = document.getElementById('userMenu');

    if (userDropdown && userMenu && !userDropdown.contains(event.target)) {
        userMenu.classList.remove('show');
    }
});

/**
 * Close modal when clicking outside
 */
document.addEventListener('click', function(event) {
    const modal = document.getElementById('loginModal');
    if (modal && event.target === modal) {
        hideLoginModal();
    }
});

/**
 * Close modal with Escape key
 */
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        hideLoginModal();
    }
});

/**
 * Require authentication for a function
 * If not logged in, shows login modal instead
 */
function requireAuth(callback) {
    if (currentUser) {
        callback();
    } else {
        showLoginModal();
    }
}

/**
 * Get current user
 */
function getCurrentUser() {
    return currentUser;
}

/**
 * Check if auth check is complete
 */
function isAuthCheckComplete() {
    return authCheckComplete;
}

/**
 * Initialize mobile menu toggle
 */
function initMobileMenu() {
    const toggle = document.getElementById('mobile-menu-toggle');
    const nav = document.getElementById('nav');

    if (toggle && nav) {
        toggle.addEventListener('click', function() {
            nav.classList.toggle('mobile-nav-open');
            toggle.classList.toggle('mobile-menu-active');

            // Animate hamburger icon
            const spans = toggle.querySelectorAll('span');
            if (toggle.classList.contains('mobile-menu-active')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    initMobileMenu();
});

/**
 * Re-check auth when page is restored from bfcache (back/forward button)
 * This fixes the issue where pressing back button shows "not logged in" UI
 * even though the user is still authenticated
 */
window.addEventListener('pageshow', function(event) {
    // event.persisted is true when page is loaded from bfcache
    if (event.persisted) {
        // Page was restored from cache, re-check auth state
        checkAuth();
    }
});
