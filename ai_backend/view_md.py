#!/usr/bin/env python3
"""
Markdown 파일을 Mermaid 다이어그램을 포함하여 브라우저에서 보여주는 로컬 서버
"""
import http.server
import os
import re
import socketserver
import sys
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import markdown
from markdown.extensions import codehilite, fenced_code, tables

PORT = 8000


class MarkdownHandler(http.server.SimpleHTTPRequestHandler):
    """Markdown 파일을 HTML로 변환하여 제공하는 핸들러"""

    def do_GET(self):
        """GET 요청 처리"""
        parsed_path = urlparse(self.path)

        # 루트 경로면 index.html 제공
        if parsed_path.path == "/" or parsed_path.path == "/index.html":
            self.send_index()
            return

        # Markdown 파일 요청
        if parsed_path.path.endswith(".md"):
            self.send_markdown(parsed_path.path)
            return

        # 정적 파일 (CSS, JS 등)
        return super().do_GET()

    def send_index(self):
        """인덱스 페이지 제공"""
        md_files = list(Path(".").glob("*.md"))

        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown Viewer</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{ color: #333; }}
        ul {{ list-style: none; padding: 0; }}
        li {{
            margin: 10px 0;
            padding: 15px;
            background: white;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        a {{
            text-decoration: none;
            color: #4CAF50;
            font-size: 18px;
            font-weight: bold;
        }}
        a:hover {{ color: #45a049; }}
    </style>
</head>
<body>
    <h1>📄 Markdown 파일 목록</h1>
    <ul>
"""
        for md_file in sorted(md_files):
            html += f'        <li><a href="{md_file.name}">{md_file.name}</a></li>\n'

        html += """    </ul>
</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def send_markdown(self, md_path):
        """Markdown 파일을 HTML로 변환하여 제공"""
        try:
            # 파일 경로 정규화
            file_path = Path(md_path.lstrip("/"))

            if not file_path.exists():
                self.send_error(404, "File not found")
                return

            # Markdown 파일 읽기
            with open(file_path, "r", encoding="utf-8") as f:
                md_content = f.read()

            # Markdown을 HTML로 변환
            md = markdown.Markdown(
                extensions=[
                    "codehilite",
                    "fenced_code",
                    "tables",
                    "nl2br",
                    "sane_lists",
                ],
                extension_configs={
                    "codehilite": {"css_class": "highlight", "use_pygments": False}
                },
            )
            html_content = md.convert(md_content)

            # Mermaid 스크립트 추가
            html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{file_path.name} - Markdown Viewer</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown.min.css">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .markdown-body {{
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .mermaid {{
            text-align: center;
            margin: 20px 0;
        }}
        code {{
            background-color: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'SFMono-Regular', Consolas, monospace;
        }}
        pre {{
            background-color: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }}
        table th, table td {{
            border: 1px solid #dfe2e5;
            padding: 8px 16px;
        }}
        table th {{
            background-color: #f6f8fa;
            font-weight: bold;
        }}
        .back-link {{
            display: inline-block;
            margin-bottom: 20px;
            color: #4CAF50;
            text-decoration: none;
            font-weight: bold;
        }}
        .back-link:hover {{
            color: #45a049;
        }}
    </style>
</head>
<body>
    <a href="/" class="back-link">← 목록으로</a>
    <div class="markdown-body">
        {html_content}
    </div>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true
            }}
        }});
    </script>
</body>
</html>"""

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        except Exception as e:
            self.send_error(500, f"Error processing markdown: {str(e)}")


def main():
    """메인 함수"""
    # 현재 디렉토리를 서버 루트로 설정
    os.chdir(Path(__file__).parent)

    # 서버 시작
    with socketserver.TCPServer(("", PORT), MarkdownHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"🚀 Markdown Viewer 서버가 시작되었습니다!")
        print(f"📄 브라우저에서 {url} 을 열어주세요")
        print(
            f"📝 Markdown 파일을 클릭하면 Mermaid 다이어그램을 포함하여 볼 수 있습니다"
        )
        print(f"\n종료하려면 Ctrl+C를 누르세요")

        # 브라우저 자동 열기
        try:
            webbrowser.open(url)
        except:
            pass

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n서버를 종료합니다.")


if __name__ == "__main__":
    main()
