/**
 * NormScout Develope Page - AI Product Compliance Workspace
 * Handles conversation flow, analysis, and workspace creation
 */

// Session state
let sessionId = null;
let conversationComplete = false;
let analysisComplete = false;

// Load existing session if coming from landing page
window.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const incomingSessionId = urlParams.get('session_id');

    if (incomingSessionId) {
        loadExistingSession(incomingSessionId);
    }
});

async function loadExistingSession(incomingSessionId) {
    try {
        const response = await fetch(`/api/develope/session/${incomingSessionId}`);
        const sessionData = await response.json();

        if (sessionData.error) {
            console.error('Error loading session:', sessionData.error);
            addMessage('assistant', 'Welcome back! It looks like your session expired. Please start a new conversation.');
            return;
        }

        sessionId = incomingSessionId;
        conversationComplete = sessionData.complete || false;

        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';

        if (sessionData.history && sessionData.history.length > 0) {
            sessionData.history.forEach(msg => {
                addMessage(msg.role, msg.content);
            });
        }

        if (conversationComplete) {
            showAnalyzeButton();
        }

        document.getElementById('userInput').focus();

    } catch (error) {
        console.error('Error loading session:', error);
        addMessage('assistant', 'Sorry, I couldn\'t load your previous conversation. Please start fresh!');
    }
}

// Send message on Enter key
document.getElementById('userInput')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();

    if (!message) return;

    input.disabled = true;
    document.getElementById('sendBtn').disabled = true;

    addMessage('user', message);
    input.value = '';

    try {
        if (analysisComplete) {
            await askAnalysisQuestion(message);
        }
        else if (!sessionId) {
            const response = await fetch('/api/develope/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({initial_input: message})
            });

            const data = await response.json();

            if (data.error) {
                addMessage('assistant', 'Error: ' + data.error);
            } else {
                sessionId = data.session_id;
                addMessage('assistant', data.message);

                if (data.complete) {
                    conversationComplete = true;
                    showAnalyzeButton();
                }
            }
        } else {
            const response = await fetch('/api/develope/respond', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: sessionId,
                    message: message
                })
            });

            const data = await response.json();

            if (data.error) {
                addMessage('assistant', 'Error: ' + data.error);
            } else {
                addMessage('assistant', data.message);

                if (data.complete) {
                    conversationComplete = true;
                    showAnalyzeButton();
                }
            }
        }
    } catch (error) {
        console.error('Error:', error);
        addMessage('assistant', 'Sorry, something went wrong. Please try again.');
    }

    input.disabled = false;
    document.getElementById('sendBtn').disabled = false;
    input.focus();
}

function addMessage(role, content) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ' + role;

    const label = role === 'user' ? 'You' : 'NormScout AI';
    messageDiv.innerHTML = `<strong>${label}</strong><p>${content}</p>`;

    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function showAnalyzeButton() {
    document.getElementById('analyzeBtn').style.display = 'block';
    document.getElementById('userInput').disabled = true;
    document.getElementById('sendBtn').disabled = true;
}

async function askAnalysisQuestion(question) {
    try {
        const response = await fetch('/api/develope/ask-analysis', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: sessionId,
                question: question
            })
        });

        const data = await response.json();

        if (data.error) {
            addMessage('assistant', 'Error: ' + data.error);
        } else {
            addMessage('assistant', data.answer);

            if (data.relevant_norms && data.relevant_norms.length > 0) {
                console.log('Relevant norms:', data.relevant_norms);
            }
        }
    } catch (error) {
        console.error('Q&A Error:', error);
        addMessage('assistant', 'Sorry, I had trouble answering that question. Please try again.');
    }
}

async function analyzeNorms() {
    if (!sessionId || !conversationComplete) return;

    const analyzeBtn = document.getElementById('analyzeBtn');
    const btnText = document.getElementById('analyzeBtnText');
    const btnProgress = document.getElementById('analyzeBtnProgress');

    analyzeBtn.disabled = true;
    analyzeBtn.classList.add('analyzing');
    btnText.textContent = 'Starting analysis...';
    btnProgress.style.width = '0%';

    try {
        const eventSource = new EventSource('/api/develope/analyze-stream?' + new URLSearchParams({
            session_id: sessionId
        }));

        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);

            if (data.phase === 'summary') {
                btnText.textContent = data.status;
                btnProgress.style.width = '5%';
            }
            else if (data.phase === 'analyzing') {
                btnText.textContent = data.status;
                const progressPercent = 5 + ((data.progress / data.total) * 90);
                btnProgress.style.width = progressPercent + '%';
            }
            else if (data.phase === 'finalizing') {
                btnText.textContent = data.status;
                btnProgress.style.width = '95%';
            }
            else if (data.phase === 'complete') {
                btnText.textContent = 'Complete!';
                btnProgress.style.width = '100%';
                eventSource.close();

                displayResults(data);

                setTimeout(() => {
                    analyzeBtn.classList.remove('analyzing');
                    analyzeBtn.disabled = false;
                    btnText.textContent = 'Analyze Compliance Norms';
                    btnProgress.style.width = '0%';
                }, 1000);
            }
            else if (data.phase === 'error') {
                eventSource.close();
                alert('Error: ' + data.error);

                analyzeBtn.classList.remove('analyzing');
                analyzeBtn.disabled = false;
                btnText.textContent = 'Analyze Compliance Norms';
                btnProgress.style.width = '0%';
            }
        };

        eventSource.onerror = function(error) {
            console.error('SSE Error:', error);
            eventSource.close();
            alert('Connection error during analysis. Please try again.');

            analyzeBtn.classList.remove('analyzing');
            analyzeBtn.disabled = false;
            btnText.textContent = 'Analyze Compliance Norms';
            btnProgress.style.width = '0%';
        };

    } catch (error) {
        console.error('Error:', error);
        alert('Sorry, something went wrong during analysis.');

        analyzeBtn.classList.remove('analyzing');
        analyzeBtn.disabled = false;
        btnText.textContent = 'Analyze Compliance Norms';
        btnProgress.style.width = '0%';
    }
}

