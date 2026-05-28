# 辅助脚本说明

本目录存放一次性或低频使用的辅助脚本，运行时请先切到 `douban_analysis/` 项目根目录。

- `python scripts/add_genres.py`：为已入库电影补充类型数据。
- `python scripts/enrich_details.py`：通过豆瓣移动端接口补充演员、国家、语言、时长、简介等详情。
- `python scripts/download_posters.py`：批量下载海报到本地 `static/posters/`。
- `python scripts/generate_report.py`：生成论文/报告草稿文档。
