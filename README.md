# cpplint

cppLint: 检查语法是符合公司的语法
qssLint: 检查QSS是否符合规则
autoexp.dat: VS下QT的代码提示，补充了VS调试无法查看部分QT内存结构体的问题
windbg_memory_check.py: 定时调用WINDBG的umdh,用以保存内存状态，方便排查内存泄露问题
vldprof: 比较vld的内存报告输出，方便查找在此期间内存的增长率(已经没什么用了，建议使用UMDH或者VS2017自带的内存分析工具)
