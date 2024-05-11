from aiohttp.web_app import Application

__all__ = ("setup_routes",)


def setup_routes(application: Application):
    import app.admin.routes
    import app.game.routes
    import app.users.routes  # TODO: remove?

    app.admin.routes.setup_routes(application)
    app.game.routes.setup_routes(application)
    app.users.routes.register_urls(application)  # TODO: remove?
