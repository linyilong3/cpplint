import re
import os.path
# todo: 后续把所有match_*的代码都改成match_and_check_*的形式，可以比较好做递归下降来进行语法分析
# todo: python在进行正则表达式匹配有时候会卡死

# 正则表达式模板字符串
template_regex_str = r"(?P<template><[\w<>:\s\d,\*&]+>)?"       # 匹配<>里面的东西
# 指针或者引用的表达式
pointer_or_ref_regex_str = r"(\*|&|\s)+"
# 类型的正则表达式
type_regex_str = r"(?P<type_name>(\w+::)?(\w+))" + template_regex_str + pointer_or_ref_regex_str

# 变量名称的正则表达式
var_name_str = r"(?P<var_name>(\w|\[|\]|->|\.|<|>|\*)+)"

# 类起始位置的正则表达式
class_regex = re.compile(r"class\s+(\w+\s+)?(?P<class_name>\w+)")

# 类声明的正则表达式
class_declare_regex = re.compile(r"class\s+(\w+\s+)?(?P<class_name>\w+);")

# 函数起始位置的正则表达式
function_regex = re.compile(r"((virtual|static|inline)\s*)?(\w+::)?(\w+)(<[\w<>:\d,\*\s&]+>)?\s*[\*,&]*\s*"
                            r"(?P<function_name>\w+)\s*\(")
# 析构函数声明的正则表达式
destroy_declare_regex = re.compile(r"(virtual\s+)?~\w+\((void)?\)")

# 变量声明正则表达式
var_regex = re.compile(r"(?:static\s+)?(?:const\s+)?"+type_regex_str + var_name_str)

# 友元函数声明
friend_declare_regex = re.compile("friend\s+.+\(")
# 多行的注释
mul_line_comment_regex = re.compile(r"/\*(.|\n)*?(\*/)")
# 单行的注释
one_line_comment_regex = re.compile(r"//.*")

# 重载操作符的正则表达式
operator_regex = re.compile(r"(static\s+)?(\w+::)?(\w+)(<[\w<>:\s\d,\*&]+>)?(\*|&|\s)+"
                            r"operator(\s|\+|\-|\*|/|!|=|<<|>>|<|>)+\(")
# do..while表达式
do_while_stat_regex = re.compile(r"do\s*\{")
# while表达式
while_stat_regex = re.compile(r"while\s*\((.|\s)+?\)\s*\{")
# for表达式
for_stat_regex = re.compile(r"for\s*\((.|\s)*?;(.|\s)*?;(.|\s)*?\)\s*?{")
# switch表达式
switch_stat_regex = re.compile(r"switch\s*\((.|\s)+?\)\s*\{")
# return 表达式
return_stat_regex = re.compile(r"return (.|\s)+?;")
# function调用表达式
function_call_regex = re.compile(r"\w+\(")
# if表达式
if_stat_regex = re.compile(r"if\s*\(")
# 赋值表达式
assign_regex = re.compile(var_name_str+r"=")
# 类成员函数表达式
class_member_impl_begin_regex = re.compile(type_regex_str + r"\w+::\w+\(")
# delete 语句
delete_stat_regex = re.compile(r"delete(\s|.)+?;")
# stream 语句
stream_stat_regex = re.compile(r".+\s*(<<|>>)\s*.[^;]+")
# define 开头语句
define_start_regex = re.compile(r"#define")
# typedef 语句
typedef_stat_regex = re.compile(r"typedef")
# enum语句
enum_stat_regex = re.compile(r"enum\s*\w*\s*\{(.|\s)*?\}\s*\w+;")
# #include "..."
self_include_regex = re.compile(r'#include\s+"(?P<include_name>(.)+)?"')
# #include <...>
system_include_regex = re.compile(r"#include\s+<(?P<include_name>(.)+)?>")
# using namespace ...;
using_name_regex = re.compile(r"using namespace (.|\s)+?;")
# qobject
qobject_regex = re.compile(r"Q_OBJECT")
# public, protected, private访问控制
access_control_regex = re.compile(r"public|protected|private|signals|slots")
# struct
struct_regex = re.compile(r"struct\s*\w*\s*\{")
# 析构函数实现的正则表达式
destroy_impl_start_regex = re.compile(r"\w+::~\w+\(")
# 构造函数实现的正则表达式
construct_impl_start_regex = re.compile(r"\w+::\w+\(")

# 错误信息
# 类相关规则
CLASS_NAME_MUST_CIT_BEGIN = r"类名称必须以cit开头"
CLASS_NAME_3RD_MUST_UPPER = r"cit后面的字符必须以大写字母开头"
CLASS_INHERIT_COLON_MUST_BE_SPACE = r"类继承的冒号前后必须要有空格"

CLASS_MEMBER_MUST_M_BEGIN = r"类成员变量必须以m_开头"
VAR_TOO_MANY = r"同时定义太多的变量"

FUNCTION_PARAM_MUST_BE_SPACE = r"不同的函数参数之间最少要留一个空格"
FUNCTION_NAME_BEGIN_CIT = r"函数名称必须以cit开头"
LOCAL_VAR_MUST_BE_L_BEGIN = r"局部变量必须以l_开头"
DEFINE_BEGIN_PREFIX_MUST_BE_CIT = r"宏定义必须以CIT_开头"
DEFINE_MUST_BE_UPPER = r"宏定义必须大写"
ENUM_USE_CIT_BEGIN_ENUM = r"单独定义的枚举要使用CIT_BEGIN_ENUM和CIT_END_ENUM"
STATIC_VAR_BEGIN_S = r"static变量以s_开头"
GLOBAL_VAR_BEGIN_G = r"全局变量以g_开头"
VAR_NAME_TOO_SHORT = r"变量名称太短"
POINT_OR_REF_NEAR_TYPE = r"*或者&必须紧跟在变量类型后面"
SYSTEM_INCLUDE_AFTER_SELF_INCLUDE = r"include顺序错误，应该把系统库放到前面"
QOBJECT_MUST_BE_END_WITH_CLASS = r"Q_OBJECT必须放在类的结尾"
DESTROY_ADVISE_VIRTUAL = r"析构函数建议是virtual"


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


