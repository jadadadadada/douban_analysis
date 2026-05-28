// 用户互动模块（电影浏览/收藏/评分）— 性能优化版

let browsePage = 1;
let favPage = 1;
let ratingPage = 1;
const MOVIE_PAGE_SIZE = 14;
const USER_LIST_PAGE_SIZE = 14;

// ==================== Tab 缓存 ====================
// 缓存各 tab 已加载的 HTML，切换时直接恢复，不再重复请求
const tabCache = {};
const userStateCache = {
    username: '',
    favSet: null,
    ratingMap: null
};

// 使缓存失效（用户执行收藏/评分等操作后）
function invalidateCache(tab) {
    if (tab) {
        delete tabCache[tab];
    } else {
        Object.keys(tabCache).forEach(k => delete tabCache[k]);
    }
}

function invalidateUserStateCache() {
    userStateCache.username = '';
    userStateCache.favSet = null;
    userStateCache.ratingMap = null;
}

// ==================== 检查登录状态 ====================
function isLoggedIn() {
    return document.getElementById('user-area').style.display === 'flex';
}

function getCurrentUsername() {
    return isLoggedIn() ? document.getElementById('display-username').textContent : '';
}

// ==================== 海报懒加载 ====================
let imageObserver = null;

function initImageObserver() {
    if (imageObserver) return;
    if (!('IntersectionObserver' in window)) return;
    imageObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                const img = entry.target;
                const src = img.dataset.src;
                if (src) {
                    img.src = src;
                    img.removeAttribute('data-src');
                }
                imageObserver.unobserve(img);
            }
        });
    }, { rootMargin: '200px' });
}

function observeImages(container) {
    initImageObserver();
    if (!imageObserver) return;
    container.querySelectorAll('img[data-src]').forEach(function(img) {
        imageObserver.observe(img);
    });
}

