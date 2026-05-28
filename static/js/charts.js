// ECharts 图表初始化和渲染模块

// 图表实例存储
const charts = {};
const CHART_COLORS = ['#1c1c1c', '#3b82f6', '#0f9f8f', '#d97706', '#b42318', '#7c3aed', '#287d3c', '#c2410c'];
const CHART_META = {
    pie: 'chart-pie',
    bar: 'chart-bar',
    line: 'chart-line',
    map: 'chart-map',
    wordcloud: 'chart-wordcloud',
    heatmap: 'chart-heatmap',
    graph: 'chart-graph',
    scatter: 'chart-scatter',
    rank: 'chart-rank'
};
const CHART_AXIS_COLOR = '#5f5f5d';
const CHART_BORDER_COLOR = '#eceae4';
const CHART_GRID_COLOR = 'rgba(28, 28, 28, 0.06)';
const CHART_TEXT_COLOR = '#1c1c1c';

function mergeTextStyle(base, extra) {
    return Object.assign({}, base, extra || {});
}

function normalizeAxis(axis) {
    if (!axis || typeof axis !== 'object') return axis;
    const isValueAxis = axis.type === 'value' || !axis.type;
    const base = {
        axisLine: { lineStyle: { color: CHART_BORDER_COLOR } },
        axisTick: { lineStyle: { color: CHART_BORDER_COLOR } },
        axisLabel: { color: CHART_AXIS_COLOR, fontSize: 11, hideOverlap: true },
        nameTextStyle: { color: CHART_AXIS_COLOR, fontSize: 11 },
        splitLine: {
            show: isValueAxis,
            lineStyle: { color: CHART_GRID_COLOR, type: 'solid' }
        }
    };

    return Object.assign({}, base, axis, {
        axisLine: Object.assign({}, base.axisLine, axis.axisLine || {}),
        axisTick: Object.assign({}, base.axisTick, axis.axisTick || {}),
        axisLabel: Object.assign({}, base.axisLabel, axis.axisLabel || {}),
        nameTextStyle: Object.assign({}, base.nameTextStyle, axis.nameTextStyle || {}),
        splitLine: Object.assign({}, base.splitLine, axis.splitLine || {})
    });
}

function normalizeAxisCollection(axis) {
    return Array.isArray(axis) ? axis.map(normalizeAxis) : normalizeAxis(axis);
}

function applyChartDefaults(option) {
    if (option.tooltip) {
        option.tooltip = Object.assign({
            confine: true,
            backgroundColor: 'rgba(252, 251, 248, 0.98)',
            borderColor: CHART_BORDER_COLOR,
            borderWidth: 1,
            textStyle: { color: CHART_TEXT_COLOR, fontSize: 12 },
            extraCssText: 'box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border-radius: 6px;'
        }, option.tooltip, {
            textStyle: mergeTextStyle({ color: CHART_TEXT_COLOR, fontSize: 12 }, option.tooltip.textStyle)
        });
    }

    if (option.legend && !Array.isArray(option.legend)) {
        option.legend = Object.assign({
            textStyle: { color: CHART_AXIS_COLOR, fontSize: 12 },
            itemGap: 14
        }, option.legend, {
            textStyle: mergeTextStyle({ color: CHART_AXIS_COLOR, fontSize: 12 }, option.legend.textStyle)
        });
    }

    if (option.grid) {
        option.grid = Object.assign({ containLabel: true }, option.grid);
    }

    if (option.xAxis) option.xAxis = normalizeAxisCollection(option.xAxis);
    if (option.yAxis) option.yAxis = normalizeAxisCollection(option.yAxis);

    if (option.visualMap && !Array.isArray(option.visualMap)) {
        option.visualMap = Object.assign({
            textStyle: { color: CHART_AXIS_COLOR, fontSize: 11 }
        }, option.visualMap, {
            textStyle: mergeTextStyle({ color: CHART_AXIS_COLOR, fontSize: 11 }, option.visualMap.textStyle)
        });
    }

    return option;
}

