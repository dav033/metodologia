The independent audit T18 rejected the accepted result of this task. Fix these confirmed findings and prove each one with a test that exercises the real entry point, not only the module in isolation:
- F8 (high): Laptop text redaction misses FLOW_GATEWAY_KEY, TELEGRAM_BOT_TOKEN and GITHUB_CLIENT_SECRET assignments; snapshot/event failure text bypasses review redaction.
