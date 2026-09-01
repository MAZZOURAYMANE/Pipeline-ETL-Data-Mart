FROM odoo:18.0
USER root
RUN pip install pdfplumber python-docx --break-system-packages
USER odoo