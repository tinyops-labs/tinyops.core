SYSTEM_RESPONSES = {
    "version": {
        200: {
            "description": "Application version from .version file",
            "content": {
                "application/json": {
                    "example": {"version": "1.0.0"}
                }
            }
        }
    },
    "db": {
        200: {
            "description": "Database dump",
            "content": {
                "application/json": {
                    "example": {}
                }
            }
        }
    },
    "logs": {
        200: {
            "description": "System logs (last N lines)",
            "content": {
                "application/json": {
                    "example": [
                        "2026-03-15 13:19:26 |     INFO | TinyOps Logger initialized",
                        "2026-03-15 13:19:26 |     INFO | Starting TinyOps REST API...",
                        "2026-03-15 13:19:26 |     INFO | TinyOps REST API running at http://0.0.0.0:5000"
                    ]
                }
            }
        }
    },
    "public_key": {
        200: {
            "description": "SSH public key",
            "content": {
                "application/json": {
                    "example": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC8xnnEIRTFxXcmjpkpkpY1eM+iCxQctmb0W/vKtQWg/Yt7UvKgPwC"
                }
            }
        }
    }
}
