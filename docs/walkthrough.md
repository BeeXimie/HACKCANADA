# Architecture Consolidation Walkthrough

## The "Jekyll and Hyde" UI Bug

Prior to this update, the ScholarSync application was suffering from a "split personality" bug. 
- The React application (Port 3000) was attempting to render the Dashboard and the Applied Tracker.
- The Flask backend (Port 5000) was simultaneously trying to serve its own templates for those exact same routes (`/applied`, `/scholarships`). 

Because there was no clear "owner" for these routes, clicking links caused jarring shifts between the older React design and the newer Tailwind CSS light-mode design pushed by your teammate.

## What Was Fixed

### 1. Route Consolidation
I established a strict route ownership map. The React application now **only** handles the main Landing Page and the centralized `/dashboard` shell.

Every other feature page is now strictly owned by **Flask**:
- `/onboarding`
- `/profile`
- `/scholarships`
- `/applied`
- `/recommendations`
- `/essay`

### 2. Proxy Traffic Controller Updates
To enforce this ownership, I updated the React `setupProxy.js` file. Now, whenever the browser asks Port 3000 for any of the feature pages listed above, the Proxy transparently forwards that request to the Flask server at `127.0.0.1:5000`.

### 3. Navigation Hand-off
I modified the React Sidebar in `App.js`. Previously, it used React Router `<Link>` components, which prevented the browser from asking the server for new pages. These were converted to standard HTML `<a href="...">` tags, forcing a hard navigation so the Flask templates can take over.

### 4. UI Synchronization
I completely overhauled the React Dashboard's CSS (`App.css`). 
- **Before:** A dark, glassmorphic theme with `#080808` backgrounds.
- **After:** A bright, clean `#f8fafc` Light Theme directly matching the pristine Tailwind CSS utilized in your teammate's Flask templates.

## Result

The application now feels like a single, cohesive unit. You can transition seamlessly from the highly dynamic React Dashboard into the Flask-rendered Kanban board without noticing you crossed server boundaries.

````carousel
![React Dashboard (Light Theme)](/Users/tanishqmathur/.gemini/antigravity/brain/c7539bdc-2e11-41ed-8c9d-053a2ee72d81/dashboard_view_1772943773916.png)
<!-- slide -->
![Flask Applied Tracker (Tailwind)](/Users/tanishqmathur/.gemini/antigravity/brain/c7539bdc-2e11-41ed-8c9d-053a2ee72d81/applied_tracker_view_1772943905215.png)
````

## Webpack Build Failure & Rebase Issues

Shortly after consolidating the routes, the React frontend (`localhost:3000`) crashed with a `SyntaxError: Identifier 'handleLogin' has already been declared`. This was caused by a duplicate function declaration introduced during a `git rebase` containing a teammate's commits. This duplicate was identified and removed, fixing the build.

Additionally, the `frontend` folder was accidentally deleted from the file system during the rebase conflicts, causing the development server to exit. This was recovered by running `git restore frontend/` and rebuilding the `node_modules`.

## Severe Infinite Redirect Loop (Auth0 + Flask)

Following the route consolidation, users encountered an `ERR_TOO_MANY_REDIRECTS` error when attempting to navigate through the application.

### The Root Cause
The React application's Proxy redirects requests for `/onboarding` to the Flask backend. In `routes.py`, the backend was attempting to verify the user's authentication status using the `auth0.get_user()` SDK method.

However, the Python SDK relies on an `appSession` cookie that was not being properly populated because the login callback handler was manually assigning the user profile to Flask's native `session['user']` dictionary instead of using the fully managed SDK lifecycle. 

As a result:
1. React proxies user to `/onboarding`.
2. Flask checks `auth0.get_user()`, finds no `appSession` cookie, and redirects to `/login`.
3. Auth0 recognizes the user is already logged in and instantly bounces back to `/callback`.
4. `/callback` assigns `session['user']` and redirects to `/onboarding`.
5. The cycle repeats infinitely.

### The Fix
I conducted a full codebase audit and modified `routes.py`, replacing **all** instances of `auth0.get_user()` with Flask's native `session.get("user")`. Furthermore, orphaned `async/await` syntax left behind by the SDK was removed or properly wrapped in `run_async()`.

The proxy handshakes now correctly identify the user state, completely eliminating the loop.

## The Chrome "Magic Fill" Extension: Live DB + API Integration

After creating a highly cohesive UI, the final task was migrating the "Magic Fill" Chrome Extension from mock session endpoints to full production databases.

**Data Flow Overhaul**:
- **Proxy**: We extended `pathFilters` in `setupProxy.js` to natively pass `/api/ai` requests sent from the extension through the React port to the Python backend.
- **SQL Link**: The `/api/user/autofill-data` endpoint was entirely rewritten. Instead of pulling from temporary session variables, it now queries `User.query.filter_by()` using the user's `auth0_sub` ID. This ensures the extension has access to the user's *authentic* persistent profile (Name, GPA, Major, Institution) rather than ephemeral form state mapping correctly to different webpage names (ie reading 'Current College' and parsing it to `institution`).

**Live Gemini AI Essay Writer**:
We tore out the hardcoded 3-bullet-point system and completely rebuilt `/api/ai/draft-essay`. The backend now actively fetches the user's profile and dynamic experiences from the SQLite database. It composites this structured data along with the specific Scholarship Essay Prompt scraped directly off the application page by the Chrome Extension.

This payload is fired up to the `google-genai` client, instructing it to draft a personalized 3-bullet response exactly answering the prompt with the user's unique context.

We deployed an un-styled `mock_scholarship_form.html` to act as an external website test ground. Activating the "Magic Fill" bookmark successfully scraped the mocked page, read the SQLite database, and injected an authentic essay draft specifically formulated around the user's actual University of Waterloo Computer Science background.

![Chrome Extension Magic Fill Demo](/Users/tanishqmathur/.gemini/antigravity/brain/c7539bdc-2e11-41ed-8c9d-053a2ee72d81/magic_fill_result_1772954480333.png)