/**
 * 创建或重建图表实例
 * @param {string} key - 图表标识
 * @param {string} elementId - DOM 元素 ID
 */
function createChart(key, elementId) {
    if (charts[key]) {
        charts[key].dispose();
    }
    const chartDom = document.getElementById(elementId);
    chartDom.innerHTML = '';
    const chart = echarts.init(chartDom);
    charts[key] = chart;
    return chart;
}

/**
 * 显示图表状态
 * @param {string} key - 图表标识
 * @param {string} elementId - DOM 元素 ID
 * @param {string} text - 状态文案
 * @param {boolean} isError - 是否错误状态
 */
function showChartState(key, elementId, text, isError = false) {
    if (charts[key]) {
        charts[key].dispose();
        delete charts[key];
    }
    const chartDom = document.getElementById(elementId);
    if (chartDom) {
        chartDom.innerHTML = `<div class="chart-state ${isError ? 'is-error' : ''}">${text}</div>`;
    }
}

function showChartEmpty(key, elementId) {
    showChartState(key, elementId, '暂无数据');
}

function showAllChartsLoading() {
    Object.entries(CHART_META).forEach(([key, elementId]) => {
        showChartState(key, elementId, '加载中...');
    });
}

function showAllChartsError() {
    Object.entries(CHART_META).forEach(([key, elementId]) => {
        showChartState(key, elementId, '加载失败', true);
    });
}

function renderChart(key, data, initFn) {
    if (data === null || data === undefined) {
        showChartState(key, CHART_META[key], '加载失败', true);
        return;
    }
    initFn(data);
}

// 中国地图数据（国家名称映射）
const COUNTRY_NAME_MAP = {
    '中国大陆': '中国', '中国香港': '中国', '中国台湾': '中国',
    '美国': '美国', '日本': '日本', '韩国': '韩国', '英国': '英国',
    '法国': '法国', '德国': '德国', '意大利': '意大利', '印度': '印度',
    '加拿大': '加拿大', '澳大利亚': '澳大利亚', '西班牙': '西班牙',
    '俄罗斯': '俄罗斯', '巴西': '巴西', '墨西哥': '墨西哥',
    '瑞典': '瑞典', '丹麦': '丹麦', '挪威': '挪威', '芬兰': '芬兰',
    '泰国': '泰国', '波兰': '波兰', '荷兰': '荷兰', '比利时': '比利时',
    '奥地利': '奥地利', '瑞士': '瑞士', '阿根廷': '阿根廷'
};

/**
 * 更新指标卡
 * @param {Object} data - 统计数据
 */
function updateIndicatorCards(data) {
    document.getElementById('total-movies').textContent = data ? (data.total_movies || 0) : '--';
    document.getElementById('avg-rating').textContent = data ? (data.avg_rating || '--') : '--';
    document.getElementById('total-directors').textContent = data ? (data.total_directors || 0) : '--';
    document.getElementById('total-actors').textContent = data ? (data.total_actors || 0) : '--';
}

/**
 * 初始化饼图（类型分布）
 * @param {Array} data - 类型数据
 */
function initPieChart(data) {
    if (!data || !data.length) {
        showChartEmpty('pie', 'chart-pie');
        return;
    }
    const chart = createChart('pie', 'chart-pie');

    const option = {
        color: CHART_COLORS,
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { type: 'scroll', bottom: 0, left: 'center' },
        series: [{
            type: 'pie',
            radius: ['35%', '65%'],
            center: ['50%', '45%'],
            itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
            label: { show: true, formatter: '{b}\n{d}%' },
            emphasis: {
                label: { show: true, fontSize: 14, fontWeight: 'bold' },
                itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' }
            },
            data: data.map(item => ({ name: item.name, value: item.count }))
        }]
    };

    chart.setOption(applyChartDefaults(option));
}

/**
 * 初始化柱状图（评分分布）
 * @param {Array} data - 评分分布数据
 */
