function showMessage(elementId, text, isSuccess) {
    const el = document.getElementById(elementId);
    el.textContent = text;
    el.className = isSuccess ? 'msg success' : 'msg error';
}

function showRegister() {
    document.getElementById('loginForm').classList.remove('active');
    document.getElementById('registerForm').classList.add('active');
    // 清空消息和输入框
    document.getElementById('regMsg').textContent = '';
    document.getElementById('regUser').value = '';
    document.getElementById('regPass').value = '';
}

function showLogin() {
    document.getElementById('registerForm').classList.remove('active');
    document.getElementById('changePasswordForm').classList.remove('active');
    document.getElementById('loginForm').classList.add('active');
    
    document.getElementById('loginMsg').textContent = '';
    document.getElementById('loginUser').value = '';
    document.getElementById('loginPass').value = '';
}

function showChangePassword() {
    document.getElementById('loginForm').classList.remove('active');
    document.getElementById('registerForm').classList.remove('active');
    document.getElementById('changePasswordForm').classList.add('active');

    document.getElementById('cpMsg').textContent = '';
    document.getElementById('cpUser').value = '';
    document.getElementById('cpIdCard').value = '';
    document.getElementById('cpNewPass').value = '';
}


// 注册 API 调用
async function register() {
    const user = document.getElementById('regUser').value.trim();
    const pwd = document.getElementById('regPass').value;
    const realName = document.getElementById('regRealName').value.trim();
    const idcard = document.getElementById('regIdCard').value.trim();
    if (!user || !pwd || !realName || !idcard) {
        showMessage('regMsg', '请填写完整注册信息', false);
        return;
    }
    
        if (idcard.length !== 18) {
        showMessage('regMsg', '身份证号格式不正确', false);
        return;
    }

    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                username: user,
                password: pwd,
                real_name: realName,
                idcard: idcard})
        });
        const data = await res.json();
        showMessage('regMsg', data.msg || '注册失败', data.success);
        if (data.success) {
            setTimeout(() => {
                showLogin(); // 注册成功后自动切回登录
            }, 1500);
        }
    } catch (err) {
        console.error(err);
        showMessage('regMsg', '网络错误，请重试', false);
    }
}

//调用登录API
let userId = null;

async function login() {
    const user = document.getElementById('loginUser').value.trim();
    const pwd = document.getElementById('loginPass').value;
    if (!user || !pwd) {
        showMessage('loginMsg', '请输入用户名和密码', false);
        return;
    }

    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pwd })
        });
        const data = await res.json();

        if (data.success) {
            // ✅ 关键修改：使用后端返回的 redirect 路径
            showMessage('loginMsg', '登录成功！正在跳转...', true);
            setTimeout(() => {
                window.location.href = data.redirect; 
            }, 1000);
        } else {
            showMessage('loginMsg', data.msg || '登录失败', false);
        }
    } catch (err) {
        console.error(err);
        showMessage('loginMsg', '网络错误，请重试', false);
    }
}

//调用改密码api
async function changePassword() {
    const user = document.getElementById('cpUser').value.trim();
    const idcard = document.getElementById('cpIdCard').value.trim();
    const newPwd = document.getElementById('cpNewPass').value;

    if (!user || !idcard || !newPwd) {
        showMessage('cpMsg', '请填写完整信息', false);
        return;
    }

    if (idcard.length !== 18) {
        showMessage('cpMsg', '身份证号格式不正确', false);
        return;
    }

    try {
        const res = await fetch('/api/change_password', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                username: user,
                idcard: idcard,
                new_password: newPwd
            })
        });

        const data = await res.json();
        showMessage('cpMsg', data.msg || '修改失败', data.success);

        if (data.success) {
            setTimeout(showLogin, 1500);
        }
    } catch (err) {
        console.error(err);
        showMessage('cpMsg', '网络错误，请重试', false);
    }
}
