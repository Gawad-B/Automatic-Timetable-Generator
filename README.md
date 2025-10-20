# ATTG - Automatic Timetable Generator

An intelligent automatic timetable generator that uses constraint satisfaction algorithms to create optimized class schedules for educational institutions.

## 🌟 Features

- **Smart Constraint Satisfaction**: Uses advanced CSP algorithms with forward checking and backtracking
- **Multi-Day Scheduling**: Distributes classes across Sunday-Thursday with intelligent day balancing
- **Strict Role-Based Assignment**: Enforces Professors for lectures, Assistant Professors for labs and sections
- **Multi-Session Support**: Handles Lecture, Lab, and Section sessions for courses
- **Intelligent Room Matching**: Automatically assigns appropriate room types (Lecture halls, Labs, Section rooms)
- **Department-Based Sections**: Smart section assignment by year and department (Years 3-4)
- **Instructor Management**: Respects instructor preferences, qualifications, and role-based restrictions
- **Web Interface**: User-friendly web interface with real-time feedback and timing information
- **Formatted Excel Export**: Generates color-coded, chronologically sorted Excel files
- **Performance Tracking**: Displays generation time and statistics on the website

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Flask
- pandas
- xlsxwriter
- openpyxl

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Gawad-B/attg.git
cd attg
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or manually install:
```bash
pip install Flask pandas xlsxwriter openpyxl
```

3. Run the application:
```bash
python server.py
```

4. Open your browser and navigate to `http://localhost:5000`

## 📁 Project Structure

```
attg/
├── server.py              # Flask web server
├── csp.py                 # Constraint satisfaction algorithm
├── templates/
│   └── index.html         # Web interface
├── static/
│   ├── uploads/           # Uploaded CSV files
│   └── assets/           # CSS/JS assets
└── README.md
```

## 📊 Data Format

The system requires 5 CSV files with the following formats:

### 1. courses.csv
```csv
CourseID,CourseName,Credits,Type
CSC111,Fundamentals of Programming,3,Lecture and Lab
MTH111,Mathematics (1),3,Lecture and Section
PHY113,Physics (1),4,Lecture and Lab and Section
LRA101,Japanese Culture,2,Lecture
```

**Required columns:**
- `CourseID`: Unique identifier for the course
- `CourseName`: Full name of the course
- `Credits`: Number of credit hours
- `Type`: Session type - can be:
  - `"Lecture"` - Lecture only
  - `"Lecture and Lab"` - Creates both Lecture and Lab sessions
  - `"Lecture and Section"` - Creates both Lecture and Section sessions
  - `"Lecture and Lab and Section"` - Creates all three session types

### 2. instructors.csv
```csv
InstructorID,Name,Role,PreferredSlots,QualifiedCourses
PROF01,Dr. John Smith,Professor,Not on Tuesday,"CSC111,MTH111"
PROF02,Dr. Jane Doe,Assistant Professor,Not on Sunday,"LRA101,CSC111"
```

**Required columns:**
- `InstructorID`: Unique identifier for the instructor
- `Name`: Full name of the instructor
- `Role`: Position (e.g., "Professor", "Assistant Professor") - **Important for role-based assignment**
- `PreferredSlots`: Day preferences (e.g., "Not on Tuesday")
- `QualifiedCourses`: Comma-separated list of courses they can teach

**Note on Role-Based Assignment:**
- Instructors with "Professor" role (without "Assistant") are assigned to **lecture sessions only**
- Instructors with "Assistant Professor" role are assigned to **lab and section sessions only**
- **This is a HARD constraint** - role mismatches are never allowed (no fallback)
- Proper role assignment ensures optimal instructor utilization and academic standards

### 3. rooms.csv
```csv
RoomID,Type,Capacity
R1,Lecture,80
L1,Lab,35
S1,Section,35
R2,Lecture,80
```

**Required columns:**
- `RoomID`: Unique identifier for the room
- `Type`: Room type - can be:
  - `"Lecture"` - For lecture sessions (typically larger capacity)
  - `"Lab"` - For lab sessions (with equipment)
  - `"Section"` - For section/discussion sessions (smaller groups)
- `Capacity`: Maximum number of students

**Room Naming Conventions:**
- Lecture rooms: Typically start with "R" (e.g., R1, R2, R101)
- Lab rooms: Typically start with "L" (e.g., L1, L2, L101)
- Section rooms: Typically start with "S" (e.g., S1, S2, S10)

### 4. timeslots.csv
```csv
Day,StartTime,EndTime
Sunday,9:00 AM,10:30 AM
Sunday,10:45 AM,12:15 PM
Monday,9:00 AM,10:30 AM
```