function initBarChart(data) {
    if (!data || !data.length) {
        showChartEmpty('bar', 'chart-bar');
        return;
    }
    const chart = createChart('bar', 'chart-bar');

    const labels = ['0-5分', '5-6分', '6-7分', '7-8分', '8-9分', '9-10分'];
    const values = labels.map(label => {
        const item = data.find(d => d.range_label === label || d.name === label);
        return item ? item.count : 0;
    });

    const colors = ['#b42318', '#c2410c', '#d97706', '#287d3c', '#0f9f8f', '#3b82f6'];

    const option = {
        tooltip: { trigger: 'axis' },
        xAxis: {
            type: 'category',
            data: labels,
            axisLabel: { rotate: 0 }
        },
        yAxis: { type: 'value', name: '电影数量' },
        series: [{
            type: 'bar',
            data: values.map((v, i) => ({
                value: v,
                itemStyle: { color: colors[i], borderRadius: [4, 4, 0, 0] }
            })),
            barWidth: '50%',
            label: { show: true, position: 'top', formatter: '{c}' }
        }]
    };

    chart.setOption(applyChartDefaults(option));
}

/**
 * 初始化折线图（年代趋势，双 Y 轴）
 * @param {Array} data - 年代趋势数据
 */
function initLineChart(data) {
    if (!data || !data.length) {
        showChartEmpty('line', 'chart-line');
        return;
    }
    const chart = createChart('line', 'chart-line');

    const years = data.map(item => item.year);
    const counts = data.map(item => item.count);
    const ratings = data.map(item => item.avg_rating);

    const option = {
        tooltip: { trigger: 'axis' },
        legend: { data: ['电影数量', '平均评分'], bottom: 0 },
        xAxis: { type: 'category', data: years, axisLabel: { rotate: 45 } },
        yAxis: [
            { type: 'value', name: '电影数量', position: 'left' },
            { type: 'value', name: '平均评分', position: 'right', min: 5, max: 10 }
        ],
        series: [
            {
                name: '电影数量',
                type: 'bar',
                data: counts,
                itemStyle: { color: CHART_COLORS[0], borderRadius: [4, 4, 0, 0] },
                barWidth: '60%'
            },
            {
                name: '平均评分',
                type: 'line',
                yAxisIndex: 1,
                data: ratings,
                lineStyle: { color: CHART_COLORS[3], width: 2 },
                itemStyle: { color: CHART_COLORS[3] },
                smooth: true
            }
        ]
    };

    chart.setOption(applyChartDefaults(option));
}

/**
 * 初始化地图（国家/地区分布）
 * 国际地图 GeoJSON 依赖外网 CDN，国内环境直接使用条形图展示
 * @param {Array} data - 国家分布数据
 */
function initMapChart(data) {
    if (!data || !data.length) {
        showChartEmpty('map', 'chart-map');
        return;
    }
    const chart = createChart('map', 'chart-map');

    // 转换国家名称并合并同名
    const countryMap = {};
    data.forEach(item => {
        const name = COUNTRY_NAME_MAP[item.name] || item.name;
        countryMap[name] = (countryMap[name] || 0) + item.count;
    });

    const mapData = Object.entries(countryMap)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value);

    // 直接使用条形图展示（世界地图 GeoJSON 需要外网 CDN）
    initMapBarChart(chart, mapData);
}

/**
 * 地图加载失败时的条形图替代方案
 */
function initMapBarChart(chart, data) {
    const top20 = data.slice(0, 20);
    const option = {
        tooltip: { trigger: 'axis' },
        grid: { left: 96, right: 48, top: 24, bottom: 36 },
        xAxis: { type: 'value', name: '电影数量' },
        yAxis: {
            type: 'category',
            data: top20.map(item => item.name).reverse(),
            axisLabel: { width: 86, overflow: 'truncate' }
        },
        series: [{
            type: 'bar',
            data: top20.map(item => item.value).reverse(),
            itemStyle: { color: CHART_COLORS[0], borderRadius: [0, 4, 4, 0] },
            label: { show: true, position: 'right', formatter: '{c}' }
        }]
    };
    chart.setOption(applyChartDefaults(option), true);
}

