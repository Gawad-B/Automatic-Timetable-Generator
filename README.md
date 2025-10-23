# ATTG - Automatic Timetable Generator

An intelligent automatic timetable generator that uses constraint satisfaction algorithms to create optimized class schedules for educational institutions. Generates comprehensive timetable packages with separate schedules for years, instructors, and rooms.

## 🌟 Features

### Core Scheduling Engine
- **Advanced CSP Algorithm**: Uses constraint satisfaction with forward checking and backtracking
- **Multi-Session Support**: Handles Lecture, Lab, and TUT (Tutorial) sessions with flexible durations
- **Smart Section Conflict Prevention**: Ensures no section is double-booked at the same timeslot
- **Flexible Duration Support**: 90-minute sessions for lectures/labs, 45-minute tutorials based on course type
- **Individual Tutorial Scheduling**: Each tutorial section gets its own dedicated timeslot

### Intelligent Assignment Rules
- **Strict Role-Based Assignment**: Professors teach lectures, Assistant Professors handle labs and tutorials
- **Room Type Matching**: Automatic assignment of Lecture rooms (R-series), Lab rooms (L-series), Tutorial rooms (T-series)
- **Department-Based Sections**: Smart section assignment by year and department for Years 3-4
- **Shared Course Support**: Year 3 courses can be shared across departments (AID, BIF, CSC, CNC)
- **Section Grouping**: Lectures group 3-4 sections, Labs group 2 sections, Tutorials are individual

### Multi-File Export System
- **Comprehensive ZIP Package**: Single download containing all timetables
- **Main Timetable**: Complete schedule with all assignments
- **Year-Specific Timetables**: Separate Excel files for Year 1, 2, 3, and 4
- **Instructor Timetables**: Individual schedules for each professor and assistant professor
- **Room Timetables**: Usage schedules for each classroom, lab, and tutorial room
- **Color-Coded Sessions**: Yellow for lectures, blue for labs, purple for tutorials

### User Experience
- **Web Interface**: Modern, user-friendly interface with drag-and-drop uploads
- **Real-Time Feedback**: Progress indicators and performance metrics
- **Detailed Statistics**: Generation time, assignment count, and file count
- **Performance Tracking**: Displays timing information and comprehensive logs

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
CourseID,CourseName,Credits,Type,Year,Shared
CSC111,Fundamentals of Programming,3,Lecture and Lab,1,
MTH111,Mathematics (1),3,Lecture and TUT,1,
PHY113,Physics (1),3,Lecture and Lab and TUT,1,
AID311,Mathematics of Data Science,3,Lecture and Lab and TUT,3,
CSC315,Seminar and Project Based,3,Lecture and Lab,3,Yes
```

**Required columns:**
- `CourseID`: Unique identifier for the course
- `CourseName`: Full name of the course
- `Credits`: Number of credit hours
- `Type`: Session type - can be:
  - `"Lecture"` - Lecture only (90 minutes)
  - `"Lecture and Lab"` - Creates both Lecture and Lab sessions (90 minutes each)
  - `"Lecture and TUT"` - Creates Lecture and Tutorial sessions (90 minutes each)
  - `"Lecture and Lab and TUT"` - Creates all three session types (Lecture 90min, Lab 90min, TUT 45min)
- `Year`: Academic year (1, 2, 3, or 4)
- `Shared` (Optional): "Yes" for Year 3 courses shared across departments (AID, BIF, CSC, CNC)

**Tutorial Duration Rules:**
- Courses with "Lecture and Lab and TUT" → TUT sessions are **45 minutes**
- Courses with "Lecture and TUT" (no Lab) → TUT sessions are **90 minutes**

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
R101,Lecture,80
R102,Lecture,80
L11,Lab,35
L12,Lab,35
T1,TUT,35
T2,TUT,35
```

**Required columns:**
- `RoomID`: Unique identifier for the room
- `Type`: Room type - can be:
  - `"Lecture"` - For lecture sessions (typically larger capacity)
  - `"Lab"` - For lab sessions (with equipment)
  - `"TUT"` - For tutorial/discussion sessions (smaller groups)
- `Capacity`: Maximum number of students

**Room Naming Conventions:**
- Lecture rooms: Typically start with "R" (e.g., R101, R102, R103, R104, R105)
- Lab rooms: Typically start with "L" (e.g., L11, L12, L13, L14)
- Tutorial rooms: Typically start with "T" (e.g., T1, T2)

### 4. timeslots.csv
```csv
Day,StartTime,EndTime,Duration
Sunday,9:00 AM,10:30 AM,90
Sunday,10:45 AM,12:15 PM,90
Sunday,9:00 AM,9:45 AM,45
Sunday,9:45 AM,10:30 AM,45
Monday,9:00 AM,10:30 AM,90
```

**Required columns:**
- `Day`: Day of the week
- `StartTime`: Class start time
- `EndTime`: Class end time
- `Duration` (Optional): Duration in minutes (90 or 45)

