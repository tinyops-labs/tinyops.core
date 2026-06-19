DASHBOARD_RESPONSES = {
    200: {
        "description": "Current system state",
        "content": {
            "application/json": {
                "example": {
                    "atoms": [
                        {
                            "id": "FKzaKn72kNl88sRLAMhF7",
                            "name": "MyApp",
                            "up_for_creation": False,
                            "up_for_deletion": False,
                            "deletable": True,
                            "image": "nginx",
                            "network": None,
                            "domain": "app.local.com",
                            "ssl": False,
                            "env": {"key": "value"},
                            "ports": {"80": 80},
                            "volumes": ["./data:/data"],
                            "link": True,
                            "created_at": "2021-01-01 12:00:00",
                            "container": {
                                "name": "MyApp-abc123",
                                "cpu_usage": 0,
                                "memory_usage": 0
                            }
                        }
                    ],
                    "networks": [
                        {
                            "id": "mwAoy3XdmkWSbEKQ",
                            "name": "app_network",
                            "up_for_creation": False,
                            "up_for_deletion": False,
                            "deletable": True
                        }
                    ],
                    "blueprint": {
                        "applications": [
                            {
                                "name": "MyApp",
                                "image": "nginx",
                                "domain": "app.local.com",
                                "ssl": False,
                                "replicas": 1,
                                "env": {"key": "value"}
                            }
                        ]
                    },
                    "system_stats": {
                        "ram_usage": "8.0GB / 16GB",
                        "cpu_usage_percent": "5.0",
                        "ram_usage_percent": "50.0",
                        "number_of_cores": 8,
                        "number_of_threads": 4
                    }
                }
            }
        }
    }
}
