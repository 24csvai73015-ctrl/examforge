from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io

def generate_pdf(exam_name: str, subject_name: str, questions: list) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        spaceAfter=12,
        alignment=1 # Center
    )
    
    subject_style = ParagraphStyle(
        'SubjectStyle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        spaceAfter=24,
        alignment=1 # Center
    )
    
    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        spaceAfter=12,
        leading=16
    )
    
    Story = []
    
    Story.append(Paragraph(exam_name, title_style))
    Story.append(Paragraph(subject_name, subject_style))
    
    Story.append(Spacer(1, 12))
    
    total_marks = sum(q.get('marks', 0) for q in questions)
    
    instructions = f"Total Marks: {total_marks}"
    Story.append(Paragraph(instructions, styles['Normal']))
    Story.append(Spacer(1, 24))
    
    for idx, q in enumerate(questions, 1):
        q_text = f"<b>Q{idx}.</b> {q.get('question_text', '')}"
        marks_text = f"[{q.get('marks', 0)} Marks]"
        
        p_text = f"{q_text} <font color=grey><i>{marks_text}</i></font>"
        Story.append(Paragraph(p_text, question_style))
        Story.append(Spacer(1, 12))
        
    doc.build(Story)
    buffer.seek(0)
    return buffer
