from unfazed.route import include, path

patterns = [
    path("/app1", routes=include("tests.proj.app1.routes")),
]
