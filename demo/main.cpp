#include <iostream>
#include <utility>
#include <pyipc.hpp>

#ifdef _WIN32
// 避免windows宏污染
#define NOMINMAX
#define WIN32_LEAN_AND_MEAN
#define NOGDI
#include <windows.h>
#include <tlhelp32.h>

// 注册自定义API 用于获取系统进程列表
PY_IPC_REGISTER_HANDLER("get_processes", [](const PyIPC::json& data, PyIPC::json& result) {
    PyIPC::json& datas = result["datas"] = PyIPC::json::array();    // 创建一个数组
    // 获取系统快照
    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnapshot == INVALID_HANDLE_VALUE) {
        // IPC框架会自动处理CPP异常并传递到Python端
        throw std::runtime_error("CreateToolhelp32Snapshot failed");
    }

    PROCESSENTRY32W pe;
    pe.dwSize = sizeof(PROCESSENTRY32W);

    if (Process32FirstW(hSnapshot, &pe)) {
        do {
            // pe.szExeFile 需要要转换编码到 UTF-8
            int len = WideCharToMultiByte(CP_UTF8, 0, pe.szExeFile, -1, nullptr, 0, nullptr, nullptr);
            std::string name(len - 1, 0); // 分配std字符串 大小减去'\0'
            WideCharToMultiByte(CP_UTF8, 0, pe.szExeFile, -1, name.data(), len, nullptr, nullptr);

            datas.push_back({
                {"pid", static_cast<int>(pe.th32ProcessID)},
                {"name", std::move(name)}
            });
        } while (Process32NextW(hSnapshot, &pe));
    }

    CloseHandle(hSnapshot);
});
#endif

// 使用PY_IPC_QUICK_MAIN宏自动生成main函数，或者自行实现消息循环。
PY_IPC_QUICK_MAIN(0);