/**
 * NormScout Workspace View
 * Handles single workspace display, Q&A, and actions
 */

let workspace = null;
let workspaceId = null;

/**
 * Initialize workspace view when page loads
 */
document.addEventListener('DOMContentLoaded', async function() {
    // Wait for auth check
    await waitForAuth();

    // Check if user is logged in
    const user = getCurrentUser();
    if (!user) {
        window.location.href = '/';
        return;
    }

    // Get workspace ID from URL
    workspaceId = getWorkspaceIdFromUrl();
    if (!workspaceId) {
        showError('Invalid workspace URL');
        return;
    }

    // Load workspace
    await loadWorkspace();
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
 * Get workspace ID from URL
 */
function getWorkspaceIdFromUrl() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 1];
}

/**
 * Load workspace from API
 */
async function loadWorkspace() {
    const loadingEl = document.getElementById('workspaceLoading');
    const errorEl = document.getElementById('workspaceError');
    const contentEl = document.getElementById('workspaceContent');

    try {
        const response = await fetch(`/api/workspaces/${workspaceId}`, {
            credentials: 'include'
        });

        if (!response.ok) {
            if (response.status === 404) {
                throw new Error('Workspace not found');
            } else if (response.status === 403) {
                throw new Error('You do not have access to this workspace');
            } else {
                throw new Error('Failed to load workspace');
            }
        }

        workspace = await response.json();

        // Hide loading, show content
        loadingEl.style.display = 'none';
        contentEl.style.display = 'block';

        // Render workspace
        renderWorkspace();

    } catch (error) {
        console.error('Error loading workspace:', error);
        loadingEl.style.display = 'none';
        errorEl.style.display = 'flex';

        const errorMessage = document.getElementById('errorMessage');
        if (errorMessage) {
            errorMessage.textContent = error.message;
        }
    }
}

/**
 * Render workspace content
 */
function renderWorkspace() {
    // Workspace header
    const workspaceNumber = document.getElementById('workspaceNumber');
    const workspaceName = document.getElementById('workspaceName');

    if (workspaceNumber) {
        workspaceNumber.textContent = `Workspace #${workspace.workspace_number}`;
    }

    if (workspaceName) {
        workspaceName.textContent = workspace.name;
    }

    // Product description (with formatting)
    const productDescription = document.getElementById('productDescription');
    if (productDescription) {
        const description = workspace.product_description || 'No description available';
        // Format with line breaks and preserve structure
        productDescription.innerHTML = formatProductDescription(description);
    }

    // Compliance results
    renderComplianceResults();

    // Q&A history
    renderQAHistory();

    // Sidebar info
    renderSidebarInfo();
}

/**
 * Render compliance results
 */
function renderComplianceResults() {
    const resultsEl = document.getElementById('complianceResults');
    if (!resultsEl) return;

    const norms = workspace.matched_norms;

    if (!norms || norms.length === 0) {
        resultsEl.innerHTML = '<p class="text-muted">No compliance results yet</p>';
        return;
    }

    let html = '<div class="norms-list">';

    norms.forEach(norm => {
        // Handle different norm data structures
        const normId = norm.norm_id || norm.id || norm.standard || 'Unknown Norm';
        const title = norm.title || norm.name || normId;
        const description = norm.description || norm.summary || '';
        const confidence = norm.confidence || norm.score || 0;
        const reasoning = norm.reasoning || '';

        html += `
            <div class="norm-item">
                <div class="norm-header">
                    <div class="norm-title-row">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" class="norm-icon">
                            <path d="M8 1l7 4v4c0 3-7 4-7 4s-7-1-7-4V5l7-4z"/>
                            <path d="M6 8l1.5 1.5L11 6"/>
                        </svg>
                        <strong class="norm-id">${escapeHtml(normId)}</strong>
                        ${confidence > 0 ? `<span class="confidence-badge confidence-${getConfidenceClass(confidence)}">${Math.round(confidence)}%</span>` : ''}
                    </div>
                    ${title !== normId ? `<h4 class="norm-title">${escapeHtml(title)}</h4>` : ''}
                </div>
                ${description ? `<p class="norm-description">${escapeHtml(description)}</p>` : ''}
                ${reasoning ? `<p class="norm-reasoning"><em>Why it applies:</em> ${escapeHtml(reasoning)}</p>` : ''}
            </div>
        `;
    });

    html += '</div>';
    resultsEl.innerHTML = html;
}

