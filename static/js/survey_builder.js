/**
 * Survey Builder Admin Interface
 * Manage AI-powered conversational surveys
 */

let currentSurveyId = null;
let currentSurvey = null;
let topics = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadSurveys();

    // Setup form submission
    document.getElementById('surveyForm').addEventListener('submit', handleSubmit);

    // Enter key in input field
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.target.id === 'userInput') {
            sendMessage();
        }
    });

    // Add first topic by default
    addTopic();
});

// ============================================================================
// SURVEY MANAGEMENT
// ============================================================================

async function loadSurveys() {
    const loading = document.getElementById('surveysLoading');
    const empty = document.getElementById('surveysEmpty');
    const grid = document.getElementById('surveysGrid');
    const count = document.getElementById('surveyCount');

    loading.style.display = 'flex';
    empty.style.display = 'none';
    grid.style.display = 'none';

    try {
        const response = await fetch('/api/survey/configs');
        if (!response.ok) throw new Error('Failed to load surveys');

        const data = await response.json();
        const surveys = data.surveys || [];

        loading.style.display = 'none';
        count.textContent = surveys.length;

        if (surveys.length === 0) {
            empty.style.display = 'flex';
        } else {
            grid.style.display = 'grid';
            renderSurveys(surveys);
        }
    } catch (error) {
        console.error('Error loading surveys:', error);
        loading.style.display = 'none';
        empty.style.display = 'flex';
    }
}

function renderSurveys(surveys) {
    const grid = document.getElementById('surveysGrid');
    grid.innerHTML = '';

    surveys.forEach(survey => {
        const card = createSurveyCard(survey);
        grid.appendChild(card);
    });
}

function createSurveyCard(survey) {
    const card = document.createElement('div');
    card.className = 'survey-card';
    card.onclick = () => viewSurvey(survey.id);

    const statusClass = survey.is_active ? 'survey-status-active' : 'survey-status-inactive';
    const statusText = survey.is_active ? 'Active' : 'Inactive';

    const createdDate = new Date(survey.created_at).toLocaleDateString();

    card.innerHTML = `
        <div class="survey-card-header">
            <h3 class="survey-card-title">${escapeHtml(survey.name)}</h3>
            <span class="survey-status-badge ${statusClass}">${statusText}</span>
        </div>
        ${survey.description ? `<p style="color: #666666; font-size: 14px; margin: 8px 0 0 0;">${escapeHtml(survey.description)}</p>` : ''}
        <div class="survey-card-meta">
            <span>
                <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 2a6 6 0 100 12A6 6 0 008 2zm1 9H7V7h2v4zm0-5H7V5h2v1z"/>
                </svg>
                Created ${createdDate}
            </span>
            <span>
                <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M3 2h10v12H3V2zm2 2v8h6V4H5z"/>
                </svg>
                ${survey.response_count || 0} responses
            </span>
        </div>
    `;

    return card;
}

// ============================================================================
// CREATE/EDIT SURVEY
// ============================================================================

function showCreateSurvey() {
    currentSurveyId = null;
    currentSurvey = null;
    topics = [];

    document.getElementById('modalTitle').textContent = 'Create New Survey';
    document.getElementById('submitBtnText').textContent = 'Create Survey';
    document.getElementById('surveyForm').reset();
    document.getElementById('temperatureValue').textContent = '0.7';
    document.getElementById('topicsList').innerHTML = '';

    // Add default topics
    addTopic();

    document.getElementById('surveyModal').style.display = 'flex';
}

function hideSurveyModal() {
    document.getElementById('surveyModal').style.display = 'none';
}

function updateTemperature(value) {
    document.getElementById('temperatureValue').textContent = value;
}

