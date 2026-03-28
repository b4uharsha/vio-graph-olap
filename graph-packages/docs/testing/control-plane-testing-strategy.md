# Control-Plane Testing Strategy: Senior Test Engineer Analysis

## Executive Summary

**Current State**: Control-plane at 52% coverage with significant gaps in K8s integration (9%), instance lifecycle (13%), and background jobs (29%).

**Root Cause**: Over-reliance on integration tests; lack of focused unit tests with proper isolation.

**Recommended Approach**: Adopt Google's Testing Pyramid with emphasis on fast, isolated unit tests using fakes over mocks.

---

## 1. Testing Pyramid for Control-Plane

```
        /\
       /  \  E2E Tests (5%)
      /----\  - Full stack with real K8s cluster
     /      \ - Notebook-based scenarios
    /--------\ Integration Tests (25%)
   /          \ - Real database, mocked K8s
  /------------\ - Multi-service coordination
 /--------------\ Unit Tests (70%)
/________________\ - Fast, isolated, comprehensive
                    - Fakes for K8s/repositories
```

**Current Distribution**: ~10% unit, ~80% integration, ~10% E2E
**Target Distribution**: ~70% unit, ~25% integration, ~5% E2E

---

## 2. Core Testing Principles (Google SWE Book)

### Principle 1: Make Tests Fast
- **Current Problem**: Integration tests take 2.42s for 157 tests
- **Solution**: Unit tests should run in <100ms total
- **Implementation**: Mock external dependencies (K8s, DB)

### Principle 2: Make Tests Deterministic
- **Current Problem**: Time-based lifecycle tests can be flaky
- **Solution**: Inject clock/time dependencies
- **Implementation**: Use `freezegun` or time injection

### Principle 3: Make Tests Isolated
- **Current Problem**: Tests share database state
- **Solution**: Each test gets fresh fixtures
- **Implementation**: Pytest fixtures with function scope

### Principle 4: Prefer Fakes Over Mocks
- **Current Problem**: Heavy mocking leads to brittle tests
- **Solution**: Create lightweight fake implementations
- **Implementation**: FakeK8sClient, FakeRepository classes

---

## 3. Area-Specific Testing Strategies

### 3.1 K8sService (Currently 9% Coverage)

**Challenge**: Kubernetes client API with complex object models.

**❌ Anti-Pattern: Heavy Mocking**
```python
# DON'T: Brittle, hard to maintain
mock_api = MagicMock()
mock_api.create_namespaced_pod = MagicMock(
    return_value=MagicMock(
        metadata=MagicMock(name="pod-123"),
        status=MagicMock(phase="Pending")
    )
)
```

**✅ Recommended: Fake K8s Client**
```python
# DO: Maintainable, realistic
class FakeK8sClient:
    """Lightweight in-memory K8s API for testing."""

    def __init__(self):
        self.pods = {}
        self.services = {}
        self.ingresses = {}

    def create_namespaced_pod(self, namespace, body):
        pod_name = body.metadata.name
        self.pods[pod_name] = V1Pod(
            metadata=V1ObjectMeta(name=pod_name),
            status=V1PodStatus(phase="Pending")
        )
        return self.pods[pod_name]

    def delete_namespaced_pod(self, name, namespace):
        if name not in self.pods:
            raise ApiException(status=404)
        del self.pods[name]
        return V1Status(status="Success")
```

**Implementation Path**:
1. Create `tests/fakes/k8s_client.py` with FakeK8sClient
2. Add fixture in `tests/conftest.py`:
   ```python
   @pytest.fixture
   def fake_k8s_service(settings):
       fake_client = FakeK8sClient()
       service = K8sService(settings)
       service._core_api = fake_client
       service._networking_api = fake_client
       service._initialized = True
       return service
   ```
3. Write focused unit tests for each method

**Test Coverage Plan**:
- ✅ Pod creation with correct env vars, volumes, resources (30 lines)
- ✅ Service creation with correct selector, ports (15 lines)
- ✅ Ingress creation for nginx vs traefik (40 lines)
- ✅ Pod deletion with cascading cleanup (10 lines)
- ✅ Error handling: ApiException 404, 409, 500 (25 lines)
- ✅ Lazy initialization paths (15 lines)
- ✅ Graceful degradation when K8s unavailable (10 lines)

**Expected Outcome**: 145 test lines → ~85% coverage (from 9%)

---

### 3.2 InstanceService (Currently 13% Coverage)

**Challenge**: Orchestrates multiple repositories and K8s service.

