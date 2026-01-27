/**
 * RFP Decision Support Agent - Frontend Application
 */

// Configuration
const API_BASE_URL = ''; // Relative path to current origin
const API_ENDPOINTS = {
    health: '/api/v1/health',
    analyze: '/api/v1/recommendation/upload-analyze'
};

// State
let selectedFile = null;
let analysisResult = null;

// DOM Elements
const elements = {
    apiStatus: document.getElementById('apiStatus'),
    dropZone: document.getElementById('dropZone'),
    fileInput: document.getElementById('fileInput'),
    selectedFile: document.getElementById('selectedFile'),
    fileName: document.getElementById('fileName'),
    fileSize: document.getElementById('fileSize'),
    removeFile: document.getElementById('removeFile'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    uploadSection: document.getElementById('uploadSection'),
    loadingSection: document.getElementById('loadingSection'),
    loadingStatus: document.getElementById('loadingStatus'),
    progressFill: document.getElementById('progressFill'),
    resultsSection: document.getElementById('resultsSection'),
    decisionBadge: document.getElementById('decisionBadge'),
    confidenceScore: document.getElementById('confidenceScore'),
    progressCircle: document.getElementById('progressCircle'),
    executiveSummary: document.getElementById('executiveSummary'),
    complianceBadge: document.getElementById('complianceBadge'),
    compliantCount: document.getElementById('compliantCount'),
    partialCount: document.getElementById('partialCount'),
    nonCompliantCount: document.getElementById('nonCompliantCount'),
    unknownCount: document.getElementById('unknownCount'),
    compliantBar: document.getElementById('compliantBar'),
    partialBar: document.getElementById('partialBar'),
    nonCompliantBar: document.getElementById('nonCompliantBar'),
    unknownBar: document.getElementById('unknownBar'),
    mandatoryIcon: document.getElementById('mandatoryIcon'),
    mandatoryText: document.getElementById('mandatoryText'),
    riskCount: document.getElementById('riskCount'),
    risksList: document.getElementById('risksList'),
    expandToolsBtn: document.getElementById('expandToolsBtn'),
    toolsBody: document.getElementById('toolsBody'),
    toolsTableBody: document.getElementById('toolsTableBody'),
    newAnalysisBtn: document.getElementById('newAnalysisBtn'),
    downloadReportBtn: document.getElementById('downloadReportBtn')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkApiHealth();
    setupEventListeners();

    // Check API health every 30 seconds
    setInterval(checkApiHealth, 30000);
});

// API Health Check
async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.health}`);
        if (response.ok) {
            elements.apiStatus.classList.remove('error');
            elements.apiStatus.classList.add('connected');
            elements.apiStatus.querySelector('span:last-child').textContent = 'Connected';
        } else {
            throw new Error('API not responding');
        }
    } catch (error) {
        elements.apiStatus.classList.remove('connected');
        elements.apiStatus.classList.add('error');
        elements.apiStatus.querySelector('span:last-child').textContent = 'Disconnected';
    }
}

// Event Listeners
function setupEventListeners() {
    // Drag and drop
    elements.dropZone.addEventListener('dragover', handleDragOver);
    elements.dropZone.addEventListener('dragleave', handleDragLeave);
    elements.dropZone.addEventListener('drop', handleDrop);
    elements.dropZone.addEventListener('click', () => elements.fileInput.click());

    // File input
    elements.fileInput.addEventListener('change', handleFileSelect);

    // Remove file
    elements.removeFile.addEventListener('click', (e) => {
        e.stopPropagation();
        removeSelectedFile();
    });

    // Analyze button
    elements.analyzeBtn.addEventListener('click', analyzeRFP);

    // Expand tools
    elements.expandToolsBtn.addEventListener('click', toggleToolsTable);

    // New analysis
    elements.newAnalysisBtn.addEventListener('click', resetToUpload);

    // Download report
    elements.downloadReportBtn.addEventListener('click', downloadReport);
}

// Drag and Drop Handlers
function handleDragOver(e) {
    e.preventDefault();
    elements.dropZone.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    elements.dropZone.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    elements.dropZone.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

// File Handling
function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFile(file) {
    const validTypes = ['.pdf', '.docx', '.doc'];
    const extension = '.' + file.name.split('.').pop().toLowerCase();

    if (!validTypes.includes(extension)) {
        alert('Please upload a PDF or DOCX file.');
        return;
    }

    selectedFile = file;
    displaySelectedFile(file);
    elements.analyzeBtn.disabled = false;
}

function displaySelectedFile(file) {
    elements.fileName.textContent = file.name;
    elements.fileSize.textContent = formatFileSize(file.size);
    elements.selectedFile.style.display = 'flex';
    elements.dropZone.style.display = 'none';
}

function removeSelectedFile() {
    selectedFile = null;
    elements.fileInput.value = '';
    elements.selectedFile.style.display = 'none';
    elements.dropZone.style.display = 'flex';
    elements.analyzeBtn.disabled = true;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Analyze RFP
async function analyzeRFP() {
    if (!selectedFile) return;

    // Show loading
    showSection('loading');
    updateLoadingStatus('Uploading document...', 10);

    try {
        // Create FormData
        const formData = new FormData();
        formData.append('file', selectedFile);

        updateLoadingStatus('Parsing document...', 30);

        // Send to API
        const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.analyze}`, {
            method: 'POST',
            body: formData
        });

        updateLoadingStatus('Analyzing requirements...', 60);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }

        updateLoadingStatus('Generating recommendation...', 90);

        const result = await response.json();
        analysisResult = result;

        updateLoadingStatus('Complete!', 100);

        // Wait a moment before showing results
        setTimeout(() => {
            displayResults(result);
            showSection('results');
        }, 500);

    } catch (error) {
        console.error('Analysis error:', error);
        alert(`Analysis failed: ${error.message}`);
        showSection('upload');
    }
}

