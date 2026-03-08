const API_BASE = 'http://localhost:5000/api';

const showFeedback = (message, isError = false) => {
    let el = document.getElementById('scholarsync-feedback');
    if (!el) {
        el = document.createElement('div');
        el.id = 'scholarsync-feedback';
        el.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            background: ${isError ? '#ff4d4f' : 'linear-gradient(135deg, #10b981 0%, #059669 100%)'};
            color: white;
            border-radius: 8px;
            font-family: system-ui, -apple-system, sans-serif;
            font-size: 14px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 999999;
            transition: opacity 0.3s ease;
        `;
        document.body.appendChild(el);
    }
    el.innerHTML = message;
    el.style.opacity = '1';
    
    if (!message.includes("thinking")) {
        setTimeout(() => {
            el.style.opacity = '0';
        }, 4000);
    }
    return el;
};

(async function initScholarSyncExtension() {
    showFeedback('🪄 ScholarSync activated. Fetching your profile...');
    
    try {
        const profileResponse = await fetch(`${API_BASE}/user/autofill-data`, {
            method: 'GET',
            mode: 'cors',
            credentials: 'include'
        });

        if (!profileResponse.ok) {
            throw new Error(profileResponse.status === 401 
                ? 'Please log into ScholarSync first on your local dashboard.' 
                : 'Failed to fetch profile.');
        }

        const profileData = await profileResponse.json();

        // Standard inputs
        const inputs = document.querySelectorAll('input, select');
        let filledCount = 0;

        inputs.forEach(input => {
            const name = (input.name || '').toLowerCase();
            const id = (input.id || '').toLowerCase();
            const labelText = (input.labels && input.labels[0] ? input.labels[0].innerText : '').toLowerCase();
            
            const identifier = `${name} ${id} ${labelText}`;

            // Name
            if (identifier.includes('first') || identifier.includes('given')) {
                input.value = profileData.firstName || '';
                filledCount++;
            } else if (identifier.includes('last') || identifier.includes('family') || identifier.includes('surname')) {
                input.value = profileData.lastName || '';
                filledCount++;
            } 
            // Email
            else if (identifier.includes('email')) {
                input.value = profileData.email || '';
                filledCount++;
            } 
            // Academic Profile
            else if (identifier.includes('gpa') || identifier.includes('grade')) {
                input.value = profileData.gpa || '';
                filledCount++;
            } else if (identifier.includes('major') || identifier.includes('degree') || identifier.includes('program')) {
                input.value = profileData.major || '';
                filledCount++;
            } else if (identifier.includes('university') || identifier.includes('school') || identifier.includes('institution') || identifier.includes('college')) {
                input.value = profileData.institution || '';
                filledCount++;
            } 
            // Address / Canadian forms
            else if (identifier.includes('province') || identifier.includes('state') || identifier.includes('location')) {
                input.value = profileData.location || '';
                filledCount++;
            } else if (identifier.includes('postal') || identifier.includes('zip')) {
                // Not mapped tightly in profile, but setup to capture forms looking for it
            }
        });

        // Essay scraping
        const textareas = document.querySelectorAll('textarea');
        let essayPrompt = null;
        let targetTextarea = null;

        textareas.forEach(textarea => {
            let context = '';
            if (textarea.labels && textarea.labels.length > 0) {
                context = textarea.labels[0].innerText;
            } else if (textarea.previousElementSibling) {
                context = textarea.previousElementSibling.innerText;
            }

            // Looks like a prompt paragraph
            if (context.length > 20 && !essayPrompt) {
                essayPrompt = context;
                targetTextarea = textarea;
            }
        });

        if (essayPrompt && targetTextarea && targetTextarea.value.length === 0) {
            showFeedback('🧠 Gemini is thinking about your essay drafting...');
            
            const aiResponse = await fetch(`${API_BASE}/ai/draft-essay`, {
                method: 'POST',
                mode: 'cors',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompt: essayPrompt })
            });

            if (aiResponse.ok) {
                const aiData = await aiResponse.json();
                targetTextarea.value = aiData.draft;
                showFeedback(`✅ ScholarSync applied your data! Filled ${filledCount} fields & drafted essay!`);
                alert(`ScholarSync applied your data! (Filled ${filledCount} fields & essay)`);
            } else {
                showFeedback(`✅ ScholarSync applied your data! Filled ${filledCount} fields, but essay draft failed.`, true);
                alert(`ScholarSync applied your data! (Essay AI failed)`);
            }
        } else {
            showFeedback(`✅ ScholarSync applied your data! Filled ${filledCount} basic profile fields.`);
            alert(`ScholarSync applied your data! (Filled ${filledCount} fields)`);
        }

    } catch (error) {
        console.error('ScholarSync Extension Error:', error);
        showFeedback(`❌ Error: ${error.message}`, true);
        alert(`ScholarSync Error: ${error.message}`);
    }
})();