**❌ Anti-Pattern: Integration Test for Everything**
```python
# DON'T: Slow, hard to debug
async def test_create_instance(db_session):
    # Sets up real DB, real K8s...
    # Takes 500ms per test
```

**✅ Recommended: Unit Test with Injected Dependencies**
```python
# DO: Fast, focused
async def test_create_instance_enforces_concurrency_limit():
    # Arrange
    fake_instance_repo = FakeInstanceRepository(
        existing_count=10  # Already at limit
    )
    fake_config_repo = FakeConfigRepository(
        max_instances_per_user=10
    )
    service = InstanceService(
        instance_repo=fake_instance_repo,
        config_repo=fake_config_repo,
        k8s_service=None  # Not needed for this test
    )

    # Act & Assert
    with pytest.raises(ConcurrencyLimitError) as exc:
        await service.create_instance(
            user=fake_user(role=UserRole.ANALYST),
            snapshot_id=1,
            description="test"
        )

    assert "10/10" in str(exc.value)
```

**Implementation Path**:
1. Create fake repositories in `tests/fakes/repositories.py`
2. Make service accept repository dependencies via constructor
3. Write parametrized tests for each business rule

**Test Coverage Plan**:
- ✅ Concurrency limit enforcement (analyst vs cluster-wide) (20 lines)
- ✅ Permission checks (owner validation) (15 lines)
- ✅ TTL/timeout defaults from config (10 lines)
- ✅ K8s pod creation success path (20 lines)
- ✅ K8s pod creation failure (best-effort logging) (15 lines)
- ✅ Termination permission checks (15 lines)
- ✅ Deletion cascade to K8s (15 lines)
- ✅ Status transition validation (15 lines)

**Expected Outcome**: 125 test lines → ~80% coverage (from 13%)

---

### 3.3 Lifecycle Job (Currently 29% Coverage)

**Challenge**: Time-based logic with complex ISO 8601 duration parsing.

**❌ Anti-Pattern: Sleep-Based Tests**
```python
# DON'T: Slow, flaky
async def test_ttl_expiration():
    instance = await create_instance(ttl_duration="PT1S")
    await asyncio.sleep(2)  # Flaky!
    await lifecycle_job.run()
    assert instance.status == "terminated"
```

**✅ Recommended: Time Injection with Freezegun**
```python
# DO: Fast, deterministic
from freezegun import freeze_time

@freeze_time("2024-01-01 12:00:00")
async def test_ttl_expiration():
    # Create instance at 12:00
    instance = await create_instance(
        ttl_duration="PT1H",
        created_at=datetime(2024, 1, 1, 10, 0)  # 2h ago
    )

    # Run job - instance should be terminated
    await lifecycle_job.run()

    assert instance.status == "terminated"
    assert instance.terminated_at == datetime(2024, 1, 1, 12, 0)
```

**Implementation Path**:
1. Inject clock dependency into LifecycleJob
2. Use `freezegun` for deterministic time
3. Parametrize duration parsing tests

**Test Coverage Plan**:
- ✅ ISO 8601 parsing: PT1H, PT24H, P1D, P7D, P1W (30 lines)
- ✅ Negative duration rejection (10 lines)
- ✅ TTL enforcement logic (20 lines)
- ✅ Inactivity timeout logic (20 lines)
- ✅ Snapshot expiration (15 lines)
- ✅ Mapping expiration (15 lines)
- ✅ Metrics updates (15 lines)
- ✅ Error recovery (continue on failure) (15 lines)

**Expected Outcome**: 140 test lines → ~75% coverage (from 29%)

---

### 3.4 Repositories (instances.py 21%, snapshots.py 21%)

**Challenge**: Complex SQL queries with filtering, pagination, JSON fields.

**❌ Anti-Pattern: Test Only Happy Path**
```python
# DON'T: Insufficient coverage
async def test_list_instances(db_session):
    instances = await repo.list_instances()
    assert len(instances) > 0
```

**✅ Recommended: Parametrized Filter Combinations**
```python
# DO: Comprehensive coverage
@pytest.mark.parametrize("filters,expected_count", [
    ({"owner_id": "user1"}, 2),
    ({"snapshot_id": 1}, 3),
    ({"status": InstanceStatus.RUNNING}, 1),
    ({"owner_id": "user1", "status": InstanceStatus.RUNNING}, 1),
    ({"search": "test"}, 2),  # Searches description
    ({}, 5),  # No filters
])
async def test_list_instances_filtering(db_session, filters, expected_count):
    # Setup known test data
    await setup_test_instances(db_session)

    # Test filtering
    result = await repo.list_instances(**filters)
    assert len(result.items) == expected_count
```

