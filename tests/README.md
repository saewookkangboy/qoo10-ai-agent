# 테스트 관련 파일

테스트 스크립트, 실행 결과, 테스트 문서를 한 곳에서 관리합니다.

## 폴더 구조

```
tests/
├── scripts/     # 테스트 스크립트 (파이프라인·API·분석 등)
├── results/     # 테스트 실행 결과 (JSON, 생성 리포트)
├── docs/        # 테스트 요약·리포트 문서 (.md)
└── README.md    # 이 파일
```

## 스크립트 실행 방법

프로젝트 루트에서 실행하세요. `scripts/` 내 스크립트는 `api` 모듈을 자동으로 참조합니다.

```bash
# API 서버 테스트 (서버 실행 후)
python tests/scripts/test_api.py

# 데이터 파이프라인 전체 테스트
python tests/scripts/test_data_pipeline_full.py

# 파이프라인 일관성 테스트
python tests/scripts/test_pipeline_data_consistency.py
```

- **API 기반 테스트**: `test_api.py`, `test_api_shop.py`, `test_shop_whipped.py`, `test_pipeline_complete.py` — 백엔드 서버(`api`)가 떠 있어야 합니다.
- **직접 서비스 호출 테스트**: `test_data_pipeline*.py`, `test_analysis_comparison.py`, `test_report_analysis.py` 등 — `api/services`를 직접 import합니다.

## 결과 파일

- `results/`에는 스크립트 실행 시 생성되는 JSON·리포트가 저장됩니다.
- 기존 결과 파일도 이 폴더로 정리되어 있습니다.

## 문서

- `docs/`: 데이터 파이프라인 테스트 요약, Shop 분석 테스트, QC/QA 리포트 등 테스트 관련 마크다운 문서가 있습니다.
