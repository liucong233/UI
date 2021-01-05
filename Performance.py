# -*- coding: utf-8 -*-
# author:liucong

# -*- coding: utf-8 -*-
# author:lcy

from core.MultiAdb import MultiAdb as Madb
import threading
from tools.Excel import *
from tools.Json import *
from tools.Screencap import *
from multiprocessing import Process, Value
import json
from collections import deque

'''
性能数据进程，首先根据storage_by_excel参数创建excel或json文件，再定期塞数据进去，最后统计各项的最大最小平均值。
'''


def enter_performance(madb, flag, start, storage_by_excel=True):
    print("设备{}进入enter_performance方法".format(madb.get_mdevice()))
    wb = ""
    jsonfilepath = ""
    if storage_by_excel:
        # 创表
        filepath, sheet, wb = create_log_excel(time.localtime(), madb.get_nickname())
        # 塞数据
        collect_data(madb, flag, storage_by_excel, sheet=sheet)
        # 计算各平均值最大值最小值等并塞数据
        avglist, maxlist, minlist = calculate(sheet)
        record_to_excel(sheet, avglist, color=(230, 230, 250))
        record_to_excel(sheet, maxlist, color=(193, 255, 193))
        record_to_excel(sheet, minlist, color=(240, 255, 240))
        wb.save()
    else:
        # 创建json文件
        jsonfilepath = create_log_json(time.localtime(), madb.get_nickname())
        print("创建json文件成功:{}".format(jsonfilepath))
        collect_data(madb, flag, storage_by_excel, jsonfilepath=jsonfilepath)
        calculate_by_json(jsonfilepath)
    nowtime = time.strftime("%H%M%S", start)
    reportpath = os.path.join(os.getcwd(), "Report")
    filename = reportpath + "\\" + madb.get_nickname() + "_" + str(nowtime) + ".html"
    print("要操作的文件名为：", filename)
    if storage_by_excel:
        reportPlusPath = EditReport(filename, storage_by_excel, avglist, maxlist, minlist, wb=wb)
    else:
        reportPlusPath = EditReport(filename, storage_by_excel, jsonfilepath=jsonfilepath)
    print("设备{}生成报告：{}完毕".format(madb.get_mdevice(), reportPlusPath))


# 接受设备madb类对象、excel的sheet对象、共享内存flag、默认延时一小时
def collect_data(madb, flag, storage_by_excel, sheet="", jsonfilepath="", timeout=3600):
    print("nowjsonfile=", jsonfilepath)
    starttime = time.time()
    dequelist = deque([])
    n = 0
    totalcpu, maxcpu = madb.get_totalcpu()
    try:
        while True:
            # 当执行一小时或flag为1时，跳出。
            # Performance.py可以单独执行，检查apk的性能，此时要把下面的flag.value注掉。因为这个是用于进程通信的，单独执行性能时没有必要。
            n += 1
            # 为了确保截取统计数据不出错，至少打印3行
            if (time.time() - starttime > timeout) or (flag.value == 1 and n > 3):
                break
            total = allocated = used = free = totalcpu = allocatedcpu = ""

            # 开启n个线程，每个线程去调用Madb类里的方法，获取adb的性能数据
            get_allocated_memory = MyThread(madb.get_allocated_memory, args=())
            get_memory_info = MyThread(madb.get_memoryinfo, args=())
            get_total_cpu = MyThread(madb.get_totalcpu, args=())
            get_allocated_cpu = MyThread(madb.get_allocated_cpu, args=())
            get_png = MyThread(GetScreen, args=(time.time(), madb.get_mdevice(), "performance"))
            # 为了避免重复场景不渲染导致的fps统计为0，fps取过去一秒内的最大值（约8次）。
            Threadlist = []
            for i in range(8):
                get_fps = MyThread(madb.get_fps, args=())
                Threadlist.append(get_fps)
            # 批量执行
            get_allocated_memory.start()
            get_memory_info.start()
            get_total_cpu.start()
            get_allocated_cpu.start()
            get_png.start()
            for p in Threadlist:
                p.start()
                fpstmp = p.get_result()
                if fpstmp == "N/a":
                    fpstmp = 0
                if len(dequelist) < 9:
                    dequelist.append(fpstmp)
                else:
                    dequelist.popleft()
                    dequelist.append(fpstmp)
            fps = max(dequelist)
            # 批量获得结果
            allocated = get_allocated_memory.get_result()
            total, free, used = get_memory_info.get_result()
            totalcpu, unused_maxcpu = get_total_cpu.get_result()
            allocatedcpu = get_allocated_cpu.get_result()
            png = get_png.get_result()
            # 批量回收线程
            get_allocated_memory.join()
            get_memory_info.join()
            get_total_cpu.join()
            get_allocated_cpu.join()
            get_png.join()
            get_fps.join()
            for p in Threadlist:
                p.join()
            # 将性能数据填充到一个数组里，塞进excel
            nowtime = time.localtime()
            inputtime = str(time.strftime("%H:%M:%S", nowtime))
            # print(inputtime,type(inputtime))
            if storage_by_excel:
                if allocatedcpu == "N/a":
                    list = ["'" + inputtime, total, "N/a", used, free, format(totalcpu / maxcpu, "0.2f") + "%", "N/a",
                            fps]
                else:
                    list = ["'" + inputtime, total, allocated, used, free, format(totalcpu / maxcpu, "0.2f") + "%",
                            format(float(allocatedcpu) / maxcpu, "0.2f") + "%", fps]
                record_to_excel(sheet, list, png=png)
            # 将性能数据填充到一个数组里，塞进json
            else:
                if allocatedcpu == "N/a":
                    list = [inputtime, total, allocated, used, free, float(format(float(totalcpu) / maxcpu, ".2f")), 0,
                            fps, png]
                else:
                    list = [inputtime, total, allocated, used, free, float(format(float(totalcpu) / maxcpu, ".2f")),
                            float(format(float(allocatedcpu) / maxcpu, "0.2f")), fps, png]
                record_to_json(jsonfilepath, list)

    except Exception as e:
        print(madb.get_mdevice() + traceback.format_exc())


