# src/web_generator.py
import json
import os
import logging
from datetime import datetime
from typing import Any
from pathlib import Path
from config import GITHUB_PAGES_URL, HTML_OUTPUT_FILES, DOCS_DIR

logger = logging.getLogger(__name__)

def generate_dashboard_html(job_list: list[dict[str, Any]], output_files: list[Path] | None = None) -> str:
    """
    수집된 전체 유효 공고 목록을 모바일 및 데스크톱에 최적화된 반응형 웹 대시보드 HTML로 빌드합니다.
    """
    if output_files is None:
        output_files = HTML_OUTPUT_FILES

    # 디렉토리 생성
    if DOCS_DIR:
        DOCS_DIR.mkdir(parents=True, exist_ok=True)

    now_str = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    total_count = len(job_list)
    highlight_count = sum(1 for j in job_list if j.get("is_highlighted"))
    wanted_count = sum(1 for j in job_list if j.get("platform") == "원티드")
    jobkorea_count = sum(1 for j in job_list if j.get("platform") == "잡코리아")
    jasoseol_count = sum(1 for j in job_list if j.get("platform") == "자소설닷컴")

    # JSON 직렬화하여 클라이언트 자바스크립트에 임베드
    jobs_json = json.dumps(job_list, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>임베디드 & 시스템 SW 채용 대시보드 | Embedded Job Radar</title>
    <meta name="description" content="원티드, 잡코리아, 자소설닷컴에서 엄선한 임베디드, 펌웨어, 시스템 소프트웨어 채용 공고를 실시간으로 확인하세요.">
    <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />
    <style>
        :root {{
            --bg-primary: #f8fafc;
            --bg-surface: #ffffff;
            --bg-subtle: #f1f5f9;
            --border-color: #e2e8f0;
            --border-hover: #cbd5e1;
            
            --text-main: #0f172a;
            --text-muted: #475569;
            --text-subtle: #64748b;
            
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --primary-light: #eff6ff;
            
            --amber: #d97706;
            --amber-light: #fef3c7;
            --emerald: #059669;
            --emerald-light: #ecfdf5;
            --rose: #e11d48;
            --rose-light: #ffe4e6;
            
            --wanted-color: #3b82f6;
            --jobkorea-color: #f97316;
            --jasoseol-color: #8b5cf6;
            
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 14px;
            --radius-full: 9999px;
            
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04);
            
            --font-family: "Pretendard", -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: var(--font-family);
            -webkit-tap-highlight-color: transparent;
        }}

        body {{
            background-color: var(--bg-primary);
            color: var(--text-main);
            line-height: 1.5;
            padding-bottom: 80px;
        }}

        /* Header */
        header {{
            background-color: #0f172a;
            color: #ffffff;
            padding: 28px 20px 24px;
            border-bottom: 1px solid #1e293b;
        }}

        .header-container {{
            max-width: 1080px;
            margin: 0 auto;
        }}

        .header-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(255, 255, 255, 0.12);
            color: #94a3b8;
            font-size: 12px;
            font-weight: 500;
            padding: 4px 10px;
            border-radius: var(--radius-full);
            margin-bottom: 12px;
        }}

        .header-badge .dot {{
            width: 8px;
            height: 8px;
            background-color: #10b981;
            border-radius: 50%;
            display: inline-block;
        }}

        .header-title {{
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .header-desc {{
            font-size: 14px;
            color: #94a3b8;
            margin-bottom: 20px;
        }}

        /* Stat Grid */
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 12px;
        }}

        .stat-card {{
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: var(--radius-md);
            padding: 12px 14px;
            backdrop-filter: blur(8px);
        }}

        .stat-card .label {{
            font-size: 12px;
            color: #94a3b8;
            margin-bottom: 4px;
        }}

        .stat-card .value {{
            font-size: 20px;
            font-weight: 700;
            color: #ffffff;
        }}

        .stat-card.highlight .value {{
            color: #fbbf24;
        }}

        /* Main Container */
        main {{
            max-width: 1080px;
            margin: -12px auto 0;
            padding: 0 16px;
        }}

        /* Filter Panel */
        .filter-panel {{
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 18px 20px;
            box-shadow: var(--shadow-md);
            margin-bottom: 20px;
        }}

        .search-box {{
            position: relative;
            margin-bottom: 16px;
        }}

        .search-box input {{
            width: 100%;
            padding: 12px 16px 12px 42px;
            font-size: 15px;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            background-color: var(--bg-subtle);
            color: var(--text-main);
            outline: none;
            transition: all 0.2s ease;
        }}

        .search-box input:focus {{
            border-color: var(--primary);
            background-color: var(--bg-surface);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
        }}

        .search-icon {{
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-subtle);
            pointer-events: none;
        }}

        .filter-row {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--border-color);
        }}

        .tabs-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}

        .tab-btn {{
            background: var(--bg-subtle);
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            font-size: 13px;
            font-weight: 500;
            padding: 6px 12px;
            border-radius: var(--radius-full);
            cursor: pointer;
            transition: all 0.15s ease;
        }}

        .tab-btn:hover {{
            border-color: var(--border-hover);
            color: var(--text-main);
        }}

        .tab-btn.active {{
            background: #0f172a;
            border-color: #0f172a;
            color: #ffffff;
            font-weight: 600;
        }}

        .select-sort {{
            padding: 6px 12px;
            font-size: 13px;
            font-weight: 500;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            background-color: var(--bg-surface);
            color: var(--text-main);
            outline: none;
            cursor: pointer;
        }}

        /* Quick keyword tag chips */
        .quick-keywords {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 6px;
            margin-top: 12px;
        }}

        .quick-label {{
            font-size: 12px;
            font-weight: 600;
            color: var(--text-subtle);
            margin-right: 4px;
        }}

        .keyword-chip {{
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            font-size: 12px;
            padding: 3px 8px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.15s ease;
        }}

        .keyword-chip:hover, .keyword-chip.active {{
            background: var(--primary-light);
            border-color: var(--primary);
            color: var(--primary);
            font-weight: 600;
        }}

        /* Job Count & Status */
        .list-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
            padding: 0 4px;
        }}

        .list-count {{
            font-size: 14px;
            font-weight: 600;
            color: var(--text-muted);
        }}

        .list-count span {{
            color: var(--primary);
        }}

        /* Job Cards Grid */
        .job-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 16px;
        }}

        .job-card {{
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 20px;
            box-shadow: var(--shadow-sm);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
            position: relative;
        }}

        .job-card:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
            border-color: var(--border-hover);
        }}

        .job-card.is-highlight {{
            border-color: #fde68a;
            background: linear-gradient(180deg, #fffdfa 0%, #ffffff 100%);
        }}

        .job-card-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
            gap: 8px;
        }}

        .company-info {{
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: wrap;
        }}

        .company-name {{
            font-size: 15px;
            font-weight: 700;
            color: var(--text-main);
            letter-spacing: -0.01em;
        }}

        .badge {{
            font-size: 11px;
            font-weight: 600;
            padding: 2px 7px;
            border-radius: var(--radius-sm);
            display: inline-flex;
            align-items: center;
            line-height: 1.3;
        }}

        .badge-highlight {{
            background-color: var(--amber-light);
            color: var(--amber);
            border: 1px solid #fcd34d;
        }}

        .badge-type-1 {{
            background-color: #fee2e2;
            color: #b91c1c;
        }}

        .badge-type-2 {{
            background-color: #e0f2fe;
            color: #0369a1;
        }}

        .badge-platform {{
            font-size: 10px;
            padding: 2px 6px;
            border-radius: var(--radius-sm);
            font-weight: 700;
        }}

        .platform-wanted {{
            background: #eff6ff;
            color: var(--wanted-color);
            border: 1px solid #bfdbfe;
        }}

        .platform-jobkorea {{
            background: #fff7ed;
            color: var(--jobkorea-color);
            border: 1px solid #fed7aa;
        }}

        .platform-jasoseol {{
            background: #f5f3ff;
            color: var(--jasoseol-color);
            border: 1px solid #ddd6fe;
        }}

        .job-title {{
            font-size: 16px;
            font-weight: 600;
            color: var(--text-main);
            margin-bottom: 12px;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            word-break: break-word;
        }}

        .job-details {{
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-bottom: 16px;
            font-size: 13px;
            color: var(--text-muted);
        }}

        .detail-row {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .detail-icon {{
            font-size: 13px;
            width: 16px;
            text-align: center;
            color: var(--text-subtle);
        }}

        .deadline-badge {{
            font-size: 11px;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: var(--radius-sm);
        }}

        .deadline-urgent {{
            background-color: var(--rose-light);
            color: var(--rose);
        }}

        .deadline-warning {{
            background-color: var(--amber-light);
            color: var(--amber);
        }}

        .deadline-normal {{
            background-color: var(--bg-subtle);
            color: var(--text-muted);
        }}

        .fit-pill {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 7px;
            border-radius: var(--radius-full);
        }}

        .fit-high {{
            background-color: var(--emerald-light);
            color: var(--emerald);
        }}

        .fit-med {{
            background-color: var(--primary-light);
            color: var(--primary);
        }}

        .fit-low {{
            background-color: var(--bg-subtle);
            color: var(--text-subtle);
        }}

        /* Duty tags */
        .duty-chips {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            margin-bottom: 16px;
        }}

        .duty-chip {{
            font-size: 11px;
            background: var(--bg-subtle);
            color: var(--text-muted);
            padding: 2px 6px;
            border-radius: var(--radius-sm);
        }}

        /* Card Bottom */
        .card-actions {{
            display: flex;
            gap: 8px;
            align-items: center;
            padding-top: 12px;
            border-top: 1px solid var(--border-color);
        }}

        .btn-link {{
            flex: 1;
            text-align: center;
            background: #0f172a;
            color: #ffffff;
            text-decoration: none;
            padding: 9px 14px;
            font-size: 13px;
            font-weight: 600;
            border-radius: var(--radius-md);
            transition: background 0.15s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
        }}

        .btn-link:hover {{
            background: #1e293b;
        }}

        .btn-bookmark {{
            background: var(--bg-subtle);
            border: 1px solid var(--border-color);
            color: var(--text-subtle);
            padding: 9px 12px;
            font-size: 14px;
            border-radius: var(--radius-md);
            cursor: pointer;
            transition: all 0.15s ease;
        }}

        .btn-bookmark:hover {{
            background: var(--bg-primary);
            color: var(--amber);
        }}

        .btn-bookmark.bookmarked {{
            background: var(--amber-light);
            border-color: #fcd34d;
            color: var(--amber);
        }}

        /* Empty State */
        .empty-state {{
            grid-column: 1 / -1;
            text-align: center;
            padding: 60px 20px;
            background: var(--bg-surface);
            border: 1px dashed var(--border-color);
            border-radius: var(--radius-lg);
            color: var(--text-subtle);
        }}

        .empty-state .icon {{
            font-size: 40px;
            margin-bottom: 12px;
        }}

        .empty-state h3 {{
            font-size: 16px;
            color: var(--text-main);
            margin-bottom: 6px;
        }}

        /* Floating Top Button */
        .btn-top {{
            position: fixed;
            bottom: 24px;
            right: 20px;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: #0f172a;
            color: #ffffff;
            border: none;
            box-shadow: var(--shadow-lg);
            display: none;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 100;
            transition: opacity 0.2s ease;
        }}

        .btn-top.visible {{
            display: flex;
        }}

        /* Responsive */
        @media (max-width: 640px) {{
            header {{
                padding: 20px 16px 20px;
            }}
            .header-title {{
                font-size: 20px;
            }}
            .stat-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            .job-grid {{
                grid-template-columns: 1fr;
            }}
            .filter-row {{
                flex-direction: column;
                align-items: stretch;
            }}
            .tabs-group {{
                overflow-x: auto;
                padding-bottom: 4px;
                flex-wrap: nowrap;
            }}
            .select-sort {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>

    <!-- Header -->
    <header>
        <div class="header-container">
            <div class="header-badge">
                <span class="dot"></span>
                <span>{now_str} 실시간 동기화</span>
            </div>
            <h1 class="header-title">
                <span>🛰️</span> 임베디드 & 시스템 SW 채용 레이더
            </h1>
            <p class="header-desc">
                원티드 · 잡코리아 · 자소설닷컴의 임베디드, 펌웨어, 시스템 엔지니어 공고 통합 수집 대시보드
            </p>

            <div class="stat-grid">
                <div class="stat-card">
                    <div class="label">총 추천 공고</div>
                    <div class="value" id="stat-total">{total_count}건</div>
                </div>
                <div class="stat-card highlight">
                    <div class="label">⭐ 주요/대기업</div>
                    <div class="value" id="stat-highlight">{highlight_count}건</div>
                </div>
                <div class="stat-card">
                    <div class="label">원티드</div>
                    <div class="value">{wanted_count}건</div>
                </div>
                <div class="stat-card">
                    <div class="label">잡코리아</div>
                    <div class="value">{jobkorea_count}건</div>
                </div>
                <div class="stat-card">
                    <div class="label">자소설닷컴</div>
                    <div class="value">{jasoseol_count}건</div>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main>
        <!-- Filter Panel -->
        <section class="filter-panel" aria-label="채용 공고 검색 및 필터">
            <div class="search-box">
                <span class="search-icon">🔍</span>
                <input type="text" id="searchInput" placeholder="기업명, 직무명, 기술 키워드 검색 (예: 현대, RTOS, BSP, STM32)" autocomplete="off">
            </div>

            <div class="filter-row">
                <div class="tabs-group" id="platformTabs" role="tablist">
                    <button class="tab-btn active" data-platform="all">전체 ({total_count})</button>
                    <button class="tab-btn" data-platform="highlight">⭐ 대기업/주요 ({highlight_count})</button>
                    <button class="tab-btn" data-platform="원티드">원티드 ({wanted_count})</button>
                    <button class="tab-btn" data-platform="잡코리아">잡코리아 ({jobkorea_count})</button>
                    <button class="tab-btn" data-platform="자소설닷컴">자소설닷컴 ({jasoseol_count})</button>
                    <button class="tab-btn" data-platform="bookmarked">⭐ 관심 공고 (<span id="bookmarkCount">0</span>)</button>
                </div>

                <select id="sortSelect" class="select-sort" aria-label="공고 정렬 기준">
                    <option value="recommend">추천순 (하이라이트 > 대기업 > 적합도)</option>
                    <option value="deadline">마감 임박순 (D-Day)</option>
                    <option value="fit">직무 적합도 점수순</option>
                    <option value="latest">최신 등록순</option>
                </select>
            </div>

            <div class="quick-keywords">
                <span class="quick-label">빠른 필터:</span>
                <button class="keyword-chip" data-keyword="대기업">#대기업</button>
                <button class="keyword-chip" data-keyword="RTOS">#RTOS</button>
                <button class="keyword-chip" data-keyword="BSP">#BSP</button>
                <button class="keyword-chip" data-keyword="펌웨어">#펌웨어</button>
                <button class="keyword-chip" data-keyword="MCU">#MCU</button>
                <button class="keyword-chip" data-keyword="C++">#C++</button>
                <button class="keyword-chip" data-keyword="Linux">#Linux커널</button>
                <button class="keyword-chip" data-keyword="AUTOSAR">#전장/AUTOSAR</button>
            </div>
        </section>

        <!-- List Header -->
        <div class="list-header">
            <div class="list-count" id="displayedCount">
                검색 결과: <span id="matchCount">{total_count}</span>건
            </div>
        </div>

        <!-- Job Cards Grid -->
        <div class="job-grid" id="jobGrid">
            <!-- 자바스크립트에 의해 동적으로 렌더링됩니다 -->
        </div>
    </main>

    <button class="btn-top" id="btnTop" aria-label="맨 위로 이동">↑</button>

    <!-- Embedded Data & Interactive App Logic -->
    <script>
        const rawJobs = {jobs_json};

        let currentPlatform = 'all';
        let currentSearch = '';
        let currentSort = 'recommend';
        let selectedKeyword = '';
        let bookmarks = JSON.parse(localStorage.getItem('job_radar_bookmarks') || '[]');

        function updateBookmarkCount() {{
            const el = document.getElementById('bookmarkCount');
            if (el) el.textContent = bookmarks.length;
        }}

        function toggleBookmark(jobId) {{
            const index = bookmarks.indexOf(jobId);
            if (index === -1) {{
                bookmarks.push(jobId);
            }} else {{
                bookmarks.splice(index, 1);
            }}
            localStorage.setItem('job_radar_bookmarks', JSON.stringify(bookmarks));
            updateBookmarkCount();
            renderJobs();
        }}

        function formatDeadline(deadlineStr) {{
            if (!deadlineStr) {{
                return {{ label: '상시 채용', badgeClass: 'deadline-normal', days: 9999 }};
            }}
            try {{
                const targetDate = new Date(deadlineStr.replace(/-/g, '/'));
                const now = new Date();
                const diffTime = targetDate - now;
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

                const month = (targetDate.getMonth() + 1).toString().padStart(2, '0');
                const day = targetDate.getDate().toString().padStart(2, '0');
                const dateText = `${{month}}/${{day}}`;

                if (diffDays < 0) {{
                    return {{ label: '마감됨', badgeClass: 'deadline-normal', days: -1 }};
                }} else if (diffDays === 0) {{
                    return {{ label: '🔥 오늘 마감', badgeClass: 'deadline-urgent', days: 0 }};
                }} else if (diffDays <= 3) {{
                    return {{ label: `🚨 D-${{diffDays}} (~${{dateText}})`, badgeClass: 'deadline-urgent', days: diffDays }};
                }} else if (diffDays <= 7) {{
                    return {{ label: `⏳ D-${{diffDays}} (~${{dateText}})`, badgeClass: 'deadline-warning', days: diffDays }};
                }} else {{
                    return {{ label: `~${{dateText}} (D-${{diffDays}})`, badgeClass: 'deadline-normal', days: diffDays }};
                }}
            }} catch (e) {{
                return {{ label: deadlineStr.substring(0, 10), badgeClass: 'deadline-normal', days: 999 }};
            }}
        }}

        function getPlatformBadgeClass(platform) {{
            if (platform === '원티드') return 'platform-wanted';
            if (platform === '잡코리아') return 'platform-jobkorea';
            if (platform === '자소설닷컴') return 'platform-jasoseol';
            return '';
        }}

        function renderJobs() {{
            const grid = document.getElementById('jobGrid');
            const matchCountEl = document.getElementById('matchCount');
            
            // 필터링
            let filtered = rawJobs.filter(job => {{
                // 북마크 필터
                if (currentPlatform === 'bookmarked') {{
                    if (!bookmarks.includes(job.job_id || job.id)) return false;
                }} else if (currentPlatform === 'highlight') {{
                    if (!job.is_highlighted && job.company_type_code !== 1) return false;
                }} else if (currentPlatform !== 'all') {{
                    if (job.platform !== currentPlatform) return false;
                }}

                // 키워드 칩 필터
                if (selectedKeyword) {{
                    const kw = selectedKeyword.toLowerCase();
                    const combined = (job.company + ' ' + job.title + ' ' + (job.duty || '') + ' ' + (job.company_type || '')).toLowerCase();
                    if (!combined.includes(kw)) return false;
                }}

                // 검색어 필터
                if (currentSearch.trim()) {{
                    const q = currentSearch.trim().toLowerCase();
                    const combined = (job.company + ' ' + job.title + ' ' + (job.duty || '') + ' ' + (job.company_type || '')).toLowerCase();
                    if (!combined.includes(q)) return false;
                }}

                return true;
            }});

            // 정렬
            filtered.sort((a, b) => {{
                if (currentSort === 'deadline') {{
                    const dlA = formatDeadline(a.deadline).days;
                    const dlB = formatDeadline(b.deadline).days;
                    return dlA - dlB;
                }} else if (currentSort === 'fit') {{
                    return (b.fit_score || 0) - (a.fit_score || 0);
                }} else if (currentSort === 'latest') {{
                    return (b.sent_at || '').localeCompare(a.sent_at || '');
                }} else {{
                    // 기본 추천순: 하이라이트 > 기업규모 > 적합도
                    if ((b.is_highlighted ? 1 : 0) !== (a.is_highlighted ? 1 : 0)) {{
                        return (b.is_highlighted ? 1 : 0) - (a.is_highlighted ? 1 : 0);
                    }}
                    if ((a.company_type_code || 4) !== (b.company_type_code || 4)) {{
                        return (a.company_type_code || 4) - (b.company_type_code || 4);
                    }}
                    return (b.fit_score || 0) - (a.fit_score || 0);
                }}
            }});

            matchCountEl.textContent = filtered.length;

            if (filtered.length === 0) {{
                grid.innerHTML = `
                    <div class="empty-state">
                        <div class="icon">🔎</div>
                        <h3>조건에 일치하는 공고가 없습니다</h3>
                        <p>검색어나 필터 조건을 변경하여 다시 확인해보세요.</p>
                    </div>
                `;
                return;
            }}

            grid.innerHTML = filtered.map(job => {{
                const jobId = job.job_id || job.id;
                const isBookmarked = bookmarks.includes(jobId);
                const isHighlight = job.is_highlighted || job.company_type_code === 1;
                const dl = formatDeadline(job.deadline);
                const platformClass = getPlatformBadgeClass(job.platform);
                
                let fitBadgeClass = 'fit-low';
                if (job.fit_level === 'High') fitBadgeClass = 'fit-high';
                else if (job.fit_level === 'Med') fitBadgeClass = 'fit-med';

                // 세부 직무 칩 파싱
                let dutyHtml = '';
                if (job.duty) {{
                    const chips = job.duty.split(/[,·/]/).map(s => s.trim()).filter(s => s.length > 0).slice(0, 4);
                    if (chips.length > 0) {{
                        dutyHtml = `<div class="duty-chips">${{chips.map(c => `<span class="duty-chip">${{c}}</span>`).join('')}}</div>`;
                    }}
                }}

                return `
                    <article class="job-card ${{isHighlight ? 'is-highlight' : ''}}" id="card-${{jobId}}">
                        <div>
                            <div class="job-card-top">
                                <div class="company-info">
                                    <span class="company-name">${{job.company || '기업명 미제공'}}</span>
                                    <span class="badge badge-platform ${{platformClass}}">${{job.platform}}</span>
                                    ${{job.is_highlighted ? '<span class="badge badge-highlight">⭐ 하이라이트</span>' : ''}}
                                    ${{job.company_type === '대기업' ? '<span class="badge badge-type-1">대기업</span>' : (job.company_type === '중견기업' ? '<span class="badge badge-type-2">중견</span>' : '')}}
                                </div>
                            </div>

                            <a href="${{job.url}}" target="_blank" rel="noopener noreferrer" style="text-decoration: none;">
                                <h2 class="job-title" title="${{job.title}}">${{job.title}}</h2>
                            </a>

                            <div class="job-details">
                                <div class="detail-row">
                                    <span class="detail-icon">⏰</span>
                                    <span class="deadline-badge ${{dl.badgeClass}}">${{dl.label}}</span>
                                    <span style="font-size: 11px; color: var(--text-subtle); margin-left: auto;">
                                        적합도 <span class="fit-pill ${{fitBadgeClass}}">${{job.fit_level}} (+${{job.fit_score || 0}})</span>
                                    </span>
                                </div>
                                ${{job.salary ? `<div class="detail-row"><span class="detail-icon">💼</span><span>${{job.salary}}</span></div>` : ''}}
                            </div>

                            ${{dutyHtml}}
                        </div>

                        <div class="card-actions">
                            <button class="btn-bookmark ${{isBookmarked ? 'bookmarked' : ''}}" onclick="toggleBookmark('${{jobId}}')" title="관심 공고 저장">
                                ${{isBookmarked ? '★' : '☆'}}
                            </button>
                            <a href="${{job.url}}" target="_blank" rel="noopener noreferrer" class="btn-link">
                                원문 공고 바로가기 ↗
                            </a>
                        </div>
                    </article>
                `;
            }}).join('');
        }}

        // Event Listeners
        document.addEventListener('DOMContentLoaded', () => {{
            updateBookmarkCount();
            renderJobs();

            // 검색 인풋
            const searchInput = document.getElementById('searchInput');
            searchInput.addEventListener('input', (e) => {{
                currentSearch = e.target.value;
                renderJobs();
            }});

            // 플랫폼 탭
            const platformTabs = document.getElementById('platformTabs');
            platformTabs.addEventListener('click', (e) => {{
                const btn = e.target.closest('.tab-btn');
                if (!btn) return;
                
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentPlatform = btn.dataset.platform;
                renderJobs();
            }});

            // 정렬 셀렉트
            const sortSelect = document.getElementById('sortSelect');
            sortSelect.addEventListener('change', (e) => {{
                currentSort = e.target.value;
                renderJobs();
            }});

            // 빠른 키워드 칩
            document.querySelectorAll('.keyword-chip').forEach(chip => {{
                chip.addEventListener('click', () => {{
                    const kw = chip.dataset.keyword;
                    if (selectedKeyword === kw) {{
                        selectedKeyword = '';
                        chip.classList.remove('active');
                    }} else {{
                        document.querySelectorAll('.keyword-chip').forEach(c => c.classList.remove('active'));
                        selectedKeyword = kw;
                        chip.classList.add('active');
                    }}
                    renderJobs();
                }});
            }});

            // Scroll to Top
            const btnTop = document.getElementById('btnTop');
            window.addEventListener('scroll', () => {{
                if (window.scrollY > 300) {{
                    btnTop.classList.add('visible');
                }} else {{
                    btnTop.classList.remove('visible');
                }}
            }});
            btnTop.addEventListener('click', () => {{
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }});
        }});
    </script>
</body>
</html>
"""

    # 파일 저장 (root / index.html 및 docs / index.html 모두 저장하여 GitHub Pages 호환성 극대화)
    for output_path in output_files:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"✅ 웹 대시보드 HTML 생성 완료: {output_path} (총 {total_count}건 임베드)")
        except Exception as e:
            logger.error(f"HTML 파일 저장 실패 ({output_path}): {e}")

    return html_content
