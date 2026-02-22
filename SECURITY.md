# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of WeMo MCP Server seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please Do Not

- **Do not** open a public GitHub issue for security vulnerabilities
- **Do not** disclose the vulnerability publicly until it has been addressed

### Please Do

1. **Report via GitHub Security Advisory**
   - Go to: https://github.com/apiarya/wemo-mcp-server/security/advisories/new
   - Provide a detailed description of the vulnerability
   - Include steps to reproduce if possible

2. **Or email directly**
   - Send details to: izzasnvyp7@privaterelay.appleid.com
   - Use subject line: `[SECURITY] WeMo MCP Server Vulnerability`
   - Include as much information as possible:
     - Type of vulnerability
     - Full paths of affected source files (if known)
     - Location of the affected code
     - Any special configuration required to reproduce
     - Step-by-step instructions to reproduce
     - Proof-of-concept or exploit code (if available)
     - Impact of the vulnerability

### What to Expect

- **Acknowledgment**: Within 48 hours of your report
- **Initial Assessment**: Within 1 week
- **Status Updates**: Every 7 days until resolution
- **Fix Timeline**: Critical vulnerabilities within 7 days, others within 30 days
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Update Process

When a security vulnerability is confirmed:

1. **Patch Development**: We will develop a fix
2. **Testing**: The fix will be tested thoroughly
3. **Release**: A new version will be published to PyPI
4. **Advisory**: A GitHub Security Advisory will be published
5. **Notification**: All users will be notified via:
   - GitHub Security Advisories
   - Release notes
   - CHANGELOG.md

## Security Best Practices for Users

### Installation

```bash
# Always install from trusted sources
pip install wemo-mcp-server

# Or use uvx for isolated execution
uvx wemo-mcp-server
```

### Network Security

- **Firewall**: Ensure your network firewall is properly configured
- **Local Network Only**: WeMo devices should only be accessible on your local network
- **No Port Forwarding**: Never expose WeMo device ports to the internet
- **Subnet Isolation**: Consider network segmentation for IoT devices

### Configuration Security

- **MCP Client Config**: Ensure your MCP client configuration files have appropriate permissions
  ```bash
  chmod 600 ~/.vscode/mcp.json
  chmod 600 "~/Library/Application Support/Claude/claude_desktop_config.json"
  ```

- **Credentials**: Never commit MCP Registry tokens or other credentials to version control
  - `.mcpregistry_github_token`
  - `.mcpregistry_registry_token`
  - These are already in `.gitignore`

### Running the Server

- **Trusted Environments**: Only run the MCP server in trusted environments
- **Keep Updated**: Always use the latest stable version
- **Monitor Logs**: Review logs for suspicious activity (stderr output)

## Known Security Considerations

### 1. Network Scanning
- The `scan_network` tool performs network scanning which may trigger IDS/IPS alerts
- Scanning is non-invasive (connection attempts only) but may be logged
- Use responsibly and only on networks you own or have permission to scan

### 2. Device Control
- The server provides direct control over WeMo devices
- Ensure only trusted users have access to the MCP client
- Consider access controls at the network level

### 3. UPnP/SSDP Discovery
- Uses UPnP/SSDP protocols which broadcast on the local network
- This is standard for WeMo device discovery
- Packets may be visible to other devices on the network

### 4. Device Credentials
- The server does not store or transmit device credentials
- WeMo devices use setup codes for HomeKit (retrieved but not stored)
- HomeKit codes should be treated as sensitive

## Security Features

### Implemented

- ✅ **Trusted Publishing**: PyPI and MCP Registry use OIDC (no long-lived tokens)
- ✅ **No Credential Storage**: Server doesn't store passwords or API keys
- ✅ **Type Safety**: Strict type hints with mypy
- ✅ **Input Validation**: All tool inputs are validated
- ✅ **Error Handling**: Comprehensive error handling prevents information leakage
- ✅ **Dependency Management**: Locked dependencies via uv.lock
- ✅ **Minimal Dependencies**: Only 3 production dependencies
- ✅ **Local Execution**: Server runs locally, no cloud services

### Planned

- ⏳ **Automated Vulnerability Scanning**: Dependabot integration
- ⏳ **Security Audit**: Third-party security audit
- ⏳ **Rate Limiting**: Protect against abuse of network scanning
- ⏳ **Audit Logging**: Enhanced logging for security events

## Responsible Disclosure

We follow responsible disclosure practices:

- We will work with security researchers to understand and fix vulnerabilities
- We will credit researchers in security advisories (with permission)
- We ask for reasonable time to fix vulnerabilities before public disclosure
- We will keep researchers informed of progress

## Security Hall of Fame

We appreciate security researchers who help keep WeMo MCP Server secure. Contributors will be listed here (with permission):

*No security vulnerabilities have been reported yet.*

## Questions?

If you have questions about this security policy, please open a discussion on GitHub:
https://github.com/apiarya/wemo-mcp-server/discussions

---

**Last Updated**: February 21, 2026
