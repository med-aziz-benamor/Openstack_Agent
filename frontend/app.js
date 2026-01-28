/**
 * OpenStack Admin Assistant Portal - Frontend Application
 */

// State
let selectedFile = null;

// DOM Elements
const uploadBox = document.getElementById('uploadBox');
const fileInput = document.getElementById('fileInput');
const selectFileBtn = document.getElementById('selectFileBtn');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const progressPercent = document.getElementById('progressPercent');
const resultsSection = document.getElementById('resultsSection');
const results = document.getElementById('results');
const clearResults = document.getElementById('clearResults');

// Stats elements
const statAnalyzed = document.getElementById('stat-analyzed');
const statIssues = document.getElementById('stat-issues');
const statHealth = document.getElementById('stat-health');
const statLast = document.getElementById('stat-last');
const sidebarVersion = document.getElementById('sidebar-version');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing...');
    setupEventListeners();
    fetchVersion();
});

function setupEventListeners() {
    console.log('Setting up event listeners...');
    console.log('selectFileBtn:', selectFileBtn);
    console.log('fileInput:', fileInput);
    console.log('uploadBox:', uploadBox);
    
    // File select button - most important, prevent bubbling
    if (selectFileBtn) {
        selectFileBtn.addEventListener('click', (e) => {
            console.log('Select file button clicked');
            e.preventDefault();
            e.stopPropagation();
            if (fileInput) {
                fileInput.click();
            } else {
                console.error('fileInput not found!');
            }
        });
    } else {
        console.error('selectFileBtn not found!');
    }
    
    // File input change
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    } else {
        console.error('fileInput not found!');
    }
    
    // Drag and drop
    if (uploadBox) {
        uploadBox.addEventListener('dragover', handleDragOver);
        uploadBox.addEventListener('dragleave', handleDragLeave);
        uploadBox.addEventListener('drop', handleDrop);
        
        // Click on upload box (but not on the button)
        uploadBox.addEventListener('click', (e) => {
            // Don't trigger if clicking the button itself
            if (e.target === selectFileBtn || selectFileBtn.contains(e.target)) {
                console.log('Button click, skipping uploadBox handler');
                return;
            }
            console.log('Upload box clicked');
            if (fileInput) {
                fileInput.click();
            }
        });
    } else {
        console.error('uploadBox not found!');
    }
    
    // Clear results button
    if (clearResults) {
        clearResults.addEventListener('click', () => {
            resultsSection.style.display = 'none';
            results.innerHTML = '';
        });
    }
    
    console.log('Event listeners set up successfully');
}

function handleDragOver(e) {
    e.preventDefault();
    uploadBox.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadBox.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadBox.classList.remove('dragover');
    
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

async function handleFile(file) {
    // Validate file type
    if (!file.name.endsWith('.tar.gz') && !file.name.endsWith('.tgz') && !file.name.endsWith('.tar')) {
        alert('Invalid file type. Please upload a .tar, .tar.gz, or .tgz file.');
        return;
    }
    
    // Validate file size (100MB limit)
    const maxSize = 100 * 1024 * 1024; // 100MB
    if (file.size > maxSize) {
        alert('File too large. Maximum size is 100MB.');
        return;
    }
    
    selectedFile = file;
    
    // Show progress
    progressContainer.style.display = 'block';
    progressText.textContent = 'Uploading and analyzing...';
    progressPercent.textContent = '0%';
    progressFill.style.width = '0%';
    
    // Upload and analyze
    await uploadAndAnalyze();
}

async function uploadAndAnalyze() {
    if (!selectedFile) return;
    
    try {
        // Create form data
        const formData = new FormData();
        formData.append('bundle', selectedFile);
        
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            if (progress <= 90) {
                progressFill.style.width = `${progress}%`;
                progressPercent.textContent = `${progress}%`;
            }
        }, 100);
        
        // Send request
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });
        
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        progressPercent.textContent = '100%';
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }
        
        const result = await response.json();
        
        // Hide progress
        setTimeout(() => {
            progressContainer.style.display = 'none';
        }, 500);
        
        // Update stats
        updateStats(result);
        
        // Display results
        displayResults(result);
        
    } catch (error) {
        console.error('Analysis error:', error);
        progressContainer.style.display = 'none';
        alert(`Analysis failed: ${error.message}`);
    }
}

