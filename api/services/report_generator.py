"""
리포트 생성 서비스
분석 결과를 PDF 또는 Excel 형태로 다운로드 가능한 리포트를 생성합니다.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import json
import io

# XML 보안: defusedxml을 사용하여 XML bomb/vector 공격 방지
# openpyxl이 Excel 파일(XLSX)을 파싱할 때 내부적으로 XML을 사용하므로
# defusedxml을 import하여 자동으로 보호됩니다.
try:
    import defusedxml.ElementTree as ET
    # openpyxl이 사용하는 XML 파서를 defusedxml으로 대체
    # 이렇게 하면 openpyxl.load_workbook()을 호출할 때 자동으로 보호됩니다.
    import defusedxml
    defusedxml.defuse_stdlib()
except ImportError:
    # defusedxml이 설치되지 않은 경우 경고
    import warnings
    warnings.warn(
        "defusedxml is not installed. XML parsing is not protected against "
        "XML bomb/vector attacks. Please install defusedxml for security.",
        UserWarning
    )


class ReportGenerator:
    """리포트 생성기"""
    
    def __init__(self):
        pass
    
    def generate_pdf_report(
        self,
        analysis_result: Dict[str, Any],
        product_data: Optional[Dict[str, Any]] = None,
        shop_data: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        PDF 리포트 생성
        
        Args:
            analysis_result: 분석 결과
            product_data: 상품 데이터 (선택사항)
            shop_data: Shop 데이터 (선택사항)
            
        Returns:
            PDF 파일 바이트
        """
        # 실제 구현 시 reportlab 또는 weasyprint 사용
        # 여기서는 간단한 텍스트 기반 리포트 생성
        
        report_content = self._generate_report_content(
            analysis_result,
            product_data,
            shop_data,
            format="pdf"
        )
        
        # PDF 생성 (실제로는 reportlab 사용)
        # 여기서는 텍스트를 반환 (실제 구현 필요)
        return report_content.encode('utf-8')
    
    def generate_excel_report(
        self,
        analysis_result: Dict[str, Any],
        product_data: Optional[Dict[str, Any]] = None,
        shop_data: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Excel 리포트 생성
        
        Args:
            analysis_result: 분석 결과
            product_data: 상품 데이터 (선택사항)
            shop_data: Shop 데이터 (선택사항)
            
        Returns:
            Excel 파일 바이트
        """
        # 실제 구현 시 openpyxl 또는 pandas 사용
        # 여기서는 JSON 형태로 반환 (실제 구현 필요)
        
        # 보안 참고: openpyxl.load_workbook()을 사용하여 Excel 파일을 읽을 때,
        # 파일 상단에서 defusedxml이 이미 import되어 있으므로
        # XML bomb/vector 공격으로부터 자동으로 보호됩니다.
        # defusedxml.defuse_stdlib()이 호출되어 표준 라이브러리의 XML 파서가
        # 안전한 버전으로 대체됩니다.
        
        excel_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "excel"
            },
            "analysis_result": analysis_result,
            "product_data": product_data,
            "shop_data": shop_data
        }
        
        # Excel 생성 (실제로는 openpyxl 사용)
        # 예시 코드:
        # from openpyxl import Workbook
        # wb = Workbook()
        # ws = wb.active
        # ... 데이터 작성 ...
        # buffer = io.BytesIO()
        # wb.save(buffer)
        # return buffer.getvalue()
        # 
        # Excel 파일을 읽는 경우 (예: openpyxl.load_workbook(file_path)):
        # defusedxml이 이미 활성화되어 있으므로 자동으로 보호됩니다.
        # 여기서는 JSON을 반환 (실제 구현 필요)
        return json.dumps(excel_data, ensure_ascii=False, indent=2).encode('utf-8')
    
    def generate_markdown_report(
        self,
        analysis_result: Dict[str, Any],
        product_data: Optional[Dict[str, Any]] = None,
        shop_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Markdown 리포트 생성
        
        Args:
            analysis_result: 분석 결과
            product_data: 상품 데이터 (선택사항)
            shop_data: Shop 데이터 (선택사항)
            
        Returns:
            Markdown 문자열
        """
        return self._generate_report_content(
            analysis_result,
            product_data,
            shop_data,
            format="markdown"
        )
    
    def _generate_report_content(
        self,
        analysis_result: Dict[str, Any],
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        format: str = "markdown"
    ) -> str:
        """리포트 내용 생성"""
        lines = []
        
        # 헤더
        lines.append("# Qoo10 Sales Intelligence Agent - 분석 리포트")
        lines.append(f"\n생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("\n---\n")
        
        # 상품 정보
        if product_data:
            lines.append("## 상품 정보")
            lines.append(f"- 상품명: {product_data.get('product_name', 'N/A')}")
            lines.append(f"- 상품 코드: {product_data.get('product_code', 'N/A')}")
            lines.append(f"- 카테고리: {product_data.get('category', 'N/A')}")
            lines.append(f"- 브랜드: {product_data.get('brand', 'N/A')}")
            lines.append("\n")
        
        # Shop 정보
        if shop_data:
            lines.append("## Shop 정보")
            lines.append(f"- Shop 이름: {shop_data.get('shop_name', 'N/A')}")
            lines.append(f"- Shop 레벨: {shop_data.get('shop_level', 'N/A')}")
            lines.append(f"- 팔로워 수: {shop_data.get('follower_count', 0):,}명")
            lines.append(f"- 상품 수: {shop_data.get('product_count', 0)}개")
            lines.append("\n")
        
        # 분석 결과
        if "product_analysis" in analysis_result:
            product_analysis = analysis_result["product_analysis"]
            lines.append("## 상품 분석 결과")
            lines.append(f"\n### 종합 점수: {product_analysis.get('overall_score', 0)}/100\n")
            
            # 이미지 분석
            image_analysis = product_analysis.get("image_analysis", {})
            lines.append(f"#### 이미지 분석: {image_analysis.get('score', 0)}/100")
            lines.append(f"- 썸네일 품질: {image_analysis.get('thumbnail_quality', 'N/A')}")
            lines.append(f"- 상세 이미지 개수: {image_analysis.get('image_count', 0)}개")
            if image_analysis.get("recommendations"):
                lines.append("제안:")
                for rec in image_analysis["recommendations"]:
                    lines.append(f"  - {rec}")
            lines.append("\n")
            
            # 설명 분석
            desc_analysis = product_analysis.get("description_analysis", {})
            lines.append(f"#### 설명 분석: {desc_analysis.get('score', 0)}/100")
            lines.append(f"- 설명 길이: {desc_analysis.get('description_length', 0)}자")
            if desc_analysis.get("recommendations"):
                lines.append("제안:")
                for rec in desc_analysis["recommendations"]:
                    lines.append(f"  - {rec}")
            lines.append("\n")
            
            # 가격 분석
            price_analysis = product_analysis.get("price_analysis", {})
            sale_price = price_analysis.get('sale_price') if price_analysis.get('sale_price') is not None else 0
            discount_rate = price_analysis.get('discount_rate') if price_analysis.get('discount_rate') is not None else 0
            lines.append(f"#### 가격 분석: {price_analysis.get('score', 0)}/100")
            lines.append(f"- 판매가: {sale_price:,}엔")
            lines.append(f"- 할인율: {discount_rate}%")
            lines.append("\n")
            
            # 리뷰 분석
            review_analysis = product_analysis.get("review_analysis", {})
            rating = review_analysis.get('rating') if review_analysis.get('rating') is not None else 0.0
            review_count = review_analysis.get('review_count') if review_analysis.get('review_count') is not None else 0
            lines.append(f"#### 리뷰 분석: {review_analysis.get('score', 0)}/100")
            lines.append(f"- 평점: {rating:.1f}/5.0")
            lines.append(f"- 리뷰 수: {review_count:,}개")
            lines.append("\n")
        
        # Shop 분석
        if "shop_analysis" in analysis_result:
            shop_analysis = analysis_result["shop_analysis"]
            lines.append("## Shop 분석 결과")
            lines.append(f"\n### 종합 점수: {shop_analysis.get('overall_score', 0)}/100\n")
            
            level_analysis = shop_analysis.get("level_analysis", {})
            lines.append("#### Shop 레벨")
            lines.append(f"- 현재 레벨: {level_analysis.get('current_level', 'N/A')}")
            lines.append(f"- 정산 리드타임: {level_analysis.get('settlement_leadtime', 15)}일")
            lines.append("\n")
        
        # 추천 아이디어
        recommendations = analysis_result.get("recommendations", [])
        if recommendations:
            lines.append("## 매출 강화 아이디어\n")
            for i, rec in enumerate(recommendations, 1):
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec.get("priority"), "⚪")
                lines.append(f"### {i}. {priority_emoji} [{rec.get('priority', 'N/A').upper()}] {rec.get('title', 'N/A')}")
                lines.append(f"\n{rec.get('description', 'N/A')}\n")
                if rec.get("action_items"):
                    lines.append("실행 방법:")
                    for item in rec["action_items"]:
                        lines.append(f"- {item}")
                lines.append("\n")
        
        # 체크리스트
        checklist = analysis_result.get("checklist", {})
        if checklist:
            lines.append("## 메뉴얼 기반 체크리스트\n")
            lines.append(f"### 전체 완성도: {checklist.get('overall_completion', 0)}%\n")
            for cl in checklist.get("checklists", []):
                lines.append(f"#### {cl.get('category', 'N/A')}: {cl.get('completion_rate', 0)}%")
                for item in cl.get("items", []):
                    status_emoji = "✅" if item.get("status") == "completed" else "⬜"
                    lines.append(f"- {status_emoji} {item.get('title', 'N/A')}")
                lines.append("\n")
        
        # 경쟁사 분석
        competitor_analysis = analysis_result.get("competitor_analysis", {})
        if competitor_analysis:
            lines.append("## 경쟁사 비교 분석\n")
            comparison = competitor_analysis.get("comparison", {})
            lines.append(f"### 가격 포지셔닝: {comparison.get('price_position', 'N/A')}")
            lines.append(f"### 평점 포지셔닝: {comparison.get('rating_position', 'N/A')}")
            lines.append(f"### 리뷰 포지셔닝: {comparison.get('review_position', 'N/A')}\n")
            
            if competitor_analysis.get("differentiation_points"):
                lines.append("### 차별화 포인트:")
                for point in competitor_analysis["differentiation_points"]:
                    lines.append(f"- {point}")
                lines.append("\n")
        
        return "\n".join(lines)
