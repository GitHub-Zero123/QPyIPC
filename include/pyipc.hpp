#pragma once
#include <string>
#include <functional>
#include <utility>
#include <thread>
#include <chrono>
#include <nlohmann/json.hpp>

// By Zero123
#define __PY_IPC_CONCATENATE_DETAIL(x, y) x##y
#define __PY_IPC_CONCATENATE(x, y) __PY_IPC_CONCATENATE_DETAIL(x, y)

#define PY_IPC_REGISTER_HANDLER(name, func) \
    static bool __PY_IPC_CONCATENATE(__ipc_handler_, __LINE__) = [](){ PyIPC::registerIpcHandler(name, (func)); return true; }();

#define PY_IPC_QUICK_MAIN(MCP_MODE) \
    int main(int argc, char** argv) { \
        if(MCP_MODE && !PyIPC::isMCPAvailable()) { return 1; } \
        while(1) { \
            std::this_thread::sleep_for(std::chrono::milliseconds(20)); \
            if(!PyIPC::checkParentProcessAliveFromArgs(argc, argv)) { return 0; } \
            else if(PyIPC::update() == PyIPC::UPDATE_STATUS::ERROR) { return 1; } \
        } \
        return 0; \
    }

namespace PyIPC
{
    enum class UPDATE_STATUS
    { 
        SUCCESS,
        ERROR,
    };
    
    using json = nlohmann::json;

    // 注册IPC请求处理器
    void registerIpcHandler(const std::string& pipeName, const std::function<void(const json&, json&)>& handler);

    // 消息循环更新 用于驱动响应处理
    UPDATE_STATUS update();

    // 心跳检测 发送空数据包
    void sendHeartbeat();

    // 检测父进程是否存活
    bool checkParentProcessAlive(unsigned long long pid);

    // 基于main args参数解析判定父进程是否存活
    bool checkParentProcessAliveFromArgs(int argc, char** argv);

    // 检测mcp包是否可用
    bool isMCPAvailable();

    // rpc消息循环封装
    template<typename Duration>
    void runUpdateLoop(Duration&& interval = std::chrono::milliseconds(20))
    {
        while(1)
        {
            std::this_thread::sleep_for(std::forward<Duration>(interval));
            if(PyIPC::update() == PyIPC::UPDATE_STATUS::ERROR)
            {
                return;
            }
        }
    };
}