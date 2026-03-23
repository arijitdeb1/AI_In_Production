
### Postgres database as a MCP server 

1. Refer [postgres-demo.py](./postgres-demo.py) for the code implementation
2. Provide required DB credentials to above.
3. Add below to VS Code `mcp.json` configuration
   ```json
   {
	"servers": {
		"postgres-server": {
			"command": "uv",
			"args": [
				"--directory",
				"C:\\Users\\223017934\\OneDrive - GE HealthCare\\Documents\\GE-Confidential\\AI-Utilities\\DB-MCP",
				"run",
				"postgres-demo.py"
			],
			"type": "stdio"
		}			
   }
   ```
