# 介绍
    eswitch管理控制台，配合eswitch组件使用
    图形化界面管理应用和开关项，动态推送到应用

## 安装
* 安装python
* 安装pip
```
    curl https://raw.githubusercontent.com/pypa/pip/master/contrib/get-pip.py     
    python get-pip.py
```

* 安装python依赖库
```
    pip install web.py
    pip install jinja2
    pip install MySQL-python
    pip install requests
```

* 数据库初始化
```
    执行eswitch_console.sql内容
```

* 运行
```
    python eswitch_console.py
```

## 演示
#### 登录
<img src="https://raw.githubusercontent.com/stone2083/assets/master/eswitch-console/login.png" width="480">

#### 管理应用

* 应用列表

<img src="https://raw.githubusercontent.com/stone2083/assets/master/eswitch-console/app_list.png" width="480">

* 应用添加

<img src="https://raw.githubusercontent.com/stone2083/assets/master/eswitch-console/app_add.png" width="480">

#### 管理应用实例

<img src="https://raw.githubusercontent.com/stone2083/assets/master/eswitch-console/instance_list.png" width="480">

#### 管理开关项

* 开关列表

<img src="https://raw.githubusercontent.com/stone2083/assets/master/eswitch-console/item_list.png" width="480">

* 开关添加

<img src="https://raw.githubusercontent.com/stone2083/assets/master/eswitch-console/item_add.png" width="480">

#### 更新开关项 & 通知应用

<img src="https://raw.githubusercontent.com/stone2083/assets/master/eswitch-console/item_update.png" width="480">