def get_next_token_pos(parser_string, token):
    # todo: 把这个函数去掉
    return parser_string.find(token)


def find_token_pair_by_pos(parser_string, start_pos, token):
    """
    从start_pos开始，找到对应匹配符号,比如'<'则会找到下一个'>',如果是<<..>>这种语法，将会找到最后那个'>'
    :param parser_string: 解析的字符串
    :param start_pos: 从哪里开始查找匹配的
    :param token: 匹配的符号
    :return: pos 读取到的字符的位置, 没读到则返回-1
    """
    assert token == "<" or token == "{" or token == "(" or token == "["
    c = parser_string[start_pos]
    assert c == "<" or c == "{" or c == "(" or c == "["

    redundancy = 0      # 冗余的符号个数，因为解析可能解析到<<>>,如果是第一个<则需要一直读取到第四个>才算匹配
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
    for i in range(start_pos, len(parser_string)):
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


def find_token_pair_pos(parser_string, token):
    # todo: 把这个函数去掉，改成使用find_token_pair_by_pos
    """
    一直读到符号匹配的对，包括<>, {}, ()
    :param token:  <, {, (
    :param parser_string: 解析的字符串
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
        end_function_pos = search.end(0)

        close_brace_pos = find_token_pair_pos(parser_string[end_function_pos+1:], "(")+1
        close_brace_pos += end_function_pos

        function_context = FunctionContext()
        function_context.function_declare = parser_string[begin_function_pos:close_brace_pos+1]

        # 从函数声明开始找，如果先遇见; 则代表只是一个函数声明
        # 如果先遇见'{' 则表示是一个函数实现，需要把所有的函数体读取出来
        for i in range(close_brace_pos+1, len(parser_string)):
            c = parser_string[i]

            if c is ';':
                end_function_pos = i+1
                break
            elif c is '{':
                end_function_pos = i
                pair_token_pos = find_token_pair_pos(parser_string[end_function_pos+1:], "{") + 1
                body_end = end_function_pos + pair_token_pos + 1
                function_context.function_impl = parser_string[end_function_pos: body_end]
                end_function_pos = body_end
                assert end_function_pos != -1
                break

        functions.append(function_context)

        parser_string = parser_string[0:begin_function_pos] + parser_string[end_function_pos:]

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
        if TokenParser.token_count(search.group()) == 1:
            scope_begin = search.end()
            continue

        next_token_pos = get_next_token_pos(parser_string[end_var_pos:], ";")
        assert next_token_pos != -1
        next_token_pos += end_var_pos + 2
        var_context = VarContext(parser_string[begin_var_pos:next_token_pos])
        ret_vars.append(var_context)
        parser_string = parser_string[0: begin_var_pos] + parser_string[next_token_pos:]

    return ret_vars, parser_string


def check_function(function_context):
    """
    检测函数的通用规则，普通的函数和类成员函数规则不一样, 普通函数的命名在其他地方检测
    :param function_context:  函数体
    :return: error_message
    """
    assert isinstance(function_context, FunctionContext)
    error_message = list()

    # 解析函数声明
    declare_error = function_context.check_params()
    if declare_error:
        error_message.append(
            ErrorReport(
                line=FileContext.current_line,
                message=declare_error,
                error_context=function_context.function_declare
            )
        )

    # 解析函数体
    if function_context.function_impl:
        function_vars = peek_scope_vars(function_context)
        for function_var in function_vars:
            msg = check_scope_var(function_var)
            if msg:
                error_message.append(
                    ErrorReport(
                        line=FileContext.current_line,
                        message=msg,
                        error_context=function_var.var_str
                    )
                )

    return error_message


def check_scope_var(member_var):
    """
    检测局部变量
    :param member_var:  局部变量
    :return: error_message
    """

    assert isinstance(member_var, VarContext)

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
        remainder_str = self.var_str[end:]
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

    def is_static(self):
        return self.var_str.find("static ") != -1


class FileContext:
    PARSER_TYPE_FILE = "FILE"
    PARSER_TYPE_CLASS = "CLASS"

    current_file_name = None        # 当前文件名

    """
    检测include文件的时候，如果已经检测到了""包含的文件，那么会将这个标志位设置True,
    如果后续再遇见<>包含的文件，则会错误
    """
    include_system_end = False
    # 当前解析的行数
    current_line = 0

    # 当前在检测的数据类型
    current_parser_context = PARSER_TYPE_FILE

    def __init__(self):
        pass

    @staticmethod
    def current_is_header():
        return FileContext.current_file_name.endswith(".h")


class FunctionContext:
    """
    函数的相关信息
    """
    # 参数间隔的正则表达式
    param_regex = re.compile(r"\s*(?:const\s+)?((\w+::)?(\w+))(<[\w<>:\s\d,]+>)?(\s|\*|&)+\w+,")

    def __init__(self):
        self.function_declare = None
        self.function_impl = None

    def function_name(self):

        match = function_regex.match(self.function_declare)
        # 重载操作符则把整个声明都当作函数名
        if match is None:
            match = operator_regex.match(self.function_declare)
            if match:
                return self.function_declare
        assert match is not None

        name = match.groupdict().get("function_name")
        return name

    def check_params(self):
        """
        分析所有函数的参数
        :return:
        """
        begin_pos = self.function_declare.find("(")
        if begin_pos == -1:
            return -1

        while True:
            search = self.param_regex.search(self.function_declare, begin_pos)
            if search is None:
                return None

            param_end = search.end()
            c = self.function_declare[param_end]
            if c != ' '\
                    and c != '\n':
                return FUNCTION_PARAM_MUST_BE_SPACE

            begin_pos = param_end+1

        return None


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
            return "%s(%d,0): < %s >======%s" % (self.file_full_path, self.line, self.error_context, self.message)
        else:
            return "%s(%d,0): %s" % (self.file_full_path, self.line, self.message)


class TokenParser:
    """
    辅助解析Token的,负责从begin_pos开始解析每一个token
    """
    # 分隔符的正则表达式
    token_regex = re.compile(r'(\w+|}|{|::|;|\(|\)|,|\*|<|>|\[|\])')

    def __init__(self, parser_string, begin_pos):
        self.token_iter = self.token_regex.finditer(parser_string, begin_pos)
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

    def current_token_end_pos(self):
        """
        返回当前解析的位置,也就是当前符号结束的位置，比如"ab,c",
        token是ab，则current_token_end_pos为,的位置
        :return:
        """
        if self.current_match:
            return self.current_match.span()[1]
        return 0

    @staticmethod
    def token_count(parser_string):
        """
        解析字符串里面有几个字符
        :param parser_string:
        :return:
        """
        search = TokenParser.token_regex.findall(parser_string)
        return len(search)


def match_stream_stat(parser_string, start_pos):
    """
    从start_pos开始检测,是否符合stream语句的语法，如果符合，则返回整个stream语句的作用域(指的是{}这个里面，或者if语句的下一句)
    :param parser_string: 需要解析的语句
    :param start_pos: 开始的位置,
    :return: stat_start, stat_end, 如果没有匹配，则都返回-1
    """
    match = stream_stat_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1

    end_pos = parser_string.find(";", match.end())
    return match.start(), end_pos


def match_using_namespace(parser_string, start_pos):
    """
    检测using namespace ...的语法
    :param parser_string:
    :param start_pos:
    :return: stat_start, stat_end, 如果没有匹配，则返回-1,否则返回
    """
    match = using_name_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1

    return match.start(), match.end()-1


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

    return match.start(), match.end()-1


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


def next_token(parser_string, start_pos):
    """
    返回下一个token
    :param parser_string:
    :param start_pos:
    :return: token
    """
    token_parser = TokenParser(parser_string, start_pos)
    token_parser.next_token()
    return token_parser.current_token()


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


def match_and_check_class_declare_function(parser_string, start_pos):
    """
    从start_pos开始检测，查看是否符合类成员函数声明的语法
    :param parser_string:
    :param start_pos:
    :return: stat_start, stat_end, error_message, 如果没有匹配，则返回-1, -1, []
    """
    error_message = list()
    while True:
        match = function_regex.match(parser_string, start_pos)
        if match:
            break
        match = operator_regex.match(parser_string, start_pos)
        if match:
            break
        return -1, -1, error_message

    function_declare_end_pos = find_token_pair_by_pos(parser_string, match.end()-1, "(")
    function_context = FunctionContext()
    function_context.function_declare = parser_string[start_pos:function_declare_end_pos+1]
    try:
        parser = TokenParser(parser_string, function_declare_end_pos+1)
        parser.next_token()
    except StopIteration:
        return -1, -1, error_message

    if parser.current_token() == "const":
        parser.next_token()

    if parser.current_token() == ";":
        function_end_pos = parser.current_token_end_pos()-1
    else:
        # 这里有可能只是类似于CIT_BEGIN_ENUM的枚举，所以直接跳过
        if parser.current_token() != "{":
            return -1, 1, error_message

        function_body_begin_pos = parser.current_token_end_pos()-1
        function_end_pos = find_token_pair_by_pos(parser_string, function_body_begin_pos, "{")
        function_context.function_impl = parser_string[function_body_begin_pos:function_end_pos+1]

    check_function_error_message = check_function(function_context)
    if len(check_function_error_message):
        error_message.append(check_function_error_message)

    return start_pos, function_end_pos, error_message


def match_and_check_function(parser_string, start_pos):
    """
    从start_pos开始检测,是否符合函数定义语法
    :param parser_string: 需要解析的语句
    :param start_pos: 开始的位置,
    :return: stat_start, stat_end, error_message,如果没有匹配，则返回-1, -1, []
    """
    error_message = list()
    while True:
        match = function_regex.match(parser_string, start_pos)
        if match:
            is_operator = False
            break
        match = operator_regex.match(parser_string, start_pos)
        if match:
            is_operator = True
            break
        return -1, -1, error_message

    function_declare_end_pos = find_token_pair_by_pos(parser_string, match.end()-1, "(")
    function_context = FunctionContext()
    function_context.function_declare = parser_string[start_pos:function_declare_end_pos+1]
    try:
        parser = TokenParser(parser_string, function_declare_end_pos+1)
        parser.next_token()
    except StopIteration:
        return -1, -1, error_message

    if parser.current_token() == "const":
        parser.next_token()

    if parser.current_token() == ";":
        function_end_pos = parser.current_token_end_pos()-1
    else:
        # 这里有可能只是类似于CIT_BEGIN_ENUM的枚举，所以直接跳过
        if parser.current_token() != "{":
            return -1, 1, error_message

        function_body_begin_pos = parser.current_token_end_pos()-1
        function_end_pos = find_token_pair_by_pos(parser_string, function_body_begin_pos, "{")
        function_context.function_impl = parser_string[function_body_begin_pos:function_end_pos+1]

    function_name = function_context.function_name()
    if function_name[0:3] != "cit" and not is_operator and function_name != "main":
        error_message.append(
            ErrorReport(
                line=FileContext.current_line,
                message=FUNCTION_NAME_BEGIN_CIT,
                error_context=function_context.function_declare
            )
        )

    check_function_error_message = check_function(function_context)
    if len(check_function_error_message):
        error_message.extend(check_function_error_message)

    return start_pos, function_end_pos, error_message


def match_and_check_class_var(parser_string, start_pos):
    """
    从start_pos开始检测,是否符合变量语法，并且检测错误
    :param parser_string: 需要解析的语句
    :param start_pos: 开始的位置,
    :return: start_pos, end_pos, error_message,如果没有匹配，则返回-1, -1, []
    """
    error_message = list()
    match = var_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1, error_message

    var_name = match.groupdict().get("var_name")
    if len(var_name) == 0:
        return -1, -1, error_message

    var_context = VarContext()
    var_context.var_str = parser_string[match.start():match.end()]

    while True:
        if len(var_context.var_name()) < 3:
            error_message.append(ErrorReport(line=FileContext.current_line,
                                             message=VAR_NAME_TOO_SHORT,
                                             error_context=var_context.var_str))
            break

        if var_context.var_name()[0:2] != "m_":
            error_message.append(ErrorReport(
                line=FileContext.current_line,
                message=CLASS_MEMBER_MUST_M_BEGIN,
                error_context=var_context.var_str
            ))

        pointer_err = check_pointer_and_ref(var_context)
        if pointer_err is not None:
            error_message.append(
                ErrorReport(
                    line=FileContext.current_line,
                    message=POINT_OR_REF_NEAR_TYPE,
                    error_context=var_context.var_str
                )
            )
            break
        break

    end_pos = parser_string.find(";", match.end())

    return match.start(), end_pos, error_message


def match_and_check_var(parser_string, start_pos):
    """
    从start_pos开始检测,是否符合变量语法，并且检测错误
    :param parser_string: 需要解析的语句
    :param start_pos: 开始的位置,
    :return: start_pos, end_pos, error_message,如果没有匹配，则返回-1, -1, []
    """
    error_message = list()
    match = var_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1, error_message

    var_name = match.groupdict().get("var_name")
    if len(var_name) == 0:
        return -1, -1, error_message

    var_context = VarContext()
    var_context.var_str = parser_string[match.start():match.end()]

    while True:
        if len(var_context.var_name()) < 3:
            error_message.append({var_context.var_str: VAR_NAME_TOO_SHORT})
            break

        if var_context.is_static():
            if var_context.var_name()[0:2] != "s_":
                error_message.append({var_context.var_str: STATIC_VAR_BEGIN_S})
                break
        elif var_context.var_name()[0:2] != "g_":
            error_message.append({var_context.var_str: GLOBAL_VAR_BEGIN_G})
            break

        pointer_err = check_pointer_and_ref(var_context)
        if pointer_err is not None:
            error_message.append({var_context.var_str: pointer_err})
            break
        break

    end_pos = parser_string.find(";", match.end())

    return match.start(), end_pos, error_message


def match_and_check_typedef(parser_string, start_pos):
    """
    从start_pos开始检测，是否符合typedef语法，并且检测错误
    :param parser_string:
    :param start_pos:
    :return: stat_start, stat_end, error_message, 如果没有匹配，则返回-1, -1, []
    """
    error_message = list()
    match = typedef_stat_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1, error_message

    # 匹配typedef
    next_token_begin = next_token_pos_not_space(parser_string, match.end())
    enum_start_pos, enum_end_pos, error_message = match_and_check_enum(parser_string, next_token_begin)
    if enum_start_pos != -1:
        return match.start(), enum_end_pos, error_message

    struct_start_pos, struct_end_pos = match_struct(parser_string, next_token_begin)
    if struct_start_pos != -1:
        return match.start(), struct_end_pos, error_message

    typedef_end_pos = parser_string.find(";", match.end())

    return match.start(), typedef_end_pos, error_message


def match_and_check_qobject(parser_string, start_pos):
    """
    检测Q_OBJECT是否在类的尾部
    :param parser_string:
    :param start_pos:
    :return: start_pos, end_pos, error_message
    """
    error_message = list()
    match = qobject_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1, error_message

    seek_first_token_pos = next_token_pos_not_space(parser_string, match.end())

    if parser_string[seek_first_token_pos:seek_first_token_pos+2] != "};":
        error_message.append(ErrorReport(line=FileContext.current_line,
                                         error_context=parser_string[match.start():match.end()],
                                         message=QOBJECT_MUST_BE_END_WITH_CLASS))
    return match.start(), match.end(), error_message


def match_class_access(parser_string, start_pos):
    """
    从start pos开始，检测是否符合public, protected, private等访问控制的语法
    :param parser_string:
    :param start_pos:
    :return: start_pos, end_pos     开始位置，结束位置
    """
    match = access_control_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1

    end_pos = parser_string.find(":", match.end())
    return match.start(), end_pos


def match_friend_declare(parser_string, start_pos):
    """
    从start_pos开始检测，是否符合友元函数语法，并且检测错误
    :param parser_string:
    :param start_pos:
    :return: stat_start, stat_end 开始的位置，结束的位置
    """
    match = friend_declare_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1

    end_pos = parser_string.find(";", match.end())

    return match.start(), end_pos


def match_and_check_destroy(parser_string, start_pos):
    """
    检测析构函数是否符合语法
    :param parser_string:
    :param start_pos:
    :return: stat_start, stat_end, error_message
    """
    error_message = list()
    match = destroy_declare_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1, error_message

    has_virtual = parser_string.find("virtual", match.start(), match.end())
    if has_virtual == -1:
        error_message.append(ErrorReport(line=FileContext.current_line,
                                         message=DESTROY_ADVISE_VIRTUAL,
                                         error_context=parser_string[match.start():match.end()]))

    return match.start(), match.end(), error_message


def match_and_check_class_impl(parser_string, start_pos):
    """
    检测函数实现
    :param parser_string:
    :param start_pos:
    :return: stat_start, stat_end, error_message
    """
    error_message = []
    while True:
        match = destroy_impl_start_regex.match(parser_string, start_pos)
        if match:
            break

        match = construct_impl_start_regex.match(parser_string, start_pos)
        if match:
            break

        match = class_member_impl_begin_regex.match(parser_string, start_pos)
        if match:
            break
        return -1, -1, error_message

    function_declare_end_pos = find_token_pair_by_pos(parser_string, match.end()-1, "(")
    function_context = FunctionContext()
    function_context.function_declare = parser_string[start_pos:function_declare_end_pos+1]
    try:
        parser = TokenParser(parser_string, function_declare_end_pos+1)
        parser.next_token()
    except StopIteration:
        return -1, -1, error_message

    if parser.current_token() == "const":
        parser.next_token()

    if parser.current_token() == ";":
        function_end_pos = parser.current_token_end_pos()-1
    else:
        # 这里有可能只是类似于CIT_BEGIN_ENUM的枚举，所以直接跳过
        if parser.current_token() != "{":
            return -1, -1, error_message

        function_body_begin_pos = parser.current_token_end_pos()-1
        function_end_pos = find_token_pair_by_pos(parser_string, function_body_begin_pos, "{")
        function_context.function_impl = parser_string[function_body_begin_pos:function_end_pos+1]

    check_function_error_message = check_function(function_context)
    if len(check_function_error_message):
        error_message.extend(check_function_error_message)

    return start_pos, function_end_pos, error_message


def match_and_check_class(parser_string, start_pos):
    """
    从start_pos开始检测,是否符合class的语法，并且检测错误
    :param parser_string:
    :param start_pos:
    :return: stat_start, stat_end, error_message, 如果没有匹配，则返回-1, -1, []
    """
    error_message = list()
    match = class_declare_regex.match(parser_string, start_pos)
    if match:
        return match.start(), match.end()-1, error_message

    match = class_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1, error_message

    # 检测类名称规则
    class_name = match.groupdict().get("class_name")
    if class_name[0:3] != "cit":
        error_message.append(
            ErrorReport(line=FileContext.current_line,
                        message=CLASS_NAME_MUST_CIT_BEGIN,
                        error_context=class_name)
        )

    c = class_name[3]
    if not c.isupper() and not c.isdigit():
        error_message.append(
            ErrorReport(
                line=FileContext.current_line,
                message=CLASS_NAME_3RD_MUST_UPPER,
                error_context=class_name
            )
        )

    try:
        FileContext.current_parser_context = FileContext.PARSER_TYPE_CLASS
        next_token_pos = next_token_pos_not_space(parser_string, match.end())

        # 检测类冒号前后是否有空格
        if parser_string[next_token_pos] == ":":
            if parser_string[next_token_pos-1] != " " and parser_string[next_token_pos+1] != " ":
                error_message.append(ErrorReport(line=FileContext.current_line,
                                                 message=CLASS_INHERIT_COLON_MUST_BE_SPACE,
                                                 error_context=parser_string[match.start(), match.end()]))
        class_declare_begin = parser_string.find("{", next_token_pos)

        class_start_pos = class_declare_begin+1
        while True:
            old_class_start_pos = class_start_pos
            class_start_pos = next_token_pos_not_space(parser_string, class_start_pos)
            assert old_class_start_pos <= class_start_pos

            access_start, access_end = match_class_access(parser_string, class_start_pos)
            if access_start != -1:
                class_start_pos = access_end + 1
                continue

            friend_start, friend_end = match_friend_declare(parser_string, class_start_pos)
            if friend_start != -1:
                class_start_pos = friend_end + 1
                continue

            class_start_pos, is_continue = helper_match_and_check(error_message,
                                                                  parser_string,
                                                                  class_start_pos,
                                                                  match_and_check_define)
            if is_continue:
                continue

            class_start_pos, is_continue = helper_match_and_check(error_message,
                                                                  parser_string,
                                                                  class_start_pos,
                                                                  match_and_check_qobject)
            if is_continue:
                continue

            class_start_pos, is_continue = helper_match_and_check(error_message,
                                                                  parser_string,
                                                                  class_start_pos,
                                                                  match_and_check_destroy)
            if is_continue:
                continue

            class_start_pos, is_continue = helper_match_and_check(error_message,
                                                                  parser_string,
                                                                  class_start_pos,
                                                                  match_and_check_class_declare_function)
            if is_continue:
                continue

            class_start_pos, is_continue = helper_match_and_check(error_message,
                                                                  parser_string,
                                                                  class_start_pos,
                                                                  match_and_check_typedef)
            if is_continue:
                continue

            class_start_pos, is_continue = helper_match_and_check(error_message,
                                                                  parser_string,
                                                                  class_start_pos,
                                                                  match_and_check_class_var)
            if is_continue:
                continue

            # 检测类是否结束
            if parser_string[class_start_pos:class_start_pos+2] == "};":
                return start_pos, class_start_pos+1, error_message

            class_start_pos = parser_string.find(";", class_start_pos)
            assert class_start_pos == -1
            return start_pos, class_start_pos, error_message
    finally:
        FileContext.current_parser_context = FileContext.PARSER_TYPE_FILE


def match_and_check_define(parser_string, start_pos):
    """
    从start_pos开始检测,是否符合define语法，并且检测错误
    :param parser_string: 需要解析的语句
    :param start_pos: 开始的位置,
    :return: stat_start, stat_end, error_message,如果没有匹配，则返回-1, -1, []
    """

    # 匹配宏定义的开始
    error_message = list()
    match = define_start_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1, error_message

    # 匹配宏定义名称
    define_name_begin_pos = next_token_pos_not_space(parser_string, match.end())
    assert define_name_begin_pos is not -1

    define_name_regex = re.compile("(\w+)(\(.+?\))?")
    define_name_match = define_name_regex.match(parser_string, define_name_begin_pos)
    assert define_name_match is not None
    define_name = parser_string[define_name_match.start():define_name_match.end()]

    # 开始检测规则
    while True:
        if define_name[0:4] != "CIT_":
            error_message.append(
                ErrorReport(
                    line=FileContext.current_line,
                    message=DEFINE_BEGIN_PREFIX_MUST_BE_CIT,
                    error_context=define_name
                )
            )
            break

        for c in define_name:
            if c.isalpha():
                if not c.isupper():
                    error_message.append(
                        ErrorReport(
                            line=FileContext.current_line,
                            message=DEFINE_MUST_BE_UPPER,
                            error_context=define_name
                        )
                    )
                    break
        break

    start_pos = match.end()
    while True:
        next_line_break = next_line_break_pos(parser_string, start_pos)
        if next_line_break == -1:
            next_line_break = len(parser_string)-1
            break

        end_postfix = parser_string[next_line_break-1]
        if end_postfix == '\\':
            start_pos = next_line_break+1
        else:
            break

    return match.start(), next_line_break, error_message


def match_and_check_enum(parser_string, start_pos):
    """
    从start_pos开始,找到枚举相关的字符串, 并且检测错误
    :param parser_string: 分析的字符串
    :param start_pos: 开始的位置
    :return: 如果找到，则返回enum的起始和结束位置，并且报告错误的list()，否则返回-1, -1, []
    """
    error_message = list()

    match = enum_stat_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1, error_message

    if FileContext.current_parser_context == FileContext.PARSER_TYPE_FILE:
        error_message.append(ErrorReport(line=FileContext.current_line,
                                         message=ENUM_USE_CIT_BEGIN_ENUM))

    return match.start(), match.end()-1, error_message


def match_and_check_include(parser_string, start_pos):
    """
    检测include的顺序
    :param parser_string:
    :param start_pos:
    :return: start_pos, end_pos, error_message
    """
    error_message = list()

    while True:
        # 检测include系统库，如果之前已经include 自己的库，则会报错
        match = system_include_regex.match(parser_string, start_pos)
        if match:
            if FileContext.include_system_end:
                error_message.append(
                    ErrorReport(
                        line=FileContext.current_line,
                        message=SYSTEM_INCLUDE_AFTER_SELF_INCLUDE,
                        error_context=parser_string[match.start(): match.end()]
                    )
                )
            break

        # 检测是否include自己的库，如果已经include，并且不是文件自己的库，在会设置标志位
        match = self_include_regex.match(parser_string, start_pos)
        if match is None:
            return -1, -1, error_message

        include_file_name = match.groupdict().get("include_name")
        if include_file_name.find(".") != -1:
            include_name, include_ext = os.path.splitext(include_file_name)
        else:
            include_name = include_file_name

        if FileContext.current_file_name.find(".") != -1:
            current_file_name, current_file_ext = os.path.splitext(FileContext.current_file_name)
        else:
            current_file_name = FileContext.current_file_name

        if current_file_name.lower() == include_name.lower():
            break
        FileContext.include_system_end = True
        break

    return match.start(), match.end()-1, error_message


def match_while_stat(parser_string, start_pos):
    """
    从start_pos开始检测,是否符合while语句的语法，如果符合，则返回整个while语句的作用域(指的是{}这个里面，或者while语句的下一句)
    :param parser_string: 需要解析的语句
    :param start_pos: 开始的位置,
    :return: stat_start, stat_end, 如果没有匹配，则都返回-1
    """
    match = while_stat_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1

    token_parser = TokenParser(parser_string, match.end()-1)
    token_parser.next_token()
    if token_parser.current_token() == "{":
        end_while_pos = find_token_pair_by_pos(parser_string, token_parser.current_token_end_pos()-1, "{")
    else:
        end_while_pos = parser_string.find(";", match.end())

    return match.start(), end_while_pos


def match_prec_stat(parser_string, start_pos):
    """
    匹配#ifdef #endi #if等预编译指令
    :param parser_string:
    :param start_pos:
    :return: stat_start, stat_end, 语句开始和结束的位置，如果没有的话，则返回-1, -1
    """
    ifdef_regex = re.compile("#ifdef")
    endif_regex = re.compile("#endif")
    if_regex = re.compile("#if")

    while True:
        match = ifdef_regex.match(parser_string, start_pos)
        if match:
            break

        match = endif_regex.match(parser_string, start_pos)
        if match:
            break

        match = if_regex.match(parser_string, start_pos)
        if match:
            break

        return -1, -1

    end_pos = next_line_break_pos(parser_string, match.end())
    return match.start(), end_pos


def match_do_while_stat(parser_string, start_pos):
    """
    从start_pos开始检测,是否符合do..while语句的语法，
    如果符合，
    则返回整个do..while语句的作用域(指的是{}这个里面，或者if语句的下一句)
    :param parser_string: 需要解析的语句
    :param start_pos: 开始的位置,
    :return: stat_start, stat_end, 如果没有匹配，则都返回-1
    """
    match = do_while_stat_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1

    token_parser = TokenParser(parser_string, match.end()-1)
    token_parser.next_token()

    assert token_parser.current_token() == "{"
    do_while_end_pos = find_token_pair_by_pos(parser_string, token_parser.current_token_end_pos()-1, "{")
    assert parser_string[do_while_end_pos] == "}"

    token_parser = TokenParser(parser_string, do_while_end_pos+1)
    token_parser.next_token()
    assert token_parser.current_token() == "while"

    do_while_end_pos = parser_string.find(";", do_while_end_pos+1)

    return match.start(), do_while_end_pos


def match_for_stat(parser_string, start_pos):
    """
    从start_pos开始检测,是否符合for语句的语法，如果符合，则返回整个for语句的作用域(指的是{}这个里面，或者if语句的下一句)
    :param parser_string: 需要解析的语句
    :param start_pos: 开始的位置,
    :return: stat_start, stat_end, 如果没有匹配，则都返回-1
    """
    match = for_stat_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1

    token_parser = TokenParser(parser_string, match.end()-1)
    token_parser.next_token()
    if token_parser.current_token() == "{":
        pos = find_token_pair_by_pos(parser_string, token_parser.current_token_end_pos()-1, "{")
        assert pos != -1
        return match.start(), pos
    else:
        pos = parser_string.find(";", match.end())
        assert pos != -1
    return match.start(), pos


def match_if_stat(parser_string, start_pos):
    """
    从start_pos开始检测,是否符合if语句的语法，如果符合，则返回整个if语句的作用域(指的是{}这个里面，或者if语句的下一句)
    :param parser_string: 需要解析的语句
    :param start_pos: 开始的位置,
    :return: stat_start, stat_end, 如果没有匹配，则都返回-1
    """
    match = if_stat_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1

    body_begin_pos = find_token_pair_by_pos(parser_string, match.end()-1, "(")
    assert body_begin_pos != -1

    token_parser = TokenParser(parser_string, body_begin_pos+1)
    token_parser.next_token()
    if token_parser.current_token() == "{":
        if_stat_end_pos = find_token_pair_by_pos(parser_string, token_parser.current_token_end_pos() - 1, "{")
        assert if_stat_end_pos != -1
    else:
        if_stat_end_pos = parser_string.find(";", match.end())

    """
    解析else if等
    """
    while True:
        token_parser = TokenParser(parser_string, if_stat_end_pos+1)
        token_parser.next_token()
        if token_parser.current_token() == "else":
            token_parser.next_token()
            if token_parser.current_token() == "if":
                token_parser.next_token()
                assert token_parser.current_token() == "("
                condition_end = find_token_pair_by_pos(parser_string,
                                                       token_parser.current_token_end_pos()-1,
                                                       "(")
                token_parser = TokenParser(parser_string, condition_end+1)
                token_parser.next_token()

            if token_parser.current_token() == "{":
                if_stat_end_pos = find_token_pair_by_pos(parser_string, token_parser.current_token_end_pos() - 1, "{")
                assert if_stat_end_pos != -1
            else:
                if_stat_end_pos = parser_string.find(";", token_parser.current_token_end_pos())
        else:
            break

    return match.start(), if_stat_end_pos


def helper_match_and_check(all_error_message, parser_string, start_pos, match_and_check_func):
    """
    检测语法规则的辅助函数
    :param all_error_message:        所有的错误，调用match_and_check_func后有错误，则会添加到这里面
    :param start_pos:                开始的位置
    :param match_and_check_func:    检测的函数
    :param parser_string:           解析的数据
    :return: start_pos, is_continue 所有的错误，下一次起始的位置, 是否continue
    """
    match_start_pos, match_end_pos, error_message = match_and_check_func(parser_string, start_pos)
    if match_start_pos != -1:
        start_pos = match_end_pos+1
        if len(error_message):
            all_error_message.extend(error_message)
        return start_pos, True

    return start_pos, False


def match_and_check(parser_string, start_pos):
    """
    检测语法规则
    :param parser_string: 解析的数据
    :param start_pos: 起始位置
    :return: error_message  解析出来的异常信息
    """
    all_error_message = list()
    old_pos = start_pos-1
    while True:
        start_pos = next_token_pos_not_space(parser_string, start_pos)
        if start_pos == -1:
            break
        assert start_pos > old_pos
        old_pos = start_pos
        FileContext.current_line = parser_string.count("\n", 0, start_pos+1)

        if start_pos == -1:
            break

        start_pos, is_continue = helper_match_and_check(all_error_message,
                                                        parser_string,
                                                        start_pos,
                                                        match_and_check_define)
        if is_continue:
            continue

        start_pos, is_continue = helper_match_and_check(all_error_message,
                                                        parser_string,
                                                        start_pos,
                                                        match_and_check_enum)
        if is_continue:
            continue

        start_pos, is_continue = helper_match_and_check(all_error_message,
                                                        parser_string,
                                                        start_pos,
                                                        match_and_check_include)
        if is_continue:
            continue

        start_pos, is_continue = helper_match_and_check(all_error_message,
                                                        parser_string,
                                                        start_pos,
                                                        match_and_check_typedef)
        if is_continue:
            continue

        start_pos, is_continue = helper_match_and_check(all_error_message,
                                                        parser_string,
                                                        start_pos,
                                                        match_and_check_class)
        if is_continue:
            continue

        start_pos, is_continue = helper_match_and_check(all_error_message,
                                                        parser_string,
                                                        start_pos,
                                                        match_and_check_class_impl)

        if is_continue:
            continue

        # 预处理的语句直接跳到下一行去，不进行处理
        prec_start_pos, prec_end_pos = match_prec_stat(parser_string, start_pos)
        if prec_start_pos != -1:
            start_pos = prec_end_pos+1
            continue

        # using namespace 直接跳过
        using_start_pos, using_end_pos = match_using_namespace(parser_string, start_pos)
        if using_start_pos != -1:
            start_pos = using_end_pos+1
            continue

        struct_start_pos, struct_end_pos = match_struct(parser_string, start_pos)
        if struct_start_pos != -1:
            start_pos = struct_end_pos+1
            continue

        start_pos, is_continue = helper_match_and_check(all_error_message,
                                                        parser_string,
                                                        start_pos,
                                                        match_and_check_function)
        if is_continue:
            continue

        start_pos, is_continue = helper_match_and_check(all_error_message,
                                                        parser_string,
                                                        start_pos,
                                                        match_and_check_var)
        if is_continue:
            continue

        start_pos = next_line_break_pos(parser_string, start_pos)
        if len(parser_string) <= start_pos:
            break

    return all_error_message


def match_struct(parser_string, start_pos):
    """
    解析struct语句
    :param parser_string:
    :param start_pos:
    :return: stat_start, stat_end
    """
    match = struct_regex.match(parser_string, start_pos)
    if match is None:
        return -1, -1

    assert parser_string[match.end()-1] == "{"
    struct_end_pos = find_token_pair_by_pos(parser_string, match.end()-1, "{")
    assert struct_end_pos != -1
    struct_end_pos = parser_string.find(";", struct_end_pos+1)
    assert parser_string[struct_end_pos] == ";"
    return match.start(), struct_end_pos


def peek_scope_vars(function_context):
    """
    解析function_context下的所有分析后的变量声明, 不会对function_context进行修改
    read_scope_var则会对数据进行修改(read_scope_var已经被废弃，尽量不要使用)
    :param function_context:
    :return: 返回所有解析出来的变量
    """

    scope_vars = list()
    assert isinstance(function_context, FunctionContext)
    context = function_context.function_impl
    not_space = re.compile(r"(\w)+")
    regex_start = 0
    while True:
        search = not_space.search(context, regex_start)       # 从1开始是为了去掉{符号
        if search is None:
            break

        if_start_pos, if_end_pos = match_if_stat(context, start_pos=search.start())
        if if_start_pos != -1:
            regex_start = if_end_pos+1
            continue

        del_start_pos, del_end_pos = match_delete_stat(context, start_pos=search.start())
        if del_start_pos != -1:
            regex_start = del_end_pos+1
            continue

        for_start_pos, for_end_pos = match_for_stat(context, start_pos=search.start())
        if for_start_pos != -1:
            assert context[for_end_pos] == "}"
            regex_start = for_end_pos+1
            continue

        stream_start_pos, stream_end_pos = match_stream_stat(context, start_pos=search.start())
        if stream_start_pos != -1:
            regex_start = stream_end_pos+1
            continue

        while_start_pos, while_end_pos = match_while_stat(context, start_pos=search.start())
        if while_start_pos != -1:
            regex_start = while_end_pos+1
            continue

        do_while_start_pos, do_while_end_pos = match_do_while_stat(context, start_pos=search.start())
        if do_while_start_pos != -1:
            regex_start = do_while_end_pos+1
            continue

        match = switch_stat_regex.match(context, search.start())
        if match:
            regex_start = find_token_pair_pos(context[match.end():], "{") + match.end()+1
            assert context[regex_start-1] == "}"
            continue

        match = return_stat_regex.match(context, search.start())  # return 语句略过不解析
        if match:
            regex_start = match.end()
            continue

        match = assign_regex.match(context, search.start())
        if match:
            # 获取=号前面的语句，然后进行解析
            for var_index in range(match.end()-1, match.start(), -1):
                c = context[var_index]
                if c is not "=" \
                        and c is not "+"\
                        and c is not "-"\
                        and c is not "*"\
                        and c is not "/"\
                        and c is not " ":
                    break

            left_op = context[match.start():var_index+1]
            if var_regex.match(left_op):
                var_context = VarContext()
                var_context.var_str = context[match.start(): var_index+1]
                scope_vars.append(var_context)

            regex_start = context.find(";", match.end())+1
            continue

        match = function_regex.match(context, search.start())
        if match:
            regex_start = context.find(";", match.end())+1
            continue

        match = var_regex.match(context, search.start())
        if match:
            end_token = context.find(";", match.end())
            if end_token is not -1:
                var_context = VarContext()
                var_context.var_str = context[match.start():end_token+1]
                scope_vars.append(var_context)
                regex_start = end_token+1
                continue

        # 如果没有找到合适的解析的，则跳过
        end = context.find(";", search.end())
        if end == -1:
            break
        regex_start = end+1

    return scope_vars


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


def remove_key(parser_string, key):
    """
    删除指定的关键字
    :param parser_string:
    :param key:
    :return:
    """
    key_regex = re.compile(r"\s*("+key + ")\s+")
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
    删除会影响解析但是不关键的字，比如Q_OBJECT, public:, private:, protected:, unsigned等
    :param parser_string:
    :return: 返回处理后的字符
    """
    parser_string = remove_key(parser_string, r"unsigned")
    return parser_string


