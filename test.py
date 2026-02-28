import pandas as pd
import pdfkit
import os

# Define file paths
xlsx_file = "your_file.xlsx" # Replace with your file name
html_file = "temp.html"
pdf_file = "output.pdf"

# Read excel file into pandas DataFrame
df = pd.read_excel(xlsx_file, sheet_name="Sheet1") # Specify your sheet name

# Convert DataFrame to HTML
df.to_html(html_file, index=False, header=True)

# Convert HTML to PDF
# You might need to specify the path to wkhtmltopdf executable if it's not in your PATH
# config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf') # Example path
pdfkit.from_file(html_file, pdf_file) #, configuration=config)

# Clean up the temporary HTML file
os.remove(html_file)

print(f"PDF saved as: {pdf_file}")