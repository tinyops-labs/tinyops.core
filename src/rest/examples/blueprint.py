BLUEPRINT_RESPONSES = {
    "get": {
        200: {
            "description": "Current blueprint configuration",
            "content": {
                "application/json": {
                    "example": {
                        "applications": [
                            {
                                "name": "MyApp",
                                "image": "nginx",
                                "domain": "app.local.com",
                                "ssl": False,
                                "replicas": 2,
                                "volumes": ["./data:/data"],
                                "env": {"key": "value"}
                            }
                        ]
                    }
                }
            }
        }
    },
    "post": {
        200: {
            "description": "Blueprint updated",
            "content": {
                "application/json": {
                    "example": True
                }
            }
        },
        400: {
            "description": "Blueprint validation failed",
            "content": {
                "application/json": {
                    "example": {"errors": ["applications must be a list."]}
                }
            }
        }
    }
}
