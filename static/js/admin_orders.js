async function loadAllOrders() {
    const tbody = document.getElementById('ordersBody');
    const emptyMsg = document.getElementById('emptyMsg');
    try {
        const res = await fetch('/api/admin/orders');
        const result = await res.json();
        if (!result.success) {
            alert('加载失败: ' + (result.msg || '未知错误'));
            return;
        }
        const orders = result.data;
        if (orders.length === 0) {
            tbody.innerHTML = '';
            emptyMsg.style.display = 'block';
        } else {
            emptyMsg.style.display = 'none';
            tbody.innerHTML = orders.map(o => `
                <tr>
                    <td>${o.order_id}</td>
                    <td>${o.user_name}</td>
                    <td><strong>${o.train_number}</strong></td>
                    <td>${o.departure} → ${o.destination}</td>
                    <td>${new Date(o.departure_time).toLocaleString('zh-CN')}</td>
                    <td>${new Date(o.order_time).toLocaleString('zh-CN')}</td>
                    <td>
                        <span class="status-${o.status}">
                            ${o.status === 'paid' ? '已支付' : '已取消'}
                        </span>
                    </td>

                    <td>
                        ${o.is_group 
                            ? '<span style="color:#8e44ad;font-weight:bold;">团体票</span>' 
                            : '单人票'}
                    </td>
                    <td>
                        ${o.group_id ?? '—'}
                    </td>

                    <td>
                        ${o.status === 'paid' 
                            ? `<button class="btn danger-btn" onclick="forceCancelOrder(${o.order_id})">强制退票</button>`
                            : `<span style="color:#999;">—</span>`
                        }
                    </td>
                </tr>
            `).join('');
        }
    } catch (err) {
        console.error(err);
        alert('网络错误');
    }
}

async function forceCancelOrder(orderId) {
    if (!confirm('⚠️ 确定要强制退票吗？此操作不可逆！')) return;
    try {
        const res = await fetch('/api/admin/cancel-order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_id: orderId })
        });
        const result = await res.json();
        alert(result.success ? '✅ 退票成功！' : '❌ ' + (result.msg || '失败'));
        if (result.success) loadAllOrders();
    } catch (err) {
        alert('网络错误');
    }
}

document.addEventListener('DOMContentLoaded', loadAllOrders);