import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from research import score11_five_deletion_suffix as m


class SuffixTests(unittest.TestCase):
    def test_exact_split(self):
        cases=[frozenset([i]) for i in range(8)]
        self.assertEqual(m.suffix(cases,5,8),cases[5:])
        self.assertFalse(set(cases[:5]) & set(m.suffix(cases,5,8)))
        with self.assertRaises(ValueError): m.suffix(cases,9,8)
        with self.assertRaises(ValueError): m.suffix(cases,5,9)
        with self.assertRaises(ValueError): m.suffix(cases[::-1],5,8)
        with self.assertRaises(ValueError): m.suffix(cases[:-1]+cases[-2:-1],5,8)

    def test_pinned_inputs_reject_different_parent(self):
        original=b'{"completed_deletion_sets":33062}'
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'report.json';p.write_bytes(original)
            expected=hashlib.sha256(original).hexdigest()
            self.assertEqual(m.checked_json(p,expected)['completed_deletion_sets'],33062)
            p.write_bytes(b'{"completed_deletion_sets":33061}')
            with self.assertRaises(ValueError): m.checked_json(p,expected)


if __name__=='__main__':
    unittest.main()
