# WapQQ
一个简单的网页端QQ，基于Ariadne。

# 部署

## 加载方式

### 作为`Saya`插件加载
加载`saya`目录下的`WapQQ`目录即可
```python
from graia.saya import Saya
from graia.broadcast import Broadcast
bcc = Broadcast()
saya = Saya(bcc)

with saya.module_context():
    saya.require("saya.WapQQ")
```

### 直接部署
本项目提供了一个示例机器人，直接使用即可
`python main.py`

## 安装依赖
### 使用`poetry`
```bash
# 安装虚拟环境
poetry env use python
# 安装依赖
poetry install
# 启动机器人
poetry run python main.py
```

### 使用`pip`安装` (不推荐)
```bash
# 安装机器人依赖
pip install -r ./requirements.txt
# 安装插件依赖
pip install -r saya/WapQQ/requirements.txt
# 启动机器人
python main.py
```


## 配置
如果选择直接使用本项目，请先按该文件内的要求编辑`config/config.yaml.sample`

IP 和 端口号的配置在`saya/WapQQ/web/config.py`内
默认为`0.0.0.0:10002`

如果一切准备就绪，请访问`http://localhost:10002/qq`