**Implementation Path**:
1. Create `tests/fixtures/database.py` with realistic test data
2. Write parametrized tests for each filter combination
3. Test JSON field edge cases

**Test Coverage Plan (per repository)**:
- ✅ All filter combinations (6 params × 3 values = 18 tests)
- ✅ Pagination edge cases (offset, limit, total) (10 lines)
- ✅ JSON field handling (null, invalid, complex) (15 lines)
- ✅ Conditional updates (COALESCE logic) (15 lines)
- ✅ Activity timestamp updates (10 lines)
- ✅ Sort field validation (5 lines)
- ✅ Count query accuracy (5 lines)

**Expected Outcome**: 80 test lines per repo → ~75% coverage (from 21%)

---

### 3.5 API Routers (Various, 18-63% coverage)

**Challenge**: Dependency injection, permission checks, error handling.

**❌ Anti-Pattern: Only Integration Tests**
```python
# DON'T: Slow, couples to full stack
async def test_create_instance_endpoint(client):
    response = client.post("/api/instances", json={...})
    assert response.status_code == 201
```

**✅ Recommended: Unit Test with Mocked Services**
```python
# DO: Fast, focused on endpoint logic
async def test_create_instance_endpoint_permission_denied():
    # Arrange: Mock service raises permission error
    mock_service = MagicMock()
    mock_service.create_instance = AsyncMock(
        side_effect=PermissionDeniedError("Instance", 1)
    )

    # Act: Call endpoint directly
    with pytest.raises(HTTPException) as exc:
        await create_instance(
            request=CreateInstanceRequest(snapshot_id=1),
            service=mock_service,
            user=fake_analyst_user()
        )

    # Assert: Correct error response
    assert exc.value.status_code == 403
    assert "PERMISSION_DENIED" in str(exc.value.detail)
```

**Implementation Path**:
1. Test endpoint functions directly (not via HTTP)
2. Mock service layer dependencies
3. Parametrize permission scenarios

**Test Coverage Plan (per router)**:
- ✅ Success case with response serialization (5 lines)
- ✅ All error cases (NotFound, PermissionDenied, ValidationError) (15 lines)
- ✅ Permission scenarios (analyst, admin, ops, owner) (20 lines)
- ✅ Pagination parameters (10 lines)
- ✅ Query parameter validation (10 lines)

**Expected Outcome**: 60 test lines per router → ~75% coverage

---

## 4. Fake Implementation Library

Create reusable fakes in `tests/fakes/`:

### 4.1 FakeK8sClient
```python
class FakeK8sClient:
    """In-memory K8s API for testing.

    Simulates pod/service/ingress lifecycle without real cluster.
    """

    def __init__(self):
        self.pods: dict[str, V1Pod] = {}
        self.services: dict[str, V1Service] = {}
        self.ingresses: dict[str, V1Ingress] = {}
        self.call_log: list[tuple[str, dict]] = []

    def create_namespaced_pod(self, namespace: str, body: V1Pod) -> V1Pod:
        name = body.metadata.name
        if name in self.pods:
            raise ApiException(status=409, reason="Already Exists")

        self.pods[name] = body
        self.call_log.append(("create_pod", {"name": name, "namespace": namespace}))
        return body

    def set_error_on_next_call(self, method: str, error: ApiException):
        """Inject failures for testing error handling."""
        self._next_error = (method, error)
```

### 4.2 FakeRepository
```python
class FakeInstanceRepository:
    """In-memory instance repository for testing.

    Provides same interface as real repository but uses dict storage.
    """

    def __init__(self, initial_instances: list[Instance] = None):
        self.instances: dict[int, Instance] = {}
        self.next_id = 1

        for instance in (initial_instances or []):
            self.instances[instance.id] = instance

    async def create(self, **kwargs) -> Instance:
        instance = Instance(id=self.next_id, **kwargs)
        self.instances[self.next_id] = instance
        self.next_id += 1
        return instance

    async def list_by_owner(self, owner_id: str) -> list[Instance]:
        return [i for i in self.instances.values() if i.owner_id == owner_id]
```

### 4.3 FakeClock
```python
class FakeClock:
    """Controllable clock for time-based testing."""

    def __init__(self, now: datetime = None):
        self._now = now or datetime.now(UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta):
        """Move time forward for testing TTL/timeouts."""
        self._now += delta
```

