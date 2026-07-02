/**
 * 移动干线电路查询智能体 - UI 交互脚本
 */

async function doQuery() {
    const input = document.getElementById('queryInput');
    const query = input.value.trim();
    if (!query) return;

    // UI 状态
    const btn = document.getElementById('queryBtn');
    const loading = document.getElementById('loading');
    const resultSection = document.getElementById('resultSection');
    const errorBox = document.getElementById('errorBox');

    btn.disabled = true;
    loading.style.display = 'block';
    resultSection.style.display = 'none';
    errorBox.style.display = 'none';

    try {
        const resp = await fetch('/api/agent/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query }),
        });

        if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);

        const json = await resp.json();
        if (json.code !== 0) throw new Error(json.message || '未知错误');

        renderResult(json.data);
    } catch (e) {
        errorBox.textContent = `❌ 查询失败: ${e.message}`;
        errorBox.style.display = 'block';
    } finally {
        btn.disabled = false;
        loading.style.display = 'none';
    }
}

function renderResult(data) {
    const container = document.getElementById('stepsContainer');
    const resultSection = document.getElementById('resultSection');
    container.innerHTML = '';

    if (!data.steps || data.steps.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="icon">🔍</div><p>未查询到相关数据</p></div>';
        resultSection.style.display = 'block';
        return;
    }

    data.steps.forEach((step, idx) => {
        const card = document.createElement('div');
        card.className = 'step-card';

        const statusIcon = step.status === 'completed' ? '✅' :
                           step.status === 'not_found' ? '❓' : 'ℹ️';

        const header = document.createElement('div');
        header.className = 'step-header';
        header.onclick = () => {
            body.style.display = body.style.display === 'none' ? 'block' : 'none';
            toggle.textContent = body.style.display === 'none' ? '展开' : '收起';
        };

        header.innerHTML = `
            <div class="step-number">${step.step}</div>
            <div class="step-status-icon">${statusIcon}</div>
            <div class="step-title">
                ${step.title}
                <div class="step-description">${step.description || ''}</div>
            </div>
            <div class="step-toggle" id="toggle-${idx}">收起</div>
        `;

        const body = document.createElement('div');
        body.className = 'step-body';
        body.id = `body-${idx}`;

        // 根据步骤渲染详细内容
        if (step.step === 1) {
            renderStep1(body, step.detail);
        } else if (step.step === 2) {
            renderStep2(body, step.detail);
        } else if (step.step === 3) {
            renderStep3(body, step.detail);
        }

        card.appendChild(header);
        card.appendChild(body);
        container.appendChild(card);
    });

    // AI 总结
    const summaryEl = document.getElementById('llmSummary');
    const summaryBody = document.getElementById('summaryBody');
    if (data.llm_summary) {
        summaryBody.textContent = data.llm_summary;
        summaryEl.style.display = 'block';
    } else {
        summaryEl.style.display = 'none';
    }

    resultSection.style.display = 'block';
}

function renderStep1(body, detail) {
    if (!detail) return;
    body.innerHTML = `
        <table class="circuit-table">
            <tr><th>字段</th><th>值</th></tr>
            <tr><td>原始输入</td><td>${esc(detail.raw_input || '')}</td></tr>
            <tr><td>识别的系统名</td><td><strong>${esc(detail.extracted_system || '')}</strong></td></tr>
            <tr><td>识别的电路号</td><td>${esc(detail.extracted_circuit_no || '')}</td></tr>
            <tr><td>意图</td><td>${esc(detail.intent || '')}</td></tr>
            <tr><td>置信度</td><td>${detail.confidence ? (detail.confidence * 100).toFixed(0) + '%' : '-'}</td></tr>
        </table>
    `;
}

function renderStep2(body, detail) {
    if (!detail) return;

    if (!detail.found) {
        body.innerHTML = '<div class="no-data">❌ 未在电路汇总表中找到匹配的电路</div>';
        return;
    }

    let html = '';
    if (detail.phase) {
        html += `<div style="margin-bottom:8px;font-size:15px;font-weight:600;">
                    所属工程期数：<span style="color:var(--primary)">${esc(detail.phase)}</span>
                 </div>`;
    }

    const matchClass = detail.match_type === '精确匹配' ? 'exact' : 'fuzzy';
    html += `<span class="match-tag ${matchClass}">${esc(detail.match_type)}</span>`;

    if (detail.circuits && detail.circuits.length > 0) {
        html += `<table class="circuit-table">
            <tr>
                <th>电路号</th>
                <th>系统名</th>
                <th>终端点</th>
                <th>系统性质</th>
                <th>容量</th>
            </tr>`;
        detail.circuits.forEach(c => {
            html += `<tr>
                <td><strong>${esc(c.circuit_no || '')}</strong></td>
                <td>${esc(c.system_name || '')}</td>
                <td>${esc(c.endpoint || '')}</td>
                <td>${esc(c.system_type || '')}</td>
                <td>${esc(c.capacity || '')}</td>
            </tr>`;
        });
        html += '</table>';
    }

    body.innerHTML = html;
}

