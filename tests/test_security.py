import os
import tempfile
import unittest

from tools.system import SystemTools


class SystemToolsSecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tools = SystemTools(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_commands_are_disabled_by_default(self):
        self.assertIn("desativados", self.tools.bash("pwd"))

    def test_workspace_write_and_read(self):
        self.assertIn("Salvo", self.tools.write("notes/ok.txt", "seguro"))
        self.assertEqual(self.tools.read("notes/ok.txt"), "seguro")

    def test_workspace_cannot_escape(self):
        self.assertIn("Erro", self.tools.write("../../outside.txt", "não"))
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(self.tmp.name), "outside.txt")))

    def test_allowlist_blocks_other_commands(self):
        tools = SystemTools(self.tmp.name, allow_commands=True, allowed_commands={"pwd"})
        self.assertIn("bloqueado", tools.bash("uname -a"))


if __name__ == "__main__":
    unittest.main()