---

## 5. Test Organization Structure

```
tests/
├── unit/                          # Fast, isolated tests (70%)
│   ├── services/
│   │   ├── test_k8s_service.py           # K8s operations
│   │   ├── test_instance_service.py      # Business logic
│   │   ├── test_mapping_service.py
│   │   └── test_snapshot_service.py
│   ├── repositories/
│   │   ├── test_instances_repo.py        # SQL queries
│   │   ├── test_snapshots_repo.py
│   │   └── test_mappings_repo.py
│   ├── jobs/
│   │   ├── test_lifecycle.py             # TTL/timeout enforcement
│   │   ├── test_export_reconciliation.py
│   │   └── test_schema_cache.py
│   ├── routers/
│   │   ├── api/
│   │   │   ├── test_instances_router.py  # Endpoint logic
│   │   │   ├── test_snapshots_router.py
│   │   │   └── test_mappings_router.py
│   │   └── internal/
│   │       └── test_internal_routers.py
│   └── models/
│       ├── test_domain.py                # Pydantic models
│       ├── test_errors.py                # ✅ Already done
│       └── test_requests_responses.py
│
├── integration/                   # Multi-service tests (25%)
│   ├── test_instance_lifecycle.py        # Create → Run → Terminate
│   ├── test_snapshot_export.py           # Export job integration
│   └── test_permission_enforcement.py    # Auth + DB + service
│
├── e2e/                           # Full stack tests (5%)
│   └── notebooks/
│       └── admin_workflow_test.ipynb     # Real K8s cluster
│
└── fakes/                         # Reusable test doubles
    ├── __init__.py
    ├── k8s_client.py              # FakeK8sClient
    ├── repositories.py            # Fake*Repository classes
    ├── clock.py                   # FakeClock
    └── fixtures.py                # Common test data builders
```

---

## 6. Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Create `tests/fakes/` directory structure
- [ ] Implement FakeK8sClient with core operations
- [ ] Implement FakeClock for time-based tests
- [ ] Add pytest fixtures in `conftest.py`

### Phase 2: Critical Services (Week 2)
- [ ] Test k8s_service.py → 85% coverage (+76%)
- [ ] Test instance_service.py → 80% coverage (+67%)
- [ ] Test lifecycle.py → 75% coverage (+46%)

### Phase 3: Data Layer (Week 3)
- [ ] Test instances.py → 75% coverage (+54%)
- [ ] Test snapshots.py → 75% coverage (+54%)
- [ ] Test mappings.py → 85% coverage (+9%)

### Phase 4: API Layer (Week 4)
- [ ] Test instances_router.py → 75% coverage (+19%)
- [ ] Test snapshots_router.py → 75% coverage (+12%)
- [ ] Test config_router.py → 75% coverage (+46%)

### Phase 5: Verification (Week 5)
- [ ] Verify all modules ≥75% coverage
- [ ] Performance check: unit tests complete in <200ms
- [ ] Flakiness check: 10 consecutive runs pass
- [ ] Documentation update

**Estimated Effort**:
- ~800 lines of fake implementations
- ~1200 lines of unit tests
- ~200 lines of integration test refactoring
- **Total: ~2000 lines of test code**

---

## 7. Measuring Success

### Metrics to Track

1. **Coverage**
   - Target: All modules ≥75%
   - Track: Line coverage, branch coverage
   - Tool: pytest-cov

2. **Speed**
   - Target: Unit tests <200ms total
   - Track: pytest --durations=10
   - Fail CI if >500ms

3. **Flakiness**
   - Target: 0 flaky tests
   - Track: Run 10x locally before merge
   - Use pytest-repeat

4. **Maintainability**
   - Target: Each test <50 lines
   - Track: Code review feedback
   - Refactor to test helpers

### Coverage Quality Checklist

For each module, verify:
- [ ] Happy path tested
- [ ] All error paths tested
- [ ] Edge cases tested (null, empty, boundary)
- [ ] Permission scenarios tested
- [ ] Concurrency scenarios tested (if applicable)
- [ ] All public methods tested
- [ ] Integration points tested (with fakes)

---

## 8. Key Insights from Google Testing Practices

### From "Software Engineering at Google"

1. **"Tests should test state, not interactions"**
   - ❌ Don't: `mock.assert_called_with(specific_args)`
   - ✅ Do: Assert on observable outcomes

2. **"Prefer testing public APIs over internals"**
   - Test `create_instance()` behavior, not `_validate_limits()`

