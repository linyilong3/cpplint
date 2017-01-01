import cppLint
import unittest
import os


class CppLintTest(unittest.TestCase):
    def test_find_token_pair(self):
        test_string = "{hello world}"
        pos = cppLint.find_token_pair_pos(test_string[1:], "{")
        self.assertEqual(pos+1, len(test_string)-1)

    def test_remove_key(self):
        var_declare = " int m_pTNum;";
        test_string = r"unsigned" + var_declare
        test_string = cppLint.remove_unnecessary_data(test_string)
        self.assertEqual(len(test_string), len(var_declare))

        test_string = r"\t\tunsigned"+var_declare
        test_string = cppLint.remove_unnecessary_data(test_string)
        self.assertEqual(len(test_string), len(r"\t\t"+var_declare))

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

        test_string = "/*citCheckBox* checks[],*/" \
                      "kkkjie" \
                      "/*int*/"
        test_string = cppLint.remove_comment(test_string)
        self.assertEqual(len(test_string), len("kkkjie"))

    def test_match_var(self):
        match = cppLint.var_regex.match("m_sProcess = new QProcess();")
        self.assertIsNone(match)

        match = cppLint.var_regex.match("switch(type)")
        self.assertIsNone(match)

        match = cppLint.var_regex.match("static map<string, string>* m_pThemes;\n")
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("var_name"), "m_pThemes")

        match = cppLint.var_regex.match("static map<string, string> *m_pThemes;\n")
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("var_name"), "m_pThemes")

        match = cppLint.var_regex.match("const char *g_p = nullptr;")
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("var_name"), "g_p")

    def test_match_and_check_assign(self):
        test_string = "const char *g_p = nullptr;"
        start_pos, end_pos, error_message = cppLint.match_and_check("const char *g_p = nullptr;")
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(test_string))
        self.assertEqual(len(error_message), 1)
        self.assertEqual(error_message[0].message, cppLint.POINT_OR_REF_NEAR_TYPE)


    def test_match_emit(self):
        match = cppLint.emit_stat_regex.match("citAlarmDecoder* l_pDecoder = NULL;")
        self.assertIsNone(match)

        match = cppLint.emit_stat_regex.match("switch(type)")
        self.assertIsNone(match)

    def test_check_vars(self):
        test_string = "static map<string, string>* m_pThemes;\n"
        error = cppLint.check_class_member_var(test_string)
        self.assertIsNone(error)

        test_string = "static map<string, string>* m_pThemes;\n"
        error = cppLint.check_class_member_var(test_string)
        self.assertIsNone(error)

        var_declare = "static std::map<std::string, std::string> *pThemes;"
        start_pos, end_pos, error = cppLint.match_and_check_var(var_declare, 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(var_declare)-1)
        self.assertEqual(len(error), 1)
        error_info = error[0].message
        self.assertIsNotNone(error_info)
        self.assertEqual(error_info, cppLint.STATIC_VAR_BEGIN_S)

        var_declare = "static std::map<std::string, std::string> *s_pThemes;"
        start_pos, end_pos, error = cppLint.match_and_check_var(var_declare, 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(var_declare)-1)
        self.assertEqual(len(error), 1)
        error_info = error[0].message
        self.assertIsNotNone(error_info)
        self.assertEqual(error_info, cppLint.POINT_OR_REF_NEAR_TYPE)

        var_declare = "std::map<std::string, std::string>* pThemes;"
        start_pos, end_pos, error = cppLint.match_and_check_var(var_declare, 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(var_declare)-1)
        self.assertEqual(len(error), 1)
        error_info = error[0].message
        self.assertIsNotNone(error_info)
        self.assertEqual(error_info, cppLint.GLOBAL_VAR_BEGIN_G)

        var_declare = "std::map<std::string, std::string>* g_pThemes;"
        start_pos, end_pos, error = cppLint.match_and_check_var(var_declare, 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(var_declare)-1)
        self.assertEqual(len(error), 0)

        var_declare = "const std::map<std::string, std::string>* g_pThemes;"
        start_pos, end_pos, error = cppLint.match_and_check_var(var_declare, 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(var_declare)-1)
        self.assertEqual(len(error), 0)

    def test_check_function_param(self):
        test_string = "void function(int a,int &b, const int b)"
        context = cppLint.FunctionContext()
        context.function_declare = test_string
        error = context.check_params()
        self.assertNotEqual(error, None)
        self.assertEqual(error, cppLint.FUNCTION_PARAM_MUST_BE_SPACE)

        test_string = "void function(int a,\n" \
                      "int &b)"
        context = cppLint.FunctionContext()
        context.function_declare = test_string
        error = context.check_params()
        self.assertEqual(error, None)

        test_string = "std::vector<std::string,QString> &function(const int &a,\n" \
                      "const std::map<std::vector<int>, int> b, const std::list<int> &b);"
        context = cppLint.FunctionContext()
        context.function_declare = test_string
        error = context.check_params()
        self.assertEqual(error, None)

        test_string = "void SaveState(QMap<QString,QVariant>& map)"
        context = cppLint.FunctionContext()
        context.function_declare = test_string
        error = context.check_params()
        self.assertEqual(error, None)

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
        self.assertEqual(match.groupdict().get("var_name"), "b[256]")

        test_string = r"char *p;"
        match = cppLint.var_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "char")
        self.assertEqual(match.groupdict().get("var_name"), "p")

        test_string = r"char *p[256];"
        match = cppLint.var_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "char")
        self.assertEqual(match.groupdict().get("var_name"), "p[256]")

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

        test_string = "static int s_usercount";
        match = cppLint.var_regex.search(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "int")

    def test_match_and_check_enum(self):
        enum_declare = "enum{\n" \
                       "a=12,\n" \
                       "b=Token,\n" \
                       "};\n"
        var_declare = "int a;"
        test_string = enum_declare + var_declare

        start_pos, end_pos, error_message = cppLint.match_and_check_enum(test_string, 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos+1, len(enum_declare)-1)
        self.assertEqual(test_string[start_pos:end_pos+1], enum_declare[0:len(enum_declare)-1])
        self.assertEqual(len(error_message), 1)
        error_info = error_message[0].get(enum_declare[start_pos:end_pos+1])
        self.assertIsNotNone(error_info)
        self.assertEqual(error_info, cppLint.ENUM_USE_CIT_BEGIN_ENUM)

    def test_operator_function(self):
        test_string = r"bool operator != (const citLatLon &latlon) const;"
        match = cppLint.operator_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"bool operator/(const citLatLon l);"
        match = cppLint.operator_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"citLatLon& operator = (const citLatLon &latlon);"
        match = cppLint.operator_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"int func(int argc, char *argc)"
        match = cppLint.operator_regex.match(test_string)
        self.assertIsNone(match)

        test_string = r"int func(int argc, char *argc)"
        match = cppLint.operator_regex.match(test_string)
        self.assertIsNone(match)
        pass

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

        test_string = r"bool operator == (const citLatLon &latlon) const;"
        match = cppLint.operator_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"QList<citWindFarm* > GetWindFarms(){ return m_WindFarms; }"
        match = cppLint.function_regex.match(test_string)
        self.assertIsNotNone(match)

    def test_class(self):
        test_string = r"class test2;" \
                      r"class test:public t," \
                      r"public t2" \
                      r"{" \
                      r"" \
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
                      "void exec(int argc,char *argv[])" \
                      "{" \
                      " int i = l_local;" \
                      " std::string s = joker;" \
                      " int i = l_l, l2;" \
                      " int l_dosome = 3;" \
                      "}" \
                      "void param(int argc,char *argv);" \
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
        self.assertEqual(len(cit_test_rule.get("function_rule")), 3)

        cit_hello_rule = error_msg["citHello"][0]
        self.assertIsNone(cit_hello_rule.get("class_rule"))
        self.assertEqual(len(cit_hello_rule.get("member_rule")), 4)
        self.assertIsNone(cit_hello_rule.get("function_rule"))

    def test_check_match_and_check_file(self):
        """
        file = "./test_data/AisKalmanFiltering.cpp"
        cppLint.FileContext.current_file_name = os.path.basename(file)
        data = cppLint.read_file_data(file)
        class_parser = cppLint.ClassParser()
        data = class_parser.read_body(data)
        error_message = cppLint.match_and_check(data, 0)
        self.assertEqual(len(error_message), 8)

        file = "./test_data/citElement.cpp"
        cppLint.FileContext.current_file_name = os.path.basename(file)
        data = cppLint.read_file_data(file)
        class_parser = cppLint.ClassParser()
        data = class_parser.read_body(data)
        error_message = cppLint.match_and_check(data, 0)
        """

    def test_file(self):
        file = "./test_data/AisKalmanFiltering.cpp"
        data = cppLint.read_file_data(file)
        class_parser = cppLint.ClassParser()
        data = class_parser.read_class_body(data)
        class_parser.parser()
        self.assertEqual(len(class_parser.class_contexts), 0)

        functions, data = cppLint.read_class_member_function_impl(data)
        self.assertEqual(len(functions), 7)

        scope_var = cppLint.peek_scope_vars(functions[0])
        self.assertEqual(len(scope_var), 0)

        scope_var = cppLint.peek_scope_vars(functions[2])
        self.assertEqual(len(scope_var), 5)

        scope_var = cppLint.peek_scope_vars(functions[3])
        self.assertEqual(len(scope_var), 3)

        scope_var = cppLint.peek_scope_vars(functions[4])
        self.assertEqual(len(scope_var), 0)

        file = "./test_data/citClientSocketMan.cpp"
        data = cppLint.read_file_data(file)
        class_parser = cppLint.ClassParser()
        data = class_parser.read_class_body(data)
        class_parser.parser()
        self.assertEqual(len(class_parser.class_contexts), 1)

        functions, data = cppLint.read_class_member_function_impl(data)
        self.assertEqual(len(functions), 169)

        scope_var = cppLint.peek_scope_vars(functions[0])
        self.assertEqual(len(scope_var), 2)

        scope_var = cppLint.peek_scope_vars(functions[1])
        self.assertEqual(len(scope_var), 0)

        scope_var = cppLint.peek_scope_vars(functions[168])
        self.assertEqual(len(scope_var), 1)

        scope_var = cppLint.peek_scope_vars(functions[3])
        self.assertEqual(len(scope_var), 1)

        scope_var = cppLint.peek_scope_vars(functions[81])
        self.assertEqual(len(scope_var), 1)

        rule = cppLint.check_function(functions[148])
        self.assertEqual(len(rule), 0)

        function_context = cppLint.FunctionContext()
        function_context.function_impl = "{l_stream << list;}"
        scope_var = cppLint.peek_scope_vars(function_context)
        self.assertEqual(len(scope_var), 0)

        function_context = cppLint.FunctionContext()
        function_context.function_impl = "{l_filters << \"*.cts\";}"
        scope_var = cppLint.peek_scope_vars(function_context)
        self.assertEqual(len(scope_var), 0)

        function_context = cppLint.FunctionContext()
        function_context.function_impl = "for (int i = 0; i < citTwowayFairwayStyleBTN::citFairwayStyleNum; i++)" \
                                         "{" \
                                         "m_pStylePushBTNs[i] = new citPushButton(this, "", i, " \
                                         "tr(citFairwayInfoWidget_TwowayFairwayStyleBTN_TEXT[i]));" \
                                         "}"

        scope_var = cppLint.peek_scope_vars(function_context)
        self.assertEqual(len(scope_var), 0)

        file = "./test_data/citTwowayFairwayInfoWidget.cpp"
        data = cppLint.read_file_data(file)
        parser = cppLint.ClassParser()
        data = parser.read_body(data)
        parser.parser()
        error_message = parser.check_rule()
        self.assertEqual(len(error_message), 0)

        file = "./test_data/citUserCreateWidget.cpp"
        data = cppLint.read_file_data(file)
        parser = cppLint.ClassParser()
        data = parser.read_body(data)
        parser.parser()
        error_message = parser.check_rule()
        self.assertEqual(len(error_message), 1)

        file = "./test_data/citTargetMan.cpp"
        data = cppLint.read_file_data(file)
        parser = cppLint.ClassParser()
        data = parser.read_body(data)
        parser.parser()
        cppLint.check_function(parser.class_member_function[7])
        error_message = parser.check_rule()
        self.assertEqual(len(error_message), 0)

        file = "./test_data/citPrintWidget.cpp"
        data = cppLint.read_file_data(file)
        parser = cppLint.ClassParser()
        data = parser.read_body(data)
        parser.parser()
        cppLint.check_function(parser.class_member_function[6])
        error_message = parser.check_rule()
        self.assertEqual(len(error_message), 0)

        file = "./test_data/citChartLayerWidget.cpp"
        data = cppLint.read_file_data(file)
        parser = cppLint.ClassParser()
        data = parser.read_body(data)
        parser.parser()
        cppLint.check_function(parser.class_member_function[9])
        cppLint.check_function(parser.class_member_function[6])
        error_message = parser.check_rule()
        self.assertEqual(len(error_message), 0)

    def test_match_and_check_include(self):
        test_string = "#include <iostream>"
        match = cppLint.system_include_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("include_name"), "iostream")

        test_string = '#include "iostream"'
        match = cppLint.self_include_regex.match(test_string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("include_name"), "iostream")

        test_string = "#include <iostream>\n" \
                      '#include "iostream"\n' \
                      "#include <iostream>\n"

        cppLint.FileContext.include_system_end = False
        cppLint.FileContext.current_file_name = "iostream2"
        test_string_start_pos = 0
        start_pos, end_pos, error_message = cppLint.match_and_check_include(test_string, test_string_start_pos)
        test_string_start_pos = end_pos+2  # +2是为了跳过\n,本来应该+1
        start_pos, end_pos, error_message = cppLint.match_and_check_include(test_string, test_string_start_pos)
        self.assertEqual(cppLint.FileContext.include_system_end, True)
        test_string_start_pos = end_pos+2
        start_pos, end_pos, error_message = cppLint.match_and_check_include(test_string, test_string_start_pos)
        self.assertEqual(len(error_message), 1)

        test_string = "#include <iostream>\n" \
                      '#include "iostream"\n' \
                      "#include <iostream>\n"

        cppLint.FileContext.include_system_end = False
        cppLint.FileContext.current_file_name = "iostream"
        test_string_start_pos = 0
        start_pos, end_pos, error_message = cppLint.match_and_check_include(test_string, test_string_start_pos)
        test_string_start_pos = end_pos+2  # +2是为了跳过\n,本来应该+1
        start_pos, end_pos, error_message = cppLint.match_and_check_include(test_string, test_string_start_pos)
        self.assertEqual(cppLint.FileContext.include_system_end, False)
        test_string_start_pos = end_pos+2
        start_pos, end_pos, error_message = cppLint.match_and_check_include(test_string, test_string_start_pos)
        self.assertEqual(len(error_message), 0)

        cppLint.FileContext.include_system_end = False
        cppLint.FileContext.current_file_name = None

    def test_match_and_check_define(self):
        define_string = "#define MAX(A,B) a > b\n"
        dummy_string = "abc"
        test_string = define_string + dummy_string

        start_pos, end_pos, error_message = cppLint.match_and_check_define(test_string, 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(define_string)-1)
        self.assertEqual(len(error_message), 1)
        self.assertIsNotNone(error_message[0].get("MAX(A,B)"))
        self.assertEqual(error_message[0].get("MAX(A,B)"), cppLint.DEFINE_BEGIN_PREFIX_MUST_BE_CIT)

        define_string = "#define CIT_max(A,B) a > b\n"
        dummy_string = "abc"
        test_string = define_string + dummy_string

        start_pos, end_pos, error_message = cppLint.match_and_check_define(test_string, 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(define_string)-1)
        self.assertEqual(len(error_message), 1)
        self.assertIsNotNone(error_message[0].get("CIT_max(A,B)"))
        self.assertEqual(error_message[0].get("CIT_max(A,B)"), cppLint.DEFINE_MUST_BE_UPPER)

        define_string = "#define CIT_MAX(A,B) a > b\n"
        dummy_string = "abc"
        test_string = define_string + dummy_string

        start_pos, end_pos, error_message = cppLint.match_and_check_define(test_string, 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(define_string)-1)
        self.assertEqual(len(error_message), 0)

        define_string = "#define CIT_MAX(A,B) a > b\\\n"
        dummy_string = "abc"
        test_string = define_string + dummy_string

        start_pos, end_pos, error_message = cppLint.match_and_check_define(test_string, 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(test_string))
        self.assertEqual(len(error_message), 0)

    def test_friend_declare(self):
        test_string = "friend citDataStream& operator>>(citDataStream& in, citCSLoginInfo& obj);"
        match = cppLint.friend_declare_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = "citDataStream& operator>>(citDataStream& in, citCSLoginInfo& obj);"
        match = cppLint.friend_declare_regex.match(test_string)
        self.assertIsNone(match)

    def test_token_parser(self):
        test_string = r"enum Type{" \
                      r"A," \
                      r"B," \
                      r"};"
        token = cppLint.TokenParser(test_string, 0)

        self.assertEqual(token.current_token_end_pos(), 0)
        self.assertEqual(token.next_token(), "enum")
        self.assertEqual(token.current_token_end_pos(), 4)

        self.assertEqual(token.next_token(), "Type")
        self.assertEqual(token.next_token(), "{")
        self.assertEqual(token.next_token(), "A")
        self.assertEqual(token.next_token(), ",")
        self.assertEqual(token.next_token(), "B")
        self.assertEqual(token.next_token(), ",")
        self.assertEqual(token.next_token(), "}")
        self.assertEqual(token.next_token(), ";")

    def test_peek_function_vars(self):
        function_context = cppLint.FunctionContext()
        function_context.function_declare = "void function(int a,int b)"
        function_context.function_impl = "{" \
                                         "int j,a,c;"\
                                         "  int a = 12;" \
                                         "  int b = func();" \
                                         "  int stat[10] = {0};" \
                                         " int i;" \
                                         "  func->fun()" \
                                         "}"
        var_stat = cppLint.peek_scope_vars(function_context)
        self.assertEqual(len(var_stat), 5)

        function_context = cppLint.FunctionContext()
        function_context.function_declare = "void function(int a,int b)"
        function_context.function_impl = "{\n" \
                                         "  emit UpdateSimTarget(target);\n" \
                                         "}"
        var_stat = cppLint.peek_scope_vars(function_context)
        self.assertEqual(len(var_stat), 0)

        function_context = cppLint.FunctionContext()
        function_context.function_declare = "inline unsigned int Idx(unsigned int r, " \
                                            "unsigned int c, unsigned int row_len)"
        function_context.function_impl = "{\n" \
                                         "  i+=12;"\
                                         "  return c + r * row_len;" \
                                         "}"
        var_stat = cppLint.peek_scope_vars(function_context)
        self.assertEqual(len(var_stat), 0)