**Required columns:**
- `Day`: Day of the week
- `StartTime`: Class start time
- `EndTime`: Class end time

### 5. sections.csv
```csv
SectionID,Capacity
1/1,30
1/2,30
2/1,30
3/CNC/1,30
3/AID/1,30
4/CNC/1,30
```

**Required columns:**
- `SectionID`: Section identifier with format:
  - **Years 1-2**: `year/number` (e.g., "1/1", "1/2", "2/1")
  - **Years 3-4**: `year/department/number` (e.g., "3/CNC/1", "4/AID/2")
- `Capacity`: Maximum students per section

**Section ID Format Rules:**
- First part: Academic year (1, 2, 3, or 4)
- **For Years 1-2**: Second part is section number
- **For Years 3-4**: Second part is department code (CNC, AID, CSC, BIF, etc.), third part is section number
- Department code is matched against first 3 letters of CourseID
  - Example: Course "AID321" matches sections "3/AID/1", "3/AID/2", etc.
  - Example: Course "CNC401" matches sections "4/CNC/1", "4/CNC/2", etc.

**Note:** If sections.csv is not provided or has fewer entries than courses, the system will automatically generate appropriate sections for all courses based on their year level.

## 🎯 How It Works

1. **Data Loading**: The system loads and validates all CSV files
2. **Smart Course Assignment**: Automatically assigns courses to appropriate sections based on year and department
3. **Session Type Parsing**: Analyzes course Type field to create appropriate session types (Lecture, Lab, Section)
4. **Domain Building**: Creates possible assignments (course-room-instructor-time combinations) with strict constraints:
   - **Room type matching**: Lecture sessions → Lecture rooms (R-series), Lab sessions → Lab rooms (L-series), Section sessions → Section rooms (S-series)
   - **Role-based assignment**: Professors → Lecture sessions only, Assistant Professors → Lab and Section sessions only
   - Instructor qualifications and preferences
   - Time conflict prevention
   - Day preferences (respects "Not on [Day]" constraints)
5. **CSP Solving**: Uses forward checking with backtracking to find valid assignments
6. **Result Formatting**: Sorts chronologically by day and time, applies color coding
7. **Performance Tracking**: Measures and reports generation time to the user

## 🔧 Algorithm Details

### Constraint Satisfaction Problem (CSP)

The timetable generation is modeled as a CSP with:

- **Variables**: Each course section session (e.g., "CSC111::1/1::Lecture", "MTH111::1/2::Section")
- **Domains**: All valid (timeslot, room, instructor) combinations
- **Constraints**:
  - No instructor conflicts (same instructor, different courses, same time)
  - No room conflicts (same room, different courses, same time)
  - Instructor qualifications (instructor must be qualified for the course)
  - **Strict role-based assignment** (Professors teach lectures ONLY, Assistant Professors teach labs and sections ONLY - no fallback)
  - **Strict room type matching** (Lecture sessions use R-series rooms, Lab sessions use L-series rooms, Section sessions use S-series rooms)
  - Instructor day preferences (respect "Not on [Day]" preferences)

### Search Strategy

- **Variable Selection**: Minimum Remaining Values (MRV) heuristic
- **Domain Randomization**: Shuffles domain values for better day distribution
- **Forward Checking**: Eliminates inconsistent values from future variables
- **Backtracking**: Intelligent backtracking when conflicts arise

### Role-Based Assignment System

The system enforces **strict role-based assignment** to maintain academic standards:

1. **Hard Constraints** (Never Violated):
   - **Professors**: Assigned to Lecture sessions ONLY
   - **Assistant Professors**: Assigned to Lab and Section sessions ONLY
   - Role mismatches are completely prevented during domain generation
   - No fallback mechanism exists for role violations

2. **Room Type Matching** (Strictly Enforced):
   - **Lecture sessions**: Must use Lecture-type rooms (typically R-series)
   - **Lab sessions**: Must use Lab-type rooms (typically L-series)
   - **Section sessions**: Must use Section-type rooms (typically S-series)
   - Room type mismatches for Lecture/Section sessions are prevented

3. **Progressive Fallbacks** (For Other Constraints):
   - If qualification/room constraints fail, the system has fallbacks:
     - Allow unqualified instructors (if needed)
     - Allow room type mismatches for Labs (if needed)
   - **Note**: Role constraints are NEVER relaxed

4. **Smart Section Assignment**:
   - **Years 1-2**: Courses assigned to any section of the same year
   - **Years 3-4**: Courses assigned to sections matching both year AND department
     - Example: "AID321" → "3/AID/1", "3/AID/2", etc.
     - Example: "CNC401" → "4/CNC/1", "4/CNC/2", etc.

This ensures role-appropriate teaching assignments while maintaining flexibility for other constraints.

