console.log('admin.js loaded');

// ========== 刷新用户列表 ==========
document.getElementById('refreshUsers').addEventListener('click', async () => {
    const res = await fetch('/api/admin/users');
    const data = await res.json();
    const tbody = document.getElementById('userList');
    if (data.success) {
        tbody.innerHTML = data.data.map(user => `
            <tr>
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td>${user.role === 'admin' ? '管理员' : '普通用户'}</td>
                <td>
                    ${user.role === 'admin' 
                        ? `<button class="btn-up" onclick="updateRole(${user.id}, 'user')">降级为用户</button>`
                        : `<button class="btn-down" onclick="updateRole(${user.id}, 'admin')">升级为管理员</button>`}
                </td>
            </tr>
        `).join('');
    } else {
        tbody.innerHTML = `<tr><td colspan="4">加载失败：${data.msg}</td></tr>`;
    }
});

// ========== 修改角色 ==========
async function updateRole(userId, newRole) {
    const res = await fetch('/api/admin/update-user-role', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ user_id: userId, role: newRole })
    });
    const result = await res.json();
    alert(result.msg);
    if (result.success) {
        document.getElementById('refreshUsers').click();
    }
}