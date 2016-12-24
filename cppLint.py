import re
# 类起始位置的正则表达式
class_regex = re.compile(r"\s*class\s+(\w+\s+)?(?P<class_name>\w+)")
# 函数其实位置的正则表达式
function_regex = re.compile(r"(virtual|static|inline)?\s*(\w+::)?(\w+)(<[\w<>:\d]+>)?\s*[\*,&]*\s*"
                            r"(?P<function_name>\w+)\s*\(")
# 构造函数的正则表达式
construct_regex = re.compile(r"\s*\w+\(")
# 析构函数的正则表达式
destroy_regex = re.compile(r"\s*(virtual)?\s*~\w+\(")
# 变量正则表达式
var_regex = re.compile(r"(?:static)?\s?(?P<type_name>(\w+::)?(\w+))(?P<template><[\w<>:\d]+>)?\s*(\**)\s*"
                       r"(?P<var_name>\w+)")
# 分隔符的正则表达式
token_regex = re.compile(r'(\w+|}|{|::|;|\(|\)|,|\*|<|>|\[|\])')
# 友元函数声明
friend_declare_regex = re.compile("friend\s+.+\(")
# 枚举
enum_regex = re.compile(r"\s*enum[\s{]")
# 多行的注释
mul_line_comment_regex = re.compile(r"/\*(.|\n)*\*/")
# 单行的注释
one_line_comment_regex = re.compile(r"//.+\n?")

# 错误信息

# 类相关规则
CLASS_NAME_MUST_CIT_BEGIN = r"类名称必须以cit开头"
CLASS_NAME_3RD_MUST_UPPER = r"cit后面的字符必须以大写字母开头"
CLASS_INHERIT_COLON_MUST_BE_SPACE = r"类继承的冒号前后必须要有空格"

CLASS_MEMBER_MUST_M_BEGIN = r"类成员变量必须以m_开头"
VAR_TOO_MANY = r"同时定义太多的变量"

FUNCTION_PARAM_MUST_BE_SPACE = r"不同的函数参数之间最少要留一个空格"

LOCAL_VAR_MUST_BE_L_BEGIN = r"局部变量必须以l_开头"


def remove_begin_space_and_newline(parser_string):
    """
    删除开头的换行,tab,空格等
    :param parser_string:
    :return: 处理完毕后的字符串
    """
    begin_pos = 0
    for i in range(0, len(parser_string)):
        c = parser_string[i]
        if c == " " \
            or c == "\n"\
            or c == "\t":
            continue

        begin_pos = i
        break

    return parser_string[begin_pos:]


def token_count(parser_string):
    """
    解析字符串里面有几个字符
    :param parser_string:
    :return:
    """
    search = token_regex.findall(parser_string)
    return len(search)


def get_next_token_pos(parser_string, token):
    return parser_string.find(token)


def find_token_pair_pos(parser_string, token):
    """
    一直读到符号匹配的对，包括<>, {}, ()
    :param token:  <, {, (
           parser_string: 解析的字符串
    :return: i: 读取到的字符的位置
    """
    assert token == "<" or token == "{" or token == "(" or token == "["

    redundancy = 1      # 冗余的符号个数，因为解析可能解析到<<>>,如果是第一个<则需要一直读取到第四个>才算匹配
    if token == "<":
        pattern_symbol = ">"
    elif token == "{":
        pattern_symbol = "}"
    elif token == "(":
        pattern_symbol = ")"
    elif token == "[":
        pattern_symbol = "]"
    else:
        assert False

    ret_string = ""
    for i in range(0, len(parser_string)):
        c = parser_string[i]
        if c == token:
            redundancy += 1
            ret_string += c
        elif c == pattern_symbol:
            redundancy -= 1
            if redundancy != 0:
                ret_string += c
        else:
            ret_string += c

        if redundancy == 0:
            return i

    return -1