// ==================== Tab 切换 ====================
function switchTab(tab) {
    document.querySelectorAll('.panel-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelector(`.panel-tab[data-tab="${tab}"]`).classList.add('active');
    document.getElementById('tab-' + tab).classList.add('active');

    // 检查缓存：如已加载过且未失效，直接恢复缓存内容
    if (tabCache[tab]) {
        restoreFromCache(tab);
        return;
    }

    if (tab === 'browse') loadMovieList(browsePage);
    if (tab === 'favorites') loadFavorites(favPage);
    if (tab === 'my-ratings') loadMyRatings(ratingPage);
}

// 从缓存恢复 tab 内容（不重新请求 API）
function restoreFromCache(tab) {
    const cache = tabCache[tab];
    if (!cache) return;

    if (tab === 'browse') {
        document.getElementById('movie-list').innerHTML = cache.html;
        renderPagination('browse-pagination', cache.total, MOVIE_PAGE_SIZE, browsePage, loadMovieList);
        observeImages(document.getElementById('movie-list'));
    } else if (tab === 'favorites') {
        document.getElementById('fav-list').innerHTML = cache.html;
        renderPagination('fav-pagination', cache.total, USER_LIST_PAGE_SIZE, favPage, loadFavorites);
        observeImages(document.getElementById('fav-list'));
    } else if (tab === 'my-ratings') {
        document.getElementById('rating-list').innerHTML = cache.html;
        renderPagination('rating-pagination', cache.total, USER_LIST_PAGE_SIZE, ratingPage, loadMyRatings);
        observeImages(document.getElementById('rating-list'));
    }
}

// ==================== 批量获取用户状态 ====================
// 一次请求获取用户所有收藏 ID，返回 Set
async function fetchFavSet() {
    if (!isLoggedIn()) {
        invalidateUserStateCache();
        return new Set();
    }
    const username = getCurrentUsername();
    if (userStateCache.username === username && userStateCache.favSet) {
        return userStateCache.favSet;
    }
    try {
        const data = await request('/api/favorites?page=1&size=100');
        if (data && data.movies) {
            userStateCache.username = username;
            userStateCache.favSet = new Set(data.movies.map(m => m.id));
            return userStateCache.favSet;
        }
    } catch (e) {}
    return new Set();
}

// 一次请求获取用户所有评分，返回 Map<movieId, rating>
async function fetchRatingMap() {
    if (!isLoggedIn()) {
        invalidateUserStateCache();
        return new Map();
    }
    const username = getCurrentUsername();
    if (userStateCache.username === username && userStateCache.ratingMap) {
        return userStateCache.ratingMap;
    }
    try {
        const data = await request('/api/ratings/my?page=1&size=100');
        if (data && data.movies) {
            const map = new Map();
            data.movies.forEach(m => {
                if (m.user_rating) map.set(m.id, m.user_rating);
            });
            userStateCache.username = username;
            userStateCache.ratingMap = map;
            return userStateCache.ratingMap;
        }
    } catch (e) {}
    return new Map();
}

// ==================== 获取当前筛选条件 ====================
function getBrowseFilters() {
    const genre = document.getElementById('filter-genre').value;
    const year = document.getElementById('filter-year').value;
    const country = document.getElementById('filter-country').value;
    const minRating = parseFloat(document.getElementById('filter-rating').value);
    const params = {};
    if (genre) params.genre = genre;
    if (year) params.year = year;
    if (country) params.country = country;
    if (minRating && minRating > 0) params.min_rating = minRating;
    return params;
}

function buildBrowseQuery(page, filters) {
    const query = new URLSearchParams();
    query.append('page', page);
    query.append('size', MOVIE_PAGE_SIZE);
    if (filters.genre) query.append('genre', filters.genre);
    if (filters.year) query.append('year', filters.year);
    if (filters.country) query.append('country', filters.country);
    if (filters.min_rating) query.append('min_rating', filters.min_rating);
    return '/api/movies?' + query.toString();
}

function escapeHtml(value) {
    return String(value || '').replace(/[&<>"']/g, function (char) {
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[char];
    });
}

function showMovieLoading(containerId, text = '加载中...', keepHeight = false) {
    const container = document.getElementById(containerId);
    if (container) {
        if (keepHeight) {
            container.style.minHeight = container.offsetHeight + 'px';
        }
        container.innerHTML = `<div class="movie-loading">${text}</div>`;
    }
}

function setMovieGridBusy(containerId, isBusy, text = '正在更新...') {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.classList.toggle('is-loading', isBusy);
    if (isBusy) {
        container.dataset.loadingText = text;
    } else {
        delete container.dataset.loadingText;
    }
}

function setPaginationBusy(containerId, isBusy) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.classList.toggle('is-loading', isBusy);
    container.querySelectorAll('button').forEach(btn => {
        btn.disabled = isBusy;
    });
}

