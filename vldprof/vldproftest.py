import unittest
import vldprof


class vldTest(unittest.TestCase):
    def test_regex(self):
        head_string = "---------- Block 3 at 0x0115EDB8: 28 bytes ----------"
        self.assertIsNotNone(vldprof.block_head_regex.match(head_string), "匹配block头错误")

        crt_alloc_string = "  CRT Alloc ID: 195"
        self.assertIsNotNone(vldprof.crt_alloc_id_regex.match(crt_alloc_string), "匹配crt alloc错误")

        leak_hash_string = "  Leak Hash: 0x2BA42105, Count: 1, Total 28 bytes"
        leak_hash = vldprof.leak_hash_regex.match(leak_hash_string)
        self.assertIsNotNone(leak_hash, "匹配leak hash错误")
        self.assertEqual(leak_hash.groupdict().get("hash"), "0x2BA42105")
        self.assertEqual(leak_hash.groupdict().get("total"), '28')

        call_stack_string = "  Call Stack (TID 7788):"
        self.assertIsNotNone(vldprof.call_stack_regex.match(call_stack_string), "匹配call stack string错误")

    def test_file(self):
        vldprof.prof("./memory_leak_report.txt")

if __name__ == '__main__':
    unittest.main()
