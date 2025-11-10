# ERD 다이어그램 보기 방법

## 방법 1: VS Code에서 보기 (권장)

1. **Mermaid Preview 확장 설치**:
   - VS Code에서 `Ctrl+Shift+X` (또는 `Cmd+Shift+X` on Mac)
   - 검색: `Mermaid Preview` 또는 `Markdown Preview Mermaid Support`
   - 설치 후 마크다운 파일 열면 자동으로 렌더링됨

2. **또는 Mermaid 에디터 확장**:
   - `Mermaid Editor` 확장 설치
   - `.md` 파일에서 Mermaid 코드 블록 자동 렌더링

## 방법 2: 온라인 뷰어 사용

1. **Mermaid Live Editor**:
   - https://mermaid.live 접속
   - `SCHEMA_PROPOSAL.md` 파일에서 Mermaid 코드 블록 복사
   - 붙여넣기 후 자동 렌더링

2. **GitHub에서 보기**:
   - GitHub에 푸시하면 자동으로 렌더링됨
   - `SCHEMA_PROPOSAL.md` 파일을 GitHub에서 보면 다이어그램이 표시됨

## 방법 3: 이미지로 변환 (로컬)

### Mermaid CLI 설치 및 사용

```bash
# Node.js 필요 (npm 또는 yarn)
npm install -g @mermaid-js/mermaid-cli

# 또는 Homebrew (Mac)
brew install mermaid-cli

# 이미지로 변환
mmdc -i ai_backend/SCHEMA_PROPOSAL.md -o erd-diagram.png
```

### Python으로 변환

```bash
# Python 패키지 설치
pip install mermaid

# 또는
pip install mermaid-diagram
```

## 방법 4: 브라우저 확장 프로그램

- **Chrome/Edge**: "Mermaid Diagrams" 확장 설치
- GitHub에서 마크다운 파일을 보면 자동으로 다이어그램 표시

## 가장 쉬운 방법

1. **VS Code에서 Mermaid Preview 확장 설치** (가장 빠름)
2. **또는 GitHub에 푸시하고 웹에서 보기** (가장 간단)

