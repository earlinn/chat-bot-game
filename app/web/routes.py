from aiohttp.web_app import Application

__all__ = ("setup_routes",)


def setup_routes(application: Application):
    import app.admin.routes
    import app.users.routes

    app.admin.routes.setup_routes(application)
    app.users.routes.register_urls(application)