# 线程类，用来获取线程函数的返回值
class MyThread(threading.Thread):
    def __init__(self, func, args=()):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        threading.Thread.join(self)  # 等待线程执行完毕
        try:
            return self.result
        except Exception as e:
            print(traceback.format_exc())
            return None


'''
小T写的。编辑由BR生成的html文件，将功能与性能整合成一个html。
'''


def EditReport(origin_html_path, storage_by_excelavglist, avglist="", maxlist="", minlist="", wb="", jsonfilepath=""):
    # 取项目的绝对路径
    rootPath = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())) + os.path.sep + ".")
    templatePath = os.path.join(rootPath, "template")
    # 读取报告文件
    f = open(origin_html_path, "r+", encoding="UTF-8")
    fr = f.read()
    f.close()

    # 拼接CSS样式
    fr_prev, fr_next = GetHtmlContent(fr, "</style>", True, 1)
    css = open(templatePath + "\\app.css", "r+", encoding='UTF-8')
    css_str = css.read()
    css.close()
    fr = fr_prev + "\n" + css_str + "\n" + fr_next

    # 拼接头部按钮
    fr_prev, fr_next = GetHtmlContent(fr, "<div", False, 3)
    header = open(templatePath + "\\header.html", "r+", encoding='UTF-8')
    header_str = header.read()
    header.close()
    fr = fr_prev + "\n" + header_str + "\n" + fr_next

    # 添加功能测试标记
    fr_prev, fr_next = GetHtmlContent(fr, "class=", False, 8)
    fr = fr_prev + 'id="functionReport" ' + fr_next

    # 拼接页面主体
    fr_prev, fr_next = GetHtmlContent(fr, "<script", False, 1)
    performance = open(templatePath + "\\performance.html", "r+", encoding='UTF-8')
    performance_str = performance.read()
    performance.close()
    fr = fr_prev + "\n" + performance_str + "\n" + fr_next

    # 拼接JS脚本
    fr_prev, fr_next = GetHtmlContent(fr, "</body>", True, 1)
    highchartspath = templatePath + "\\highcharts.js"
    highcharts_str = "<script src = " + highchartspath + " > </script >"
    js = open(templatePath + "\\app.js", "r+", encoding='UTF-8')
    js_str = js.read()
    js.close()
    fr = fr_prev + "\n" + highcharts_str + "\n" + js_str + "\n" + fr_next
    Time_series = TotalMemory = AllocatedMemory = UsedMemory = FreeMemory = TotalCPU = AllocatedCPU = FPS = PNG = ""
    Max_AllocatedMemory = Min_AllocatedMemory = Avg_AllocatedMemory = Max_AllocatedCPU = Min_AllocatedCPU = Avg_AllocatedCPU = Max_FPS = Min_FPS = Avg_FPS = 0
    data_count = ""
    if storage_by_excelavglist:
        # 嵌入性能测试结果到excel
        sheet = wb.sheets("Sheet1")
        Time_series = get_json(sheet, "Time")
        TotalMemory = get_json(sheet, "TotalMemory(MB)")
        AllocatedMemory = get_json(sheet, "AllocatedMemory(MB)")
        UsedMemory = get_json(sheet, "UsedMemory(MB)")
        FreeMemory = get_json(sheet, "FreeMemory(MB)")
        TotalCPU = get_json(sheet, "TotalCPU")
        AllocatedCPU = get_json(sheet, "AllocatedCPU")
        FPS = get_json(sheet, "FPS")
        PNG = get_json(sheet, "PNGAddress")
        Max_AllocatedMemory = maxlist[2]
        Min_AllocatedMemory = minlist[2]
        Avg_AllocatedMemory = avglist[2]
        Max_AllocatedCPU = maxlist[6]
        Min_AllocatedCPU = minlist[6]
        Avg_AllocatedCPU = avglist[6]
        Max_FPS = maxlist[7]
        Min_FPS = minlist[7]
        Avg_FPS = avglist[7]
        data_count = {"Max_AllocatedMemory": [Max_AllocatedMemory], "Min_AllocatedMemory": [Min_AllocatedMemory],
                      "Avg_AllocatedMemory": [Avg_AllocatedMemory], "Max_AllocatedCPU": [Max_AllocatedCPU],
                      "Min_AllocatedCPU": [Min_AllocatedCPU], "Avg_AllocatedCPU": [Avg_AllocatedCPU],
                      "Max_FPS": [Max_FPS],
                      "Min_FPS": [Min_FPS], "Avg_FPS": [Avg_FPS]}
        data_count = "\n" + "var data_count=" + json.dumps(data_count)
        # 嵌入性能测试结果到json
    else:
        jsonfilepath = (os.getcwd() + "\\" + jsonfilepath)
        jsondata = open(jsonfilepath, "r+", encoding='UTF-8')
        jsondata = json.load(jsondata)
        Time_series = json.dumps({"Time": jsondata["Time_series"]})
        TotalMemory = json.dumps({"TotalMemory(MB)": jsondata["TotalMemory"]})
        AllocatedMemory = json.dumps({"AllocatedMemory(MB)": jsondata["AllocatedMemory"]})
        UsedMemory = json.dumps({"UsedMemory(MB)": jsondata["UsedMemory"]})
        FreeMemory = json.dumps({"FreeMemory(MB)": jsondata["FreeMemory"]})
        TotalCPU = json.dumps({"TotalCPU": jsondata["TotalCPU"]})
        AllocatedCPU = json.dumps({"AllocatedCPU": jsondata["AllocatedCPU"]})
        FPS = json.dumps({"FPS": jsondata["FPS"]})
        PNG = json.dumps({"PNGAddress": jsondata["PNGAddress"]})
        data_count = json.dumps(jsondata["data_count"])
        data_count = data_count[1:-1]
        data_count = "\n" + "var data_count=" + data_count
    # data_series和data_count会被嵌入到html里，作为highcharts的数据源。
    data_series = Time_series + "\n" + "var TotalMemory=" + TotalMemory + "\n" + "var AllocatedMemory=" + AllocatedMemory + "\n" + "var UsedMemory=" + UsedMemory + "\n" + "var FreeMemory=" \
                  + FreeMemory + "\n" + "var TotalCPU=" + TotalCPU + "\n" + "var AllocatedCPU=" + AllocatedCPU + "\n" + "var FPS=" + FPS + "\n" + "var PNG=" + PNG + "\n"
    fr_prev, fr_next = GetHtmlContent(fr, "// tag data", False, 1)
    fr = fr_prev + data_series + "\n" + data_count + "\n" + fr_next

    # 写入文件
    newPath = origin_html_path.replace(".html", "_PLUS.html")
    f = open(newPath, "w", encoding="UTF-8")
    f.write(fr)
    f.close()

    return newPath


