"""Minimal loopback Streamable-HTTP MCP client, standard library only.
Default: initialize + tools/list. Optional query requires operator-reviewed tool.
Does not start a server, open an IDB, attach a debugger, or execute arbitrary code.
Not a complete MCP client: no auth/OAuth, stdio, legacy SSE, elicitation or retries.
"""
import argparse
import ipaddress
import json
import urllib.parse
import urllib.request

MAX_BODY = 8 * 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Redirect refused; verify the local MCP endpoint")


def validate_url(url):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "http" or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("Use an HTTP loopback literal URL without credentials/query/fragment")
    try:
        address = ipaddress.ip_address(parts.hostname or "")
    except ValueError as exc:
        raise ValueError("Use 127.0.0.1 or [::1], not a DNS hostname") from exc
    if not address.is_loopback:
        raise ValueError("Remote/non-loopback server refused")
    return url


def decode_response(payload, expected_id):
    text = payload.decode("utf-8")
    try:
        messages = [json.loads(text)]
    except json.JSONDecodeError:
        # Minimal finite SSE response handling; notifications do not satisfy request.
        messages, data = [], []
        for line in (text + "\n\n").splitlines():
            if not line and data:
                messages.append(json.loads("\n".join(data)))
                data = []
            elif line.startswith("data:"):
                data.append(line[5:].lstrip())
    for message in messages:
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            raise RuntimeError("Invalid JSON-RPC 2.0 envelope")
        if "id" not in message:
            if not isinstance(message.get("method"), str) or "result" in message or "error" in message:
                raise RuntimeError("Invalid JSON-RPC notification")
            continue
        response_id = message["id"]
        if type(response_id) not in (int, str):
            raise RuntimeError("Invalid JSON-RPC response ID")
        if ("result" in message) == ("error" in message) or "method" in message:
            raise RuntimeError("Response must contain exactly one result or error")
        if "error" in message:
            error = message["error"]
            if not isinstance(error, dict) or type(error.get("code")) is not int or not isinstance(error.get("message"), str):
                raise RuntimeError("Invalid JSON-RPC error")
        if type(response_id) is type(expected_id) and response_id == expected_id:
            if "error" in message:
                raise RuntimeError("MCP error: " + json.dumps(message["error"]))
            return message["result"]
    raise RuntimeError("No matching JSON-RPC response")


class Client:
    def __init__(self, url):
        self.url, self.session, self.version, self.serial = validate_url(url), None, None, 0
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def send(self, method, params=None, notification=False):
        self.serial += 1
        message = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        if not notification:
            message["id"] = self.serial
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        if self.version:
            headers["MCP-Protocol-Version"] = self.version
        request = urllib.request.Request(self.url, json.dumps(message).encode(), headers, method="POST")
        with self.opener.open(request, timeout=30) as response:
            session = response.headers.get("Mcp-Session-Id")
            if session:
                self.session = session
            payload = response.read(MAX_BODY + 1)
        if len(payload) > MAX_BODY:
            raise RuntimeError("Response exceeded 8 MiB; narrow/page query")
        if notification:
            return None
        return decode_response(payload, self.serial)

    def initialize(self):
        result = self.send("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
            "clientInfo": {"name": "skillforge-ida-read-example", "version": "1.0"}})
        self.version = result.get("protocolVersion")
        if self.version != "2025-03-26":
            raise RuntimeError("Unsupported negotiated protocol version; use a compatible MCP client")
        self.send("notifications/initialized", notification=True)
        return result

    def tools(self):
        # Explicitly bounded discovery; more pages mean no query until full discovery.
        result = self.send("tools/list", {})
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Verified installed adapter endpoint, e.g. http://127.0.0.1:13337/mcp")
    parser.add_argument("--tool", help="Exact reviewed read-only function query tool from tools/list")
    parser.add_argument("--arguments", default="{}", help="JSON matching the discovered tool schema")
    parser.add_argument("--read-only-reviewed", action="store_true")
    args = parser.parse_args()
    client = Client(args.url)
    handshake, discovered = client.initialize(), client.tools()
    if not args.tool:
        print(json.dumps({"initialize": handshake, "tools": discovered}, ensure_ascii=False, indent=2))
        return
    # Restrict to known query-tool families; no Python/eval/execute/mutation tools.
    allowed = {"lookup_funcs", "list_funcs", "get_function_by_address", "get_function_by_name"}
    if not args.read_only_reviewed or args.tool not in allowed:
        raise RuntimeError("Only reviewed function-query tool families are allowed; arbitrary/code-mode tools refused")
    if discovered.get("nextCursor"):
        raise RuntimeError("Tool listing has more pages; use a full MCP client to complete discovery")
    tools = {tool["name"]: tool for tool in discovered.get("tools", [])}
    if args.tool not in tools:
        raise RuntimeError("Tool not advertised by this adapter; do not guess a replacement")
    arguments = json.loads(args.arguments)
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be an object")
    result = client.send("tools/call", {"name": args.tool, "arguments": arguments})
    print(json.dumps({"server": handshake.get("serverInfo"), "tool": args.tool,
                      "arguments": arguments, "result": result}, ensure_ascii=False, indent=2))
    if result.get("isError"):
        raise RuntimeError("Tool reported isError; inspect result, do not blindly retry")


if __name__ == "__main__":
    main()
