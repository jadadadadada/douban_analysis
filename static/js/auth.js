// 用户认证模块

// 模态框显示/隐藏
function showModal(id) {
    document.getElementById(id).style.display = 'flex';
}

function hideModal(id) {
    document.getElementById(id).style.display = 'none';
    // 清空错误信息
    const errEl = document.getElementById(id).querySelector('.form-error');
    if (errEl) errEl.textContent = '';
}

function switchToRegister() {
    hideModal('login-modal');
    showModal('register-modal');
}

function switchToLogin() {
    hideModal('register-modal');
    showModal('login-modal');
}

// 点击遮罩层关闭模态框
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.style.display = 'none';
    }
});

// 检查登录状态
async function checkAuth() {
    try {
        const resp = await fetch('/api/auth/me');
        const result = await resp.json();
        if (result.code === 200 && result.data) {
            showLoggedIn(result.data.username);
        } else {
            showLoggedOut();
        }
    } catch (e) {
        showLoggedOut();
    }
}

function showLoggedIn(username) {
    if (typeof invalidateUserStateCache === 'function') {
        invalidateUserStateCache();
    }
    document.getElementById('guest-area').style.display = 'none';
    document.getElementById('user-area').style.display = 'flex';
    document.getElementById('display-username').textContent = username;
}

function showLoggedOut() {
    if (typeof invalidateUserStateCache === 'function') {
        invalidateUserStateCache();
    }
    document.getElementById('guest-area').style.display = 'flex';
    document.getElementById('user-area').style.display = 'none';
}

// 登录
async function doLogin() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('login-error');
    errorEl.textContent = '';

    if (!username || !password) {
        errorEl.textContent = '请输入用户名和密码';
        return;
    }

    try {
        const resp = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const result = await resp.json();
        if (result.code === 200) {
            hideModal('login-modal');
            showLoggedIn(result.data.username);
            document.getElementById('login-username').value = '';
            document.getElementById('login-password').value = '';
        } else {
            errorEl.textContent = result.msg;
        }
    } catch (e) {
        errorEl.textContent = '网络错误，请重试';
    }
}

// 注册
async function doRegister() {
    const username = document.getElementById('reg-username').value.trim();
    const password = document.getElementById('reg-password').value;
    const email = document.getElementById('reg-email').value.trim();
    const errorEl = document.getElementById('register-error');
    errorEl.textContent = '';

    if (!username || !password) {
        errorEl.textContent = '请输入用户名和密码';
        return;
    }

    try {
        const resp = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, email })
        });
        const result = await resp.json();
        if (result.code === 200) {
            hideModal('register-modal');
            showLoggedIn(result.data.username);
            document.getElementById('reg-username').value = '';
            document.getElementById('reg-password').value = '';
            document.getElementById('reg-email').value = '';
        } else {
            errorEl.textContent = result.msg;
        }
    } catch (e) {
        errorEl.textContent = '网络错误，请重试';
    }
}

// 登出
async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
    } catch (e) {
        // 忽略错误
    }
    showLoggedOut();
}

// 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', async function () {
    await checkAuth();
    // auth 检查完成后再加载电影列表
    if (typeof loadMovieList === 'function') {
        loadMovieList(1);
    }
});