function renderStep3(body, detail) {
    if (!detail) return;

    if (!detail.has_hops) {
        body.innerHTML = '<div class="no-data">ℹ️ 该电路无详细路由数据</div>';
        return;
    }

    let html = `<div class="routing-info">
                    共 <strong>${detail.total_hops}</strong> 跳路由
                    ${detail.match_context ? ' · <span style="color:var(--primary)">' + esc(detail.match_context) + '</span>' : ''}
                    ${detail.match_type && !detail.match_context ? ' · <span style="color:var(--primary)">' + esc(detail.match_type) + '</span>' : ''}
                    ${detail.has_device_detail ? ' · 含设备级端口信息' : ''}
                </div>`;

    html += `<table class="hops-table">
        <tr>
            <th>跳次</th>
            <th>A站</th>
            <th>B站</th>
            <th>单盘类型(A/B)</th>
            <th>时隙ID</th>
            <th>复用段</th>
            <th>设备类型</th>
            <th>设备厂家</th>
            <th>电路名称</th>
        </tr>`;

    detail.hops.forEach(h => {
        const vendor = h.vendor || '';
        const vendorHtml = vendor
            ? `<span class="vendor-tag vendor-${vendor}">${esc(vendor)}</span>`
            : '<span class="vendor-tag vendor-none">—</span>';
        // 单盘名称：A盘 / B盘（用普通字符串拼接避免嵌套反引号）
        const ba = h.board_type_a ? esc(h.board_type_a) : '';
        const bb = h.board_type_b ? esc(h.board_type_b) : '';
        let boardHtml;
        if (ba || bb) {
            const aPart = ba
                ? '<span class="board-chip board-a">' + ba + '</span>'
                : '<span class="board-chip board-empty">—</span>';
            const bPart = bb
                ? '<span class="board-chip board-b">' + bb + '</span>'
                : '<span class="board-chip board-empty">—</span>';
            boardHtml = aPart + ' / ' + bPart;
        } else {
            boardHtml = '<span class="board-chip board-na">—</span>';
        }
        html += `<tr>
            <td>${h.hop_order || '-'}</td>
            <td>${esc(h.station_a || '')}</td>
            <td>${esc(h.station_b || '')}</td>
            <td>${boardHtml}</td>
            <td>${esc(h.timeslot_id || '')}</td>
            <td>${esc(h.multiplex_section || '')}</td>
            <td>${esc(h.device_type || '')}</td>
            <td>${vendorHtml}</td>
            <td>${esc(h.circuit_name || '')}</td>
        </tr>`;
    });

    html += '</table>';

    // 如果有设备级信息，展开显示完整字段
    if (detail.has_device_detail) {
        html += `<details style="margin-top:12px;">
            <summary style="cursor:pointer;font-weight:600;font-size:13px;color:var(--primary);">
                查看完整设备端口详情
            </summary>
            <table class="hops-table" style="margin-top:8px;">
                <tr>
                    <th>跳次</th>
                    <th>A端设备</th>
                    <th>A线路槽位</th>
                    <th>A线路端口</th>
                    <th>A线路板</th>
                    <th>A支路槽位</th>
                    <th>A支路端口</th>
                    <th>B端设备</th>
                    <th>B线路槽位</th>
                    <th>B线路端口</th>
                    <th>B线路板</th>
                    <th>B支路槽位</th>
                    <th>B支路端口</th>
                </tr>`;
        detail.hops.forEach(h => {
            if (h.a_equipment_id || h.b_equipment_id || h.a_line_board || h.b_line_board) {
                html += `<tr>
                    <td>${h.hop_order || '-'}</td>
                    <td>${esc(h.a_equipment_id || '')}</td>
                    <td>${esc(h.a_line_slot || '')}</td>
                    <td>${esc(h.a_line_port || '')}</td>
                    <td>${esc(h.a_line_board || '')}</td>
                    <td>${esc(h.a_tributary_slot || '')}</td>
                    <td>${esc(h.a_tributary_port || '')}</td>
                    <td>${esc(h.b_equipment_id || '')}</td>
                    <td>${esc(h.b_line_slot || '')}</td>
                    <td>${esc(h.b_line_port || '')}</td>
                    <td>${esc(h.b_line_board || '')}</td>
                    <td>${esc(h.b_tributary_slot || '')}</td>
                    <td>${esc(h.b_tributary_port || '')}</td>
                </tr>`;
            }
        });
        html += '</table></details>';
    }

    body.innerHTML = html;
}

function esc(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
