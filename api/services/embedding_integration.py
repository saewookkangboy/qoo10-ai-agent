"""
임베딩 서비스 통합 모듈
크롤러와 리포트 생성기에 임베딩 기능을 통합하여
한국어-일본어 텍스트 매칭 및 자동 학습 기능을 제공합니다.
"""
import logging
from typing import Dict, List, Optional, Any
from .embedding_service import EmbeddingService
from .database import CrawlerDatabase

logger = logging.getLogger(__name__)


class EmbeddingIntegration:
    """임베딩 통합 클래스"""
    
    def __init__(self, db: Optional[CrawlerDatabase] = None, embedding_service: Optional[EmbeddingService] = None):
        """
        임베딩 통합 초기화
        
        Args:
            db: 데이터베이스 인스턴스
            embedding_service: 임베딩 서비스 인스턴스 (None이면 자동 생성)
        """
        self.db = db or CrawlerDatabase()
        try:
            self.embedding_service = embedding_service or EmbeddingService(db=self.db)
            self.embedding_available = True
        except ImportError:
            # sentence-transformers가 설치되지 않은 경우
            self.embedding_service = None
            self.embedding_available = False
            logger.debug("임베딩 서비스를 사용할 수 없습니다 (sentence-transformers 미설치). 크롤링은 계속 진행됩니다.")
    
    def save_crawled_texts(
        self,
        product_data: Dict[str, Any],
        url: str,
        auto_learn: bool = True
    ) -> Dict[str, Any]:
        """
        크롤링된 텍스트 데이터를 임베딩하여 저장
        
        Args:
            product_data: 크롤링된 상품 데이터
            url: 크롤링한 URL
            auto_learn: 자동 학습 활성화 여부
            
        Returns:
            저장된 임베딩 정보
        """
        saved_embeddings = {}
        
        if not auto_learn:
            return saved_embeddings
        
        # 임베딩 서비스가 사용 불가능한 경우 조용히 반환
        if not self.embedding_available or not self.embedding_service:
            return saved_embeddings
        
        # 임베딩 저장 (타임아웃 보호)
        try:
            import signal
            
            # 타임아웃 핸들러 (Unix 시스템에서만 작동)
            def timeout_handler(signum, frame):
                raise TimeoutError("임베딩 저장 타임아웃")
            
            # 타임아웃 설정 (30초)
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(30)
            except (AttributeError, ValueError):
                # Windows에서는 signal.alarm이 없으므로 타임아웃 없이 진행
                pass
            
            try:
                saved_embeddings = self._save_embeddings_sync(product_data, url)
            finally:
                try:
                    signal.alarm(0)  # 타임아웃 취소
                except (AttributeError, ValueError):
                    pass
                    
        except TimeoutError:
            logger.warning("임베딩 저장 타임아웃 (30초), 건너뜁니다")
            return {}
        except Exception as e:
            logger.warning(f"임베딩 저장 실패 (계속 진행): {str(e)}")
            return {}
        
        return saved_embeddings
    
    def _save_embeddings_sync(self, product_data: Dict[str, Any], url: str) -> Dict[str, Any]:
        """동기 방식으로 임베딩 저장"""
        saved_embeddings = {}
        
        try:
            # 상품명 저장
            if product_data.get("product_name"):
                embedding_id = self.embedding_service.save_embedding(
                    text=product_data["product_name"],
                    text_type="product_name",
                    metadata={
                        "url": url,
                        "product_code": product_data.get("product_code"),
                        "source": "crawler"
                    }
                )
                if embedding_id:
                    saved_embeddings["product_name"] = embedding_id
            
            # 상품 설명 저장
            if product_data.get("description"):
                embedding_id = self.embedding_service.save_embedding(
                    text=product_data["description"],
                    text_type="description",
                    metadata={
                        "url": url,
                        "product_code": product_data.get("product_code"),
                        "source": "crawler"
                    }
                )
                if embedding_id:
                    saved_embeddings["description"] = embedding_id
            
            # 검색 키워드 저장
            if product_data.get("search_keywords"):
                keywords_text = ", ".join(product_data["search_keywords"]) if isinstance(product_data["search_keywords"], list) else str(product_data["search_keywords"])
                if keywords_text:
                    embedding_id = self.embedding_service.save_embedding(
                        text=keywords_text,
                        text_type="search_keywords",
                        metadata={
                            "url": url,
                            "product_code": product_data.get("product_code"),
                            "source": "crawler"
                        }
                    )
                    if embedding_id:
                        saved_embeddings["search_keywords"] = embedding_id
            
            # 카테고리 저장
            if product_data.get("category"):
                embedding_id = self.embedding_service.save_embedding(
                    text=product_data["category"],
                    text_type="category",
                    metadata={
                        "url": url,
                        "product_code": product_data.get("product_code"),
                        "source": "crawler"
                    }
                )
                if embedding_id:
                    saved_embeddings["category"] = embedding_id
            
            # 브랜드 저장
            if product_data.get("brand"):
                embedding_id = self.embedding_service.save_embedding(
                    text=product_data["brand"],
                    text_type="brand",
                    metadata={
                        "url": url,
                        "product_code": product_data.get("product_code"),
                        "source": "crawler"
                    }
                )
                if embedding_id:
                    saved_embeddings["brand"] = embedding_id
            
            logger.info(f"임베딩 저장 완료: {len(saved_embeddings)}개 필드, URL={url}")
            
        except Exception as e:
            logger.error(f"임베딩 저장 실패: {e}", exc_info=True)
        
        return saved_embeddings
    
    def match_japanese_to_korean(
        self,
        japanese_text: str,
        text_type: Optional[str] = None,
        threshold: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        """
        일본어 텍스트와 가장 유사한 한국어 텍스트를 찾음
        
        Args:
            japanese_text: 일본어 텍스트
            text_type: 텍스트 타입 필터 (None이면 모든 타입)
            threshold: 최소 유사도 임계값
            
        Returns:
            매칭된 한국어 텍스트 정보 또는 None
        """
        if not self.embedding_available or not self.embedding_service:
            return None
        
        try:
            # 한국어 텍스트만 검색
            results = self.embedding_service.find_similar_in_db(
                query_text=japanese_text,
                text_type=text_type,
                source_lang="ko",
                top_k=1,
                threshold=threshold
            )
            
            if results:
                return results[0]
            return None
            
        except Exception as e:
            logger.error(f"일본어-한국어 매칭 실패: {e}", exc_info=True)
            return None
    
    def validate_translation(
        self,
        japanese_text: str,
        korean_text: str,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        일본어 텍스트와 한국어 텍스트 간의 번역 정확도 검증
        
        Args:
            japanese_text: 일본어 원문
            korean_text: 한국어 번역문
            threshold: 최소 유사도 임계값
            
        Returns:
            검증 결과 {"is_valid": bool, "similarity": float, "message": str}
        """
        if not self.embedding_available or not self.embedding_service:
            return {
                "is_valid": False,
                "similarity": 0.0,
                "message": "임베딩 서비스를 사용할 수 없습니다"
            }
        
        try:
            similarity = self.embedding_service.compute_similarity(
                japanese_text,
                korean_text
            )
            
            is_valid = similarity >= threshold
            
            return {
                "is_valid": is_valid,
                "similarity": similarity,
                "message": f"유사도: {similarity:.3f} ({'통과' if is_valid else '실패'})"
            }
            
        except Exception as e:
            logger.error(f"번역 검증 실패: {e}", exc_info=True)
            return {
                "is_valid": False,
                "similarity": 0.0,
                "message": f"검증 실패: {str(e)}"
            }
    
    def suggest_korean_translation(
        self,
        japanese_text: str,
        text_type: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        일본어 텍스트에 대한 한국어 번역 제안
        
        Args:
            japanese_text: 일본어 텍스트
            text_type: 텍스트 타입 필터
            top_k: 반환할 상위 k개 제안
            
        Returns:
            번역 제안 리스트
        """
        if not self.embedding_available or not self.embedding_service:
            return []
        
        try:
            results = self.embedding_service.find_similar_in_db(
                query_text=japanese_text,
                text_type=text_type,
                source_lang="ko",
                top_k=top_k,
                threshold=0.5
            )
            
            suggestions = []
            for result in results:
                suggestions.append({
                    "korean_text": result["text"],
                    "similarity": result["similarity"],
                    "text_type": result.get("text_type"),
                    "metadata": result.get("metadata", {})
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"번역 제안 실패: {e}", exc_info=True)
            return []
    
    def improve_data_accuracy(
        self,
        crawled_data: Dict[str, Any],
        report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        크롤링 데이터와 리포트 데이터 간의 정확도 개선
        
        Args:
            crawled_data: 크롤링된 원본 데이터 (일본어)
            report_data: 리포트에 사용된 데이터 (한국어)
            
        Returns:
            개선 제안 및 검증 결과
        """
        improvements = {}
        
        try:
            # 각 필드에 대해 검증 및 개선 제안
            fields_to_check = ["product_name", "description", "category", "brand"]
            
            for field in fields_to_check:
                jp_text = crawled_data.get(field)
                kr_text = report_data.get(field)
                
                if not jp_text or not kr_text:
                    continue
                
                # 번역 검증
                validation = self.validate_translation(jp_text, kr_text)
                
                if not validation["is_valid"]:
                    # 개선 제안
                    suggestions = self.suggest_korean_translation(jp_text, text_type=field)
                    
                    improvements[field] = {
                        "validation": validation,
                        "suggestions": suggestions,
                        "needs_improvement": True
                    }
                else:
                    improvements[field] = {
                        "validation": validation,
                        "needs_improvement": False
                    }
            
        except Exception as e:
            logger.error(f"데이터 정확도 개선 실패: {e}", exc_info=True)
        
        return improvements
