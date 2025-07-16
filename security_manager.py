#!/usr/bin/env python3
"""
보안 강화 및 접근 제어 시스템
"""
import hashlib
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
import json

class SecurityManager:
    def __init__(self):
        self.secret_key = secrets.token_urlsafe(32)
        self.token_expiry = timedelta(hours=24)
        self.rate_limits = {}
        self.blocked_ips = set()
    def generate_secure_token(self, user_id: str) -> str:
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(16)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    def validate_token(self, token: str) -> Optional[Dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logging.warning("만료된 토큰 사용 시도")
            return None
        except jwt.InvalidTokenError:
            logging.warning("유효하지 않은 토큰 사용 시도")
            return None
    def check_rate_limit(self, client_ip: str, endpoint: str) -> bool:
        key = f"{client_ip}:{endpoint}"
        current_time = datetime.now()
        if key not in self.rate_limits:
            self.rate_limits[key] = []
        self.rate_limits[key] = [req_time for req_time in self.rate_limits[key] if (current_time - req_time).total_seconds() < 60]
        if len(self.rate_limits[key]) >= 60:
            self.blocked_ips.add(client_ip)
            logging.warning(f"Rate limit exceeded for {client_ip}")
            return False
        self.rate_limits[key].append(current_time)
        return True
    def encrypt_sensitive_data(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()
    def audit_log(self, action: str, user_id: str, details: Dict):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user_id': user_id,
            'details': details
        }
        with open('security_audit.log', 'a', encoding='utf-8') as f:
            f.write(f"{json.dumps(log_entry, ensure_ascii=False)}\n")
