# 豆瓣电影数据分析系统

(大学作业)基于豆瓣电影数据的可视化分析系统，后端使用 Flask + MySQL，前端使用 ECharts 展示统计分析结果，并配套提供爬虫、数据补充和论文辅助脚本。

当前仓库仅托管项目实现代码，不包含本机配置、虚拟环境、论文终稿和图片素材。

## 项目特性

- Flask RESTful API
- MySQL 参数化 SQL 数据访问
- 豆瓣电影数据爬取与详情补充
- ECharts 多图表联动可视化
- 用户登录、收藏、评分功能
- 论文配套辅助脚本与设计说明

## 目录结构

```text
douban_analysis/
├── app.py
├── health_check.py
├── config.example.py
├── config.py              # 本地创建，不提交仓库
├── requirements.txt
├── api/
├── analysis/
├── db/
├── docs/
├── scripts/
├── spider/
├── static/
└── templates/
```

## 快速运行

### 1. 安装依赖

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
mysql -u root -p
```

```sql
CREATE DATABASE douban_movies CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```bash
mysql -u root -p douban_movies < db/schema.sql
```

如需执行增量脚本：

```bash
mysql -u root -p douban_movies < db/migrations/001_add_user_ratings_updated_at.sql
```

### 3. 配置本机环境

```bash
copy config.example.py config.py
```

然后在 `config.py` 中填写本机 MySQL 密码。

### 4. 运行体检与启动服务

```bash
python health_check.py
python app.py
```

浏览器访问 [http://localhost:5000](http://localhost:5000)。

## 常用脚本

以下脚本在当前项目根目录执行：

- `python scripts/add_genres.py`：补充类型数据
- `python scripts/enrich_details.py`：补充电影详情数据
- `python scripts/download_posters.py`：下载海报到本地
- `python scripts/generate_report.py`：生成论文/报告草稿

## 仓库说明

- 设计说明保存在 `docs/DESIGN.md`
- 本仓库不包含 `config.py`，请从 `config.example.py` 复制生成
- 本仓库不包含 `venv/`、本地海报资源、论文文档和图片素材

## 当前状态

- 功能开发完成
- 图表展示完成
- 用户登录、收藏、评分完成
- 代码仓库已整理完成
