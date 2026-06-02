const tbody = document.querySelector('.trains-list tbody');
const placeholder = document.getElementById('placeholder');
const ordersContainer = document.getElementById('orders-container');
const logoutBtn = document.getElementById('logout-btn');

// 渲染我的订单以及退票相关
async function loadMyOrders() {
    try {
        const res = await fetch('/api/my-orders');
        const data = await res.json();
        if (data.success) {
            if (data.data.length === 0) {
                ordersContainer.innerHTML = '<p style="color:#7f8c8d; font-style:italic;">暂无订单</p>';
            } else {
                let html = '';
                data.data.forEach(order => {
                    const d = new Date(order.departure_time);
                    const timeStr = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;

                    let statusText = '';
                    let statusColor = '';
                    let buttonHtml = '';
                    let groupInfoText = '';

                    if (order.is_group) {
                        statusText = order.group_status === 'paid' ? '团体已支付' : '团体已退票';
                        statusColor = '#8e44ad';

                        if (order.is_applicant && order.group_status === 'paid') {
                            groupInfoText = `<p style="margin-top:4px;color:#8e44ad;font-size:13px;">
                                                团体票：共 ${order.total_passengers} 张</p>`;

                            buttonHtml = `
                                <button class="cancel-btn"
                                    onclick="cancelGroup('${order.group_id}')"
                                    style="margin-top:8px;padding:4px 10px;
                                    background:#8e44ad;color:white;border:none;
                                    border-radius:3px;cursor:pointer;">
                                    团体退票
                                </button>`;
                        } else {
                            buttonHtml = `<span style="color:#8e44ad;font-style:italic;">团体购票</span>`;
                        }
                    } else {
                        if (order.status === 'paid') {
                            statusText = '已支付';
                            statusColor = '#27ae60';
                            buttonHtml = `
                                <button class="cancel-btn"
                                    onclick="cancelOrder(${order.order_id})"
                                    style="margin-top:8px;padding:4px 10px;
                                    background:#e74c3c;color:white;border:none;
                                    border-radius:3px;">
                                    退票
                                </button>`;
                        } else if (order.status === 'cancelled') {
                            statusText = '已取消';
                            statusColor = '#7f8c8d';
                            buttonHtml = `<span style="color:#7f8c8d;">无法操作</span>`;
                        }
                    }

                    html += `
                        <div class="order-item">
                            <p><span class="order-label">车次：</span>${order.train_number}</p>
                            <p><span class="order-label">出发站：</span>${order.departure}</p>
                            <p><span class="order-label">到达站：</span>${order.destination}</p>
                            <p><span class="order-label">时间：</span>${timeStr}</p>
                            <p><span class="order-label">票价：</span>¥${parseFloat(order.price).toFixed(2)}</p>
                            <p><span class="order-label">状态：</span>
                                <span style="color:${statusColor};font-weight:bold;">
                                    ${statusText}
                                </span>
                            </p>
                            ${groupInfoText}
                            <div class="order-actions">
                                ${buttonHtml}
                            </div>
                        </div>`;});
                ordersContainer.innerHTML = html;
            }
        } else {
            ordersContainer.innerHTML = '<p style="color:#e74c3c;">请先登录</p>';
        }
    } catch (err) {
        console.error(err);
        ordersContainer.innerHTML = '<p>加载失败</p>';
    }
}

// 退出登录
async function handleLogout() {
    if (!confirm('确定要退出登录吗？')) return;
    try {
        const res = await fetch('/api/logout', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            alert('已退出登录');
            window.location.href = '/';
        } else {
            alert('退出失败');
        }
    } catch (err) {
        console.error(err);
        alert('网络错误，退出失败');
    }
}

// 退票函数
async function cancelOrder(orderId) {
    if (!confirm('确定要退掉这张车票吗？退票后不可恢复！')) return;

    try {
        const res = await fetch('/api/cancel-order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_id: orderId })
        });

        const data = await res.json();
        if (data.success) {
            alert('✅ 退票成功！');
            loadMyOrders();
            const dep = document.getElementById('departure').value.trim();
            const dest = document.getElementById('destination').value.trim();
            const date = document.getElementById('date').value;
            if (dep || dest || date) {
                searchTrains();
            }
        } else {
            alert('❌ ' + data.msg);
        }
    } catch (err) {
        console.error(err);
        alert('网络错误，请重试');
    }
}

