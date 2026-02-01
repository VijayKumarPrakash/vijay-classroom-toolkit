import pytest
from src.student_manager import (
    StudentManager,
    Student,
    DuplicateStudentIdError,
    SectionNotFoundError,
    StudentNotFoundError,
)


@pytest.fixture
def manager():
    """Fixture to provide a fresh StudentManager instance for each test."""
    return StudentManager()


@pytest.fixture
def populated_manager():
    """Fixture with some pre-loaded data."""
    manager = StudentManager()
    manager.add_section("A", "Section A")
    manager.add_section("B", "Section B")
    manager.add_student("Alice", "A", "alice1")
    manager.add_student("Bob", "A", "bob1")
    manager.add_student("Charlie", "B", "charlie1")
    return manager


class TestAddSection:
    def test_add_section_success(self, manager):
        """Test adding a new section."""
        section = manager.add_section("sec1", "Section 1")

        assert section.section_id == "sec1"
        assert section.name == "Section 1"
        assert manager.get_section("sec1") is not None

    def test_add_section_update_existing(self, manager):
        """Test that adding a section with same ID updates the name."""
        manager.add_section("sec1", "Original Name")
        manager.add_section("sec1", "Updated Name")

        section = manager.get_section("sec1")
        assert section.name == "Updated Name"


class TestAddStudent:
    def test_add_student_success(self, manager):
        """Test adding a student to a section."""
        manager.add_section("A", "Section A")
        student = manager.add_student("Alice", "A", "alice1")

        assert isinstance(student, Student)
        assert student.name == "Alice"
        assert student.section_id == "A"
        assert student.student_id == "alice1"

    def test_add_student_auto_creates_section(self, manager):
        """Test that adding a student to non-existent section creates it."""
        student = manager.add_student("Alice", "NewSection", "alice1")

        assert student.section_id == "NewSection"
        assert manager.get_section("NewSection") is not None

    def test_add_student_auto_generates_id(self, manager):
        """Test that student_id is auto-generated if not provided."""
        manager.add_section("A", "Section A")
        student = manager.add_student("Alice", "A")

        assert student.student_id is not None
        assert len(student.student_id) > 0

    def test_add_duplicate_student_id_raises(self, manager):
        """Test that adding a student with duplicate ID raises error."""
        manager.add_section("A", "Section A")
        manager.add_student("Alice", "A", "same_id")

        with pytest.raises(DuplicateStudentIdError):
            manager.add_student("Bob", "A", "same_id")


class TestRemoveStudent:
    def test_remove_student_success(self, populated_manager):
        """Test removing an existing student."""
        populated_manager.remove_student("alice1")

        students = populated_manager.get_students_by_section("A")
        student_ids = [s.student_id for s in students]
        assert "alice1" not in student_ids

    def test_remove_student_non_existent_raises(self, populated_manager):
        """Test removing a non-existent student raises error."""
        with pytest.raises(StudentNotFoundError):
            populated_manager.remove_student("nonexistent")


class TestUpdateStudent:
    def test_update_student_name(self, populated_manager):
        """Test updating a student's name."""
        updated = populated_manager.update_student("alice1", name="Alicia")

        assert updated.name == "Alicia"
        assert updated.student_id == "alice1"

    def test_update_student_section(self, populated_manager):
        """Test moving a student to a different section."""
        updated = populated_manager.update_student("alice1", section_id="B")

        assert updated.section_id == "B"

        # Verify student is in new section
        section_b_students = populated_manager.get_students_by_section("B")
        assert any(s.student_id == "alice1" for s in section_b_students)

        # Verify student is not in old section
        section_a_students = populated_manager.get_students_by_section("A")
        assert not any(s.student_id == "alice1" for s in section_a_students)

    def test_update_student_non_existent_raises(self, populated_manager):
        """Test updating a non-existent student raises error."""
        with pytest.raises(StudentNotFoundError):
            populated_manager.update_student("nonexistent", name="New Name")

    def test_update_student_to_non_existent_section_raises(self, populated_manager):
        """Test moving student to non-existent section raises error."""
        with pytest.raises(SectionNotFoundError):
            populated_manager.update_student("alice1", section_id="NonExistent")


class TestGetStudentsBySection:
    def test_get_students_by_section_valid(self, populated_manager):
        """Test retrieving students from a valid section."""
        students = populated_manager.get_students_by_section("B")

        assert len(students) == 1
        assert students[0].name == "Charlie"

    def test_get_students_by_section_multiple(self, populated_manager):
        """Test retrieving multiple students from a section."""
        students = populated_manager.get_students_by_section("A")

        assert len(students) == 2
        names = {s.name for s in students}
        assert names == {"Alice", "Bob"}

    def test_get_students_by_section_empty(self, manager):
        """Test retrieving students from an empty section."""
        manager.add_section("empty", "Empty Section")
        students = manager.get_students_by_section("empty")

        assert students == []

    def test_get_students_by_section_non_existent_raises(self, manager):
        """Test retrieving from non-existent section raises error."""
        with pytest.raises(SectionNotFoundError):
            manager.get_students_by_section("nonexistent")


class TestImportRosterFromCSV:
    def test_import_roster_success(self, manager):
        """Test importing students from CSV."""
        csv_data = """section_id,section_name,student_id,student_name
sec1,Math 101,s1,Alice
sec1,Math 101,s2,Bob
sec2,English 101,s3,Charlie"""

        stats = manager.import_roster_from_csv(csv_data)

        assert stats["students_added"] == 3
        assert stats["sections_seen"] == 2

        math_students = manager.get_students_by_section("sec1")
        assert len(math_students) == 2

    def test_import_roster_skips_duplicates(self, manager):
        """Test that duplicate student IDs are skipped during import."""
        csv_data = """section_id,section_name,student_id,student_name
sec1,Math 101,s1,Alice
sec1,Math 101,s1,Alice Duplicate"""

        stats = manager.import_roster_from_csv(csv_data)

        assert stats["students_added"] == 1

    def test_import_roster_missing_columns_raises(self, manager):
        """Test that CSV with missing columns raises error."""
        csv_data = """section_id,student_name
sec1,Alice"""

        with pytest.raises(ValueError):
            manager.import_roster_from_csv(csv_data)
