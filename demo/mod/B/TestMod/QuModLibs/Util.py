# -*- coding: utf-8 -*-
from functools import wraps
from time import time
import pickle as _pickle

class UniversalObject(object):
    """ 万用对象 """
    def __init__(self):
        pass

    def __getattribute__(self, __name):
        return self

    def __call__(self, *args, **kwds):
        return self

class EventsData(object):
    """ 事件Data """
    def __init__(self, json):
        self._quJson = json

    def __getattribute__(self, __name):
        return object.__getattribute__(self, "_quJson")[__name]

class EventsRedirect(object):
    """ 事件重定向 """
    def __getattribute__(self, __name):
        return type(__name, (EventsData,), {})

class SystemSide(object):
    def __init__(self, Path, SystemName = None):
        self.SystemName = SystemName # 绑定系统
        self.Path = Path

ModDirName = SystemSide.__module__.split(".")[0]
buil = UniversalObject()
Unknown = type("Unknown",(object,),{})
# ThreadLock = Lock()

class QRAIIBase:
    """ QRAII基类 规范基础协议 """
    def _cleanup(self):
        pass

class QRAIIDelayed(QRAIIBase):
    """ 延迟加载资源基类 规范协议 """
    def _loadResource(self):
        pass

class QRAIIDelayedFunc(QRAIIDelayed):
    """ 延迟加载函数资源 """
    def __init__(self, bindFunc=lambda: None):
        self.bindFunc = bindFunc

    def _loadResource(self):
        self.bindFunc()

class QBaseRAIIEnv:
    def __init__(self):
        self._raiiResSet = set()    # type: set[QRAIIBase]

    def addRAIIRes(self, res):
        # type: (QRAIIBase) -> bool
        """ 添加RAII资源 """
        if res in self._raiiResSet:
            return False
        self._raiiResSet.add(res)
        return True

    def freeRAIIRes(self, res):
        # type: (QRAIIBase) -> bool
        """ 释放RAII资源 """
        if not res in self._raiiResSet:
            return False
        self._raiiResSet.remove(res)
        res._cleanup()
        return True

    def freeALLRAIIRes(self):
        # type: () -> None
        """ 释放所有RAII资源 """
        while self._raiiResSet:
            for res in list(self._raiiResSet):
                TRY_EXEC_FUN(res._cleanup)
                self._raiiResSet.discard(res)

    def hasRAIIRes(self, res):
        # type: (QRAIIBase) -> bool
        return res in self._raiiResSet

    def getRAIIResSetRef(self):
        # type: () -> set[QRAIIBase]
        """ 获取RAII资源集合引用 """
        return self._raiiResSet

    def getRAIIList(self):
        # type: () -> list[QRAIIBase]
        return list(self._raiiResSet)

class QDRAIIEnv(QBaseRAIIEnv):
    def __init__(self):
        QBaseRAIIEnv.__init__(self)
        self._draiiEnvState = False

    def loadDRAIIRes(self, res):
        # type: (QRAIIDelayed) -> bool
        """ 加载延迟RAII资源 """
        if self.hasRAIIRes(res):
            res._loadResource()
            return True
        return False

    def addRAIIRes(self, res):
        state = QBaseRAIIEnv.addRAIIRes(self, res)
        if state and self._draiiEnvState:
            # 如果RAII环境已经初始化 则立即加载资源
            if isinstance(res, QRAIIDelayed):
                res._loadResource()

    def setDRAIIEnvState(self, state=True):
        self._draiiEnvState = state

    def loadALLDRAIIRes(self):
        # type: () -> None
        """ 加载所有延迟RAII资源 """
        for res in list(self._raiiResSet):
            if isinstance(res, QRAIIDelayed):
                res._loadResource()

def RandomUid():
    """ 创建随机UID """
    from uuid import uuid4
    return "QuMod_"+uuid4().hex

def Base64(_text = ""):
    # type: (str) -> str
    """ 将string值进行加密 """
    from base64 import b64encode
    _text = str(_text)
    basText = str(b64encode(_text.encode()))
    if len(basText) > 16:
        basText = basText[:16]
    return basText