/**
 * Get confidence class for styling
 */
function getConfidenceClass(confidence) {
    if (confidence >= 80) return 'high';
    if (confidence >= 60) return 'medium';
    return 'low';
}

/**
 * Render Q&A history
 */
function renderQAHistory() {
    const historyEl = document.getElementById('qaHistory');
    if (!historyEl) return;

    const qaHistory = workspace.qa_history || [];

    if (qaHistory.length === 0) {
        historyEl.innerHTML = '<p class="text-muted">No questions asked yet. Ask your first question below!</p>';
        return;
    }

    let html = '';
    qaHistory.forEach((qa, index) => {
        const timestamp = qa.timestamp ? new Date(qa.timestamp).toLocaleString() : '';
        html += `
            <div class="qa-item">
                <div class="qa-question">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <circle cx="8" cy="8" r="7" stroke="currentColor" fill="none"/>
                        <text x="8" y="11" text-anchor="middle" font-size="10" fill="currentColor">Q</text>
                    </svg>
                    <div>
                        <strong>Question ${index + 1}</strong>
                        ${timestamp ? `<span class="qa-timestamp">${timestamp}</span>` : ''}
                        <p>${escapeHtml(qa.question)}</p>
                    </div>
                </div>
                <div class="qa-answer">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <circle cx="8" cy="8" r="7" stroke="currentColor" fill="none"/>
                        <text x="8" y="11" text-anchor="middle" font-size="10" fill="currentColor">A</text>
                    </svg>
                    <div>
                        <strong>Answer</strong>
                        <p>${escapeHtml(qa.answer)}</p>
                    </div>
                </div>
            </div>
        `;
    });

    historyEl.innerHTML = html;
}

/**
 * Render sidebar info
 */
function renderSidebarInfo() {
    const createdDate = document.getElementById('createdDate');
    const updatedDate = document.getElementById('updatedDate');
    const qaCount = document.getElementById('qaCount');

    if (createdDate) {
        const date = new Date(workspace.created_at);
        createdDate.textContent = date.toLocaleDateString();
    }

    if (updatedDate) {
        const date = new Date(workspace.updated_at);
        updatedDate.textContent = date.toLocaleDateString();
    }

    if (qaCount) {
        qaCount.textContent = workspace.qa_count || 0;
    }
}

/**
 * Ask a question
 */
async function askQuestion() {
    const input = document.getElementById('questionInput');
    const askBtn = document.getElementById('askBtn');
    const question = input.value.trim();

    if (!question) {
        alert('Please enter a question');
        return;
    }

    // Disable input
    input.disabled = true;
    askBtn.disabled = true;
    askBtn.textContent = 'Sending...';

    try {
        const response = await fetch(`/api/workspaces/${workspaceId}/ask`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({ question: question })
        });

        if (!response.ok) {
            const data = await response.json();
            if (data.limit_exceeded) {
                alert(data.error);
            } else {
                throw new Error('Failed to send question');
            }
            return;
        }

        const data = await response.json();

        // Add Q&A to history
        if (!workspace.qa_history) {
            workspace.qa_history = [];
        }
        workspace.qa_history.push(data.qa);
        workspace.qa_count = (workspace.qa_count || 0) + 1;

        // Re-render Q&A section
        renderQAHistory();
        renderSidebarInfo();

        // Clear input
        input.value = '';

    } catch (error) {
        console.error('Error asking question:', error);
        alert('Failed to send question. Please try again.');
    } finally {
        // Re-enable input
        input.disabled = false;
        askBtn.disabled = false;
        askBtn.textContent = 'Send Question';
    }
}

/**
 * Export workspace as PDF
 */
function exportWorkspace() {
    window.location.href = `/api/workspaces/${workspaceId}/export/pdf`;
}

/**
 * Show rename modal
 */
