"""Tests for database utility functions: cache decorator, query helpers."""
import time
from src.backend.database import cached, _cache


class TestCacheDecorator:
    def test_caches_result(self):
        call_count = 0

        @cached(ttl_seconds=60)
        def expensive():
            nonlocal call_count
            call_count += 1
            return {"data": "test"}

        result1 = expensive()
        result2 = expensive()
        assert result1 == result2
        assert call_count == 1

    def test_cache_expires(self):
        call_count = 0

        @cached(ttl_seconds=0.1)
        def quick_expire():
            nonlocal call_count
            call_count += 1
            return call_count

        result1 = quick_expire()
        time.sleep(0.15)
        result2 = quick_expire()
        assert result1 == 1
        assert result2 == 2

    def test_different_args_different_cache(self):
        @cached(ttl_seconds=60)
        def with_args(x):
            return x * 2

        assert with_args(5) == 10
        assert with_args(3) == 6

    def test_kwargs_cached_separately(self):
        call_count = 0

        @cached(ttl_seconds=60)
        def with_kwargs(name="default"):
            nonlocal call_count
            call_count += 1
            return name

        with_kwargs(name="a")
        with_kwargs(name="b")
        with_kwargs(name="a")  # should hit cache
        assert call_count == 2
