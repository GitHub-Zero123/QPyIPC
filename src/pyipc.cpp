#include "pyipc.hpp"
#include <iostream>
#include <unordered_map>
#ifdef _WIN32
    #define NOMINMAX
    #define NOGDI
    #include <windows.h>
#endif
#include <filesystem>

// By Zero123
static constexpr const char* IPC_MAGIC = "PYIPCHEAD_";

class IPC_MANAGER
{
private:
    IPC_MANAGER() = default;
    ~IPC_MANAGER() = default;
public:
    std::unordered_map<std::string, std::function<void(const PyIPC::json&, PyIPC::json&)>> mIpcHandlers;

    static IPC_MANAGER& getInstance()
    {
        static IPC_MANAGER instance;
        return instance;
    }

    // 禁止复制/移动
    IPC_MANAGER(const IPC_MANAGER&) = delete;
    IPC_MANAGER& operator=(const IPC_MANAGER&) = delete;
    IPC_MANAGER(IPC_MANAGER&&) = delete;
    IPC_MANAGER& operator=(IPC_MANAGER&&) = delete;
};

// 注册IPC请求处理器
void PyIPC::registerIpcHandler(
    const std::string& pipeName,
    const std::function<void(const json&, json&)>& handler
) {
    IPC_MANAGER::getInstance().mIpcHandlers[pipeName] = handler;
}

// PIPE 管道消息解析
//
// 【Python → C++ 请求协议】
// {
//     "call":  "pipeName",      // 调用的管道名
//     "id":    "callbackId",    // 回调标识，用于对应请求和响应
//     "data":  { ... }          // 调用参数（对象）
// }
//
// 【C++ → Python 响应协议】
// {
//     "id":    "callbackId",    // 与请求对应的回调标识
//     "data":  { ... },         // 正常返回时存在
//     "error": "error message"  // 出错时存在
// }
// 
// 说明：
// - "data" 与 "error" 二选一，互斥存在
// - "data" 存在时表示调用成功，不会有 "error"
// - "error" 存在时表示调用异常，不会有 "data"
static void handleIpcMessage(const std::string& message)
{
    // 判断头是否为 IPC_MAGIC
    if (message.size() <= strlen(IPC_MAGIC) || message.substr(0, strlen(IPC_MAGIC)) != IPC_MAGIC) {
        return;
    }
    std::string jsonStr = message.substr(strlen(IPC_MAGIC));
    auto jo = PyIPC::json::parse(jsonStr, nullptr, false);
    // 检查数据有效性
    if (jo.is_discarded() || !jo.is_object()) {
        return;
    }
    // 获取指定key
    std::string pipeName = jo.value("call", "");
    auto& ipcHandlers = IPC_MANAGER::getInstance().mIpcHandlers;
    auto it = ipcHandlers.find(pipeName);
    PyIPC::json responseData = PyIPC::json::object();   // 生成响应数据
    std::string callbackId = jo.value("id", "");
    responseData["id"] = callbackId;
    if (it == ipcHandlers.end()) {
        // 未找到对应处理器 抛出异常给Python端
        responseData["error"] = "No handler: " + pipeName;
        std::cout << IPC_MAGIC << responseData.dump() << "\n" << std::flush;
        return;
    }
    // 解析数据字段
    auto dataIt = jo.find("data");
    PyIPC::json requestData = (dataIt != jo.end() && dataIt->is_object()) ? *dataIt : PyIPC::json::object();
    // 调用处理器
    try {
        auto ret = PyIPC::json::object();
        it->second(requestData, ret);
        responseData["data"] = ret;
    } catch (const std::exception& e) {
        responseData["error"] = e.what();
    }
    // 输出响应数据
    std::cout << IPC_MAGIC << responseData.dump() << "\n" << std::flush;
}

void PyIPC::sendHeartbeat()
{
    std::cout << IPC_MAGIC << "{}\n" << std::flush;
}

#ifdef _WIN32

static HANDLE hIn = INVALID_HANDLE_VALUE;
static std::string acc;
static constexpr int BUF_SIZE = 4096;
static char buf[BUF_SIZE];

