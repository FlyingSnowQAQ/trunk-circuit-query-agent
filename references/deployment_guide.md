# 部署指南

## 系统要求

- **操作系统**: Windows 10/11 或 Windows Server
- **Python**: 3.10+
- **磁盘空间**: 至少 1GB（数据库约 200-300MB）
- **内存**: 至少 2GB
- **端口**: 8000（默认）

## 安装步骤

### 1. 准备数据源

系统需要以下 Excel 数据源文件（存放于 D: 盘或其他路径）：

```
D:\常用资料\路由\电路资料\电路查询\
├── 1-移动干线电路名称汇总（仅工程电路名称汇总集团调度电路不在此列).xlsx
├── 2-光通道路由表/
│   ├── 7期光通道路由表.doc
│   ├── 8.1期通道路由表.xls
│   ├── ...
│   └── 17期400G.xlsx
└── 3-具体路由表-包含各厂家具体网元ID槽位端口/
    ├── 10期/
    ├── 11.1期/
    └── ...
```

### 2. 构建数据库

```bash
cd circuit-query-system
pip install -r requirements.txt
python preprocess.py
```

预计耗时 1-5 分钟，生成 `output/circuits.db`（约 200MB）。

### 3. 数据库迁移（路由名称补全）

```bash
cd circuit-query-agent
pip install -r requirements.txt
python migrate_db.py
```

该步骤会向 `circuit_hops` 表添加 `circuit_name` 列并从 `circuits` 表回填数据。

### 4. 启动服务

```bash
# 方式一：一键启动
start.bat

# 方式二：手动启动
set PYTHONHOME=
set PYTHONPATH=
python -m api.server
```

### 5. 配置 DeepSeek API（可选）

设置环境变量以启用 AI 意图识别和格式化总结：

```bash
set DEEPSEEK_API_KEY=sk-your-api-key-here
```

### 6. 验证

```bash
curl http://localhost:8000/api/health
```

预期返回：
```json
{"code":0,"message":"ok","data":{"status":"healthy","circuits":162840, ...}}
```

## 常见问题

| 问题 | 解决方案 |
|------|---------|
| Python 报 encodings 错误 | 清除 `PYTHONHOME` 环境变量 |
| 数据库找不到 | 设置 `CIRCUIT_DB_PATH` 环境变量指向实际路径 |
| 端口被占用 | 修改 `CIRCUIT_API_PORT` 为其他端口 |
| 路由查不到数据 | 运行 `migrate_db.py` 补全数据 |
