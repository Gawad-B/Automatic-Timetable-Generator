# ATTG - Automatic Timetable Generator

An intelligent automatic timetable generator that uses constraint satisfaction algorithms to create optimized class schedules for educational institutions.

## 🌟 Features

- **Smart Constraint Satisfaction**: Uses advanced CSP algorithms with forward checking and backtracking
- **Multi-Day Scheduling**: Distributes classes across Sunday-Thursday with intelligent day balancing
- **Role-Based Assignment**: Automatically assigns Professors to lectures and Assistant Professors to labs
- **Instructor Management**: Respects instructor preferences, qualifications, and role-based restrictions
- **Dual Session Support**: Handles both lecture and lab sessions for courses
- **Room Allocation**: Matches room types (lecture halls vs labs) with course requirements
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
MTH111,Mathematics (1),3,Lecture and Lab
LRA101,Japanese Culture,2,Lecture
```

**Required columns:**
- `CourseID`: Unique identifier for the course
- `CourseName`: Full name of the course
- `Credits`: Number of credit hours
- `Type`: Either "Lecture", "Lab", or "Lecture and Lab"

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
- Instructors with "Assistant Professor" role are assigned to **lab sessions only**
- Proper role assignment ensures optimal instructor utilization

### 3. rooms.csv
```csv
RoomID,Type,Capacity
R101,Lecture,80
L1,Lab,35
R102,Lecture,80
```

**Required columns:**
- `RoomID`: Unique identifier for the room
- `Type`: Either "Lecture" or "Lab"
- `Capacity`: Maximum number of students

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

### 5. sections.csv (Optional)
```csv
SectionID,Semester,Capacity
1/1,fall,30
1/2,fall,30
2/1,fall,30
```

**Required columns:**
- `SectionID`: Section identifier (format: level/section)
- `Semester`: Academic semester
- `Capacity`: Maximum students per section

**Note:** If sections.csv has fewer entries than courses, the system will automatically generate sections for all courses.

## 🎯 How It Works

1. **Data Loading**: The system loads and validates all CSV files
2. **Domain Building**: Creates possible assignments (course-room-instructor-time combinations)
3. **Constraint Application**: 
   - Instructor qualifications and preferences
   - **Role-based assignment** (Professors → Lectures, Assistant Professors → Labs)
   - Room type matching (lab courses → lab rooms)
   - Time conflict prevention
   - Day preferences (respects "Not on [Day]" constraints)
4. **CSP Solving**: Uses forward checking with backtracking to find valid assignments
5. **Result Formatting**: Sorts chronologically by day and time, applies color coding
6. **Performance Tracking**: Measures and reports generation time to the user

## 🔧 Algorithm Details

### Constraint Satisfaction Problem (CSP)

The timetable generation is modeled as a CSP with:

- **Variables**: Each course section session (e.g., "CSC111::1/1::Lecture")
- **Domains**: All valid (timeslot, room, instructor) combinations
- **Constraints**:
  - No instructor conflicts (same instructor, different courses, same time)
  - No room conflicts (same room, different courses, same time)
  - Instructor qualifications (instructor must be qualified for the course)
  - **Role-based assignment** (Professors teach lectures, Assistant Professors teach labs)
  - Room type matching (lab courses require lab rooms)
  - Instructor day preferences (respect "Not on [Day]" preferences)

### Search Strategy

- **Variable Selection**: Minimum Remaining Values (MRV) heuristic
- **Domain Randomization**: Shuffles domain values for better day distribution
- **Forward Checking**: Eliminates inconsistent values from future variables
- **Backtracking**: Intelligent backtracking when conflicts arise

### Role-Based Assignment System

The system enforces instructor role-based assignments with intelligent fallbacks:

1. **Strict Enforcement** (Priority 1):
   - Professors are assigned to lecture sessions
   - Assistant Professors are assigned to lab sessions
   - All other constraints (qualifications, room types, preferences) are respected

2. **Progressive Fallbacks** (Priority 2-4):
   - If strict enforcement fails, the system progressively relaxes constraints:
     - Allow unqualified instructors (if needed)
     - Allow room type mismatches (if needed)
     - Allow role mismatches (as last resort)

3. **Diagnostic Tracking**:
   - The system tracks which fallbacks were used for each assignment
   - Rejection reasons are logged for debugging purposes

This ensures the best possible timetable while maintaining role appropriateness wherever feasible.

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
- **Color-coded sessions**: Yellow background for lectures, blue background for labs
- **Chronological sorting**: Organized by day (Sunday → Thursday) and time (9:00 AM → 2:15 PM)
- **Professional formatting**: Borders, proper column widths, centered text, and text wrapping
- **Complete information**: Course details, instructor names (role-appropriate), rooms, and time slots

## 📈 Output Format

The generated timetable includes:

- **CourseID**: Course identifier
- **CourseName**: Full course name
- **SectionID**: Section identifier (level/section format)
- **Session**: Session type ("Lecture" or "Lab") - color-coded in Excel
- **Day**: Day of the week (sorted: Sunday → Monday → Tuesday → Wednesday → Thursday)
- **StartTime** & **EndTime**: Class timing (sorted chronologically within each day)
- **Room**: Assigned room
- **Instructor**: Assigned instructor name (role-appropriate for session type)

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
   - Verify that you have enough Professors for all lectures and Assistant Professors for all labs
   - Ensure enough timeslots and rooms are available
   - Verify instructor day preferences aren't too restrictive

2. **Missing courses in output**
   - Courses appear only if they have sections (auto-generated if needed)
   - Check that instructors are qualified for all courses
   - Ensure proper role distribution (Professors for lectures, Assistant Professors for labs)

3. **Role assignment issues**
   - Verify the `Role` column in instructors.csv contains either "Professor" or "Assistant Professor"
   - The system has fallback mechanisms but will prioritize role-appropriate assignments

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