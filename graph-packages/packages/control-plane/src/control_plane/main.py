"""FastAPI application factory."""

import structlog
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from control_plane.cache.schema_cache import SchemaMetadataCache
from control_plane.config import Settings, get_settings
from control_plane.infrastructure.database import (
    DatabaseCommitMiddleware,
    DatabaseManager,
    get_session_factory,
)
from control_plane.jobs import BackgroundJobScheduler
from control_plane.middleware import RequestIdMiddleware, register_exception_handlers
from control_plane.routers import health_router
from control_plane.routers.api import (
    admin_router,
    cluster_router,
    config_router,
    data_sources_router,
    export_jobs_router,
    favorites_router,
    instances_router,
    mappings_router,
    ops_router,
    schema_router,
    # SNAPSHOT FUNCTIONALITY DISABLED - snapshots are now created implicitly
    # snapshots_router,
)
from control_plane.routers.internal import (
    data_sources_router as internal_data_sources_router,
)
from control_plane.routers.internal import (
    export_jobs_router as internal_export_jobs_router,
)
from control_plane.routers.internal import (
    instances_router as internal_instances_router,
)
from control_plane.routers.internal import (
    snapshots_router as internal_snapshots_router,
)
from control_plane.routers.metrics import router as metrics_router

logger = structlog.get_logger()


async def _seed_default_data_source(
    settings: Settings,
    db_manager: DatabaseManager,
) -> None:
    """Seed a default data source from env vars if none exist.

    Ensures backward compatibility: existing deployments that configure
    Starburst via GRAPH_OLAP_STARBURST_URL env var will auto-migrate
    that config into the data_sources table on first startup.
    """
    if not settings.starburst_url:
        return

    try:
        from control_plane.repositories.data_sources import DataSourceRepository

        session_factory = get_session_factory()
        async with session_factory() as session:
            repo = DataSourceRepository(session)

            # Check if any data sources already exist
            count_sql = "SELECT COUNT(*) FROM data_sources"
            count = await repo._fetch_scalar(count_sql, {})
            if count and count > 0:
                return

            # Create system-level default data source from env vars
            starburst_password = settings.starburst_password.get_secret_value()
            await repo.create(
                owner_username="system@viograph.io",
                name="Default Starburst",
                source_type="starburst",
                config={
                    "host": settings.starburst_url,
                    "catalog": settings.starburst_catalog,
                    "user": settings.starburst_user,
                },
                credentials={
                    "password": starburst_password,
                },
                is_default=True,
            )
            await session.commit()

            logger.info(
                "Seeded default data source from env vars",
                name="Default Starburst",
                source_type="starburst",
                host=settings.starburst_url,
                catalog=settings.starburst_catalog,
            )
    except Exception as e:
        logger.warning(
            "Failed to seed default data source",
            error=str(e),
        )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional settings override (for testing)

    Returns:
        Configured FastAPI application
    """
    if settings is None:
        settings = get_settings()

    # Database manager for lifecycle
    db_manager = DatabaseManager(settings)

    # Background job scheduler for lifecycle and reconciliation
    scheduler = BackgroundJobScheduler(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Application lifespan handler."""
        # Startup
        await db_manager.startup()

        # Seed default data source from env vars (backward compatibility)
        await _seed_default_data_source(settings, db_manager)

        # Initialize schema metadata cache
        schema_cache = SchemaMetadataCache()
        app.state.schema_cache = schema_cache
        # Give scheduler access to schema cache for background refresh job
        scheduler.set_schema_cache(schema_cache)
        await scheduler.start()
        # Store scheduler in app state for ops endpoints
        app.state.scheduler = scheduler
        yield
        # Shutdown
        await scheduler.stop()
        await db_manager.shutdown()

    app = FastAPI(
        title="Graph OLAP API",
        description="API for Graph OLAP Platform",
        version="0.1.0",
        lifespan=lifespan,
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Store settings in app state for access by dependencies
    app.state.settings = settings

    # Middleware (order matters - first added is outermost)
    app.add_middleware(RequestIdMiddleware)

    # CORS (configure as needed for your environment)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Database commit middleware (innermost - runs just before response)
    # CRITICAL: This must be added LAST so it commits sessions before response is sent
    # Ensures read-after-write consistency for all mutations
    app.add_middleware(DatabaseCommitMiddleware)

    # Exception handlers
    register_exception_handlers(app)

    # Health check routes
    app.include_router(health_router)

    # Metrics endpoint (for Prometheus)
    app.include_router(metrics_router, include_in_schema=False)

    # Public API routes (shown in docs)
    app.include_router(mappings_router)
    app.include_router(instances_router)
    app.include_router(data_sources_router)

    # Public API routes (hidden from docs — not yet tested)
    app.include_router(favorites_router, include_in_schema=False)
    app.include_router(config_router, include_in_schema=False)
    app.include_router(cluster_router, include_in_schema=False)
    app.include_router(schema_router, include_in_schema=False)
    app.include_router(ops_router, include_in_schema=False)
    app.include_router(admin_router, include_in_schema=False)
    app.include_router(export_jobs_router, include_in_schema=False)

    # Internal API routes (service-to-service, hidden from docs)
    app.include_router(internal_snapshots_router, include_in_schema=False)
    app.include_router(internal_instances_router, include_in_schema=False)
    app.include_router(internal_export_jobs_router, include_in_schema=False)
    app.include_router(internal_data_sources_router, include_in_schema=False)

    return app


# Default application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "control_plane.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
