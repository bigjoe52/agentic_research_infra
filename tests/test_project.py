import unittest

from {{PACKAGE_NAME}}.project import project_identity


class ProjectIdentityTests(unittest.TestCase):
    def test_identity_is_explicitly_exploratory(self) -> None:
        self.assertEqual(project_identity(), "{{PROJECT_NAME}}: lightweight_exploration")


if __name__ == "__main__":
    unittest.main()