// Fetch version from API
async function fetchVersion() {
    try {
        const response = await fetch('/api/version');
        const data = await response.json();
        if (sidebarVersion) {
            sidebarVersion.textContent = data.version || '1.0.0';
        }
    } catch (error) {
        console.error('Failed to fetch version:', error);
    }
}

// Update dashboard stats
function updateStats(result) {
    // Increment analyzed count
    const currentCount = parseInt(statAnalyzed.textContent) || 0;
    statAnalyzed.textContent = currentCount + 1;
    
    // Update issues count
    const issuesCount = (result.failed_services?.length || 0) + 
                        (result.top_errors?.length || 0);
    statIssues.textContent = issuesCount;
    
    // Update health status
    if (issuesCount === 0) {
        statHealth.textContent = 'Excellent';
        statHealth.style.color = 'var(--accent-green)';
    } else if (issuesCount < 5) {
        statHealth.textContent = 'Good';
        statHealth.style.color = 'var(--accent-green)';
    } else if (issuesCount < 10) {
        statHealth.textContent = 'Fair';
        statHealth.style.color = 'var(--accent-yellow)';
    } else {
        statHealth.textContent = 'Poor';
        statHealth.style.color = 'var(--openstack-red)';
    }
    
    // Update last analysis time
    const now = new Date();
    statLast.textContent = now.toLocaleTimeString();
}
    
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
    results.innerHTML = '';
    
    // Scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
    
    let html = '';
    
    // Display metadata
    if (data.metadata) {
        html += `
            <div class="result-panel">
                <div class="result-panel-header">
                    <h3 class="result-panel-title">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                        </svg>
                        Bundle Metadata
                    </h3>
                </div>
                <div class="result-panel-body">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
                        <div><strong>Hostname:</strong> ${data.metadata.hostname || 'Unknown'}</div>
                        <div><strong>Timestamp:</strong> ${data.metadata.timestamp || 'Unknown'}</div>
                        <div><strong>File Hash:</strong> <code>${data.metadata.file_hash?.substring(0, 16)}...</code></div>
                        <div><strong>Files Extracted:</strong> ${data.metadata.extracted_file_count}</div>
                        <div><strong>Directories:</strong> ${data.metadata.extracted_dir_count}</div>
                        <div><strong>Filename:</strong> ${data.metadata.uploaded_filename || 'N/A'}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Display failed services
    if (data.failed_services && data.failed_services.length > 0) {
        html += `
            <div class="result-panel">
                <div class="result-panel-header">
                    <h3 class="result-panel-title">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                        </svg>
                        Failed Services
                    </h3>
                    <span class="badge badge-error">${data.failed_services.length}</span>
                </div>
                <div class="result-panel-body">
                    <ul class="result-list">
                        ${data.failed_services.map(service => `
                            <li class="result-list-item">
                                <div class="result-list-item-title" style="color: var(--openstack-red);">
                                    ❌ ${escapeHtml(service)}
                                </div>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
    
    // Display HAProxy findings
    if (data.haproxy_findings) {
        const findings = data.haproxy_findings;
        const hasFindings = 
            (findings.has_no_server_available && findings.has_no_server_available.length > 0) ||
            (findings.server_up_down && findings.server_up_down.length > 0) ||
            (findings.timeouts && findings.timeouts.length > 0);
        
        if (hasFindings) {
            html += `
                <div class="result-panel">
                    <div class="result-panel-header">
                        <h3 class="result-panel-title">
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/>
                            </svg>
                            HAProxy Health
                        </h3>
                    </div>
                    <div class="result-panel-body">
            `;
            
            if (findings.has_no_server_available && findings.has_no_server_available.length > 0) {
                html += `
                    <div style="margin-bottom: 1.5rem;">
                        <h4 style="color: var(--openstack-red); margin-bottom: 0.5rem;">⚠️ Backends with No Available Servers</h4>
                        <div class="code-block">
                            ${findings.has_no_server_available.map(line => escapeHtml(line)).join('\n')}
                        </div>
                    </div>
                `;
            }
            
            if (findings.server_up_down && findings.server_up_down.length > 0) {
                html += `
                    <div style="margin-bottom: 1.5rem;">
                        <h4 style="color: var(--accent-yellow); margin-bottom: 0.5rem;">🔄 Server Status Changes</h4>
                        <div class="code-block">
                            ${findings.server_up_down.slice(0, 10).map(line => escapeHtml(line)).join('\n')}
                        </div>
                    </div>
                `;
            }
            
            if (findings.timeouts && findings.timeouts.length > 0) {
                html += `
                    <div style="margin-bottom: 1.5rem;">
                        <h4 style="color: var(--accent-yellow); margin-bottom: 0.5rem;">⏱️ Timeouts</h4>
                        <div class="code-block">
                            ${findings.timeouts.slice(0, 10).map(line => escapeHtml(line)).join('\n')}
                        </div>
                    </div>
                `;
            }
            
            html += `
                    </div>
                </div>
            `;
        }
    }
    
    // Display errors
    if (data.error_summary && data.error_summary.length > 0) {
        html += `
            <div class="result-panel">
                <div class="result-panel-header">
                    <h3 class="result-panel-title">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                        </svg>
                        Top Errors
                    </h3>
                    <span class="badge badge-error">${data.error_summary.length}</span>
                </div>
                <div class="result-panel-body">
                    <ul class="result-list">
                        ${data.error_summary.map(error => `
                            <li class="result-list-item">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                    <strong style="color: var(--openstack-red);">${escapeHtml(error.service)}</strong>
                                    <span class="badge badge-error">×${error.count}</span>
                                </div>
                                <div class="code-block" style="margin-bottom: 0.25rem;">${escapeHtml(error.line)}</div>
                                ${error.source_file ? `<div style="font-size: 0.75rem; color: var(--text-tertiary);">Source: ${escapeHtml(error.source_file)}</div>` : ''}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
    
    // Display port listeners
    if (data.listen_summary && data.listen_summary.length > 0) {
        html += `
            <div class="result-panel">
                <div class="result-panel-header">
                    <h3 class="result-panel-title">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
                        </svg>
                        Port Listeners Summary
                    </h3>
                    <span class="badge badge-info">${data.listen_summary.length}</span>
                </div>
                <div class="result-panel-body">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: var(--bg-tertiary); text-align: left;">
                                <th style="padding: 0.75rem; font-weight: 600;">Port</th>
                                <th style="padding: 0.75rem; font-weight: 600;">Process</th>
                                <th style="padding: 0.75rem; font-weight: 600;">Details</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.listen_summary.map((port, idx) => `
                                <tr style="border-bottom: 1px solid var(--border-color);">
                                    <td style="padding: 0.75rem;"><strong style="color: var(--accent-blue);">${escapeHtml(port.port)}</strong></td>
                                    <td style="padding: 0.75rem;">${port.process ? escapeHtml(port.process) : '<em>unknown</em>'}</td>
                                    <td style="padding: 0.75rem; font-size: 0.8125rem; color: var(--text-secondary);">${escapeHtml(port.full_line)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    // Display recommendations
    if (data.recommendations && data.recommendations.length > 0) {
        html += `
            <div class="result-panel">
                <div class="result-panel-header">
                    <h3 class="result-panel-title">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z"/>
                        </svg>
                        Suggested Next Steps
                    </h3>
                </div>
                <div class="result-panel-body">
                    <ul class="result-list">
                        ${data.recommendations.map(rec => `
                            <li class="result-list-item">
                                <div class="result-list-item-title" style="color: var(--accent-purple);">💡 ${escapeHtml(rec)}</div>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
    
    results.innerHTML = html;
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
