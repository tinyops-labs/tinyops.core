CONTAINER_RESPONSES = {
    "logs": {
        200: {
            "description": "Container logs",
            "content": {
                "application/json": {
                    "example": [
                        "/docker-entrypoint.sh: Configuration complete; ready for start up",
                        "2026/03/15 13:19:26 [notice] 1#1: using the \"epoll\" event method",
                        "2026/03/15 13:19:26 [notice] 1#1: nginx/1.27.3",
                        "2026/03/15 13:19:26 [notice] 1#1: start worker processes",
                        "2026/03/15 13:19:26 [notice] 1#1: start worker process 23"
                    ]
                }
            }
        }
    }
}
