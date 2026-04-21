import os

os.environ["GROQ_API_KEY"] = ""
os.environ["TAVILY_API_KEY"] = ""
from tavily import TavilyClient

tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])from langchain_groq import ChatGroq
from tavily import TavilyClient

llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
    temperature=0
)

tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def search_web(query):
    response = tavily.search(query=query, search_depth="advanced")

    results = []
    for r in response["results"]:
        results.append(f"Source: {r['url']}\nContent: {r['content']}")

    return "\n\n".join(results)

from langchain_groq import ChatGroq

llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
    temperature=0
)

def legal_agent(query): #latest
    results = tavily.search(query=query, search_depth="advanced", max_results=5)

    sources = []
    context = ""   

    for r in results["results"]:
        sources.append(r["url"])
        context += r["content"] + "\n\n"


    prompt = f"""
    You are a professional legal researcher.

    STRICT FORMAT (follow exactly):

    Topic:
    <paragraph>

    Key Laws or Acts:
    1. <law name>: <description>

    Important Points:
    - point
    - point

    Conclusion:
    <short paragraph>

    DO NOT use:
    - ** symbols
    - ### symbols

    Query: {query}

    Context:
    {context}
    """

    response = llm.invoke(prompt)

    report = response.content

    source_text = "\n\nSources:\n"
    for i, s in enumerate(sources, 1):
        source_text += f"{i}. {s}\n"

    return report + source_text


from fpdf import FPDF
import re

def clean_text(text):
    return re.sub(r'[^\x00-\xFF]+', '', text)

def generate_pdf(text, query):   
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 12, query, ln=True, align="C")
    pdf.ln(5)

    text = clean_text(text)
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if line.lower().startswith("topic"):
          continue

        if not line:
            pdf.ln(3)
            continue

        # 🔴 MAIN HEADINGS
        if line.lower().startswith("clear explanation"):
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Clear Explanation", ln=True)
            pdf.ln(2)

        elif line.lower().startswith("key laws"):
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Key Laws or Acts", ln=True)
            pdf.ln(2)

        elif line.lower().startswith("important points"):
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Important Points", ln=True)
            pdf.ln(2)

        elif line.lower().startswith("conclusion"):
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Conclusion", ln=True)
            pdf.ln(2)

        # 🔹 NUMBERED LIST
        elif re.match(r'^\d+\.', line):
          pdf.set_font("Arial", size=11)
        # Extract number and text
          number, content = line.split(".", 1)
          number = number + "."
          content = content.strip()

        # Print number
          pdf.set_x(10)
          pdf.cell(10, 6, number)

    # Print content with proper wrapping
          x_current = pdf.get_x()
          y_current = pdf.get_y()

          pdf.multi_cell(0, 6, content)

          pdf.ln(1)

        # 🔹 BULLETS
        elif line.startswith("-"):
            pdf.set_font("Arial", size=11)
            pdf.set_x(15)
            pdf.multi_cell(0, 6, "- " + line[1:].strip())
            pdf.ln(1)

        # 🔹 NORMAL TEXT
        else:
            pdf.set_font("Arial", size=11)
            pdf.set_x(10)
            pdf.multi_cell(0, 7, line)
            pdf.ln(1)

    file_path = "/content/legal_report.pdf"
    pdf.output(file_path)

    return file_path

import gradio as gr #latest-
def is_legal_keyword(query):
    keywords = [
        "law", "legal", "act", "rights", "crime",
        "cyber", "court", "ipc", "constitution",
        "section", "regulation", "privacy",
        "penalty", "offence", "contract"
    ]

    query_lower = query.lower()
    return any(k in query_lower for k in keywords)


def process(query):
    try:
        if not query:
            return "⚠️ Please enter a query.", None

        if is_legal_keyword(query):
            report = legal_agent(query)
            pdf_file = generate_pdf(report, query)
            return report, pdf_file
        else:
            return """❌ Only legal queries are allowed.

Examples:
- Cybercrime laws in India
- IT Act 2000
- Data privacy laws
""", None

    except Exception as e:
        return f"❌ ERROR:\n{str(e)}", None




with gr.Blocks(theme=gr.themes.Soft()) as app:

    gr.Markdown("# ⚖️ Autonomous Legal Research AI")
    gr.Markdown("### Get professional legal insights with sources & downloadable reports")

    query = gr.Textbox(
        label="Enter Legal Query",
        placeholder="e.g. What are cybercrime laws in India?",
        lines=2
    )

    with gr.Row():
        submit = gr.Button("🔍 Research")
        clear = gr.Button("❌ Clear")

    output = gr.Markdown()  
    pdf_output = gr.File(label="📥 Download Report")

    submit.click(process, inputs=query, outputs=[output, pdf_output], show_progress=True)
    clear.click(lambda: ("", None), None, [output, pdf_output])

    gr.Examples(
        examples=[
            "What are data privacy laws in India?",
            "Is web scraping legal in India?",
            "What are penalties for cybercrime in India?",
            "Explain IT Act 2000 in India"
        ],
        inputs=[query]
    )

app.launch()
