# QPyIPC
**QPyIPC** 是一个轻量级通用 IPC 库，基于 **PIPE** 实现，专为 Python 设计，支持 **Python 2.x 和 Python 3.x 全版本**。

> ℹ️ **项目背景**：由 `Zero123` 假期开发，主要用于 **网易我的世界 MCS调试环境** 的外部调用解决方案。

## 特性
- ✅ **跨 Python 版本**：兼容 Python 2.x 与 3.x  
- ✅ **轻量级**：精简包体，易于集成  
- ✅ **基于 PIPE**：可靠的进程间通信  

## CMake 示例
```cmake
cmake_minimum_required(VERSION 3.15)

project(WINAPI LANGUAGES CXX C)

if(MSVC)
    add_compile_options(/utf-8 /EHsc)
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Release>:>")
endif()

# 包含 pyipc
add_subdirectory(qpyipc)

add_executable(winApi main.cpp)
target_compile_features(winApi PRIVATE cxx_std_20)

# 链接 pyipc 对象库
target_link_libraries(winApi PRIVATE pyipc)
```

## IPC 扩展开发
### 注册API
`pyipc`提供了一系列宏用于注册API，简化开发流程。
```cpp
#include <iostream>
#include <pyipc.hpp>

// 使用 PY_IPC_REGISTER_HANDLER 宏注册API
PY_IPC_REGISTER_HANDLER("hello_world", [](const PyIPC::json& data, PyIPC::json& result) {
    // result将返回py侧并解析为dict
    result["return"] = "[CPP] Hello, World!";
});

PY_IPC_REGISTER_HANDLER("error_test", [](const PyIPC::json& data, PyIPC::json& result) {
    // 异常测试 (将返回py侧并转换为RuntimeError)
    throw std::runtime_error("This is a test error from C++!");
});

PY_IPC_QUICK_MAIN(0);   // 使用宏注册主函数消息循环
```

### 消息循环
若使用 `PY_IPC_QUICK_MAIN` 宏会自动生成一个标准的消息循环。
```cpp
#include <iostream>
#include <pyipc.hpp>

int main(int argc, char** argv)
{
    // 如果需要自定义消息循环或其他业务逻辑，可以手动编写
    while(1) {
        std::this_thread::sleep_for(std::chrono::milliseconds(20));
        if(!PyIPC::checkParentProcessAliveFromArgs(argc, argv)) {
            return 0;
        }
        else if(PyIPC::update() == PyIPC::UPDATE_STATUS::ERROR) {
            return 1;
        }
    }
    return 0;
}
```

## Python 端使用示例
此处演示通用的 Python 端使用方法。

### 同步调用
使用**get**方法同步调用API，阻塞等待结果。
```python
from .pyipc import PyIPC

winApi = PyIPC("./winApi.exe")
winApi.start()

print(winApi.get("hello_world"))
# 输出: {'return': '[CPP] Hello, World!'}
winApi.get("error_test")  # 将抛出RuntimeError

winApi.stop()
```

### 异步调用
使用**request**方法异步调用API，立即返回。
```python
from .pyipc import PyIPC, IPCHandler

winApi = PyIPC("./winApi.exe")
winApi.start()

def callback(result):
    print("Callback received:", result)

# 异步调用，并在单独的消息循环线程中触发回调(请注意线程安全)
winApi.request("hello_world", {}, IPCHandler(callback))

# winApi.stop()  # 在异步回调处理完毕之前不要关闭IPC连接
```

## 在 MC 中使用
请参考 `demo` 目录下的 `mod` 示例，展示了如何在 **网易我的世界 MCS** 环境中集成和使用 **QPyIPC**。
```python
# -*- coding: utf-8 -*-
# 此处以QuMod框架为例，其他框架可自行参考处理。
from .QuModLibs.Client import *
from .ipcLibs.mcTools import FIND_BEH_FILE
from .ipcLibs.pyipc import PyIPC
import random

class IPC:
    winApi = PyIPC(FIND_BEH_FILE("winApi.exe"))

    @staticmethod
    @regModLoadFinishHandler
    def modInit():
        # 启动IPC句柄
        IPC.winApi.start()

    @staticmethod
    @DestroyFunc
    def onDestroy():
        # 安全的关闭IPC句柄
        IPC.winApi.stop()

@Listen("ClientJumpButtonPressDownEvent")
def ClientJumpButtonPressDownEvent(_={}):
    """ 按下跳跃按键触发IPC测试逻辑 """
    # 调用 winApi.exe 的 get_processes 接口
    result = IPC.winApi.get("get_processes")
    datas = result["datas"]
    random.shuffle(datas) # 随机打乱排序

    # 发送消息(此处仅显示一部分进程信息)
    comp = clientApi.GetEngineCompFactory().CreateTextNotifyClient(levelId)
    for data in datas[:min(15, len(datas))]:
        name = data["name"]
        pid = data["pid"]
        comp.SetLeftCornerNotify("[进程: {}] {}".format(pid, name))
```

## 第三方依赖
- [nlohmann/json](https://github.com/nlohmann/json) - 用于 JSON 解析和处理