def read_function_by_regex(parser_string, regex):
    """
    根据指定的正则表达式，查找函数
    :param parser_string: 需要解析的字符串
    :param regex:         指定则正则表达式
    :return: functions  解析出来的函数体, FunctionContext
             parser_string 解析完毕后剩下的字符串
    """
    assert regex is not None

    functions = list()
    while True:
        search = regex.search(parser_string)
        if search is None:
            break

        begin_function_pos = search.start(0)
        end_funtion_pos = search.end(0)

        close_brace_pos = find_token_pair_pos(parser_string[end_funtion_pos+1:], "(")+1
        close_brace_pos += end_funtion_pos

        function_context = FunctionContext()
        function_context.function_declare = parser_string[begin_function_pos:close_brace_pos+1]

        # 从函数声明开始找，如果先遇见; 则代表只是一个函数声明
        # 如果先遇见'{' 则表示是一个函数实现，需要把所有的函数体读取出来
        for i in range(close_brace_pos+1, len(parser_string)):
            c = parser_string[i]

            if c is ';':
                end_funtion_pos = i
                break
            elif c is '{':
                end_funtion_pos = i
                pair_token_pos = find_token_pair_pos(parser_string[end_funtion_pos+1:], "{") + 1
                body_end = end_funtion_pos + pair_token_pos + 1
                function_context.function_impl = parser_string[end_funtion_pos: body_end+1]
                end_funtion_pos = body_end
                assert end_funtion_pos != -1
                break

        functions.append(function_context)

        parser_string = parser_string[0:begin_function_pos] + parser_string[end_funtion_pos+1:]

    return functions, parser_string


def read_function(parser_string):
    """
    读取函数相关的信息
    :param parser_string:
    :return: functions  解析出来的函数体, FunctionBody
             parser_string 解析完毕后剩下的字符串
    """
    functions = list()
    while True:
        search = function_regex.search(parser_string)
        if search is None:
            break

        begin_function_pos = search.start(0)
        end_funtion_pos = search.end(0)

        close_brace_pos = find_token_pair_pos(parser_string[end_funtion_pos+1:], "(")+1
        close_brace_pos += end_funtion_pos

        function_context = FunctionContext()
        function_context.function_declare = parser_string[begin_function_pos:close_brace_pos+1]

        # 从函数声明开始找，如果先遇见; 则代表只是一个函数声明
        # 如果先遇见'{' 则表示是一个函数实现，需要把所有的函数体读取出来
        for i in range(close_brace_pos+1, len(parser_string)):
            c = parser_string[i]

            if c is ';':
                end_funtion_pos = i
                break
            elif c is '{':
                end_funtion_pos = i
                pair_token_pos = find_token_pair_pos(parser_string[end_funtion_pos+1:], "{") + 1
                body_end = end_funtion_pos + pair_token_pos + 1
                function_context.function_impl = parser_string[end_funtion_pos: body_end+1]
                end_funtion_pos = body_end
                assert end_funtion_pos != -1
                break

        functions.append(function_context)

        parser_string = parser_string[0:begin_function_pos] + parser_string[end_funtion_pos+1:]

    return functions, parser_string


def read_scope_var(parser_string):
    """
    读取作用域范围内所有的var变量
    :return: ret_vars, parser_string

             ret_vars: 读取到的变量列表, 列表内容是VarContext结构体
             parser_string: 解析后的字符串
    """

    ret_vars = list()
    scope_begin = get_next_token_pos(parser_string, "{")
    if scope_begin == -1:
        scope_begin = 0

    while True:
        search = var_regex.search(parser_string, scope_begin)
        if search is None:
            break

        begin_var_pos = search.start(0)
        end_var_pos = search.end(0)
        if token_count(search.group()) == 1:
            scope_begin = search.end()
            continue

        type_name = search.groupdict().get("type_name")
        if type_name == "return":
            scope_begin = search.end()
            continue

        next_token_pos = get_next_token_pos(parser_string[end_var_pos:], ";")
        assert next_token_pos != -1
        next_token_pos += end_var_pos + 2
        var_context = VarContext(parser_string[begin_var_pos:next_token_pos])
        ret_vars.append(var_context)
        parser_string = parser_string[0: begin_var_pos] + parser_string[next_token_pos+1:]

    return ret_vars, parser_string


def check_class_name(class_body):
    """
    检测类名称是否符合规则
    :param class_body: 解析的字符串
    :return: error_messages
    """

    search = class_regex.search(class_body)
    if search is None:
        return []

    class_name = search.groupdict().get("class_name")
    if class_name[0:3] != "cit":
        return CLASS_NAME_MUST_CIT_BEGIN

    c = class_name[3]
    if not c.isupper() and not c.isdigit():
        return CLASS_NAME_3RD_MUST_UPPER

    class_name_end_pos = search.end()
    for i in range(class_name_end_pos, len(class_body)):
        c = class_body[i]
        if c == '{':
            break
        elif c == ':':
            if i == 0:
                return CLASS_INHERIT_COLON_MUST_BE_SPACE
            if class_body[i-1] != ' ' \
               or class_body[i+1] != ' ':
                return CLASS_INHERIT_COLON_MUST_BE_SPACE
            break

    return None


