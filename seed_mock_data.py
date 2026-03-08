import sqlite3
import os

DB_NAME = "scholarships.db"

def seed():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Re-verify or create scholarships table structure
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ouinfo_scholarships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            university TEXT,
            amount TEXT,
            deadline TEXT,
            type TEXT,
            url TEXT UNIQUE,
            description TEXT,
            eligibility TEXT,
            demographics TEXT,
            match_score INTEGER,
            match_reasoning TEXT
        )
    """)
    
    mock_scholarships = [
        (
            "Google Generation Scholarship",
            "Computer Science / Engineering",
            "$10,000",
            "2024-03-12",
            "Internal",
            "https://buildyourfuture.withgoogle.com/scholarships/generation-google-scholarship",
            "The Generation Google Scholarship was established to help aspiring computer scientists excel in technology and become leaders in the field.",
            "Must be currently enrolled in an undergraduate or graduate program.",
            "STEM, Underrepresented Groups",
            99,
            '["Matches your 3.9 GPA requirement", "Aligned with Computer Science major", "Strong leadership signals from extracurriculars"]'
        ),
        (
            "STEM Innovation Grant",
            "Various Institutions",
            "$1,500",
            "2024-03-20",
            "Internal",
            "https://example.com/stem-innovation",
            "Supports students pursuing innovative projects in STEM fields.",
            "Open to all STEM students with a focus on innovation.",
            "STEM",
            85,
            '["STEM focus matches your academic profile", "Innovation focus matches your interests"]'
        ),
        (
            "Global Leadership Award",
            "Various Institutions",
            "$20,000",
            "2024-03-05",
            "Internal",
            "https://example.com/global-leadership",
            "Recognizes students who have demonstrated exceptional leadership qualities on a global scale.",
            "Requires proof of international leadership experience.",
            "Global, Leadership",
            92,
            '["Leadership experience from your extracurricular activities", "International background is a plus"]'
        ),
        (
            "Amazon Future Engineer Scholarship",
            "Various Institutions",
            "$10,000",
            "2024-04-01",
            "External",
            "https://www.amazonfutureengineer.com/scholarship",
            "For high school seniors who intend to study computer science in college.",
            "High school senior, 3.0 GPA minimum.",
            "STEM, Computer Science",
            98,
            '["High academic standing", "Computer Science major"]'
        ),
        (
            "Microsoft Tuition Grant",
            "STEM Students",
            "$5,000",
            "2024-05-15",
            "External",
            "https://www.microsoft.com/en-us/diversity/programs/scholarships",
            "Microsoft is committed to helping the next generation of diverse tech leaders.",
            "Must be enrolled in a STEM program.",
            "STEM, Diversity",
            87,
            '["STEM focus matches your academic profile", "Diversity demographic matches"]'
        )
    ]
    
    print("Seeding mock scholarships...")
    for s in mock_scholarships:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO ouinfo_scholarships 
                (title, university, amount, deadline, type, url, description, eligibility, demographics, match_score, match_reasoning)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, s)
        except Exception as e:
            print(f"Error inserting {s[0]}: {e}")
            
    conn.commit()
    
    # Also check/create users table to ensure app doesn't crash
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auth0_sub TEXT UNIQUE NOT NULL,
            institution TEXT,
            major TEXT,
            degree TEXT,
            gpa TEXT,
            grad_year INTEGER,
            enrollment TEXT,
            income_bracket TEXT,
            first_gen TEXT,
            fafsa TEXT,
            aid_amount INTEGER,
            ethnicity TEXT,
            gender TEXT,
            location TEXT,
            disability TEXT,
            veteran TEXT,
            career_goals TEXT,
            interests TEXT,
            year_of_study TEXT,
            experiences_json TEXT DEFAULT '[]',
            resume_uploaded BOOLEAN DEFAULT 0,
            resume_filename TEXT,
            transcript_uploaded BOOLEAN DEFAULT 0,
            transcript_filename TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("Done! Scholarships and Users table are ready.")

if __name__ == "__main__":
    seed()