function updateLoadingStatus(status, progress) {
    elements.loadingStatus.textContent = status;
    elements.progressFill.style.width = `${progress}%`;
}

// Display Results
function displayResults(result) {
    const rec = result.recommendation;

    // Decision Badge
    const decision = rec.recommendation;
    elements.decisionBadge.textContent = decision.replace('_', ' ');
    elements.decisionBadge.className = 'decision-badge ' + decision.toLowerCase();

    // Confidence Score (animate)
    animateConfidence(rec.confidence_score);

    // Executive Summary
    elements.executiveSummary.textContent = rec.executive_summary;

    // Compliance Summary
    const compliance = rec.compliance_summary;
    elements.complianceBadge.textContent = compliance.overall_compliance.replace('_', ' ');
    elements.complianceBadge.className = 'compliance-badge ' + compliance.overall_compliance.toLowerCase();

    elements.compliantCount.textContent = compliance.compliant_count;
    elements.partialCount.textContent = compliance.partial_count;
    elements.nonCompliantCount.textContent = compliance.non_compliant_count;
    elements.unknownCount.textContent = compliance.unknown_count;

    // Compliance bars
    const total = compliance.total_evaluated || 1;
    elements.compliantBar.style.width = `${(compliance.compliant_count / total) * 100}%`;
    elements.partialBar.style.width = `${(compliance.partial_count / total) * 100}%`;
    elements.nonCompliantBar.style.width = `${(compliance.non_compliant_count / total) * 100}%`;
    elements.unknownBar.style.width = `${(compliance.unknown_count / total) * 100}%`;

    // Mandatory status
    const mandatoryMet = compliance.mandatory_met;
    elements.mandatoryIcon.textContent = mandatoryMet ? '✓' : '✕';
    elements.mandatoryText.textContent = mandatoryMet ? 'Mandatory Requirements Met' : 'Mandatory Requirements NOT Met';
    document.querySelector('.mandatory-status').classList.toggle('failed', !mandatoryMet);

    // Risks
    displayRisks(rec.risks || []);

    // Tool Results
    displayToolResults(compliance.tool_results || []);
}

function animateConfidence(target) {
    const duration = 1500;
    const start = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);

        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(target * eased);

        elements.confidenceScore.textContent = current;

        // Update circle
        const circumference = 283;
        const offset = circumference - (current / 100) * circumference;
        elements.progressCircle.style.strokeDashoffset = offset;
        elements.progressCircle.style.stroke = getConfidenceColor(current);

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

function getConfidenceColor(value) {
    if (value >= 70) return '#22c55e';
    if (value >= 40) return '#f59e0b';
    return '#ef4444';
}

function displayRisks(risks) {
    elements.riskCount.textContent = `${risks.length} risk${risks.length !== 1 ? 's' : ''}`;

    if (risks.length === 0) {
        elements.risksList.innerHTML = '<div class="no-risks">✅ No significant risks identified</div>';
        return;
    }

    elements.risksList.innerHTML = risks.map(risk => `
        <div class="risk-item ${risk.severity.toLowerCase()}">
            <span class="risk-severity">${risk.severity}</span>
            <div class="risk-content">
                <div class="risk-description">${risk.description}</div>
                <div class="risk-source">${risk.source_tool} • ${risk.category}</div>
            </div>
        </div>
    `).join('');
}

function displayToolResults(results) {
    elements.toolsTableBody.innerHTML = results.map(result => {
        const icon = getComplianceIcon(result.compliance_level);
        return `
            <tr>
                <td>${result.tool_name}</td>
                <td>${truncate(result.requirement, 50)}</td>
                <td><span class="compliance-icon">${icon}</span> ${result.status}</td>
                <td>${Math.round(result.confidence * 100)}%</td>
            </tr>
        `;
    }).join('');
}

function getComplianceIcon(level) {
    const icons = {
        'COMPLIANT': '✅',
        'PARTIAL': '◐',
        'NON_COMPLIANT': '❌',
        'UNKNOWN': '❓',
        'WARNING': '⚠️'
    };
    return icons[level] || '❓';
}

function truncate(str, length) {
    if (!str) return '';
    return str.length > length ? str.substring(0, length) + '...' : str;
}

// UI Helpers
function showSection(section) {
    elements.uploadSection.style.display = section === 'upload' ? 'flex' : 'none';
    elements.loadingSection.style.display = section === 'loading' ? 'flex' : 'none';
    elements.resultsSection.style.display = section === 'results' ? 'grid' : 'none';
}

function toggleToolsTable() {
    const isExpanded = elements.toolsBody.style.display !== 'none';
    elements.toolsBody.style.display = isExpanded ? 'none' : 'block';
    elements.expandToolsBtn.classList.toggle('expanded', !isExpanded);
    elements.expandToolsBtn.querySelector('span').textContent = isExpanded ? 'Show Details' : 'Hide Details';
}

function resetToUpload() {
    removeSelectedFile();
    analysisResult = null;
    elements.progressFill.style.width = '0%';
    showSection('upload');
}

function downloadReport() {
    if (!analysisResult || !analysisResult.report_markdown) {
        alert('No report available');
        return;
    }

    const blob = new Blob([analysisResult.report_markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'rfp_recommendation_report.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
