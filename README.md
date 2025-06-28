# Mineflayer Scripts in Python
A collection of Mineflayer bots in Python using JSPyBridge

All of these scripts require Node.js v18 or newer and Python 3.10 or newer.

You can join the [0x26e discord](https://discord.gg/FMqnBQ5j6C) for help, or join the [Mineflayer discord](https://discord.gg/PXbmVHkKXh) to see what others are working on.

# 基础环境

当你git clone了这个项目并cd进这个项目目录后，需要python和node.js的支持。为了保持项目环境的独立性，我们使用uv和nvm管理python和nodejs的环境。

## python支持

给这个项目建立一个uv venv环境：

```
uv venv
uv pip install javascript
```

## node.js支持

```
nvm use 22
npm i mineflayer
```

# 刷铁轨机

我把youtube上的一个[刷铁轨机教程](https://www.youtube.com/watch?v=7MmJoxSAUsw)做成了[程序](https://github.com/bigsam512/MineflayerPython/blob/main/scripts/digbot.py)