**Duration System:**
- **90-minute slots**: Used for Lectures and Labs
- **45-minute slots**: Used for TUT sessions (when course has "Lecture and Lab and TUT")
- System automatically filters appropriate timeslots based on session type and course configuration

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
   - Years 1-2: Simple year matching
   - Years 3-4: Department and year matching
   - Shared courses (Year 3): Assigned to all departments (AID, BIF, CSC, CNC)
3. **Session Type Parsing**: Analyzes course Type field to create appropriate session types (Lecture, Lab, TUT)
   - Creates individual variables for each section group and session type
   - Tutorials: Each section gets its own timeslot (1 section per group)
   - Labs: Sections paired (2 sections per group)
   - Lectures: Sections grouped by 3-4 per group
4. **Duration Assignment**: Intelligently assigns session durations
   - "Lecture and Lab and TUT" courses → TUT sessions use 45-minute timeslots
   - "Lecture and TUT" courses → TUT sessions use 90-minute timeslots
   - All Lectures and Labs use 90-minute timeslots
5. **Domain Building**: Creates possible assignments with strict constraints:
   - **Room type matching**: Lecture → R-rooms, Lab → L-rooms, TUT → T-rooms
   - **Role-based assignment**: Professors → Lectures only, Assistant Professors → Labs and TUTs only
   - **Section conflict prevention**: No section can be assigned to multiple courses at the same timeslot
   - Instructor qualifications and day preferences
   - Timeslot duration matching
6. **CSP Solving**: Uses forward checking with backtracking to find valid assignments
7. **Multi-File Generation**: Creates comprehensive timetable package
   - Main timetable with all assignments
   - Year-specific timetables (filtered by year)
   - Instructor-specific timetables (filtered by instructor)
   - Room-specific timetables (filtered by room)
8. **ZIP Packaging**: Bundles all Excel files into a single downloadable ZIP
9. **Performance Tracking**: Measures and reports generation time and file count

## 🔧 Algorithm Details

### Constraint Satisfaction Problem (CSP)

The timetable generation is modeled as a CSP with:

- **Variables**: Each course section session (e.g., "CSC111::1/1::Lecture", "MTH111::1/2::TUT")
- **Domains**: All valid (timeslot, room, instructor) combinations
- **Constraints**:
  - **No instructor conflicts**: Same instructor cannot teach different courses at same time
  - **No room conflicts**: Same room cannot host different courses at same time
  - **No section conflicts**: Same section cannot attend different courses at same time (NEW)
  - **Instructor qualifications**: Instructor must be qualified for the course
  - **Strict role-based assignment**: Professors teach Lectures ONLY, Assistant Professors teach Labs and TUTs ONLY
  - **Strict room type matching**: Lecture → R-rooms, Lab → L-rooms, TUT → T-rooms
  - **Duration matching**: Sessions matched to appropriate timeslot durations (45min or 90min)
  - **Instructor day preferences**: Respect "Not on [Day]" constraints

### Search Strategy

- **Variable Selection**: Minimum Remaining Values (MRV) heuristic
- **Domain Randomization**: Shuffles domain values for better day distribution
- **Forward Checking**: Eliminates inconsistent values from future variables after each assignment
- **Conflict Tracking**: Maintains three separate tracking sets per timeslot:
  - `instructors`: Prevents instructor double-booking
  - `rooms`: Prevents room double-booking
  - `sections`: Prevents section double-booking (NEW)
- **Backtracking**: Intelligent backtracking when conflicts arise

### Role-Based Assignment System

The system enforces **strict role-based assignment** to maintain academic standards:

1. **Hard Constraints** (Never Violated):
   - **Professors**: Assigned to Lecture sessions ONLY
   - **Assistant Professors**: Assigned to Lab and TUT sessions ONLY
   - Role mismatches are completely prevented during domain generation
   - No fallback mechanism exists for role violations

2. **Room Type Matching** (Strictly Enforced):
   - **Lecture sessions**: Must use Lecture-type rooms (typically R-series)
   - **Lab sessions**: Must use Lab-type rooms (typically L-series)
   - **TUT sessions**: Must use TUT-type rooms (typically T-series)
   - Room type mismatches for Lecture/TUT sessions are prevented

3. **Duration-Based Domain Filtering**:
   - Courses with "Lecture and Lab and TUT" → TUT sessions limited to 45-minute timeslots
   - Courses with "Lecture and TUT" → TUT sessions limited to 90-minute timeslots
   - All Lectures and Labs use 90-minute timeslots
   - Ensures proper session pacing and student schedules

4. **Progressive Fallbacks** (For Other Constraints):
   - If qualification/room constraints fail, the system has fallbacks:
     - Allow unqualified instructors (if needed)
     - Allow room type mismatches for Labs (if needed)
   - **Note**: Role constraints and section conflicts are NEVER relaxed

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