function addTopic() {
    const topicId = Date.now();
    const topicItem = document.createElement('div');
    topicItem.className = 'topic-item';
    topicItem.dataset.id = topicId;

    topicItem.innerHTML = `
        <div class="topic-drag-handle">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M2 4h12M2 8h12M2 12h12"/>
            </svg>
        </div>
        <div class="topic-fields">
            <input type="text" class="topic-name-input" placeholder="e.g., Name, Email, Age..." required>
            <label class="topic-mandatory">
                <input type="checkbox" checked>
                <span>Mandatory</span>
            </label>
        </div>
        <button type="button" class="topic-remove" onclick="removeTopic(${topicId})">Remove</button>
    `;

    document.getElementById('topicsList').appendChild(topicItem);
    topics.push({ id: topicId });
}

function removeTopic(topicId) {
    const item = document.querySelector(`[data-id="${topicId}"]`);
    if (item) {
        item.remove();
        topics = topics.filter(t => t.id !== topicId);
    }

    // Ensure at least one topic
    if (topics.length === 0) {
        addTopic();
    }
}

function collectTopics() {
    const topicItems = document.querySelectorAll('.topic-item');
    const collectedTopics = [];

    topicItems.forEach((item, index) => {
        const nameInput = item.querySelector('.topic-name-input');
        const mandatoryInput = item.querySelector('input[type="checkbox"]');

        if (nameInput && nameInput.value.trim()) {
            collectedTopics.push({
                name: nameInput.value.trim(),
                mandatory: mandatoryInput.checked,
                order: index + 1
            });
        }
    });

    return collectedTopics;
}