/**
 * 初始化词云
 * @param {Array} data - 词频数据
 */
function initWordcloudChart(data) {
    if (!data || !data.length) {
        showChartEmpty('wordcloud', 'chart-wordcloud');
        return;
    }
    const chart = createChart('wordcloud', 'chart-wordcloud');

    const option = {
        tooltip: { show: true },
        series: [{
            type: 'wordCloud',
            shape: 'circle',
            left: 'center',
            top: 'center',
            width: '90%',
            height: '90%',
            sizeRange: [13, 44],
            rotationRange: [-25, 25],
            rotationStep: 15,
            gridSize: 8,
            drawOutOfBound: false,
            textStyle: {
                fontFamily: 'sans-serif',
                fontWeight: 'bold',
                color: function (params) {
                    return CHART_COLORS[params.dataIndex % CHART_COLORS.length];
                }
            },
            data: data.map(item => ({ name: item.name, value: item.value }))
        }]
    };

    chart.setOption(applyChartDefaults(option));
}

/**
 * 初始化热力图（年份×类型）
 * @param {Array} data - 热力图数据
 */
function initHeatmapChart(data) {
    if (!data || !data.length) {
        showChartEmpty('heatmap', 'chart-heatmap');
        return;
    }
    const chart = createChart('heatmap', 'chart-heatmap');

    // 提取唯一的年份和类型
    const years = [...new Set(data.map(item => item.year))].sort();
    const genres = [...new Set(data.map(item => item.genre))].sort();

    // 构建热力图数据 [yearIndex, genreIndex, value]
    const heatData = [];
    let maxVal = 0;
    data.forEach(item => {
        const yearIdx = years.indexOf(item.year);
        const genreIdx = genres.indexOf(item.genre);
        if (yearIdx >= 0 && genreIdx >= 0) {
            heatData.push([yearIdx, genreIdx, item.count]);
            if (item.count > maxVal) maxVal = item.count;
        }
    });

    const option = {
        tooltip: {
            formatter: function (params) {
                return years[params.data[0]] + '年 ' + genres[params.data[1]] + ': ' + params.data[2] + ' 部';
            }
        },
        grid: { left: 96, right: 24, top: 20, bottom: 76 },
        xAxis: {
            type: 'category',
            data: years,
            axisLabel: { rotate: 45, fontSize: 10 }
        },
        yAxis: {
            type: 'category',
            data: genres,
            axisLabel: { fontSize: 11 }
        },
        visualMap: {
            min: 0,
            max: maxVal,
            calculable: true,
            orient: 'horizontal',
            left: 'center',
            bottom: 0,
            inRange: { color: ['#fcfbf8', '#f1eadc', '#f3d5a6', '#d9a441', '#0f9f8f', '#3b82f6'] }
        },
        series: [{
            type: 'heatmap',
            data: heatData,
            label: { show: false },
            emphasis: {
                itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' }
            }
        }]
    };

    chart.setOption(applyChartDefaults(option));
}

/**
 * 初始化关系图（导演-演员网络）
 * @param {Array} data - 关系数据
 */
function initGraphChart(data) {
    if (!data || !data.length) {
        showChartEmpty('graph', 'chart-graph');
        return;
    }
    const chart = createChart('graph', 'chart-graph');

    // 构建节点和边
    const nodeSet = new Set();
    const nodes = [];
    let links = [];

    data.forEach(item => {
        if (!nodeSet.has(item.director)) {
            nodeSet.add(item.director);
            nodes.push({
                name: item.director,
                symbolSize: 20,
                category: 0,
                itemStyle: { color: CHART_COLORS[0] }
            });
        }
        if (!nodeSet.has(item.actor)) {
            nodeSet.add(item.actor);
            nodes.push({
                name: item.actor,
                symbolSize: 12,
                category: 1,
                itemStyle: { color: CHART_COLORS[3] }
            });
        }
        links.push({
            source: item.director,
            target: item.actor,
            value: item.count
        });
    });

    // 限制节点数量避免过于拥挤
    if (nodes.length > 80) {
        nodes.length = 80;
        const nodeNames = new Set(nodes.map(n => n.name));
        links = links.filter(l => nodeNames.has(l.source) && nodeNames.has(l.target));
    }

    const option = {
        tooltip: {},
        legend: {
            data: ['导演', '演员'],
            bottom: 0
        },
        series: [{
            type: 'graph',
            layout: 'force',
            data: nodes,
            links: links,
            categories: [
                { name: '导演' },
                { name: '演员' }
            ],
            roam: true,
            label: { show: true, position: 'right', fontSize: 10 },
            force: { repulsion: 140, edgeLength: [55, 180] },
            emphasis: {
                focus: 'adjacency',
                lineStyle: { width: 4 }
            },
            lineStyle: { color: 'source', curveness: 0.1 }
        }]
    };

    chart.setOption(applyChartDefaults(option));
}

