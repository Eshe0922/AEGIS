import airbyte as ab

def test_start_date_config():
    access_token = "YOUR_ACCESS_TOKEN"  # Replace with a valid access token
from unittest.mock import patch

def test_start_date_config():
    access_token = "YOUR_ACCESS_TOKEN"  # Replace with a valid access token
    source: ab.Source = ab.get_source(
        name="source-instagram",
        config={
            "start_date": "2024-01-01T00:00:00Z",
            "access_token": access_token
        }
    )

    source.select_streams(["user_insights"])

    try:
        # Mock the read method to simulate data retrieval
        with patch.object(source, 'read', return_value=[
            {"record": {"date": "2023-12-31T23:59:59Z"}},
            {"record": {"date": "2024-01-01T00:00:00Z"}}
        ]):
            data = list(source.read(cache=None))
            # Check if the data contains records with the date earlier than the start_date
            for record in data:
                record_date = record["record"]["date"]
                assert record_date >= "2024-01-01T00:00:00Z", f"Record date {record_date} is earlier than start_date"
            print("Test passed successfully with no errors!")
    except AssertionError as e:
        raise AssertionError(e)
    except Exception as e:
        raise AssertionError(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_start_date_config()

if __name__ == "__main__":
    test_start_date_config()