function displayResults(data) {
    document.getElementById('resultsContainer').classList.add('visible');

    const formattedDescription = formatProductDescription(data.product_description);

    document.getElementById('productDescription').innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3>Product Description</h3>
        </div>
        <div id="productDescText" style="line-height: 1.8; color: var(--text-dark);" data-raw="${data.product_description.replace(/"/g, '&quot;')}">
            ${formattedDescription}
        </div>
    `;

    document.getElementById('normsCount').textContent = data.total_norms;

    const normsList = document.getElementById('normsList');
    normsList.innerHTML = '';

    if (data.norms.length === 0) {
        normsList.innerHTML = '<p>No applicable norms found.</p>';
    } else {
        data.norms.forEach(norm => {
            const normDiv = document.createElement('div');
            normDiv.className = 'norm-item';

            let confidenceClass = 'high';
            if (norm.confidence < 80) confidenceClass = 'medium';
            if (norm.confidence < 60) confidenceClass = 'low';

            normDiv.innerHTML = `
                <div class="norm-header">
                    <div class="norm-title">${norm.norm_name} ${norm.url ? '🔗' : ''}</div>
                    <div class="confidence-badge ${confidenceClass}">${norm.confidence}%</div>
                </div>
                <div class="norm-id">ID: ${norm.norm_id}</div>
                <div class="norm-reasoning">${norm.reasoning}</div>
            `;

            if (norm.url) {
                normDiv.classList.add('clickable');
                normDiv.onclick = () => window.open(norm.url, '_blank');
                normDiv.title = 'Click to view official document';
            }

            normsList.appendChild(normDiv);
        });
    }

    document.getElementById('resultsContainer').scrollIntoView({behavior: 'smooth'});

    analysisComplete = true;

    document.getElementById('userInput').disabled = false;
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('userInput').placeholder =
        "Ask questions about the analysis (e.g., 'Why does this norm apply?')";
    document.getElementById('userInput').focus();

    addMessage('assistant',
        '✓ Analysis complete! Ask me questions about the results.');

    document.getElementById('createWorkspaceBtn').style.display = 'block';
}

function formatProductDescription(description) {
    if (!description) return '';

    try {
        let formatted = description;

        formatted = formatted.replace(/^([A-Z\s]{3,}:)/gm, '<h4 style="color: var(--brand-blue); margin-top: 1.5rem; margin-bottom: 0.75rem; font-size: 1rem; font-weight: 700;">$1</h4>');
        formatted = formatted.replace(/^(\d+\.\s+[A-Z][a-zA-Z\s&\/]+)/gm, '<h5 style="color: var(--text-dark); margin-top: 1rem; margin-bottom: 0.5rem; font-size: 0.95rem; font-weight: 600;">$1</h5>');
        formatted = formatted.replace(/^([A-Z][a-zA-Z\s&\/]+:)(?=\s*\n|$)/gm, '<h5 style="color: var(--text-dark); margin-top: 1rem; margin-bottom: 0.5rem; font-size: 0.95rem; font-weight: 600;">$1</h5>');
        formatted = formatted.replace(/^\s*\*\s+(.+)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/^\s*-\s+(.+)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/(<li>.*?<\/li>\n?)+/g, function(match) {
            return '<ul style="margin: 0.5rem 0 1rem 1.5rem; padding-left: 1rem;">' + match + '</ul>';
        });
        formatted = formatted.replace(/\n\n+/g, '</p><p style="margin-bottom: 0.75rem;">');
        formatted = formatted.replace(/\n/g, '<br>');

        if (!formatted.startsWith('<h4') && !formatted.startsWith('<h5') && !formatted.startsWith('<ul') && !formatted.startsWith('<p')) {
            formatted = '<p style="margin-bottom: 0.75rem;">' + formatted + '</p>';
        }

        formatted = formatted.replace(/<p[^>]*>\s*<\/p>/g, '');

        return formatted;
    } catch (error) {
        console.error('Error formatting description:', error);
        return '<pre style="white-space: pre-wrap; font-family: inherit;">' + description + '</pre>';
    }
}

async function createWorkspace() {
    if (!analysisComplete) {
        alert('Please complete the analysis first');
        return;
    }

    const btn = document.getElementById('createWorkspaceBtn');
    const originalText = btn.innerHTML;

    btn.disabled = true;
    btn.innerHTML = '<span class="analyze-btn-text">Creating workspace...</span>';

    try {
        const response = await fetch('/api/workspace/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_id: sessionId})
        });

        const data = await response.json();

        if (data.error) {
            alert('Error creating workspace: ' + data.error);
            btn.disabled = false;
            btn.innerHTML = originalText;
        } else {
            window.location.href = data.url;
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Sorry, something went wrong creating the workspace.');
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}
