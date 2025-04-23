import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from fpdf import FPDF
import qrcode
from PIL import Image
import tempfile
import os

# Setup Streamlit
st.set_page_config(page_title="Urban Ladder PDF Generator", layout="centered")
st.title("🛋️ Urban Ladder PDF Generator (Selenium)")

# Configure Selenium (headless)
def setup_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def fetch_product_details(url):
    driver = setup_selenium()
    driver.get(url)
    time.sleep(3)  # Wait for dynamic content
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()  # Close browser

    # Extract title
    title = soup.find("h1", class_="product-title").text.strip()
    
    # Extract price (dynamic class)
    price = soup.find("span", class_="final-price").text.strip()
    
    # Extract features (bullet points)
    features = []
    features_section = soup.find("div", class_="product-features")
    if features_section:
        features = [li.text.strip() for li in features_section.find_all("li")]
    
    # Extract specs (material, dimensions)
    specs = {}
    for row in soup.select(".specs-table tr"):
        key = row.find("th").text.strip()
        value = row.find("td").text.strip()
        specs[key] = value
    
    # Extract image
    img_tag = soup.find("img", class_="product-hero-image")
    img_url = img_tag["src"] if img_tag else None
    
    return {
        "title": title,
        "price": price,
        "material": specs.get("Material", "N/A"),
        "dimensions": specs.get("Dimensions", "N/A"),
        "features": features,
        "img_url": img_url,
        "url": url
    }

def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, data["title"], 0, 1, "C")
    
    # Price
    pdf.set_font("Arial", "", 16)
    pdf.cell(0, 10, f"Price: {data['price']}", 0, 1, "C")
    pdf.ln(10)
    
    # Features
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Features:", 0, 1)
    pdf.set_font("Arial", "", 14)
    for feature in data["features"]:
        pdf.cell(10)  # Indent
        pdf.cell(0, 8, "• " + feature, 0, 1)
    
    # QR Code
    qr = qrcode.QRCode(version=1, box_size=4, border=4)
    qr.add_data(data["url"])
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    qr_img.save(qr_temp.name)
    pdf.image(qr_temp.name, x=160, y=250, w=30)
    os.unlink(qr_temp.name)  # Delete temp file
    
    # Save PDF
    pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    pdf.output(pdf_path)
    return pdf_path

# Streamlit UI
url = st.text_input("Enter Urban Ladder Product URL", 
                   value="https://www.urbanladder.com/products/florence-armchair")

if st.button("Generate PDF"):
    with st.spinner("Scraping data (this may take 10-15 seconds)..."):
        try:
            data = fetch_product_details(url)
            st.success("✅ Data fetched successfully!")
            
            with st.spinner("Generating PDF..."):
                pdf_file = generate_pdf(data)
                st.download_button(
                    "📥 Download PDF",
                    open(pdf_file, "rb"),
                    file_name=f"{data['title']}.pdf"
                )
        except Exception as e:
            st.error(f"Failed: {str(e)}")