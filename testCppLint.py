import cppLint
import unittest


class CppLintTest(unittest.TestCase):
    def test_find_token_pair(self):
        test_string = "{hello world}"
        pos = cppLint.find_token_pair_pos(test_string[1:], "{")
        self.assertEqual(pos+1, len(test_string)-1)

    def test_remove_comment(self):
        test_string = "// int i;hello\n" \
                      "int j;"

        test_string = cppLint.remove_comment(test_string)
        self.assertTrue(test_string[0] != "\n")
        self.assertEqual(len(test_string), len("int j;"))

        test_string = "/*citCheckBox* checks[],*/"
        test_string = cppLint.remove_comment(test_string)
        self.assertEqual(len(test_string), 0)

        test_string = "/*citCheckBox* checks[],*/" \
                      "//kkkjie\n" \
                      "int"

        test_string = cppLint.remove_comment(test_string)
        self.assertEqual(len(test_string), len("int"))

        test_string = "void SetCheckStateById(/*citCheckBox* checks[],*/ const QVector<int>& idList)"
        test_string = cppLint.remove_comment(test_string)
        self.assertEqual(len(test_string), len("void SetCheckStateById( const QVector<int>& idList)"))

    def test_construct(self):
        test_string = "test_construct();"
        match = cppLint.construct_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = "~test_destry();"
        match = cppLint.destroy_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = "int a(int b)"
        match = cppLint.construct_regex.match(test_string)
        self.assertIsNone(match)

        test_string = "virtual ~test_destroy();"
        match = cppLint.destroy_regex.match(test_string)
        self.assertIsNotNone(match)

    def test_var_regex(self):
        test_string = "int a;"
        match = cppLint.var_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "int")
        self.assertEqual(match.groupdict().get("var_name"), "a")

        test_string = r"int b[256], a, b;"
        match = cppLint.var_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "int")
        self.assertEqual(match.groupdict().get("var_name"), "b")

        test_string = r"char *p;"
        match = cppLint.var_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "char")
        self.assertEqual(match.groupdict().get("var_name"), "p")

        test_string = r"char *p[256];"
        match = cppLint.var_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "char")
        self.assertEqual(match.groupdict().get("var_name"), "p")

        test_string = r"static char *p;"
        match = cppLint.var_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.start(), 0)
        self.assertEqual(match.groupdict().get("type_name"), "char")
        self.assertEqual(match.groupdict().get("var_name"), "p")

        test_string = r"std::string p;"
        match = cppLint.var_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "std::string")
        self.assertEqual(match.groupdict().get("var_name"), "p")

        test_string = r"std::shared_ptr<int> p;"
        match = cppLint.var_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "std::shared_ptr")
        self.assertEqual(match.groupdict().get("template"), "<int>")
        self.assertEqual(match.groupdict().get("var_name"), "p")
        test_string = r"std::shared_ptr<std::string> p;"
        match = cppLint.var_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "std::shared_ptr")
        self.assertEqual(match.groupdict().get("var_name"), "p")
        self.assertEqual(match.groupdict().get("template"), "<std::string>")

        test_string = r"QSharedPtr<std::string> p;"
        match = cppLint.var_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "QSharedPtr")
        self.assertEqual(match.groupdict().get("var_name"), "p")
        self.assertEqual(match.groupdict().get("template"), "<std::string>")

        test_string = r"std::vector< std::vector<int> > s"
        match = cppLint.var_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "std::vector")
        self.assertEqual(match.groupdict().get("var_name"), "s")
        self.assertEqual(match.groupdict().get("template"), "< std::vector<int> >")

        test_string = r"std::vector<int> *p"
        match = cppLint.var_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "std::vector")
        self.assertEqual(match.groupdict().get("var_name"), "p")
        self.assertEqual(match.groupdict().get("template"), "<int>")

        test_string = r"map<QString, int> m"
        match = cppLint.var_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "map")
        self.assertEqual(match.groupdict().get("var_name"), "m")
        self.assertEqual(match.groupdict().get("template"), "<QString, int>")

        test_string = "static map<string, vector<QTranslator*>*>* m_pLanguages;"
        match = cppLint.var_regex.search(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "map")
        self.assertEqual(match.groupdict().get("var_name"), "m_pLanguages")
        self.assertEqual(match.groupdict().get("template"), "<string, vector<QTranslator*>*>")

    def test_function_regex(self):
        test_string = r"int func(int argc, char *argc)"
        match = cppLint.function_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"static int func(int argc, char *argc)"
        match = cppLint.function_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"int func(std::string &s);"
        match = cppLint.function_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"std::string func(std::string &s)"
        match = cppLint.function_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"std::vector<int> func(std::string &s)"
        match = cppLint.function_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"static std::vector<int> func(std::string &s)"
        match = cppLint.function_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"static vector<int*> *func(std::string &s)"
        match = cppLint.function_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"int *func(std::string &s);"
        match = cppLint.function_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"std::vector<int> *func(std::string &s)"
        match = cppLint.function_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"std::vector<int>* func(std::string &s)"
        match = cppLint.function_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"std::vector<int>*func(std::string &s)"
        match = cppLint.function_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"std::vector<int> &func(std::string &s)"
        match = cppLint.function_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"static vector<QTranslator*>* ReadAllTranslatorFile(string dir)"
        match = cppLint.function_regex.match(test_string)
        self.assertIsNotNone(match)

    def test_class(self):
        test_string = r"class test2;" \
                      r"class test:public t," \
                      r"public t2" \
                      r"{" \
                      r"};" \
                      r"class test2" \
                      r"{" \
                      r"};"

        parser = cppLint.ClassParser()
        test_string = parser.read_class_body(test_string)
        self.assertTrue(len(test_string) == 0)
        self.assertEqual(len(parser.class_contexts), 2)
        self.assertEqual(parser.class_contexts[0].class_name(), "test")

        test_string = r"class test:public t," \
                      r"public t2" \
                      r"{" \
                      r"};"

        parser = cppLint.ClassParser()
        test_string = parser.read_class_body(test_string)
        self.assertEqual(len(test_string), 0)
        self.assertEqual(len(parser.class_contexts), 1)

        test_string = "class citHello" \
                      "{" \
                      "public:" \
                      " int a;" \
                      " int *p;" \
                      " std::vector<int> p;" \
                      " std::vector<std::vector<int> > *p;" \
                      " std::vector<int> *get_vector(int argc, std::vector<int> &argv);" \
                      " void param(int argc, char *argv);" \
                      "};"

        parser = cppLint.ClassParser()
        test_string = parser.read_class_body(test_string)
        parser.parser()
        self.assertEqual(len(parser.class_contexts), 1)
        self.assertEqual(len(parser.class_contexts[0].functions), 2)
        self.assertEqual(len(parser.class_contexts[0].member_vars), 4)
        self.assertEqual(len(test_string), 0)

        test_string = r"class cittest:public protect, public d" \
                      r"{" \
                      r"public:" \
                      r"    int a;" \
                      r"    int b;" \
                      r"    char *p;" \
                      r"    int a[256];" \
                      r"    void param(int argc, char *argv);" \
                      r"protected:" \
                      r"    void _doParam(int argc,char *argv[]);" \
                      r"};"
        parser = cppLint.ClassParser()
        parser.read_class_body(test_string)
        parser.parser()

        test_string = "class citTest:public protect, public d" \
                      "{" \
                      "     Q_OBJECT " \
                      "public:" \
                      " int a;" \
                      " int b;" \
                      " char *p;" \
                      " int a[256];" \
                      "citTest()" \
                      "{" \
                      " int i;" \
                      "}" \
                      "~citTest()" \
                      "{" \
                      "}" \
                      "void exec(int argc, char *argv[])" \
                      "{" \
                      " int i = l_local;" \
                      " std::string s = joker;" \
                      " int i = l_l, l2;" \
                      " int l_dosome = 3;" \
                      "}" \
                      "void param(int argc, char *argv);" \
                      "virtual void param(int argc, char *argv);" \
                      "enum" \
                      "{" \
                      " TokenA," \
                      " TokenB," \
                      "};" \
                      "enum Type" \
                      "{" \
                      " tokenb," \
                      "};" \
                      "enum EnumDeclare;" \
                      "protected:" \
                      " void _doparam(int argc, char *argv[]);" \
                      "};" \
                      "class citHello" \
                      "{" \
                      "public:" \
                      " int a;" \
                      " int *p;" \
                      " std::vector<int> p;" \
                      " std::vector<std::vector<int> > *p;" \
                      " std::vector<int> *get_vector(int argc, std::vector<int> &argv);" \
                      " void param(int argc, char *argv);" \
                      "};"

        test_string = cppLint.remove_unnecessary_data(test_string)
        parser = cppLint.ClassParser()
        parser.read_class_body(test_string)
        parser.parser()
        self.assertEqual(len(parser.class_contexts), 2)

        self.assertEqual(len(parser.class_contexts[0].functions), 6)
        self.assertEqual(len(parser.class_contexts[0].member_vars), 4)
        self.assertEqual(len(parser.class_contexts[0].enums), 3)

        self.assertEqual(len(parser.class_contexts[1].functions), 2)
        self.assertEqual(len(parser.class_contexts[1].member_vars), 4)
        self.assertEqual(len(parser.class_contexts[1].enums), 0)

        error_msg = parser.check_rule()
        cit_test_rule = error_msg["citTest"][0]

        self.assertEqual(len(cit_test_rule.get("class_rule")), 1)
        self.assertEqual(len(cit_test_rule.get("member_rule")), 4)
        self.assertEqual(len(cit_test_rule.get("function_rule")), 2)

        cit_hello_rule = error_msg["citHello"][0]
        self.assertIsNone(cit_hello_rule.get("class_rule"))
        self.assertEqual(len(cit_hello_rule.get("member_rule")), 4)
        self.assertIsNone(cit_hello_rule.get("function_rule"))

    def test_friend_declare(self):
        test_string = "friend citDataStream& operator>>(citDataStream& in, citCSLoginInfo& obj);"
        match = cppLint.friend_declare_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = "citDataStream& operator>>(citDataStream& in, citCSLoginInfo& obj);"
        match = cppLint.friend_declare_regex.match(test_string)
        self.assertIsNone(match)

    def test_remove_friend_declare(self):
        test_string = "friend citDataStream& operator>>(citDataStream& in, citCSLoginInfo& obj);"
        test_string = cppLint.remove_friend_regex(test_string)
        self.assertEqual(len(test_string), 0)

        test_string = "friend citDataStream& operator>>(citDataStream& in, citCSLoginInfo& obj);\n"\
                      "friend citDataStream& operator>>(citDataStream& in, citCSLoginInfo& obj);\n"\
                      "void func(int a, int b);"
        test_string = cppLint.remove_friend_regex(test_string)
        self.assertTrue(len(test_string) > len("void func(int a, int b)"))

    def test_read_enum(self):
        test_string = "enum Type{\n" \
                      "A,\n" \
                      "B,\n" \
                      "};"

        enum_str, parser_string = cppLint.read_enum(test_string)
        self.assertEqual(len(enum_str), 1)
        self.assertEqual(len(enum_str[0]), len(test_string))

        test_string = "enum var;"
        enum_str, parser_string = cppLint.read_enum(test_string)
        self.assertEqual(len(enum_str), 1)
        self.assertEqual(len(enum_str[0]), len(test_string))

        test_string = "enum\n" \
                      "{" \
                      "a,\n" \
                      "b,\n" \
                      "};"
        enum_str, parser_string = cppLint.read_enum(test_string)
        self.assertEqual(len(enum_str), 1)
        self.assertEqual(len(enum_str[0]), len(test_string))

        test_string = "enum" \
                       "{" \
                       " TokenA," \
                       " TokenB," \
                       "};" \
                       "enum Type" \
                       "{" \
                       " tokenb," \
                       "};" \
                       "enum EnumDeclare;"

        enum_str, parser_string = cppLint.read_enum(test_string)
        self.assertEqual(len(enum_str), 3)

    def test_token_parser(self):
        test_string = r"enum Type{" \
                      r"A," \
                      r"B," \
                      r"};"
        token = cppLint.TokenParser(test_string, 0)

        self.assertEqual(token.current_pos(), 0)
        self.assertEqual(token.next_token(), "enum")
        self.assertEqual(token.current_pos(), 4)

        self.assertEqual(token.next_token(), "Type")
        self.assertEqual(token.next_token(), "{")
        self.assertEqual(token.next_token(), "A")
        self.assertEqual(token.next_token(), ",")
        self.assertEqual(token.next_token(), "B")
        self.assertEqual(token.next_token(), ",")
        self.assertEqual(token.next_token(), "}")
        self.assertEqual(token.next_token(), ";")



    def test_function_rule(self):
        pass
        '''
        test_string = "void SaveState(QMap<QString,QVariant>& map)"
        function_context = cppLint.FunctionContext()
        function_context.function_declare = test_string
        result = cppLint.check_function(function_context)
        self.assertIsNone(result)
        '''