def ExceptionHandling(errorFun=lambda: None, output=False):
    """ 异常处理装饰器 当函数抛出异常时将会返回预定值 """
    def exceptionHandling(func):
        @wraps(func)
        def newFun(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if output:
                    print("[Error]: 异常捕获 {}".format(str(e)))
                    import traceback
                    traceback.print_exc()
                return errorFun()
        return newFun
    return exceptionHandling

def InitOperation(fun):
    """ 初始化运行 装饰器 @InitOperation 函数将会自动执行一次 不支持传参 """
    try:
        fun()
    except Exception as e:
        print("[Error] " + str(e))
    return fun

class Math:
    """ 简易数学运算类 """
    @staticmethod
    def pointDistance(point1, point2):
        # type: (tuple, tuple) -> float
        """ 两点距离计算 """
        x1, y1, z1 = point1
        x2, y2, z2 = point2
        result = ((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)**0.5
        return result

    @staticmethod
    def getUnitVector(vector):
        # type: (tuple[int|float]) -> tuple[int|float]
        """ 获取向量的单位向量 """
        length = (sum(i ** 2 for i in vector)) ** 0.5
        if length == 0:
            return vector
        unitVector = tuple((i / length) for i in vector)
        return unitVector

def errorPrint(charPtr):
    """ 异常输出 """
    print("[Error] "+str(charPtr))

def TRY_EXEC_FUN(funObj, *args, **kwargs):
    try:
        return funObj(*args, **kwargs)
    except Exception as e:
        import traceback
        print("TRY_EXEC发生异常: {}".format(e))
        traceback.print_exc()

def traceCallStack(printNow=True):
    # type: (bool) -> list[str]
    """ 获取当前的调用栈信息 """
    import traceback
    stackTrace = traceback.extract_stack()
    # 打印堆栈跟踪
    outStr = []
    for args in stackTrace:
        outStr.append("<{}({})> {}".format(args[0], args[1], args[2]))
    if printNow:
        print("\n".join(outStr))
    return outStr

def getObjectPathName(_callObj = lambda: None):
    # type: (object) -> str
    """ 获取可执行对象的目录名 """
    return ".".join((_callObj.__module__, _callObj.__name__))

def QThrottle(intervalTime=0.1):
    """ 该装饰器用于限制函数重复执行的最小时间间隔 """
    def _func(f):
        lastTime = [0.0]
        def _newFunc(*args, **kwargs):
            nowTime = time()
            if nowTime > lastTime[0] + intervalTime:
                lastTime[0] = nowTime
                return f(*args, **kwargs)
            return None
        return _newFunc
    return _func

class _QConstStatic:
    initFuncSet = set()

def QConstInit(funcObj):
    """ 常量初始化函数执行(将自动检查reload) """
    funcName = getObjectPathName(funcObj)
    if not funcName in _QConstStatic.initFuncSet:
        _QConstStatic.initFuncSet.add(funcName)
        TRY_EXEC_FUN(funcObj)
    return funcObj

class QStruct:
    """ 结构体 用于通用数据模型约定(即不涉及任何API) 应定义在Server/Client以外的通用文件 同理Struct也不应该持有任何涉及端侧API的内容 """
    _SIGN_FORMAT = "_QSTRUCT[{}]"
    def dumps(self):
        """ 序列化对象 """
        return _pickle.dumps(self)

    def signDumps(self):
        """ 带有特征签名的序列化 """
        data = self.dumps()
        return [QStruct._SIGN_FORMAT.format(hex(hash(data))), data]

    @staticmethod
    def isSignData(data):
        """ 校验数据 """
        if not isinstance(data, list) or len(data) != 2:
            return False
        signKey = data[0]
        if isinstance(signKey, str):
            dataObj = data[1]
            return signKey == QStruct._SIGN_FORMAT.format(hex(hash(dataObj)))
        return False

    @staticmethod
    def loads(data):
        # type: (str) -> QStruct
        """ 反序列化加载对象 """
        return _pickle.loads(data)

    @staticmethod
    def loadSignData(data):
        # type: (list) -> QStruct
        """ 反序列化加载Sign对象表(不会校验) """
        return _pickle.loads(data[1])

    def onNetUnPack(self):
        return self

# 为性能考虑Call不会盲目的计算每一个容器的所有数据字段 因此有了以下类型封装 在Call后将会解包原型数据
class QRefStruct(QStruct):
    """ 万能引用 """
    def __init__(self, refObject):
        self.ref = refObject

    def onNetUnPack(self):
        return self.ref

class QListStruct(QStruct, list):
    """ List容器结构 """
    def onNetUnPack(self):
        return list(self)

class QDictStruct(QStruct, dict):
    """ Dict容器结构 """
    def onNetUnPack(self):
        return dict(self)

class QTupleStruct(QStruct, tuple):
    """ Tuple容器结构 """
    def onNetUnPack(self):
        return tuple(self)