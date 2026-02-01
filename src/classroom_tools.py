import random
import math
from typing import List, Dict, Any, Optional
import student_manager

def spin_wheel(section_id: str) -> Optional[Dict[str, Any]]:
    """
    Randomly selects a single student from a specific section.

    Args:
        section_id (str): The unique identifier for the discussion section.

    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the selected student, 
                                  or None if the section is empty or does not exist.
    """
    students = student_manager.get_students_by_section(section_id)
    
    if not students:
        return None
        
    return random.choice(students)

def form_groups_by_size(section_id: str, group_size: int) -> List[List[Dict[str, Any]]]:
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

    students = student_manager.get_students_by_section(section_id)
    
    if not students:
        return []

    # Shuffle to ensure randomness
    shuffled_students = students.copy()
    random.shuffle(shuffled_students)

    groups = []
    for i in range(0, len(shuffled_students), group_size):
        groups.append(shuffled_students[i : i + group_size])

    return groups

def form_groups_by_count(section_id: str, num_groups: int) -> List[List[Dict[str, Any]]]:
    """
    Distributes students into a specific number of groups as evenly as possible.

    Args:
        section_id (str): The unique identifier for the discussion section.
        num_groups (int): The target number of groups to create.

    Returns:
        List[List[Dict[str, Any]]]: A list of groups, where each group is a list of student dictionaries.
                                    Returns an empty list if no students are found.

    Raises:
        ValueError: If num_groups is less than 1.
    """
    if num_groups < 1:
        raise ValueError("Number of groups must be at least 1.")

    students = student_manager.get_students_by_section(section_id)
    
    if not students:
        return []

    # If requested groups exceed student count, cap it at student count (groups of 1)
    target_groups = min(num_groups, len(students))

    # Shuffle to ensure randomness
    shuffled_students = students.copy()
    random.shuffle(shuffled_students)

    # Initialize empty groups
    groups = [[] for _ in range(target_groups)]

    # Distribute students round-robin style
    for index, student in enumerate(shuffled_students):
        group_index = index % target_groups
        groups[group_index].append(student)

    return groups