function showMovieEmpty(containerId, text) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<p class="empty-hint">${text}</p>`;
    }
}

function resetMovieContainerHeight(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.style.minHeight = '';
    }
}

function scrollUserPanelToTop(behavior = 'auto') {
    const panel = document.getElementById('user-panel');
    if (!panel) return;
    const top = panel.getBoundingClientRect().top + window.pageYOffset - 12;
    window.scrollTo({ top, behavior: behavior });
}

// ==================== 加载电影列表（优化版）====================
async function loadMovieList(page, shouldScrollTop = false) {
    browsePage = page || 1;
    const filters = getBrowseFilters();
    const grid = document.getElementById('movie-list');
    const hasCards = grid && grid.querySelector('.movie-card');
    if (shouldScrollTop) {
        scrollUserPanelToTop('auto');
    }
    if (hasCards) {
        setMovieGridBusy('movie-list', true);
    } else {
        showMovieLoading('movie-list');
    }
    setPaginationBusy('browse-pagination', true);

    try {
        // 并行请求：电影列表 + 已缓存的用户收藏/评分状态
        const [data, favSet, ratingMap] = await Promise.all([
            request(buildBrowseQuery(browsePage, filters)),
            fetchFavSet(),
            fetchRatingMap()
        ]);
        if (!data) {
            showMovieEmpty('movie-list', '电影列表加载失败');
            renderPagination('browse-pagination', 0, MOVIE_PAGE_SIZE, browsePage, loadMovieList);
            return;
        }

        grid.innerHTML = '';
        resetMovieContainerHeight('movie-list');

        if (!data.movies || data.movies.length === 0) {
            showMovieEmpty('movie-list', '当前筛选条件下暂无电影');
            renderPagination('browse-pagination', 0, MOVIE_PAGE_SIZE, browsePage, loadMovieList);
            return;
        }

        // 同步创建卡片（无需逐个请求收藏/评分状态）
        data.movies.forEach(m => {
            grid.appendChild(createMovieCard(m, favSet.has(m.id), ratingMap.get(m.id)));
        });

        renderPagination('browse-pagination', data.total, MOVIE_PAGE_SIZE, browsePage, loadMovieList);
        observeImages(grid);

        // 缓存结果
        tabCache['browse'] = { html: grid.innerHTML, total: data.total };
    } finally {
        setMovieGridBusy('movie-list', false);
        setPaginationBusy('browse-pagination', false);
    }
}

// ==================== 创建电影卡片（同步版）====================
// 收藏状态和评分通过参数传入，不再逐个请求 API
function createMovieCard(movie, favorited, userRating, options = {}) {
    const card = document.createElement('div');
    card.className = 'movie-card';

    const safeTitle = escapeHtml(movie.title || '未命名电影');
    const yearText = movie.year ? `${movie.year}年` : '年份未知';
    const doubanRating = movie.rating || movie.douban_rating;
    const mode = options.mode || 'browse';

    // 海报懒加载：本地路径直接用，豆瓣 URL 走服务端代理
    let posterSrc = '';
    if (movie.poster_url) {
        posterSrc = movie.poster_url.startsWith('/static/')
            ? movie.poster_url
            : '/api/proxy/poster?url=' + encodeURIComponent(movie.poster_url);
    }
    const safePosterSrc = escapeHtml(posterSrc);
    const posterHtml = posterSrc
        ? `<img data-src="${safePosterSrc}" alt="${safeTitle}" onerror="this.onerror=null;this.style.display='none';this.parentNode.innerHTML='<div class=\\'no-poster\\'>暂无海报</div>'">`
        : '<div class="no-poster">暂无海报</div>';
    const userScoreHtml = mode === 'rating' && userRating
        ? `<span class="user-score-badge">我的评分 ${userRating} 分</span>`
        : '';
    const doubanScoreHtml = doubanRating
        ? `<span class="douban-score">豆瓣 ${doubanRating}</span>`
        : '<span class="douban-score">暂无评分</span>';

    card.innerHTML = `
        <div class="movie-poster">
            ${posterHtml}
        </div>
        <div class="movie-info">
            <h4 class="movie-title" title="${safeTitle}">${safeTitle}</h4>
            <p class="movie-meta">${yearText}</p>
            <div class="movie-score-row">
                ${doubanScoreHtml}
                ${userScoreHtml}
            </div>
            <div class="movie-actions">
                <button class="fav-btn ${favorited ? 'favorited' : ''}" onclick="toggleFavorite(${movie.id}, this)" title="${favorited ? '取消收藏' : '收藏'}">
                    ${favorited ? '&#9829;' : '&#9825;'}
                </button>
                <div class="rating-stars" data-movie-id="${movie.id}">
                    ${renderStars(movie.id, userRating)}
                </div>
            </div>
        </div>
    `;

    return card;
}

// ==================== 渲染星星评分 ====================
function renderStars(movieId, currentRating) {
    let html = '';
    const selectedRating = currentRating ? Math.round(currentRating) : null;
    for (let i = 1; i <= 5; i++) {
        const filled = selectedRating && i <= selectedRating;
        const isSelected = selectedRating === i;
        const action = isSelected ? `clearRating(${movieId})` : `rateMovie(${movieId}, ${i})`;
        const title = isSelected ? '取消评分' : `${i}分`;
        html += `<span class="star ${filled ? 'star-filled' : ''}" onclick="${action}" title="${title}">${filled ? '&#9733;' : '&#9734;'}</span>`;
    }
    if (currentRating) {
        html += `<span class="my-rating-text" title="再次点击当前评分可取消">${currentRating}分</span>`;
    }
    return html;
}

// ==================== 收藏/取消收藏 ====================
function updateFavoriteButton(btn, favorited) {
    btn.classList.toggle('favorited', favorited);
    btn.innerHTML = favorited ? '&#9829;' : '&#9825;';
    btn.title = favorited ? '取消收藏' : '收藏';
}

function setFavoritePending(btn, isPending) {
    btn.disabled = isPending;
    btn.classList.toggle('is-pending', isPending);
}

function updateCachedFavSet(movieId, favorited) {
    if (!userStateCache.favSet) return;
    if (favorited) {
        userStateCache.favSet.add(movieId);
    } else {
        userStateCache.favSet.delete(movieId);
    }
}

async function toggleFavorite(movieId, btn) {
    if (!isLoggedIn()) {
        showModal('login-modal');
        return;
    }

    const isFav = btn.classList.contains('favorited');
    const nextFav = !isFav;
    const method = isFav ? 'DELETE' : 'POST';
    const url = isFav ? '/api/favorites/' + movieId : '/api/favorites';

    if (btn.dataset.pending === 'true') return;
    btn.dataset.pending = 'true';
    updateFavoriteButton(btn, nextFav);
    setFavoritePending(btn, true);
    updateCachedFavSet(movieId, nextFav);

    try {
        const resp = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: method === 'POST' ? JSON.stringify({ movie_id: movieId }) : undefined
        });
        const result = await resp.json();
        if (!resp.ok || result.code !== 200) {
            updateFavoriteButton(btn, isFav);
            updateCachedFavSet(movieId, isFav);
            return;
        }

        invalidateCache('browse');
        invalidateCache('favorites');
    } catch (e) {
        updateFavoriteButton(btn, isFav);
        updateCachedFavSet(movieId, isFav);
        console.error('收藏操作失败', e);
    } finally {
        delete btn.dataset.pending;
        setFavoritePending(btn, false);
    }
}

// ==================== 评分 ====================
function updateCachedRatingMap(movieId, rating) {
    if (userStateCache.ratingMap) {
        userStateCache.ratingMap.set(movieId, rating);
    }
}

function deleteCachedRating(movieId) {
    if (userStateCache.ratingMap) {
        userStateCache.ratingMap.delete(movieId);
    }
}

function restoreCachedRatingMap(movieId, previousRating, hadPreviousRating) {
    if (!userStateCache.ratingMap) return;
    if (hadPreviousRating) {
        userStateCache.ratingMap.set(movieId, previousRating);
    } else {
        userStateCache.ratingMap.delete(movieId);
    }
}

function setRatingPending(movieId, isPending) {
    document.querySelectorAll(`.rating-stars[data-movie-id="${movieId}"]`).forEach(container => {
        container.classList.toggle('is-pending', isPending);
        container.dataset.pending = isPending ? 'true' : '';
    });
}

function snapshotRatingViews(movieId) {
    return Array.from(document.querySelectorAll(`.rating-stars[data-movie-id="${movieId}"]`)).map(container => {
        const card = container.closest('.movie-card');
        const badge = card ? card.querySelector('.user-score-badge') : null;
        return {
            container: container,
            html: container.innerHTML,
            badge: badge,
            badgeText: badge ? badge.textContent : null
        };
    });
}

function updateRatingViews(movieId, rating) {
    document.querySelectorAll(`.rating-stars[data-movie-id="${movieId}"]`).forEach(container => {
        container.innerHTML = renderStars(movieId, rating);
        const card = container.closest('.movie-card');
        const badge = card ? card.querySelector('.user-score-badge') : null;
        if (badge) {
            badge.textContent = rating ? `我的评分 ${rating} 分` : '已取消评分';
        }
    });
}

function restoreRatingViews(snapshots) {
    snapshots.forEach(snapshot => {
        snapshot.container.innerHTML = snapshot.html;
        if (snapshot.badge) {
            snapshot.badge.textContent = snapshot.badgeText;
        }
    });
}

async function rateMovie(movieId, rating) {
    if (!isLoggedIn()) {
        showModal('login-modal');
        return;
    }

    const activeContainer = document.querySelector(`.rating-stars[data-movie-id="${movieId}"]`);
    if (activeContainer && activeContainer.dataset.pending === 'true') return;

    const snapshots = snapshotRatingViews(movieId);
    const hadPreviousRating = userStateCache.ratingMap ? userStateCache.ratingMap.has(movieId) : false;
    const previousRating = hadPreviousRating ? userStateCache.ratingMap.get(movieId) : null;
    updateRatingViews(movieId, rating);
    setRatingPending(movieId, true);
    updateCachedRatingMap(movieId, rating);

    try {
        const resp = await fetch('/api/ratings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ movie_id: movieId, rating: rating })
        });
        const result = await resp.json();
        if (!resp.ok || result.code !== 200) {
            restoreRatingViews(snapshots);
            restoreCachedRatingMap(movieId, previousRating, hadPreviousRating);
            return;
        }

        invalidateCache('browse');
        invalidateCache('my-ratings');
    } catch (e) {
        restoreRatingViews(snapshots);
        restoreCachedRatingMap(movieId, previousRating, hadPreviousRating);
        console.error('评分失败', e);
    } finally {
        setRatingPending(movieId, false);
    }
}

async function clearRating(movieId) {
    if (!isLoggedIn()) {
        showModal('login-modal');
        return;
    }

    const activeContainer = document.querySelector(`.rating-stars[data-movie-id="${movieId}"]`);
    if (activeContainer && activeContainer.dataset.pending === 'true') return;

    const snapshots = snapshotRatingViews(movieId);
    const hadPreviousRating = userStateCache.ratingMap ? userStateCache.ratingMap.has(movieId) : false;
    const previousRating = hadPreviousRating ? userStateCache.ratingMap.get(movieId) : null;
    updateRatingViews(movieId, null);
    setRatingPending(movieId, true);
    deleteCachedRating(movieId);

    try {
        const resp = await fetch('/api/ratings/' + movieId, {
            method: 'DELETE'
        });
        const result = await resp.json();
        if (!resp.ok || result.code !== 200) {
            restoreRatingViews(snapshots);
            restoreCachedRatingMap(movieId, previousRating, hadPreviousRating);
            return;
        }

        invalidateCache('browse');
        invalidateCache('my-ratings');
    } catch (e) {
        restoreRatingViews(snapshots);
        restoreCachedRatingMap(movieId, previousRating, hadPreviousRating);
        console.error('取消评分失败', e);
    } finally {
        setRatingPending(movieId, false);
    }
}

// ==================== 加载我的收藏 ====================
async function loadFavorites(page, shouldScrollTop = false) {
    favPage = page || 1;
    if (!isLoggedIn()) {
        document.getElementById('fav-login-hint').style.display = 'flex';
        document.getElementById('fav-list').style.display = 'none';
        return;
    }
    document.getElementById('fav-login-hint').style.display = 'none';
    document.getElementById('fav-list').style.display = 'grid';
    const grid = document.getElementById('fav-list');
    const hasCards = grid && grid.querySelector('.movie-card');
    if (shouldScrollTop) {
        scrollUserPanelToTop('auto');
    }
    if (hasCards) {
        setMovieGridBusy('fav-list', true);
    } else {
        showMovieLoading('fav-list');
    }
    setPaginationBusy('fav-pagination', true);

    try {
        const data = await request('/api/favorites?page=' + favPage + '&size=' + USER_LIST_PAGE_SIZE);
        if (!data) {
            showMovieEmpty('fav-list', '收藏列表加载失败');
            renderPagination('fav-pagination', 0, USER_LIST_PAGE_SIZE, favPage, loadFavorites);
            return;
        }

        grid.innerHTML = '';
        resetMovieContainerHeight('fav-list');

        if (data.movies.length === 0) {
            showMovieEmpty('fav-list', '还没有收藏电影，去"电影浏览"中收藏吧');
            renderPagination('fav-pagination', 0, USER_LIST_PAGE_SIZE, favPage, loadFavorites);
            return;
        }

        // 收藏列表中的电影默认已收藏，无需额外查询
        data.movies.forEach(m => {
            grid.appendChild(createMovieCard(m, true, null, { mode: 'favorite' }));
        });

        renderPagination('fav-pagination', data.total, USER_LIST_PAGE_SIZE, favPage, loadFavorites);
        observeImages(grid);

        // 缓存结果
        tabCache['favorites'] = { html: grid.innerHTML, total: data.total };
    } finally {
        setMovieGridBusy('fav-list', false);
        setPaginationBusy('fav-pagination', false);
    }
}

// ==================== 加载我的评分 ====================
async function loadMyRatings(page, shouldScrollTop = false) {
    ratingPage = page || 1;
    if (!isLoggedIn()) {
        document.getElementById('rate-login-hint').style.display = 'flex';
        document.getElementById('rating-list').style.display = 'none';
        return;
    }
    document.getElementById('rate-login-hint').style.display = 'none';
    document.getElementById('rating-list').style.display = 'grid';
    const grid = document.getElementById('rating-list');
    const hasCards = grid && grid.querySelector('.movie-card');
    if (shouldScrollTop) {
        scrollUserPanelToTop('auto');
    }
    if (hasCards) {
        setMovieGridBusy('rating-list', true);
    } else {
        showMovieLoading('rating-list');
    }
    setPaginationBusy('rating-pagination', true);

    try {
        const data = await request('/api/ratings/my?page=' + ratingPage + '&size=' + USER_LIST_PAGE_SIZE);
        if (!data) {
            showMovieEmpty('rating-list', '评分列表加载失败');
            renderPagination('rating-pagination', 0, USER_LIST_PAGE_SIZE, ratingPage, loadMyRatings);
            return;
        }

        grid.innerHTML = '';
        resetMovieContainerHeight('rating-list');

        if (data.movies.length === 0) {
            showMovieEmpty('rating-list', '还没有评分，去"电影浏览"中评分吧');
            renderPagination('rating-pagination', 0, USER_LIST_PAGE_SIZE, ratingPage, loadMyRatings);
            return;
        }

        // 评分列表自带 user_rating，无需额外查询
        data.movies.forEach(m => {
            grid.appendChild(createMovieCard(m, false, m.user_rating, { mode: 'rating' }));
        });

        renderPagination('rating-pagination', data.total, USER_LIST_PAGE_SIZE, ratingPage, loadMyRatings);
        observeImages(grid);

        // 缓存结果
        tabCache['my-ratings'] = { html: grid.innerHTML, total: data.total };
    } finally {
        setMovieGridBusy('rating-list', false);
        setPaginationBusy('rating-pagination', false);
    }
}

// ==================== 渲染分页 ====================
function renderPagination(containerId, total, size, current, callback) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const totalPages = Math.ceil(total / size);
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = '';
    if (current > 1) html += `<button type="button" onclick="(${callback.name})(${current - 1})">上一页</button>`;
    html += `<span class="page-info">第 ${current} / ${totalPages} 页</span>`;
    if (current < totalPages) html += `<button type="button" onclick="(${callback.name})(${current + 1})">下一页</button>`;
    container.innerHTML = html;
}

// 由 auth.js 在 checkAuth 完成后调用 loadMovieList
