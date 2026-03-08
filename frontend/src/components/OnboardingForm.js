import React, { useState } from 'react';
import { Loader2, ArrowRight, ArrowLeft, UploadCloud, CheckCircle, FileText } from 'lucide-react';

const cities = ["Toronto", "Montreal", "Vancouver", "Calgary", "Edmonton", "Ottawa", "Winnipeg", "Quebec City", "Hamilton", "Kitchener", "London", "Victoria", "Halifax", "Oshawa", "Windsor", "Saskatoon", "Regina", "St. John's", "Kelowna", "Abbotsford"];

const OnboardingForm = () => {
    const [step, setStep] = useState(1);
    const [status, setStatus] = useState('idle'); // idle, parsing, saving, error
    const [errorMsg, setErrorMsg] = useState('');

    // Step 1 State
    const [location, setLocation] = useState('');
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [notInCanada, setNotInCanada] = useState(false);
    const [gender, setGender] = useState('');
    const [ethnicity, setEthnicity] = useState('');
    const [yearOfStudy, setYearOfStudy] = useState('');
    const [citizenship, setCitizenship] = useState('');
    const [incomeBracket, setIncomeBracket] = useState('');
    const [firstGen, setFirstGen] = useState('');
    const [enrollment, setEnrollment] = useState('');
    const [fafsa, setFafsa] = useState('');
    const [resumeFile, setResumeFile] = useState(null);
    const [transcriptFile, setTranscriptFile] = useState(null);

    // Step 2 State (Autofilled Profile)
    const [profile, setProfile] = useState({
        name: '', institution: '', major: '', degree: '',
        gpa_confirm: '', grad_year: '', interests: '', aid_amount: '', experiences: []
    });

    const filteredCities = cities.filter(c => c.toLowerCase().includes(location.toLowerCase()));

    const handleStep1Submit = async (e) => {
        e.preventDefault();

        if (!notInCanada && !cities.some(c => c.toLowerCase() === location.toLowerCase())) {
            setErrorMsg('Please select a valid Canadian city or check "Outside of Canada".');
            return;
        }
        setErrorMsg('');
        setStatus('parsing');

        const formData = new FormData();
        formData.append('location', notInCanada ? 'International' : location);
        formData.append('gender', gender);
        formData.append('ethnicity', ethnicity);
        formData.append('year_of_study', yearOfStudy);
        formData.append('citizenship', citizenship);
        formData.append('income_bracket', incomeBracket);
        formData.append('first_gen', firstGen);
        formData.append('enrollment', enrollment);
        formData.append('fafsa', fafsa);
        if (resumeFile) formData.append('resume', resumeFile);
        if (transcriptFile) formData.append('transcript', transcriptFile);

        try {
            const res = await fetch('/api/user/onboarding', {
                method: 'POST',
                headers: { 'Accept': 'application/json' },
                credentials: 'include',
                body: formData
            });
            const rawText = await res.text();
            console.log('Flask status:', res.status, 'response:', rawText.substring(0, 300));
            let data;
            try { data = JSON.parse(rawText); } catch(e) {
                setStatus('error');
                setErrorMsg('Non-JSON from Flask (status ' + res.status + '): ' + rawText.substring(0, 200));
                return;
            }
            if (res.ok && data.status === 'ok') {
                const p = data.profile || {};
                console.log('Profile fields:', Object.keys(p));
                setProfile(prev => ({
                    ...prev,
                    institution: p.institution || '',
                    major: p.major || '',
                    degree: p.degree || '',
                    grad_year: p.grad_year ? String(p.grad_year) : '',
                    experiences: (p.experiences || []).map(e => ({
                        company: e.company || '',
                        role: e.role || '',
                        start_date: e.start_date || '',
                        end_date: e.end_date || '',
                        current: e.current || false,
                        description: e.description || ''
                    })),
                    interests: Array.isArray(p.interests) ? p.interests.join(', ') : (p.interests || '')
                }));
                setStatus('idle');
                setStep(2);
            } else {
                setStatus('error');
                setErrorMsg('Error (status ' + res.status + '): ' + JSON.stringify(data).substring(0, 200));
            }
        } catch (err) {
            setStatus('error');
            setErrorMsg('Network error. Is Flask running on port 5000?');
        }
    };

    const handleStep2Change = (e) => {
        const { name, value } = e.target;
        setProfile(prev => ({ ...prev, [name]: value }));
    };

    const handleExpChange = (i, field, value) => {
        const arr = [...profile.experiences];
        arr[i] = { ...arr[i], [field]: value };
        setProfile(prev => ({ ...prev, experiences: arr }));
    };

    const handleAddExp = () => setProfile(prev => ({ ...prev, experiences: [...prev.experiences, { company: '', role: '', start_date: '', end_date: '', current: false }] }));
    const handleRemoveExp = (i) => setProfile(prev => ({ ...prev, experiences: prev.experiences.filter((_, idx) => idx !== i) }));

    const handleStep2Submit = async (e) => {
        e.preventDefault();
        setStatus('saving');
        const formData = new FormData();
        Object.entries(profile).forEach(([k, v]) => {
            if (k === 'experiences') {
                v.forEach(exp => {
                    formData.append('exp_company[]', exp.company || '');
                    formData.append('exp_role[]', exp.role || '');
                    formData.append('exp_start[]', exp.start_date || '');
                    formData.append('exp_end[]', exp.end_date || '');
                    formData.append('exp_current[]', exp.current ? 'true' : 'false');
                    formData.append('exp_volunteer[]', 'false');
                    formData.append('exp_hours[]', '');
                    formData.append('exp_desc[]', exp.description || '');
                });
            } else {
                formData.append(k, v);
            }
        });
        formData.append('institution', profile.institution);
        try {
            const res = await fetch('/api/user/onboarding', { method: 'POST', headers: { 'Accept': 'application/json' }, body: formData });
            if (res.ok) {
                setStatus('idle');
                window.location.href = '/dashboard';
            } else {
                setStatus('error');
                setErrorMsg('Failed to save profile.');
            }
        } catch {
            setStatus('error');
            setErrorMsg('Network error.');
        }
    };

    const is = { width: '100%', padding: '0.8rem 1rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: 'white', fontSize: '0.9rem', outline: 'none' };
    const ls = { display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#888', marginBottom: '0.5rem', fontWeight: '600' };
    const divider = { margin: '2rem 0', height: '1px', background: 'rgba(255,255,255,0.05)' };

    return (
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            {/* Progress header */}
            <div style={{ marginBottom: '2rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                    <span style={{ padding: '0.25rem 0.75rem', background: 'rgba(129,140,248,0.1)', color: 'var(--accent-primary)', fontSize: '0.75rem', fontWeight: 'bold', borderRadius: '99px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Step {step} of 2</span>
                    <div style={{ flex: 1, height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
                        <div style={{ width: step === 1 ? '50%' : '100%', height: '100%', background: 'var(--accent-primary)', transition: 'width 0.5s ease' }} />
                    </div>
                </div>
                <h1 style={{ fontSize: '2rem', fontWeight: '800', marginBottom: '0.5rem' }}>{step === 1 ? 'Tell us about yourself' : 'Review AI Autofill'}</h1>
                <p style={{ color: '#888' }}>{step === 1 ? "Upload your resume and we'll autofill everything." : "Verify the data Gemini parsed from your documents."}</p>
            </div>

            {errorMsg && <div style={{ padding: '1rem', background: 'rgba(255,100,100,0.1)', border: '1px solid rgba(255,100,100,0.2)', color: '#ff8080', borderRadius: '12px', marginBottom: '1.5rem' }}>{errorMsg}</div>}

            {/* STEP 1 */}
            {step === 1 && (
                <form onSubmit={handleStep1Submit} className="module-card">
                    <h3 style={{ fontSize: '1.1rem', fontWeight: '700', marginBottom: '1.5rem', color: 'var(--accent-primary)' }}>Demographics</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                        {/* Location */}
                        <div style={{ position: 'relative' }}>
                            <label style={ls}>Location</label>
                            <input style={is} value={location} onChange={e => { setLocation(e.target.value); setShowSuggestions(true); }} placeholder="Search Canadian cities..." disabled={notInCanada} />
                            {showSuggestions && location && !notInCanada && (
                                <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: '#111', border: '1px solid rgba(255,255,255,0.1)', zIndex: 10, borderRadius: '0 0 12px 12px', maxHeight: '150px', overflowY: 'auto' }}>
                                    {filteredCities.map(c => <div key={c} style={{ padding: '0.6rem 1rem', cursor: 'pointer', borderBottom: '1px solid rgba(255,255,255,0.05)' }} onClick={() => { setLocation(c); setShowSuggestions(false); }}>{c}</div>)}
                                </div>
                            )}
                            <div style={{ marginTop: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <input type="checkbox" checked={notInCanada} onChange={e => { setNotInCanada(e.target.checked); setLocation(''); }} />
                                <span style={{ fontSize: '0.8rem', color: '#888' }}>Outside of Canada</span>
                            </div>
                        </div>
                        <div><label style={ls}>Gender</label><select style={is} value={gender} onChange={e => setGender(e.target.value)} required><option value="" disabled>Select</option><option>Male</option><option>Female</option><option>Non-binary</option><option>Prefer not to say</option></select></div>
                        <div><label style={ls}>Ethnicity</label><select style={is} value={ethnicity} onChange={e => setEthnicity(e.target.value)} required><option value="" disabled>Select</option><option>Indigenous</option><option>Black</option><option>Asian</option><option>White</option><option>Hispanic</option><option>Other</option></select></div>
                        <div><label style={ls}>Year of Study</label><select style={is} value={yearOfStudy} onChange={e => setYearOfStudy(e.target.value)} required><option value="" disabled>Select</option><option>Incoming First Year</option><option>1st Year</option><option>2nd Year</option><option>3rd Year</option><option>4th Year</option><option>Graduate</option></select></div>
                        <div><label style={ls}>Citizenship</label><select style={is} value={citizenship} onChange={e => setCitizenship(e.target.value)} required><option value="" disabled>Select</option><option value="Domestic">Domestic (Citizen/PR)</option><option value="International">International (Visa)</option></select></div>
                    </div>

                    <div style={divider} />
                    <h3 style={{ fontSize: '1.1rem', fontWeight: '700', marginBottom: '1.5rem' }}>Eligibility & Aid</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                        <div><label style={ls}>Household Income</label><select style={is} value={incomeBracket} onChange={e => setIncomeBracket(e.target.value)} required><option value="" disabled>Select</option><option>Under $30,000</option><option>$30,000 – $60,000</option><option>$60,000 – $100,000</option><option>$100,000 – $150,000</option><option>Over $150,000</option><option>Prefer not to say</option></select></div>
                        <div><label style={ls}>First-Gen Student?</label><select style={is} value={firstGen} onChange={e => setFirstGen(e.target.value)} required><option value="" disabled>Select</option><option value="yes">Yes</option><option value="no">No</option></select></div>
                        <div><label style={ls}>Enrollment Status</label><select style={is} value={enrollment} onChange={e => setEnrollment(e.target.value)} required><option value="" disabled>Select</option><option>Full-time</option><option>Part-time</option></select></div>
                        <div><label style={ls}>Filed for Financial Aid?</label><select style={is} value={fafsa} onChange={e => setFafsa(e.target.value)} required><option value="" disabled>Select</option><option>Yes</option><option>No</option></select></div>
                    </div>

                    <div style={divider} />
                    <h3 style={{ fontSize: '1.1rem', fontWeight: '700', marginBottom: '0.5rem' }}>AI Autofill</h3>
                    <p style={{ color: '#888', fontSize: '0.85rem', marginBottom: '1.5rem' }}>Upload a PDF resume and Gemini 2.5 Flash will autofill Step 2.</p>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                        <label style={{ display: 'block', border: `2px dashed ${resumeFile ? 'rgba(52,211,153,0.4)' : 'rgba(255,255,255,0.1)'}`, background: 'rgba(255,255,255,0.02)', padding: '2rem', textAlign: 'center', borderRadius: '16px', cursor: 'pointer' }}>
                            <input type="file" style={{ display: 'none' }} onChange={e => setResumeFile(e.target.files[0])} accept=".pdf,.doc,.docx" />
                            <UploadCloud size={32} color={resumeFile ? '#34d399' : 'var(--accent-primary)'} style={{ margin: '0 auto 0.5rem' }} />
                            <p style={{ fontSize: '0.9rem', fontWeight: 'bold', color: resumeFile ? '#34d399' : 'var(--accent-primary)' }}>{resumeFile ? resumeFile.name : 'Upload Resume (PDF)'}</p>
                            <p style={{ fontSize: '0.75rem', color: '#666', marginTop: '0.25rem' }}>Required for autofill</p>
                        </label>
                        <label style={{ display: 'block', border: `2px dashed ${transcriptFile ? 'rgba(52,211,153,0.4)' : 'rgba(255,255,255,0.06)'}`, background: 'rgba(255,255,255,0.01)', padding: '2rem', textAlign: 'center', borderRadius: '16px', cursor: 'pointer' }}>
                            <input type="file" style={{ display: 'none' }} onChange={e => setTranscriptFile(e.target.files[0])} accept=".pdf,.png,.jpg,.jpeg" />
                            <FileText size={32} color={transcriptFile ? '#34d399' : '#555'} style={{ margin: '0 auto 0.5rem' }} />
                            <p style={{ fontSize: '0.9rem', fontWeight: 'bold', color: transcriptFile ? '#34d399' : '#666' }}>{transcriptFile ? transcriptFile.name : 'Upload Transcript'}</p>
                            <p style={{ fontSize: '0.75rem', color: '#555', marginTop: '0.25rem' }}>Optional</p>
                        </label>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2.5rem' }}>
                        <button type="submit" className="auth-button" disabled={status === 'parsing'} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--accent-primary)', color: 'white', border: 'none', minWidth: '200px', justifyContent: 'center' }}>
                            {status === 'parsing' ? <><Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> Analyzing with AI...</> : <>Autofill & Continue <ArrowRight size={18} /></>}
                        </button>
                    </div>
                </form>
            )}

            {/* STEP 2 */}
            {step === 2 && (
                <form onSubmit={handleStep2Submit} className="module-card">
                    <p style={{ color: '#34d399', fontSize: '0.85rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CheckCircle size={16} /> AI autofill complete — review and edit anything below.</p>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
                        <div><label style={ls}>Full Name</label><input style={is} name="name" value={profile.name} onChange={handleStep2Change} /></div>
                        <div><label style={ls}>Institution</label><input style={is} name="institution" value={profile.institution} onChange={handleStep2Change} /></div>
                        <div><label style={ls}>Major</label><input style={is} name="major" value={profile.major} onChange={handleStep2Change} /></div>
                        <div><label style={ls}>Degree Type</label><input style={is} name="degree" value={profile.degree} onChange={handleStep2Change} /></div>
                        <div><label style={ls}>Cumulative GPA</label><input style={is} name="gpa_confirm" value={profile.gpa_confirm} onChange={handleStep2Change} /></div>
                        <div><label style={ls}>Expected Graduation</label><input style={is} name="grad_year" value={profile.grad_year} onChange={handleStep2Change} /></div>
                        <div style={{ gridColumn: '1/-1' }}><label style={ls}>Aid Needed ($)</label><input style={is} type="number" name="aid_amount" value={profile.aid_amount} onChange={handleStep2Change} /></div>
                        <div style={{ gridColumn: '1/-1' }}><label style={ls}>Areas of Interest</label><input style={is} name="interests" value={profile.interests} onChange={handleStep2Change} placeholder="e.g. Machine Learning, Finance" /></div>
                    </div>

                    <div style={divider} />
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                        <h3 style={{ fontSize: '1.1rem', fontWeight: '700', margin: 0 }}>Experiences</h3>
                        <button type="button" onClick={handleAddExp} style={{ background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid rgba(255,255,255,0.1)', padding: '0.4rem 0.8rem', borderRadius: '8px', fontSize: '0.8rem', cursor: 'pointer' }}>+ Add</button>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                        {profile.experiences.map((exp, i) => (
                            <div key={i} style={{ background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', position: 'relative' }}>
                                <button type="button" onClick={() => handleRemoveExp(i)} style={{ position: 'absolute', top: '1rem', right: '1rem', color: '#ff8080', background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.8rem' }}>Remove</button>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                    <div><label style={ls}>Company / Org</label><input style={is} value={exp.company || ''} onChange={e => handleExpChange(i, 'company', e.target.value)} /></div>
                                    <div><label style={ls}>Role / Title</label><input style={is} value={exp.role || ''} onChange={e => handleExpChange(i, 'role', e.target.value)} /></div>
                                    <div><label style={ls}>Start Date</label><input style={is} value={exp.start_date || ''} onChange={e => handleExpChange(i, 'start_date', e.target.value)} placeholder="MM/YYYY" /></div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', justifyContent: 'flex-end' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><input type="checkbox" checked={!!exp.current} onChange={e => handleExpChange(i, 'current', e.target.checked)} /><span style={{ fontSize: '0.8rem', color: '#888' }}>Current</span></div>
                                        {!exp.current && <input style={is} value={exp.end_date || ''} onChange={e => handleExpChange(i, 'end_date', e.target.value)} placeholder="End MM/YYYY" />}
                                    </div>
                                </div>
                            </div>
                        ))}
                        {profile.experiences.length === 0 && <p style={{ color: '#555', textAlign: 'center', padding: '1.5rem', fontSize: '0.9rem' }}>No experiences parsed. Click "+ Add" to add manually.</p>}
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2.5rem' }}>
                        <button type="button" onClick={() => setStep(1)} className="auth-button" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><ArrowLeft size={18} /> Back</button>
                        <button type="submit" className="auth-button" disabled={status === 'saving'} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--accent-primary)', color: 'white', border: 'none', minWidth: '180px', justifyContent: 'center' }}>
                            {status === 'saving' ? <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> : <><CheckCircle size={18} /> Complete Onboarding</>}
                        </button>
                    </div>
                </form>
            )}
        </div>
    );
};

export default OnboardingForm;
