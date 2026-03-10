# Copyright 2025 masa@kugel
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
from datetime import timedelta
from jose import jwt
from app.dependencies.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM
)

def test_password_hashing_consistency():
    """test_password_hashing_consistency
    Verify that password hashing is consistent and verifiable.
    """
    password = "secure_password_123"
    hashed = get_password_hash(password)
    
    # Verify same password works
    assert verify_password(password, hashed) is True
    
    # Verify different password fails
    assert verify_password("wrong_password", hashed) is False
    
    # Verify hashing twice produces different hashes (salt) but both are verifiable
    hashed_2 = get_password_hash(password)
    assert hashed != hashed_2
    assert verify_password(password, hashed_2) is True

def test_jwt_payload_contents():
    """test_jwt_payload_contents
    Verify that the JWT payload contains the expected claims.
    """
    data = {
        "sub": "test_user",
        "tenant_id": "T1234",
        "is_superuser": True
    }
    token = create_access_token(data=data)
    
    # Decode and verify payload
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    assert payload["sub"] == data["sub"]
    assert payload["tenant_id"] == data["tenant_id"]
    assert payload["is_superuser"] == data["is_superuser"]
    assert "exp" in payload