The generated Excel files include:
- **Color-coded sessions**: 
  - Yellow background (#FFD966) for Lecture sessions
  - Blue background (#9FC5E8) for Lab sessions
  - Purple background (#B4A7D6) for TUT sessions
- **Multi-file package**: Main timetable plus separate files for each year, instructor, and room
- **Chronological sorting**: Organized by day (Sunday → Thursday) and time (9:00 AM → 2:15 PM)
- **Professional formatting**: Borders, proper column widths, centered text, and text wrapping
- **Complete information**: Course details, instructor names (role-appropriate), rooms (type-matched), and time slots
- **Duration-aware**: Properly handles both 45-minute and 90-minute sessions

## 📈 Output Format

### ZIP File Structure
The system generates a single **timetables.zip** file containing:

```
timetables.zip
├── Main_Timetable.xlsx                    # Complete schedule
├── Years/
│   ├── Year_1.xlsx                        # All Year 1 sections
│   ├── Year_2.xlsx                        # All Year 2 sections
│   ├── Year_3.xlsx                        # All Year 3 sections
│   └── Year_4.xlsx                        # All Year 4 sections
├── Instructors/
│   ├── Dr. John Smith.xlsx                # Individual instructor schedules
│   ├── Eng. Jane Doe.xlsx
│   └── ... (one file per instructor)
└── Rooms/
    ├── R101.xlsx                          # Individual room schedules
    ├── L11.xlsx
    ├── T1.xlsx
    └── ... (one file per room)
```

### Excel File Contents

Each Excel file includes:

- **CourseID**: Course identifier
- **CourseName**: Full course name
- **SectionID**: Section identifier (e.g., "1/5" for Year 1, "3/CNC/1" for Year 3 CNC department)
- **Session**: Session type ("Lecture", "Lab", or "TUT") - **color-coded**:
  - 🟨 **Yellow**: Lecture sessions
  - 🟦 **Blue**: Lab sessions
  - 🟪 **Purple**: TUT (Tutorial) sessions
- **Day**: Day of the week (sorted: Sunday → Monday → Tuesday → Wednesday → Thursday)
- **StartTime** & **EndTime**: Class timing (sorted chronologically within each day)
- **Room**: Assigned room (type-matched: R-series for Lectures, L-series for Labs, T-series for TUTs)
- **Instructor**: Assigned instructor name (role-appropriate: Professors for Lectures, Assistant Professors for Labs/TUTs)

### Performance Metrics

After generation completes, the system displays:
- **Generation Time**: How long it took to create the timetable (in seconds)
- **Total Files**: Number of Excel files generated (typically 60-70 files)
- **Total Assignments**: Number of scheduled sessions
- Example: *"Generated in 14.70s (65 files)"*

This information helps monitor system performance and understand the complexity of the generated schedule.

## 🔍 Troubleshooting

### Common Issues

1. **"No valid timetable found"**
   - Check instructor qualifications match course requirements
   - **Verify sufficient Professors for all Lecture sessions** (strict requirement)
   - **Verify sufficient Assistant Professors for all Lab and TUT sessions** (strict requirement)
   - Ensure enough timeslots and rooms are available
   - Verify appropriate room types: R-series for Lectures, L-series for Labs, T-series for TUTs
   - Check instructor day preferences aren't too restrictive
   - Verify timeslots have correct Duration values (45 or 90 minutes)
   - Ensure sections aren't double-booked (section conflict prevention)

2. **Missing courses in output**
   - Courses appear only if they have sections (auto-generated based on year/department if needed)
   - Check that instructors are qualified for all courses
   - **Ensure proper role distribution** (cannot assign Professors to Labs/TUTs, or Assistant Professors to Lectures)
   - For Year 3 shared courses, verify "Shared" column is set to "Yes"

3. **Section assignment issues (Years 3-4)**
   - Verify section IDs follow format: "year/department/number" (e.g., "3/CNC/1", "4/AID/2")
   - Department code must match first 3 letters of CourseID
   - Example: AID courses need AID sections, CNC courses need CNC sections
   - **Section conflicts**: Each section can only attend one course per timeslot (enforced by CSP)

4. **Role assignment is strict**
   - Verify the `Role` column in instructors.csv contains either "Professor" or "Assistant Professor"
   - **The system has NO fallback for role mismatches** - this is a hard constraint
   - If generation fails, you may need to adjust instructor roles or hire additional staff

5. **ZIP file download issues**
   - Ensure browser allows automatic downloads
   - Check that server has write permissions for temporary files
   - Verify all CSV files are properly formatted before generation
   - File count should match: 1 main + 4 years + instructors count + rooms count

6. **TUT duration issues**
   - 45-minute TUTs: Course Type must be "Lecture and Lab and TUT"
   - 90-minute TUTs: Course Type must be "Lecture and TUT"
   - Check timeslots.csv has entries with Duration=45 and Duration=90
   - Each TUT session is scheduled individually (1 section per timeslot)

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