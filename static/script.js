/**
 * EduGenie – Google Gemini Powered Learning Assistant
 * Frontend JavaScript Controller & API Integration
 */

// =====================================================================
// 1. Navigation & Tab Controller
// =====================================================================

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
    // Remove active status from all nav links
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));

    // Show target tab
    const targetTab = document.getElementById(`tab-${tabName}`);
    if (targetTab) {
        targetTab.classList.add('active');
    }

    // Set active link
    const targetLink = document.querySelector(`.nav-link[data-tab="${tabName}"]`);
    if (targetLink) {
        targetLink.classList.add('active');
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// =====================================================================
// 2. Generic API Request Helper
// =====================================================================

async function apiRequest(endpoint, data) {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            const errorMsg = result.error || `Request failed with status ${response.status}`;
            throw new Error(errorMsg);
        }

        return result.data;
    } catch (err) {
        console.error(`API Error on ${endpoint}:`, err);
        throw err;
    }
}

// =====================================================================
// 3. UI Helpers & Toast Notifications
// =====================================================================

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icon = type === 'success' ? 'fa-circle-check text-emerald' : 'fa-triangle-exclamation text-rose';
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${escapeHtml(message)}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
}

function renderMarkdown(text) {
    if (!text) return '';
    // Lightweight markdown parser for educational output
    let html = escapeHtml(text);

    // Code blocks ```...```
    html = html.replace(/```([a-z]*)\n([\s\S]*?)```/gm, '<pre><code>$2</code></pre>');

    // Inline code `...`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold **...**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic *...*
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Headings ### ...
    html = html.replace(/^### (.*$)/gim, '<h4>$1</h4>');
    html = html.replace(/^## (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^# (.*$)/gim, '<h2>$1</h2>');

    // Unordered lists
    html = html.replace(/^\s*[-*]\s+(.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>[\s\S]*?<\/li>)/gm, '<ul>$1</ul>');

    // Paragraphs
    html = html.replace(/\n\n+/g, '</p><p>');
    return `<p>${html}</p>`;
}

function copyResult(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;

    const text = el.innerText || el.textContent;
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(err => {
        showToast('Failed to copy', 'error');
    });
}

// =====================================================================
// 4. Feature 1: Ask AI Tutor
// =====================================================================

function fillQuestion(q) {
    document.getElementById('askQuestion').value = q;
    document.getElementById('askQuestion').focus();
}

function clearAskForm() {
    document.getElementById('askQuestion').value = '';
    document.getElementById('askResultCard').style.display = 'none';
}

async function handleAskSubmit(e) {
    e.preventDefault();
    const question = document.getElementById('askQuestion').value.trim();
    if (!question) return;

    const submitBtn = document.getElementById('askSubmitBtn');
    const resultCard = document.getElementById('askResultCard');
    const resultContent = document.getElementById('askAnswerContent');

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> EduGenie is thinking...';

    try {
        const data = await apiRequest('/api/ask', { question });
        resultContent.innerHTML = renderMarkdown(data.answer);
        resultCard.style.display = 'block';
        resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        showToast('Answer generated successfully!', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Ask EduGenie';
    }
}

// =====================================================================
// 5. Feature 2: Concept Explainer
// =====================================================================

function fillExplain(topic, level) {
    document.getElementById('explainTopic').value = topic;
    document.getElementById('explainLevel').value = level;
    document.getElementById('explainTopic').focus();
}

function clearExplainForm() {
    document.getElementById('explainTopic').value = '';
    document.getElementById('explainResultCard').style.display = 'none';
}

async function handleExplainSubmit(e) {
    e.preventDefault();
    const topic = document.getElementById('explainTopic').value.trim();
    const level = document.getElementById('explainLevel').value;
    if (!topic) return;

    const submitBtn = document.getElementById('explainSubmitBtn');
    const resultCard = document.getElementById('explainResultCard');

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Explaining concept...';

    try {
        const data = await apiRequest('/api/explain', { topic, level });

        document.getElementById('explainResultTopic').innerText = data.topic;
        
        const badge = document.getElementById('explainEngineBadge');
        if (data.engine === 'local_lamini') {
            badge.className = 'badge badge-emerald';
            badge.innerText = 'Local LaMini-T5';
        } else {
            badge.className = 'badge badge-indigo';
            badge.innerText = `Google Gemini (${data.level})`;
        }

        document.getElementById('explainDefinitionText').innerText = data.definition;
        document.getElementById('explainDetailedText').innerHTML = renderMarkdown(data.explanation);
        document.getElementById('explainExampleText').innerText = data.example;

        const takeawaysList = document.getElementById('explainTakeawaysList');
        takeawaysList.innerHTML = '';
        if (Array.isArray(data.key_takeaways)) {
            data.key_takeaways.forEach(item => {
                const li = document.createElement('li');
                li.innerText = item;
                takeawaysList.appendChild(li);
            });
        }

        document.getElementById('explainFullText').innerText = 
            `Concept: ${data.topic}\n\nDefinition:\n${data.definition}\n\nExplanation:\n${data.explanation}\n\nExample:\n${data.example}`;

        resultCard.style.display = 'block';
        resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        showToast('Concept explained successfully!', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Explain Concept';
    }
}

// =====================================================================
// 6. Feature 3: Study Summarizer
// =====================================================================

function updateWordCounter() {
    const text = document.getElementById('summarizeText').value.trim();
    const words = text ? text.split(/\s+/).length : 0;
    document.getElementById('summarizeCharCount').innerText = `${words} words (${text.length} chars)`;
}

function fillSampleStudyPassage() {
    const sample = `Photosynthesis is the fundamental biological process by which green plants, algae, and certain bacteria convert light energy, usually from the Sun, into chemical energy in the form of glucose. This vital transformation occurs primarily within the chloroplasts of plant cells, specifically utilizing the green pigment chlorophyll. 

The process takes place in two main stages: the light-dependent reactions and the light-independent reactions (commonly referred to as the Calvin cycle). During the light-dependent phase, chlorophyll absorbs sunlight and uses its energy to split water molecules into hydrogen ions and oxygen gas, releasing oxygen into the atmosphere as a crucial byproduct. In the Calvin cycle, carbon dioxide from the air is captured and synthesized into energy-rich carbohydrates. 

Without photosynthesis, life on Earth would cease to exist as we know it, because it is the primary source of organic matter for almost all living organisms and maintains atmospheric oxygen levels.`;
    document.getElementById('summarizeText').value = sample;
    updateWordCounter();
}

function clearSummarizeForm() {
    document.getElementById('summarizeText').value = '';
    updateWordCounter();
    document.getElementById('summarizeResultCard').style.display = 'none';
}

async function handleSummarizeSubmit(e) {
    e.preventDefault();
    const text = document.getElementById('summarizeText').value.trim();
    if (!text || text.length < 20) {
        showToast('Please enter at least 20 characters of study material.', 'error');
        return;
    }

    const submitBtn = document.getElementById('summarizeSubmitBtn');
    const resultCard = document.getElementById('summarizeResultCard');

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Condensing material...';

    try {
        const data = await apiRequest('/api/summarize', { text });

        document.getElementById('summaryHeadline').innerText = data.headline || 'Summary';
        document.getElementById('summaryBodyText').innerHTML = renderMarkdown(data.summary);

        if (data.stats) {
            document.getElementById('statOrigWords').innerText = data.stats.original_words || '0';
            document.getElementById('statSummaryWords').innerText = data.stats.summary_words || '0';
            document.getElementById('statReduction').innerText = data.stats.reduction_percentage || '0%';
            document.getElementById('statTimeSaved').innerText = data.stats.estimated_read_time_saved || '0 mins';
        }

        const pointsList = document.getElementById('summaryKeyPointsList');
        pointsList.innerHTML = '';
        if (Array.isArray(data.key_points)) {
            data.key_points.forEach(pt => {
                const li = document.createElement('li');
                li.innerText = pt;
                pointsList.appendChild(li);
            });
        }

        const termsContainer = document.getElementById('summaryKeyTermsContainer');
        const termsList = document.getElementById('summaryKeyTermsList');
        termsList.innerHTML = '';
        if (Array.isArray(data.key_terms) && data.key_terms.length > 0) {
            termsContainer.style.display = 'block';
            data.key_terms.forEach(t => {
                const div = document.createElement('div');
                div.className = 'term-card';
                div.innerHTML = `<strong>${escapeHtml(t.term)}</strong><span>${escapeHtml(t.definition)}</span>`;
                termsList.appendChild(div);
            });
        } else {
            termsContainer.style.display = 'none';
        }

        resultCard.style.display = 'block';
        resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        showToast('Summary created successfully!', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-compress"></i> Summarize Material';
    }
}

// =====================================================================
// 7. Feature 4: Interactive Quiz Runner
// =====================================================================

let activeQuizData = null;
let userAnswers = {};

function fillQuiz(topic, difficulty) {
    document.getElementById('quizTopic').value = topic;
    document.getElementById('quizDifficulty').value = difficulty;
    document.getElementById('quizTopic').focus();
}

function resetQuiz() {
    activeQuizData = null;
    userAnswers = {};
    document.getElementById('quizPlayerCard').style.display = 'none';
    document.getElementById('quizConfigCard').style.display = 'block';
    document.getElementById('quizScoreReport').style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function handleQuizSubmit(e) {
    e.preventDefault();
    const topic = document.getElementById('quizTopic').value.trim();
    const text = document.getElementById('quizSourceText').value.trim();
    const count = parseInt(document.getElementById('quizCount').value, 10);
    const difficulty = document.getElementById('quizDifficulty').value;

    if (!topic && !text) {
        showToast('Please enter a topic or paste text to generate a quiz.', 'error');
        return;
    }

    const submitBtn = document.getElementById('quizSubmitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating Quiz Questions...';

    try {
        const data = await apiRequest('/api/quiz', {
            topic,
            text,
            number_of_questions: count,
            difficulty
        });

        activeQuizData = data;
        userAnswers = {};

        renderQuizPlayer(data);
        document.getElementById('quizConfigCard').style.display = 'none';
        document.getElementById('quizPlayerCard').style.display = 'block';
        document.getElementById('quizScoreReport').style.display = 'none';
        document.getElementById('quizPlayerCard').scrollIntoView({ behavior: 'smooth' });
        showToast('Quiz ready! Select your answers below.', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-play"></i> Generate Quiz';
    }
}

function renderQuizPlayer(quiz) {
    document.getElementById('quizDisplayTopic').innerText = `Quiz: ${quiz.topic}`;
    document.getElementById('quizDisplayMeta').innerText = `${quiz.difficulty.toUpperCase()} • ${quiz.total_questions} Questions`;

    const container = document.getElementById('quizQuestionsContainer');
    container.innerHTML = '';

    quiz.questions.forEach((q, qIndex) => {
        const qCard = document.createElement('div');
        qCard.className = 'quiz-question-card';
        qCard.id = `question-card-${qIndex}`;

        let optionsHtml = '';
        q.options.forEach((opt, optIndex) => {
            optionsHtml += `
                <label class="quiz-option-label" id="label-q${qIndex}-opt${optIndex}" onclick="selectQuizOption(${qIndex}, '${escapeHtml(opt)}', ${optIndex})">
                    <input type="radio" name="question_${qIndex}" value="${escapeHtml(opt)}" style="display:none;">
                    <i class="fa-regular fa-circle" id="icon-q${qIndex}-opt${optIndex}"></i>
                    <span>${escapeHtml(opt)}</span>
                </label>
            `;
        });

        qCard.innerHTML = `
            <div class="quiz-question-title">
                <span class="text-amber">Q${qIndex + 1}.</span> ${escapeHtml(q.question)}
            </div>
            <div class="quiz-options-list">
                ${optionsHtml}
            </div>
            <div class="quiz-explanation-box" id="explanation-${qIndex}">
                <strong><i class="fa-solid fa-circle-info"></i> Explanation:</strong>
                <p class="mt-1">${escapeHtml(q.explanation)}</p>
            </div>
        `;

        container.appendChild(qCard);
    });

    document.getElementById('submitQuizAnswersBtn').style.display = 'inline-flex';
}

function selectQuizOption(qIndex, optionText, optIndex) {
    if (!activeQuizData) return;
    userAnswers[qIndex] = optionText;

    // Deselect siblings
    activeQuizData.questions[qIndex].options.forEach((_, idx) => {
        const label = document.getElementById(`label-q${qIndex}-opt${idx}`);
        const icon = document.getElementById(`icon-q${qIndex}-opt${idx}`);
        if (label) label.classList.remove('selected');
        if (icon) icon.className = 'fa-regular fa-circle';
    });

    // Select active
    const selectedLabel = document.getElementById(`label-q${qIndex}-opt${optIndex}`);
    const selectedIcon = document.getElementById(`icon-q${qIndex}-opt${optIndex}`);
    if (selectedLabel) selectedLabel.classList.add('selected');
    if (selectedIcon) selectedIcon.className = 'fa-solid fa-circle-dot text-indigo';
}

function gradeQuiz() {
    if (!activeQuizData) return;

    const total = activeQuizData.questions.length;
    const answeredCount = Object.keys(userAnswers).length;

    if (answeredCount < total) {
        if (!confirm(`You have answered ${answeredCount} of ${total} questions. Do you want to submit anyway?`)) {
            return;
        }
    }

    let score = 0;

    activeQuizData.questions.forEach((q, qIndex) => {
        const userChoice = userAnswers[qIndex];
        const correctChoice = q.correct_answer;

        const isCorrect = userChoice === correctChoice;
        if (isCorrect) score++;

        // Highlight options
        q.options.forEach((opt, optIndex) => {
            const label = document.getElementById(`label-q${qIndex}-opt${optIndex}`);
            if (!label) return;

            label.onclick = null; // disable further clicks
            label.classList.remove('selected');

            if (opt === correctChoice) {
                label.classList.add('correct');
            } else if (opt === userChoice && !isCorrect) {
                label.classList.add('incorrect');
            }
        });

        // Show explanation
        const expBox = document.getElementById(`explanation-${qIndex}`);
        if (expBox) expBox.style.display = 'block';
    });

    // Calculate percentage
    const percent = Math.round((score / total) * 100);
    document.getElementById('scorePercentValue').innerText = `${percent}%`;
    document.getElementById('scoreDetailsText').innerText = `You scored ${score} out of ${total} (${percent}%).`;

    const verdict = document.getElementById('scoreVerdict');
    if (percent === 100) verdict.innerText = '🎉 Perfect Score! Excellent Mastery!';
    else if (percent >= 70) verdict.innerText = '👏 Great Job! Good Understanding!';
    else verdict.innerText = '💡 Keep Practicing! Review the explanations below.';

    document.getElementById('quizScoreReport').style.display = 'block';
    document.getElementById('submitQuizAnswersBtn').style.display = 'none';
    document.getElementById('quizScoreReport').scrollIntoView({ behavior: 'smooth' });

    showToast(`Quiz Completed! You scored ${score}/${total}`, 'success');
}

// =====================================================================
// 8. Feature 5: Learning Path Generator
// =====================================================================

function fillPath(topic, level, duration, hours) {
    document.getElementById('pathTopic').value = topic;
    document.getElementById('pathLevel').value = level;
    document.getElementById('pathDuration').value = duration;
    document.getElementById('pathHours').value = hours;
    document.getElementById('pathTopic').focus();
}

function clearPathForm() {
    document.getElementById('pathTopic').value = '';
    document.getElementById('pathResultCard').style.display = 'none';
}

async function handlePathSubmit(e) {
    e.preventDefault();
    const topic = document.getElementById('pathTopic').value.trim();
    const level = document.getElementById('pathLevel').value;
    const duration = document.getElementById('pathDuration').value;
    const hours_per_week = parseInt(document.getElementById('pathHours').value, 10);

    if (!topic) return;

    const submitBtn = document.getElementById('pathSubmitBtn');
    const resultCard = document.getElementById('pathResultCard');

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Designing Curriculum...';

    try {
        const data = await apiRequest('/api/learning-path', {
            topic,
            level,
            duration,
            hours_per_week
        });

        document.getElementById('pathTitle').innerText = data.title;
        document.getElementById('pathOverview').innerText = data.overview;

        // Prerequisites
        const prereqsList = document.getElementById('pathPrereqsList');
        prereqsList.innerHTML = '';
        if (Array.isArray(data.prerequisites)) {
            data.prerequisites.forEach(p => {
                const li = document.createElement('li');
                li.innerText = p;
                prereqsList.appendChild(li);
            });
        }

        // Weekly Timeline
        const timeline = document.getElementById('pathWeeklyTimeline');
        timeline.innerHTML = '';

        if (Array.isArray(data.weekly_plan)) {
            data.weekly_plan.forEach(w => {
                const card = document.createElement('div');
                card.className = 'week-card';

                let goalsHtml = (w.learning_goals || []).map(g => `<li>${escapeHtml(g)}</li>`).join('');
                let topicsHtml = (w.core_topics || []).map(t => `<li>${escapeHtml(t)}</li>`).join('');
                let activitiesHtml = (w.activities || []).map(a => `<li>${escapeHtml(a)}</li>`).join('');
                let practiceHtml = (w.practice_tasks || []).map(p => `<li>${escapeHtml(p)}</li>`).join('');

                card.innerHTML = `
                    <span class="week-badge">Week ${w.week || 'Milestone'}</span>
                    <h4 class="week-title">${escapeHtml(w.title || 'Weekly Module')}</h4>
                    
                    <div class="week-section">
                        <h5>🎯 Learning Goals</h5>
                        <ul>${goalsHtml}</ul>
                    </div>
                    
                    <div class="week-section">
                        <h5>📚 Core Topics</h5>
                        <ul>${topicsHtml}</ul>
                    </div>

                    <div class="week-section">
                        <h5>🛠️ Hands-on Activities & Practice</h5>
                        <ul>${activitiesHtml}${practiceHtml}</ul>
                    </div>

                    ${w.checkpoint ? `
                    <div class="week-section">
                        <h5>✅ Weekly Checkpoint</h5>
                        <p class="text-muted text-sm">${escapeHtml(w.checkpoint)}</p>
                    </div>` : ''}
                `;

                timeline.appendChild(card);
            });
        }

        // Capstone
        if (data.capstone_project) {
            document.getElementById('capstoneTitle').innerText = data.capstone_project.title || 'Final Capstone Project';
            document.getElementById('capstoneDesc').innerText = data.capstone_project.description || '';
            document.getElementById('pathCapstoneBox').style.display = 'block';
        } else {
            document.getElementById('pathCapstoneBox').style.display = 'none';
        }

        // Resources
        const resList = document.getElementById('pathResourcesList');
        resList.innerHTML = '';
        if (Array.isArray(data.recommended_resources)) {
            data.recommended_resources.forEach(r => {
                const li = document.createElement('li');
                li.innerText = r;
                resList.appendChild(li);
            });
        }

        resultCard.style.display = 'block';
        resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        showToast('Learning path generated successfully!', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-compass"></i> Generate Learning Path';
    }
}
