import os
import time
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from io import BytesIO
import pandas as pd
import xlsxwriter
import csp
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_BASE = os.path.join(BASE_DIR, 'static', 'uploads')

os.makedirs(UPLOAD_BASE, exist_ok=True)

ALLOWED_TARGETS = {'courses', 'instructors', 'rooms', 'timeslots', 'sections'}



app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    # Track generation time
    start_time = time.time()
    
    # Generate timetable using uploaded CSVs in static/uploads
    try:
        upload_dir = os.path.join(UPLOAD_BASE)
        df = csp.generate_timetable_from_uploads(upload_dir)
        generation_time = time.time() - start_time
        
        # Log timing to console
        print(f"\n{'='*60}")
        print(f"Timetable Generation Complete!")
        print(f"Time taken: {generation_time:.2f} seconds")
        print(f"Total assignments: {len(df)}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        # Log full traceback to server console for debugging
        traceback.print_exc()
        return jsonify(success=False, message=str(e)), 500

    # Sort by day of week (Sunday, Monday, Tuesday, etc.) and then by time
    day_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    df['DayOrder'] = df['Day'].map(lambda x: day_order.index(x) if x in day_order else 999)
    
    # Convert time to sortable format (handle AM/PM)
    def time_to_minutes(time_str):
        """Convert time string like '9:00 AM' to minutes since midnight for sorting"""
        try:
            time_part, period = time_str.strip().split()
            hours, minutes = map(int, time_part.split(':'))
            if period == 'PM' and hours != 12:
                hours += 12
            elif period == 'AM' and hours == 12:
                hours = 0
            return hours * 60 + minutes
        except:
            return 9999  # Put invalid times at the end
    
    df['TimeOrder'] = df['StartTime'].apply(time_to_minutes)
    df = df.sort_values(['DayOrder', 'TimeOrder', 'CourseID']).drop(['DayOrder', 'TimeOrder'], axis=1).reset_index(drop=True)

    # Write to Excel in-memory using xlsxwriter for custom formatting
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Timetable')
    
    # Define formats similar to the sample PDF
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D9D9D9',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    # Different colors for different session types
    lecture_format = workbook.add_format({
        'bg_color': '#FFD966',  # Yellow for lectures
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    })
    
    lab_format = workbook.add_format({
        'bg_color': '#9FC5E8',  # Blue for labs
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    })
    
    cell_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    })
    
    # Write headers
    headers = ['CourseID', 'CourseName', 'SectionID', 'Session', 'Day', 'StartTime', 'EndTime', 'Room', 'Instructor']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Write data rows
    for row_idx, row in enumerate(df.itertuples(index=False), start=1):
        # Determine format based on session type
        session = getattr(row, 'Session', '')
        is_lab = 'lab' in str(session).lower()
        session_format = lab_format if is_lab else lecture_format
        
        worksheet.write(row_idx, 0, getattr(row, 'CourseID', ''), cell_format)
        worksheet.write(row_idx, 1, getattr(row, 'CourseName', ''), cell_format)
        worksheet.write(row_idx, 2, getattr(row, 'SectionID', ''), cell_format)
        worksheet.write(row_idx, 3, session, session_format)
        worksheet.write(row_idx, 4, getattr(row, 'Day', ''), cell_format)
        worksheet.write(row_idx, 5, getattr(row, 'StartTime', ''), cell_format)
        worksheet.write(row_idx, 6, getattr(row, 'EndTime', ''), cell_format)
        worksheet.write(row_idx, 7, getattr(row, 'Room', ''), cell_format)
        worksheet.write(row_idx, 8, getattr(row, 'Instructor', ''), cell_format)
    
    # Set column widths for better readability
    worksheet.set_column(0, 0, 12)  # CourseID
    worksheet.set_column(1, 1, 30)  # CourseName
    worksheet.set_column(2, 2, 12)  # SectionID
    worksheet.set_column(3, 3, 12)  # Session
    worksheet.set_column(4, 4, 12)  # Day
    worksheet.set_column(5, 5, 12)  # StartTime
    worksheet.set_column(6, 6, 12)  # EndTime
    worksheet.set_column(7, 7, 10)  # Room
    worksheet.set_column(8, 8, 25)  # Instructor
    
    workbook.close()
    output.seek(0)

    return (output.read(), 200, {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': 'attachment; filename="timetable.xlsx"',
        'X-Generation-Time': f'{generation_time:.2f}',
        'X-Total-Assignments': str(len(df))
    })


@app.route('/upload/<target>', methods=['POST'])
def upload(target):
    if target not in ALLOWED_TARGETS:
        return jsonify(success=False, message='Invalid upload target'), 400

    if 'file' not in request.files:
        return jsonify(success=False, message='No file part'), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify(success=False, message='No selected file'), 400

    filename = secure_filename(file.filename)
    # Allow client to request a different saved filename:
    # - send 'save_as' in the form data to force a filename (example: 'courses.csv')
    # - or send 'use_target_name' (true/1) to use '<target><orig_ext>' as the filename
    save_as = request.form.get('save_as')
    use_target_name = request.form.get('use_target_name')

    if save_as:
        # sanitize client-supplied name
        filename = secure_filename(save_as)
    elif use_target_name and use_target_name.lower() in ('1', 'true', 'yes'):
        orig_ext = os.path.splitext(filename)[1]
        filename = secure_filename(f"{target}{orig_ext}")
    # Ensure target directory exists
    target_dir = os.path.join(UPLOAD_BASE, target)
    os.makedirs(target_dir, exist_ok=True)

    save_path = os.path.join(target_dir, filename)
    try:
        # Overwrite existing file if present (user requested behavior)
        file.save(save_path)
        print(f"[upload] saved file for target={target} filename={filename} path={save_path}")
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

    return jsonify(success=True, message='File uploaded', filename=filename), 200

if __name__ == '__main__':
    app.run(debug=True)