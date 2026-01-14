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
    import warnings
    warnings.warn(
        "python-docx is not installed. DOC report generation will not be available.",
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
                
                ws[f'A{row}'] = "상품명"
                ws[f'B{row}'] = product_data.get('product_name', 'N/A')
                row += 1
                ws[f'A{row}'] = "상품 코드"
                ws[f'B{row}'] = product_data.get('product_code', 'N/A')
                row += 1
                ws[f'A{row}'] = "카테고리"
                ws[f'B{row}'] = product_data.get('category', 'N/A')
                row += 1
                ws[f'A{row}'] = "브랜드"
                ws[f'B{row}'] = product_data.get('brand', 'N/A')
                row += 2
            
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
            self._add_info_table(doc, [
                ("상품명", product_data.get('product_name', 'N/A')),
                ("상품 코드", product_data.get('product_code', 'N/A')),
                ("카테고리", product_data.get('category', 'N/A')),
                ("브랜드", product_data.get('brand', 'N/A')),
            ])
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
    
    def _add_info_table(self, doc: Document, data: List[tuple]):
        """정보 테이블 추가"""
        table = doc.add_table(rows=len(data), cols=2)
        table.style = 'Light Grid Accent 1'
        
        for i, (key, value) in enumerate(data):
            table.rows[i].cells[0].text = key
            table.rows[i].cells[1].text = str(value)
            table.rows[i].cells[0].paragraphs[0].runs[0].bold = True
    
    def _add_analysis_section(self, doc: Document, title: str, analysis: Dict[str, Any]):
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
            key_elements = analysis.get("key_elements_present", {})
            if key_elements:
                doc.add_paragraph('주요 요소 존재 여부:')
                for key, present in key_elements.items():
                    doc.add_paragraph(f'  - {key}: {"예" if present else "아니오"}', style='List Bullet 2')
        
        # 추천 사항
        if analysis.get("recommendations"):
            doc.add_paragraph('추천 사항:', style='List Bullet')
            for rec in analysis["recommendations"]:
                doc.add_paragraph(rec, style='List Bullet 2')
        
        doc.add_paragraph()
    
    def _add_price_analysis_section(self, doc: Document, analysis: Dict[str, Any]):
        """가격 분석 섹션 추가"""
        doc.add_heading('가격 분석', level=2)
        
        score = analysis.get('score', 0)
        score_para = doc.add_paragraph()
        score_para.add_run('점수: ').bold = True
        score_para.add_run(f'{score}/100').bold = True
        score_para.add_run(f' ({self._get_grade(score)})')
        
        sale_price = analysis.get('sale_price', 0) or 0
        original_price = analysis.get('original_price', 0) or 0
        discount_rate = analysis.get('discount_rate', 0) or 0
        
        doc.add_paragraph(f'판매가: {sale_price:,}円')
        if original_price > 0:
            doc.add_paragraph(f'정가: {original_price:,}円')
        if discount_rate > 0:
            doc.add_paragraph(f'할인율: {discount_rate}%')
        
        positioning = analysis.get('positioning', '')
        if positioning:
            doc.add_paragraph(f'가격 포지셔닝: {positioning}')
        
        if analysis.get("recommendations"):
            doc.add_paragraph('추천 사항:', style='List Bullet')
            for rec in analysis["recommendations"]:
                doc.add_paragraph(rec, style='List Bullet 2')
        
        doc.add_paragraph()
    
    def _add_review_analysis_section(self, doc: Document, analysis: Dict[str, Any]):
        """리뷰 분석 섹션 추가"""
        doc.add_heading('리뷰 분석', level=2)
        
        score = analysis.get('score', 0)
        score_para = doc.add_paragraph()
        score_para.add_run('점수: ').bold = True
        score_para.add_run(f'{score}/100').bold = True
        score_para.add_run(f' ({self._get_grade(score)})')
        
        rating = analysis.get('rating', 0) or 0.0
        review_count = analysis.get('review_count', 0) or 0
        negative_ratio = analysis.get('negative_ratio', 0.0) or 0.0
        
        doc.add_paragraph(f'평점: {rating:.1f}/5.0')
        doc.add_paragraph(f'리뷰 수: {review_count:,}개')
        if negative_ratio > 0:
            doc.add_paragraph(f'부정 리뷰 비율: {negative_ratio:.1%}')
        
        if analysis.get("recommendations"):
            doc.add_paragraph('추천 사항:', style='List Bullet')
            for rec in analysis["recommendations"]:
                doc.add_paragraph(rec, style='List Bullet 2')
        
        doc.add_paragraph()
    
    def _add_shop_info_section(self, doc: Document, shop_analysis: Dict[str, Any]):
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
    
    def _add_shop_specialty_section(self, doc: Document, specialty: Dict[str, Any]):
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
    
    def _add_customized_insights_section(self, doc: Document, insights: Dict[str, Any]):
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
        format: str = "markdown"
    ) -> str:
        """리포트 내용 생성 (Markdown 형식)"""
        lines = []
        
        # 헤더
        lines.append("# Qoo10 Sales Intelligence Agent - 분석 리포트")
        lines.append(f"\n**생성일시:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("\n---\n")
        
        # 크롤링 방법 표시
        crawled_with = None
        if product_data and "crawled_with" in product_data:
            crawled_with = product_data["crawled_with"]
        elif shop_data and "crawled_with" in shop_data:
            crawled_with = shop_data["crawled_with"]
        
        if crawled_with:
            lines.append(f"**크롤링 방법:** {crawled_with.upper()}")
            lines.append("\n---\n")
        
        # 상품 정보
        if product_data:
            lines.append("## 📦 상품 정보")
            lines.append("")
            lines.append("| 항목 | 내용 |")
            lines.append("|------|------|")
            lines.append(f"| 상품명 | {product_data.get('product_name', 'N/A')} |")
            lines.append(f"| 상품 코드 | {product_data.get('product_code', 'N/A')} |")
            lines.append(f"| 카테고리 | {product_data.get('category', 'N/A')} |")
            lines.append(f"| 브랜드 | {product_data.get('brand', 'N/A')} |")
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
        if checklist:
            lines.append("## ✅ 메뉴얼 기반 체크리스트")
            lines.append("")
            overall_completion = checklist.get('overall_completion', 0)
            lines.append(f"### 전체 완성도: **{overall_completion}%**")
            lines.append("")
            for cl in checklist.get("checklists", []):
                lines.append(f"#### {cl.get('category', 'N/A')}: {cl.get('completion_rate', 0)}%")
                lines.append("")
                for item in cl.get("items", []):
                    status = "✅" if item.get("status") == "completed" else "⬜"
                    lines.append(f"- {status} {item.get('title', 'N/A')}")
                lines.append("")
        
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
            key_elements = analysis.get("key_elements_present", {})
            if key_elements:
                lines.append("- 주요 요소 존재 여부:")
                for key, present in key_elements.items():
                    lines.append(f"  - {key}: {'예' if present else '아니오'}")
        
        if analysis.get("recommendations"):
            lines.append("**추천 사항:**")
            for rec in analysis["recommendations"]:
                lines.append(f"- {rec}")
        lines.append("")
    
    def _add_markdown_price_analysis(self, lines: List[str], analysis: Dict[str, Any]):
        """Markdown 가격 분석 추가"""
        score = analysis.get('score', 0)
        grade = self._get_grade(score)
        lines.append(f"#### 가격 분석: **{score}/100** ({grade})")
        lines.append("")
        
        sale_price = analysis.get('sale_price', 0) or 0
        original_price = analysis.get('original_price', 0) or 0
        discount_rate = analysis.get('discount_rate', 0) or 0
        
        lines.append(f"- 판매가: {sale_price:,}円")
        if original_price > 0:
            lines.append(f"- 정가: {original_price:,}円")
        if discount_rate > 0:
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
        """Markdown 리뷰 분석 추가"""
        score = analysis.get('score', 0)
        grade = self._get_grade(score)
        lines.append(f"#### 리뷰 분석: **{score}/100** ({grade})")
        lines.append("")
        
        rating = analysis.get('rating', 0) or 0.0
        review_count = analysis.get('review_count', 0) or 0
        negative_ratio = analysis.get('negative_ratio', 0.0) or 0.0
        
        lines.append(f"- 평점: {rating:.1f}/5.0")
        lines.append(f"- 리뷰 수: {review_count:,}개")
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