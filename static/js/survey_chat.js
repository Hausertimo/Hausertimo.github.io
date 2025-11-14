/**
 * Survey Chat Interface
 * Public-facing conversational survey
 */

let conversationId = null;
let surveyId = null;
let isProcessing = false;
let completionPercentage = 0;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Get survey ID from data attribute
    const surveyData = document.getElementById('surveyData');
    surveyId = surveyData.dataset.surveyId;

    // Start the survey
    startSurvey();

    // Setup enter key
    document.getElementById('userInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

// ============================================================================
// SURVEY FLOW
// ============================================================================

async function startSurvey() {
    try {
        showTyping();

        const response = await fetch('/api/survey/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                survey_id: surveyId,
                session_identifier: generateSessionId()
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to start survey');
        }

        const data = await response.json();
        conversationId = data.conversation_id;

        hideTyping();

        // Display welcome message
        await addMessageWithDelay('assistant', data.welcome_message, 500);

        // Display first question
        await addMessageWithDelay('assistant', data.first_question, 1000);

        // Enable input
        enableInput();

    } catch (error) {
        console.error('Error starting survey:', error);
        hideTyping();
        addMessage('assistant', 'Sorry, there was an error starting the survey. Please refresh the page and try again.');
    }
}

async function sendMessage() {
    const input = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const message = input.value.trim();

    if (!message || isProcessing || !conversationId) return;

    // Disable input
    isProcessing = true;
    input.disabled = true;
    sendBtn.disabled = true;

    // Add user message
    addMessage('user', message);
    input.value = '';

    // Show typing
    showTyping();

    try {
        const response = await fetch('/api/survey/message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                conversation_id: conversationId,
                message: message
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to send message');
        }

        const data = await response.json();

        hideTyping();

        // Update progress
        if (data.completion_percentage !== undefined) {
            updateProgress(data.completion_percentage);
        }

        // Add AI response
        await addMessageWithDelay('assistant', data.response, 500);

        if (data.completed) {
            // Survey complete!
            completeSurvey(data.gathered_data, data.response);
        } else {
            // Re-enable input
            enableInput();
        }

    } catch (error) {
        console.error('Error sending message:', error);
        hideTyping();
        addMessage('assistant', 'Sorry, there was an error processing your response. Please try again.');
        enableInput();
    }
}

function completeSurvey(gatheredData, completionMessage) {
    // Hide input
    document.getElementById('inputContainer').style.display = 'none';

    // Show completion view
    setTimeout(() => {
        document.getElementById('chatMessages').style.display = 'none';

        const completionView = document.getElementById('completionView');
        const completionMsg = document.getElementById('completionMessage');
        const completionSummary = document.getElementById('completionSummary');

        completionMsg.textContent = completionMessage || 'Thank you for completing the survey!';

        // Show gathered data
        let summaryHtml = '<h3>Your Responses:</h3>';
        if (gatheredData && Object.keys(gatheredData).length > 0) {
            summaryHtml += '<div>';
            for (const [key, value] of Object.entries(gatheredData)) {
                summaryHtml += `
                    <div class="data-item">
                        <span class="data-label">${escapeHtml(key)}</span>
                        <span class="data-value">${escapeHtml(String(value))}</span>
                    </div>
                `;
            }
            summaryHtml += '</div>';
        }

        completionSummary.innerHTML = summaryHtml;
        completionView.style.display = 'flex';

        // Confetti effect (optional)
        updateProgress(100);
    }, 1000);
}

// ============================================================================
// UI HELPERS
// ============================================================================

function addMessage(role, content) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message';

    const isAssistant = role === 'assistant';

    messageDiv.innerHTML = `
        <div class="message-${role}">
            <div class="message-avatar avatar-${role}">
                ${isAssistant ? 'AI' : 'You'}
            </div>
            <div class="message-bubble bubble-${role}">
                ${escapeHtml(content)}
            </div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

async function addMessageWithDelay(role, content, delay) {
    return new Promise(resolve => {
        setTimeout(() => {
            addMessage(role, content);
            resolve();
        }, delay);
    });
}

function showTyping() {
    document.getElementById('typingIndicator').style.display = 'flex';
    scrollToBottom();
}

function hideTyping() {
    document.getElementById('typingIndicator').style.display = 'none';
}

function enableInput() {
    const input = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');

    input.disabled = false;
    sendBtn.disabled = false;
    input.focus();
    isProcessing = false;
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

function updateProgress(percentage) {
    completionPercentage = percentage;

    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    progressFill.style.width = percentage + '%';
    progressText.textContent = Math.round(percentage) + '% Complete';
}

// ============================================================================
// UTILITIES
// ============================================================================

function generateSessionId() {
    // Simple session identifier (could use fingerprinting library)
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
