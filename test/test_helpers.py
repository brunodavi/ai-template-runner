from unittest import TestCase

from test.helpers import get_root

class TestHelpers(TestCase):
    def test_get_root(self):
        self.assertEqual(get_root().name, 'ai-template-runner')

