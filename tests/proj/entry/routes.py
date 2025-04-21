from unfazed.route import include, path

patterns = [
    path("/api/app", routes=include("app.routes")),
]