/**
 * 初始化散点图（时长 vs 评分）
 * @param {Array} data - 散点数据
 */
function initScatterChart(data) {
    if (!data || !data.length) {
        showChartEmpty('scatter', 'chart-scatter');
        return;
    }
    const chart = createChart('scatter', 'chart-scatter');

    const option = {
        tooltip: {
            formatter: function (params) {
                return '时长: ' + params.data[0] + '分钟<br/>评分: ' + params.data[1];
            }
        },
        xAxis: {
            type: 'value',
            name: '时长（分钟）'
        },
        yAxis: {
            type: 'value',
            name: '评分',
            min: 3,
            max: 10
        },
        series: [{
            type: 'scatter',
            data: data.map(item => [item.duration_minutes, item.rating]),
            symbolSize: 4,
            itemStyle: {
                color: 'rgba(59, 130, 246, 0.46)'
            },
            emphasis: {
                itemStyle: { color: CHART_COLORS[3], shadowBlur: 10 }
            }
        }]
    };

    chart.setOption(applyChartDefaults(option));
}

/**
 * 初始化排行榜（横向柱状图）
 * @param {Array} data - 排行数据
 */
function initRankChart(data) {
    if (!data || !data.length) {
        showChartEmpty('rank', 'chart-rank');
        return;
    }
    const chart = createChart('rank', 'chart-rank');

    // 反转数据（从低到高，顶部显示最高分）
    const reversed = [...data].reverse();

    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            formatter: function (params) {
                const d = params[0];
                const movie = reversed[d.dataIndex];
                return movie.title + '<br/>评分: ' + movie.rating + '<br/>年份: ' + movie.year;
            }
        },
        grid: { left: 170, right: 52, top: 12, bottom: 28 },
        xAxis: {
            type: 'value',
            name: '评分',
            min: 7,
            max: 10
        },
        yAxis: {
            type: 'category',
            data: reversed.map(item => item.title),
            axisLabel: {
                width: 160,
                overflow: 'truncate',
                fontSize: 11
            }
        },
        series: [{
            type: 'bar',
            data: reversed.map(item => item.rating),
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                    { offset: 0, color: CHART_COLORS[0] },
                    { offset: 1, color: CHART_COLORS[1] }
                ]),
                borderRadius: [0, 4, 4, 0]
            },
            label: {
                show: true,
                position: 'right',
                formatter: '{c}',
                fontSize: 11
            },
            barWidth: '60%'
        }]
    };

    chart.setOption(applyChartDefaults(option));
}

/**
 * 加载筛选选项
 */
async function loadFilters() {
    const filters = await fetchFilters();
    if (!filters) return;

    // 填充类型下拉框
    const genreSelect = document.getElementById('filter-genre');
    if (filters.genres) {
        filters.genres.forEach(genre => {
            const opt = document.createElement('option');
            opt.value = genre;
            opt.textContent = genre;
            genreSelect.appendChild(opt);
        });
    }

    // 填充年份下拉框
    const yearSelect = document.getElementById('filter-year');
    if (filters.years) {
        filters.years.forEach(year => {
            const opt = document.createElement('option');
            opt.value = year;
            opt.textContent = year + '年';
            yearSelect.appendChild(opt);
        });
    }

    // 填充国家下拉框
    const countrySelect = document.getElementById('filter-country');
    if (filters.countries) {
        filters.countries.forEach(country => {
            const opt = document.createElement('option');
            opt.value = country;
            opt.textContent = country;
            countrySelect.appendChild(opt);
        });
    }
}

