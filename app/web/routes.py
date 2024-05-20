from aiohttp.web_app import Application

__all__ = ("setup_routes",)


def setup_routes(application: Application):
    import app.admin.routes
    import app.game.routes

    app.admin.routes.setup_routes(application)
    app.game.routes.setup_routes(application)
