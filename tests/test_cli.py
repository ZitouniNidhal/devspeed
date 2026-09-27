import os
import tempfile
import unittest
from pathlib import Path
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from devspeed import cli
from devspeed import config


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
        for stack_name in (
            "node-postgres-redis",
            "fastapi-postgres",
            "django-postgres",
            "flask-postgres",
        ):
            with self.subTest(stack=stack_name):
                stack = cli.get_stack(stack_name)
                config = stack.default_config("test-project")
                self.assertIn("services:", stack.compose_yaml(config))
                self.assertTrue(stack.starter_files(config))

    def test_init_dry_run_does_not_write_files(self):
        with tempfile.TemporaryDirectory() as directory:
            original_directory = Path.cwd()
            os.chdir(directory)
            try:
                cli._create_config("flask-postgres", "dry-run", dry_run=True)
            finally:
                os.chdir(original_directory)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_up_generates_files_and_runs_mocked_docker(self):
        with tempfile.TemporaryDirectory() as directory:
            original_directory = Path.cwd()
            os.chdir(directory)
            try:
                config.save_config(cli.get_stack("fastapi-postgres").default_config("demo"))
                completed = type("Completed", (), {"returncode": 0})()
                with patch("devspeed.cli.shutil.which", return_value="docker"), patch(
                    "devspeed.cli.subprocess.run", return_value=completed
                ) as run:
                    cli.cmd_up(Namespace(dry_run=False))
                self.assertEqual(run.call_args.args[0][-2:], ["up", "-d"])
                self.assertTrue(Path(cli.GENERATED_COMPOSE).exists())
                self.assertTrue(Path(cli.GENERATED_ENV_EXAMPLE).exists())
                self.assertIn("<password>", Path(cli.GENERATED_ENV_EXAMPLE).read_text())
            finally:
                os.chdir(original_directory)

    def test_docker_commands_are_mocked_and_forwarded(self):
        with tempfile.TemporaryDirectory() as directory:
            original_directory = Path.cwd()
            os.chdir(directory)
            try:
                Path(cli.GENERATED_COMPOSE).write_text("services: {}\n")
                completed = type("Completed", (), {"returncode": 0})()
                with patch("devspeed.cli.shutil.which", return_value="docker"), patch(
                    "devspeed.cli.subprocess.run", return_value=completed
                ) as run:
                    with self.assertRaises(SystemExit) as down_exit:
                        cli.cmd_down(Namespace())
                    with self.assertRaises(SystemExit) as status_exit:
                        cli.cmd_status(Namespace())
                    with self.assertRaises(SystemExit) as logs_exit:
                        cli.cmd_logs(Namespace(follow=True, service="app"))
                self.assertEqual(down_exit.exception.code, 0)
                self.assertEqual(status_exit.exception.code, 0)
                self.assertEqual(logs_exit.exception.code, 0)
                self.assertEqual(run.call_count, 3)
                self.assertEqual(run.call_args.args[0][-2:], ["--follow", "app"])
            finally:
                os.chdir(original_directory)

    def test_missing_docker_message_is_actionable(self):
        with patch("devspeed.cli.shutil.which", return_value=None), self.assertRaises(SystemExit):
            output = StringIO()
            with redirect_stdout(output):
                cli._require_docker()
        self.assertIn("docker.com/products/docker-desktop", output.getvalue())

    def test_invalid_yaml_exits_with_friendly_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / config.CONFIG_FILENAME
            path.write_text("services: [not: valid")
            with self.assertRaises(SystemExit):
                config.load_config(Path(directory))

    def test_list_and_parser_include_dry_run(self):
        output = StringIO()
        with redirect_stdout(output):
            cli.cmd_list(Namespace())
        self.assertIn("flask-postgres", output.getvalue())
        args = cli.build_parser().parse_args(["up", "--dry-run"])
        self.assertTrue(args.dry_run)


if __name__ == "__main__":
    unittest.main()
