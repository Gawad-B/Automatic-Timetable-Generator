import os
import time
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from io import BytesIO
import pandas as pd
import xlsxwriter
import csp
import traceback
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_BASE = os.path.join(BASE_DIR, 'static', 'uploads')

os.makedirs(UPLOAD_BASE, exist_ok=True)

ALLOWED_TARGETS = {'courses', 'instructors', 'rooms', 'timeslots', 'sections'}



app = Flask(__name__)

def create_excel_timetable(df, title="Timetable"):
    """
    Create an Excel file from a timetable DataFrame
    Returns BytesIO object containing the Excel file
    """
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Timetable')
    
    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D9D9D9',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
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
    
    tut_format = workbook.add_format({
        'bg_color': '#B4A7D6',  # Purple for tutorials
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
        session = getattr(row, 'Session', '')
        session_lower = str(session).lower()
        
        if 'lab' in session_lower:
            session_format = lab_format
        elif 'tut' in session_lower:
            session_format = tut_format
        else:
            session_format = lecture_format
        
        worksheet.write(row_idx, 0, getattr(row, 'CourseID', ''), cell_format)
        worksheet.write(row_idx, 1, getattr(row, 'CourseName', ''), cell_format)
        worksheet.write(row_idx, 2, getattr(row, 'SectionID', ''), cell_format)
        worksheet.write(row_idx, 3, session, session_format)
        worksheet.write(row_idx, 4, getattr(row, 'Day', ''), cell_format)
        worksheet.write(row_idx, 5, getattr(row, 'StartTime', ''), cell_format)
        worksheet.write(row_idx, 6, getattr(row, 'EndTime', ''), cell_format)
        worksheet.write(row_idx, 7, getattr(row, 'Room', ''), cell_format)
        worksheet.write(row_idx, 8, getattr(row, 'Instructor', ''), cell_format)
    
    # Set column widths
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
    return output

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

    # Sort by day of week and time
    day_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    df['DayOrder'] = df['Day'].map(lambda x: day_order.index(x) if x in day_order else 999)
    
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
            return 9999
    
    df['TimeOrder'] = df['StartTime'].apply(time_to_minutes)
    df_sorted = df.sort_values(['DayOrder', 'TimeOrder', 'CourseID']).drop(['DayOrder', 'TimeOrder'], axis=1).reset_index(drop=True)

    # Extract year from SectionID for year-based filtering
    def extract_year_from_section(section_id):
        """Extract year from section ID like '1/5', '2/3', '3/AID/1', '4/BIF/2'"""
        try:
            if pd.notna(section_id):
                parts = str(section_id).split('/')
                if parts:
                    return int(parts[0])
        except:
            pass
        return None
    
    df_sorted['Year'] = df_sorted['SectionID'].apply(extract_year_from_section)
    
    # Create zip file in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        
        # 1. Main timetable
        print("[generate] Creating main timetable...")
        main_excel = create_excel_timetable(df_sorted.drop('Year', axis=1), "Main Timetable")
        zip_file.writestr('Main_Timetable.xlsx', main_excel.getvalue())
        
        # 2. Year-specific timetables
        print("[generate] Creating year-specific timetables...")
        years = sorted([y for y in df_sorted['Year'].unique() if pd.notna(y)])
        for year in years:
            year_df = df_sorted[df_sorted['Year'] == year].drop('Year', axis=1).copy()
            year_excel = create_excel_timetable(year_df, f"Year {year} Timetable")
            zip_file.writestr(f'Years/Year_{year}.xlsx', year_excel.getvalue())
        
        print(f"[generate] Created {len(years)} year timetables")
        
        # 3. Individual instructor timetables
        print("[generate] Creating instructor timetables...")
        instructors = df_sorted['Instructor'].unique()
        for instructor in instructors:
            if pd.notna(instructor) and str(instructor).strip():
                instructor_df = df_sorted[df_sorted['Instructor'] == instructor].drop('Year', axis=1).copy()
                instructor_excel = create_excel_timetable(instructor_df, f"Timetable - {instructor}")
                # Sanitize filename
                safe_name = str(instructor).replace('/', '_').replace('\\', '_').replace(':', '_')
                zip_file.writestr(f'Instructors/{safe_name}.xlsx', instructor_excel.getvalue())
        
        print(f"[generate] Created {len(instructors)} instructor timetables")
        
        # 4. Individual room timetables
        print("[generate] Creating room timetables...")
        rooms = df_sorted['Room'].unique()
        for room in rooms:
            if pd.notna(room) and str(room).strip():
                room_df = df_sorted[df_sorted['Room'] == room].drop('Year', axis=1).copy()
                room_excel = create_excel_timetable(room_df, f"Timetable - Room {room}")
                # Sanitize filename
                safe_name = str(room).replace('/', '_').replace('\\', '_').replace(':', '_')
                zip_file.writestr(f'Rooms/{safe_name}.xlsx', room_excel.getvalue())
        
        print(f"[generate] Created {len(rooms)} room timetables")
    
    zip_buffer.seek(0)
    
    total_files = 1 + len(years) + len(instructors) + len(rooms)
    print(f"[generate] Total files in zip: {total_files}")

    return (zip_buffer.read(), 200, {
        'Content-Type': 'application/zip',
        'Content-Disposition': 'attachment; filename="timetables.zip"',
        'X-Generation-Time': f'{generation_time:.2f}',
        'X-Total-Assignments': str(len(df)),
        'X-Total-Files': str(total_files)
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