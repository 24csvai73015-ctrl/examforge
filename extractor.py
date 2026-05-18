import pdfplumber
import PyPDF2

def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract text dynamically from uploaded PDF file.
    """
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        # Fallback to PyPDF2 if pdfplumber fails
        pdf_file.seek(0)
        reader = PyPDF2.PdfReader(pdf_file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text
