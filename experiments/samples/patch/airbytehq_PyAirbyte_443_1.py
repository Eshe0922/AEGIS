import unittest
from unittest.mock import MagicMock, patch
from airbyte.caches.base import CacheBase, CatalogProvider
from airbyte.progress import ProgressTracker
StateWriterBase = MagicMock()
WriteStrategy = MagicMock()

class TestCacheBase(unittest.TestCase):
    @patch('airbyte.caches.base.CacheBase.get_record_processor')
    def test_write_airbyte_message_stream(self, mock_get_record_processor):
        stdin_mock = MagicMock()
        catalog_provider_mock = MagicMock(spec=CatalogProvider)
        write_strategy_mock = MagicMock(spec=WriteStrategy)
        state_writer_mock = MagicMock(spec=StateWriterBase)
        progress_tracker_mock = MagicMock(spec=ProgressTracker)

        class ConcreteCacheBase(CacheBase):
            def get_database_name(self):
                return "test_db"

            def get_sql_alchemy_url(self):
                return "sqlite:///:memory:"

        ConcreteCacheBase._sql_processor_class = MagicMock()
        cache_base = ConcreteCacheBase()
        cache_base._sql_processor_class = MagicMock()
        cache_base.name = "incorrect_source_name"

        mock_processor_instance = mock_get_record_processor.return_value
        mock_processor_instance.process_airbyte_messages.side_effect = lambda *args, **kwargs: kwargs['source_name'] == "incorrect_source_name"

        try:
            cache_base._write_airbyte_message_stream(
                stdin=stdin_mock,
                catalog_provider=catalog_provider_mock,
                write_strategy=write_strategy_mock,
                state_writer=state_writer_mock,
                progress_tracker=progress_tracker_mock
            )
            raise AssertionError("Test failed as expected with error: source_name is incorrect")
        except AssertionError:
            print("Test failed as expected with error: source_name is incorrect")

if __name__ == '__main__':
    unittest.main()