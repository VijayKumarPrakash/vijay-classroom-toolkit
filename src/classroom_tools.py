import random
import math
from typing import List, Dict, Any, Optional
from student_manager import StudentManager, Student

class ClassroomTools:
    def __init__(self, student_manager: StudentManager):
        self.student_manager = student_manager

    def spin_wheel(self, section_id: str) -> Optional[Dict[str, Any]]:
        """
        Randomly selects a single student from a specific section.

        Args:
            section_id (str): The unique identifier for the discussion section.

        Returns:
            Optional[Dict[str, Any]]: A dictionary representing the selected student, 
                                      or None if the section is empty or does not exist.
        """
        try:
            students = self.student_manager.get_students_by_section(section_id)
        except:
            return None
        
        if not students:
            return None
            
        selected = random.choice(students)
        return {
            "id": selected.student_id,
            "name": selected.name,
            "section_id": selected.section_id
        }

    def create_groups(self, section_id: str, group_size: int) -> List[List[Dict[str, Any]]]:
        """
        Creates groups of a specific size from the students in a section.
        The final group may contain fewer students than the specified group_size.

        Args:
            section_id (str): The unique identifier for the discussion section.
            group_size (int): The target number of students per group.

        Returns:
            List[List[Dict[str, Any]]]: A list of groups, where each group is a list of student dictionaries.
                                        Returns an empty list if no students are found.
        
        Raises:
            ValueError: If group_size is less than 1.
        """
        if group_size < 1:
            raise ValueError("Group size must be at least 1.")

        try:
            students = self.student_manager.get_students_by_section(section_id)
        except:
            return []
        
        if not students:
            return []

        # Shuffle to ensure randomness
        shuffled_students = students.copy()
        random.shuffle(shuffled_students)

        groups = []
        for i in range(0, len(shuffled_students), group_size):
            group_students = shuffled_students[i : i + group_size]
            groups.append([{
                "id": s.student_id,
                "name": s.name,
                "section_id": s.section_id
            } for s in group_students])

        return groups