async function handleSubmit(e) {
    e.preventDefault();

    const topics = collectTopics();

    if (topics.length === 0) {
        alert('Please add at least one topic');
        return;
    }

    const surveyData = {
        name: document.getElementById('surveyName').value.trim(),
        description: document.getElementById('surveyDescription').value.trim(),
        model: document.getElementById('modelSelect').value,
        temperature: parseFloat(document.getElementById('temperatureSlider').value),
        character_prompt: document.getElementById('characterPrompt').value.trim(),
        survey_explanation: document.getElementById('surveyExplanation').value.trim(),
        topics: topics
    };

    const submitBtn = document.getElementById('submitBtnText');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Saving...';

    try {
        let response;

        if (currentSurveyId) {
            // Update existing survey
            response = await fetch(`/api/survey/config/${currentSurveyId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(surveyData)
            });
        } else {
            // Create new survey
            response = await fetch('/api/survey/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(surveyData)
            });
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save survey');
        }

        hideSurveyModal();
        loadSurveys();

        alert(currentSurveyId ? 'Survey updated successfully!' : 'Survey created successfully!');
    } catch (error) {
        console.error('Error saving survey:', error);
        alert('Error: ' + error.message);
    } finally {
        submitBtn.textContent = originalText;
    }
}

// ============================================================================
// VIEW SURVEY
// ============================================================================

async function viewSurvey(surveyId) {
    try {
        const response = await fetch(`/api/survey/config/${surveyId}`);
        if (!response.ok) throw new Error('Failed to load survey');

        const survey = await response.json();
        currentSurvey = survey;
        currentSurveyId = survey.id;

        // Load responses
        const responsesRes = await fetch(`/api/survey/responses/${surveyId}`);
        const responsesData = await responsesRes.json();
        const responses = responsesData.responses || [];

        // Load stats
        const statsRes = await fetch(`/api/survey/stats/${surveyId}`);
        const stats = await statsRes.json();

        renderSurveyDetails(survey, responses, stats);

        // Update toggle button
        const toggleBtn = document.getElementById('toggleStatusBtn');
        toggleBtn.textContent = survey.is_active ? 'Deactivate' : 'Activate';

        document.getElementById('viewSurveyModal').style.display = 'flex';
    } catch (error) {
        console.error('Error loading survey:', error);
        alert('Failed to load survey details');
    }
}

function renderSurveyDetails(survey, responses, stats) {
    document.getElementById('viewSurveyName').textContent = survey.name;

    const topics = typeof survey.topics === 'string' ? JSON.parse(survey.topics) : survey.topics;

    const content = document.getElementById('viewSurveyContent');
    content.innerHTML = `
        <div class="form-section" style="margin-bottom: 24px;">
            <h3 style="color: #2048D5; margin-bottom: 16px;">Survey Configuration</h3>
            <div style="display: grid; gap: 12px;">
                <div><strong>Model:</strong> ${escapeHtml(survey.model)}</div>
                <div><strong>Temperature:</strong> ${survey.temperature}</div>
                <div><strong>Status:</strong> <span style="color: ${survey.is_active ? '#16a34a' : '#dc2626'}">${survey.is_active ? 'Active' : 'Inactive'}</span></div>
            </div>
        </div>

        <div class="form-section" style="margin-bottom: 24px;">
            <h3 style="color: #2048D5; margin-bottom: 16px;">Topics (${topics.length})</h3>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                ${topics.map(t => `
                    <div style="padding: 8px 12px; background: white; border-radius: 6px; display: flex; justify-content: space-between;">
                        <span>${escapeHtml(t.name)}</span>
                        <span style="color: ${t.mandatory ? '#16a34a' : '#666'}">${t.mandatory ? 'Mandatory' : 'Optional'}</span>
                    </div>
                `).join('')}
            </div>
        </div>

        <div class="form-section" style="margin-bottom: 24px;">
            <h3 style="color: #2048D5; margin-bottom: 16px;">Statistics</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px;">
                <div style="text-align: center; padding: 16px; background: white; border-radius: 8px;">
                    <div style="font-size: 32px; font-weight: 700; color: #3869FA;">${stats.total_conversations || 0}</div>
                    <div style="font-size: 13px; color: #666;">Total</div>
                </div>
                <div style="text-align: center; padding: 16px; background: white; border-radius: 8px;">
                    <div style="font-size: 32px; font-weight: 700; color: #16a34a;">${stats.completed || 0}</div>
                    <div style="font-size: 13px; color: #666;">Completed</div>
                </div>
                <div style="text-align: center; padding: 16px; background: white; border-radius: 8px;">
                    <div style="font-size: 32px; font-weight: 700; color: #f59e0b;">${stats.in_progress || 0}</div>
                    <div style="font-size: 13px; color: #666;">In Progress</div>
                </div>
                <div style="text-align: center; padding: 16px; background: white; border-radius: 8px;">
                    <div style="font-size: 32px; font-weight: 700; color: #3869FA;">${stats.avg_completion_rate || 0}%</div>
                    <div style="font-size: 13px; color: #666;">Avg Completion</div>
                </div>
            </div>
        </div>

        <div class="form-section">
            <h3 style="color: #2048D5; margin-bottom: 16px;">Recent Responses (${responses.length})</h3>
            ${responses.length === 0 ? '<p style="color: #666;">No responses yet</p>' : `
                <div style="max-height: 300px; overflow-y: auto;">
                    ${responses.slice(0, 10).map(r => {
                        const data = typeof r.gathered_data === 'string' ? JSON.parse(r.gathered_data) : r.gathered_data;
                        const date = new Date(r.started_at).toLocaleString();
                        return `
                            <div style="padding: 12px; background: white; border-radius: 8px; margin-bottom: 8px; border: 1px solid #e0e0e0;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                    <span style="font-weight: 600; font-size: 13px;">${date}</span>
                                    <span style="font-size: 13px; color: ${r.status === 'completed' ? '#16a34a' : '#f59e0b'}">${r.status}</span>
                                </div>
                                ${Object.entries(data || {}).length > 0 ? `
                                    <div style="font-size: 13px; color: #666;">
                                        ${Object.entries(data).slice(0, 3).map(([k, v]) => `<div><strong>${k}:</strong> ${escapeHtml(String(v))}</div>`).join('')}
                                        ${Object.entries(data).length > 3 ? `<div style="margin-top: 4px; font-style: italic;">+ ${Object.entries(data).length - 3} more...</div>` : ''}
                                    </div>
                                ` : '<div style="font-size: 13px; color: #999;">No data gathered yet</div>'}
                            </div>
                        `;
                    }).join('')}
                </div>
            `}
        </div>
    `;
}

function hideViewSurveyModal() {
    document.getElementById('viewSurveyModal').style.display = 'none';
    currentSurvey = null;
    currentSurveyId = null;
}

function editCurrentSurvey() {
    if (!currentSurvey) return;

    hideViewSurveyModal();

    // Populate form
    document.getElementById('modalTitle').textContent = 'Edit Survey';
    document.getElementById('submitBtnText').textContent = 'Update Survey';
    document.getElementById('surveyName').value = currentSurvey.name;
    document.getElementById('surveyDescription').value = currentSurvey.description || '';
    document.getElementById('modelSelect').value = currentSurvey.model;
    document.getElementById('temperatureSlider').value = currentSurvey.temperature;
    updateTemperature(currentSurvey.temperature);
    document.getElementById('characterPrompt').value = currentSurvey.character_prompt;
    document.getElementById('surveyExplanation').value = currentSurvey.survey_explanation || '';

    // Populate topics
    const topics = typeof currentSurvey.topics === 'string' ? JSON.parse(currentSurvey.topics) : currentSurvey.topics;
    document.getElementById('topicsList').innerHTML = '';

    topics.forEach(topic => {
        const topicId = Date.now() + Math.random();
        const topicItem = document.createElement('div');
        topicItem.className = 'topic-item';
        topicItem.dataset.id = topicId;

        topicItem.innerHTML = `
            <div class="topic-drag-handle">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M2 4h12M2 8h12M2 12h12"/>
                </svg>
            </div>
            <div class="topic-fields">
                <input type="text" class="topic-name-input" value="${escapeHtml(topic.name)}" required>
                <label class="topic-mandatory">
                    <input type="checkbox" ${topic.mandatory ? 'checked' : ''}>
                    <span>Mandatory</span>
                </label>
            </div>
            <button type="button" class="topic-remove" onclick="removeTopic(${topicId})">Remove</button>
        `;

        document.getElementById('topicsList').appendChild(topicItem);
    });

    document.getElementById('surveyModal').style.display = 'flex';
}

async function toggleSurveyStatus() {
    if (!currentSurveyId || !currentSurvey) return;

    const newStatus = !currentSurvey.is_active;

    try {
        const response = await fetch(`/api/survey/config/${currentSurveyId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: newStatus })
        });

        if (!response.ok) throw new Error('Failed to update status');

        currentSurvey.is_active = newStatus;
        document.getElementById('toggleStatusBtn').textContent = newStatus ? 'Deactivate' : 'Activate';

        hideViewSurveyModal();
        loadSurveys();

        alert(`Survey ${newStatus ? 'activated' : 'deactivated'} successfully!`);
    } catch (error) {
        console.error('Error updating status:', error);
        alert('Failed to update survey status');
    }
}

async function deleteSurvey() {
    if (!currentSurveyId || !currentSurvey) return;

    if (!confirm(`Are you sure you want to delete "${currentSurvey.name}"? This cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/survey/config/${currentSurveyId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete survey');

        hideViewSurveyModal();
        loadSurveys();

        alert('Survey deleted successfully');
    } catch (error) {
        console.error('Error deleting survey:', error);
        alert('Failed to delete survey');
    }
}

function copySurveyLink() {
    if (!currentSurveyId) return;

    const link = `${window.location.origin}/survey?id=${currentSurveyId}`;

    navigator.clipboard.writeText(link).then(() => {
        alert('Survey link copied to clipboard!\n\n' + link);
    }).catch(() => {
        prompt('Copy this survey link:', link);
    });
}

// ============================================================================
// UTILITIES
// ============================================================================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
