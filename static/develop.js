/**
 * Modern /develop page - Chat-based workspace creation
 * Uses same logic as landing page teaser chat but for logged-in users
 */

// Global variables to store session state
let developSessionId = null;
let waitingForWorkspaceName = false;

/**
 * Send message in develop chat
 */
async function sendDevelopMessage() {
    const input = document.getElementById('developProductInput');
    const message = input.value.trim();

    if (!message) {
        // Highlight the input field
        input.style.borderColor = '#ef4444';
        setTimeout(() => {
            input.style.borderColor = '';
        }, 1000);
        return;
    }

    // Disable input and button
    const sendBtn = document.getElementById('developSendBtn');
    input.disabled = true;
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';

    // Add user message to chat
    addDevelopMessage('user', message);
    input.value = '';

    // Show typing indicator
    addDevelopTypingIndicator();

    try {
        let response, data;

        // If we already have a session, continue the conversation
        if (developSessionId) {
            response = await fetch('/api/develope/respond', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: developSessionId,
                    message: message
                })
            });
        } else {
            // First message - start new conversation
            response = await fetch('/api/develope/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({initial_input: message})
            });
        }

        data = await response.json();

        // Remove typing indicator
        removeDevelopTypingIndicator();

        if (data.error) {
            addDevelopMessage('assistant', 'Error: ' + data.error);
        } else {
            // Store session ID
            if (data.session_id) {
                developSessionId = data.session_id;
            }

            // Add AI response
            addDevelopMessage('assistant', data.message);

            // Check if AI has enough info to generate report
            if (data.complete) {
                // AI is ready! User is already logged in since /develop is protected
                waitingForWorkspaceName = true;

                // Hide the chat input container
                const inputContainer = document.getElementById('developInputContainer');
                if (inputContainer) {
                    inputContainer.style.display = 'none';
                }

                // Show workspace name input
                const workspaceNameContainer = document.getElementById('developWorkspaceNameContainer');
                if (workspaceNameContainer) {
                    workspaceNameContainer.style.display = 'flex';
                }

                // Add a clear follow-up prompt for workspace name
                addDevelopMessage('assistant', 'What would you like to name your workspace?');
            } else {
                // AI needs more info, keep chatting
                sendBtn.textContent = 'Send';
            }
        }
    } catch (error) {
        console.error('Error:', error);
        removeDevelopTypingIndicator();
        addDevelopMessage('assistant', 'Sorry, something went wrong. Please try again.');
    } finally {
        // Re-enable input and button
        input.disabled = false;
        sendBtn.disabled = false;

        // Update button text
        if (!developSessionId) {
            sendBtn.textContent = 'Start Chat';
        } else {
            sendBtn.textContent = 'Send';
        }
    }
}

/**
 * Add message to develop chat
 */
