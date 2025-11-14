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

    // Product description (rendered as HTML from backend)
    const productDescription = document.getElementById('productDescription');
    if (productDescription) {
        // Use pre-rendered HTML from backend (Markdown → HTML)
        productDescription.innerHTML = workspace.product_description_html || workspace.product_description || 'No description available';
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
    const normsCountEl = document.getElementById('normsCount');

    if (!norms || norms.length === 0) {
        resultsEl.innerHTML = '<p class="text-muted">No compliance results yet</p>';
        if (normsCountEl) normsCountEl.textContent = '';
        return;
    }

    // Update count badge
    if (normsCountEl) {
        normsCountEl.textContent = `${norms.length}`;
    }

    let html = '<div class="norms-list">';

    norms.forEach(norm => {
        // Handle different norm data structures
        const normId = norm.norm_id || norm.id || norm.standard || 'Unknown Norm';
        const title = norm.title || norm.name || normId;
        const description = norm.description || norm.summary || '';
        const confidence = norm.confidence || norm.score || 0;
        const reasoning = norm.reasoning || '';
        const url = norm.url || norm.link || null;

        // Make the whole card clickable if there's a URL
        const cardTag = url ? 'a' : 'div';
        const cardAttrs = url ? `href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="norm-item norm-clickable"` : 'class="norm-item"';

        html += `
            <${cardTag} ${cardAttrs}>
                <div class="norm-header">
                    <div class="norm-title-row">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" class="norm-icon">
                            <path d="M8 1l7 4v4c0 3-7 4-7 4s-7-1-7-4V5l7-4z"/>
                            <path d="M6 8l1.5 1.5L11 6"/>
                        </svg>
                        <strong class="norm-id">${escapeHtml(normId)}</strong>
                        ${confidence > 0 ? `<span class="confidence-badge confidence-${getConfidenceClass(confidence)}">${Math.round(confidence)}%</span>` : ''}
                        ${url ? `<svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor" class="norm-link-icon" style="margin-left: auto;">
                            <path d="M11 8v3a2 2 0 01-2 2H3a2 2 0 01-2-2V5a2 2 0 012-2h3M9 1h4v4M6 8l7-7"/>
                        </svg>` : ''}
                    </div>
                    ${title !== normId ? `<h4 class="norm-title">${escapeHtml(title)}</h4>` : ''}
                </div>
                ${description ? `<p class="norm-description">${escapeHtml(description)}</p>` : ''}
                ${reasoning ? `<p class="norm-reasoning"><em>Why it applies:</em> ${escapeHtml(reasoning)}</p>` : ''}
            </${cardTag}>
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
 * Render Q&A history as chat messages
 */
function renderQAHistory() {
    const messagesEl = document.getElementById('chatMessages');
    if (!messagesEl) return;

    const qaHistory = workspace.qa_history || [];

    if (qaHistory.length === 0) {
        messagesEl.innerHTML = `
            <div class="ns-message assistant">
                <strong>NormScout AI</strong>
                <p>Hi! I'm here to help answer questions about your product and its compliance requirements. Ask me anything!</p>
            </div>
        `;
        return;
    }

    let html = '';
    qaHistory.forEach((qa, index) => {
        // User question (purple gradient)
        html += `
            <div class="ns-message user">
                <strong>You</strong>
                <p>${escapeHtml(qa.question)}</p>
            </div>
        `;

        // AI answer (light gray)
        html += `
            <div class="ns-message assistant">
                <strong>NormScout AI</strong>
                <p>${escapeHtml(qa.answer)}</p>
            </div>
        `;
    });

    messagesEl.innerHTML = html;

    // Scroll to bottom to show latest message
    messagesEl.scrollTop = messagesEl.scrollHeight;
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
        // Highlight input briefly
        input.style.borderColor = '#ef4444';
        setTimeout(() => {
            input.style.borderColor = '';
        }, 1000);
        return;
    }

    // Disable input
    input.disabled = true;
    askBtn.disabled = true;
    const originalBtnHTML = askBtn.innerHTML;
    askBtn.innerHTML = '<span class="spinner" style="display: inline-block; width: 16px; height: 16px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.6s linear infinite;"></span> Sending...';

    // Add user message immediately to chat
    addChatMessage('user', question);

    // Clear input immediately for better UX
    input.value = '';

    // Show typing indicator
    addTypingIndicator();

    try {
        const response = await fetch(`/api/workspaces/${workspaceId}/ask`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({ question: question })
        });

        // Remove typing indicator
        removeTypingIndicator();

        if (!response.ok) {
            const data = await response.json();
            if (data.limit_exceeded) {
                addChatMessage('assistant', `⚠️ ${data.error}`);
            } else {
                throw new Error('Failed to send question');
            }
            return;
        }

        const data = await response.json();

        // Add Q&A to workspace history
        if (!workspace.qa_history) {
            workspace.qa_history = [];
        }
        workspace.qa_history.push(data.qa);
        workspace.qa_count = (workspace.qa_count || 0) + 1;

        // Add AI response to chat
        addChatMessage('assistant', data.qa.answer);

        // Check if AI proposed a product change
        if (data.proposed_description) {
            showProposedChange(data.proposed_description);
        }

        // Check if change was applied
        if (data.change_applied) {
            // Update product description display
            workspace.product.description = data.new_description;
            const descEl = document.getElementById('productDescription');
            if (descEl) {
                descEl.innerHTML = escapeHtml(data.new_description);
            }

            // Show re-analysis prompt if requested
            if (data.prompt_reanalysis) {
                showReanalysisPrompt();
            }
        }

        // Update sidebar info
        renderSidebarInfo();

    } catch (error) {
        console.error('Error asking question:', error);
        removeTypingIndicator();
        addChatMessage('assistant', '⚠️ Sorry, something went wrong. Please try again.');
    } finally {
        // Re-enable input
        input.disabled = false;
        askBtn.disabled = false;
        askBtn.innerHTML = originalBtnHTML;
        input.focus();
    }
}

/**
 * Add a chat message to the UI
 */
function addChatMessage(role, content) {
    const messagesEl = document.getElementById('chatMessages');
    if (!messagesEl) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `ns-message ${role}`;

    const label = role === 'user' ? 'You' : 'NormScout AI';
    messageDiv.innerHTML = `<strong>${label}</strong><p>${escapeHtml(content)}</p>`;

    messagesEl.appendChild(messageDiv);

    // Scroll to bottom
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

/**
 * Add typing indicator
 */
function addTypingIndicator() {
    const messagesEl = document.getElementById('chatMessages');
    if (!messagesEl) return;

    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'ns-message assistant typing-indicator';
    typingDiv.innerHTML = '<strong>NormScout AI</strong><p>is typing...</p>';

    messagesEl.appendChild(typingDiv);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

/**
 * Remove typing indicator
 */
function removeTypingIndicator() {
    const typingDiv = document.getElementById('typingIndicator');
    if (typingDiv) {
        typingDiv.remove();
    }
}

/**
 * Print workspace
 */
function exportWorkspace() {
    window.print();
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

        // Prompt user to re-run analysis since product changed
        const shouldReanalyze = confirm(
            'Product description updated! Would you like to re-run the compliance analysis with the new description?\n\n' +
            'Click OK to re-analyze now, or Cancel to keep the existing analysis.'
        );

        if (shouldReanalyze) {
            await reAnalyzeCompliance();
        } else {
            // Add a note in the chat that analysis might be outdated
            addChatMessage('assistant',
                '⚠️ Note: Your product description has been updated, but the compliance analysis is based on the previous version. ' +
                'You may want to re-analyze to ensure the norms match your current product. Ask me "Can you re-analyze my product?" to run a fresh analysis.'
            );
        }

    } catch (error) {
        console.error('Error saving description:', error);
        alert('Failed to save description. Please try again.');
        // Reload to revert changes
        await loadWorkspace();
    }
}

/**
 * Show proposed product change in chat with preview
 */
function showProposedChange(newDescription) {
    const messagesEl = document.getElementById('chatMessages');
    if (!messagesEl) return;

    const changeCard = document.createElement('div');
    changeCard.className = 'proposed-change-card';
    changeCard.innerHTML = `
        <div class="proposed-change-header">
            <strong>📝 Proposed Product Update</strong>
        </div>
        <div class="proposed-change-preview">
            <div class="change-label">New Description:</div>
            <div class="change-content">${escapeHtml(newDescription)}</div>
        </div>
        <div class="proposed-change-hint">
            💡 Just type "yes" or "apply it" to confirm this change
        </div>
    `;

    messagesEl.appendChild(changeCard);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

/**
 * Show re-analysis prompt with quick action buttons
 */
function showReanalysisPrompt() {
    const messagesEl = document.getElementById('chatMessages');
    if (!messagesEl) return;

    const promptCard = document.createElement('div');
    promptCard.className = 'reanalysis-prompt-card';
    promptCard.innerHTML = `
        <div class="reanalysis-prompt-buttons">
            <button class="btn btn-accent btn-small" onclick="triggerReanalysisFromPrompt()">
                🔄 Yes, Re-analyze Now
            </button>
            <button class="btn btn-secondary btn-small" onclick="dismissReanalysisPrompt()">
                Later
            </button>
        </div>
    `;

    messagesEl.appendChild(promptCard);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

/**
 * Trigger re-analysis from quick action button
 */
async function triggerReanalysisFromPrompt() {
    // Remove the prompt card
    const promptCard = document.querySelector('.reanalysis-prompt-card');
    if (promptCard) promptCard.remove();

    // Trigger re-analysis
    await reAnalyzeCompliance();
}

/**
 * Dismiss re-analysis prompt
 */
function dismissReanalysisPrompt() {
    const promptCard = document.querySelector('.reanalysis-prompt-card');
    if (promptCard) promptCard.remove();

    addChatMessage('assistant',
        '👍 No problem! You can always ask me to "re-analyze" later when you\'re ready.'
    );
}

/**
 * Re-analyze product compliance after description changes
 */
async function reAnalyzeCompliance() {
    // Show loading state in chat
    addChatMessage('assistant', 'Re-analyzing your product for compliance requirements...');

    try {
        // Call backend to trigger re-analysis
        const response = await fetch(`/api/workspaces/${workspaceId}/reanalyze`, {
            method: 'POST',
            credentials: 'include',
            headers: {'Content-Type': 'application/json'}
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            const errorMsg = data.error || 'Re-analysis failed';
            throw new Error(errorMsg);
        }

        // Update workspace with new analysis
        workspace.matched_norms = data.matched_norms;
        workspace.analysis = data.analysis;

        // Re-render compliance results
        renderComplianceResults();

        // Notify success in chat
        addChatMessage('assistant',
            `✅ Re-analysis complete! Found ${data.matched_norms.length} applicable compliance norms based on your updated product description.`
        );

        // Update norms count
        const normsCountEl = document.getElementById('normsCount');
        if (normsCountEl) {
            normsCountEl.textContent = `${data.matched_norms.length}`;
        }

    } catch (error) {
        console.error('Error re-analyzing:', error);
        addChatMessage('assistant',
            `⚠️ ${error.message || 'Sorry, I encountered an error while re-analyzing your product. Please try again or ask me a question about your current analysis.'}`
        );
    }
}

/**
 * Handle Enter key in question input (send on Enter, new line on Shift+Enter)
 */
document.addEventListener('DOMContentLoaded', function() {
    const questionInput = document.getElementById('questionInput');
    if (questionInput) {
        questionInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
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
