import pytest
from src.classroom_tools import ClassroomTools
from src.student_manager import StudentManager


@pytest.fixture
def student_manager():
    """Create a StudentManager with test data."""
    manager = StudentManager()
    manager.add_section("sec1", "Section 1")
    manager.add_student("Alice", "sec1", "s1")
    manager.add_student("Bob", "sec1", "s2")
    manager.add_student("Charlie", "sec1", "s3")
    return manager


@pytest.fixture
def classroom_tools(student_manager):
    """Create a ClassroomTools instance with the test StudentManager."""
    return ClassroomTools(student_manager)


class TestSpinWheel:
    def test_spin_wheel_returns_student_from_section(self, classroom_tools):
        """Test that spin_wheel returns a student dict from the section."""
        result = classroom_tools.spin_wheel("sec1")

        assert result is not None
        assert "id" in result
        assert "name" in result
        assert "section_id" in result
        assert result["id"] in ["s1", "s2", "s3"]
        assert result["name"] in ["Alice", "Bob", "Charlie"]
        assert result["section_id"] == "sec1"

    def test_spin_wheel_single_student(self):
        """Test spin_wheel with a section containing one student."""
        manager = StudentManager()
        manager.add_section("solo", "Solo Section")
        manager.add_student("Lonely", "solo", "lone1")
        tools = ClassroomTools(manager)

        result = tools.spin_wheel("solo")

        assert result is not None
        assert result["name"] == "Lonely"
        assert result["id"] == "lone1"

    def test_spin_wheel_empty_section(self):
        """Test spin_wheel with an empty section returns None."""
        manager = StudentManager()
        manager.add_section("empty", "Empty Section")
        tools = ClassroomTools(manager)

        result = tools.spin_wheel("empty")

        assert result is None

    def test_spin_wheel_nonexistent_section(self, classroom_tools):
        """Test spin_wheel with a non-existent section returns None."""
        result = classroom_tools.spin_wheel("nonexistent")

        assert result is None


class TestCreateGroups:
    def test_create_groups_even_distribution(self):
        """Test creating groups where students divide evenly."""
        manager = StudentManager()
        manager.add_section("sec", "Test Section")
        for i, name in enumerate(["A", "B", "C", "D", "E", "F"]):
            manager.add_student(name, "sec", f"id{i}")
        tools = ClassroomTools(manager)

        groups = tools.create_groups("sec", group_size=2)

        assert len(groups) == 3
        for group in groups:
            assert len(group) == 2

        # Verify all students are present
        all_ids = [s["id"] for group in groups for s in group]
        assert set(all_ids) == {f"id{i}" for i in range(6)}

    def test_create_groups_uneven_distribution(self):
        """Test creating groups where there is a remainder."""
        manager = StudentManager()
        manager.add_section("sec", "Test Section")
        for i, name in enumerate(["A", "B", "C", "D", "E"]):
            manager.add_student(name, "sec", f"id{i}")
        tools = ClassroomTools(manager)

        groups = tools.create_groups("sec", group_size=2)

        assert len(groups) == 3  # [2, 2, 1]
        lengths = sorted([len(g) for g in groups])
        assert lengths == [1, 2, 2]

    def test_create_groups_size_larger_than_list(self):
        """Test creating a group size larger than the student list."""
        manager = StudentManager()
        manager.add_section("sec", "Test Section")
        manager.add_student("A", "sec", "id1")
        manager.add_student("B", "sec", "id2")
        tools = ClassroomTools(manager)

        groups = tools.create_groups("sec", group_size=5)

        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_create_groups_empty_section(self):
        """Test creating groups from an empty section."""
        manager = StudentManager()
        manager.add_section("empty", "Empty Section")
        tools = ClassroomTools(manager)

        groups = tools.create_groups("empty", group_size=3)

        assert groups == []

    def test_create_groups_invalid_size_zero(self, classroom_tools):
        """Test creating groups with size 0 raises ValueError."""
        with pytest.raises(ValueError):
            classroom_tools.create_groups("sec1", group_size=0)

    def test_create_groups_invalid_size_negative(self, classroom_tools):
        """Test creating groups with negative size raises ValueError."""
        with pytest.raises(ValueError):
            classroom_tools.create_groups("sec1", group_size=-1)

    def test_create_groups_nonexistent_section(self, classroom_tools):
        """Test creating groups from a non-existent section returns empty list."""
        groups = classroom_tools.create_groups("nonexistent", group_size=2)

        assert groups == []

    def test_create_groups_as_pairs(self):
        """Test creating pairs (group_size=2) with even number of students."""
        manager = StudentManager()
        manager.add_section("sec", "Test Section")
        for i, name in enumerate(["A", "B", "C", "D"]):
            manager.add_student(name, "sec", f"id{i}")
        tools = ClassroomTools(manager)

        pairs = tools.create_groups("sec", group_size=2)

        assert len(pairs) == 2
        for pair in pairs:
            assert len(pair) == 2

    def test_create_groups_as_pairs_odd(self):
        """Test creating pairs with odd number of students."""
        manager = StudentManager()
        manager.add_section("sec", "Test Section")
        for i, name in enumerate(["A", "B", "C"]):
            manager.add_student(name, "sec", f"id{i}")
        tools = ClassroomTools(manager)

        pairs = tools.create_groups("sec", group_size=2)

        assert len(pairs) == 2
        lengths = sorted([len(p) for p in pairs])
        assert lengths == [1, 2]
