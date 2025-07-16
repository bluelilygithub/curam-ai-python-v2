// Load system status on page load
window.addEventListener('load', function() {
    loadSystemStatus();
});

async function loadSystemStatus() {
    try {
        // Use relative path for subdirectory deployment
        const response = await fetch('../health');
        const data = await response.json();
        
        // Update system status
        document.getElementById('system-status').innerHTML = `
            <div><span class="status-indicator status-ok"></span>Status: ${data.status}</div>
            <div>Python: ${data.python_version}</div>
            <div>Flask: ${data.flask_version}</div>
        `;
        
        // Update API status
        const apiStatus = data.environment_variables;
        document.getElementById('api-status').innerHTML = Object.entries(apiStatus)
            .map(([key, value]) => `
                <div>
                    <span class="status-indicator ${value === 'Set' ? 'status-ok' : 'status-error'}"></span>
                    ${key}: ${value}
                </div>
            `).join('');
        
        // Update library status
        const libStatus = data.library_availability;
        document.getElementById('library-status').innerHTML = Object.entries(libStatus)
            .map(([key, value]) => `
                <div>
                    <span class="status-indicator ${value ? 'status-ok' : 'status-error'}"></span>
                    ${key}: ${value ? 'Available' : 'Missing'}
                </div>
            `).join('');
        
        // Update client status
        const clientStatus = data.client_status;
        document.getElementById('client-status').innerHTML = Object.entries(clientStatus)
            .map(([key, value]) => `
                <div>
                    <span class="status-indicator ${value ? 'status-ok' : 'status-error'}"></span>
                    ${key}: ${value ? 'Ready' : 'Not Initialized'}
                </div>
            `).join('');
            
    } catch (error) {
        document.getElementById('system-status').innerHTML = 
            `<div class="error">Error loading status: ${error.message}</div>`;
    }
}

async function testLLM(service) {
    const responseArea = document.getElementById('test-response');
    const message = document.getElementById('test-message').value;
    
    responseArea.style.display = 'block';
    responseArea.innerHTML = `<div class="loading">Testing ${service}...</div>`;
    
    try {
        const response = await fetch(`../api/test-${service}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        if (data.success) {
            responseArea.innerHTML = `
                <div class="success">✅ ${data.service} Test Successful</div>
                <div><strong>Response:</strong></div>
                <div>${escapeHtml(data.response)}</div>
                <div><small>Timestamp: ${data.timestamp}</small></div>
            `;
        } else {
            responseArea.innerHTML = `
                <div class="error">❌ ${data.service || service} Test Failed</div>
                <div><strong>Error:</strong> ${escapeHtml(data.error)}</div>
                ${data.details ? `<div><strong>Details:</strong> ${escapeHtml(data.details)}</div>` : ''}
            `;
        }
    } catch (error) {
        responseArea.innerHTML = `
            <div class="error">❌ Network Error</div>
            <div><strong>Error:</strong> ${escapeHtml(error.message)}</div>
        `;
    }
}

async function testFeeds() {
    const responseArea = document.getElementById('test-response');
    
    responseArea.style.display = 'block';
    responseArea.innerHTML = `<div class="loading">Testing RSS feeds...</div>`;
    
    try {
        const response = await fetch('../api/test-feeds');
        const data = await response.json();
        
        if (data.success) {
            responseArea.innerHTML = `
                <div class="success">✅ RSS Feed Test Successful</div>
                <div><strong>Feed:</strong> ${escapeHtml(data.feed_title)}</div>
                <div><strong>Entries found:</strong> ${data.entries_count}</div>
                <div><strong>Sample entries:</strong></div>
                ${data.sample_entries.map(entry => `
                    <div class="feed-entry">
                        <strong>${escapeHtml(entry.title)}</strong>
                        <small>${escapeHtml(entry.published)}</small>
                    </div>
                `).join('')}
                <div><small>Timestamp: ${data.timestamp}</small></div>
            `;
        } else {
            responseArea.innerHTML = `
                <div class="error">❌ RSS Feed Test Failed</div>
                <div><strong>Error:</strong> ${escapeHtml(data.error)}</div>
                ${data.details ? `<div><strong>Details:</strong> ${escapeHtml(data.details)}</div>` : ''}
            `;
        }
    } catch (error) {
        responseArea.innerHTML = `
            <div class="error">❌ Network Error</div>
            <div><strong>Error:</strong> ${escapeHtml(error.message)}</div>
        `;
    }
}

// Utility function to escape HTML and prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}