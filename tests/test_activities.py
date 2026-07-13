"""
Tests for Mergington High School Activities API
Tests follow the AAA (Arrange-Act-Assert) pattern for clarity
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client with a fresh app instance"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    from src import app as app_module
    app_module.activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    yield


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all available activities"""
        # Arrange - No additional setup needed, activities already initialized

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 3
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities

    def test_get_activities_includes_activity_details(self, client, reset_activities):
        """Test that activities include required fields"""
        # Arrange - No additional setup needed

        # Act
        response = client.get("/activities")
        activities = response.json()
        chess = activities["Chess Club"]

        # Assert
        assert "description" in chess
        assert "schedule" in chess
        assert "max_participants" in chess
        assert "participants" in chess
        assert chess["max_participants"] == 12
        assert len(chess["participants"]) == 2

    def test_get_activities_participants_list(self, client, reset_activities):
        """Test that participants are correctly listed"""
        # Arrange - No additional setup needed

        # Act
        response = client.get("/activities")
        activities = response.json()
        chess_participants = activities["Chess Club"]["participants"]

        # Assert
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_successful_signup(self, client, reset_activities):
        """Test successful signup for an activity"""
        # Arrange
        email = "alice@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert email in data["message"]
        assert activity in data["message"]

    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity"""
        # Arrange
        email = "alice@mergington.edu"
        activity = "Chess Club"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])

        # Act
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        response = client.get("/activities")
        activities = response.json()
        chess_participants = activities[activity]["participants"]

        assert email in chess_participants
        assert len(chess_participants) == initial_count + 1

    def test_signup_duplicate_email_returns_error(self, client, reset_activities):
        """Test that duplicate signup returns 400 error"""
        # Arrange
        email = "michael@mergington.edu"  # Already registered in Chess Club
        activity = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that signup to non-existent activity returns 404"""
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_with_different_activities(self, client, reset_activities):
        """Test that student can sign up for multiple activities"""
        # Arrange
        student_email = "alice@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"

        # Act - Sign up for first activity
        response1 = client.post(
            f"/activities/{activity1}/signup",
            params={"email": student_email}
        )
        # Act - Sign up for second activity
        response2 = client.post(
            f"/activities/{activity2}/signup",
            params={"email": student_email}
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200

        response = client.get("/activities")
        activities = response.json()
        assert student_email in activities[activity1]["participants"]
        assert student_email in activities[activity2]["participants"]


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_successful_unregister(self, client, reset_activities):
        """Test successful unregister from an activity"""
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])

        # Act
        client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )

        # Assert
        response = client.get("/activities")
        activities = response.json()
        chess_participants = activities[activity]["participants"]

        assert email not in chess_participants
        assert len(chess_participants) == initial_count - 1

    def test_unregister_student_not_registered_returns_404(self, client, reset_activities):
        """Test that unregistering non-registered student returns 404"""
        # Arrange
        email = "notregistered@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that unregister from non-existent activity returns 404"""
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"

        # Act
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_then_can_signup_again(self, client, reset_activities):
        """Test that student can sign up again after unregistering"""
        # Arrange
        email = "alice@mergington.edu"
        activity = "Chess Club"

        # Act - Sign up
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Act - Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )

        # Act - Sign up again
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert unregister_response.status_code == 200
        assert signup_response.status_code == 200

        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root path redirects to static index"""
        # Arrange - No setup needed

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_signup_unregister_signup_workflow(self, client, reset_activities):
        """Test complete signup -> unregister -> signup workflow"""
        # Arrange
        email = "integration@mergington.edu"
        activity = "Chess Club"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])

        # Act - Initial signup
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert - Signup succeeded
        assert signup_response.status_code == 200
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count + 1

        # Act - Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )

        # Assert - Unregister succeeded
        assert unregister_response.status_code == 200
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count

        # Act - Sign up again
        signup_response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert - Final state
        assert signup_response2.status_code == 200
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count + 1
        assert email in response.json()[activity]["participants"]