def check_function(function_body):
    """
    检测函数的规则
    :param function_body:  函数体
    :return: error_message
    """
    assert isinstance(function_body, FunctionContext)
    error_message = list()

    # 解析函数声明
    param_begin_pos = get_next_token_pos(function_body.function_declare, "(")
    param_end_pos = find_token_pair_pos(function_body.function_declare[param_begin_pos+1:], "(")
    param_end_pos += param_begin_pos+2

    param_str = function_body.function_declare[param_begin_pos:param_end_pos]

    params = param_str.split(",")
    for i in range(1, len(params)):
        if params[i][0] != ' ':
            error_message.append((
                                  remove_begin_space_and_newline(function_body.function_declare),
                                  FUNCTION_PARAM_MUST_BE_SPACE))
            break

    # 解析函数体
    if function_body.function_impl:
        function_vars, _ = read_scope_var(function_body.function_impl)
        for function_var in function_vars:
            msg = check_scope_var(function_var)
            if msg:
                error_message.append((
                                      remove_begin_space_and_newline(function_var.var_str),
                                      msg))

    return error_message


def check_scope_var(member_var):
    """
    检测局部变量
    :param member_var:  局部变量
    :return: error_message
    """

    assert isinstance(member_var, VarContext)

    if member_var.var_count() > 1:
        return VAR_TOO_MANY

    if member_var.var_name()[0:2] != "l_":
        return LOCAL_VAR_MUST_BE_L_BEGIN

    return None


def check_class_member_var(member_var):
    """
    检测类成员变量
    :param member_var: 成员变量
    :return: error_message
    """
    assert isinstance(member_var, VarContext)

    if member_var.var_count() > 1:
        return VAR_TOO_MANY

    if member_var.var_name()[0:2] != "m_":
        return CLASS_MEMBER_MUST_M_BEGIN

    return None


class VarContext:
    """
    变量的相关信息
    """
    def __init__(self, var_str=None):
        self.var_str = var_str

    def var_count(self):
        """
        获取声明了多少个变量
        :return:
        """

        # todo: var_regex如果用search会有问题,具体看var_name里面的todo注释
        match = var_regex.match(remove_begin_space_and_newline(self.var_str))
        assert match is not None
        end = match.end(match.lastgroup)
        # int a, b, c  找到a后面的地方
        remainder_str = self.var_str[end+1:]
        return remainder_str.count(",")+1

    def var_name(self):
        """
        获取第一个变量的名称
        :return:
        """

        # todo: 这里需要把前面的\t \n等删除，否则这个正则表达式查找的时候会有问题
        # 比如: \tstatic map<string, vector<QTranslator*>*>* m_pLanguages;这里会把var_name解析成map
        search = var_regex.search(remove_begin_space_and_newline(self.var_str))
        var_name = search.groupdict().get("var_name")
        assert var_name is not None

        return var_name


class FunctionContext:
    """
    函数的相关信息
    """
    def __init__(self):
        self.function_declare = None
        self.function_impl = None


