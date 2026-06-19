DOMAIN_RESPONSES = {
    "get": {
        200: {
            "description": "All domains with SSL status",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "name": "MyApp",
                            "domain": "app.local.com",
                            "ssl": True,
                            "ssl_ready": True,
                            "ssl_pending": False,
                            "ssl_creation_failed": False
                        },
                        {
                            "name": "ApiService",
                            "domain": "api.local.com",
                            "ssl": True,
                            "ssl_ready": False,
                            "ssl_pending": True,
                            "ssl_creation_failed": False
                        }
                    ]
                }
            }
        }
    },
    "reset": {
        200: {
            "description": "SSL creation failed flag reset",
            "content": {
                "application/json": {
                    "example": True
                }
            }
        }
    }
}
