from unfazed.route import include, path

patterns = [
    path("/app1", routes=include("app1.routes")),
]
