# Model Context Protocol server for Zotero

This project is a python-based server that implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) for [Zotero](https://www.zotero.org/).

## Features

This MCP server provides the following tools:

- `zotero_search_items`: Search for items in your Zotero library using a text query
- `zotero_item_metadata`: Get detailed information about a specific Zotero item
- `zotero_item_fulltext`: Get the full text of a specific Zotero item

These can be discovered and accessed through the [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) or any other [MCP client](https://modelcontextprotocol.io/clients).

Each tool returns formatted text containing relevant information from your Zotero items.

## Installation

To use this with Claude Desktop, add the following to the `mcpServers` configuration:

```json
    "zotero": {
      "command": "uvx",
      "args": ["zotero-mcp"],
      "env": {
        "ZOTERO_LOCAL": "true"
      }
    }
```

The following environment variables are supported:

- `ZOTERO_LOCAL=true`: Use the local Zotero API (default: false) (
- `ZOTERO_LIBRARY_ID`: Your Zotero library ID (not required for the local API)
- `ZOTERO_LIBRARY_TYPE`: The type of library (user or group, default: user)
- `ZOTERO_API_KEY`: Your Zotero API key (not required for the local API)

You can find your library ID and create an API key in your Zotero account settings: https://www.zotero.org/settings/keys

The [local Zotero API](https://groups.google.com/g/zotero-dev/c/ElvHhIFAXrY/m/fA7SKKwsAgAJ) can be used with Zotero 7 running on the same machine.

> [!WARNING]
> An upcoming Zotero release is needed to support the fulltext API locally, in the meantime you'll need to install a [Zotero Beta Build](https://www.zotero.org/support/beta_builds) for that functionality to work (as of 2025-03-07). See https://github.com/zotero/zotero/pull/5004 for more information.

## Development

1. Clone this repository
1. Install dependencies with [uv](https://docs.astral.sh/uv/) by running: `uv sync`
1. Create a `.env` file in the project root with the environment variables above

Start the [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) for local development:

```bash
npx @modelcontextprotocol/inspector uv run zotero-mcp
```

### Running Tests

To run the test suite:

```bash
uv run pytest
```

## Relevant Documentation

- https://modelcontextprotocol.io/tutorials/building-mcp-with-llms
- https://github.com/modelcontextprotocol/python-sdk
- https://pyzotero.readthedocs.io/en/latest/
- https://www.zotero.org/support/dev/web_api/v3/start
