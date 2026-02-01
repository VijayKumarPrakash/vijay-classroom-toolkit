import csv
import io
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

class StudentManagerError(Exception):
    """Base exception for student manager errors."""
    pass

class DuplicateStudentIdError(StudentManagerError):
    """Raised when attempting to add a student with an existing ID."""
    pass

class SectionNotFoundError(StudentManagerError):
    """Raised when an operation is requested for a non-existent section."""
    pass

class StudentNotFoundError(StudentManagerError):
    """Raised when an operation is requested for a non-existent student."""
    pass

@dataclass
class Student:
    """
    Represents a student entity.
    
    Attributes:
        name (str): The full name of the student.
        student_id (str): Unique identifier for the student.
        section_id (str): The ID of the section the student belongs to.
    """
    name: str
    student_id: str
    section_id: str

@dataclass
class Section:
    """
    Represents a classroom section.
    
    Attributes:
        section_id (str): Unique identifier for the section.
        name (str): Human-readable name of the section (e.g., "Math 101").
    """
    section_id: str
    name: str

class StudentManager:
    """
    Manages students and sections within a school system.
    
    This class serves as the central repository for student and section data.
    It enforces constraints such as unique student IDs and ensures referential
    integrity between students and sections.
    """

    def __init__(self) -> None:
        # Storage: section_id -> Section object
        self._sections: Dict[str, Section] = {}
        # Storage: student_id -> Student object
        self._students: Dict[str, Student] = {}
        # Index: section_id -> Set of student_ids for O(1) lookup by section
        self._section_roster_index: Dict[str, Set[str]] = {}

    def add_section(self, section_id: str, name: str) -> Section:
        """
        Creates and adds a new section to the manager.

        Args:
            section_id (str): Unique ID for the section.
            name (str): Name of the section.

        Returns:
            Section: The created section object.
        """
        if section_id in self._sections:
            # Idempotent update or raise error? Choosing update for simplicity here,
            # but in strict systems, this might raise an error.
            self._sections[section_id].name = name
        else:
            self._sections[section_id] = Section(section_id=section_id, name=name)
            self._section_roster_index[section_id] = set()
        
        return self._sections[section_id]

    def get_section(self, section_id: str) -> Optional[Section]:
        """Retrieves a section by ID."""
        return self._sections.get(section_id)

    def add_student(self, name: str, section_id: str, student_id: Optional[str] = None) -> Student:
        """
        Adds a new student to the system.

        Args:
            name (str): Student's name.
            section_id (str): ID of the section to assign.
            student_id (Optional[str]): Unique student ID. If not provided, auto-generated.

        Returns:
            Student: The created student object.

        Raises:
            DuplicateStudentIdError: If student_id already exists.
            SectionNotFoundError: If section_id does not exist.
        """
        if student_id is None:
            student_id = str(uuid.uuid4())
        
        if student_id in self._students:
            raise DuplicateStudentIdError(f"Student ID {student_id} already exists.")
        
        # Create section if it doesn't exist
        if section_id not in self._sections:
            self.add_section(section_id, section_id)  # Use section_id as name for simplicity

        new_student = Student(name=name, student_id=student_id, section_id=section_id)
        
        self._students[student_id] = new_student
        self._section_roster_index[section_id].add(student_id)
        
        return new_student

    def remove_student(self, student_id: str) -> None:
        """
        Removes a student from the system.

        Args:
            student_id (str): The ID of the student to remove.

        Raises:
            StudentNotFoundError: If the student does not exist.
        """
        if student_id not in self._students:
            raise StudentNotFoundError(f"Student ID {student_id} not found.")

        student = self._students[student_id]
        
        # Clean up index
        if student.section_id in self._section_roster_index:
            self._section_roster_index[student.section_id].discard(student_id)
        
        # Remove record
        del self._students[student_id]

    def update_student(self, student_id: str, name: Optional[str] = None, section_id: Optional[str] = None) -> Student:
        """
        Updates an existing student's details.

        Args:
            student_id (str): The ID of the student to update.
            name (Optional[str]): New name (if changing).
            section_id (Optional[str]): New section ID (if changing).

        Returns:
            Student: The updated student object.

        Raises:
            StudentNotFoundError: If the student does not exist.
            SectionNotFoundError: If the new section_id does not exist.
        """
        if student_id not in self._students:
            raise StudentNotFoundError(f"Student ID {student_id} not found.")

        student = self._students[student_id]

        if name is not None:
            student.name = name

        if section_id is not None and section_id != student.section_id:
            if section_id not in self._sections:
                raise SectionNotFoundError(f"Target Section ID {section_id} not found.")
            
            # Remove from old section index
            self._section_roster_index[student.section_id].discard(student_id)
            
            # Update student record
            student.section_id = section_id
            
            # Add to new section index
            self._section_roster_index[section_id].add(student_id)

        return student

    def get_students_by_section(self, section_id: str) -> List[Student]:
        """
        Retrieves all students belonging to a specific section.

        Args:
            section_id (str): The section ID to filter by.

        Returns:
            List[Student]: A list of Student objects.

        Raises:
            SectionNotFoundError: If the section does not exist.
        """
        if section_id not in self._sections:
            raise SectionNotFoundError(f"Section ID {section_id} not found.")

        student_ids = self._section_roster_index.get(section_id, set())
        return [self._students[sid] for sid in student_ids]

    def import_roster_from_csv(self, csv_text: str) -> Dict[str, int]:
        """
        Imports students and sections from a CSV string.
        
        Expected CSV format: section_id, section_name, student_id, student_name
        
        This method is upsert-friendly for sections (will create if missing),
        but strict on duplicate student IDs.

        Args:
            csv_text (str): The raw CSV content string.

        Returns:
            Dict[str, int]: Statistics on the import {'students_added': int, 'sections_seen': int}
        """
        f = io.StringIO(csv_text)
        reader = csv.DictReader(f)
        
        # Normalize headers to lower case strip for robustness
        reader.fieldnames = [name.strip().lower() for name in (reader.fieldnames or [])]
        
        required_fields = {'section_id', 'section_name', 'student_id', 'student_name'}
        if not required_fields.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"CSV must contain columns: {required_fields}")

        stats = {'students_added': 0, 'sections_seen': 0}
        seen_sections = set()

        for row in reader:
            sec_id = row['section_id'].strip()
            sec_name = row['section_name'].strip()
            stu_id = row['student_id'].strip()
            stu_name = row['student_name'].strip()

            # Ensure section exists
            if sec_id not in self._sections:
                self.add_section(sec_id, sec_name)
            
            seen_sections.add(sec_id)

            # Add student
            try:
                self.add_student(stu_name, sec_id, stu_id)
                stats['students_added'] += 1
            except DuplicateStudentIdError:
                # In a bulk import, we might log this and continue, 
                # or raise. For this implementation, we skip duplicates.
                continue

        stats['sections_seen'] = len(seen_sections)
        return stats