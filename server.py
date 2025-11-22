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

# Store upload status
upload_status = {
    'courses': False,
    'instructors': False,
    'rooms': False,
    'timeslots': False,
    'sections': False
}

# Store generated zip temporarily
last_generated_zip = None

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def create_excel_timetable(df, title="Timetable"):
    """
    Create a grid-style Excel timetable matching the PDF structure exactly
    """
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Timetable')
    
    # Define formats
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#4472C4',
        'font_color': 'white',
        'border': 1
    })
    
    label_format = workbook.add_format({
        'bold': True,
        'font_size': 10,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#D0D0D0',
        'border': 1
    })
    
    group_name_format = workbook.add_format({
        'bold': True,
        'font_size': 10,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })
    
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D9D9D9',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 10
    })
    
    time_format = workbook.add_format({
        'bold': True,
        'bg_color': '#E8E8E8',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 9
    })
    
    lecture_format = workbook.add_format({
        'bg_color': '#FFD966',
        'border': 1,
        'align': 'left',
        'valign': 'top',
        'text_wrap': True,
        'font_size': 8
    })
    
    lab_format = workbook.add_format({
        'bg_color': '#9FC5E8',
        'border': 1,
        'align': 'left',
        'valign': 'top',
        'text_wrap': True,
        'font_size': 8
    })
    
    tut_format = workbook.add_format({
        'bg_color': '#B4A7D6',
        'border': 1,
        'align': 'left',
        'valign': 'top',
        'text_wrap': True,
        'font_size': 8
    })
    
    empty_format = workbook.add_format({
        'border': 1,
        'bg_color': '#FFFFFF'
    })
    
    # Days order
    days_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
    
    # Create TimeSlot column
    df['TimeSlot'] = df['StartTime'] + ' - ' + df['EndTime']
    
    # Extract year and department
    def extract_info(section_id):
        try:
            parts = str(section_id).split('/')
            year = int(parts[0])
            dept = parts[1] if len(parts) > 1 else str(parts[1]) if len(parts) > 1 else ''
            section_num = parts[2] if len(parts) > 2 else parts[1] if len(parts) > 1 else ''
            return year, dept, section_num
        except:
            return 0, '', ''
    
    df['Year'] = df['SectionID'].apply(lambda x: extract_info(x)[0])
    df['Dept'] = df['SectionID'].apply(lambda x: extract_info(x)[1])
    df['SectionNum'] = df['SectionID'].apply(lambda x: extract_info(x)[2])
    
    # Time sorting
    def time_to_minutes(time_str):
        try:
            # Remove any extra spaces
            time_str = time_str.strip()
            # Handle formats like "9:00", "9:0", "09:00", "1:15", etc.
            if ':' in time_str:
                parts = time_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1]) if len(parts) > 1 and parts[1] else 0
                return hours * 60 + minutes
            # If no colon, assume it's just hours
            return int(time_str) * 60
        except Exception as e:
            print(f"Error parsing time '{time_str}': {e}")
            return 0
    
    def parse_timeslot(timeslot):
        try:
            # Split by ' - ' and parse both start and end times
            if ' - ' in timeslot:
                parts = timeslot.split(' - ')
                start = parts[0].strip()
                end = parts[1].strip() if len(parts) > 1 else ""
                start_mins = time_to_minutes(start)
                end_mins = time_to_minutes(end)
                # Sort by start time first, then by end time
                return (start_mins, end_mins)
            return (0, 0)
        except Exception as e:
            print(f"Error parsing timeslot '{timeslot}': {e}")
            return (0, 0)
    
    # Function to sort section IDs numerically
    def sort_sections_numerically(sections):
        def section_sort_key(section_id):
            try:
                parts = str(section_id).split('/')
                year = int(parts[0])
                # Get the numeric part (last part for year 1-2, or third part for year 3-4)
                if len(parts) == 2:
                    num = int(parts[1])
                elif len(parts) == 3:
                    num = int(parts[2])
                else:
                    num = 0
                return (year, num)
            except:
                return (0, 0)
        return sorted(sections, key=section_sort_key)
    
    # Organize groups by year - matching PDF structure
    groups_to_create = []
    
    # Year 1: CSIT (Group 1), (Group 2), (Group 3), (Group 4)
    year1_sections = sort_sections_numerically([s for s in df[df['Year'] == 1]['SectionID'].unique()])
    for i in range(0, len(year1_sections), 4):
        group_sections = year1_sections[i:i+4]
        if group_sections:
            group_num = (i // 4) + 1
            groups_to_create.append({
                'year_title': '1st Year' if i == 0 else None,
                'group_num': group_num,
                'group_name': f'CSIT (Group {group_num})',
                'sections': group_sections
            })
    
    # Year 2: CSIT (Group 1), (Group 2), (Group 3), (Group 4)
    year2_sections = sort_sections_numerically([s for s in df[df['Year'] == 2]['SectionID'].unique()])
    for i in range(0, len(year2_sections), 3):
        group_sections = year2_sections[i:i+3]
        if group_sections:
            group_num = (i // 3) + 1
            groups_to_create.append({
                'year_title': '2nd Year' if i == 0 else None,
                'group_num': group_num,
                'group_name': f'CSIT (Group {group_num})',
                'sections': group_sections
            })
    
    # Year 3 & 4: By department - CSIT (AID), CSIT (BIF), CSIT (CNC), CSIT (CSC)
    for year, year_label in [(3, '3rd Year'), (4, '4th Year')]:
        first_dept = True
        for dept in ['AID', 'BIF', 'CNC', 'CSC']:
            dept_sections = sort_sections_numerically([s for s in df[(df['Year'] == year) & (df['Dept'] == dept)]['SectionID'].unique()])
            if dept_sections:
                groups_to_create.append({
                    'year_title': year_label if first_dept else None,
                    'group_num': None,
                    'group_name': f'CSIT ({dept})',
                    'sections': dept_sections
                })
                first_dept = False
    
    # Create the timetable
    current_row = 0
    
    for group_info in groups_to_create:
        # Write Year title if this is the first group of a year
        if group_info['year_title']:
            worksheet.merge_range(current_row, 0, current_row, len(days_order), 
                                group_info['year_title'], title_format)
            worksheet.set_row(current_row, 25)
            current_row += 1
            
            # Write "Faculty", "Group", "Section" row headers
            worksheet.write(current_row, 0, 'Faculty', label_format)
            worksheet.write(current_row, 1, 'Group', label_format)
            worksheet.write(current_row, 2, 'Section', label_format)
            for col in range(3, len(days_order) + 1):
                worksheet.write(current_row, col, '', label_format)
            current_row += 1
        
        # Filter data for this group
        group_df = df[df['SectionID'].isin(group_info['sections'])]
        
        if group_df.empty:
            continue
        
        # Write group identifier row
        worksheet.write(current_row, 0, group_info['group_name'], group_name_format)
        worksheet.write(current_row, 1, str(group_info['group_num']) if group_info['group_num'] else '', group_name_format)
        sections_str = ', '.join([str(s).split('/')[-1] for s in group_info['sections']])
        worksheet.write(current_row, 2, sections_str, group_name_format)
        for col in range(3, len(days_order) + 1):
            worksheet.write(current_row, col, '', group_name_format)
        current_row += 1
        
        # Get unique timeslots and sort
        timeslots = sorted(group_df['TimeSlot'].unique(), key=parse_timeslot)
        
        # Write day headers
        worksheet.write(current_row, 0, '', header_format)
        for col_idx, day in enumerate(days_order, start=1):
            worksheet.write(current_row, col_idx, day, header_format)
        worksheet.set_row(current_row, 20)
        current_row += 1
        
        # Build grid data - organize by timeslot, day, and course/section
        grid_data = {}
        for _, row in group_df.iterrows():
            timeslot = row['TimeSlot']
            day = row['Day']
            course_id = row['CourseID']
            section_id = row['SectionID']
            session_type = str(row['Session']).lower()
            
            # For lectures, use course_id only (same for all sections)
            # For LAB/TUT, include section_id to make them separate
            if 'lec' in session_type:
                key = (timeslot, day, course_id, 'LEC')
            else:
                key = (timeslot, day, course_id, section_id)
            
            # Format like PDF: Course + Name, Instructor, Type, Room
            cell_text = f"{row['CourseID']} {row['CourseName']}\n"
            cell_text += f"{row['Instructor']}\n"
            
            # Add SectionID for LAB and TUT sessions only
            if 'lab' in session_type or 'tut' in session_type:
                cell_text += f"{row['Session']} ({row['SectionID']})\n"
            else:
                cell_text += f"{row['Session']}\n"
            
            cell_text += f"{row['Room']}"
            
            # For lectures, only store once (don't duplicate for each section)
            if key not in grid_data or 'lec' not in session_type:
                grid_data[key] = {
                    'text': cell_text,
                    'type': session_type,
                    'timeslot': timeslot,
                    'day': day
                }
        
        # Group entries by timeslot and day, then create separate rows for each unique entry
        timeslot_day_entries = {}
        for key, data in grid_data.items():
            timeslot = data['timeslot']
            day = data['day']
            td_key = (timeslot, day)
            if td_key not in timeslot_day_entries:
                timeslot_day_entries[td_key] = []
            timeslot_day_entries[td_key].append(data)
        
        # Fill grid - create separate rows for each unique course at same timeslot
        for timeslot in timeslots:
            # Find max entries across all days for this timeslot
            max_entries = 0
            for day in days_order:
                td_key = (timeslot, day)
                if td_key in timeslot_day_entries:
                    max_entries = max(max_entries, len(timeslot_day_entries[td_key]))
            
            # Create rows for this timeslot (one row per entry)
            for entry_idx in range(max(1, max_entries)):
                # Write timeslot only in first row
                if entry_idx == 0:
                    worksheet.write(current_row, 0, timeslot, time_format)
                else:
                    worksheet.write(current_row, 0, '', time_format)
                
                for col_idx, day in enumerate(days_order, start=1):
                    td_key = (timeslot, day)
                    
                    if td_key in timeslot_day_entries and entry_idx < len(timeslot_day_entries[td_key]):
                        entry = timeslot_day_entries[td_key][entry_idx]
                        
                        session_type = entry['type']
                        if 'lab' in session_type:
                            cell_format = lab_format
                        elif 'tut' in session_type:
                            cell_format = tut_format
                        else:
                            cell_format = lecture_format
                        
                        worksheet.write(current_row, col_idx, entry['text'], cell_format)
                    else:
                        worksheet.write(current_row, col_idx, '', empty_format)
                
                worksheet.set_row(current_row, 50)
                current_row += 1
        
        # Blank row between groups
        current_row += 1
    
    # Set column widths
    worksheet.set_column(0, 0, 15)  # Time/Faculty column
    worksheet.set_column(1, 1, 12)  # Group column
    worksheet.set_column(2, 2, 12)  # Section column
    worksheet.set_column(3, len(days_order), 28)  # Day columns (adjust start from column 3)
    
    # Adjust to proper column layout - time in col 0, days in cols 1-5
    worksheet.set_column(0, 0, 15)  # Time column
    worksheet.set_column(1, len(days_order), 28)  # Day columns
    
    workbook.close()
    output.seek(0)
    return output

@app.route('/generate', methods=['POST'])
def generate():
    global last_generated_zip
    
    # Track generation time
    start_time = time.time()
    
    # Reset the zip file
    last_generated_zip = None
    
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
    
    # Store the zip file globally for download
    last_generated_zip = zip_buffer.read()

    # Return JSON response for API
    return jsonify(
        success=True,
        total_assignments=len(df),
        total_files=total_files,
        generation_time=generation_time,
        message='Timetables generated successfully'
    )

@app.route('/download', methods=['GET'])
def download():
    """Download the last generated timetable zip"""
    global last_generated_zip
    
    if last_generated_zip is None:
        return jsonify(success=False, message='No timetable generated yet'), 404
    
    from flask import Response
    return Response(
        last_generated_zip,
        mimetype='application/zip',
        headers={'Content-Disposition': 'attachment; filename="timetables.zip"'}
    )


@app.route('/upload', methods=['POST'])
def upload_all():
    """Handle bulk file upload from new UI"""
    try:
        uploaded_count = 0
        for target in ALLOWED_TARGETS:
            if target in request.files:
                file = request.files[target]
                if file.filename != '':
                    filename = f"{target}.csv"
                    target_dir = os.path.join(UPLOAD_BASE, target)
                    os.makedirs(target_dir, exist_ok=True)
                    filepath = os.path.join(target_dir, filename)
                    file.save(filepath)
                    upload_status[target] = True
                    uploaded_count += 1
        
        all_uploaded = all(upload_status.values())
        return jsonify(
            success=True,
            uploaded=uploaded_count,
            all_ready=all_uploaded,
            message=f'Uploaded {uploaded_count} files successfully'
        )
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

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