from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime

class PdfService:
    def _add_header(self, elements, title, staff_name):
        """Adds a standard header to the PDF elements list."""
        styles = getSampleStyleSheet()
        
        elements.append(Paragraph(title, styles['h1']))
        
        # Updated sub-header format
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sub_header_text = f"Exported by: {staff_name} | Date: {timestamp}"
        elements.append(Paragraph(sub_header_text, styles['Normal']))
        
        elements.append(Spacer(1, 0.25 * inch))
        return elements

    def generate_earnings_report(self, staff_name, line_chart_path, bar_chart_path):
        """Generates a PDF for the Earning Summary."""
        file_path = f"Earning_Summary_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(file_path, pagesize=(11*inch, 8.5*inch)) # Landscape
        
        elements = []
        styles = getSampleStyleSheet()
        elements = self._add_header(elements, "Earning Summary Report", staff_name)
        
        overview_title = Paragraph("Earning Summary Overview", getSampleStyleSheet()['h2'])
        elements.append(overview_title)
        elements.append(Spacer(1, 0.2 * inch))

        try:
            img_line = Image(line_chart_path, width=4.8*inch, height=3.2*inch)
            img_bar = Image(bar_chart_path, width=4.8*inch, height=3.2*inch)
            
            image_table = Table([[img_line, img_bar]], colWidths=[5*inch, 5*inch])
            image_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            elements.append(image_table)
        except Exception as e:
            print(f"Error adding images to PDF: {e}")
            elements.append(Paragraph(f"Error: Could not load graph images. {e}", getSampleStyleSheet()['Normal']))

        doc.build(elements)
        return file_path

    def generate_rental_report(self, staff_name, rental_data):
        """Generates a PDF for the Car Rental table."""
        file_path = f"Car_Rental_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(file_path, pagesize=(11*inch, 8.5*inch)) # Landscape

        elements = []
        elements = self._add_header(elements, "Car Rental Report", staff_name)

        header = ["ID", "Renter Name", "Car Rented", "Date Rented", "Total Price", "Status"]
        data = [header]
        for item in rental_data:
            data.append([
                item['rental_id'],
                item['customer_name'],
                item['car_name'],
                item['date_rented'].strftime('%Y-%m-%d'),
                f"${item['total_price']:.2f}",
                item['status']
            ])

        table = Table(data, colWidths=[0.5*inch, 2.5*inch, 2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ])
        table.setStyle(style)
        
        elements.append(table)
        doc.build(elements)
        return file_path

    def generate_receipt(self, customer_name, contact_number, car_name, duration, total_price, rental_id, logo_path=None):
        """Generates a simple PDF receipt for a customer rental."""
        file_path = f"Receipt_{rental_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(file_path, pagesize=(8.5*inch, 11*inch))

        elements = []
        styles = getSampleStyleSheet()

        if logo_path:
            try:
                elements.append(Image(logo_path, width=1.4*inch, height=1.4*inch))
                elements.append(Spacer(1, 0.15 * inch))
            except Exception:
                pass

        elements.append(Paragraph("Rental Receipt", styles['h1']))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(f"Date: {timestamp}", styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))

        data = [
            ["Receipt ID", str(rental_id)],
            ["Renter Name", customer_name],
            ["Contact Number", contact_number],
            ["Car", car_name],
            ["Duration", duration],
            ["Total Price", f"PHP {total_price:,.2f}"],
        ]
        table = Table(data, colWidths=[2.0*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black)
        ]))
        elements.append(table)
        doc.build(elements)
        return file_path