def remove_unnecessary_data(data):
    """
    删除不需要的数据
    :param data:
    :return: 解析后的数据
    """
    data = remove_comment(data)
    data = remove_unnecessary_key(data)
    return data


def read_file_data(file_path):
    """
    读取文件解析出来的语句, 将会去除多余的文件
    :param file_path: 文件的路径
    :return:  返回去掉不需要的关键字后的数据
    """
    with open(file_path, mode="r", encoding="gb2312") as fp:
        fp.seek(0, 2)
        length = fp.tell()
        fp.seek(0, 0)
        data = fp.read(length)
        data = remove_unnecessary_data(data)
    return data


def check_file(file_path):
    """
    解析文件的规则
    :param file_path: 文件路径
    :return: rule 有检测出错误,返回检测出的结果
             None 没有检测出错误
    """
    try:
        FileContext.current_file_name = os.path.basename(file_path)
        data = read_file_data(file_path)
        match_and_check_result = match_and_check(data, 0)
        for rule in match_and_check_result:
            rule.file_full_path = os.path.abspath(file_path)

        return match_and_check_result
    finally:
        FileContext.include_system_end = False

    return None


def check_pointer_and_ref(var_context):
    """
    检测变量类型的*和&修饰符
    :param var_context: VarContext结构体
    :return: 如果有问题，在返回错误，没有则返回None
    """
    pointer_pos = var_context.var_str.find("*")
    if pointer_pos != -1:
        if var_context.var_str[pointer_pos-1] == " ":
            return POINT_OR_REF_NEAR_TYPE

    ref_pos = var_context.var_str.find("&")
    if ref_pos != -1:
        if var_context.var_str[ref_pos-1] == " ":
            return POINT_OR_REF_NEAR_TYPE

    return None


def count_rule(rules):
    rule_count = 1
    if isinstance(rules, list) or isinstance(rules, tuple):
        for rule in rules:
            rule_count += count_rule(rule)
    elif isinstance(rules, dict):
        for rule in rules:
            rule_count += count_rule(rule)
    return rule_count


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
            if file.endswith(".h") or file.endswith(".cpp"):
                try:
                    print("解析文件"+file)
                    check_rule = check_file(root + '/' + file)
                    if check_rule:
                        error_message.append({file: check_rule})
                except UnicodeDecodeError as e:
                    print("解析"+file+"文件编码错误:" + str(e))
                except AssertionError as e:
                    print("解析"+file+"文件有断言")

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

    count = count_rule(check_result)
    for rule in check_result:
        print(rule)


