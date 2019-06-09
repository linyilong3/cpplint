### 每隔一段时间，通过windbg的umdh，输出指定程序的内存log，方便比较

import os
import time

log_path = r"./memory/"
umdh_path = r"umdh.exe"
monitor_processor = "citProcessor.exe"
interval_log = 3600        ## 记录的间隔，秒为单位
gflags = r"gflags.exe /i" + " " + monitor_processor + " +ust"

seq = 0     ## log文件的序号
os.system(gflags)
#print("set gflags")
while(True):
   log_file_name = "memory_log_" + str(seq)
   seq+=1
   umdh_command = umdh_path + " -pn:" + monitor_processor + " -f:" + log_path + log_file_name
   print(umdh_command)
   output = os.popen(umdh_command)
   print(output.read())
   time.sleep(interval_log)


