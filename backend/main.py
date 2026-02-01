import sys
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --- Import Path Configuration ---
# Ensure the 'src' directory is in the python path so we can import modules
# Assuming the structure is:
# /project_root
#   /backend
#     main.py
#   /src
#     student_manager.py
#     classroom_tools.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from student_manager import StudentManager
    from classroom_tools import ClassroomTools
except ImportError as e:
    print(f"Error importing core modules: {e}")
    print("Please ensure 'student_manager.py' and 'classroom_tools.py' exist in the '../src' directory.")
    sys.exit(1)

# --- Pydantic Models ---

class StudentCreate(BaseModel):
    """Schema for adding a new student."""
    name: str = Field(..., min_length=1, description="Name of the student")
    section_id: str = Field(..., min_length=1, description="ID of the section the student belongs to")

class GroupRequest(BaseModel):
    """Schema for requesting group creation."""
    section_id: str = Field(..., description="The section ID to group")
    group_size: int = Field(..., gt=1, description="Target size for each group")

class StudentResponse(BaseModel):
    """Schema for student output."""
    id: str
    name: str
    section_id: str

# --- App Initialization ---

app = FastAPI(
    title="Vijay's Classroom Toolkit API",
    description="Backend API for managing students, sections, and classroom utilities.",
    version="1.0.0"
)

# --- CORS Configuration ---

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dependency Injection / State Management ---

# Initialize core business logic modules
# In a larger app, these might be injected via `Depends`, but global instances work for this scale.
student_manager = StudentManager()
classroom_tools = ClassroomTools(student_manager)

# --- Endpoints ---

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Vijay's Classroom Toolkit API is running"}

@app.post("/students", response_model=StudentResponse, status_code=201)
async def add_student(student: StudentCreate):
    """
    Add a student to a specific section.
    Delegates to StudentManager.
    """
    try:
        # Assuming student_manager.add_student returns the created student dict or object
        new_student = student_manager.add_student(student.name, student.section_id)
        return new_student
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/sections/{section_id}", response_model=List[StudentResponse])
async def get_section_students(section_id: str):
    """
    Retrieve all students in a specific section.
    """
    students = student_manager.get_students_by_section(section_id)
    if not students:
        # Depending on requirements, empty list might be valid, 
        # or 404 if the section strictly doesn't exist.
        # Returning empty list is usually safer for UI.
        return []
    return students

@app.post("/spin/{section_id}", response_model=StudentResponse)
async def spin_wheel(section_id: str):
    """
    Randomly select a student from a section.
    Delegates to ClassroomTools.
    """
    try:
        selected_student = classroom_tools.spin_wheel(section_id)
        if not selected_student:
            raise HTTPException(status_code=404, detail="No students found in this section to select from.")
        return selected_student
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/groups", response_model=List[List[StudentResponse]])
async def create_groups(request: GroupRequest):
    """
    Create random groups of students from a section.
    Delegates to ClassroomTools.
    """
    try:
        groups = classroom_tools.create_groups(request.section_id, request.group_size)
        if not groups:
             raise HTTPException(status_code=404, detail="Not enough students to form groups.")
        return groups
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))