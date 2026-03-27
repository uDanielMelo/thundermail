import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from PyPDF2 import PdfReader, PdfWriter
import base64


def generate_audit_page(contract):
    """Gera a página de auditoria em PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#111111'),
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        spaceAfter=2,
    )
    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#111111'),
        spaceAfter=8,
    )

    elements = []

    # Cabeçalho
    elements.append(Paragraph("Registro de Assinaturas", title_style))
    elements.append(Paragraph(f"Documento: {contract.title}", subtitle_style))
    elements.append(Paragraph(
        f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}",
        subtitle_style
    ))
    elements.append(Spacer(1, 0.5*cm))

    # Linha separadora
    elements.append(Table(
        [['']],
        colWidths=[17*cm],
        style=TableStyle([('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#e5e7eb'))])
    ))
    elements.append(Spacer(1, 0.5*cm))

    # Info do contrato
    elements.append(Paragraph("Informações do documento", label_style))
    contract_data = [
        ['Título:', contract.title],
        ['Status:', contract.get_status_display()],
        ['Criado em:', contract.created_at.strftime('%d/%m/%Y %H:%M')],
        ['Total de signatários:', str(contract.total_signers())],
        ['Assinados:', str(contract.signed_count())],
    ]
    t = Table(contract_data, colWidths=[4*cm, 13*cm])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#666666')),
        ('TEXTCOLOR', (1,0), (1,-1), colors.HexColor('#111111')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.5*cm))

    # Signatários
    elements.append(Table(
        [['']],
        colWidths=[17*cm],
        style=TableStyle([('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#e5e7eb'))])
    ))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph("Registro de assinaturas", label_style))
    elements.append(Spacer(1, 0.3*cm))

    for signer in contract.signers.all():
        # Box do signatário
        signer_data = [
            ['Nome:', signer.name],
            ['E-mail:', signer.email],
            ['CPF:', signer.cpf or 'Não informado'],
            ['Status:', signer.get_status_display()],
        ]

        if signer.status == 'assinado':
            signer_data += [
                ['Assinado em:', signer.signed_at.strftime('%d/%m/%Y %H:%M:%S')],
                ['IP:', signer.ip_address or 'Não registrado'],
                ['Dispositivo:', (signer.user_agent or '')[:80] + '...'],
            ]

        t = Table(signer_data, colWidths=[4*cm, 13*cm])
        t.setStyle(TableStyle([
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#666666')),
            ('TEXTCOLOR', (1,0), (1,-1), colors.HexColor('#111111')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f9fafb')),
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.HexColor('#f9fafb'), colors.white]),
        ]))
        elements.append(t)

        # Imagem da assinatura
        if signer.status == 'assinado' and signer.signature_data:
            elements.append(Spacer(1, 0.2*cm))
            elements.append(Paragraph("Assinatura:", label_style))

            if signer.signature_data.startswith('data:image'):
                try:
                    img_data = signer.signature_data.split(',')[1]
                    img_bytes = base64.b64decode(img_data)
                    img_buffer = io.BytesIO(img_bytes)
                    img = Image(img_buffer, width=6*cm, height=2*cm)
                    elements.append(img)
                except Exception:
                    elements.append(Paragraph(f"[Assinatura digital registrada]", value_style))
            elif signer.signature_data.startswith('text:'):
                text = signer.signature_data.replace('text:', '')
                sig_style = ParagraphStyle(
                    'Sig',
                    parent=styles['Normal'],
                    fontSize=18,
                    fontName='Helvetica-Oblique',
                    textColor=colors.HexColor('#111111'),
                )
                elements.append(Paragraph(text, sig_style))

        elements.append(Spacer(1, 0.4*cm))

    # Rodapé legal
    elements.append(Table(
        [['']],
        colWidths=[17*cm],
        style=TableStyle([('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#e5e7eb'))])
    ))
    elements.append(Spacer(1, 0.3*cm))
    legal_style = ParagraphStyle(
        'Legal',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#9ca3af'),
        alignment=TA_CENTER,
    )
    elements.append(Paragraph(
        "Este documento foi assinado eletronicamente através do ThunderMail. "
        "As assinaturas eletrônicas têm validade jurídica conforme a MP 2.200-2/2001 e Lei 14.063/2020. "
        "Os registros de IP, data, hora e identificação dos signatários garantem a autenticidade deste documento.",
        legal_style
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def merge_pdf_with_audit(contract):
    """Mescla o PDF original com a página de auditoria."""
    writer = PdfWriter()

    # Adiciona páginas do PDF original
    original_path = contract.document.path
    reader = PdfReader(original_path)
    for page in reader.pages:
        writer.add_page(page)

    # Adiciona página de auditoria
    audit_buffer = generate_audit_page(contract)
    audit_reader = PdfReader(audit_buffer)
    for page in audit_reader.pages:
        writer.add_page(page)

    # Retorna o PDF final em memória
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output