3. **"Write tests that are resilient to refactoring"**
   - Test contracts, not implementation details

4. **"Make tests complete and concise"**
   - Each test should be self-contained
   - Keep tests under 50 lines

5. **"Test behaviors, not methods"**
   - One test per behavior, not one test per method

### Avoid Test-Induced Design Damage

Current code has some testability issues:
1. K8sService singleton pattern makes injection hard
2. Repositories tightly coupled to SQLAlchemy
3. Services create their own dependencies

**Refactoring for Testability**:
```python
# Before: Hard to test
class InstanceService:
    def __init__(self, settings: Settings):
        self.repo = InstanceRepository(get_session())  # Coupled!
        self.k8s = get_k8s_service()  # Singleton!

# After: Easy to test
class InstanceService:
    def __init__(
        self,
        instance_repo: InstanceRepository,
        k8s_service: K8sService | None = None,
        config_repo: ConfigRepository | None = None,
    ):
        self.instance_repo = instance_repo
        self.k8s_service = k8s_service
        self.config_repo = config_repo or get_config_repo()
```

---

## 9. Anti-Patterns to Avoid

### ❌ Don't: Overly Specific Mocks
```python
mock.assert_called_with(
    V1Pod(
        metadata=V1ObjectMeta(name="instance-123-abc"),  # Brittle!
        spec=V1PodSpec(...)
    )
)
```

### ✅ Do: Assert on Behavior
```python
# Check that a pod was created with correct properties
pods = fake_k8s.pods.values()
assert len(pods) == 1
pod = pods[0]
assert pod.metadata.name.startswith("instance-123")
assert pod.spec.containers[0].image == "wrapper:latest"
```

### ❌ Don't: Test Implementation Details
```python
def test_create_calls_validate():
    service.create_instance(...)
    service._validate_limits.assert_called_once()  # Couples to impl!
```

### ✅ Do: Test Behavior
```python
def test_create_respects_concurrency_limit():
    # When at limit
    with pytest.raises(ConcurrencyLimitError):
        service.create_instance(...)
```

### ❌ Don't: Share Test Data via Module Globals
```python
TEST_INSTANCE = Instance(...)  # Shared state!

def test_a():
    instance = TEST_INSTANCE
    instance.status = "running"  # Modifies global!
```

### ✅ Do: Use Fixtures for Fresh Data
```python
@pytest.fixture
def test_instance():
    return Instance(id=1, status="pending")  # Fresh each time

def test_a(test_instance):
    test_instance.status = "running"  # Isolated
```

---

## 10. Tooling Recommendations

### Essential Testing Tools

1. **pytest-asyncio** ✅ Already using
   - For async/await testing

2. **freezegun** 🆕 Add for time-based tests
   ```bash
   pip install freezegun
   ```

3. **pytest-parametrize-cases** 🆕 For cleaner parametrization
   ```bash
   pip install pytest-parametrize-cases
   ```

4. **pytest-repeat** 🆕 For flakiness detection
   ```bash
   pip install pytest-repeat
   ```

5. **pytest-timeout** 🆕 Catch slow tests
   ```bash
   pip install pytest-timeout
   ```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
test:
  steps:
    - name: Unit Tests
      run: |
        pytest tests/unit/ \
          --cov=control_plane \
          --cov-report=term \
          --cov-fail-under=75 \
          --timeout=1 \
          --maxfail=5

    - name: Flakiness Check
      run: |
        pytest tests/unit/ --count=3 --verbose

    - name: Integration Tests
      run: |
        pytest tests/integration/ \
          --timeout=10
```

---

## 11. Example: Complete Test Suite for K8sService.create_pod()

```python
# tests/unit/services/test_k8s_service.py

import pytest
from kubernetes.client import ApiException, V1Pod, V1Container

from control_plane.services.k8s_service import K8sService
from tests.fakes.k8s_client import FakeK8sClient


