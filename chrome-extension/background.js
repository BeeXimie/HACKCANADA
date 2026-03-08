const API_BASE = 'http://localhost:5000/api';

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'FETCH_PROFILE') {
        fetch(`${API_BASE}/user/autofill-data`, {
            method: 'GET',
            mode: 'cors',
            credentials: 'include' // This sends Auth0 cookies because background possesses host_permissions
        })
        .then(res => {
            if (!res.ok) throw new Error(res.status === 401 ? 'Please log into ScholarSync first on your local dashboard.' : 'Failed to fetch profile.');
            return res.json();
        })
        .then(data => sendResponse({ success: true, data }))
        .catch(error => sendResponse({ success: false, error: error.message }));
        
        return true; // Keep message channel open for async fetch
    }

    if (request.type === 'DRAFT_ESSAY') {
        fetch(`${API_BASE}/ai/draft-essay`, {
            method: 'POST',
            mode: 'cors',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: request.prompt })
        })
        .then(res => {
            if (!res.ok) throw new Error('AI drafting failed.');
            return res.json();
        })
        .then(data => sendResponse({ success: true, data }))
        .catch(error => sendResponse({ success: false, error: error.message }));
        
        return true; // Keep message channel open for async fetch
    }
});
