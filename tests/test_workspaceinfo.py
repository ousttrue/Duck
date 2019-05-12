import unittest
import pathlib
from workspacefolder.lsp import workspaceinfo


class RpcTest(unittest.TestCase):
    def test_py_root(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        samples = root / 'samples'

        py_single = samples / 'python_single'
        self.assertEqual(
            root / 'setup.py',
            workspaceinfo.find_to_ancestors(py_single / 'sample.py',
                                            'setup.py'))

    def test_cs_root(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        samples = root / 'samples'

        dotnet = samples / 'dotnetcore'
        self.assertEqual(
            dotnet / 'dotnetcore.csproj',
            workspaceinfo.find_to_ancestors(dotnet / 'Program.cs', '*.csproj'))


if __name__ == '__main__':
    unittest.main()
