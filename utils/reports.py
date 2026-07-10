"""
Report Generation Utilities — Excel and PDF report builders.
"""
import io
import os
import pandas as pd
from datetime import datetime


def generate_excel_report(report_title: str, data: pd.DataFrame,
                          metadata: dict = None, sheet_name: str = "Report") -> io.BytesIO:
    """
    Generate a formatted Excel report.

    Args:
        report_title: Title for the report
        data: DataFrame with report data
        metadata: Optional dict of metadata key-value pairs
        sheet_name: Name of the main data sheet

    Returns:
        BytesIO buffer containing the Excel file
    """
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Main data sheet
        data.to_excel(writer, index=False, sheet_name=sheet_name)

        # Metadata sheet
        if metadata:
            meta_df = pd.DataFrame([
                {"Field": k, "Value": str(v)} for k, v in metadata.items()
            ])
            meta_df.to_excel(writer, index=False, sheet_name="Metadata")

        # Summary sheet (for numeric data)
        numeric_cols = data.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            summary = data[numeric_cols].describe().round(2)
            summary.to_excel(writer, sheet_name="Summary")

    buffer.seek(0)
    return buffer


def generate_pdf_report(report_title: str, data: pd.DataFrame,
                        metadata: dict = None, max_rows: int = 100) -> io.BytesIO:
    """
    Generate a formatted PDF report with banking theme.

    Args:
        report_title: Title for the report
        data: DataFrame with report data
        metadata: Optional dict of metadata
        max_rows: Maximum rows to include in the PDF table

    Returns:
        BytesIO buffer containing the PDF file
    """
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    elements = []

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        fontSize=18, textColor=colors.HexColor('#1B2A4A'),
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#6C757D'),
        spaceAfter=20
    )

    # Title
    elements.append(Paragraph(f"🏦 {report_title}", title_style))
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph(f"Generated: {generated_at}", subtitle_style))

    # Metadata
    if metadata:
        meta_data = [[str(k), str(v)] for k, v in metadata.items()]
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1B2A4A')),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 0.3*inch))

    # Data table
    display_cols = data.columns[:8].tolist()  # Limit columns for readability
    table_data = [display_cols]
    for _, row in data.head(max_rows).iterrows():
        table_data.append([str(row[col])[:25] for col in display_cols])

    if table_data:
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B2A4A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#D4AF37')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DEE2E6')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elements.append(t)

    # Footer
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(
        f"AI Banking Customer Insights Platform · {len(data)} records · Page 1",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def get_report_data(report_type: str, conn, filters: dict = None) -> pd.DataFrame:
    """
    Fetch data for a specific report type.

    Args:
        report_type: Type of report to generate
        conn: Database connection
        filters: Optional filters

    Returns:
        DataFrame with report data
    """
    queries = {
        "Customer Report": "SELECT * FROM customers",
        "Loan Report": "SELECT * FROM loans",
        "Transaction Report": "SELECT * FROM transactions",
        "Customer Segmentation Report": "SELECT * FROM customers",
        "Churn Report": "SELECT * FROM customers WHERE is_active = 0",
    }

    query = queries.get(report_type, "SELECT 1")
    return pd.read_sql(query, conn)