## 🌐 Web Interface

The web interface provides:

1. **File Upload**: Drag-and-drop or click to upload CSV files for each data type
2. **Data Validation**: Automatic validation of file formats and required columns
3. **Real-time Feedback**: Visual progress indicators during generation
4. **Performance Metrics**: Displays generation time and number of assignments
5. **Formatted Excel Download**: One-click download of color-coded timetable

### User Experience Features

- **Smart Messaging**: Shows upload status, generation progress, and completion time
- **Success Indicators**: Green checkmarks for successful uploads
- **Error Handling**: Clear error messages if generation fails
- **Download Automation**: Automatically triggers file download upon completion

### Excel Output Features

The generated Excel file includes:
- **Color-coded sessions**: Yellow background for lectures, blue background for labs, green background for sections
- **Chronological sorting**: Organized by day (Sunday → Thursday) and time (9:00 AM → 2:15 PM)
- **Professional formatting**: Borders, proper column widths, centered text, and text wrapping
- **Complete information**: Course details, instructor names (role-appropriate), rooms (type-matched), and time slots

## 📈 Output Format

The generated timetable includes:

- **CourseID**: Course identifier
- **CourseName**: Full course name
- **SectionID**: Section identifier (e.g., "1/5" for Year 1, "3/CNC/1" for Year 3 CNC department)
- **Session**: Session type ("Lecture", "Lab", or "Section") - color-coded in Excel
- **Day**: Day of the week (sorted: Sunday → Monday → Tuesday → Wednesday → Thursday)
- **StartTime** & **EndTime**: Class timing (sorted chronologically within each day)
- **Room**: Assigned room (type-matched: R-series for Lectures, L-series for Labs, S-series for Sections)
- **Instructor**: Assigned instructor name (role-appropriate: Professors for Lectures, Assistant Professors for Labs/Sections)

### Performance Metrics

After generation completes, the system displays:
- **Generation Time**: How long it took to create the timetable (in seconds)
- **Total Assignments**: Number of scheduled sessions
- Example: *"Generated in 16.21s (145 assignments)"*

This information helps monitor system performance and understand the complexity of the generated schedule.

## 🔍 Troubleshooting

### Common Issues

1. **"No valid timetable found"**
   - Check instructor qualifications match course requirements
   - **Verify sufficient Professors for all Lecture sessions** (strict requirement)
   - **Verify sufficient Assistant Professors for all Lab and Section sessions** (strict requirement)
   - Ensure enough timeslots and rooms are available
   - Verify appropriate room types: R-series for Lectures, L-series for Labs, S-series for Sections
   - Check instructor day preferences aren't too restrictive

2. **Missing courses in output**
   - Courses appear only if they have sections (auto-generated based on year/department if needed)
   - Check that instructors are qualified for all courses
   - **Ensure proper role distribution** (cannot assign Professors to Labs/Sections, or Assistant Professors to Lectures)

3. **Section assignment issues (Years 3-4)**
   - Verify section IDs follow format: "year/department/number" (e.g., "3/CNC/1", "4/AID/2")
   - Department code must match first 3 letters of CourseID
   - Example: AID courses need AID sections, CNC courses need CNC sections

4. **Role assignment is strict**
   - Verify the `Role` column in instructors.csv contains either "Professor" or "Assistant Professor"
   - **The system has NO fallback for role mismatches** - this is a hard constraint
   - If generation fails, you may need to adjust instructor roles or hire additional staff

4. **Slow generation time**
   - Large datasets (90+ courses) may take 15-30 seconds
   - Performance metrics are displayed after completion
   - Check server console for detailed timing logs

5. **Uneven day distribution**
   - The algorithm uses randomization for balanced distribution
   - Run generation multiple times for different distributions

### Debug Information

The system provides detailed diagnostic information when generation fails, including:
- Variables with empty domains
- Constraint violation statistics
- Role mismatch rejection counts
- Fallback attempt results

## 👨‍💻 Development

### Key Files

- `server.py`: Flask web application handling uploads and downloads
- `csp.py`: Core constraint satisfaction algorithm
- `templates/index.html`: Web interface

### Adding New Constraints

To add new constraints, modify the `build_domains()` function in `csp.py`:

```python
# Example: Add maximum classes per day constraint
if classes_per_day[instructor][day] >= max_classes:
    rejection_reasons[var]['max_classes_exceeded'] += 1
    continue
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

Created by [Abdelrahman Gawad](https://github.com/Gawad-B)

- GitHub: [@Gawad-B](https://github.com/Gawad-B)
- Website: [https://gawad163.pythonanywhere.com](https://gawad163.pythonanywhere.com)

---

**ATTG** - Making timetable generation intelligent and effortless! 🎓