function addDevelopMessage(role, content) {
    const messagesDiv = document.getElementById('developChatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `teaser-message teaser-${role}`;

    const label = role === 'user' ? 'You' : 'NormScout AI';
    messageDiv.innerHTML = `<strong>${label}</strong><p>${content}</p>`;

    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

/**
 * Add typing indicator to develop chat
 */
function addDevelopTypingIndicator() {
    const messagesDiv = document.getElementById('developChatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.id = 'developTypingIndicator';
    typingDiv.className = 'teaser-message teaser-assistant typing-indicator';
    typingDiv.innerHTML = `<strong>NormScout AI</strong><p>is typing...</p>`;
    messagesDiv.appendChild(typingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

/**
 * Remove typing indicator from develop chat
 */
function removeDevelopTypingIndicator() {
    const typingDiv = document.getElementById('developTypingIndicator');
    if (typingDiv) {
        typingDiv.remove();
    }
}

/**
 * Create workspace from develop session
 */
async function createWorkspaceFromDevelop() {
    const workspaceNameInput = document.getElementById('developWorkspaceName');
    const workspaceName = workspaceNameInput.value.trim();

    if (!workspaceName) {
        // Highlight the input field
        workspaceNameInput.style.borderColor = '#ef4444';
        setTimeout(() => {
            workspaceNameInput.style.borderColor = '';
        }, 1000);
        return;
    }

    if (!developSessionId) {
        addDevelopMessage('assistant', 'Sorry, I couldn\'t find your session. Please refresh and try again.');
        return;
    }

    // Get UI elements
    const workspaceNameContainer = document.getElementById('developWorkspaceNameContainer');
    const progressBtn = document.getElementById('developProgressBtn');
    const progressBar = document.getElementById('developProgressBar');
    const progressText = document.getElementById('developProgressText');

    try {
        // Step 1: Run the norm analysis
        addDevelopMessage('assistant', 'Analyzing your product for compliance requirements...');

        // Hide workspace name input, show progress button
        if (workspaceNameContainer) workspaceNameContainer.style.display = 'none';
        if (progressBtn) {
            progressBtn.style.display = 'block';
            progressBtn.disabled = true;
            progressBtn.classList.add('analyzing');
        }
        if (progressText) progressText.textContent = 'Starting analysis...';
        if (progressBar) progressBar.style.width = '0%';

        // Connect to analysis stream
        const eventSource = new EventSource(`/api/develope/analyze-stream?session_id=${developSessionId}`);

        let analysisComplete = false;
        let analysisResults = null;

        await new Promise((resolve, reject) => {
            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);

                if (data.phase === 'analyzing') {
                    // Update progress bar
                    const progressPercent = Math.round((data.progress / data.total) * 100);
                    if (progressBar) progressBar.style.width = `${progressPercent}%`;
                    if (progressText) progressText.textContent = `Analyzing compliance norms... ${progressPercent}%`;
                }
                else if (data.phase === 'complete') {
                    // Analysis done!
                    analysisComplete = true;
                    analysisResults = data;
                    eventSource.close();
                    if (progressBar) progressBar.style.width = '100%';
                    if (progressText) progressText.textContent = 'Analysis complete!';
                    resolve();
                }
                else if (data.phase === 'error') {
                    eventSource.close();
                    reject(new Error(data.error || 'Analysis failed'));
                }
            };

            eventSource.onerror = function(error) {
                eventSource.close();
                reject(new Error('Connection to analysis service failed'));
            };
        });

        if (!analysisComplete) {
            throw new Error('Analysis did not complete successfully');
        }

        // Step 2: Create workspace with analysis results
        addDevelopMessage('assistant', `Found ${analysisResults.total_norms} relevant compliance norms! Creating your workspace...`);

        if (progressText) progressText.textContent = 'Creating workspace...';

        // Get session data (now includes analysis results)
        const sessionResponse = await fetch(`/api/develope/session/${developSessionId}`, {
            credentials: 'include'
        });

        if (!sessionResponse.ok) {
            const errorData = await sessionResponse.json().catch(() => ({}));
            throw new Error(errorData.error || 'Failed to get session data');
        }

        const sessionData = await sessionResponse.json();

        // Create workspace with analysis data
        const response = await fetch('/api/workspaces/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({
                name: workspaceName,
                product_description: sessionData.product_description || sessionData.history?.[0]?.content || workspaceName,
                matched_norms: sessionData.matched_norms || [],
                all_results: sessionData.all_norm_results || {}
            })
        });

        const data = await response.json();

        if (!response.ok) {
            if (data.limit_exceeded) {
                addDevelopMessage('assistant', `Sorry, ${data.error}`);
                // Reset UI
                if (progressBtn) progressBtn.style.display = 'none';
                if (workspaceNameContainer) workspaceNameContainer.style.display = 'flex';
                return;
            }
            throw new Error(data.error || 'Failed to create workspace');
        }

        // Success! Show confirmation and redirect
        addDevelopMessage('assistant', `Perfect! "${workspaceName}" has been created with ${analysisResults.total_norms} compliance norms. Redirecting...`);

        if (progressText) progressText.textContent = 'Complete! Redirecting...';

        // Clear session from localStorage since we're done with it
        localStorage.removeItem('teaserSessionId');
        localStorage.removeItem('redirectAfterLogin');

        // Redirect to workspace after a short delay
        setTimeout(() => {
            window.location.href = `/workspace/${data.workspace.id}`;
        }, 1500);

    } catch (error) {
        console.error('Error creating workspace:', error);
        addDevelopMessage('assistant', `Oops! Something went wrong: ${error.message}. Please try again.`);

        // Reset UI state
        if (progressBtn) {
            progressBtn.style.display = 'none';
            progressBtn.classList.remove('analyzing');
            progressBtn.disabled = false;
        }
        if (progressBar) progressBar.style.width = '0%';
        if (progressText) progressText.textContent = 'Analyzing...';
        if (workspaceNameContainer) workspaceNameContainer.style.display = 'flex';
    }
}

/**
 * Restore session from localStorage if available
 */
async function restoreSession() {
    const savedSessionId = localStorage.getItem('teaserSessionId');

    if (!savedSessionId) {
        return; // No saved session
    }

    try {
        // Fetch session data
        const response = await fetch(`/api/develope/session/${savedSessionId}`, {
            credentials: 'include'
        });

        if (!response.ok) {
            // Session not found or expired, clear localStorage
            localStorage.removeItem('teaserSessionId');
            localStorage.removeItem('redirectAfterLogin');
            return;
        }

        const sessionData = await response.json();

        // Restore session ID
        developSessionId = savedSessionId;

        // Display conversation history
        if (sessionData.history && sessionData.history.length > 0) {
            // Clear the welcome message
            const messagesDiv = document.getElementById('developChatMessages');
            messagesDiv.innerHTML = '';

            // Add all messages from history
            sessionData.history.forEach(msg => {
                addDevelopMessage(msg.role === 'user' ? 'user' : 'assistant', msg.content);
            });
        }

        // If conversation was complete, show workspace name input
        if (sessionData.conversation_complete || sessionData.matched_norms) {
            waitingForWorkspaceName = true;

            // Hide the chat input container
            const inputContainer = document.getElementById('developInputContainer');
            if (inputContainer) {
                inputContainer.style.display = 'none';
            }

            // Show workspace name input
            const workspaceNameContainer = document.getElementById('developWorkspaceNameContainer');
            if (workspaceNameContainer) {
                workspaceNameContainer.style.display = 'flex';
            }

            // Add a message prompting for workspace name
            addDevelopMessage('assistant', 'Welcome back! What would you like to name your workspace?');
        }

        // Clear the redirect flag
        localStorage.removeItem('redirectAfterLogin');

    } catch (error) {
        console.error('Error restoring session:', error);
        // Clear invalid session
        localStorage.removeItem('teaserSessionId');
        localStorage.removeItem('redirectAfterLogin');
    }
}

// Allow Enter key to send message
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('developProductInput');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendDevelopMessage();
            }
        });
    }

    const workspaceNameInput = document.getElementById('developWorkspaceName');
    if (workspaceNameInput) {
        workspaceNameInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                createWorkspaceFromDevelop();
            }
        });
    }

    // Restore session if available
    restoreSession();
});
