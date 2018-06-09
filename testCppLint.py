import cppLint
import unittest
import os


class CppLintTest(unittest.TestCase):
    def test_remove_key(self):
        var_declare = " int m_pTNum;"
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
        self.assertTrue(test_string[0] == "\n")
        self.assertEqual(len(test_string), len("\nint j;"))

        test_string = "/*citCheckBox* checks[],*/"
        test_string = cppLint.remove_comment(test_string)
        self.assertEqual(len(test_string), 0)

        test_string = "/*citCheckBox* checks[],*/\n" \
                      "//kkkjie\n" \
                      "int"

        test_string = cppLint.remove_comment(test_string)
        self.assertEqual(len(test_string), len("\n\nint"))

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

        match = cppLint.var_regex.match("struct cpplint *s;")
        self.assertIsNotNone(match)

        match = cppLint.var_regex.match("static const struct cpplint *s;")
        self.assertIsNotNone(match)

        match = cppLint.var_regex.match("long long a;")
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict().get("type_name"), "long long")
        self.assertEqual(match.groupdict().get("var_name"), "a")

        match = cppLint.var_regex.match("static const long long a;")
        self.assertIsNotNone(match)

        match = cppLint.var_regex.match("long long l_len = "
                                        "l_pRender->m_pCurrent->m_width*l_pRender->m_pCurrent->m_height;")
        self.assertIsNotNone(match)

    def test_match_function_call(self):
        test_string = "CIT_ELM_COL_PRO_BEGIN(citOnewayFairway)"
        match = cppLint.function_call_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = "int func(int a, int b);"
        match = cppLint.function_call_regex.match(test_string)
        self.assertIsNone(match)

        test_string = "foreach(QFileInfo fileInfo, fileInfoList)"
        match = cppLint.function_call_regex.match(test_string)
        self.assertIsNotNone(match)

    def test_match_construct_from_decl(self):
        test_string = "citObjectTypeInfo(){};"
        match = cppLint.construct_decl_begin_regex.match(test_string)
        self.assertIsNotNone(match)

    def test_match_and_check_class(self):
        test_string = "class citObjectTypeInfo" \
                      "{"                       \
                      "public:" \
                      "     citObjectTypeInfo() {};" \
                      "     virtual ~citObjectTypeInfo() {};" \
                      "public:" \
                      "     QString m_name;" \
                      "     QString m_info;" \
                      "};"
        start_pos, end_pos, error_message = cppLint.match_and_check_class(test_string, 0)
        self.assertEqual(len(error_message), 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(test_string)-1)

        test_string = "class citObjectTypeInfo" \
                      "{"                       \
                      "public:" \
                      "     citObjectTypeInfo() {}" \
                      "     virtual ~citObjectTypeInfo() {}" \
                      "public:" \
                      "     QString m_name;" \
                      "     QString m_info;" \
                      "};"
        start_pos, end_pos, error_message = cppLint.match_and_check_class(test_string, 0)
        self.assertEqual(len(error_message), 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(test_string)-1)

        test_string = "class citObjectTypeInfo" \
                      "{"                       \
                      "public:" \
                      "     citObjectTypeInfo();" \
                      "     virtual ~citObjectTypeInfo();" \
                      "public:" \
                      "     QString m_name;" \
                      "     QString m_info;" \
                      "};"
        start_pos, end_pos, error_message = cppLint.match_and_check_class(test_string, 0)
        self.assertEqual(len(error_message), 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(test_string)-1)

    def test_foreach_stat(self):
        test_string = "foreach(QFileInfo fileInfo, fileInfoList){}"
        start_pos, end_pos = cppLint.match_foreach_stat(test_string, 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(test_string)-1)

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
        self.assertEqual(len(error), 2)

        var_declare = "const std::map<std::string, std::string>* g_pThemes;"
        start_pos, end_pos, error = cppLint.match_and_check_var(var_declare, 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(var_declare)-1)
        self.assertEqual(len(error), 2)

    def test_match_static_class_member_init(self):
        test_string = "std::string class::member_name s = 12;"
        match = cppLint.class_static_init_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = "std::string s = 12;"
        match = cppLint.class_static_init_regex.match(test_string)
        self.assertIsNone(match)

        test_string = "std::string* class::memeber_name s = 12;"
        match = cppLint.class_static_init_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = "bool citMainWidget::m_sCompletePreheat = false;"
        match = cppLint.class_static_init_regex.match(test_string)
        self.assertIsNotNone(match)

        error_message = cppLint.match_and_check(test_string, 0)
        self.assertEqual(len(error_message), 0)

    def test_class_member_impl(self):
        test_string = r"citLatLon& citLatLon::operator=(const citLatLon &latlon)"
        match = cppLint.class_member_impl_begin_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"citLatLon& citLatLon::citLatLon(const citLatLon &latlon)"
        match = cppLint.class_member_impl_begin_regex.match(test_string)
        self.assertIsNotNone(match)

        test_string = r"int func(int argc, char *argv)"
        match = cppLint.class_member_impl_begin_regex.match(test_string)
        self.assertIsNone(match)

    def test_match_and_function_impl(self):
        test_string = "citLatLon& citLatLon::operator=(const citLatLon& lat)\n\
                       {\n" \
                        "return *this;" \
                       "}"

        match = cppLint.match_and_check_class_impl(test_string, 0)
        self.assertEqual(len(match[2]), 0)

        test_string = "citLatLon& citLatLon::operator=(const citLatLon& lat)\n\
                           {\n" \
                      "int i;" \
                      "}"

        match = cppLint.match_and_check_class_impl(test_string, 0)
        self.assertEqual(len(match[2]), 1)

        test_string = "citLatLon& citLatLon::operator==(const citLatLon& lat)\n\
                       {\n" \
                      "int i;" \
                      "}"

        match = cppLint.match_and_check_class_impl(test_string, 0)
        self.assertEqual(len(match[2]), 1)

        test_string = "CIT_BEGIN_ENUM(citReplayType)"
        match = cppLint.function_regex.match(test_string, 0)
        self.assertIsNone(match)

    def test_match_and_check_function(self):
        test_string = "void citGlowRenderObj::OnGetRender(citGlowRenderStructglow)\
        {\
            QByteArray l_byte;\
            long long l_len = l_pRender->m_pCurrent->m_width * l_pRender->m_pCurrent->m_height;\
        }"

        start_pos, end_pos, error_message = cppLint.match_and_check_class_impl(test_string, 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(test_string)-1)
        self.assertEqual(len(error_message), 0)

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
        error_info = error_message[0]
        self.assertIsNotNone(error_info)
        self.assertEqual(error_info.message, cppLint.ENUM_USE_CIT_BEGIN_ENUM)

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
        result = cppLint.check_file(file)

        file = "./test_data/citClientSocketMan.cpp"
        result = cppLint.check_file(file)

        file = "./test_data/citTwowayFairwayInfoWidget.cpp"
        result = cppLint.check_file(file)

        file = "./test_data/citUserCreateWidget.cpp"
        result = cppLint.check_file(file)

        file = "./test_data/citTargetMan.cpp"
        result = cppLint.check_file(file)

        file = "./test_data/citPrintWidget.cpp"
        result = cppLint.check_file(file)

        file = "./test_data/citChartLayerWidget.cpp"
        result = cppLint.check_file(file)

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
        self.assertIsNotNone(error_message[0].error_context == "MAX(A,B)")
        self.assertEqual(error_message[0].message, cppLint.DEFINE_BEGIN_PREFIX_MUST_BE_CIT)

        define_string = "#define CIT_max(A,B) a > b\n"
        dummy_string = "abc"
        test_string = define_string + dummy_string

        start_pos, end_pos, error_message = cppLint.match_and_check_define(test_string, 0)
        self.assertEqual(start_pos, 0)
        self.assertEqual(end_pos, len(define_string)-1)
        self.assertEqual(len(error_message), 1)
        self.assertIsNotNone(error_message[0].error_context == "CIT_max(A,B)" )
        self.assertEqual(error_message[0].message, cppLint.DEFINE_MUST_BE_UPPER)

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

        define_string = "#define CIT_MAX(a, b) a > b"
        start_pos, end_pos, error_message = cppLint.match_and_check_define(define_string, 0)
        self.assertEqual(start_pos, 0)
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

    def test_raw_pointor(self):
        test_string = "int l_aa = ccc * ddd;\n"
        error = cppLint.check_raw_pointer(test_string)
        self.assertIsNone(error)

        test_string = "citMultiFunAlarm* l_pAlarm = (citMultiFunAlarm*)m_pAlarm;\n"
        error = cppLint.check_raw_pointer(test_string)
        self.assertIsNotNone(error)

        test_string = "int l_pAlarm = (citMultiFunAlarm*)m_pAlarm;\n"
        error = cppLint.check_raw_pointer(test_string)
        self.assertIsNone(error)

    def test_c_array(self):
        test_string = "int g_array[4] = {0};\n"
        error_info, var_str = cppLint.check_raw_array(test_string, 0)
        self.assertIsNotNone(error_info)

        test_string = "int g_array[] = {0,1,2};\n"
        error_info, var_str = cppLint.check_raw_array(test_string, 0)
        self.assertIsNotNone(error_info)

        test_string = "int l_pAlarm = str[0];\n"
        error_info, var_str = cppLint.check_raw_array(test_string, 0)
        self.assertIsNone(error_info)

    def test_c_cast(self):
        test_string = "a = ( i_nt * ) _aa;\n"
        error_info, var_str = cppLint.check_C_cast(test_string, 0)
        self.assertIsNotNone(error_info)

        test_string = "void* l_pNewWindow = new citChartWindow((QWidget*)l_pMainWidget->m_pCanvasContainer);\n"
        error_info, var_str = cppLint.check_C_cast(test_string, 0)
        self.assertIsNotNone(error_info)

        test_string = "m_pChartMan->SetDisPlayMode((hqzDisPlayMode)m_displayConfig->m_disPlayMode);\n"
        error_info, var_str = cppLint.check_C_cast(test_string, 0)
        self.assertIsNotNone(error_info)

        test_string = "connect(l_pMes, SIGNAL(ReceiveDataSignal(citBaseMes*)), m_pClientSocketMan, SLOT(OnHeartBeat(citBaseMes*)));\n"
        error_info, var_str = cppLint.check_C_cast(test_string, 0)
        self.assertIsNone(error_info)

        test_string = "void UpdateEllipseSignal(citAlarmObjInfo *);\n"
        error_info, var_str = cppLint.check_C_cast(test_string, 0)
        self.assertIsNone(error_info)

        def test_memcpy_memset(self):
            test_string = "memset(&pRender->m_pCurrent->m_pBuff[StartPos], col, pRender->m_Xmax[i]-pRender->m_Xmin[i]);\n"
            error_info, var_str = cppLint.check_memset_memcpy(test_string, 0)
            self.assertIsNotNone(error_info)

            test_string = "memcpy(l_pGetCountInfo->szCoding, DepId,strlen(DepId));\n"
            error_info, var_str = cppLint.check_memset_memcpy(test_string, 0)
            self.assertIsNotNone(error_info)

            test_string = "memset_s(&pRender->m_pCurrent->m_pBuff[StartPos], col, pRender->m_Xmax[i]-pRender->m_Xmin[i]);\n"
            error_info, var_str = cppLint.check_memset_memcpy(test_string, 0)
            self.assertIsNone(error_info)

            test_string = "memcpy_s(l_pGetCountInfo->szCoding, DepId,strlen(DepId));\n"
            error_info, var_str = cppLint.check_memset_memcpy(test_string, 0)
            self.assertIsNone(error_info)

        def test_std_container(self):
            test_string = "std::string l_str = str;\n"
            error_info = cppLint.check_std_container(test_string)
            self.assertIsNotNone(error_info)

            test_string = "std::vector l_vec = vector;\n"
            error_info = cppLint.check_std_container(test_string)
            self.assertIsNotNone(error_info)

            test_string = "std::map l_map = vmap;\n"
            error_info = cppLint.check_std_container(test_string)
            self.assertIsNotNone(error_info)

            test_string = "std::array l_map = array;\n"
            error_info = cppLint.check_std_container(test_string)
            self.assertIsNotNone(error_info)