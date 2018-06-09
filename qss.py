import re
import os.path
import logging


class ErrorReport:
    """
    错误报告
    """

    def __init__(self,
                 line=None,
                 message=None,
                 file_full_path=None,
                 error_context=None):

        self.line = line
        self.message = message
        self.file_full_path = file_full_path
        self.error_context = error_context

    def __str__(self):
        if self.error_context is not None:
            return "%s(%d): < %s >======%s" % (self.file_full_path, self.line, self.error_context, self.message)
        else:
            return "%s(%d): %s" % (self.file_full_path, self.line, self.message)


def match_delete_stat(parser_string, start_pos):
    """
    从start_pos开始检测,是否符合delete语句的语法，如果符合，则返回整个delete语句的作用域(指的是{}这个里面，或者if语句的下一句)
    :param parser_string: 需要解析的语句
    :param start_pos: 开始的位置,
    :return: stat_start, stat_end, 如果没有匹配，则都返回-1
    """
    match = delete_stat_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1

    return match.start(), match.end() - 1


def next_token_pos_not_space(parser_string, start_pos):
    """
    找到下一个非空格的字符串起始位置
    :param parser_string:
    :param start_pos:
    :return: 下一个的起始位置
    """
    for i in range(start_pos, len(parser_string)):
        if not parser_string[i].isspace():
            return i
    return -1


def next_token_pos_pair(parser_string, start_pos, findpair_string):
    """
    找到下一个非注释的字符串起始位置
    :param parser_string:
    :param start_pos:
    :param findpair_string:需要找到的匹配字符串
    :return: 下一个的起始位置
    """
    mark_end_regex = None
    mark_start_regex =  findpair_string
    if findpair_string == "/*":
        mark_end_regex = "\*/"
    elif findpair_string == "{":
        mark_end_regex = "}"

    if mark_start_regex is None:
        return  start_pos

    while 1:
        start_pos = next_token_pos_not_space(parser_string, start_pos)
        search_pos = parser_string.find(mark_start_regex, start_pos)
        if search_pos == -1:
            return start_pos
        mark_start_pos = search_pos
        if start_pos < mark_start_pos:
            return start_pos
        search_pos = parser_string.find(mark_end_regex, search_pos)  # 找到注释的结束点

        if search_pos == -1:
            return  -1
        mark_end_pos = search_pos
        while 1:
            search = parser_string.find(mark_start_regex, mark_start_pos) #找到注释点的第二个开始点
            mark_start_pos2 = search
            if (mark_start_pos2 is not range(mark_start_pos, mark_end_pos)):
                start_pos = mark_end_pos+len(mark_end_regex)
                break
            mark_end_pos =   parser_string.find(mark_end_regex, mark_end_pos)  # 找到注释的结束点
            mark_start_pos = mark_start_pos2 + len(mark_end_regex)

    return -1


def next_line_break_pos(parser_string, start_pos):
    """
    从start_pos开始找到下一个换行符的位置
    :param parser_string:
    :param start_pos:
    :return: 如果有找到则返回位置，没有则返回字符串结束的位置
    """

    line_break_regex = re.compile("\n")
    search = line_break_regex.search(parser_string, start_pos)
    if search is None:
        return len(parser_string)

    return search.start()


# !匹配规则
def match_and_check(parser_string, fileName):
    error_message = list()
    parser_len = len(parser_string)
    start_pos = 0
    regex_name = fileName[0:(len(fileName) - 4)] #和文件名比较
    class_name_regex = re.compile(regex_name)
    while 1:
        start_pos = next_token_pos_not_space(parser_string, start_pos)
        if start_pos == -1:
            break
        start_pos = next_token_pos_pair(parser_string, start_pos, "/*") #找到非注释起始位置
        if start_pos == -1:
            break

        message_end = next_line_break_pos(parser_string, start_pos)
        current_line = parser_string.count("\n", 0, start_pos) + 1  # 检查的行数
        match = class_name_regex.match(parser_string, start_pos)
        if match is None:  # 未找到类名
            line_data = parser_string[start_pos:message_end]
            error_message.append(ErrorReport(line=current_line, message=r"未用类名", error_context=line_data))

        qss_body_start = parser_string.find("{", start_pos, parser_len)
        qss_body_end = next_token_pos_pair(parser_string, qss_body_start, "{")
        current_line = parser_string.count("\n", 0, qss_body_start) + 1  # 检查的行数
        if qss_body_end == -1:
            return error_message

        start_pos = qss_body_end
        if (start_pos >= len(parser_string)):
            return error_message

    return error_message


def read_file_data(file_path):
    """
    读取文件解析出来的语句, 将会去除多余的文件
    :param file_path: 文件的路径
    :return:
    """
    with open(file_path, mode="r") as fp:
        fp.seek(0, 2)
        length = fp.tell()
        fp.seek(0, 0)
        data = fp.read(length)
    return data


# !检查.qss文件
def check_file(file_path):
    """
    解析文件的规则
    :param file_path: 文件路径
    :return: rule 有检测出错误,返回检测出的结果
             None 没有检测出错误
    """
    try:
        data = read_file_data(file_path)
        file_name = os.path.basename(file_path)
        error_message = match_and_check(data, file_name)

        for rule in error_message:
            rule.file_full_path = os.path.abspath(file_path)

        return error_message
    except UnicodeDecodeError:
        logging.error(file_path + "编码错误，请查看是否GB2312编码")
    finally:
        pass

    return None


# !遍历目录
def check_dir(dir_path):
    """
    检测目录下的所有.h和.cpp文件的规则
    :param dir_path:
    :return:
    """
    import os
    error_message = list()
    for root, dirs, files in os.walk(dir_path):
        for file in files:  # 检查文件
            if file.endswith(".qss"):
                try:
                    check_rule = check_file(root + '/' + file)
                    if check_rule:
                        error_message.extend(check_rule)
                except UnicodeDecodeError as e:
                    logging.error("解析" + file + "文件编码错误:" + str(e))
                except AssertionError as e:
                    logging.error("解析" + file + "文件有断言")

    return error_message


if __name__ == "__main__":
    import sys
    import getopt

    print(sys.argv[1:])
    opts, args = getopt.getopt(sys.argv[1:], "hf:d:")
    logging.basicConfig(level=logging.DEBUG,
                        format="[line:%(lineno)d] %(levelname)s %(message)s")
    check_result = None

    for opt, value in opts:
        if opt == "-f":
            check_result = check_dir(value)
        elif opt == "-d":
            check_result = check_file(value)
        else:
            continue

    for result in check_result:
        print(result)

    print("总共发现:" + str(len(check_result)))
