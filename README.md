# WapQQ
一个简单的网页端QQ，基于Ariadne。

# 部署

## 加载方式

### 作为`Saya`插件加载
加载`saya`目录下的`WapQQ`目录即可
```python
saya.require("WapQQ")
```

### 直接部署
本项目提供了一个示例机器人，直接使用即可
`python main.py`

## 安装依赖
使用`pip`安装`saya/WapQQ/requirements.txt`即可
`pip install -r saya/WapQQ/requirements.txt`

~~什么，为什么不用`poetry`之类的？别问，问就是懒狗。~~

## 配置
如果选择直接使用本项目，请先按该文件内的要求编辑`config/config.yaml.sample`

IP 和 端口号的配置在`saya/WapQQ/web/config.py`内
默认为`localhost:8888`

如果一切准备就绪，请访问`http://localhost:8888/qq`


