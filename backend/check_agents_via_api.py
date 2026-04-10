#!/usr/bin/env python3
"""通过 API 查询 Agent"""
import requests

response = requests.get(
    'http://localhost:8000/api/v1/agents',
    headers={'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vIiwiZXhwIjoxNzc1ODc0MTMwfQ.hTffy1-HO_FDSxTBd5vGNr-JN2SqiTLJFbb9s-eSE2o'}
)

print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}")
print(f"\nAgent 数量: {response.json().get('count', 0)}")
