# -*- coding: utf-8 -*-
from .QuModLibs.Client import *
from .ipcLibs.mcTools import FIND_BEH_FILE
from .ipcLibs.pyipc import PyIPC
import random
lambda: "By Zero123"

class IPC:
    winApi = PyIPC(FIND_BEH_FILE("winApi.exe"))

    @staticmethod
    @regModLoadFinishHandler
    def modInit():
        # 启动IPC句柄 使用regModLoadFinishHandler装饰器确保mod加载完毕后唯一调用一次
        IPC.winApi.start()

    @staticmethod
    @DestroyFunc
    def onDestroy():
        # 安全的关闭IPC句柄
        # 若使用PY_IPC_QUICK_MAIN宏构建则会在exe端侧自动检测回收，但不够及时，建议手动触发
        IPC.winApi.stop()

@Listen("ClientJumpButtonPressDownEvent")
def ClientJumpButtonPressDownEvent(_={}):
    """ 按下跳跃按键触发IPC测试 """
    # 使用get方法调用winApi.exe的get_processes接口
    # 注：get通过阻塞线程实现同步调用，高频高性能场景请使用异步request + QuModLibs的Thread库返回主线程执行
    result = IPC.winApi.get("get_processes")
    datas = result["datas"]
    random.shuffle(datas) # 随机打乱排序
    comp = clientApi.GetEngineCompFactory().CreateTextNotifyClient(levelId)
    # 为避免SetLeftCornerNotify性能问题 此处仅显示一部分
    for data in datas[:min(15, len(datas))]:
        name = data["name"]
        pid = data["pid"]
        comp.SetLeftCornerNotify("[进程: {}] {}".format(pid, name))