import os
import tempfile
import unittest
from pathlib import Path

from devspeed import cli


class CliTests(unittest.TestCase):
    def test_init_creates_config_and_starter_files(self):
        with tempfile.TemporaryDirectory() as directory:
            original_directory = Path.cwd()
            os.chdir(directory)
            try:
                cli._create_config("fastapi-postgres", "test-api")
            finally:
                os.chdir(original_directory)

            self.assertTrue((Path(directory) / "devspeed.yaml").exists())
            self.assertTrue((Path(directory) / "main.py").exists())
            self.assertTrue((Path(directory) / "requirements.txt").exists())

    def test_init_does_not_overwrite_existing_starter(self):
        with tempfile.TemporaryDirectory() as directory:
            original_directory = Path.cwd()
            os.chdir(directory)
            try:
                Path("main.py").write_text("# keep this file\n")
                cli._create_config("fastapi-postgres", "test-api")
            finally:
                os.chdir(original_directory)

            self.assertEqual((Path(directory) / "main.py").read_text(), "# keep this file\n")

    def test_all_stacks_render_compose(self):
        for stack_name in ("node-postgres-redis", "fastapi-postgres", "django-postgres"):
            with self.subTest(stack=stack_name):
                stack = cli.get_stack(stack_name)
                config = stack.default_config("test-project")
                self.assertIn("services:", stack.compose_yaml(config))
                self.assertTrue(stack.starter_files(config))


if __name__ == "__main__":
    unittest.main()
