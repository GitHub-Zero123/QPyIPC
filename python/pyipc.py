# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import json
import threading
import time
lambda: "By Zero123"

class IPCHandler:
    """ IPC 回调处理类 """
    def __init__(self, onData=None, onError=None):
        self.mOnData = onData
        self.mOnError = onError
        self._idCount = 0

    def onError(self, error):
        # type: (str) -> None
        """ 处理错误回调 """
        if self.mOnError:
            return self.mOnError(error)

    def onData(self, data):
        # type: (dict) -> None
        """ 处理数据回调 """
        if self.mOnData:
            return self.mOnData(data)
    
    def createId(self):
        # type: () -> str
        """ 创建唯一ID """
        self._idCount += 1
        return str(id(self)) + "_" + str(self._idCount)

class PyIPC:
    """ Python子进程 IPC 通信类(C++ PIPE通信) """
    # 性能测试
    # 解释器版本：Python2.7/3.12
    # 测试条件：单线程，Python默认参数，CPP消息循环间隔20ms
    # request：每秒1500次处理
    # get：每秒30次处理(受阻塞影响)
    MAGIC_HEADER = "PYIPCHEAD_"
    def __init__(self, targetPath, msgLoopInterval=0.005, stdoutSupport=True, enableLogging=True, passParentPid=True):
        # type: (str, float, bool, bool, bool) -> None
        """
        :param targetPath: 可执行文件路径
        :param msgLoopInterval: 消息循环间隔，单位秒
        :param stdoutSupport: 是否支持读取子进程的标准输出
        :param enableLogging: 是否启用日志
        :param passParentPid: 是否传递当前进程ID给子进程
        """
        self.mTargetPath = targetPath   # 可执行文件路径
        self.mCmdArgs = [targetPath]
        self.mMsgLoopInterval = msgLoopInterval
        self.mStdoutSupport = stdoutSupport
        self.mEnableLogging = enableLogging
        self.mProc = None   # type: subprocess.Popen | None
        self.mHandlerMap = {}   # type: dict[str, IPCHandler]
        if passParentPid:
            # 传递当前进程ID给子进程
            self.mCmdArgs.append(str(os.getpid()))

    def isProcAlive(self):
        # type: () -> bool
        """ 检查子进程是否存活 """
        if self.mProc is None:
            return False
        state = self.mProc.poll() is None
        if not state:
            self.mProc = None
        return state

    def getPid(self):
        # type: () -> int | None
        """ 获取子进程的PID """
        if not self.isProcAlive():
            return None
        return self.mProc.pid

    def start(self):
        # type: () -> bool
        """ 启动子进程 """
        if self.isProcAlive():
            return False
        if sys.version_info[0] >= 3:
            self.mProc = subprocess.Popen(
                self.mCmdArgs,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        else:
            self.mProc = subprocess.Popen(
                self.mCmdArgs,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
        self.mHandlerMap = {}   # 清理回调映射
        threading.Thread(target=lambda: self._procLooper(self.mProc)).start()
        if self.mEnableLogging:
            print("[Info] Process started with PID: {}".format(self.mProc.pid))
        return True

    def _procLooper(self, localProc):
        # type: (subprocess.Popen) -> None
        """ 持续读取子进程的标准输出 """
        if self.mStdoutSupport:
            print("[Thread] Process Thread started")
        # 非阻塞轮询 stdout
        stdout = self.mProc.stdout
        while self.mProc == localProc:
            line = stdout.readline()
            if not line:
                # 进程可能已结束
                if not self.isProcAlive():
                    break
                time.sleep(self.mMsgLoopInterval * 2)
            line = line.rstrip("\r\n")
            if not line.startswith(PyIPC.MAGIC_HEADER):
                if self.mStdoutSupport:
                    print("[STDOUT] " + line)
                continue
            line = line[len(PyIPC.MAGIC_HEADER):]   # 解析有效信息字段
            self.parseAndHandleMessage(line)
        if self.mEnableLogging:
            print("[Info] Process Thread has exited")

    def parseAndHandleMessage(self, line):
        # type: (str) -> None
        """ 解析并处理消息 """
        try:
            jo = json.loads(line)   # type: dict
            if not jo:
                return  # 心跳检测
            callBackId = jo.get("id", None)
            handler = self.mHandlerMap.pop(callBackId, None)    # type: IPCHandler | None
            if "error" in jo:
                if handler and handler.onError(jo["error"]):
                    # 若onError返回True则表示已处理，不再抛出异常
                    return
                raise RuntimeError("[CPP_ERROR] " + str(jo["error"]))
            data = jo.get("data", {})
            if handler:
                handler.onData(data)
        except Exception:
            import traceback
            traceback.print_exc()
    
    def sendCommand(self, command):
        if not self.isProcAlive():
            raise RuntimeError("Process is not running")
        self.mProc.stdin.write(command)
        self.mProc.stdin.flush()

    def request(self, funcName, args=None, handler=None):
        # type: (str, dict | None, IPCHandler | None) -> None
        """ 发送请求到子进程，回调函数将在子线程中被调用，请注意线程安全 """
        if not self.isProcAlive():
            raise RuntimeError("Process is not running")
        callId = handler.createId() if handler else ""
        data = {
            "call": str(funcName),
            "id": callId,
            "data": args or {}
        }
        command = PyIPC.MAGIC_HEADER + json.dumps(data) + "\n"
        if handler:
            self.mHandlerMap[callId] = handler
        self.sendCommand(command)

    def get(self, funcName, args=None, timeout=30.0):
        # type: (str, dict | None, float | None) -> dict
        """ 发送请求并等待结果返回(阻塞调用返回当前线程) """
        argsRef = []
        errRef = []
        def _dataCallback(data):
            argsRef.append(data)
        def _errorCallback(err):
            errRef.append(err)
            return True  # 表示错误已处理
        self.request(funcName, args, IPCHandler(_dataCallback, _errorCallback))
        startTime = time.time()
        while not argsRef and not errRef:
            if not timeout is None and time.time() - startTime > timeout:
                raise RuntimeError("Request timed out after {} seconds".format(timeout))
            time.sleep(self.mMsgLoopInterval)
        if errRef:
            raise RuntimeError("[CPP_ERROR] " + str(errRef[0]))
        return argsRef[0]

    def stop(self):
        # type: () -> None
        """ 安全的停止子进程 """
        if not self.isProcAlive():
            return
        self.mProc.terminate()
        self.mProc = None
        if self.mEnableLogging:
            print("[Info] Process terminated")

    def kill(self):
        # type: () -> None
        """ 强制杀死子进程 """
        if not self.isProcAlive():
            return
        self.mProc.kill()
        self.mProc = None
        if self.mEnableLogging:
            print("[Info] Process killed")