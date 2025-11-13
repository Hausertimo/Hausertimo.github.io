/**
 * NormScout Dashboard
 * Manages workspace display, filtering, and actions
 */

let workspaces = [];
let currentSort = 'last_accessed';
let workspaceToRename = null;
let workspaceToDelete = null;

/**
 * Initialize dashboard when page loads
 */
document.addEventListener('DOMContentLoaded', async function() {
    // Wait for auth check to complete
    await waitForAuth();

    // Check if user is logged in
    const user = getCurrentUser();
    if (!user) {
        // Redirect to home if not logged in
        window.location.href = '/';
        return;
    }

    // Update user info
    updateUserInfo(user);

    // Load workspaces
    await loadWorkspaces();

    // Setup filter buttons
    setupFilters();
});

/**
 * Wait for auth check to complete
 */
async function waitForAuth() {
    return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
            if (isAuthCheckComplete()) {
                clearInterval(checkInterval);
                resolve();
            }
        }, 100);
    });
}

/**
 * Update user info in dashboard
 */
function updateUserInfo(user) {
    // Welcome section
    const userName = document.getElementById('userName');
    const userEmailDisplay = document.getElementById('userEmailDisplay');

    if (userName) {
        const name = user.user_metadata?.full_name ||
                    user.user_metadata?.name ||
                    user.email.split('@')[0];
        userName.textContent = name;
    }

    if (userEmailDisplay) {
        userEmailDisplay.textContent = user.email;
    }

    // Account section
    const accountEmail = document.getElementById('accountEmail');
    const accountProvider = document.getElementById('accountProvider');
    const accountCreated = document.getElementById('accountCreated');

    if (accountEmail) {
        accountEmail.textContent = user.email;
    }

    if (accountProvider) {
        // Get provider from identities or app_metadata
        const provider = user.app_metadata?.provider ||
                        user.user_metadata?.provider ||
                        'Email';
        accountProvider.textContent = provider.charAt(0).toUpperCase() + provider.slice(1);
    }

    if (accountCreated) {
        const created = new Date(user.created_at);
        accountCreated.textContent = created.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
}

/**
 * Load workspaces from API
 */
async function loadWorkspaces() {
    const loadingEl = document.getElementById('workspacesLoading');
    const emptyEl = document.getElementById('workspacesEmpty');
    const gridEl = document.getElementById('workspacesGrid');

    // Show loading state
    loadingEl.style.display = 'flex';
    emptyEl.style.display = 'none';
    gridEl.style.display = 'none';

    try {
        const response = await fetch(`/api/workspaces/?sort_by=${currentSort}&order=desc`, {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Failed to load workspaces');
        }

        const data = await response.json();
        workspaces = data.workspaces || [];

        // Hide loading
        loadingEl.style.display = 'none';

        // Update count
        const countEl = document.getElementById('workspaceCount');
        if (countEl) {
            countEl.textContent = workspaces.length;
        }

        if (workspaces.length === 0) {
            // Show empty state
            emptyEl.style.display = 'flex';
        } else {
            // Show workspaces
            gridEl.style.display = 'grid';
            renderWorkspaces();
        }
    } catch (error) {
        console.error('Error loading workspaces:', error);
        loadingEl.style.display = 'none';
        emptyEl.style.display = 'flex';
        alert('Failed to load workspaces. Please try again.');
    }
}

/**
 * Render workspaces in grid
 */
function renderWorkspaces() {
    const gridEl = document.getElementById('workspacesGrid');
    if (!gridEl) return;

    gridEl.innerHTML = '';

    workspaces.forEach(workspace => {
        const card = createWorkspaceCard(workspace);
        gridEl.appendChild(card);
    });
}

/**
 * Create workspace card element
 */
function createWorkspaceCard(workspace) {
    const card = document.createElement('div');
    card.className = 'workspace-card';

    const createdDate = new Date(workspace.created_at);
    const lastAccessedDate = new Date(workspace.last_accessed);
    const now = new Date();

    card.innerHTML = `
        <div class="workspace-card-header">
            <div>
                <span class="workspace-number">#${workspace.workspace_number}</span>
                <h3 class="workspace-name">${escapeHtml(workspace.name)}</h3>
            </div>
            <div class="workspace-actions-btn">
                <button class="icon-btn" onclick="toggleWorkspaceMenu(event, '${workspace.id}')">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <circle cx="8" cy="3" r="1.5"/>
                        <circle cx="8" cy="8" r="1.5"/>
                        <circle cx="8" cy="13" r="1.5"/>
                    </svg>
                </button>
                <div class="workspace-menu" id="menu-${workspace.id}" style="display: none;">
                    <button onclick="openWorkspace('${workspace.id}')">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                            <path d="M2 2h10v10H2V2z"/>
                        </svg>
                        Open
                    </button>
                    <button onclick="showRenameModal('${workspace.id}', '${escapeHtml(workspace.name)}')">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                            <path d="M2 10l8-8 2 2-8 8H2v-2z"/>
                        </svg>
                        Rename
                    </button>
                    <button onclick="exportWorkspace('${workspace.id}')">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                            <path d="M7 2v8M4 7l3 3 3-3M2 12h10"/>
                        </svg>
                        Export PDF
                    </button>
                    <hr>
                    <button class="text-danger" onclick="showDeleteModal('${workspace.id}', '${escapeHtml(workspace.name)}')">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                            <path d="M3 3l8 8M11 3l-8 8"/>
                        </svg>
                        Delete
                    </button>
                </div>
            </div>
        </div>
        <p class="workspace-description">${escapeHtml(truncate(workspace.product_description, 150))}</p>
        <div class="workspace-meta">
            <span>Created ${formatRelativeTime(createdDate, now)}</span>
            <span>•</span>
            <span>Opened ${formatRelativeTime(lastAccessedDate, now)}</span>
        </div>
        <div class="workspace-card-actions">
            <button class="btn btn-primary btn-sm" onclick="openWorkspace('${workspace.id}')">Open</button>
            <button class="btn btn-secondary btn-sm" onclick="showRenameModal('${workspace.id}', '${escapeHtml(workspace.name)}')">Rename</button>
        </div>
    `;

    return card;
}

/**
 * Toggle workspace menu
 */
function toggleWorkspaceMenu(event, workspaceId) {
    event.stopPropagation();
    const menu = document.getElementById(`menu-${workspaceId}`);

    // Close all other menus
    document.querySelectorAll('.workspace-menu').forEach(m => {
        if (m.id !== `menu-${workspaceId}`) {
            m.style.display = 'none';
        }
    });

    if (menu) {
        menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    }
}

/**
 * Close all workspace menus when clicking outside
 */
document.addEventListener('click', function() {
    document.querySelectorAll('.workspace-menu').forEach(menu => {
        menu.style.display = 'none';
    });
});

/**
 * Open workspace
 */
function openWorkspace(workspaceId) {
    window.location.href = `/workspace/${workspaceId}`;
}

/**
 * Show rename modal
 */
function showRenameModal(workspaceId, currentName) {
    workspaceToRename = workspaceId;
    const modal = document.getElementById('renameModal');
    const input = document.getElementById('newWorkspaceName');

    if (modal && input) {
        input.value = unescapeHtml(currentName);
        modal.style.display = 'flex';
        setTimeout(() => input.focus(), 100);
    }
}

/**
 * Hide rename modal
 */
function hideRenameModal() {
    const modal = document.getElementById('renameModal');
    if (modal) {
        modal.style.display = 'none';
        workspaceToRename = null;
    }
}

/**
 * Save renamed workspace
 */
async function saveRename() {
    if (!workspaceToRename) return;

    const input = document.getElementById('newWorkspaceName');
    const newName = input.value.trim();

    if (!newName) {
        alert('Please enter a name');
        return;
    }

    try {
        const response = await fetch(`/api/workspaces/${workspaceToRename}/rename`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({ name: newName })
        });

        if (!response.ok) {
            throw new Error('Failed to rename workspace');
        }

        // Reload workspaces
        await loadWorkspaces();
        hideRenameModal();
    } catch (error) {
        console.error('Error renaming workspace:', error);
        alert('Failed to rename workspace. Please try again.');
    }
}

/**
 * Show delete confirmation modal
 */
function showDeleteModal(workspaceId, workspaceName) {
    workspaceToDelete = workspaceId;
    const modal = document.getElementById('deleteModal');
    const nameEl = document.getElementById('deleteWorkspaceName');

    if (modal && nameEl) {
        nameEl.textContent = unescapeHtml(workspaceName);
        modal.style.display = 'flex';
    }
}

/**
 * Hide delete modal
 */
function hideDeleteModal() {
    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.style.display = 'none';
        workspaceToDelete = null;
    }
}

