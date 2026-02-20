#!/usr/bin/env python3
"""
API 테스트 스크립트
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8080"

def test_health():
    """헬스 체크 테스트"""
    print("=" * 50)
    print("1. 헬스 체크 테스트")
    print("=" * 50)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 헬스 체크 실패: {str(e)}")
        return False

def test_root():
    """루트 엔드포인트 테스트"""
    print("\n" + "=" * 50)
    print("2. 루트 엔드포인트 테스트")
    print("=" * 50)
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 루트 엔드포인트 실패: {str(e)}")
        return False

def test_start_analysis():
    """분석 시작 테스트"""
    print("\n" + "=" * 50)
    print("3. 분석 시작 테스트")
    print("=" * 50)
    
    test_url = "https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=1093098159"
    
    try:
        payload = {
            "url": test_url
        }
        
        print(f"Request URL: {test_url}")
        print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/analyze",
            json=payload,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 분석 시작 성공!")
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            analysis_id = result.get("analysis_id")
            if analysis_id:
                print(f"\n분석 ID: {analysis_id}")
                return analysis_id
            else:
                print("❌ analysis_id가 응답에 없습니다")
                return None
        else:
            print(f"❌ 분석 시작 실패")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 분석 시작 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_get_analysis_result(analysis_id):
    """분석 결과 조회 테스트"""
    print("\n" + "=" * 50)
    print("4. 분석 결과 조회 테스트")
    print("=" * 50)
    
    if not analysis_id:
        print("❌ analysis_id가 없어서 테스트를 건너뜁니다")
        return False
    
    max_attempts = 60  # 최대 60번 시도 (약 5분)
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/analyze/{analysis_id}",
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status", "unknown")
                progress = result.get("progress", {})
                
                print(f"시도 {attempt + 1}/{max_attempts}")
                print(f"Status: {status}")
                print(f"Progress: {json.dumps(progress, indent=2, ensure_ascii=False)}")
                
                if status == "completed":
                    print("✅ 분석 완료!")
                    print(f"Result keys: {list(result.get('result', {}).keys())}")
                    return True
                elif status == "failed":
                    print("❌ 분석 실패")
                    print(f"Error: {result.get('error', 'Unknown error')}")
                    return False
                else:
                    # processing 상태면 계속 대기
                    time.sleep(5)
                    attempt += 1
            else:
                print(f"❌ 결과 조회 실패: Status Code {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 결과 조회 중 오류 발생: {str(e)}")
            return False
    
    print(f"⏱️ 타임아웃: {max_attempts}번 시도 후에도 완료되지 않았습니다")
    return False

def main():
    """메인 테스트 함수"""
    print("🚀 API 테스트 시작\n")
    
    # 1. 헬스 체크
    if not test_health():
        print("\n❌ 헬스 체크 실패. 서버가 실행 중인지 확인하세요.")
        sys.exit(1)
    
    # 2. 루트 엔드포인트
    if not test_root():
        print("\n⚠️ 루트 엔드포인트 테스트 실패 (계속 진행)")
    
    # 3. 분석 시작
    analysis_id = test_start_analysis()
    
    if analysis_id:
        # 4. 분석 결과 조회
        test_get_analysis_result(analysis_id)
    else:
        print("\n❌ 분석 시작 실패로 결과 조회 테스트를 건너뜁니다")
    
    print("\n" + "=" * 50)
    print("✅ 테스트 완료")
    print("=" * 50)

if __name__ == "__main__":
    main()
