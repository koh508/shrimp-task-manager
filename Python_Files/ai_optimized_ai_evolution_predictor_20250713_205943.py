# 성능 팁: list comprehension 사용 고려

#!/usr/bin/env python3
"""
🔮 AI 진화 예측 시스템
머신러닝을 통해 AI의 미래 진화 방향을 예측하고 최적화 경로를 제안
"""

import numpy as np
import pandas as pd
import sqlite3
import json
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

class AIEvolutionPredictor:
    """AI 진화 예측 시스템"""
    
    def __init__(self):
        self.db_connection = sqlite3.connect('self_evolution.db')
        self.scaler = StandardScaler()
        self.model = None
        self.prediction_accuracy = 0.0
        
        # 예측 모델들
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boost': GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        
        self.feature_importance = {}
        
    def load_historical_data(self):
        """역사적 진화 데이터 로드"""
        try:
            query = '''
            SELECT generation, intelligence_level, performance_gain, 
                   timestamp, code_analysis, improvement_suggestion
            FROM evolution_log 
            ORDER BY timestamp
            '''
            
            df = pd.read_sql_query(query, self.db_connection)
            
            if len(df) < 5:
                print("⚠️ 학습에 충분한 데이터가 없습니다 (최소 5개 필요)")
                return None
            
            # 특성 엔지니어링
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
            
            # 이동 평균 계산
            df['intelligence_ma3'] = df['intelligence_level'].rolling(window=3, min_periods=1).mean()
            df['performance_ma3'] = df['performance_gain'].rolling(window=3, min_periods=1).mean()
            
            # 성장률 계산
            df['intelligence_growth_rate'] = df['intelligence_level'].pct_change().fillna(0)
            df['performance_volatility'] = df['performance_gain'].rolling(window=3, min_periods=1).std().fillna(0)
            
            # 텍스트 특성 추출
            df['code_analysis_length'] = df['code_analysis'].fillna('').str.len()
            df['improvement_length'] = df['improvement_suggestion'].fillna('').str.len()
            
            return df
            
        except Exception as e:
            print(f"데이터 로드 오류: {e}")
            return None
    
    def prepare_features(self, df):
        """예측을 위한 특성 준비"""
        try:
            # 예측할 타겟 변수
            target_cols = ['intelligence_level', 'performance_gain']
            
            # 입력 특성
            feature_cols = [
                'generation', 'intelligence_ma3', 'performance_ma3',
                'intelligence_growth_rate', 'performance_volatility',
                'hour', 'day_of_week', 'code_analysis_length', 'improvement_length'
            ]
            
            # 결측값 처리
            for col in feature_cols:
                if col in df.columns:
                    df[col] = df[col].fillna(df[col].median())
            
            X = df[feature_cols].values
            y = df[target_cols].values
            
            return X, y, feature_cols, target_cols
            
        except Exception as e:
            print(f"특성 준비 오류: {e}")
            return None, None, None, None
    
    def train_prediction_models(self):
        """예측 모델 학습"""
        try:
            print("🧠 AI 진화 예측 모델 학습 시작...")
            
            # 데이터 로드
            df = self.load_historical_data()
            if df is None:
                return False
            
            # 특성 준비
            X, y, feature_cols, target_cols = self.prepare_features(df)
            if X is None:
                return False
            
            print(f"📊 학습 데이터: {X.shape[0]}개 샘플, {X.shape[1]}개 특성")
            
            # 데이터 분할
            if len(X) > 10:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
            else:
                X_train, X_test, y_train, y_test = X, X, y, y
            
            # 스케일링
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # 모델 학습 및 평가
            best_model = None
            best_score = -float('inf')
            
            for model_name, model in self.models.items():
                try:
                    # 지능 레벨 예측 학습
                    model.fit(X_train_scaled, y_train[:, 0])  # intelligence_level
                    
                    # 예측 및 평가
                    y_pred = model.predict(X_test_scaled)
                    r2 = r2_score(y_test[:, 0], y_pred)
                    
                    print(f"🎯 {model_name} 예측 정확도: {r2:.3f}")
                    
                    if r2 > best_score:
                        best_score = r2
                        best_model = model
                        self.model = model
                        self.prediction_accuracy = r2
                        
                        # 특성 중요도 저장
                        if hasattr(model, 'feature_importances_'):
                            self.feature_importance = dict(zip(
                                feature_cols, model.feature_importances_
                            ))
                    
                except Exception as e:
                    print(f"모델 {model_name} 학습 오류: {e}")
                    continue
            
            if best_model is not None:
                print(f"✅ 최적 모델 선택 완료 - 정확도: {self.prediction_accuracy:.3f}")
                return True
            else:
                print("❌ 모델 학습 실패")
                return False
                
        except Exception as e:
            print(f"모델 학습 오류: {e}")
            return False
    
    def predict_future_evolution(self, steps=10):
        """미래 진화 예측"""
        try:
            if self.model is None:
                print("⚠️ 예측 모델이 학습되지 않았습니다")
                return None
            
            print(f"🔮 {steps}세대 미래 진화 예측 중...")
            
            # 최신 데이터 가져오기
            df = self.load_historical_data()
            if df is None or len(df) == 0:
                return None
            
            # 최신 상태
            latest = df.iloc[-1]
            current_generation = int(latest['generation'])
            current_intelligence = latest['intelligence_level']
            
            predictions = []
            
            # 단계별 예측
            for step in range(1, steps + 1):
                try:
                    # 예측용 특성 생성
                    pred_generation = current_generation + step
                    
                    # 최근 3개 세대의 평균값 사용
                    recent_intelligence = df['intelligence_level'].tail(3).mean()
                    recent_performance = df['performance_gain'].tail(3).mean()
                    
                    # 성장률 계산
                    growth_rate = df['intelligence_growth_rate'].tail(3).mean()
                    volatility = df['performance_volatility'].tail(3).mean()
                    
                    # 시간 특성 (현재 시간 기준)
                    current_time = datetime.now()
                    hour = current_time.hour
                    day_of_week = current_time.weekday()
                    
                    # 텍스트 길이 (최근 평균)
                    code_length = df['code_analysis_length'].tail(3).mean()
                    improvement_length = df['improvement_length'].tail(3).mean()
                    
                    # 예측 특성 벡터
                    features = np.array([[
                        pred_generation, recent_intelligence, recent_performance,
                        growth_rate, volatility, hour, day_of_week,
                        code_length, improvement_length
                    ]])
                    
                    # 스케일링
                    features_scaled = self.scaler.transform(features)
                    
                    # 예측
                    predicted_intelligence = self.model.predict(features_scaled)[0]
                    
                    # 성능 향상 예측 (간단한 휴리스틱)
                    performance_gain = max(1.0, predicted_intelligence - current_intelligence)
                    
                    predictions.append({
                        'generation': pred_generation,
                        'predicted_intelligence': predicted_intelligence,
                        'predicted_performance_gain': performance_gain,
                        'confidence': min(100, self.prediction_accuracy * 100)
                    })
                    
                    # 다음 예측을 위해 현재 값 업데이트
                    current_intelligence = predicted_intelligence
                    
                except Exception as e:
                    print(f"예측 단계 {step} 오류: {e}")
                    continue
            
            return predictions
            
        except Exception as e:
            print(f"미래 예측 오류: {e}")
            return None
    
    def analyze_evolution_patterns(self):
        """진화 패턴 분석"""
        try:
            df = self.load_historical_data()
            if df is None or len(df) < 3:
                return None
            
            analysis = {
                'total_generations': len(df),
                'avg_intelligence_growth': df['intelligence_level'].diff().mean(),
                'avg_performance_gain': df['performance_gain'].mean(),
                'intelligence_trend': 'increasing' if df['intelligence_level'].corr(df['generation']) > 0 else 'decreasing',
                'performance_volatility': df['performance_gain'].std(),
                'best_performing_hour': df.groupby('hour')['performance_gain'].mean().idxmax(),
                'evolution_acceleration': df['intelligence_level'].diff().diff().mean()
            }
            
            # 특성 중요도 추가
            if self.feature_importance:
                analysis['key_factors'] = sorted(
                    self.feature_importance.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:5]
            
            return analysis
            
        except Exception as e:
            print(f"패턴 분석 오류: {e}")
            return None
    
    def suggest_optimization_strategy(self):
        """최적화 전략 제안"""
        try:
            patterns = self.analyze_evolution_patterns()
            predictions = self.predict_future_evolution(5)
            
            if not patterns or not predictions:
                return None
            
            suggestions = []
            
            # 성능 기반 제안
            if patterns['avg_performance_gain'] < 10:
                suggestions.append({
                    'category': 'performance',
                    'priority': 'high',
                    'suggestion': '창의성 엔진 강화 - 더 다양한 테마와 접근법 필요',
                    'expected_improvement': '15-25% 성능 향상 예상'
                })
            
            # 시간 기반 제안
            best_hour = patterns.get('best_performing_hour', 12)
            suggestions.append({
                'category': 'timing',
                'priority': 'medium',
                'suggestion': f'{best_hour}시경이 최적 진화 시간대입니다',
                'expected_improvement': '5-10% 성능 향상 예상'
            })
            
            # 진화 가속도 기반 제안
            if patterns['evolution_acceleration'] < 0:
                suggestions.append({
                    'category': 'acceleration',
                    'priority': 'high',
                    'suggestion': '진화 속도 저하 감지 - 새로운 학습 알고리즘 도입 필요',
                    'expected_improvement': '진화 속도 20-30% 증가 예상'
                })
            
            # 미래 예측 기반 제안
            future_intelligence = predictions[-1]['predicted_intelligence']
            current_intelligence = patterns.get('avg_intelligence_growth', 500) * patterns['total_generations']
            
            if future_intelligence < current_intelligence * 1.1:
                suggestions.append({
                    'category': 'growth',
                    'priority': 'medium',
                    'suggestion': '성장 한계 도달 예상 - 새로운 진화 메커니즘 필요',
                    'expected_improvement': '새로운 성장 곡선 시작 가능'
                })
            
            return {
                'analysis_date': datetime.now().isoformat(),
                'model_accuracy': self.prediction_accuracy,
                'suggestions': suggestions,
                'predicted_trajectory': predictions
            }
            
        except Exception as e:
            print(f"최적화 전략 제안 오류: {e}")
            return None
    
    def generate_prediction_report(self):
        """종합 예측 보고서 생성"""
        try:
            print("📊 AI 진화 예측 보고서 생성 중...")
            
            # 모델 학습
            if not self.train_prediction_models():
                return None
            
            # 분석 수행
            patterns = self.analyze_evolution_patterns()
            predictions = self.predict_future_evolution(10)
            strategy = self.suggest_optimization_strategy()
            
            # 보고서 생성
            report = {
                'report_id': f"prediction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'generation_date': datetime.now().isoformat(),
                'model_performance': {
                    'accuracy': self.prediction_accuracy,
                    'confidence_level': 'high' if self.prediction_accuracy > 0.8 else 'medium' if self.prediction_accuracy > 0.6 else 'low'
                },
                'current_patterns': patterns,
                'future_predictions': predictions,
                'optimization_strategy': strategy,
                'recommendations': {
                    'immediate_actions': [
                        '창의성 엔진 파라미터 조정',
                        '중복 방지 알고리즘 강화',
                        '성능 평가 메트릭 개선'
                    ],
                    'long_term_goals': [
                        '자율적 목표 설정 시스템 구축',
                        '멀티모달 학습 능력 개발',
                        '분산 진화 시스템 구현'
                    ]
                }
            }
            
            # 보고서 저장 (JSON 호환성 처리)
            report_file = f"ai_evolution_prediction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            def convert_numpy_types(obj):
                """NumPy 타입을 JSON 호환 타입으로 변환"""
                if hasattr(obj, 'dtype'):
                    if 'int' in str(obj.dtype):
                        return int(obj)
                    elif 'float' in str(obj.dtype):
                        return float(obj)
                    else:
                        return str(obj)
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(item) for item in obj]
                else:
                    return obj
            
            report_json = convert_numpy_types(report)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_json, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 예측 보고서 생성 완료: {report_file}")
            return report
            
        except Exception as e:
            print(f"보고서 생성 오류: {e}")
            return None

if __name__ == "__main__":
    predictor = AIEvolutionPredictor()
    report = predictor.generate_prediction_report()
    
    if report:
        print("\n🔮 AI 진화 예측 보고서 요약:")
        print(f"📊 모델 정확도: {report['model_performance']['accuracy']:.3f}")
        print(f"🎯 신뢰도: {report['model_performance']['confidence_level']}")
        
        if report['future_predictions']:
            next_prediction = report['future_predictions'][0]
            print(f"🚀 다음 세대 예측 지능: {next_prediction['predicted_intelligence']:.1f}")
            print(f"📈 예상 성능 향상: {next_prediction['predicted_performance_gain']:.1f}")
        
        print(f"\n💡 주요 권장사항: {len(report['optimization_strategy']['suggestions'])}개")
        for suggestion in report['optimization_strategy']['suggestions'][:3]:
            print(f"   • {suggestion['suggestion']}")
    else:
        print("❌ 예측 보고서 생성 실패")
