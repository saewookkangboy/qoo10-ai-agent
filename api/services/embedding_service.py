"""
한국어-일본어 임베딩 서비스
Qoo10 사이트의 일본어 데이터와 한국어 리포트 간의 의미적 유사도를 계산하고,
DB에 저장하여 자동 학습 기능을 제공합니다.

추천 모델 (앙상블 모드):
1. BGE-M3 (기본 모델): 가장 정확한 다국어 임베딩, 100개 이상 언어 지원
2. Multilingual-E5-Base (보완 모델): 균형잡힌 성능과 속도
   - 두 모델을 앙상블하여 더 정확한 결과 제공 (가중치: BGE-M3 0.7, E5-Base 0.3)

기타 모델:
3. multilingual-e5-small: 경량 모델 (빠른 속도)
4. paraphrase-multilingual-MiniLM-L12-v2: 경량 모델 (빠른 속도)
"""
import os
import json
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import logging
from functools import lru_cache

# sentence-transformers 임포트
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

# 언어 감지 라이브러리
try:
    import langdetect
    from langdetect import detect, detect_langs
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

logger = logging.getLogger(__name__)


class EmbeddingService:
    """한국어-일본어 임베딩 서비스"""
    
    # 지원 모델 목록 (우선순위 순)
    SUPPORTED_MODELS = {
        "bge-m3": {
            "name": "BAAI/bge-m3",
            "description": "BGE-M3: 가장 정확한 다국어 임베딩 모델 (100+ 언어 지원)",
            "dimension": 1024,
            "max_length": 8192,
            "recommended": True
        },
        "multilingual-e5-base": {
            "name": "intfloat/multilingual-e5-base",
            "description": "Multilingual E5 Base: 균형잡힌 성능과 속도",
            "dimension": 768,
            "max_length": 512,
            "recommended": False
        },
        "multilingual-e5-small": {
            "name": "intfloat/multilingual-e5-small",
            "description": "Multilingual E5 Small: 경량 모델 (빠른 속도)",
            "dimension": 384,
            "max_length": 512,
            "recommended": False
        },
        "paraphrase-multilingual": {
            "name": "paraphrase-multilingual-MiniLM-L12-v2",
            "description": "Paraphrase Multilingual: 경량 모델 (빠른 속도, 적당한 정확도)",
            "dimension": 384,
            "max_length": 128,
            "recommended": False
        }
    }
    
    def __init__(self, model_name: Optional[str] = None, db=None, use_ensemble: bool = True):
        """
        임베딩 서비스 초기화
        
        Args:
            model_name: 사용할 모델 이름 (None이면 환경변수 또는 기본값 사용)
            db: 데이터베이스 인스턴스 (임베딩 저장용)
            use_ensemble: 앙상블 모드 사용 여부 (BGE-M3 + Multilingual-E5-Base)
        """
        self.db = db
        self.use_ensemble = use_ensemble
        
        # 모델 선택
        if model_name is None:
            model_name = os.getenv("EMBEDDING_MODEL", "bge-m3")
        
        if model_name not in self.SUPPORTED_MODELS:
            logger.warning(f"지원하지 않는 모델: {model_name}, 기본 모델(bge-m3) 사용")
            model_name = "bge-m3"
        
        self.model_name = model_name
        self.model_config = self.SUPPORTED_MODELS[model_name]
        self.model = None
        self._model_loaded = False  # 모델 로딩 상태 추적
        
        # 보완 모델 설정 (앙상블 모드)
        self.complementary_model = None
        self.complementary_model_name = None
        self.complementary_model_config = None
        
        # 앙상블 모드 활성화 여부 확인
        if use_ensemble:
            ensemble_enabled = os.getenv("EMBEDDING_ENSEMBLE", "1").lower() in {"1", "true", "yes"}
            if ensemble_enabled and model_name == "bge-m3":
                # BGE-M3를 기본으로 사용하고, Multilingual-E5-Base를 보완 모델로 사용
                self.complementary_model_name = "multilingual-e5-base"
                self.complementary_model_config = self.SUPPORTED_MODELS[self.complementary_model_name]
                self.use_ensemble = True
            else:
                self.use_ensemble = False
        
        # 지연 로딩: 모델은 실제 사용 시점에 로드 (서버 시작 시 블로킹 방지)
        # self._load_model()  # 주석 처리하여 지연 로딩으로 변경
        
        # 언어 감지 초기화
        if LANGDETECT_AVAILABLE:
            try:
                # 언어 감지 설정 (한국어, 일본어 우선)
                langdetect.DetectorFactory.seed = 0
            except Exception as e:
                logger.warning(f"언어 감지 초기화 실패: {e}")
    
    def _ensure_model_loaded(self):
        """모델이 로드되지 않았으면 로드 (지연 로딩, 스레드 안전)"""
        if not self._model_loaded or self.model is None:
            import threading
            if not hasattr(self, '_loading_lock'):
                self._loading_lock = threading.Lock()
            
            # 이미 다른 스레드에서 로딩 중인지 확인
            if hasattr(self, '_loading_in_progress') and self._loading_in_progress:
                # 로딩 완료까지 대기 (최대 60초)
                import time
                wait_count = 0
                while wait_count < 60 and (not self._model_loaded or self.model is None):
                    time.sleep(1)
                    wait_count += 1
                if not self._model_loaded or self.model is None:
                    logger.warning("임베딩 모델 로딩 대기 시간 초과")
                    raise RuntimeError("임베딩 모델 로딩 시간 초과")
                return
            
            with self._loading_lock:
                # 이중 체크 (다른 스레드에서 이미 로딩 중일 수 있음)
                if not self._model_loaded or self.model is None:
                    self._loading_in_progress = True
                    logger.info("임베딩 모델 지연 로딩 시작...")
                    try:
                        self._load_model()
                        self._model_loaded = True
                        logger.info("임베딩 모델 로딩 완료")
                    except Exception as e:
                        logger.error(f"임베딩 모델 로딩 실패: {str(e)}", exc_info=True)
                        self._model_loaded = False
                        raise
                    finally:
                        self._loading_in_progress = False
    
    def _load_model(self):
        """모델 로드 (기본 모델 + 보완 모델)"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("sentence-transformers가 설치되지 않았습니다. 임베딩 기능을 사용할 수 없습니다. (선택적 기능)")
            logger.info("임베딩 기능을 사용하려면: pip install sentence-transformers")
            raise ImportError("sentence-transformers 패키지가 필요합니다")
        
        # 기본 모델 로드
        try:
            logger.info(f"기본 임베딩 모델 로딩 중: {self.model_config['name']}")
            self.model = SentenceTransformer(self.model_config['name'])
            logger.info(f"기본 임베딩 모델 로딩 완료: {self.model_name}")
        except Exception as e:
            logger.error(f"기본 모델 로딩 실패: {e}")
            # 폴백 모델 시도
            if self.model_name != "paraphrase-multilingual":
                logger.info("폴백 모델(paraphrase-multilingual) 시도 중...")
                self.model_name = "paraphrase-multilingual"
                self.model_config = self.SUPPORTED_MODELS[self.model_name]
                self.model = SentenceTransformer(self.model_config['name'])
            else:
                raise
        
        # 보완 모델 로드 (앙상블 모드)
        if self.use_ensemble and self.complementary_model_name:
            try:
                logger.info(f"보완 임베딩 모델 로딩 중: {self.complementary_model_config['name']}")
                self.complementary_model = SentenceTransformer(self.complementary_model_config['name'])
                logger.info(f"보완 임베딩 모델 로딩 완료: {self.complementary_model_name}")
                logger.info(f"앙상블 모드 활성화: {self.model_name} + {self.complementary_model_name}")
            except Exception as e:
                logger.warning(f"보완 모델 로딩 실패: {e}. 기본 모델만 사용합니다.")
                self.use_ensemble = False
                self.complementary_model = None
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        텍스트 언어 감지
        
        Args:
            text: 감지할 텍스트
            
        Returns:
            (언어 코드, 신뢰도) 튜플
        """
        if not LANGDETECT_AVAILABLE:
            # 간단한 휴리스틱으로 언어 감지
            japanese_chars = len([c for c in text if '\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' or '\u4E00' <= c <= '\u9FAF'])
            korean_chars = len([c for c in text if '\uAC00' <= c <= '\uD7A3'])
            
            if japanese_chars > korean_chars * 2:
                return ("ja", 0.8)
            elif korean_chars > japanese_chars * 2:
                return ("ko", 0.8)
            else:
                return ("unknown", 0.5)
        
        try:
            detected_langs = detect_langs(text)
            if detected_langs:
                lang = detected_langs[0]
                return (lang.lang, lang.prob)
            return ("unknown", 0.0)
        except Exception as e:
            logger.warning(f"언어 감지 실패: {e}")
            return ("unknown", 0.0)
    
    def encode(self, texts: List[str], normalize: bool = True, use_ensemble: Optional[bool] = None) -> np.ndarray:
        """
        텍스트 리스트를 임베딩 벡터로 변환
        
        Args:
            texts: 임베딩할 텍스트 리스트
            normalize: L2 정규화 여부 (기본값: True, 코사인 유사도 계산에 유리)
            use_ensemble: 앙상블 사용 여부 (None이면 self.use_ensemble 사용)
            
        Returns:
            임베딩 벡터 배열 (n_samples, dimension)
        """
        self._ensure_model_loaded()  # 지연 로딩
        if self.model is None:
            raise RuntimeError("모델이 로드되지 않았습니다")
        
        use_ensemble = use_ensemble if use_ensemble is not None else self.use_ensemble
        
        try:
            # 기본 모델로 임베딩 생성
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=normalize,
                show_progress_bar=False,
                batch_size=32
            )
            
            # 앙상블 모드: 보완 모델 결과와 결합
            if use_ensemble and self.complementary_model is not None:
                try:
                    # 보완 모델로 임베딩 생성
                    complementary_embeddings = self.complementary_model.encode(
                        texts,
                        normalize_embeddings=normalize,
                        show_progress_bar=False,
                        batch_size=32
                    )
                    
                    # 두 임베딩을 결합 (가중 평균)
                    # BGE-M3 가중치: 0.7, Multilingual-E5-Base 가중치: 0.3
                    weight_primary = 0.7
                    weight_complementary = 0.3
                    
                    # 차원이 다른 경우 보완 모델 임베딩을 기본 모델 차원에 맞게 조정
                    if embeddings.shape[1] != complementary_embeddings.shape[1]:
                        comp_dim = complementary_embeddings.shape[1]
                        primary_dim = embeddings.shape[1]
                        
                        if comp_dim < primary_dim:
                            # 보완 임베딩을 반복하여 확장 (간단한 방법)
                            repeat_factor = primary_dim // comp_dim
                            remainder = primary_dim % comp_dim
                            expanded = np.tile(complementary_embeddings, (1, repeat_factor))
                            if remainder > 0:
                                expanded = np.concatenate([
                                    expanded,
                                    complementary_embeddings[:, :remainder]
                                ], axis=1)
                            complementary_embeddings = expanded
                        else:
                            # 보완 임베딩을 평균하여 축소
                            reduce_factor = comp_dim // primary_dim
                            reduced = []
                            for i in range(primary_dim):
                                start_idx = i * reduce_factor
                                end_idx = start_idx + reduce_factor
                                if end_idx <= comp_dim:
                                    reduced.append(np.mean(complementary_embeddings[:, start_idx:end_idx], axis=1))
                                else:
                                    reduced.append(np.mean(complementary_embeddings[:, start_idx:], axis=1))
                            complementary_embeddings = np.column_stack(reduced)
                    
                    # 가중 평균으로 결합
                    embeddings = weight_primary * embeddings + weight_complementary * complementary_embeddings
                    
                    # 재정규화 (L2 정규화)
                    if normalize:
                        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                        norms = np.where(norms == 0, 1, norms)  # 0으로 나누기 방지
                        embeddings = embeddings / norms
                    
                except Exception as e:
                    logger.warning(f"보완 모델 임베딩 생성 실패: {e}. 기본 모델만 사용합니다.")
            
            return embeddings
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            raise
    
    def compute_similarity(self, text1: str, text2: str, use_ensemble: Optional[bool] = None) -> float:
        """
        두 텍스트 간의 코사인 유사도 계산 (앙상블 모드 지원)
        
        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트
            use_ensemble: 앙상블 사용 여부 (None이면 self.use_ensemble 사용)
            
        Returns:
            코사인 유사도 (0.0 ~ 1.0)
        """
        use_ensemble = use_ensemble if use_ensemble is not None else self.use_ensemble
        embeddings = self.encode([text1, text2], normalize=True, use_ensemble=use_ensemble)
        similarity = np.dot(embeddings[0], embeddings[1])
        return float(similarity)
    
    def find_similar_texts(
        self,
        query_text: str,
        candidate_texts: List[str],
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[Tuple[str, float, int]]:
        """
        쿼리 텍스트와 가장 유사한 텍스트들을 찾음
        
        Args:
            query_text: 검색할 텍스트
            candidate_texts: 후보 텍스트 리스트
            top_k: 반환할 상위 k개
            threshold: 최소 유사도 임계값
            
        Returns:
            [(텍스트, 유사도, 인덱스), ...] 리스트 (유사도 내림차순)
        """
        if not candidate_texts:
            return []
        
        # 쿼리와 후보들을 모두 임베딩
        all_texts = [query_text] + candidate_texts
        embeddings = self.encode(all_texts, normalize=True)
        
        query_embedding = embeddings[0]
        candidate_embeddings = embeddings[1:]
        
        # 코사인 유사도 계산
        similarities = np.dot(candidate_embeddings, query_embedding)
        
        # 상위 k개 선택
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            similarity = float(similarities[idx])
            if similarity >= threshold:
                results.append((candidate_texts[idx], similarity, int(idx)))
        
        return results
    
    def save_embedding(
        self,
        text: str,
        text_type: str,
        source_lang: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        임베딩을 데이터베이스에 저장
        
        Args:
            text: 원본 텍스트
            text_type: 텍스트 타입 (예: "product_name", "description", "review")
            source_lang: 원본 언어 (None이면 자동 감지)
            metadata: 추가 메타데이터
            
        Returns:
            저장된 임베딩 ID (실패 시 None)
        """
        if self.db is None:
            logger.warning("데이터베이스가 설정되지 않아 임베딩을 저장할 수 없습니다")
            return None
        
        try:
            # 언어 감지
            if source_lang is None:
                source_lang, confidence = self.detect_language(text)
            else:
                _, confidence = self.detect_language(text)
            
            # 임베딩 생성
            embedding = self.encode([text], normalize=True)[0]
            embedding_json = json.dumps(embedding.tolist())
            
            # 메타데이터 준비
            metadata_json = json.dumps(metadata or {})
            
            # 데이터베이스에 저장
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db.use_postgres:
                    cursor.execute("""
                        INSERT INTO text_embeddings (
                            text, text_type, source_lang, lang_confidence,
                            embedding, embedding_dimension, model_name, metadata,
                            created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        text,
                        text_type,
                        source_lang,
                        confidence,
                        embedding_json,
                        self.model_config['dimension'],
                        self.model_name,
                        metadata_json,
                        datetime.now(),
                        datetime.now()
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO text_embeddings (
                            text, text_type, source_lang, lang_confidence,
                            embedding, embedding_dimension, model_name, metadata,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        text,
                        text_type,
                        source_lang,
                        confidence,
                        embedding_json,
                        self.model_config['dimension'],
                        self.model_name,
                        metadata_json,
                        datetime.now(),
                        datetime.now()
                    ))
                    cursor.execute("SELECT last_insert_rowid()")
                
                result = cursor.fetchone()
                embedding_id = result[0] if result else None
                conn.commit()
                
                logger.info(f"임베딩 저장 완료: ID={embedding_id}, type={text_type}, lang={source_lang}")
                return embedding_id
                
        except Exception as e:
            logger.error(f"임베딩 저장 실패: {e}", exc_info=True)
            return None
    
    def find_similar_in_db(
        self,
        query_text: str,
        text_type: Optional[str] = None,
        source_lang: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        데이터베이스에서 유사한 텍스트 검색
        
        Args:
            query_text: 검색할 텍스트
            text_type: 필터링할 텍스트 타입 (None이면 모든 타입)
            source_lang: 필터링할 언어 (None이면 모든 언어)
            top_k: 반환할 상위 k개
            threshold: 최소 유사도 임계값
            
        Returns:
            검색 결과 리스트
        """
        if self.db is None:
            logger.warning("데이터베이스가 설정되지 않아 검색할 수 없습니다")
            return []
        
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.encode([query_text], normalize=True)[0]
            query_embedding_json = json.dumps(query_embedding.tolist())
            
            # 데이터베이스에서 검색
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 필터 조건 구성
                filters = []
                params = [query_embedding_json, threshold]
                
                if text_type:
                    filters.append("text_type = ?" if not self.db.use_postgres else "text_type = %s")
                    params.append(text_type)
                
                if source_lang:
                    filters.append("source_lang = ?" if not self.db.use_postgres else "source_lang = %s")
                    params.append(source_lang)
                
                filter_clause = " AND " + " AND ".join(filters) if filters else ""
                
                # PostgreSQL의 경우 벡터 유사도 검색 사용
                if self.db.use_postgres:
                    # pgvector 확장이 있다면 사용, 없으면 코사인 유사도 직접 계산
                    sql = f"""
                        SELECT id, text, text_type, source_lang, embedding, metadata,
                            1 - (embedding::vector <=> %s::vector) as similarity
                        FROM text_embeddings
                        WHERE 1=1 {filter_clause}
                        ORDER BY similarity DESC
                        LIMIT %s
                    """
                    params = [query_embedding_json] + params[1:] + [top_k]
                else:
                    # SQLite의 경우 JSON으로 저장된 벡터를 파싱하여 계산
                    # 간단한 구현: 모든 임베딩을 로드하여 메모리에서 계산
                    sql = f"""
                        SELECT id, text, text_type, source_lang, embedding, metadata
                        FROM text_embeddings
                        WHERE 1=1 {filter_clause}
                    """
                
                cursor.execute(sql, params if self.db.use_postgres else params[1:])
                rows = cursor.fetchall()
                
                # SQLite의 경우 메모리에서 유사도 계산
                if not self.db.use_postgres:
                    results = []
                    for row in rows:
                        stored_embedding = np.array(json.loads(row[4]))
                        similarity = float(np.dot(query_embedding, stored_embedding))
                        if similarity >= threshold:
                            results.append({
                                'id': row[0],
                                'text': row[1],
                                'text_type': row[2],
                                'source_lang': row[3],
                                'similarity': similarity,
                                'metadata': json.loads(row[5]) if row[5] else {}
                            })
                    results.sort(key=lambda x: x['similarity'], reverse=True)
                    return results[:top_k]
                else:
                    # PostgreSQL 결과 처리
                    results = []
                    for row in rows:
                        results.append({
                            'id': row[0],
                            'text': row[1],
                            'text_type': row[2],
                            'source_lang': row[3],
                            'similarity': float(row[6]),
                            'metadata': json.loads(row[5]) if row[5] else {}
                        })
                    return results
                    
        except Exception as e:
            logger.error(f"데이터베이스 검색 실패: {e}", exc_info=True)
            return []
    
    def match_jp_kr_texts(
        self,
        japanese_texts: List[str],
        korean_texts: List[str],
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        일본어 텍스트와 한국어 텍스트 간의 매칭
        
        Args:
            japanese_texts: 일본어 텍스트 리스트
            korean_texts: 한국어 텍스트 리스트
            threshold: 최소 유사도 임계값
            
        Returns:
            매칭 결과 리스트 [{"jp_text": "...", "kr_text": "...", "similarity": 0.95, "jp_idx": 0, "kr_idx": 1}, ...]
        """
        if not japanese_texts or not korean_texts:
            return []
        
        # 모든 텍스트 임베딩
        all_texts = japanese_texts + korean_texts
        embeddings = self.encode(all_texts, normalize=True)
        
        jp_embeddings = embeddings[:len(japanese_texts)]
        kr_embeddings = embeddings[len(japanese_texts):]
        
        # 유사도 매트릭스 계산
        similarity_matrix = np.dot(jp_embeddings, kr_embeddings.T)
        
        # 매칭 결과 생성
        matches = []
        used_kr_indices = set()
        
        # 각 일본어 텍스트에 대해 가장 유사한 한국어 텍스트 찾기
        for jp_idx, jp_text in enumerate(japanese_texts):
            best_kr_idx = np.argmax(similarity_matrix[jp_idx])
            similarity = float(similarity_matrix[jp_idx][best_kr_idx])
            
            if similarity >= threshold and best_kr_idx not in used_kr_indices:
                matches.append({
                    "jp_text": jp_text,
                    "kr_text": korean_texts[best_kr_idx],
                    "similarity": similarity,
                    "jp_idx": jp_idx,
                    "kr_idx": int(best_kr_idx)
                })
                used_kr_indices.add(best_kr_idx)
        
        # 유사도 내림차순 정렬
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches
    
    def get_model_info(self) -> Dict[str, Any]:
        """현재 사용 중인 모델 정보 반환"""
        info = {
            "model_name": self.model_name,
            "model_config": self.model_config,
            "is_loaded": self.model is not None,
            "use_ensemble": self.use_ensemble
        }
        
        if self.use_ensemble and self.complementary_model is not None:
            info["complementary_model_name"] = self.complementary_model_name
            info["complementary_model_config"] = self.complementary_model_config
            info["complementary_model_loaded"] = True
        else:
            info["complementary_model_loaded"] = False
        
        return info
