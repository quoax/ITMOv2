import unittest
from service import subscribe, subscribers, unsubscribe, is_subscribed


class SubscribeTest(unittest.TestCase):
    def setUp(self):
        subscribers.clear()

    def test_subscribe(self):
        self.assertEqual(subscribe("Ann"), {"subscribed": True})
        self.assertEqual(subscribers, {"Ann"})

    def test_empty(self):
        with self.assertRaises(ValueError):
            subscribe(" ")

    def test_duplicate(self):
        subscribe("Ann")
        subscribe("Ann")
        self.assertEqual(len(subscribers), 1)

    def test_unsubscribe_existing(self):
        subscribe("Ann")
        self.assertTrue(is_subscribed("Ann"))
        self.assertEqual(unsubscribe("Ann"), {"unsubscribed": True})
        self.assertFalse(is_subscribed("Ann"))

    def test_unsubscribe_nonexistent(self):
        self.assertEqual(unsubscribe("Bob"), {"unsubscribed": False})

    def test_normalization(self):
        subscribe(" Ann ")
        self.assertTrue(is_subscribed("Ann"))


if __name__ == "__main__":
    unittest.main()
