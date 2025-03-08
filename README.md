# Model Context Protocol server for Zotero

This project is a python server that implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) for [Zotero](https://www.zotero.org/), giving you access to your Zotero library within AI assistants. It is intended to implement a small but maximally useful set of interactions with Zotero for use with [MCP clients](https://modelcontextprotocol.io/clients).

## Features

This MCP server provides the following tools:

- `zotero_search_items`: Search for items in your Zotero library using a text query
- `zotero_item_metadata`: Get detailed metadata information about a specific Zotero item
- `zotero_item_fulltext`: Get the full text of a specific Zotero item (i.e. PDF contents)

These can be discovered and accessed through any MCP client or through the [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector).

Each tool returns formatted text containing relevant information from your Zotero items, and AI assistants such as Claude can use them sequentially, searching for items then retrieving their metadata or text content.

## Installation

To use this with Claude Desktop, add the following to the `mcpServers` configuration:

```json
{
  "mcpServers": {
    "zotero": {
      "command": "uvx",
      "args": ["zotero-mcp"],
      "env": {
        "ZOTERO_LOCAL": "true"
      }
    }
  }
}
```

The `ZOTERO_LOCAL` setting points the plugin to the [local Zotero API](https://groups.google.com/g/zotero-dev/c/ElvHhIFAXrY/m/fA7SKKwsAgAJ) and requires Zotero 7 (or the beta version, see note below) running on the same machine as the client.

To use the Zotero Web API, you'll need to create an API key and find your Library ID (usually your User ID) in your Zotero account settings here: <https://www.zotero.org/settings/keys>

The following environment variables provide configuration options:

- `ZOTERO_LOCAL=true`: Use the local Zotero API (default: false, see note below)
- `ZOTERO_API_KEY`: Your Zotero API key (not required for the local API)
- `ZOTERO_LIBRARY_ID`: Your Zotero library ID (your user ID for user libraries, not required for the local API)
- `ZOTERO_LIBRARY_TYPE`: The type of library (user or group, default: user)

> [!IMPORTANT]
> For access to the fulltext API locally, an upcoming Zotero release is required. In the meantime you'll need to install a [Zotero Beta Build](https://www.zotero.org/support/beta_builds) for that functionality to work (as of 2025-03-07). See https://github.com/zotero/zotero/pull/5004 for more information.

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
