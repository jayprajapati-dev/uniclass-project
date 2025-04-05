from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from flask_login import login_required, current_user
from models import db, User, Subject, StudyMaterial, Notification, Timetable
from datetime import datetime, timedelta
import pandas as pd
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def list_reports():
    if not current_user.is_admin:
        flash('Only administrators can access reports', 'error')
        return redirect(url_for('main.index'))
    return render_template('reports/list.html')

@reports_bp.route('/user-activity')
@login_required
def user_activity_report():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get date range from request
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Convert to datetime objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Get user activity data
    users = User.query.all()
    activity_data = []
    
    for user in users:
        # Count study materials uploaded
        materials_count = StudyMaterial.query.filter(
            StudyMaterial.uploaded_by == user.id,
            StudyMaterial.created_at.between(start_date, end_date)
        ).count()
        
        # Count notifications sent (for admins)
        notifications_count = Notification.query.filter(
            Notification.created_by == user.id,
            Notification.created_at.between(start_date, end_date)
        ).count()
        
        # Count timetable entries created
        timetable_count = Timetable.query.filter(
            Timetable.created_by == user.id,
            Timetable.created_at.between(start_date, end_date)
        ).count()
        
        activity_data.append({
            'user': user.username,
            'role': 'Admin' if user.is_admin else 'User',
            'materials_uploaded': materials_count,
            'notifications_sent': notifications_count,
            'timetable_entries': timetable_count,
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'
        })
    
    # Create DataFrame and generate Excel file
    df = pd.DataFrame(activity_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='User Activity', index=False)
        worksheet = writer.sheets['User Activity']
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:E', 20)
        worksheet.set_column('F:F', 25)
    
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'user_activity_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@reports_bp.route('/study-materials')
@login_required
def study_materials_report():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Get all study materials with related data
        materials = StudyMaterial.query.all()
        materials_data = []
        
        # Prepare data for the table
        table_data = [['Material Title', 'Subject Name', 'Uploaded By', 'Upload Date & Time', 'File Type']]
        
        for material in materials:
            subject = Subject.query.get(material.subject_id)
            uploader = User.query.get(material.uploaded_by)
            
            table_data.append([
                material.title or 'Untitled',
                subject.name if subject else 'Not Assigned',
                uploader.username if uploader else 'Unknown User',
                material.created_at.strftime('%Y-%m-%d %H:%M:%S') if material.created_at else 'N/A',
                material.file_path.split('.')[-1].upper() if material.file_path else 'N/A'
            ])
        
        # Create PDF
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        timestamp_style = ParagraphStyle(
            'CustomTimestamp',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.gray,
            alignment=2  # Right alignment
        )
        
        note_style = ParagraphStyle(
            'CustomNote',
            parent=styles['Italic'],
            fontSize=8,
            textColor=colors.gray,
            alignment=0  # Left alignment
        )
        
        # Create the PDF content
        elements = []
        
        # Add title
        elements.append(Paragraph('Study Materials Report', title_style))
        
        # Add timestamp
        elements.append(Paragraph(f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', timestamp_style))
        
        # Add spacing
        elements.append(Spacer(1, 20))
        
        # Create table
        table = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1*inch])
        
        # Add table style
        style = TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data style
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        table.setStyle(style)
        elements.append(table)
        
        # Add note about encoding
        elements.append(Spacer(1, 20))
        elements.append(Paragraph('Note: This report is generated with proper text encoding for English display.', note_style))
        
        # Build PDF
        doc.build(elements)
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Study_Materials_Report_{datetime.now().strftime("%Y%m%d")}.pdf'
        )
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'danger')
        return redirect(url_for('reports.list_reports'))

@reports_bp.route('/notifications')
@login_required
def notifications_report():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get date range from request
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Convert to datetime objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Get notifications data
    notifications = Notification.query.filter(
        Notification.created_at.between(start_date, end_date)
    ).all()
    
    notifications_data = []
    for notification in notifications:
        sender = User.query.get(notification.created_by)
        notifications_data.append({
            'title': notification.title,
            'type': notification.type,
            'target_audience': notification.target_audience,
            'sent_by': sender.username if sender else 'Unknown',
            'sent_date': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'read_count': Notification.query.filter(
                Notification.id == notification.id,
                Notification.read == True
            ).count()
        })
    
    # Create DataFrame and generate Excel file
    df = pd.DataFrame(notifications_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Notifications', index=False)
        worksheet = writer.sheets['Notifications']
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 25)
        worksheet.set_column('F:F', 15)
    
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'notifications_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
    ) 