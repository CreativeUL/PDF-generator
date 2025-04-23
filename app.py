
import streamlit as st
from bs4 import BeautifulSoup
import requests
from fpdf import FPDF
from PIL import Image
from io import BytesIO
import tempfile
import re

st.set_page_config(page_title="Urban Ladder PDF Generator", layout="centered")

def fetch_product_details(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    title = soup.find('h1').text.strip()
    price = soup.find('div', {'class': 'price'}).text.strip().split("₹")[-1].strip()

    # Highlights
    highlights_tag = soup.find('div', {'id': 'h2-highlight'})
    highlights = highlights_tag.get_text(separator="\n", strip=True) if highlights_tag else "Highlights not found."

    # Specs
    specs = []
    for spec in soup.select('.spec-section .spec-row'):
        label = spec.find(class_="spec-label")
        value = spec.find(class_="spec-value")
        if label and value:
            specs.append(f"{label.text.strip()}: {value.text.strip()}")

    # Dimensions (optional fallback)
    dims = soup.find(string=re.compile("Dimensions"))
    dimensions = dims.find_next().text.strip() if dims else ""

    # Image
    img_tag = soup.find('img', {'class': 'product-image'})
    img_url = img_tag['src'] if img_tag else None
    img_data = requests.get(img_url).content if img_url else None

    return {
        "title": title,
        "price": price,
        "highlights": highlights,
        "specs": specs,
        "dimensions": dimensions,
        "image": img_data
    }

def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, txt=data["title"], ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Price: ₹{data['price']}", ln=True, align='L')

    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt="Highlights", ln=True)
    pdf.set_font("Arial", size=11)
    for line in data["highlights"].split('\n'):
        pdf.multi_cell(0, 8, txt=line)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt="Specifications", ln=True)
    pdf.set_font("Arial", size=11)
    for spec in data["specs"]:
        pdf.multi_cell(0, 8, txt=spec)

    pdf.add_page()
    if data["image"]:
        image = Image.open(BytesIO(data["image"]))
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmpfile:
            image.save(tmpfile.name, "JPEG")
            pdf.image(tmpfile.name, x=10, y=20, w=180)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        return tmp.name

# UI
st.title("🛋️ Urban Ladder PDF Generator")
url = st.text_input("Paste Urban Ladder product URL")

if url:
    with st.spinner("Fetching details..."):
        try:
            data = fetch_product_details(url)
            pdf_file = generate_pdf(data)
            st.success("PDF generated!")
            st.download_button("📄 Download PDF", open(pdf_file, "rb"), file_name="product.pdf")
        except Exception as e:
            st.error(f"Something went wrong: {e}")
