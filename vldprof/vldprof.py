import re

# 不同版本的VLD报告不一样，所以会有不同版本的正则表达式
block_head_regex = re.compile(r"-+ Block \d+ at 0x(\d|\w)+: (?P<bytes>\d+) bytes -+")
crt_alloc_id_regex = re.compile(r"\s+CRT Alloc ID: \d+")
leak_hash_regex = re.compile(r"\s+Leak Hash: (?P<hash>0x(\d|\w)+), Count: (?P<count>\d+)(, Total (?P<total>\d+) bytes)?")
call_stack_regex = re.compile(r"\s+Call Stack \(TID \d+\):")

leak_hash_regex_v2 = re.compile(r"\s*Leak Hash: (?P<hash>0x(\d|\w)+) "
                                r"Count: (?P<count>\d+)")

blocks = list()     ## 整个文件的块信息


class BlockInfo:
    """
    块内存的信息
    """
    def __init__(self):
        self.count = 0
        self.hash = 0
        self.bytes = 0
        self.message = ""

    def total_size(self):
        return self.bytes * self.count


def prof(file_full_path, max_report = 20):
    """
    分析vld的报告文件，不包含数据类型
    :param file_name: 文件路径
    :return: None
    """
    with open(file_full_path, "r") as vld_file:
        for line in vld_file:
            match = block_head_regex.match(line)
            if match is None:
                continue

            block_info = BlockInfo()
            block_info.bytes = int(match.groupdict().get("bytes"))
            block_info.message += line
            # 开始解析
            """
            crt_alloc_id_line = vld_file.readline()
            crt_alloc_id_match = crt_alloc_id_regex.match(crt_alloc_id_line)
            assert crt_alloc_id_match is not None
            """

            leak_hash_line = vld_file.readline()
            leak_hash_match = leak_hash_regex_v2.match(leak_hash_line)
            assert leak_hash_match is not None
            block_info.hash = leak_hash_match.groupdict().get("hash")
            block_info.count = int(leak_hash_match.groupdict().get("count"))
            block_info.message += leak_hash_line

            for stack in vld_file:
                if stack == "\n" or stack == "\r\n":
                    break
                block_info.message += stack

            blocks.append(block_info)

    print("-------------------------TOP MEMORY------------------------------")
    sorted_blocks = sorted(blocks, key=lambda block: block.total_size())

    top_size = 0
    for block in sorted_blocks[-1:-max_report:-1]:
        print(block.hash + ' ---> ' + str(block.total_size()/1024/1024) + "M" + " ---> count: " + str(block.count))
        print(block.message)
        top_size += block.total_size()

    print("top " + str(max_report) + " size --> " + str(top_size/1024/1024) + " M")
    all_size = sum([block.total_size() for block in sorted_blocks])
    print("all size --> " + str(all_size/1024/1024) + " M")

    print("------------------------TOP COUNT------------------------------------")
    sorted_blocks = sorted(blocks, key=lambda block: block.count)
    for block in sorted_blocks[-1:-max_report:-1]:
        print(block.hash + ' ---> ' + str(block.total_size()/1024/1024) + "M" + " ---> count: " + str(block.count))
        print(block.message)

if __name__ == "__main__":
    prof("./memory_leak_report.txt")