class ClassContext:
    """
    类相关的信息
    """
    def __init__(self):
        self.class_body = None
        self.functions = list()
        self.member_vars = list()
        self.enums = list()

    def class_name(self):
        search = class_regex.search(self.class_body)
        assert search is not None
        return search.groupdict().get("class_name")

    def check_rule(self):
        """
        检测规则
        :return: 返回错误信息
        """
        error_message = dict()

        # 检测类的信息
        msg = check_class_name(self.class_body)
        if msg:
            if error_message.get("class_rule") is None:
                error_message["class_rule"] = list()

            error_message["class_rule"].append(msg)

        # 检测函数的信息
        for function_context in self.functions:
            msg = check_function(function_context)
            if msg:
                if error_message.get("function_rule") is None:
                    error_message["function_rule"] = list()

                error_message["function_rule"].append(msg)

        # 检测类成员变量
        for member_var in self.member_vars:
            msg = check_class_member_var(member_var)
            if msg:
                if error_message.get("member_rule") is None:
                    error_message["member_rule"] = list()
                error_message["member_rule"].append((
                                                     remove_begin_space_and_newline(member_var.var_str),
                                                     msg))

        return error_message

    def parser(self):
        assert self.class_body is not None

        # 注意这里需要保证顺序，否则会导致错乱，因为一个正则表达式可以匹配好多情况
        self.parser_enums()
        self.parser_function()
        # self.parser_destroy()
        # self.parser_construct()
        self.parser_vars()

    def parser_enums(self):
        """
        解析所有的类枚举
        :return:
        """
        enums, self.class_body = read_enum(self.class_body)
        if len(enums):
            self.enums.extend(enums)

    def parser_vars(self):
        """
        解析所有的类成员变量
        :return:
        """
        parser_vars, self.class_body = read_scope_var(self.class_body)
        if len(parser_vars):
            self.member_vars.extend(parser_vars)

    def parser_function(self):
        """
        解析函数,并且会消掉函数的字符串
        :return:
        """
        functions, self.class_body = read_function(self.class_body)
        if len(functions) > 0:
            self.functions.extend(functions)

    def parser_construct(self):
        """
        解析构造函数
        :return: None
        """
        constructs, self.class_body = read_function_by_regex(self.class_body, construct_regex)
        if len(constructs) > 0:
            self.constructs.extend(constructs)

    def parser_destroy(self):
        """
        解析析构函数
        :return:
        """
        destroys, self.class_body = read_function_by_regex(self.class_body, destroy_regex)
        assert len(destroys) <= 1
        self.destroy = destroys


class ClassParser:
    def __init__(self):
        self.class_contexts = list()

    def parser(self):
        """
        开始解析类相关的信息
        :return: None
        """
        for context in self.class_contexts:
            context.parser()

    def check_rule(self):
        """
        检测结果
        :return: 返回error_message, error_message是一个dict,key是类名称, values为这个类检测的结果
        """
        error_message = dict()
        for context in self.class_contexts:
            msg = context.check_rule()
            if len(msg):
                if error_message.get(context.class_name()) is None:
                    error_message[context.class_name()] = list()

                error_message[context.class_name()].append(msg)

        return error_message

    def read_class_body(self, parser_string):
        """
        从parser_string读取出对应的结构体信息
        :param parser_string:
        :return: 删除了class_body相关字符串的parser_string
        """
        while True:
            search = class_regex.search(parser_string)
            if search is None:
                break

            begin_class_pos = search.start(0)
            end_class_pos = search.end(0)
            if parser_string[end_class_pos] == ';':     # 表示是声明
                parser_string = parser_string[0:begin_class_pos] + parser_string[end_class_pos+1:]  # 删除类声明
                continue

            open_brace_pos = get_next_token_pos(parser_string[end_class_pos:], "{")
            assert open_brace_pos != -1
            open_brace_pos += end_class_pos

            close_brace_pos = find_token_pair_pos(parser_string[open_brace_pos+1:], "{")
            # 第一次取出来的是相对位置
            close_brace_pos = open_brace_pos + close_brace_pos + 2

            class_body = parser_string[begin_class_pos:close_brace_pos+1]
            class_context = ClassContext()
            class_context.class_body = class_body
            self.class_contexts.append(class_context)
            assert class_body[-1] == ";"
            parser_string = parser_string[0:begin_class_pos] + parser_string[close_brace_pos+1:]

        return parser_string


class TokenParser:
    """
    辅助解析Token的,负责从begin_pos开始解析每一个token
    """
    def __init__(self, parser_string, begin_pos):
        self.token_iter = token_regex.finditer(parser_string, begin_pos)
        self.parser_string = parser_string
        self.current_match = None

    def next_token(self):
        """
        获取下一个符号
        :return: 下一个符号
        """
        self.current_match = self.token_iter.__next__()
        return self.current_token()

    def current_token(self):
        return self.parser_string[self.current_match.span()[0]:self.current_match.span()[1]]

    def current_pos(self):
        if self.current_match:
            return self.current_match.span()[1]
        return 0


def read_enum(parser_string):
    """
    找到枚举相关的字符串
    :param parser_string:
    :return: enum_strings, parser_string
    """
    enum_strings = list()

    while True:
        search = enum_regex.search(parser_string)
        if search is None:
            break

        enum_begin = search.start()
        token_parser = TokenParser(parser_string, enum_begin)

        while True:
            current_token = token_parser.next_token()

            if current_token == ";":     # 如果没读到;而是一直读到发生异常,说明语法有问题
                break

        enum_strings.append(parser_string[enum_begin:token_parser.current_pos()])
        parser_string = parser_string[0:enum_begin] + parser_string[token_parser.current_pos():]

    return enum_strings, parser_string


