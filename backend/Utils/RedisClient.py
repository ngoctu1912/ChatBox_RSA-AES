import redis
import json
from typing import Optional, Any


class RedisClient:
    """
    Quản lý kết nối Redis để cache online users, session keys, etc.
    """
    
    def __init__(self, host='localhost', port=6379, db=0, decode_responses=True):
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=decode_responses
            )
            # Test connection
            self.client.ping()
            print("✅ Redis connected successfully")
        except redis.ConnectionError as e:
            print(f"❌ Redis connection failed: {e}")
            self.client = None

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Lưu data vào Redis với optional expiration time (seconds)"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if expire:
                return self.client.setex(key, expire, value)
            return self.client.set(key, value)
        except Exception as e:
            print(f"Redis SET error: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Lấy data từ Redis"""
        try:
            value = self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            print(f"Redis GET error: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Xóa key khỏi Redis"""
        try:
            return self.client.delete(key) > 0
        except Exception as e:
            print(f"Redis DELETE error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Kiểm tra key có tồn tại không"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            return False

    def hset(self, name: str, key: str, value: Any) -> bool:
        """Set hash field"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.client.hset(name, key, value)
        except Exception as e:
            print(f"Redis HSET error: {e}")
            return False

    def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field"""
        try:
            value = self.client.hget(name, key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            print(f"Redis HGET error: {e}")
            return None

    def hgetall(self, name: str) -> dict:
        """Get all hash fields"""
        try:
            data = self.client.hgetall(name)
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except json.JSONDecodeError:
                    result[k] = v
            return result
        except Exception as e:
            print(f"Redis HGETALL error: {e}")
            return {}

    def hdel(self, name: str, key: str) -> bool:
        """Delete hash field"""
        try:
            return self.client.hdel(name, key) > 0
        except Exception as e:
            print(f"Redis HDEL error: {e}")
            return False

    def sadd(self, name: str, *values) -> int:
        """Add to set"""
        try:
            return self.client.sadd(name, *values)
        except Exception as e:
            print(f"Redis SADD error: {e}")
            return 0

    def srem(self, name: str, *values) -> int:
        """Remove from set"""
        try:
            return self.client.srem(name, *values)
        except Exception as e:
            print(f"Redis SREM error: {e}")
            return 0

    def smembers(self, name: str) -> set:
        """Get all set members"""
        try:
            return self.client.smembers(name)
        except Exception as e:
            print(f"Redis SMEMBERS error: {e}")
            return set()

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time"""
        try:
            return self.client.expire(key, seconds)
        except Exception as e:
            print(f"Redis EXPIRE error: {e}")
            return False


# Singleton instance
redis_client = RedisClient()