# 小T写的。获取需要插入性能图表的节点，reverse参数决定了从左数还是从右数，然后将html拆成2分，方便填标签。很有趣的思路。
def GetHtmlContent(content, tag, reverse=False, round_num=1):
    fr_r_index = ""
    if reverse:
        fr_r_index = content.rfind(tag)
    else:
        fr_r_index = content.find(tag)
    for i in range(1, round_num):
        if reverse:
            fr_r_index = content.rfind(tag, 0, fr_r_index)
        else:
            fr_r_index = content.find(tag, fr_r_index + 1)
    fr_prev = content[0:fr_r_index]
    fr_next = content[fr_r_index:len(content)]
    return fr_prev, fr_next


# 调试代码，单独执行的话，flag默认为1。
if __name__ == "__main__":
    devicesList = Madb().getdevices()
    print("最终的devicesList=", devicesList)

    start = time.localtime()
    '''
    madb = Madb(devicesList[0])
    flag = Value('i', 0)
    enter_performance (madb, flag, start,)
    '''
    print("启动进程池")
    flag = Value('i', 0)
    Processlist = []
    for i in range(len(devicesList)):
        madb = Madb(devicesList[i])
        if madb.get_androidversion() < 5:
            print("设备{}的安卓版本低于5，不支持。".format(madb.get_mdevice()))
            break
        print("{}开始进行性能测试".format(madb.get_mdevice()))
        # 根据设备列表去循环创建进程，对每个进程调用下面的enter_processing方法。
        p = Process(target=enter_performance, args=(madb, flag, start,))
        Processlist.append(p)
    for p in Processlist:
        p.start()
    for p in Processlist:
        p.join()

    print("性能测试结束")
