# API 端点参考文档

> 基础路径: `http://localhost:8000`

## 智能体查询接口

### POST /api/agent/query

智能体主入口，执行三步推理查询。

**请求**:
```json
{
  "query": "查一下北京-上海39系统的路由"
}
```

**响应结构**:
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "query": "用户原始查询",
    "steps": [
      {
        "step": 1,
        "title": "识别传输系统名",
        "status": "completed",
        "description": "从输入中识别出传输系统名【XXX】",
        "detail": {
          "raw_input": "...",
          "extracted_system": "...",
          "extracted_circuit_no": "...",
          "intent": "search_system",
          "confidence": 0
        }
      },
      {
        "step": 2,
        "title": "查询所属工程期数",
        "status": "completed",
        "description": "查得【XXX】属于【10期】工程",
        "detail": {
          "found": true,
          "phase": "10期",
          "match_type": "模糊匹配",
          "circuits": [
            {
              "circuit_no": "4950",
              "system_name": "北京-上海39系统",
              "circuit_name": "上海JS1-北京JS1",
              "endpoint": "浦东-大白楼",
              "project_phase": "10期",
              "system_type": "SDH",
              "capacity": "1+1 10G POS"
            }
          ]
        }
      },
      {
        "step": 3,
        "title": "查询路由详情",
        "status": "completed",
        "description": "在【10期】路由表中查得 N 条路由跳段",
        "detail": {
          "has_hops": true,
          "total_hops": 126,
          "has_device_detail": false,
          "match_type": "电路名称匹配（XXX）",
          "hops": [
            {
              "hop_order": 1,
              "station_a": "大白楼",
              "station_b": "三台",
              "timeslot_id": "M8122λ16-4",
              "multiplex_section": "大白楼-三台10c",
              "device_type": "OSN9800",
              "route_type": "主用",
              "circuit_name": "北京JS1-上海JS1"
            }
          ]
        }
      }
    ],
    "llm_summary": "AI 生成的文字总结（需配置 DeepSeek API）"
  }
}
```

---

## 健康检查

### GET /api/health

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "status": "healthy",
    "db_path": ".../circuits.db",
    "db_exists": true,
    "llm_enabled": false,
    "circuits": 162840,
    "hops": 157132,
    "multiplex_sections": 27203,
    "db_size_mb": 236.0
  }
}
```

---

## 快捷搜索

### GET /api/circuits/search?q={keyword}&page=1&page_size=20

跳过智能体，直接搜索电路摘要。

**参数**:
| 参数 | 说明 | 默认 |
|------|------|------|
| `q` | 搜索关键词 | 必填 |
| `page` | 页码 | 1 |
| `page_size` | 每页条数 | 20 |

---

## 快捷详情

### GET /api/circuits/detail?circuit_no={no}&system_name={name}

跳过智能体，直接查询路由详情。

**参数**: `circuit_no` 或 `system_name` 至少传一个。
