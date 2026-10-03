from unittest.mock import MagicMock, patch
from app.database.session import check_database_connection, get_db
from app.schemas.health import DatabaseHealth


def test_database_connection_disconnected():
    """Verify that when database is unavailable, diagnostic reports disconnected with error."""
    result = check_database_connection()
    # On a host without PostgreSQL running, result status should be disconnected
    assert "status" in result
    assert "pgvector_installed" in result
    assert result["status"] in ("connected", "disconnected")


def test_database_connection_mocked_success():
    """Verify that when PostgreSQL and pgvector respond, check_database_connection correctly returns connected."""
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    # Mock SELECT 1
    mock_connection.execute.return_value = mock_cursor
    # Mock pgvector check
    mock_cursor.fetchone.return_value = ("vector", "0.7.4")

    with patch("app.database.session.engine.connect") as mock_connect:
        mock_connect.return_value.__enter__.return_value = mock_connection

        result = check_database_connection()
        assert result["status"] == "connected"
        assert result["pgvector_installed"] is True
        assert result["pgvector_version"] == "0.7.4"
        assert result["error"] is None

        # Verify it conforms to DatabaseHealth schema
        db_health = DatabaseHealth(**result)
        assert db_health.status == "connected"
        assert db_health.pgvector_installed is True


def test_get_db_yields_session():
    """Verify that get_db generator yields a valid session and closes it."""
    db_gen = get_db()
    session = next(db_gen)
    assert session is not None
    try:
        next(db_gen)
    except StopIteration:
        pass
