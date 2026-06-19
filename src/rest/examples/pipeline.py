PIPELINE_RESPONSES = {
    "get": {
        200: {
            "description": "All pipelines",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "lSniJml117N2KWQZ",
                            "repo_name": "tinyops.ui-develop",
                            "git_key": "git@github.com:example/tinyops.ui.git#develop",
                            "git_url": "git@github.com:example/tinyops.ui.git",
                            "git_branch": "develop",
                            "directory": "/home/tinyops/repos/tinyops.ui-develop",
                            "image_name": "tinyops.ui-develop-530998cf8a3c1a1165e8dfc9e643e1517d82c708",
                            "created": "2026-04-04 12:00:00",
                            "finished": "2026-04-04 12:01:30",
                            "duration": 90.0,
                            "log": "Step 1/5 : FROM node:18-alpine\nStep 2/5 : WORKDIR /app\nSuccessfully built 3a1b2c3d4e5f",
                            "status": "success"
                        },
                        {
                            "id": "h7afh788aiwdiztabd",
                            "repo_name": "tinyops.api",
                            "git_key": "git@github.com:example/tinyops.api.git",
                            "git_url": "git@github.com:example/tinyops.api.git",
                            "git_branch": None,
                            "directory": "/home/tinyops/repos/tinyops.api",
                            "image_name": "tinyops.api-dfa318f29a1165e8dfc9e643e1517d82c708",
                            "created": "2026-04-04 12:05:00",
                            "finished": None,
                            "duration": None,
                            "log": None,
                            "status": "pending"
                        },
                        {
                            "id": "d2ga2hml117NgWQ3",
                            "repo_name": "tinyops.api-main",
                            "git_key": "git@github.com:example/tinyops.api.git#main",
                            "git_url": "git@github.com:example/tinyops.api.git",
                            "git_branch": "main",
                            "directory": "/home/tinyops/repos/tinyops.api-main",
                            "image_name": "tinyops.api-main-dfa318f29a1165e8dfc9e643e1517d82c708",
                            "created": "2026-04-04 11:50:00",
                            "finished": "2026-04-04 11:51:15",
                            "duration": 75.0,
                            "log": "Step 3/5 : RUN npm install\nERROR: failed to solve: process '/bin/sh -c npm install' did not complete successfully",
                            "status": "failed"
                        }
                    ]
                }
            }
        }
    }
}
