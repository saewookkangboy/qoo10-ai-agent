"""
리포트 생성 서비스
분석 결과를 PDF, Excel, Markdown, DOC 형태로 다운로드 가능한 리포트를 생성합니다.

리포트 생성 원칙:
- CRAWLING_ANALYSIS_PRINCIPLES.md 참조
- 모든 리포트는 일관된 구조와 형식을 따라야 함
- 크롤링 방법(crawled_with)을 명시해야 함
- 점수 계산 기준은 원칙 문서를 준수해야 함
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import io
import os

from services.logging_utils import log_debug as _log_debug

# XML 보안: defusedxml을 사용하여 XML bomb/vector 공격 방지
try:
    import defusedxml.ElementTree as ET
    import defusedxml
    defusedxml.defuse_stdlib()
except ImportError:
    import warnings
    warnings.warn(
        "defusedxml is not installed. XML parsing is not protected against "
        "XML bomb/vector attacks. Please install defusedxml for security.",
        UserWarning
    )

# DOC 파일 생성을 위한 python-docx
try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    # Document가 없을 때를 위한 더미 클래스 (타입 힌트용)
    Document = None  # type: ignore


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
        # Markdown 리포트를 생성하여 PDF로 변환
        markdown_content = self.generate_markdown_report(
            analysis_result,
            product_data,
            shop_data
        )
        # 실제 PDF 생성은 reportlab 사용 (향후 구현)
        return markdown_content.encode('utf-8')
    
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
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            
            wb = Workbook()
            ws = wb.active
            ws.title = "분석 리포트"
            
            # 헤더 스타일
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=12)
            
            row = 1
            
            # 제목
            ws.merge_cells(f'A{row}:D{row}')
            ws[f'A{row}'] = "Qoo10 Sales Intelligence Agent - 분석 리포트"
            ws[f'A{row}'].font = Font(bold=True, size=16)
            ws[f'A{row}'].alignment = Alignment(horizontal="center", vertical="center")
            row += 2
            
            # 생성일시
            ws[f'A{row}'] = f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            row += 2
            
            # 상품 정보
            if product_data:
                ws[f'A{row}'] = "상품 정보"
                ws[f'A{row}'].font = header_font
                ws[f'A{row}'].fill = header_fill
                row += 1
                
                # 상품명 (개선된 추출 로직 반영)
                product_name = product_data.get('product_name', 'N/A')
                if product_name and product_name != '상품명 없음' and product_name != 'N/A':
                    product_name_display = product_name
                else:
                    product_name_display = 'N/A (추출 실패)'
                
                ws[f'A{row}'] = "상품명"
                ws[f'B{row}'] = product_name_display
                row += 1
                ws[f'A{row}'] = "상품 코드"
                ws[f'B{row}'] = product_data.get('product_code', 'N/A')
                row += 1
                ws[f'A{row}'] = "카테고리"
                ws[f'B{row}'] = product_data.get('category', 'N/A')
                row += 1
                ws[f'A{row}'] = "브랜드"
                ws[f'B{row}'] = product_data.get('brand', 'N/A')
                row += 1
                
                # 가격 정보 (유효성 검증된 값만 표시)
                price_data = product_data.get('price', {})
                sale_price = price_data.get('sale_price')
                original_price = price_data.get('original_price')
                
                ws[f'A{row}'] = "판매가"
                if sale_price and 100 <= sale_price <= 1000000:
                    ws[f'B{row}'] = f"{sale_price:,}円"
                else:
                    ws[f'B{row}'] = "N/A"
                row += 1
                
                if original_price and 100 <= original_price <= 1000000:
                    ws[f'A{row}'] = "정가"
                    ws[f'B{row}'] = f"{original_price:,}円"
                    row += 1
                    if sale_price and original_price > sale_price:
                        discount_rate = int((original_price - sale_price) / original_price * 100)
                        ws[f'A{row}'] = "할인율"
                        ws[f'B{row}'] = f"{discount_rate}%"
                        row += 1
                
                # Qポイント 정보
                qpoint_info = product_data.get('qpoint_info', {})
                if qpoint_info and any(qpoint_info.values()):
                    qpoint_lines = []
                    if qpoint_info.get('max_points'):
                        qpoint_lines.append(f"최대 {qpoint_info['max_points']}P")
                    if qpoint_info.get('receive_confirmation_points'):
                        qpoint_lines.append(f"수령확인 {qpoint_info['receive_confirmation_points']}P")
                    if qpoint_info.get('review_points'):
                        qpoint_lines.append(f"리뷰작성 {qpoint_info['review_points']}P")
                    if qpoint_lines:
                        ws[f'A{row}'] = "Qポイント"
                        ws[f'B{row}'] = ', '.join(qpoint_lines)
                        row += 1
                
                # 반품 정보
                shipping_info = product_data.get('shipping_info', {})
                return_policy = shipping_info.get('return_policy')
                if return_policy:
                    return_text = "무료반품 가능" if return_policy == "free_return" else "반품 가능"
                    ws[f'A{row}'] = "반품 정책"
                    ws[f'B{row}'] = return_text
                    row += 1
                
                row += 1
            
            # Shop 정보
            if shop_data:
                ws[f'A{row}'] = "Shop 정보"
                ws[f'A{row}'].font = header_font
                ws[f'A{row}'].fill = header_fill
                row += 1
                
                ws[f'A{row}'] = "Shop 이름"
                ws[f'B{row}'] = shop_data.get('shop_name', 'N/A')
                row += 1
                ws[f'A{row}'] = "Shop 레벨"
                ws[f'B{row}'] = shop_data.get('shop_level', 'N/A')
                row += 1
                ws[f'A{row}'] = "팔로워 수"
                ws[f'B{row}'] = shop_data.get('follower_count', 0)
                row += 1
                ws[f'A{row}'] = "상품 수"
                ws[f'B{row}'] = shop_data.get('product_count', 0)
                row += 2
            
            # 분석 결과
            if "product_analysis" in analysis_result:
                product_analysis = analysis_result["product_analysis"]
                ws[f'A{row}'] = "상품 분석 결과"
                ws[f'A{row}'].font = header_font
                ws[f'A{row}'].fill = header_fill
                row += 1
                
                ws[f'A{row}'] = "종합 점수"
                ws[f'B{row}'] = f"{product_analysis.get('overall_score', 0)}/100"
                row += 1
                
                # 각 분석 항목
                for analysis_type in ["image_analysis", "description_analysis", "price_analysis", 
                                     "review_analysis", "seo_analysis", "page_structure_analysis"]:
                    if analysis_type in product_analysis:
                        analysis = product_analysis[analysis_type]
                        ws[f'A{row}'] = analysis_type.replace("_", " ").title()
                        ws[f'B{row}'] = f"{analysis.get('score', 0)}/100"
                        row += 1
                row += 1
            
            # 컬럼 너비 조정
            ws.column_dimensions['A'].width = 25
            ws.column_dimensions['B'].width = 40
            
            buffer = io.BytesIO()
            wb.save(buffer)
            return buffer.getvalue()
        except ImportError:
            # openpyxl이 없는 경우 JSON 반환
            excel_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "report_type": "excel"
                },
                "analysis_result": analysis_result,
                "product_data": product_data,
                "shop_data": shop_data
            }
            return json.dumps(excel_data, ensure_ascii=False, indent=2).encode('utf-8')
    
    def generate_markdown_report(
        self,
        analysis_result: Dict[str, Any],
        product_data: Optional[Dict[str, Any]] = None,
        shop_data: Optional[Dict[str, Any]] = None,
        validation_result: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Markdown 리포트 생성
        
        Args:
            analysis_result: 분석 결과
            product_data: 상품 데이터 (선택사항)
            shop_data: Shop 데이터 (선택사항)
            validation_result: 검증 결과 (선택사항)
            
        Returns:
            Markdown 문자열
        """
        # #region agent log - H5 가설 검증
        _log_debug("debug-session", "run1", "H5", "report_generator.py:generate_markdown_report", "리포트 생성 함수 호출 - 체크리스트 확인", {
            "has_analysis_result": bool(analysis_result),
            "analysis_result_keys": list(analysis_result.keys()) if analysis_result and isinstance(analysis_result, dict) else None,
            "has_checklist_in_result": "checklist" in analysis_result if analysis_result and isinstance(analysis_result, dict) else False,
            "checklist_data": analysis_result.get("checklist") if analysis_result and isinstance(analysis_result, dict) else None,
            "checklist_overall_completion": analysis_result.get("checklist", {}).get("overall_completion") if analysis_result and isinstance(analysis_result, dict) and analysis_result.get("checklist") else None,
            "checklist_count": len(analysis_result.get("checklist", {}).get("checklists", [])) if analysis_result and isinstance(analysis_result, dict) and analysis_result.get("checklist") else 0,
            "has_validation_result": bool(validation_result)
        })
        # #endregion
        return self._generate_report_content(
            analysis_result,
            product_data,
            shop_data,
            format="markdown",
            validation_result=validation_result
        )
    
    def generate_doc_report(
        self,
        analysis_result: Dict[str, Any],
        product_data: Optional[Dict[str, Any]] = None,
        shop_data: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        DOC 리포트 생성
        
        Args:
            analysis_result: 분석 결과
            product_data: 상품 데이터 (선택사항)
            shop_data: Shop 데이터 (선택사항)
            
        Returns:
            DOC 파일 바이트
        """
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx is required for DOC report generation")
        
        doc = Document()
        
        # 제목
        title = doc.add_heading('Qoo10 Sales Intelligence Agent - 분석 리포트', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 생성일시
        date_para = doc.add_paragraph(f'생성일시: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()  # 빈 줄
        
        # 상품 정보
        if product_data:
            doc.add_heading('상품 정보', level=1)
            
            # 상품명 (개선된 추출 로직 반영)
            product_name = product_data.get('product_name', 'N/A')
            if product_name and product_name != '상품명 없음' and product_name != 'N/A':
                product_name_display = product_name
            else:
                product_name_display = 'N/A (추출 실패)'
            
            info_items = [
                ("상품명", product_name_display),
                ("상품 코드", product_data.get('product_code', 'N/A')),
                ("카테고리", product_data.get('category', 'N/A')),
                ("브랜드", product_data.get('brand', 'N/A')),
            ]
            
            # 가격 정보 (유효성 검증된 값만 표시)
            price_data = product_data.get('price', {})
            sale_price = price_data.get('sale_price')
            original_price = price_data.get('original_price')
            
            if sale_price and 100 <= sale_price <= 1000000:
                info_items.append(("판매가", f"{sale_price:,}円"))
            else:
                info_items.append(("판매가", "N/A"))
            
            if original_price and 100 <= original_price <= 1000000:
                info_items.append(("정가", f"{original_price:,}円"))
                if sale_price and original_price > sale_price:
                    discount_rate = int((original_price - sale_price) / original_price * 100)
                    info_items.append(("할인율", f"{discount_rate}%"))
            
            # Qポイント 정보
            qpoint_info = product_data.get('qpoint_info', {})
            if qpoint_info and any(qpoint_info.values()):
                qpoint_lines = []
                if qpoint_info.get('max_points'):
                    qpoint_lines.append(f"최대 {qpoint_info['max_points']}P")
                if qpoint_info.get('receive_confirmation_points'):
                    qpoint_lines.append(f"수령확인 {qpoint_info['receive_confirmation_points']}P")
                if qpoint_info.get('review_points'):
                    qpoint_lines.append(f"리뷰작성 {qpoint_info['review_points']}P")
                if qpoint_lines:
                    info_items.append(("Qポイント", ', '.join(qpoint_lines)))
                else:
                    info_items.append(("Qポイント", "N/A"))
            else:
                info_items.append(("Qポイント", "N/A"))
            
            # 반품 정보
            shipping_info = product_data.get('shipping_info', {})
            return_policy = shipping_info.get('return_policy')
            if return_policy:
                return_text = "무료반품 가능" if return_policy == "free_return" else "반품 가능"
                info_items.append(("반품 정책", return_text))
            else:
                info_items.append(("반품 정책", "N/A"))
            
            self._add_info_table(doc, info_items)
            doc.add_paragraph()
        
        # Shop 정보
        if shop_data:
            doc.add_heading('Shop 정보', level=1)
            self._add_info_table(doc, [
                ("Shop 이름", shop_data.get('shop_name', 'N/A')),
                ("Shop 레벨", shop_data.get('shop_level', 'N/A')),
                ("팔로워 수", f"{shop_data.get('follower_count', 0):,}명"),
                ("상품 수", f"{shop_data.get('product_count', 0)}개"),
            ])
            doc.add_paragraph()
        
        # 상품 분석 결과
        if "product_analysis" in analysis_result:
            product_analysis = analysis_result["product_analysis"]
            doc.add_heading('상품 분석 결과', level=1)
            
            # 종합 점수
            overall_score = product_analysis.get('overall_score', 0)
            score_para = doc.add_paragraph()
            score_para.add_run('종합 점수: ').bold = True
            score_para.add_run(f'{overall_score}/100').bold = True
            score_para.add_run(f' ({self._get_grade(overall_score)})')
            doc.add_paragraph()
            
            # 이미지 분석
            self._add_analysis_section(doc, "이미지 분석", product_analysis.get("image_analysis", {}))
            
            # 설명 분석
            self._add_analysis_section(doc, "상품 설명 분석", product_analysis.get("description_analysis", {}))
            
            # 가격 분석
            self._add_price_analysis_section(doc, product_analysis.get("price_analysis", {}))
            
            # 리뷰 분석
            self._add_review_analysis_section(doc, product_analysis.get("review_analysis", {}))
            
            # SEO 분석
            self._add_analysis_section(doc, "SEO 분석", product_analysis.get("seo_analysis", {}))
            
            # 페이지 구조 분석
            self._add_analysis_section(doc, "페이지 구조 분석", product_analysis.get("page_structure_analysis", {}))
        
        # Shop 분석
        if "shop_analysis" in analysis_result:
            shop_analysis = analysis_result["shop_analysis"]
            doc.add_heading('Shop 분석 결과', level=1)
            
            overall_score = shop_analysis.get('overall_score', 0)
            score_para = doc.add_paragraph()
            score_para.add_run('종합 점수: ').bold = True
            score_para.add_run(f'{overall_score}/100').bold = True
            score_para.add_run(f' ({self._get_grade(overall_score)})')
            doc.add_paragraph()
            
            # Shop 정보 분석
            self._add_shop_info_section(doc, shop_analysis)
            
            # Shop 특수성 분석
            if "shop_specialty" in shop_analysis:
                self._add_shop_specialty_section(doc, shop_analysis.get("shop_specialty", {}))
            
            # 맞춤형 인사이트
            if "customized_insights" in shop_analysis:
                self._add_customized_insights_section(doc, shop_analysis.get("customized_insights", {}))
        
        # 추천 아이디어
        recommendations = analysis_result.get("recommendations", [])
        if recommendations:
            doc.add_heading('매출 강화 아이디어', level=1)
            for i, rec in enumerate(recommendations, 1):
                priority = rec.get("priority", "medium").upper()
                title_text = f"{i}. [{priority}] {rec.get('title', 'N/A')}"
                doc.add_heading(title_text, level=2)
                
                doc.add_paragraph(rec.get('description', 'N/A'))
                
                if rec.get("action_items"):
                    doc.add_paragraph('실행 방법:', style='List Bullet')
                    for item in rec["action_items"]:
                        doc.add_paragraph(item, style='List Bullet 2')
                doc.add_paragraph()
        
        # 체크리스트
        checklist = analysis_result.get("checklist", {})
        if checklist:
            doc.add_heading('메뉴얼 기반 체크리스트', level=1)
            overall_completion = checklist.get('overall_completion', 0)
            doc.add_paragraph(f'전체 완성도: {overall_completion}%')
            doc.add_paragraph()
            
            for cl in checklist.get("checklists", []):
                doc.add_heading(f"{cl.get('category', 'N/A')}: {cl.get('completion_rate', 0)}%", level=2)
                for item in cl.get("items", []):
                    status = "✅" if item.get("status") == "completed" else "⬜"
                    doc.add_paragraph(f"{status} {item.get('title', 'N/A')}", style='List Bullet')
                doc.add_paragraph()
        
        # 경쟁사 분석
        competitor_analysis = analysis_result.get("competitor_analysis", {})
        if competitor_analysis:
            doc.add_heading('경쟁사 비교 분석', level=1)
            comparison = competitor_analysis.get("comparison", {})
            doc.add_paragraph(f'가격 포지셔닝: {comparison.get("price_position", "N/A")}')
            doc.add_paragraph(f'평점 포지셔닝: {comparison.get("rating_position", "N/A")}')
            doc.add_paragraph(f'리뷰 포지셔닝: {comparison.get("review_position", "N/A")}')
            doc.add_paragraph()
            
            if competitor_analysis.get("differentiation_points"):
                doc.add_heading('차별화 포인트', level=2)
                for point in competitor_analysis["differentiation_points"]:
                    doc.add_paragraph(point, style='List Bullet')
        
        # 문서를 바이트로 변환
        buffer = io.BytesIO()
        doc.save(buffer)
        return buffer.getvalue()
    
    def _add_info_table(self, doc: Any, data: List[tuple]):
        """정보 테이블 추가"""
        table = doc.add_table(rows=len(data), cols=2)
        table.style = 'Light Grid Accent 1'
        
        for i, (key, value) in enumerate(data):
            table.rows[i].cells[0].text = key
            table.rows[i].cells[1].text = str(value)
            table.rows[i].cells[0].paragraphs[0].runs[0].bold = True
    
    def _add_analysis_section(self, doc: Any, title: str, analysis: Dict[str, Any]):
        """분석 섹션 추가"""
        doc.add_heading(title, level=2)
        
        score = analysis.get('score', 0)
        score_para = doc.add_paragraph()
        score_para.add_run('점수: ').bold = True
        score_para.add_run(f'{score}/100').bold = True
        score_para.add_run(f' ({self._get_grade(score)})')
        
        # 세부 정보 추가
        if title == "이미지 분석":
            doc.add_paragraph(f'썸네일 품질: {analysis.get("thumbnail_quality", "N/A")}')
            doc.add_paragraph(f'상세 이미지 개수: {analysis.get("image_count", 0)}개')
        elif title == "상품 설명 분석":
            doc.add_paragraph(f'설명 길이: {analysis.get("description_length", 0)}자')
            doc.add_paragraph(f'구조화 품질: {analysis.get("structure_quality", "N/A")}')
        elif title == "SEO 분석":
            doc.add_paragraph(f'키워드 상품명 포함: {"예" if analysis.get("keywords_in_name") else "아니오"}')
            doc.add_paragraph(f'키워드 설명 포함: {"예" if analysis.get("keywords_in_description") else "아니오"}')
            doc.add_paragraph(f'카테고리 설정: {"예" if analysis.get("category_set") else "아니오"}')
            doc.add_paragraph(f'브랜드 설정: {"예" if analysis.get("brand_set") else "아니오"}')
        elif title == "페이지 구조 분석":
            doc.add_paragraph(f'전체 클래스 수: {analysis.get("total_classes", 0)}개')
            grade = analysis.get("grade") or self._get_grade(analysis.get("score", 0))
            doc.add_paragraph(f'등급: {grade}')
            key_elements = analysis.get("key_elements_present", {})
            if key_elements:
                doc.add_paragraph('주요 요소 존재 여부:')
                for key, present in key_elements.items():
                    doc.add_paragraph(f'  - {key}: {"예" if present else "아니오"}', style='List Bullet 2')
            eq = analysis.get("element_quality") or {}
            if eq.get("overall_quality_score") is not None:
                doc.add_paragraph(f'요소 품질 점수: {eq.get("overall_quality_score", 0)}/100 (다양성: {eq.get("diversity_score", 0)}, 일관성: {eq.get("consistency_score", 0)})')
            rel = analysis.get("element_relationships") or {}
            if rel.get("relationship_score") is not None:
                doc.add_paragraph(f'요소 간 관계 점수: {rel.get("relationship_score", 0)}/100')
        
        # 추천 사항
        if analysis.get("recommendations"):
            doc.add_paragraph('추천 사항:', style='List Bullet')
            for rec in analysis["recommendations"]:
                doc.add_paragraph(rec, style='List Bullet 2')
        
        doc.add_paragraph()
    
    def _add_price_analysis_section(self, doc: Any, analysis: Dict[str, Any]):
        """가격 분석 섹션 추가 (개선된 크롤러 데이터 반영)"""
        doc.add_heading('가격 분석', level=2)
        
        score = analysis.get('score', 0)
        score_para = doc.add_paragraph()
        score_para.add_run('점수: ').bold = True
        score_para.add_run(f'{score}/100').bold = True
        score_para.add_run(f' ({self._get_grade(score)})')
        
        # 유효성 검증된 가격만 표시 (100~1,000,000엔 범위)
        sale_price = analysis.get('sale_price')
        original_price = analysis.get('original_price')
        discount_rate = analysis.get('discount_rate', 0) or 0
        
        if sale_price and 100 <= sale_price <= 1000000:
            doc.add_paragraph(f'판매가: {sale_price:,}円')
        else:
            doc.add_paragraph('판매가: N/A (유효하지 않은 값)')
        
        if original_price and 100 <= original_price <= 1000000:
            doc.add_paragraph(f'정가: {original_price:,}円')
            if sale_price and original_price > sale_price:
                calculated_discount = int((original_price - sale_price) / original_price * 100)
                doc.add_paragraph(f'할인율: {calculated_discount}%')
        elif discount_rate > 0:
            doc.add_paragraph(f'할인율: {discount_rate}%')
        
        positioning = analysis.get('positioning', '')
        if positioning:
            doc.add_paragraph(f'가격 포지셔닝: {positioning}')
        
        if analysis.get("recommendations"):
            doc.add_paragraph('추천 사항:', style='List Bullet')
            for rec in analysis["recommendations"]:
                doc.add_paragraph(rec, style='List Bullet 2')
        
        doc.add_paragraph()
    
    def _add_review_analysis_section(self, doc: Any, analysis: Dict[str, Any]):
        """리뷰 분석 섹션 추가 (개선된 크롤러 데이터 반영)"""
        doc.add_heading('리뷰 분석', level=2)
        
        score = analysis.get('score', 0)
        score_para = doc.add_paragraph()
        score_para.add_run('점수: ').bold = True
        score_para.add_run(f'{score}/100').bold = True
        score_para.add_run(f' ({self._get_grade(score)})')
        
        rating = analysis.get('rating', 0) or 0.0
        review_count = analysis.get('review_count', 0) or 0
        # fallback: reviews 배열 길이 사용
        reviews_list = analysis.get('reviews', [])
        if review_count == 0 and len(reviews_list) > 0:
            review_count = len(reviews_list)
        
        negative_ratio = analysis.get('negative_ratio', 0.0) or 0.0
        
        doc.add_paragraph(f'평점: {rating:.1f}/5.0')
        if review_count > 0:
            doc.add_paragraph(f'리뷰 수: {review_count:,}개')
        else:
            doc.add_paragraph('리뷰 수: 0개 (또는 추출 실패)')
        
        if len(reviews_list) > 0:
            doc.add_paragraph(f'추출된 리뷰 텍스트: {len(reviews_list)}개')
        
        if negative_ratio > 0:
            doc.add_paragraph(f'부정 리뷰 비율: {negative_ratio:.1%}')
        
        if analysis.get("recommendations"):
            doc.add_paragraph('추천 사항:', style='List Bullet')
            for rec in analysis["recommendations"]:
                doc.add_paragraph(rec, style='List Bullet 2')
        
        doc.add_paragraph()
    
    def _add_shop_info_section(self, doc: Any, shop_analysis: Dict[str, Any]):
        """Shop 정보 분석 섹션 추가"""
        shop_info = shop_analysis.get("shop_info", {})
        if shop_info:
            doc.add_heading('Shop 정보 분석', level=2)
            doc.add_paragraph(f'점수: {shop_info.get("score", 0)}/100 ({self._get_grade(shop_info.get("score", 0))})')
            doc.add_paragraph()
        
        level_analysis = shop_analysis.get("level_analysis", {})
        if level_analysis:
            doc.add_heading('Shop 레벨 분석', level=2)
            doc.add_paragraph(f'현재 레벨: {level_analysis.get("current_level", "N/A")}')
            doc.add_paragraph(f'정산 리드타임: {level_analysis.get("settlement_leadtime", 15)}일')
            doc.add_paragraph(f'목표 레벨: {level_analysis.get("target_level", "N/A")}')
            
            if level_analysis.get("requirements"):
                doc.add_paragraph('요구사항:', style='List Bullet')
                for req in level_analysis["requirements"]:
                    doc.add_paragraph(req, style='List Bullet 2')
            
            if level_analysis.get("recommendations"):
                doc.add_paragraph('추천 사항:', style='List Bullet')
                for rec in level_analysis["recommendations"]:
                    doc.add_paragraph(rec, style='List Bullet 2')
            doc.add_paragraph()
    
    def _add_shop_specialty_section(self, doc: Any, specialty: Dict[str, Any]):
        """Shop 특수성 섹션 추가"""
        doc.add_heading('Shop 특수성 분석', level=2)
        
        doc.add_paragraph(f'브랜드 샵 여부: {"예" if specialty.get("is_brand_shop") else "아니오"}')
        if specialty.get("brand_name"):
            doc.add_paragraph(f'브랜드명: {specialty.get("brand_name")}')
        
        lineup_type = specialty.get("product_lineup_type", "mixed")
        doc.add_paragraph(f'제품 라인업 특성: {lineup_type}')
        
        target_customer = specialty.get("target_customer", "general")
        doc.add_paragraph(f'타겟 고객층: {target_customer.replace("_", " ")}')
        
        unique_features = specialty.get("unique_features", [])
        if unique_features:
            doc.add_paragraph('독특한 특징:', style='List Bullet')
            for feature in unique_features:
                doc.add_paragraph(feature, style='List Bullet 2')
        
        doc.add_paragraph(f'특수성 점수: {specialty.get("specialty_score", 0)}/100')
        doc.add_paragraph()
    
    def _add_customized_insights_section(self, doc: Any, insights: Dict[str, Any]):
        """맞춤형 인사이트 섹션 추가"""
        doc.add_heading('맞춤형 인사이트', level=2)
        
        if insights.get("shop_positioning"):
            doc.add_paragraph(f'Shop 포지셔닝: {insights.get("shop_positioning")}')
            doc.add_paragraph()
        
        strengths = insights.get("strengths", [])
        if strengths:
            doc.add_heading('강점', level=3)
            for strength in strengths:
                doc.add_paragraph(strength, style='List Bullet')
            doc.add_paragraph()
        
        opportunities = insights.get("opportunities", [])
        if opportunities:
            doc.add_heading('기회', level=3)
            for opp in opportunities:
                doc.add_paragraph(opp, style='List Bullet')
            doc.add_paragraph()
        
        recommendations = insights.get("recommendations", [])
        if recommendations:
            doc.add_heading('추천 사항', level=3)
            for rec in recommendations:
                doc.add_paragraph(rec, style='List Bullet')
            doc.add_paragraph()
        
        advantages = insights.get("competitive_advantages", [])
        if advantages:
            doc.add_heading('경쟁 우위', level=3)
            for adv in advantages:
                doc.add_paragraph(adv, style='List Bullet')
            doc.add_paragraph()
    
    def _get_grade(self, score: int) -> str:
        """점수에 따른 등급 반환"""
        if score >= 90:
            return "Excellent"
        elif score >= 70:
            return "Good"
        elif score >= 50:
            return "Fair"
        else:
            return "Poor"
    
    def _generate_report_content(
        self,
        analysis_result: Dict[str, Any],
        product_data: Optional[Dict[str, Any]],
        shop_data: Optional[Dict[str, Any]],
        format: str = "markdown",
        validation_result: Optional[Dict[str, Any]] = None
    ) -> str:
        # #region agent log - H3 가설 검증
        _log_debug("debug-session", "run1", "H3", "report_generator.py:_generate_report_content", "리포트 생성 시작 - 입력 데이터 구조", {
            "has_analysis_result": bool(analysis_result),
            "analysis_result_keys": list(analysis_result.keys()) if analysis_result and isinstance(analysis_result, dict) else None,
            "has_product_analysis": "product_analysis" in analysis_result if analysis_result and isinstance(analysis_result, dict) else False,
            "has_checklist": "checklist" in analysis_result if analysis_result and isinstance(analysis_result, dict) else False,
            "has_product_data": bool(product_data),
            "product_data_keys": list(product_data.keys()) if product_data and isinstance(product_data, dict) else None,
            "product_name_in_data": product_data.get("product_name") if product_data and isinstance(product_data, dict) else None,
            "price_sale_in_data": product_data.get("price", {}).get("sale_price") if product_data and isinstance(product_data, dict) and product_data.get("price") else None
        })
        # #endregion
        """리포트 내용 생성 (Markdown 형식)"""
        lines = []
        
        # 헤더
        lines.append("# Qoo10 Sales Intelligence Agent - 분석 리포트")
        lines.append(f"\n**생성일시:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("\n---\n")
        
        # 데이터 소스 표시 (크롤링 방법 또는 API)
        crawled_with = None
        if product_data and "crawled_with" in product_data:
            crawled_with = product_data["crawled_with"]
        elif shop_data and "crawled_with" in shop_data:
            crawled_with = shop_data["crawled_with"]
        
        if crawled_with:
            if crawled_with == "qoo10_api":
                lines.append(f"**데이터 소스:** Qoo10 공식 API")
            else:
                lines.append(f"**크롤링 방법:** {crawled_with.upper()}")
            lines.append("\n---\n")
        
        # 상품 정보
        if product_data:
            # #region agent log - H3 가설 검증
            _log_debug("debug-session", "run1", "H3", "report_generator.py:_generate_report_content", "상품 정보 리포트에 추가 시작", {
                "product_name": product_data.get('product_name'),
                "price_sale": product_data.get('price', {}).get('sale_price'),
                "price_original": product_data.get('price', {}).get('original_price'),
                "has_qpoint": bool(product_data.get('qpoint_info')),
                "has_coupon": bool(product_data.get('coupon_info', {}).get('has_coupon'))
            })
            # #endregion
            lines.append("## 📦 상품 정보")
            lines.append("")
            lines.append("| 항목 | 내용 |")
            lines.append("|------|------|")
            
            # 상품명 (개선된 추출 로직 반영)
            product_name = product_data.get('product_name', 'N/A')
            if product_name and product_name != '상품명 없음' and product_name != 'N/A':
                lines.append(f"| 상품명 | {product_name} |")
            else:
                lines.append(f"| 상품명 | N/A (추출 실패) |")
            
            lines.append(f"| 상품 코드 | {product_data.get('product_code', 'N/A')} |")
            lines.append(f"| 카테고리 | {product_data.get('category', 'N/A')} |")
            lines.append(f"| 브랜드 | {product_data.get('brand', 'N/A')} |")
            
            # 가격 정보 (유효성 검증된 값만 표시)
            price_data = product_data.get('price', {})
            sale_price = price_data.get('sale_price')
            original_price = price_data.get('original_price')
            
            if sale_price and 100 <= sale_price <= 1000000:  # 유효성 검증
                lines.append(f"| 판매가 | {sale_price:,}円 |")
            else:
                lines.append(f"| 판매가 | N/A |")
            
            if original_price and 100 <= original_price <= 1000000:  # 유효성 검증
                lines.append(f"| 정가 | {original_price:,}円 |")
                if sale_price and original_price > sale_price:
                    discount_rate = int((original_price - sale_price) / original_price * 100)
                    lines.append(f"| 할인율 | {discount_rate}% |")
            
            # Qポイント 정보 (개선된 추출 로직 반영)
            qpoint_info = product_data.get('qpoint_info', {})
            if qpoint_info and any(qpoint_info.values()):
                qpoint_lines = []
                if qpoint_info.get('max_points'):
                    qpoint_lines.append(f"최대 {qpoint_info['max_points']}P")
                if qpoint_info.get('receive_confirmation_points'):
                    qpoint_lines.append(f"수령확인 {qpoint_info['receive_confirmation_points']}P")
                if qpoint_info.get('review_points'):
                    qpoint_lines.append(f"리뷰작성 {qpoint_info['review_points']}P")
                if qpoint_info.get('auto_points'):
                    qpoint_lines.append(f"자동 {qpoint_info['auto_points']}P")
                
                if qpoint_lines:
                    lines.append(f"| Qポイント | {', '.join(qpoint_lines)} |")
                else:
                    lines.append(f"| Qポイント | N/A |")
            else:
                lines.append(f"| Qポイント | N/A |")
            
            # 반품 정보 (개선된 추출 로직 반영)
            shipping_info = product_data.get('shipping_info', {})
            return_policy = shipping_info.get('return_policy')
            if return_policy:
                return_text = "무료반품 가능" if return_policy == "free_return" else "반품 가능"
                lines.append(f"| 반품 정책 | {return_text} |")
            else:
                lines.append(f"| 반품 정책 | N/A |")
            
            # 배송 정보
            if shipping_info.get('free_shipping'):
                lines.append(f"| 배송 | 무료배송 |")
            elif shipping_info.get('shipping_fee'):
                lines.append(f"| 배송비 | {shipping_info['shipping_fee']:,}円 |")
            
            # 쿠폰 정보
            coupon_info = product_data.get('coupon_info', {})
            if coupon_info.get('has_coupon'):
                coupon_type = coupon_info.get('coupon_type', 'auto')
                max_discount = coupon_info.get('max_discount')
                if max_discount:
                    lines.append(f"| 쿠폰 | {coupon_type} (최대 {max_discount}円 할인) |")
                else:
                    lines.append(f"| 쿠폰 | {coupon_type} |")
            
            lines.append("\n")
        
        # Shop 정보
        if shop_data:
            lines.append("## 🏪 Shop 정보")
            lines.append("")
            lines.append("| 항목 | 내용 |")
            lines.append("|------|------|")
            lines.append(f"| Shop 이름 | {shop_data.get('shop_name', 'N/A')} |")
            lines.append(f"| Shop 레벨 | {shop_data.get('shop_level', 'N/A')} |")
            lines.append(f"| 팔로워 수 | {shop_data.get('follower_count', 0):,}명 |")
            lines.append(f"| 상품 수 | {shop_data.get('product_count', 0)}개 |")
            lines.append("\n")
        
        # 상품 분석 결과
        if "product_analysis" in analysis_result:
            product_analysis = analysis_result["product_analysis"]
            lines.append("## 📊 상품 분석 결과")
            lines.append("")
            
            overall_score = product_analysis.get('overall_score', 0)
            grade = self._get_grade(overall_score)
            lines.append(f"### 종합 점수: **{overall_score}/100** ({grade})")
            lines.append("")
            
            # 이미지 분석
            self._add_markdown_analysis_section(lines, "이미지 분석", product_analysis.get("image_analysis", {}))
            
            # 설명 분석
            self._add_markdown_analysis_section(lines, "상품 설명 분석", product_analysis.get("description_analysis", {}))
            
            # 가격 분석
            self._add_markdown_price_analysis(lines, product_analysis.get("price_analysis", {}))
            
            # 리뷰 분석
            self._add_markdown_review_analysis(lines, product_analysis.get("review_analysis", {}))
            
            # SEO 분석
            self._add_markdown_analysis_section(lines, "SEO 분석", product_analysis.get("seo_analysis", {}))
            
            # 페이지 구조 분석
            self._add_markdown_analysis_section(lines, "페이지 구조 분석", product_analysis.get("page_structure_analysis", {}))
        
        # Shop 분석
        if "shop_analysis" in analysis_result:
            shop_analysis = analysis_result["shop_analysis"]
            lines.append("## 🏬 Shop 분석 결과")
            lines.append("")
            
            overall_score = shop_analysis.get('overall_score', 0)
            grade = self._get_grade(overall_score)
            lines.append(f"### 종합 점수: **{overall_score}/100** ({grade})")
            lines.append("")
            
            # Shop 정보 분석
            self._add_markdown_shop_info(lines, shop_analysis)
            
            # Shop 특수성 분석
            if "shop_specialty" in shop_analysis:
                self._add_markdown_shop_specialty(lines, shop_analysis.get("shop_specialty", {}))
            
            # 맞춤형 인사이트
            if "customized_insights" in shop_analysis:
                self._add_markdown_customized_insights(lines, shop_analysis.get("customized_insights", {}))
        
        # AI 인사이트 (Gemini 생성)
        product_analysis = analysis_result.get("product_analysis", {})
        ai_insights = product_analysis.get("ai_insights")
        if ai_insights:
            lines.append("## 🤖 AI 인사이트 (Gemini)")
            lines.append("")
            
            strengths = ai_insights.get("strengths", [])
            if strengths:
                lines.append("### 강점")
                for strength in strengths:
                    lines.append(f"- ✅ {strength}")
                lines.append("")
            
            weaknesses = ai_insights.get("weaknesses", [])
            if weaknesses:
                lines.append("### 개선 필요 사항")
                for weakness in weaknesses:
                    lines.append(f"- ⚠️ {weakness}")
                lines.append("")
            
            action_items = ai_insights.get("action_items", [])
            if action_items:
                lines.append("### 우선순위 액션 아이템")
                for i, item in enumerate(action_items[:5], 1):  # 상위 5개만
                    priority = item.get("priority", "medium").upper()
                    priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "⚪")
                    lines.append(f"{i}. {priority_emoji} **{item.get('title', 'N/A')}**")
                    lines.append(f"   - {item.get('description', 'N/A')}")
                    if item.get("expected_impact"):
                        lines.append(f"   - 예상 효과: {item.get('expected_impact')}")
                    lines.append("")
            
            insights = ai_insights.get("insights")
            if insights:
                lines.append("### 종합 인사이트")
                lines.append(insights)
                lines.append("")
        
        # 추천 아이디어
        recommendations = analysis_result.get("recommendations", [])
        if recommendations:
            lines.append("## 💡 매출 강화 아이디어")
            lines.append("")
            for i, rec in enumerate(recommendations, 1):
                priority = rec.get("priority", "medium").upper()
                priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(priority, "⚪")
                lines.append(f"### {i}. {priority_emoji} [{priority}] {rec.get('title', 'N/A')}")
                lines.append("")
                lines.append(rec.get('description', 'N/A'))
                lines.append("")
                if rec.get("action_items"):
                    lines.append("**실행 방법:**")
                    for item in rec["action_items"]:
                        lines.append(f"- {item}")
                lines.append("")
        
        # 체크리스트
        checklist = analysis_result.get("checklist", {})
        # #region agent log - H5 가설 검증
        _log_debug("debug-session", "run1", "H5", "report_generator.py:_generate_report_content", "체크리스트 데이터 확인", {
            "has_checklist": bool(checklist),
            "checklist_keys": list(checklist.keys()) if checklist and isinstance(checklist, dict) else None,
            "overall_completion": checklist.get('overall_completion') if checklist and isinstance(checklist, dict) else None,
            "checklist_count": len(checklist.get("checklists", [])) if checklist and isinstance(checklist, dict) else 0,
            "first_checklist_category": checklist.get("checklists", [{}])[0].get("category") if checklist and isinstance(checklist, dict) and checklist.get("checklists") else None,
            "first_checklist_items_count": len(checklist.get("checklists", [{}])[0].get("items", [])) if checklist and isinstance(checklist, dict) and checklist.get("checklists") else 0,
            "total_items": sum(len(cl.get("items", [])) for cl in checklist.get("checklists", [])) if checklist and isinstance(checklist, dict) else 0,
            "completed_items": sum(len([item for item in cl.get("items", []) if item.get("status") == "completed"]) for cl in checklist.get("checklists", [])) if checklist and isinstance(checklist, dict) else 0
        })
        # #endregion
        if checklist:
            lines.append("## ✅ 메뉴얼 기반 체크리스트")
            lines.append("")
            overall_completion = checklist.get('overall_completion', 0)
            lines.append(f"### 전체 완성도: **{overall_completion}%**")
            lines.append("")
            # #region agent log - H5 가설 검증
            _log_debug("debug-session", "run1", "H5", "report_generator.py:_generate_report_content", "체크리스트 리포트에 추가 시작", {
                "overall_completion": overall_completion,
                "checklist_categories_count": len(checklist.get("checklists", []))
            })
            # #endregion
            items_added_count = 0
            for cl in checklist.get("checklists", []):
                category = cl.get('category', 'N/A')
                completion_rate = cl.get('completion_rate', 0)
                lines.append(f"#### {category}: {completion_rate}%")
                lines.append("")
                for item in cl.get("items", []):
                    status = "✅" if item.get("status") == "completed" else "⬜"
                    item_title = item.get('title', 'N/A')
                    lines.append(f"- {status} {item_title}")
                    items_added_count += 1
                lines.append("")
            # #region agent log - H5 가설 검증
            _log_debug("debug-session", "run1", "H5", "report_generator.py:_generate_report_content", "체크리스트 리포트에 추가 완료", {
                "items_added_to_report": items_added_count,
                "total_items_in_checklist": sum(len(cl.get("items", [])) for cl in checklist.get("checklists", []))
            })
            # #endregion
        else:
            # #region agent log - H5 가설 검증
            _log_debug("debug-session", "run1", "H5", "report_generator.py:_generate_report_content", "체크리스트 없음 - 리포트에 추가되지 않음", {
                "checklist_in_result": bool(analysis_result.get("checklist"))
            })
            # #endregion
        
        # 경쟁사 분석
        competitor_analysis = analysis_result.get("competitor_analysis", {})
        if competitor_analysis:
            lines.append("## 🏆 경쟁사 비교 분석")
            lines.append("")
            comparison = competitor_analysis.get("comparison", {})
            lines.append(f"### 가격 포지셔닝: {comparison.get('price_position', 'N/A')}")
            lines.append(f"### 평점 포지셔닝: {comparison.get('rating_position', 'N/A')}")
            lines.append(f"### 리뷰 포지셔닝: {comparison.get('review_position', 'N/A')}")
            lines.append("")
            if competitor_analysis.get("differentiation_points"):
                lines.append("### 차별화 포인트:")
                for point in competitor_analysis["differentiation_points"]:
                    lines.append(f"- {point}")
                lines.append("")
        
        # 데이터 검증 결과
        if validation_result:
            lines.append("## 🔍 데이터 검증 결과")
            lines.append("")
            
            validation_score = validation_result.get("validation_score", 0)
            is_valid = validation_result.get("is_valid", False)
            mismatches = validation_result.get("mismatches", [])
            missing_items = validation_result.get("missing_items", [])
            corrected_fields = validation_result.get("corrected_fields", [])
            
            # 검증 점수 및 상태
            status_emoji = "✅" if is_valid else "⚠️"
            status_text = "일치" if is_valid else "불일치"
            lines.append(f"### {status_emoji} 검증 점수: **{validation_score:.1f}%** ({status_text})")
            lines.append("")
            
            # 보정된 필드
            if corrected_fields:
                lines.append(f"**자동 보정된 필드 ({len(corrected_fields)}개):**")
                for field in corrected_fields:
                    lines.append(f"- {field}")
                lines.append("")
            
            # 불일치 항목
            if mismatches:
                lines.append(f"**불일치 항목 ({len(mismatches)}개):**")
                for mismatch in mismatches:
                    field = mismatch.get("field", "N/A")
                    crawler_value = mismatch.get("crawler_value", "N/A")
                    report_value = mismatch.get("report_value", "N/A")
                    severity = mismatch.get("severity", "medium")
                    corrected = mismatch.get("corrected", False)
                    severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
                    corrected_text = " (자동 보정됨)" if corrected else ""
                    lines.append(f"- {severity_emoji} **{field}**: 크롤러={crawler_value}, 리포트={report_value}{corrected_text}")
                lines.append("")
            
            # 누락 항목
            if missing_items:
                lines.append(f"**누락 항목 ({len(missing_items)}개):**")
                for missing in missing_items:
                    field = missing.get("field", "N/A")
                    checklist_item_id = missing.get("checklist_item_id", "N/A")
                    severity = missing.get("severity", "medium")
                    severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
                    lines.append(f"- {severity_emoji} **{field}**: 체크리스트 항목={checklist_item_id}")
                lines.append("")
            
            # 데이터 소스 정보
            data_source = validation_result.get("data_source", "unknown")
            has_api_data = validation_result.get("has_api_data", False)
            if has_api_data:
                lines.append(f"**데이터 소스:** Qoo10 공식 API (우선 사용)")
            else:
                lines.append(f"**데이터 소스:** {data_source}")
            
            # 구조 비교 결과 (API 구조 기반)
            structure_comparison = validation_result.get("structure_comparison")
            if structure_comparison:
                lines.append("")
                lines.append("**API 구조 기반 검증:**")
                if structure_comparison.get("structure_match"):
                    lines.append("- ✅ 데이터 구조가 API 구조와 일치합니다")
                else:
                    missing = structure_comparison.get("missing_fields", [])
                    extra = structure_comparison.get("extra_fields", [])
                    if missing:
                        lines.append(f"- ⚠️ 누락된 필드 ({len(missing)}개): {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}")
                    if extra:
                        lines.append(f"- ℹ️ 추가 필드 ({len(extra)}개): {', '.join(extra[:5])}{'...' if len(extra) > 5 else ''}")
            lines.append("")
            
            # 검증 시간
            timestamp = validation_result.get("timestamp")
            if timestamp:
                lines.append(f"**검증 시간:** {timestamp}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _add_markdown_analysis_section(self, lines: List[str], title: str, analysis: Dict[str, Any]):
        """Markdown 분석 섹션 추가"""
        score = analysis.get('score', 0)
        grade = self._get_grade(score)
        lines.append(f"#### {title}: **{score}/100** ({grade})")
        lines.append("")
        
        if title == "이미지 분석":
            lines.append(f"- 썸네일 품질: {analysis.get('thumbnail_quality', 'N/A')}")
            lines.append(f"- 상세 이미지 개수: {analysis.get('image_count', 0)}개")
        elif title == "상품 설명 분석":
            lines.append(f"- 설명 길이: {analysis.get('description_length', 0)}자")
            lines.append(f"- 구조화 품질: {analysis.get('structure_quality', 'N/A')}")
            keywords = analysis.get('seo_keywords', [])
            if keywords:
                lines.append(f"- SEO 키워드: {', '.join(keywords)}")
        elif title == "SEO 분석":
            lines.append(f"- 키워드 상품명 포함: {'예' if analysis.get('keywords_in_name') else '아니오'}")
            lines.append(f"- 키워드 설명 포함: {'예' if analysis.get('keywords_in_description') else '아니오'}")
            lines.append(f"- 카테고리 설정: {'예' if analysis.get('category_set') else '아니오'}")
            lines.append(f"- 브랜드 설정: {'예' if analysis.get('brand_set') else '아니오'}")
        elif title == "페이지 구조 분석":
            lines.append(f"- 전체 클래스 수: {analysis.get('total_classes', 0)}개")
            grade = analysis.get("grade") or self._get_grade(analysis.get("score", 0))
            lines.append(f"- 등급: **{grade}**")
            key_elements = analysis.get("key_elements_present", {})
            if key_elements:
                lines.append("- 주요 요소 존재 여부:")
                for key, present in key_elements.items():
                    lines.append(f"  - {key}: {'예' if present else '아니오'}")
            eq = analysis.get("element_quality") or {}
            if eq.get("overall_quality_score") is not None:
                lines.append(f"- 요소 품질: {eq.get('overall_quality_score', 0)}/100 (다양성 {eq.get('diversity_score', 0)}, 일관성 {eq.get('consistency_score', 0)})")
            rel = analysis.get("element_relationships") or {}
            if rel.get("relationship_score") is not None:
                lines.append(f"- 요소 간 관계 점수: {rel.get('relationship_score', 0)}/100")
        
        if analysis.get("recommendations"):
            lines.append("**추천 사항:**")
            for rec in analysis["recommendations"]:
                lines.append(f"- {rec}")
        lines.append("")
    
    def _add_markdown_price_analysis(self, lines: List[str], analysis: Dict[str, Any]):
        """Markdown 가격 분석 추가 (개선된 크롤러 데이터 반영)"""
        score = analysis.get('score', 0)
        grade = self._get_grade(score)
        lines.append(f"#### 가격 분석: **{score}/100** ({grade})")
        lines.append("")
        
        # 유효성 검증된 가격만 표시 (100~1,000,000엔 범위)
        sale_price = analysis.get('sale_price')
        original_price = analysis.get('original_price')
        discount_rate = analysis.get('discount_rate', 0) or 0
        
        if sale_price and 100 <= sale_price <= 1000000:
            lines.append(f"- 판매가: {sale_price:,}円")
        else:
            lines.append(f"- 판매가: N/A (유효하지 않은 값)")
        
        if original_price and 100 <= original_price <= 1000000:
            lines.append(f"- 정가: {original_price:,}円")
            if sale_price and original_price > sale_price:
                calculated_discount = int((original_price - sale_price) / original_price * 100)
                lines.append(f"- 할인율: {calculated_discount}%")
        elif discount_rate > 0:
            lines.append(f"- 할인율: {discount_rate}%")
        
        positioning = analysis.get('positioning', '')
        if positioning:
            lines.append(f"- 가격 포지셔닝: {positioning}")
        
        if analysis.get("recommendations"):
            lines.append("**추천 사항:**")
            for rec in analysis["recommendations"]:
                lines.append(f"- {rec}")
        lines.append("")
    
    def _add_markdown_review_analysis(self, lines: List[str], analysis: Dict[str, Any]):
        """Markdown 리뷰 분석 추가 (개선된 크롤러 데이터 반영)"""
        score = analysis.get('score', 0)
        grade = self._get_grade(score)
        lines.append(f"#### 리뷰 분석: **{score}/100** ({grade})")
        lines.append("")
        
        rating = analysis.get('rating', 0) or 0.0
        review_count = analysis.get('review_count', 0) or 0
        # fallback: reviews 배열 길이 사용
        reviews_list = analysis.get('reviews', [])
        if review_count == 0 and len(reviews_list) > 0:
            review_count = len(reviews_list)
        
        negative_ratio = analysis.get('negative_ratio', 0.0) or 0.0
        
        lines.append(f"- 평점: {rating:.1f}/5.0")
        if review_count > 0:
            lines.append(f"- 리뷰 수: {review_count:,}개")
        else:
            lines.append(f"- 리뷰 수: 0개 (또는 추출 실패)")
        
        if len(reviews_list) > 0:
            lines.append(f"- 추출된 리뷰 텍스트: {len(reviews_list)}개")
        
        if negative_ratio > 0:
            lines.append(f"- 부정 리뷰 비율: {negative_ratio:.1%}")
        
        if analysis.get("recommendations"):
            lines.append("**추천 사항:**")
            for rec in analysis["recommendations"]:
                lines.append(f"- {rec}")
        lines.append("")
    
    def _add_markdown_shop_info(self, lines: List[str], shop_analysis: Dict[str, Any]):
        """Markdown Shop 정보 분석 추가"""
        shop_info = shop_analysis.get("shop_info", {})
        if shop_info:
            score = shop_info.get("score", 0)
            grade = self._get_grade(score)
            lines.append(f"#### Shop 정보 분석: **{score}/100** ({grade})")
            lines.append("")
        
        level_analysis = shop_analysis.get("level_analysis", {})
        if level_analysis:
            lines.append("#### Shop 레벨 분석")
            lines.append("")
            lines.append(f"- 현재 레벨: {level_analysis.get('current_level', 'N/A')}")
            lines.append(f"- 정산 리드타임: {level_analysis.get('settlement_leadtime', 15)}일")
            lines.append(f"- 목표 레벨: {level_analysis.get('target_level', 'N/A')}")
            lines.append("")
            
            if level_analysis.get("requirements"):
                lines.append("**요구사항:**")
                for req in level_analysis["requirements"]:
                    lines.append(f"- {req}")
                lines.append("")
            
            if level_analysis.get("recommendations"):
                lines.append("**추천 사항:**")
                for rec in level_analysis["recommendations"]:
                    lines.append(f"- {rec}")
                lines.append("")
    
    def _add_markdown_shop_specialty(self, lines: List[str], specialty: Dict[str, Any]):
        """Markdown Shop 특수성 추가"""
        lines.append("#### Shop 특수성 분석")
        lines.append("")
        lines.append(f"- 브랜드 샵 여부: {'예' if specialty.get('is_brand_shop') else '아니오'}")
        if specialty.get("brand_name"):
            lines.append(f"- 브랜드명: {specialty.get('brand_name')}")
        lines.append(f"- 제품 라인업 특성: {specialty.get('product_lineup_type', 'mixed')}")
        lines.append(f"- 타겟 고객층: {specialty.get('target_customer', 'general').replace('_', ' ')}")
        lines.append("")
        
        unique_features = specialty.get("unique_features", [])
        if unique_features:
            lines.append("**독특한 특징:**")
            for feature in unique_features:
                lines.append(f"- {feature}")
            lines.append("")
        
        score = specialty.get("specialty_score", 0)
        grade = self._get_grade(score)
        lines.append(f"- 특수성 점수: **{score}/100** ({grade})")
        lines.append("")
    
    def _add_markdown_customized_insights(self, lines: List[str], insights: Dict[str, Any]):
        """Markdown 맞춤형 인사이트 추가"""
        lines.append("#### 맞춤형 인사이트")
        lines.append("")
        
        if insights.get("shop_positioning"):
            lines.append(f"**Shop 포지셔닝:** {insights.get('shop_positioning')}")
            lines.append("")
        
        strengths = insights.get("strengths", [])
        if strengths:
            lines.append("**강점:**")
            for strength in strengths:
                lines.append(f"- {strength}")
            lines.append("")
        
        opportunities = insights.get("opportunities", [])
        if opportunities:
            lines.append("**기회:**")
            for opp in opportunities:
                lines.append(f"- {opp}")
            lines.append("")
        
        recommendations = insights.get("recommendations", [])
        if recommendations:
            lines.append("**추천 사항:**")
            for rec in recommendations:
                lines.append(f"- {rec}")
            lines.append("")
        
        advantages = insights.get("competitive_advantages", [])
        if advantages:
            lines.append("**경쟁 우위:**")
            for adv in advantages:
                lines.append(f"- {adv}")
            lines.append("")