def remove_comment(parser_string):
    """
    删除注释相关的文本
    :param parser_string: 需要处理的文本
    :return:  删除注释完毕后的文本
    """
    while True:
       search = mul_line_comment_regex.search(parser_string)
       if search is None:
           break

       comment_begin_pos = search.start(0)
       comment_end_pos = search.end(0)
       parser_string = parser_string[0:comment_begin_pos] + parser_string[comment_end_pos:]

    while True:
        search = one_line_comment_regex.search(parser_string)
        if search is None:
            break

        comment_begin_pos = search.start(0)
        comment_end_pos = search.end(0)
        parser_string = parser_string[0:comment_begin_pos] + parser_string[comment_end_pos:]

    return parser_string


def remove_friend_regex(parser_string):
    """
    删除指定友元函数声明
    :param parser_string:   分析的字符串
    :return: 删除后的字符串
    """

    while True:
        search = friend_declare_regex.search(parser_string)
        if search is None:
            break

        friend_declare_begin = search.span()[0]
        params_begin = search.span()[1]
        end_pos = find_token_pair_pos(parser_string[params_begin+1:], "(")+1
        end_pos += params_begin
        assert parser_string[end_pos+1] == ';'
        end_pos += 1

        parser_string = parser_string[0:friend_declare_begin] + parser_string[end_pos+1:]

    return parser_string


def remove_key(parser_string, key):
    """
    删除指定的关键字
    :param parser_string:
    :param key:
    :return:
    """
    key_regex = re.compile("\s*("+key + ")\s+")
    while True:
        search = key_regex.search(parser_string)
        if search is None:
            break

        start = search.start(1)
        end = search.end(1)

        parser_string = parser_string[0:start] + parser_string[end:]

    return parser_string


def remove_unnecessary_key(parser_string):
    """
    删除会影响解析但是不关键的字，比如Q_OBJECT, public:, private:, protected:等
    :param parser_string:
    :return: 返回处理后的字符
    """
    parser_string = remove_key(parser_string, r"Q_OBJECT")
    parser_string = remove_key(parser_string, r"public:")
    parser_string = remove_key(parser_string, r"private:")
    parser_string = remove_key(parser_string, r"protected:")
    parser_string = remove_key(parser_string, r"signals:")
    parser_string = remove_key(parser_string, r"protected\s+slots:")
    parser_string = remove_key(parser_string, r"public\s+slots:")
    parser_string = remove_key(parser_string, r"private\s+slots:")

    return parser_string


def remove_unnecessary_data(data):
    """
    删除不需要的数据
    :param data:
    :return: 解析后的数据
    """
    data = remove_comment(data)
    data = remove_unnecessary_key(data)
    data = remove_friend_regex(data)
    return data


def check_file(file_path):
    """
    解析文件的规则
    :param file_path: 文件路径
    :return: rule 有检测出错误,返回检测出的结果
             None 没有检测出错误
    """
    fp = open(file_path, mode="r", encoding="gb2312")
    fp.seek(0, 2)
    length = fp.tell()
    fp.seek(0, 0)
    data = fp.read(length)

    data = remove_unnecessary_data(data)

    parser = ClassParser()
    parser.read_class_body(data)
    parser.parser()
    rule = parser.check_rule()
    if len(rule) != 0:
        return rule

    return None


def check_dir(dir_path):
    """
    检测目录下的所有.h和.cpp文件的规则
    :param dir_path:
    :return:
    """
    import os
    error_message = list()
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".h"):
                try:
                    check_rule = check_file(root + '/' + file)
                    if check_rule:
                        error_message.append({file: check_rule})
                except Exception as e:
                    print("解析"+file+"文件错误:" + str(e))

    return error_message


if __name__ == "__main__":
    import sys
    import getopt
    opts, args = getopt.getopt(sys.argv[1:], "hf:d:")
    check_result = None
    for opt, value in opts:
        if opt == "-f":
            check_result = check_file(value)
        elif opt == "-d":
            check_result = check_dir(value)
        else:
            continue

    import json
    f = open("./output_back.json", "w")
    json.dump(check_result, f, ensure_ascii=False, indent=4)
    f.close()
