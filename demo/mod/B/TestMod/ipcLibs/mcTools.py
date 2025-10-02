# -*- coding: utf-8 -*-
import os
import sys
lambda: "By Zero123"
# 为MCBE的行为包提供适用于mcs环境的文件搜索功能

_BEH_PATH_CACHE = {}    # type: dict[str, str]

def GET_BEH_PATHS():
    """ 获取所有加载的BEH包目录 """
    _ROOT_PACK = "/behavior_packs"
    for pathDir in sys.path[::-1]:
        dirPath = os.path.dirname(pathDir)
        if not os.path.dirname(dirPath).endswith(_ROOT_PACK):
            continue
        yield dirPath

def FIND_BEH_FILE(filePath):
    # type: (str) -> str | None
    """ 从行为包中访问特定文件 如果失败则返回None """
    if filePath in _BEH_PATH_CACHE:
        return _BEH_PATH_CACHE[filePath]
    for behPath in GET_BEH_PATHS():
        newPath = os.path.join(behPath, filePath)
        if os.path.isfile(newPath):
            realPath = os.path.realpath(newPath)
            _BEH_PATH_CACHE[filePath] = realPath
            return realPath
    return None