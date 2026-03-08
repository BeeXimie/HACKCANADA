# Chrome Extension Real Data Integration

We will finalize the Chrome Extension by wiring it up to the live SQLite database (`scholarships.db`) and the active Gemini AI backend, moving away from mock data.

## Proposed Changes

### Configuration
#### [MODIFY] `frontend/src/setupProxy.js`
- Append the `/api/ai` and `/api/user/autofill-data` paths to the `pathFilter` array to ensure proxy passthrough from Port 3000 to Port 5000.

### Backend Routing & Logic
#### [MODIFY] `routes.py`
-  Update `/api/user/autofill-data`:
    - Rather than reading from the ephemeral `session['scholarship_profile']`, query the `User` model using `db_user = User.query.filter_by(auth0_sub=user['sub']).first()`.
    - Extract the user's real first name, last name, GPA, Major, and Institution from the `db_user` object.
- Update `/api/ai/draft-essay`:
    - Remove the hardcoded 3-bullet mock response.
    - Query the `User` model to retrieve the student's real profile data.
    - Format a prompt combining the student's actual profile (GPA, Major, Experiences, Interests) with the incoming Chrome Extension `prompt` (the specific scholarship essay question).
    - Call the `google-genai` client using the configured `GEMINI_API_KEY` to generate a customized 3-bullet response.

### Testing Site
#### [NEW] `mock_scholarship_form.html`
- Create a realistic local HTML file with input IDs (e.g., `first-name-input`, `candidate_gpa`) that purposely differ slightly from our DB columns to test the extension's fuzzy matching heuristics.
- Include a text area for an essay question and a button to trigger the Gemini integration.

## Verification Plan

### Automated Tests
- Validate that the proxy successfully forwards requests to `/api/ai/draft-essay` without returning a 404 or CORS error.

### Manual Verification
- Open `mock_scholarship_form.html` in Chrome.
- Ensure the user is logged into Port 3000.
- Click the "Magic Fill" extension button.
- Verify that standard fields (Name, GPA) populate with data pulled from `scholarships.db`.
- Trigger the AI essay writer on the mock form and verify that the 3-bullet response accurately reflects the user's saved profile traits.
