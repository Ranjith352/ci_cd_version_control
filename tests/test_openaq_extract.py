import unittest
from etl.extraction.openaq_extract import OpenAQExtractor

class TestOpenAQExtract(unittest.TestCase):
    def test_openaq_extractor_initialization_with_key(self):
        extractor = OpenAQExtractor(api_key="test_key_12345")
        self.assertEqual(extractor.api_key, "test_key_12345")
        self.assertEqual(extractor.headers.get("X-API-Key"), "test_key_12345")

    def test_openaq_extractor_missing_key_raises_error(self):
        with self.assertRaises(ValueError):
            OpenAQExtractor(api_key="")

if __name__ == "__main__":
    unittest.main()
