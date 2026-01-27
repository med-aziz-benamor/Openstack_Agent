/**
 * OpenStack Admin Assistant Portal - Frontend Application
 */

// State
let selectedFile = null;

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const progressBar = document.getElementById('progressBar');
const progressFill = document.getElementById('progressFill');
const resultsSection = document.getElementById('resultsSection');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
});

function setupEventListeners() {
    // Browse button
    browseBtn.addEventListener('click', () => fileInput.click());
    
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // Analyze button
    analyzeBtn.addEventListener('click', analyzeBundle);
}

function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFile(file) {
    // Validate file type
    if (!file.name.endsWith('.tar.gz') && !file.name.endsWith('.tgz')) {
        showError('Invalid file type. Please upload a .tar.gz or .tgz file.');
        return;
    }
    
    // Validate file size (100MB limit)
    const maxSize = 100 * 1024 * 1024; // 100MB
    if (file.size > maxSize) {
        showError('File too large. Maximum size is 100MB.');
        return;
    }
    
    selectedFile = file;
    
    // Update UI
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    fileInfo.style.display = 'block';
    analyzeBtn.disabled = false;
    
    hideError();
}

async function analyzeBundle() {
    if (!selectedFile) return;
    
    // Disable button and show progress
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing...';
    progressBar.style.display = 'block';
    resultsSection.style.display = 'none';
    hideError();
    
    // Animate progress
    animateProgress();
    
    try {
        // Create form data
        const formData = new FormData();
        formData.append('bundle', selectedFile);
        
        // Send request
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }
        
        const result = await response.json();
        
        // Display results
        displayResults(result);
        
    } catch (error) {
        console.error('Analysis error:', error);
        showError(error.message || 'Failed to analyze bundle. Please try again.');
    } finally {
        // Reset UI
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze Bundle';
        progressBar.style.display = 'none';
        progressFill.style.width = '0%';
    }
}

function animateProgress() {
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) {
            clearInterval(interval);
            progress = 90;
        }
        progressFill.style.width = progress + '%';
    }, 200);
}

function displayResults(data) {
    resultsSection.style.display = 'block';
    
    // Scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
    
    // Display metadata
    displayMetadata(data.metadata);
    
    // Display failed services
    if (data.failed_services && data.failed_services.length > 0) {
        displayFailedServices(data.failed_services);
    } else {
        document.getElementById('servicesPanel').style.display = 'none';
    }
    
    // Display HAProxy findings
    if (data.haproxy_findings) {
        displayHAProxyFindings(data.haproxy_findings);
    } else {
        document.getElementById('haproxyPanel').style.display = 'none';
    }
    
    // Display errors
    if (data.error_summary && data.error_summary.length > 0) {
        displayErrors(data.error_summary);
    } else {
        document.getElementById('errorsPanel').style.display = 'none';
    }
    
    // Display port listeners
    if (data.listen_summary && data.listen_summary.length > 0) {
        displayPortListeners(data.listen_summary);
    } else {
        document.getElementById('portsPanel').style.display = 'none';
    }
    
    // Display recommendations
    if (data.recommendations && data.recommendations.length > 0) {
        displayRecommendations(data.recommendations);
    } else {
        document.getElementById('recommendationsPanel').style.display = 'none';
    }
}

function displayMetadata(metadata) {
    const panel = document.getElementById('metadataPanel');
    
    const html = `
        <div class="metadata-grid">
            <div class="metadata-item">
                <span class="metadata-label">Hostname:</span>
                <span class="metadata-value">${metadata.hostname || 'Unknown'}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Timestamp:</span>
                <span class="metadata-value">${metadata.timestamp || 'Unknown'}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">File Hash:</span>
                <span class="metadata-value code">${metadata.file_hash.substring(0, 16)}...</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Files Extracted:</span>
                <span class="metadata-value">${metadata.extracted_file_count}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Directories:</span>
                <span class="metadata-value">${metadata.extracted_dir_count}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Original Filename:</span>
                <span class="metadata-value">${metadata.uploaded_filename || 'N/A'}</span>
            </div>
        </div>
    `;
    
    panel.innerHTML = html;
}

function displayFailedServices(services) {
    const panel = document.getElementById('servicesPanel');
    const body = document.getElementById('servicesBody');
    const badge = document.getElementById('servicesBadge');
    
    panel.style.display = 'block';
    badge.textContent = services.length;
    
    const html = `
        <ul class="service-list">
            ${services.map(service => `
                <li class="service-item failed">
                    <span class="service-icon">❌</span>
                    <span class="service-name">${escapeHtml(service)}</span>
                </li>
            `).join('')}
        </ul>
    `;
    
    body.innerHTML = html;
}

