from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


ACTIVITY_NAME = "Chess Club"
EXISTING_PARTICIPANT = "michael@mergington.edu"


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app, follow_redirects=False) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_root_redirects_to_index(client):
    # Arrange
    path = "/"

    # Act
    response = client.get(path)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    # Arrange
    path = "/activities"

    # Act
    response = client.get(path)

    # Assert
    assert response.status_code == 200
    assert ACTIVITY_NAME in response.json()
    assert EXISTING_PARTICIPANT in response.json()[ACTIVITY_NAME]["participants"]


def test_signup_adds_participant(client):
    # Arrange
    email = "new.student@mergington.edu"
    path = f"/activities/{ACTIVITY_NAME}/signup"

    # Act
    response = client.post(path, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {ACTIVITY_NAME}"}
    assert email in activities[ACTIVITY_NAME]["participants"]


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    unknown_activity = "Unknown Club"
    path = f"/activities/{unknown_activity}/signup"

    # Act
    response = client.post(
        path,
        params={"email": "new.student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    path = f"/activities/{ACTIVITY_NAME}/signup"

    # Act
    response = client.post(
        path,
        params={"email": EXISTING_PARTICIPANT},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }


def test_unregister_removes_participant(client):
    # Arrange
    path = f"/activities/{ACTIVITY_NAME}/signup"

    # Act
    response = client.delete(
        path,
        params={"email": EXISTING_PARTICIPANT},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {EXISTING_PARTICIPANT} from {ACTIVITY_NAME}"
    }
    assert EXISTING_PARTICIPANT not in activities[ACTIVITY_NAME]["participants"]


def test_unregister_returns_not_found_for_unknown_activity(client):
    # Arrange
    unknown_activity = "Unknown Club"
    path = f"/activities/{unknown_activity}/signup"

    # Act
    response = client.delete(
        path,
        params={"email": EXISTING_PARTICIPANT},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_not_found_for_unregistered_participant(client):
    # Arrange
    unregistered_email = "not.signed.up@mergington.edu"
    path = f"/activities/{ACTIVITY_NAME}/signup"

    # Act
    response = client.delete(
        path,
        params={"email": unregistered_email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
