// API 调用封装模块

/**
 * 通用请求函数
 * @param {string} url - 请求地址
 * @returns {Promise} - 响应数据
 */
async function request(url) {
    try {
        const response = await fetch(url);
        const result = await response.json();
        if (result.code === 200) {
            return result.data;
        } else {
            console.error('API 错误:', result.msg);
            return null;
        }
    } catch (error) {
        console.error('请求失败:', error);
        return null;
    }
}

/**
 * 构建筛选查询参数
 * @param {Object} filters - 筛选条件
 * @returns {string} - URL 查询字符串
 */
function buildFilterQuery(filters = {}) {
    const query = new URLSearchParams();
    if (filters.genre) query.append('genre', filters.genre);
    if (filters.year) query.append('year', filters.year);
    if (filters.country) query.append('country', filters.country);
    if (filters.min_rating && filters.min_rating > 0) query.append('min_rating', filters.min_rating);
    const str = query.toString();
    return str ? '?' + str : '';
}

/**
 * 获取电影列表
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
async function fetchMovies(params = {}) {
    const query = new URLSearchParams();
    if (params.page) query.append('page', params.page);
    if (params.size) query.append('size', params.size);
    if (params.genre) query.append('genre', params.genre);
    if (params.year) query.append('year', params.year);
    if (params.min_rating) query.append('min_rating', params.min_rating);
    if (params.country) query.append('country', params.country);
    return request('/api/movies?' + query.toString());
}

/**
 * 获取电影详情
 * @param {number} id - 电影 ID
 * @returns {Promise}
 */
async function fetchMovieDetail(id) {
    return request('/api/movies/' + id);
}

/**
 * 搜索电影
 * @param {string} keyword - 搜索关键词
 * @returns {Promise}
 */
async function searchMovies(keyword) {
    return request('/api/movies/search?keyword=' + encodeURIComponent(keyword));
}

/**
 * 获取类型分布数据
 * @param {Object} filters - 筛选条件
 * @returns {Promise}
 */
async function fetchGenreDistribution(filters = {}) {
    return request('/api/stats/genre-distribution' + buildFilterQuery(filters));
}

/**
 * 获取评分分布数据
 * @param {Object} filters - 筛选条件
 * @returns {Promise}
 */
async function fetchRatingDistribution(filters = {}) {
    return request('/api/stats/rating-distribution' + buildFilterQuery(filters));
}

/**
 * 获取年代趋势数据
 * @param {Object} filters - 筛选条件
 * @returns {Promise}
 */
async function fetchYearTrend(filters = {}) {
    return request('/api/stats/year-trend' + buildFilterQuery(filters));
}

/**
 * 获取国家分布数据
 * @param {Object} filters - 筛选条件
 * @returns {Promise}
 */
async function fetchCountryDistribution(filters = {}) {
    return request('/api/stats/country-distribution' + buildFilterQuery(filters));
}

/**
 * 获取评分最高电影
 * @param {number} limit - 数量限制
 * @param {Object} filters - 筛选条件
 * @returns {Promise}
 */
async function fetchTopRated(limit = 20, filters = {}) {
    const params = new URLSearchParams();
    params.append('limit', limit);
    if (filters.genre) params.append('genre', filters.genre);
    if (filters.year) params.append('year', filters.year);
    if (filters.country) params.append('country', filters.country);
    if (filters.min_rating && filters.min_rating > 0) params.append('min_rating', filters.min_rating);
    return request('/api/stats/top-rated?' + params.toString());
}

/**
 * 获取热力图数据
 * @param {Object} filters - 筛选条件
 * @returns {Promise}
 */
async function fetchGenreYearHeatmap(filters = {}) {
    return request('/api/stats/genre-year-heatmap' + buildFilterQuery(filters));
}

/**
 * 获取导演-演员关系数据
 * @param {Object} filters - 筛选条件
 * @returns {Promise}
 */
async function fetchDirectorNetwork(filters = {}) {
    return request('/api/stats/director-network' + buildFilterQuery(filters));
}

/**
 * 获取词云数据
 * @param {Object} filters - 筛选条件
 * @returns {Promise}
 */
async function fetchWordcloudData(filters = {}) {
    return request('/api/stats/summary-wordcloud' + buildFilterQuery(filters));
}

/**
 * 获取时长-评分数据
 * @param {Object} filters - 筛选条件
 * @returns {Promise}
 */
async function fetchDurationRating(filters = {}) {
    return request('/api/stats/duration-rating' + buildFilterQuery(filters));
}

/**
 * 获取核心指标统计
 * @param {Object} filters - 筛选条件
 * @returns {Promise}
 */
async function fetchSummaryStats(filters = {}) {
    return request('/api/stats/summary-stats' + buildFilterQuery(filters));
}

/**
 * 获取筛选选项
 * @returns {Promise}
 */
async function fetchFilters() {
    const [genres, years, countries] = await Promise.all([
        request('/api/filters/genres'),
        request('/api/filters/years'),
        request('/api/filters/countries')
    ]);
    return { genres, years, countries };
}