function displayHAProxyFindings(findings) {
    const panel = document.getElementById('haproxyPanel');
    const body = document.getElementById('haproxyBody');
    
    const hasFindings = 
        (findings.has_no_server_available && findings.has_no_server_available.length > 0) ||
        (findings.server_up_down && findings.server_up_down.length > 0) ||
        (findings.timeouts && findings.timeouts.length > 0);
    
    if (!hasFindings) {
        panel.style.display = 'none';
        return;
    }
    
    panel.style.display = 'block';
    
    let html = '';
    
    if (findings.has_no_server_available && findings.has_no_server_available.length > 0) {
        html += `
            <div class="finding-section">
                <h4>⚠️ Backends with No Available Servers</h4>
                <div class="log-lines">
                    ${findings.has_no_server_available.map(line => `
                        <div class="log-line error">${escapeHtml(line)}</div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    if (findings.server_up_down && findings.server_up_down.length > 0) {
        html += `
            <div class="finding-section">
                <h4>🔄 Server Status Changes</h4>
                <div class="log-lines">
                    ${findings.server_up_down.slice(0, 10).map(line => `
                        <div class="log-line warning">${escapeHtml(line)}</div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    if (findings.timeouts && findings.timeouts.length > 0) {
        html += `
            <div class="finding-section">
                <h4>⏱️ Timeouts</h4>
                <div class="log-lines">
                    ${findings.timeouts.slice(0, 10).map(line => `
                        <div class="log-line warning">${escapeHtml(line)}</div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    body.innerHTML = html;
}

function displayErrors(errors) {
    const panel = document.getElementById('errorsPanel');
    const body = document.getElementById('errorsBody');
    const badge = document.getElementById('errorsBadge');
    
    panel.style.display = 'block';
    badge.textContent = errors.length;
    
    const html = `
        <div class="errors-list">
            ${errors.map(error => `
                <div class="error-entry">
                    <div class="error-header">
                        <span class="error-service">${escapeHtml(error.service)}</span>
                        <span class="error-count">×${error.count}</span>
                    </div>
                    <div class="error-line">${escapeHtml(error.line)}</div>
                    ${error.source_file ? `<div class="error-source">Source: ${escapeHtml(error.source_file)}</div>` : ''}
                </div>
            `).join('')}
        </div>
    `;
    
    body.innerHTML = html;
}

function displayPortListeners(ports) {
    const panel = document.getElementById('portsPanel');
    const body = document.getElementById('portsBody');
    const badge = document.getElementById('portsBadge');
    
    panel.style.display = 'block';
    badge.textContent = ports.length;
    
    const html = `
        <table class="ports-table">
            <thead>
                <tr>
                    <th>Port</th>
                    <th>Process</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
                ${ports.map(port => `
                    <tr>
                        <td><span class="port-number">${escapeHtml(port.port)}</span></td>
                        <td>${port.process ? escapeHtml(port.process) : '<em>unknown</em>'}</td>
                        <td class="port-details">${escapeHtml(port.full_line)}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    body.innerHTML = html;
}

function displayRecommendations(recommendations) {
    const panel = document.getElementById('recommendationsPanel');
    const body = document.getElementById('recommendationsBody');
    
    panel.style.display = 'block';
    
    const html = recommendations.map((rec, index) => `
        <div class="recommendation">
            <div class="recommendation-header">
                <h4>${escapeHtml(rec.title)}</h4>
            </div>
            <p class="recommendation-why">${escapeHtml(rec.why)}</p>
            ${rec.commands && rec.commands.length > 0 ? `
                <div class="recommendation-commands">
                    <h5>Suggested Commands:</h5>
                    ${rec.commands.map((cmd, cmdIndex) => `
                        <div class="command-item">
                            <code class="command-code">${escapeHtml(cmd)}</code>
                            <button class="btn-copy" onclick="copyToClipboard('${escapeForJs(cmd)}', ${index}, ${cmdIndex})">
                                📋 Copy
                            </button>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `).join('');
    
    body.innerHTML = html;
}

function copyToClipboard(text, recIndex, cmdIndex) {
    navigator.clipboard.writeText(text).then(() => {
        // Show feedback
        const btn = document.querySelector(
            `.recommendation:nth-child(${recIndex + 1}) .command-item:nth-child(${cmdIndex + 2}) .btn-copy`
        );
        if (btn) {
            const originalText = btn.textContent;
            btn.textContent = '✓ Copied!';
            btn.classList.add('copied');
            setTimeout(() => {
                btn.textContent = originalText;
                btn.classList.remove('copied');
            }, 2000);
        }
    }).catch(err => {
        console.error('Failed to copy:', err);
        showError('Failed to copy to clipboard');
    });
}

function showError(message) {
    errorText.textContent = message;
    errorMessage.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(hideError, 5000);
}

function hideError() {
    errorMessage.style.display = 'none';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function escapeForJs(str) {
    return str.replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, '\\n');
}