// 消息循环更新(触发接收处理)
PyIPC::UPDATE_STATUS PyIPC::update()
{
    if (hIn == INVALID_HANDLE_VALUE) {
        // 初始化获取输入句柄
        hIn = GetStdHandle(STD_INPUT_HANDLE);
        if (hIn == INVALID_HANDLE_VALUE) {
            return UPDATE_STATUS::ERROR; // 无法获取输入句柄
        }
    }
    DWORD avail = 0;
    BOOL ok = PeekNamedPipe(hIn, NULL, 0, NULL, &avail, NULL);
    if (ok && avail > 0)
    {
        DWORD toRead = std::min<DWORD>(BUF_SIZE, avail);
        DWORD read = 0;
        if (ReadFile(hIn, buf, toRead, &read, NULL) && read > 0) {
            acc.append(buf, buf + read);
            size_t pos;
            while ((pos = acc.find('\n')) != std::string::npos) {
                std::string line = acc.substr(0, pos);
                acc.erase(0, pos + 1);
                handleIpcMessage(line);
            }
        } else {
            DWORD err = GetLastError();
            if (err == ERROR_BROKEN_PIPE) {
                // 父进程关了管道或者其他异常情况
                return UPDATE_STATUS::ERROR;
            } else if (err == ERROR_NO_DATA) {
                // 没有数据可读
                return UPDATE_STATUS::SUCCESS;
            } else {
                // 其他异常错误
                return UPDATE_STATUS::ERROR;
            }
        }
        return UPDATE_STATUS::SUCCESS;
    }
    return UPDATE_STATUS::SUCCESS;
}

bool PyIPC::checkParentProcessAlive(unsigned long long pid)
{
    HANDLE hProcess = OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION, 
        FALSE, 
        static_cast<DWORD>(pid)
    );
    if (!hProcess) {
        // 打不开句柄，可能进程不存在
        return false;
    }
    DWORD exitCode = 0;
    GetExitCodeProcess(hProcess, &exitCode);
    CloseHandle(hProcess);
    return exitCode == STILL_ACTIVE;
}

static std::filesystem::path& getExePath()
{
    static std::filesystem::path path;
    if(path.empty())
    {
        wchar_t buf[MAX_PATH];
        DWORD len = GetModuleFileNameW(NULL, buf, MAX_PATH);
        if(len > 0 && len < MAX_PATH)
        {
            path.assign(buf, buf + len);
        }
    }
    return path;
}

#else
PyIPC::UPDATE_STATUS PyIPC::update() = delete;
PyIPC::checkParentProcessAlive() = delete;
static std::filesystem::path& getExePath() = delete;
#endif

// 检查mcp包是否存在
bool PyIPC::isMCPAvailable()
{
    auto& exePath = getExePath();
    // 获取目录
    auto dir = exePath.parent_path();
    // 获取当前可执行文件名但不包含扩展名
    auto exeName = exePath.stem().string();
    // 构造mcp包路径
    auto noMcpPath = dir / exeName;
    auto mcpPath = dir / (exeName + ".mcp");
    if(std::filesystem::exists(noMcpPath))  {
        // 不可以存在同名无扩展名文件夹/文件
        return false;
    }
    if(std::filesystem::exists(mcpPath) && std::filesystem::is_regular_file(mcpPath)) {
        return true;
    }
    return false;
}

// 默认认为checkParentProcessAliveFromArgs所解析的args是不变的可以缓存
static unsigned long long _pidCache = 0; 
static HANDLE hCached = nullptr;

bool PyIPC::checkParentProcessAliveFromArgs(int argc, char** argv)
{
    if(argc < 2) {
        // 没有传入父进程PID参数，默认认为禁用此功能
        return true;
    }

    if(_pidCache == 0) {
        try {
            _pidCache = std::stoull(argv[1]);
        } catch (...) {
            // 参数无法转换为数字 异常进程ID
            return false;
        }
    }

    // 初始化缓存 HANDLE
    if(!hCached) {
        hCached = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, (DWORD)_pidCache);
        if(!hCached) { 
            return false;
        }
    }

    DWORD exitCode = 0;
    // 检查父进程是否存活
    if(!GetExitCodeProcess(hCached, &exitCode)) {
        return false;
    }

    if(exitCode != STILL_ACTIVE) {
        // 父进程已经退出，释放 HANDLE 并清空缓存
        CloseHandle(hCached);
        hCached = nullptr;
        return false;
    }
    return true;
}