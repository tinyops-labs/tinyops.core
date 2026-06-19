SETTINGS_RESPONSES = {
    "get": {
        200: {
            "description": "SSH public key and internal database snapshot",
            "content": {
                "application/json": {
                    "example": {
                        "ssh_public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC8xnnEIRTFxXcmjpkpkpY1eM+iCxQctmb0W/vKtQWg/Yt7UvKgPwC",
                        "database": {}
                    }
                }
            }
        }
    }
}
