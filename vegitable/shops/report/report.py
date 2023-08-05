import time
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from io import BytesIO
from django.shortcuts import render
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet


def get_epoch():
    return str(time.time()).split(".")[0]


class Report:

    @staticmethod
    def generate_sales_bill_table_report(data_list):
        # Create a file-like buffer to receive PDF data
        buffer = BytesIO()

        # Create the PDF object, using the buffer as its "file"
        pdf = SimpleDocTemplate(buffer, pagesize=letter)

        # Data for the table
        data = [["Bill No", "Customer Name", "Item", "Bags", "Amount", "Balance", "Mode"]]
        data.extend(data_list)

        # Create the table
        table = Table(data)

        # Add style to the table
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
        table.setStyle(style)

        # Build the PDF document
        elements = [table]
        pdf.build(elements)

        # File buffer is now ready to be used to generate the PDF file
        buffer.seek(0)

        # Create the HttpResponse object with the appropriate PDF headers
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{get_epoch()}sales_bill_report.pdf"'

        # Write the PDF buffer to the HttpResponse
        response.write(buffer.getvalue())

        return response

    @staticmethod
    def generate_patti_pdf(context):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="patti_bill.pdf"'

        doc = SimpleDocTemplate(response, pagesize=letter)
        elements = []

        # Add PDF content here
        # Use the context dictionary to populate the data

        styles = getSampleStyleSheet()

        # Add Bill details
        elements.append(Paragraph('Bill No: {}'.format(context.get('bill_number', '')), styles['Normal']))
        elements.append(Paragraph('Date: {}'.format(context.get('bill_date', '')), styles['Normal']))
        elements.append(Paragraph('Lorry Number: {}'.format(context.get('lorry_number', '')), styles['Normal']))
        elements.append(Paragraph('Farmer Name: {}'.format(context.get('farmer_name', '')), styles['Normal']))
        elements.append(Paragraph('Advance Amount: {}'.format(context.get('advance_amount', '')), styles['Normal']))

        # Add Sales Bill entries table
        sales_entries = context.get('sales_entries', [])
        table_data = [['Item Name', 'Lot Number', 'Sold Qty', 'Balance Qty', 'Weight', 'Rate', 'Amount']]
        for entry in sales_entries:
            table_data.append([
                entry.get('item_name', ''),
                entry.get('lot_number', ''),
                entry.get('sold_qty', ''),
                entry.get('balance_qty', ''),
                entry.get('weight', ''),
                entry.get('rate', ''),
                entry.get('amount', ''),
            ])

        table = Table(table_data)
        table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), '#CCCCCC'),
                                   ('GRID', (0, 0), (-1, -1), 1, '#000000')]))
        elements.append(table)

        # Add Total Weight, Hamali, and Net Amount
        elements.append(Paragraph('Total Weight: {}'.format(context.get('total_weight', '')), styles['Normal']))
        elements.append(Paragraph('Hamali: {}'.format(context.get('hamali', '')), styles['Normal']))
        elements.append(Paragraph('Net Amount: {}'.format(context.get('net_amount', '')), styles['Normal']))

        doc.build(elements)
        return response

    @staticmethod
    def patti_report_view(request):
        context = {
            'bill_number': 2,
            'bill_date': '08/01/2023',
            'lorry_number': 'KA-12-12345',
            'farmer_name': 'Praveen',
            'advance_amount': 0,
            'sales_entries': [
                {
                    'item_name': 'Potato',
                    'lot_number': 'P1',
                    'sold_qty': 40,
                    'balance_qty': 0,
                    'weight': 100,
                    'rate': 1000,
                    'amount': 2000,
                },
                # Add more sales entries if needed
            ],
            'total_weight': 100,
            'hamali': 0,
            'net_amount': 2000,
        }

        return Report.generate_patti_pdf(context)
