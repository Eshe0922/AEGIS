import airbyte as ab

def test_check_with_api_key():
    try:
        source = ab.get_source('source-mailchimp')
        config = {
            "credentials": {
                "auth_type": "apikey",
                "apikey": "dummy_apikey_value"
            }
        }

        source.set_config(config=config)
        source.check()
    except Exception as e:
        log_file_path = '/tmp/airbyte/logs/source-mailchimp/source-mailchimp-log-JFFM0FJTC.log'
        with open(log_file_path, 'r') as log_file:
            log_content = log_file.read()
            print("Log content:\n", log_content)
            if "'AirbyteMessage' object has no attribute 'json'" in log_content:
                raise AssertionError(f"Test failed as expected with error: {e}")
            else:
                raise e

try:
    test_check_with_api_key()
except AssertionError as e:
    raise AssertionError("Test failed as expected with error:", e)
else:
    print("Test passed successfully with no errors!")
import airbyte as ab

def test_check_with_api_key():
    try:
        source = ab.get_source('source-mailchimp')
        config = {
            "credentials": {
                "auth_type": "apikey",
                "apikey": "dummy_apikey_value"
            }
        }

        source.set_config(config=config)
        source.check()
    except Exception as e:
        log_file_path = '/tmp/airbyte/logs/source-mailchimp/source-mailchimp-log-JFFM0FJTC.log'
        with open(log_file_path, 'r') as log_file:
            log_content = log_file.read()
            if "'AirbyteMessage' object has no attribute 'json'" in log_content:
                raise AssertionError(f"Test failed as expected with error: {e}")
            else:
                print(log_content)
                raise e

try:
    test_check_with_api_key()
except AssertionError as e:
    raise AssertionError("Test failed as expected with error:", e)
else:
    print("Test passed successfully with no errors!")