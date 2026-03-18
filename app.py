import os
import re
from flask import Flask, render_template, request, redirect, session, send_file
from PyPDF2 import PdfReader
import docx

# ---------------- APP SETUP ---------------- #
app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------- TEXT EXTRACTION ---------------- #

def extract_text(file_path):
    text = ""

    if file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() or ""

    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"

    return text

# ---------------- CLEAN TEXT ---------------- #

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return text

# ---------------- ANALYSIS ---------------- #

def analyze_resume(text, skills):
    text = clean_text(text)

    matched = []
    missing = []

    for skill in skills:
        if skill.lower() in text:
            matched.append(skill)
        else:
            missing.append(skill)

    score = int((len(matched) / len(skills)) * 100) if skills else 0

    return score, matched, missing

# ---------------- RESUME GENERATOR ---------------- #

def generate_resume(text, role, skills):
    skill_str = ", ".join(skills)

    return f"""
===============================
        {role.upper()} RESUME
===============================

🎯 TARGET ROLE:
{role}

-------------------------------
🧠 PROFESSIONAL SUMMARY
Skilled in {skill_str}. Passionate developer.

-------------------------------
💻 SKILLS
{skill_str}

-------------------------------
📌 EXPERIENCE
{text[:500]}

-------------------------------
🚀 PROJECTS
- Built projects using {skill_str}

-------------------------------
📈 STRENGTHS
- Problem Solving
- Communication
"""

# ---------------- INTERVIEW QUESTIONS ---------------- #

def generate_questions(role, skills):
    return [
        f"What experience do you have as a {role}?",
        f"Explain {skills[0] if skills else 'your skills'}",
        "Tell me about your project",
        "Why should we hire you?"
    ]

# ---------------- PDF ---------------- #

def create_pdf(content):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    file_path = os.path.join("uploads", "resume.pdf")

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    story = []

    for line in content.split("\n"):
        story.append(Paragraph(line, styles["Normal"]))
        story.append(Spacer(1, 10))

    doc.build(story)

    return file_path

# ---------------- LOGIN (ANY PASSWORD WORKS) ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]

        # No password validation
        session["user"] = username

        return redirect("/")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# ---------------- MAIN APP ---------------- #

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    return render_template("index.html", user=session["user"])

@app.route("/analyze", methods=["POST"])
def analyze():
    if "user" not in session:
        return redirect("/login")

    file = request.files["resume"]
    role = request.form["role"]
    description = request.form["description"]

    skills = [s.strip() for s in description.split(",")]

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)

    text = extract_text(file_path)

    score, matched, missing = analyze_resume(text, skills)
    new_resume = generate_resume(text, role, skills)
    questions = generate_questions(role, skills)

    return render_template(
        "result.html",
        score=score,
        matched=matched,
        missing=missing,
        new_resume=new_resume,
        questions=questions
    )

@app.route("/download")
def download():
    content = request.args.get("content")
    file_path = create_pdf(content)
    return send_file(file_path, as_attachment=True)

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    print("🚀 Server running...")
    app.run(debug=True)