class TestK8sServiceCreatePod:
    """Test suite for K8sService.create_pod()."""

    @pytest.fixture
    def fake_k8s_service(self, settings):
        """Create K8sService with fake K8s client."""
        fake_client = FakeK8sClient()
        service = K8sService(settings)
        service._core_api = fake_client
        service._initialized = True
        return service, fake_client

    def test_create_pod_success(self, fake_k8s_service):
        """Should create pod with correct configuration."""
        service, fake_client = fake_k8s_service

        # Act
        pod_name = service.create_pod(
            instance_id="inst-123",
            snapshot_id="snap-456",
            mapping_id="map-789",
            owner_id="user-1",
            gcs_path="gs://bucket/snap-456"
        )

        # Assert
        assert pod_name.startswith("inst-123")
        assert len(fake_client.pods) == 1

        pod = fake_client.pods[pod_name]
        assert pod.metadata.labels["instance-id"] == "inst-123"

        container = pod.spec.containers[0]
        assert container.image == "wrapper:latest"

        # Check environment variables
        env_dict = {e.name: e.value for e in container.env}
        assert env_dict["WRAPPER_INSTANCE_ID"] == "inst-123"
        assert env_dict["WRAPPER_SNAPSHOT_ID"] == "snap-456"
        assert env_dict["WRAPPER_GCS_BASE_PATH"] == "gs://bucket/snap-456"

    def test_create_pod_with_resource_limits(self, fake_k8s_service):
        """Should respect CPU and memory limits."""
        service, fake_client = fake_k8s_service

        pod_name = service.create_pod(
            instance_id="inst-123",
            snapshot_id="snap-456",
            mapping_id="map-789",
            owner_id="user-1",
            gcs_path="gs://bucket/snap-456",
            cpu_limit="2000m",
            memory_limit="4Gi"
        )

        pod = fake_client.pods[pod_name]
        resources = pod.spec.containers[0].resources
        assert resources.limits["cpu"] == "2000m"
        assert resources.limits["memory"] == "4Gi"

    def test_create_pod_duplicate_name_raises_conflict(self, fake_k8s_service):
        """Should raise error when pod already exists."""
        service, fake_client = fake_k8s_service

        # Create first pod
        service.create_pod(
            instance_id="inst-123",
            snapshot_id="snap-456",
            mapping_id="map-789",
            owner_id="user-1",
            gcs_path="gs://bucket/snap-456"
        )

        # Try to create duplicate
        with pytest.raises(ApiException) as exc:
            service.create_pod(
                instance_id="inst-123",  # Same ID
                snapshot_id="snap-456",
                mapping_id="map-789",
                owner_id="user-1",
                gcs_path="gs://bucket/snap-456"
            )

        assert exc.value.status == 409

    @pytest.mark.parametrize("error_code", [500, 503])
    def test_create_pod_api_error_propagates(self, fake_k8s_service, error_code):
        """Should propagate K8s API errors."""
        service, fake_client = fake_k8s_service

        # Inject API error
        fake_client.set_error_on_next_call(
            "create_namespaced_pod",
            ApiException(status=error_code, reason="Server Error")
        )

        with pytest.raises(ApiException) as exc:
            service.create_pod(
                instance_id="inst-123",
                snapshot_id="snap-456",
                mapping_id="map-789",
                owner_id="user-1",
                gcs_path="gs://bucket/snap-456"
            )

        assert exc.value.status == error_code
```

**Test Metrics**:
- Lines of test code: 95
- Lines of production code tested: ~60
- Coverage improvement: 9% → ~45% (single method)
- Test execution time: <10ms
- Number of edge cases covered: 5

---

## 12. Conclusion

**To achieve 75% coverage on control-plane**:

1. ✅ **Adopt testing pyramid**: 70% unit, 25% integration, 5% E2E
2. ✅ **Build fake library**: FakeK8sClient, FakeRepository, FakeClock
3. ✅ **Write focused unit tests**: 1 behavior per test, <50 lines each
4. ✅ **Use time injection**: freezegun for deterministic time-based tests
5. ✅ **Parametrize extensively**: Cover filter combinations, error codes
6. ✅ **Refactor for testability**: Inject dependencies, avoid singletons
7. ✅ **Measure quality**: Speed, flakiness, maintainability

**Estimated ROI**:
- **Time investment**: ~2 weeks for 2000 lines of test code
- **Coverage gain**: 52% → 75% (+23% = 714 production lines covered)
- **Long-term benefit**:
  - Faster development (instant feedback vs 2.4s integration tests)
  - Higher confidence in refactoring
  - Better documentation via tests
  - Fewer production bugs

**Next Steps**:
1. Get buy-in from team on testing pyramid approach
2. Start with Phase 1: Build fake library
3. Pick one critical service (k8s_service or instance_service)
4. Write comprehensive test suite following this guide
5. Measure success and iterate

---

**References**:
- Google's "Software Engineering at Google" (Chapter 11-14)
- Martin Fowler's "Test Pyramid" (2012)
- "Growing Object-Oriented Software, Guided by Tests" (Freeman & Pryce)
- Pytest documentation on fixtures and parametrization
