"""Executable evidence for the documented frozen-oracle limitation."""
from pathlib import Path
import unittest

from lab.check import run_examples


class ExceptionInterpretationTests(unittest.TestCase):
    def test_value_error_contract_also_accepts_unicode_decode_error(self):
        source=Path(__file__).resolve().parents[1]/'evidence/artifacts/initial/safe-path/solution.py'
        row=run_examples(source,[{'input':{'path':'%ff'},'error':'ValueError'}])[0]
        self.assertFalse(row['passed'])
        namespace={}
        exec(compile(source.read_text(),str(source),'exec'),namespace)
        with self.assertRaises(ValueError):
            namespace['solve']({'path':'%ff'})
        self.assertTrue(issubclass(UnicodeDecodeError,ValueError))


if __name__=='__main__':unittest.main()
