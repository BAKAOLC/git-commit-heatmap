#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def get_git_commits(repo_path: Path, repo_name: str = None, days: int = None, 
                    since: str = None, until: str = None, author: str = None) -> list[tuple[datetime, int, str]]:
    if repo_name is None:
        repo_name = repo_path.name
    
    try:
        cmd = ["git", "log", "--format=%ai|%an", "--all"]
        
        if since:
            cmd.extend(["--since", since])
        if until:
            cmd.extend(["--until", until])
        if author:
            cmd.extend(["--author", author])
        
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True,
        )
        
        commits = []
        cutoff_date = None
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
        
        if not result.stdout:
            return commits
        
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                parts = line.split("|", 1)
                if len(parts) < 2:
                    continue
                
                dt_str = parts[0]
                author_name = parts[1] if len(parts) > 1 else ""
                
                dt = datetime.strptime(dt_str[:19], "%Y-%m-%d %H:%M:%S")
                
                if cutoff_date and dt < cutoff_date:
                    continue
                
                date_only = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                hour = dt.hour
                commits.append((date_only, hour, repo_name))
            except ValueError:
                continue
        
        return commits
    except subprocess.CalledProcessError as e:
        print(f"警告: 无法获取仓库 {repo_name} 的提交历史: {e}", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("错误: 未找到 git 命令，请确保已安装 Git", file=sys.stderr)
        sys.exit(1)


def generate_heatmap(commits: list[tuple[datetime, int, str]]) -> tuple[dict[tuple[datetime, int], int], dict[tuple[datetime, int], dict[str, int]], dict[str, int]]:
    heatmap = defaultdict(int)
    repo_heatmap = defaultdict(lambda: defaultdict(int))
    repo_stats = defaultdict(int)
    
    for date, hour, repo_name in commits:
        heatmap[(date, hour)] += 1
        repo_heatmap[(date, hour)][repo_name] += 1
        repo_stats[repo_name] += 1
    
    return heatmap, repo_heatmap, repo_stats


def print_heatmap_table(heatmap: dict[tuple[datetime, int], int], repo_stats: dict[str, int] = None):
    if not heatmap:
        print("没有数据可显示")
        return
    
    dates = sorted(set(date for date, _ in heatmap.keys()))
    
    max_count = max(heatmap.values()) if heatmap else 1
    
    def get_color(count: int) -> str:
        if count == 0:
            return "\033[38;5;232m"
        elif count <= max_count * 0.25:
            return "\033[38;5;22m"
        elif count <= max_count * 0.5:
            return "\033[38;5;28m"
        elif count <= max_count * 0.75:
            return "\033[38;5;34m"
        else:
            return "\033[38;5;40m"
    
    reset_color = "\033[0m"
    
    print("\n" + " " * 6, end="")
    for date in dates:
        date_str = date.strftime("%m-%d")
        print(f"{date_str:>6}", end="")
    print()
    
    for hour in range(24):
        print(f"{hour:2} ", end="")
        for date in dates:
            count = heatmap.get((date, hour), 0)
            color = get_color(count)
            if count == 0:
                block = "  "
            elif count < 10:
                block = f"{count:2}"
            else:
                block = "++"
            print(f"{color}{block}{reset_color}", end="  ")
        print()
    
    total_commits = sum(heatmap.values())
    print(f"\n总提交数: {total_commits}")
    
    if repo_stats and len(repo_stats) > 1:
        print("\n各仓库提交统计:")
        for repo_name, count in sorted(repo_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_commits * 100) if total_commits > 0 else 0
            print(f"  {repo_name}: {count} 次 ({percentage:.1f}%)")
    
    print(f"显示日期范围: {dates[0].strftime('%Y-%m-%d')} 至 {dates[-1].strftime('%Y-%m-%d')}")
    print(f"共 {len(dates)} 天有提交记录")
    
    if heatmap:
        max_key = max(heatmap.items(), key=lambda x: x[1])
        date, hour = max_key[0]
        print(f"最活跃时段: {date.strftime('%Y-%m-%d')} {hour}时 ({max_key[1]} 次提交)")


def print_heatmap_table_plain(heatmap: dict[tuple[datetime, int], int], repo_stats: dict[str, int] = None):
    if not heatmap:
        print("没有数据可显示")
        return
    
    dates = sorted(set(date for date, _ in heatmap.keys()))
    
    print("\n" + " " * 6, end="")
    for date in dates:
        date_str = date.strftime("%m-%d")
        print(f"{date_str:>8}", end="")
    print()
    
    for hour in range(24):
        print(f"{hour:2} ", end="")
        for date in dates:
            count = heatmap.get((date, hour), 0)
            print(f"{count:8}", end="")
        print()
    
    total_commits = sum(heatmap.values())
    print(f"\n总提交数: {total_commits}")
    
    if repo_stats and len(repo_stats) > 1:
        print("\n各仓库提交统计:")
        for repo_name, count in sorted(repo_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_commits * 100) if total_commits > 0 else 0
            print(f"  {repo_name}: {count} 次 ({percentage:.1f}%)")
    
    print(f"显示日期范围: {dates[0].strftime('%Y-%m-%d')} 至 {dates[-1].strftime('%Y-%m-%d')}")
    print(f"共 {len(dates)} 天有提交记录")
    
    if heatmap:
        max_key = max(heatmap.items(), key=lambda x: x[1])
        date, hour = max_key[0]
        print(f"最活跃时段: {date.strftime('%Y-%m-%d')} {hour}时 ({max_key[1]} 次提交)")


def generate_html_heatmap(heatmap: dict[tuple[datetime, int], int], output_path: Path, repo_stats: dict[str, int] = None, repo_heatmap: dict[tuple[datetime, int], dict[str, int]] = None):
    if not heatmap:
        print("没有数据可显示")
        return
    
    dates = sorted(set(date for date, _ in heatmap.keys()))
    max_count = max(heatmap.values()) if heatmap else 1
    
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Git 提交时间网格表</title>
    <style>
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', 'Consolas', 'Monaco', monospace;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            color: #c9d1d9;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            color: #58a6ff;
            margin: 0 0 20px 0;
            font-size: clamp(24px, 4vw, 32px);
            font-weight: 600;
        }
        
        .heatmap-wrapper {
            background-color: #161b22;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        .heatmap {
            overflow-x: auto;
            overflow-y: visible;
            -webkit-overflow-scrolling: touch;
        }
        
        .heatmap::-webkit-scrollbar {
            height: 8px;
        }
        
        .heatmap::-webkit-scrollbar-track {
            background: #0d1117;
            border-radius: 4px;
        }
        
        .heatmap::-webkit-scrollbar-thumb {
            background: #30363d;
            border-radius: 4px;
        }
        
        .heatmap::-webkit-scrollbar-thumb:hover {
            background: #484f58;
        }
        
        table {
            border-collapse: collapse;
            background-color: transparent;
            width: 100%;
            min-width: 600px;
        }
        
        thead {
            position: sticky;
            top: 0;
            z-index: 10;
            background-color: #161b22;
        }
        
        thead tr:first-child {
            position: sticky;
            top: 0;
            z-index: 11;
        }
        
        th {
            padding: 8px 4px;
            text-align: center;
            color: #8b949e;
            font-weight: 500;
            font-size: clamp(10px, 1.2vw, 12px);
            white-space: nowrap;
            border-bottom: 2px solid #30363d;
            border-right: 1px solid #21262d;
        }
        
        th.date-header {
            border-right: 1px solid #30363d;
        }
        
        th:last-child {
            border-right: none;
        }
        
        th:first-child {
            text-align: left;
            padding-left: 0;
            min-width: 35px;
        }
        
        th.year-header {
            background-color: #0d1117;
            border-bottom: 1px solid #30363d;
            border-right: 1px solid #30363d;
            padding: 10px 0;
            position: relative;
            overflow: visible;
        }
        
        th.year-header:last-child {
            border-right: none;
        }
        
        th.year-header .year-text {
            font-weight: 600;
            font-size: clamp(11px, 1.4vw, 14px);
            color: #58a6ff;
            white-space: nowrap;
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
        }
        
        th.year-header .year-text.visible {
            opacity: 1;
        }
        
        tbody tr:first-child td {
            padding-top: 8px;
        }
        
        td {
            padding: 3px 2px 3px 2px;
            text-align: center;
            vertical-align: middle;
            border-right: 1px solid #21262d;
            height: auto;
            line-height: 1;
        }
        
        td:last-child {
            border-right: none;
        }
        
        tbody tr:nth-child(even) {
            background-color: #0d1117;
        }
        
        td:first-child {
            color: #8b949e;
            font-weight: 500;
            padding: 3px 6px 3px 0;
            font-size: clamp(11px, 1.3vw, 13px);
            position: sticky;
            left: 0;
            background-color: #161b22;
            z-index: 5;
            text-align: right;
            vertical-align: middle;
            line-height: 1.2;
            width: 30px;
            max-width: 30px;
        }
        
        td:first-child::after {
            content: '';
            position: absolute;
            right: -1px;
            top: 0;
            bottom: 0;
            width: 1px;
            background-color: #30363d;
            z-index: 6;
            pointer-events: none;
        }
        
        tbody tr:nth-child(even) td:first-child {
            background-color: #0d1117;
        }
        
        tbody tr:nth-child(even) td:first-child::after {
            background-color: #30363d;
        }
        
        .cell {
            width: clamp(14px, 1.8vw, 20px);
            height: clamp(14px, 1.8vw, 20px);
            display: inline-block;
            vertical-align: middle;
            border-radius: 2px;
            margin: 0 1px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            cursor: pointer;
            position: relative;
        }
        
        .cell:hover {
            transform: scale(1.1);
            z-index: 10;
        }
        
        .tooltip {
            position: absolute;
            background-color: #161b22;
            color: #c9d1d9;
            padding: 10px 12px;
            border-radius: 6px;
            font-size: 13px;
            line-height: 1.5;
            white-space: normal;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
            border: 1px solid #30363d;
            z-index: 1000;
            pointer-events: none;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.2s ease, visibility 0.2s ease;
            max-width: 320px;
            min-width: 180px;
            bottom: calc(100% + 8px);
            left: 50%;
            transform: translateX(-50%);
        }
        
        .tooltip-header {
            font-weight: 600;
            color: #58a6ff;
            margin-bottom: 6px;
            font-size: 14px;
        }
        
        .tooltip-total {
            color: #8b949e;
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 1px solid #21262d;
            font-size: 12px;
        }
        
        .tooltip-repos {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        
        .tooltip-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
        }
        
        .tooltip-repo {
            color: #c9d1d9;
            text-align: left;
            flex: 1;
            font-size: 13px;
        }
        
        .tooltip-count {
            color: #58a6ff;
            text-align: right;
            font-weight: 500;
            font-size: 13px;
            white-space: nowrap;
        }
        
        .tooltip::before {
            content: '';
            position: absolute;
            width: 0;
            height: 0;
            border: 6px solid transparent;
            border-top-color: #161b22;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
        }
        
        .cell:hover .tooltip,
        .cell.active .tooltip {
            opacity: 1;
            visibility: visible;
        }
        
        @media (max-width: 768px) {
            .tooltip {
                font-size: 12px;
                padding: 8px 10px;
                max-width: 280px;
                min-width: 160px;
            }
            
            .tooltip-header {
                font-size: 13px;
            }
            
            .tooltip-repo,
            .tooltip-count {
                font-size: 12px;
            }
        }
        
        .level-0 { background-color: #161b22; border: 1px solid #21262d; }
        .level-1 { background-color: #0e4429; }
        .level-2 { background-color: #006d32; }
        .level-3 { background-color: #26a641; }
        .level-4 { background-color: #39d353; }
        
        .stats {
            background-color: #161b22;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        .stats p {
            margin: 12px 0;
            font-size: clamp(14px, 1.5vw, 16px);
            line-height: 1.6;
        }
        
        .stats strong {
            color: #58a6ff;
            font-weight: 600;
        }
        
        .stats ul {
            margin: 12px 0;
            padding-left: 24px;
        }
        
        .stats li {
            margin: 8px 0;
            font-size: clamp(14px, 1.5vw, 16px);
        }
        
        .legend {
            background-color: #161b22;
            border-radius: 8px;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        .legend > span {
            font-weight: 600;
            color: #c9d1d9;
            font-size: clamp(14px, 1.5vw, 16px);
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: clamp(12px, 1.3vw, 14px);
            color: #8b949e;
        }
        
        @media (max-width: 768px) {
            body {
                padding: 12px;
            }
            
            .heatmap-wrapper {
                padding: 12px;
            }
            
            .stats {
                padding: 16px;
            }
            
            .legend {
                padding: 16px;
                gap: 12px;
            }
            
            th {
                padding: 6px 3px;
            }
            
            td {
                padding: 2px 2px 4px 2px;
                text-align: center;
                vertical-align: middle;
                border-right: 1px solid #21262d;
                height: auto;
                line-height: 1;
            }
            
            td:first-child {
                padding: 2px 4px 4px 0;
                width: 25px;
                max-width: 25px;
                vertical-align: middle;
                line-height: 1.2;
            }
            
            .cell {
                vertical-align: middle;
                margin-top: -1px;
            }
            
            th:first-child {
                min-width: 25px;
            }
        }
        
        @media (max-width: 480px) {
            h1 {
                font-size: 20px;
            }
            
            th {
                font-size: 9px;
                padding: 4px 2px;
            }
            
            td {
                padding: 2px 2px 4px 2px;
                text-align: center;
                vertical-align: middle;
                border-right: 1px solid #21262d;
                height: auto;
                line-height: 1;
            }
            
            td:first-child {
                font-size: 10px;
                padding: 2px 4px 4px 0;
                width: 22px;
                max-width: 22px;
                vertical-align: middle;
                line-height: 1.2;
            }
            
            .cell {
                vertical-align: middle;
                margin-top: -1px;
            }
            
            th:first-child {
                min-width: 22px;
            }
        }
        
        @media (min-width: 1920px) {
            .container {
                max-width: 1600px;
            }
            
            .cell {
                width: 22px;
                height: 22px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Git 提交时间网格表</h1>
        
        <div class="heatmap-wrapper">
            <div class="heatmap">
                <table>
                    <thead>
                        <tr>
                            <th class="year-header"></th>
"""
    
    from collections import defaultdict
    year_counts = defaultdict(int)
    for date in dates:
        year = date.year
        year_counts[year] += 1
    
    current_year = None
    year_start_idx = 0
    year_colspans = []
    for i, date in enumerate(dates):
        year = date.year
        if year != current_year:
            if current_year is not None:
                colspan = i - year_start_idx
                year_colspans.append((current_year, colspan))
            current_year = year
            year_start_idx = i
    
    if current_year is not None:
        colspan = len(dates) - year_start_idx
        year_colspans.append((current_year, colspan))
    
    for year, colspan in year_colspans:
        html += f'                            <th class="year-header" colspan="{colspan}"><span class="year-text">{year}</span></th>\n'
    
    html += """                        </tr>
                        <tr>
                            <th></th>
"""
    
    prev_year = None
    for i, date in enumerate(dates):
        date_str = date.strftime("%m-%d")
        current_year = date.year
        is_year_boundary = prev_year is not None and current_year != prev_year
        class_attr = ' class="date-header"' if is_year_boundary else ''
        html += f'                            <th{class_attr}>{date_str}</th>\n'
        prev_year = current_year
    
    html += """                        </tr>
                    </thead>
                    <tbody>
"""
    
    for hour in range(24):
        html += f'                        <tr><td>{hour:2}</td>\n'
        for date in dates:
            count = heatmap.get((date, hour), 0)
            if count == 0:
                level = 0
            elif count <= max_count * 0.25:
                level = 1
            elif count <= max_count * 0.5:
                level = 2
            elif count <= max_count * 0.75:
                level = 3
            else:
                level = 4
            
            date_str = date.strftime("%Y-%m-%d")
            
            if repo_heatmap and (date, hour) in repo_heatmap:
                repo_details = repo_heatmap[(date, hour)]
                repo_items = []
                for repo_name, repo_count in sorted(repo_details.items()):
                    repo_items.append(f'<div class="tooltip-row"><span class="tooltip-repo">{repo_name}</span><span class="tooltip-count">{repo_count} 次</span></div>')
                tooltip_text = f'<div class="tooltip-header">{date_str} {hour}时</div><div class="tooltip-total">总计: {count} 次提交</div><div class="tooltip-repos">' + ''.join(repo_items) + '</div>'
            else:
                tooltip_text = f'<div class="tooltip-header">{date_str} {hour}时</div><div class="tooltip-total">总计: {count} 次提交</div>'
            
            html += f'                            <td><div class="cell level-{level}"><div class="tooltip">{tooltip_text}</div></div></td>\n'
        html += '                        </tr>\n'
    
    html += """                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="stats">
"""
    
    total_commits = sum(heatmap.values())
    html += f'            <p>总提交数: <strong>{total_commits}</strong></p>\n'
    
    if repo_stats and len(repo_stats) > 1:
        html += '            <p>各仓库提交统计:</p><ul>\n'
        for repo_name, count in sorted(repo_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_commits * 100) if total_commits > 0 else 0
            html += f'                <li><strong>{repo_name}</strong>: {count} 次 ({percentage:.1f}%)</li>\n'
        html += '            </ul>\n'
    
    html += f'            <p>显示日期范围: <strong>{dates[0].strftime("%Y-%m-%d")}</strong> 至 <strong>{dates[-1].strftime("%Y-%m-%d")}</strong></p>\n'
    html += f'            <p>共 <strong>{len(dates)}</strong> 天有提交记录</p>\n'
    
    if heatmap:
        max_key = max(heatmap.items(), key=lambda x: x[1])
        date, hour = max_key[0]
        html += f'            <p>最活跃时段: <strong>{date.strftime("%Y-%m-%d")} {hour}时</strong> ({max_key[1]} 次提交)</p>\n'
    
    html += """        </div>
        
        <div class="legend">
            <span>图例:</span>
            <div class="legend-item"><div class="cell level-0"></div><span>0 次</span></div>
            <div class="legend-item"><div class="cell level-1"></div><span>少</span></div>
            <div class="legend-item"><div class="cell level-2"></div><span>中</span></div>
            <div class="legend-item"><div class="cell level-3"></div><span>多</span></div>
            <div class="legend-item"><div class="cell level-4"></div><span>很多</span></div>
        </div>
    </div>
    <script>
        let rafId = null;
        
        function updateYearPositions() {
            if (rafId) {
                cancelAnimationFrame(rafId);
            }
            
            rafId = requestAnimationFrame(() => {
                const yearHeaders = document.querySelectorAll('th.year-header');
                const heatmap = document.querySelector('.heatmap');
                if (!heatmap) return;
                
                const heatmapRect = heatmap.getBoundingClientRect();
                const viewportWidth = heatmapRect.width;
                const viewportLeft = heatmapRect.left;
                
                yearHeaders.forEach(header => {
                    const text = header.querySelector('.year-text');
                    if (!text) return;
                    
                    const headerRect = header.getBoundingClientRect();
                    const headerLeft = headerRect.left - viewportLeft;
                    const headerRight = headerLeft + headerRect.width;
                    const headerWidth = headerRect.width;
                    const textWidth = text.scrollWidth;
                    
                    if (headerLeft < 0 && headerRight < 0) {
                        text.classList.remove('visible');
                        return;
                    }
                    
                    if (headerLeft > viewportWidth) {
                        text.classList.remove('visible');
                        return;
                    }
                    
                    if (textWidth > headerWidth) {
                        text.classList.remove('visible');
                        return;
                    }
                    
                    const visibleLeft = Math.max(0, headerLeft);
                    const visibleRight = Math.min(viewportWidth, headerRight);
                    const visibleWidth = visibleRight - visibleLeft;
                    
                    if (visibleWidth < textWidth) {
                        text.classList.remove('visible');
                        return;
                    }
                    
                    const centerX = visibleLeft + visibleWidth / 2;
                    const headerCenterX = headerLeft + headerWidth / 2;
                    const offsetX = centerX - headerCenterX;
                    
                    text.style.left = '50%';
                    text.style.transform = `translate(calc(-50% + ${offsetX}px), -50%)`;
                    text.classList.add('visible');
                });
                
                rafId = null;
            });
        }
        
        const heatmap = document.querySelector('.heatmap');
        if (heatmap) {
            let ticking = false;
            const throttledUpdate = () => {
                if (!ticking) {
                    ticking = true;
                    updateYearPositions();
                    requestAnimationFrame(() => {
                        ticking = false;
                    });
                }
            };
            
            heatmap.addEventListener('scroll', throttledUpdate, { passive: true });
            window.addEventListener('resize', throttledUpdate);
            updateYearPositions();
        }
        
        // Tooltip 处理
        (function() {
            const cells = document.querySelectorAll('.cell');
            let activeCell = null;
            
            function hideTooltip() {
                if (activeCell) {
                    activeCell.classList.remove('active');
                    activeCell = null;
                }
            }
            
            cells.forEach(cell => {
                // 桌面端：鼠标悬停
                cell.addEventListener('mouseenter', function() {
                    hideTooltip();
                    this.classList.add('active');
                    activeCell = this;
                });
                
                cell.addEventListener('mouseleave', function() {
                    this.classList.remove('active');
                    if (activeCell === this) {
                        activeCell = null;
                    }
                });
                
                // 移动端：点击切换
                cell.addEventListener('click', function(e) {
                    e.stopPropagation();
                    if (activeCell === this) {
                        hideTooltip();
                    } else {
                        hideTooltip();
                        this.classList.add('active');
                        activeCell = this;
                    }
                });
            });
            
            // 点击其他地方关闭 tooltip
            document.addEventListener('click', function(e) {
                if (!e.target.closest('.cell')) {
                    hideTooltip();
                }
            });
        })();
    </script>
</body>
</html>"""
    
    output_path.write_text(html, encoding='utf-8')
    print(f"\nHTML 文件已生成: {output_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='生成 Git 提交时间网格表（以日期为横坐标，小时为纵坐标）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 统计当前仓库
  %(prog)s
  
  # 统计多个仓库
  %(prog)s --repo ../repo1 --repo ../repo2 --repo ../repo3
  
  # 只显示最近90天的提交
  %(prog)s --days 90
  
  # 指定时间范围
  %(prog)s --since "2024-01-01" --until "2024-12-31"
  
  # 过滤指定作者
  %(prog)s --author "John Doe"
  
  # 组合使用
  %(prog)s --repo ../repo1 --repo ../repo2 --author "John" --since "2024-01-01" --html output.html
        """
    )
    parser.add_argument('--html', type=str, metavar='FILE', help='生成 HTML 文件（指定输出路径）')
    parser.add_argument('--repo', type=str, action='append', metavar='PATH', dest='repos',
                       help='指定要统计的仓库路径（可多次使用以指定多个仓库）')
    parser.add_argument('--days', type=int, metavar='N', help='只显示最近 N 天的提交')
    parser.add_argument('--since', type=str, metavar='DATE', help='只显示指定日期之后的提交（格式：YYYY-MM-DD 或相对时间如 "2 weeks ago"）')
    parser.add_argument('--until', type=str, metavar='DATE', help='只显示指定日期之前的提交（格式：YYYY-MM-DD 或相对时间如 "1 week ago"）')
    parser.add_argument('--author', type=str, metavar='PATTERN', help='只显示指定作者的提交（支持正则表达式）')
    args = parser.parse_args()
    
    repo_paths = []
    if args.repos:
        for repo_str in args.repos:
            repo_path = Path(repo_str).resolve()
            if not repo_path.exists():
                print(f"警告: 仓库路径不存在: {repo_path}", file=sys.stderr)
                continue
            if not (repo_path / ".git").exists():
                print(f"警告: 不是有效的 Git 仓库: {repo_path}", file=sys.stderr)
                continue
            repo_paths.append(repo_path)
    else:
        repo_path = Path.cwd()
        if (repo_path / ".git").exists():
            repo_paths.append(repo_path)
        else:
            print("错误: 当前目录不是 Git 仓库，请使用 --repo 参数指定仓库路径", file=sys.stderr)
            sys.exit(1)
    
    if not repo_paths:
        print("错误: 没有有效的仓库路径", file=sys.stderr)
        sys.exit(1)
    
    all_commits = []
    for repo_path in repo_paths:
        repo_name = repo_path.name
        print(f"正在分析仓库: {repo_path} ({repo_name})")
        commits = get_git_commits(repo_path, repo_name=repo_name, days=args.days, 
                                 since=args.since, until=args.until, author=args.author)
        all_commits.extend(commits)
        print(f"  找到 {len(commits)} 个提交")
    
    if not all_commits:
        print("未找到任何提交记录")
        return
    
    print(f"\n总共找到 {len(all_commits)} 个提交")
    
    heatmap, repo_heatmap, repo_stats = generate_heatmap(all_commits)
    
    if args.html:
        output_path = Path(args.html)
        generate_html_heatmap(heatmap, output_path, repo_stats, repo_heatmap)
    else:
        if sys.stdout.isatty():
            print_heatmap_table(heatmap, repo_stats)
        else:
            print_heatmap_table_plain(heatmap, repo_stats)


if __name__ == "__main__":
    main()