/**
 * 加载所有图表数据
 * @param {Object} filters - 筛选条件
 */
async function loadAllCharts(filters = {}) {
    showAllChartsLoading();
    updateIndicatorCards(null);

    try {
        // 并行加载所有数据
        const [
            stats,
            genreData,
            ratingData,
            yearData,
            countryData,
            topData,
            heatmapData,
            networkData,
            wordcloudData,
            scatterData
        ] = await Promise.all([
            fetchSummaryStats(filters),
            fetchGenreDistribution(filters),
            fetchRatingDistribution(filters),
            fetchYearTrend(filters),
            fetchCountryDistribution(filters),
            fetchTopRated(20, filters),
            fetchGenreYearHeatmap(filters),
            fetchDirectorNetwork(filters),
            fetchWordcloudData(filters),
            fetchDurationRating(filters)
        ]);

        // 更新指标卡
        updateIndicatorCards(stats);

        // 初始化图表
        renderChart('pie', genreData, initPieChart);
        renderChart('bar', ratingData, initBarChart);
        renderChart('line', yearData, initLineChart);
        renderChart('map', countryData, initMapChart);
        renderChart('wordcloud', wordcloudData, initWordcloudChart);
        renderChart('heatmap', heatmapData, initHeatmapChart);
        renderChart('graph', networkData, initGraphChart);
        renderChart('scatter', scatterData, initScatterChart);
        renderChart('rank', topData, initRankChart);
    } catch (error) {
        console.error('图表加载失败:', error);
        updateIndicatorCards(null);
        showAllChartsError();
    }
}

function setFilterButtonsLoading(isLoading) {
    const applyBtn = document.getElementById('filter-apply');
    const resetBtn = document.getElementById('filter-reset');
    if (!applyBtn || !resetBtn) return;
    applyBtn.disabled = isLoading;
    resetBtn.disabled = isLoading;
    applyBtn.classList.toggle('is-loading', isLoading);
    applyBtn.textContent = isLoading ? '加载中...' : '应用筛选';
}

/**
 * 窗口 resize 自适应
 */
function handleResize() {
    Object.values(charts).forEach(chart => {
        if (chart && chart.resize) {
            chart.resize();
        }
    });
}

/**
 * 获取当前筛选条件
 */
function getFilterParams() {
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

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', async function () {
    // 加载筛选选项
    await loadFilters();

    // 加载所有图表
    await loadAllCharts();

    // 评分滑块实时显示
    const ratingSlider = document.getElementById('filter-rating');
    const ratingDisplay = document.getElementById('rating-display');
    ratingSlider.addEventListener('input', function () {
        ratingDisplay.textContent = this.value;
    });

    // 应用筛选按钮（同时刷新图表和电影列表）
    document.getElementById('filter-apply').addEventListener('click', async function () {
        const filters = getFilterParams();
        invalidateCache('browse');
        setFilterButtonsLoading(true);
        try {
            await Promise.all([loadAllCharts(filters), loadMovieList(1)]);
        } finally {
            setFilterButtonsLoading(false);
        }
    });

    // 重置筛选按钮
    document.getElementById('filter-reset').addEventListener('click', async function () {
        document.getElementById('filter-genre').value = '';
        document.getElementById('filter-year').value = '';
        document.getElementById('filter-country').value = '';
        document.getElementById('filter-rating').value = 0;
        document.getElementById('rating-display').textContent = '0';
        invalidateCache('browse');
        setFilterButtonsLoading(true);
        try {
            await Promise.all([loadAllCharts(), loadMovieList(1)]);
        } finally {
            setFilterButtonsLoading(false);
        }
    });

    // 窗口 resize
    window.addEventListener('resize', handleResize);
});