// 购票
async function bookTicket(trainId) {
    if (!confirm('确认购买此车票？')) return;

    try {
        const res = await fetch('/api/book', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ train_id: trainId })
        });

        const data = await res.json();
        if (data.success) {
            alert('🎉 购票成功！');
            searchTrains();
            loadMyOrders();
        } else {
            alert('❌ ' + data.msg);
        }
    } catch (err) {
        console.error(err);
        alert('网络错误，请重试');
    }
}

// 查询车次
async function searchTrains() {
    const departure = document.getElementById('departure').value.trim();
    const destination = document.getElementById('destination').value.trim();
    const date = document.getElementById('date').value;

    if (!departure && !destination && !date) {
        alert('请至少填写一个查询条件');
        return;
    }

    const url = `/api/trains?departure=${encodeURIComponent(departure)}&destination=${encodeURIComponent(destination)}&date=${date}`;
    
    try {
        const res = await fetch(url);
        const data = await res.json();
        if (data.success) {
            renderTrains(data.data);
        } else {
            alert('查询失败：' + data.msg);
            renderTrains([]);
        }
    } catch (err) {
        console.error(err);
        alert('网络错误，请重试');
        renderTrains([]);
    }
}

// 渲染车次列表
function renderTrains(trains) {
    // 没有查询结果
    if (trains.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7">暂无符合条件的车次</td></tr>';
        placeholder.style.display = 'none';
        return;
    }

    let html = '';

    trains.forEach(train => {
        // 时间格式化
        const d = new Date(train.departure_time);
        const timeStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} `
                    + `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;

        // 操作列内容
        let actionHtml = '';

        if (train.is_pre_sal === '1') {
            // 在售：可以购买、团购
            actionHtml = `
                <button class="buy-btn" onclick="bookTicket(${train.id})">购买</button>
                <button class="buy-btn"
                        style="background:#8e44ad;margin-left:6px;"
                        onclick="groupBook(${train.id})">
                        团购
                </button>
            `;
        } else if (train.is_pre_sal === '0') {
            // 预售：不可购买
            actionHtml = `<span style="color:#e67e22;font-weight:bold;">预售</span>`;
        }

        html += `
            <tr>
                <td>${train.train_number}</td>
                <td>${train.departure}</td>
                <td>${train.destination}</td>
                <td>${timeStr}</td>
                <td>¥${parseFloat(train.price).toFixed(2)}</td>
                <td>${train.available_seats}</td>
                <td>${actionHtml}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
    placeholder.style.display = 'none';
}


//团体购票与退票
async function cancelGroup(groupId) {
    if (!confirm('确认整团退票？此操作不可恢复！')) return;

    try {
        const res = await fetch('/api/cancel-group', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ group_id: groupId })
        });
        const data = await res.json();

        if (data.success) {
            alert('✅ 团体退票成功');
            loadMyOrders();
            searchTrains();
        } else {
            alert('❌ ' + data.msg);
        }
    } catch (e) {
        alert('网络错误');
    }
}

async function groupBook(trainId) {
    const countStr = prompt('请输入团体购票人数（至少 2 人）');
    const count = parseInt(countStr);

    if (!countStr || isNaN(count) || count < 2) {
        alert('人数必须是大于等于 2 的数字');
        return;
    }

    let passengers = [];

    for (let i = 0; i < count; i++) {
        const name = prompt(`请输入第 ${i + 1} 位乘客的姓名`);
        if (name === null || !name.trim()) {
            alert('团体购票已取消');
            return;
        }

        const idcard = prompt(`请输入 ${name} 的身份证号`);
        if (idcard === null) {
            alert('团体购票已取消');
            return;
        }

        passengers.push({
            real_name: name.trim(),
            idcard: idcard.trim()
        });
    }

    // 提交到后端
    try {
        const res = await fetch('/api/group-book', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                train_id: trainId,
                passengers
            })
        });

        const data = await res.json();
        if (data.success) {
            alert('🎉 团体购票成功！');
            loadMyOrders();
            searchTrains();
        } else {
            alert('❌ ' + data.msg);
        }
    } catch (e) {
        alert('网络错误，请稍后重试');
    }
}



// 绑定事件
document.querySelector('.search-btn').addEventListener('click', searchTrains);
logoutBtn.addEventListener('click', handleLogout);

// 页面加载时自动加载订单
window.addEventListener('load', () => {
    loadMyOrders();
});