/**
 * Confirm delete workspace
 */
async function confirmDelete() {
    if (!workspaceToDelete) return;

    try {
        const response = await fetch(`/api/workspaces/${workspaceToDelete}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Failed to delete workspace');
        }

        // Reload workspaces
        await loadWorkspaces();
        hideDeleteModal();
    } catch (error) {
        console.error('Error deleting workspace:', error);
        alert('Failed to delete workspace. Please try again.');
    }
}

/**
 * Export workspace as PDF
 */
async function exportWorkspace(workspaceId) {
    try {
        window.location.href = `/api/workspaces/${workspaceId}/export/pdf`;
    } catch (error) {
        console.error('Error exporting workspace:', error);
        alert('Failed to export workspace. Please try again.');
    }
}

/**
 * Setup filter buttons
 */
function setupFilters() {
    const filterBtns = document.querySelectorAll('.filter-btn');

    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active from all
            filterBtns.forEach(b => b.classList.remove('active'));
            // Add active to clicked
            this.classList.add('active');

            // Update sort and reload
            currentSort = this.getAttribute('data-sort');
            loadWorkspaces();
        });
    });
}

/**
 * Format relative time
 */
function formatRelativeTime(date, now) {
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    const weeks = Math.floor(days / 7);
    const months = Math.floor(days / 30);

    if (seconds < 60) return 'just now';
    if (minutes < 60) return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} ago`;
    if (hours < 24) return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;
    if (days < 7) return `${days} ${days === 1 ? 'day' : 'days'} ago`;
    if (weeks < 4) return `${weeks} ${weeks === 1 ? 'week' : 'weeks'} ago`;
    if (months < 12) return `${months} ${months === 1 ? 'month' : 'months'} ago`;

    const years = Math.floor(months / 12);
    return `${years} ${years === 1 ? 'year' : 'years'} ago`;
}

/**
 * Truncate text
 */
function truncate(text, length) {
    if (!text) return '';
    if (text.length <= length) return text;
    return text.substring(0, length) + '...';
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Unescape HTML
 */
function unescapeHtml(html) {
    const div = document.createElement('div');
    div.innerHTML = html;
    return div.textContent;
}

/**
 * Handle Enter key in rename input
 */
document.addEventListener('DOMContentLoaded', function() {
    const renameInput = document.getElementById('newWorkspaceName');
    if (renameInput) {
        renameInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                saveRename();
            }
        });
    }
});