function showRenameModal() {
    const modal = document.getElementById('renameModal');
    const input = document.getElementById('newWorkspaceName');

    if (modal && input) {
        input.value = workspace.name;
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
    }
}

/**
 * Save renamed workspace
 */
async function saveRename() {
    const input = document.getElementById('newWorkspaceName');
    const newName = input.value.trim();

    if (!newName) {
        alert('Please enter a name');
        return;
    }

    try {
        const response = await fetch(`/api/workspaces/${workspaceId}/rename`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({ name: newName })
        });

        if (!response.ok) {
            throw new Error('Failed to rename workspace');
        }

        const data = await response.json();
        workspace = data.workspace;

        // Update UI
        const workspaceName = document.getElementById('workspaceName');
        if (workspaceName) {
            workspaceName.textContent = workspace.name;
        }

        hideRenameModal();

    } catch (error) {
        console.error('Error renaming workspace:', error);
        alert('Failed to rename workspace. Please try again.');
    }
}

/**
 * Show delete modal
 */
function showDeleteModal() {
    const modal = document.getElementById('deleteModal');
    if (modal) {
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
    }
}

/**
 * Confirm delete workspace
 */
async function confirmDelete() {
    try {
        const response = await fetch(`/api/workspaces/${workspaceId}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Failed to delete workspace');
        }

        // Redirect to dashboard
        window.location.href = '/dashboard';

    } catch (error) {
        console.error('Error deleting workspace:', error);
        alert('Failed to delete workspace. Please try again.');
    }
}

/**
 * Show error state
 */
function showError(message) {
    const loadingEl = document.getElementById('workspaceLoading');
    const errorEl = document.getElementById('workspaceError');
    const errorMessage = document.getElementById('errorMessage');

    if (loadingEl) loadingEl.style.display = 'none';
    if (errorEl) errorEl.style.display = 'flex';
    if (errorMessage) errorMessage.textContent = message;
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format product description with proper line breaks and structure
 */
function formatProductDescription(text) {
    if (!text) return '';

    // Replace line breaks with <br> tags
    let formatted = escapeHtml(text);

    // Convert double line breaks to paragraph breaks
    formatted = formatted.replace(/\n\n/g, '</p><p class="desc-paragraph">');

    // Convert single line breaks to <br>
    formatted = formatted.replace(/\n/g, '<br>');

    // Wrap in paragraph
    formatted = `<p class="desc-paragraph">${formatted}</p>`;

    // Bold section headers (lines ending with colon)
    formatted = formatted.replace(/([A-Z][^<\n:]+:)/g, '<strong>$1</strong>');

    return formatted;
}

/**
 * Toggle edit mode for product description
 */
function toggleEditDescription() {
    const descEl = document.getElementById('productDescription');
    const editBtn = document.getElementById('editDescBtn');
    const isEditing = descEl.getAttribute('contenteditable') === 'true';

    if (isEditing) {
        // Save mode
        descEl.setAttribute('contenteditable', 'false');
        descEl.classList.remove('editing');
        editBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M2 12l10-10 2 2-10 10H2v-2z"/>
            </svg>
            Edit
        `;

        // Save the updated description
        const newDescription = descEl.innerText;
        saveProductDescription(newDescription);
    } else {
        // Edit mode
        descEl.setAttribute('contenteditable', 'true');
        descEl.classList.add('editing');
        editBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M2 6l6 6L14 6"/>
            </svg>
            Save
        `;
        descEl.focus();
    }
}

/**
 * Save product description
 */
async function saveProductDescription(newDescription) {
    try {
        const response = await fetch(`/api/workspaces/${workspaceId}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({ product_description: newDescription })
        });

        if (!response.ok) {
            throw new Error('Failed to save description');
        }

        workspace.product_description = newDescription;

    } catch (error) {
        console.error('Error saving description:', error);
        alert('Failed to save description. Please try again.');
        // Reload to revert changes
        await loadWorkspace();
    }
}

/**
 * Handle Enter key in question input
 */
document.addEventListener('DOMContentLoaded', function() {
    const questionInput = document.getElementById('questionInput');
    if (questionInput) {
        questionInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && e.ctrlKey) {
                askQuestion();
            }
        });
    }
});

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
