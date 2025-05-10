from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from zotero_mcp.client import get_attachment_details, get_zotero_client

# Create an MCP server
mcp = FastMCP("Zotero")


def format_item(item: dict[str, Any]) -> str:
    """Format a Zotero item's metadata as a readable string optimized for LLM consumption"""
    data = item["data"]
    item_key = item["key"]
    item_type = data.get("itemType", "unknown")

    # Special handling for notes
    if item_type == "note":
        # Get note content
        note_content = data.get("note", "")
        # Strip HTML tags for cleaner text (simple approach)
        note_content = (
            note_content.replace("<p>", "").replace("</p>", "\n").replace("<br>", "\n")
        )
        note_content = note_content.replace("<strong>", "**").replace("</strong>", "**")
        note_content = note_content.replace("<em>", "*").replace("</em>", "*")

        # Format note with clear sections
        formatted = [
            "## 📝 Note",
            f"Item Key: `{item_key}`",
        ]

        # Add parent item reference if available
        if parent_item := data.get("parentItem"):
            formatted.append(f"Parent Item: `{parent_item}`")

        # Add date if available
        if date := data.get("dateModified"):
            formatted.append(f"Last Modified: {date}")

        # Add tags with formatting for better visibility
        if tags := data.get("tags"):
            tag_list = [f"`{tag['tag']}`" for tag in tags]
            formatted.append(f"\n### Tags\n{', '.join(tag_list)}")

        # Add note content
        formatted.append(f"\n### Note Content\n{note_content}")

        return "\n".join(formatted)

    # Regular item handling (non-notes)

    # Basic metadata with key for easy reference
    formatted = [
        f"## {data.get('title', 'Untitled')}",
        f"Item Key: `{item_key}`",
        f"Type: {item_type}",
        f"Date: {data.get('date', 'No date')}",
    ]

    # Creators with role differentiation
    creators_by_role = {}
    for creator in data.get("creators", []):
        role = creator.get("creatorType", "contributor")
        name = ""
        if "firstName" in creator and "lastName" in creator:
            name = f"{creator['lastName']}, {creator['firstName']}"
        elif "name" in creator:
            name = creator["name"]

        if name:
            if role not in creators_by_role:
                creators_by_role[role] = []
            creators_by_role[role].append(name)

    for role, names in creators_by_role.items():
        role_display = role.capitalize() + ("s" if len(names) > 1 else "")
        formatted.append(f"{role_display}: {'; '.join(names)}")

    # Publication details
    if publication := data.get("publicationTitle"):
        formatted.append(f"Publication: {publication}")
    if volume := data.get("volume"):
        volume_info = f"Volume: {volume}"
        if issue := data.get("issue"):
            volume_info += f", Issue: {issue}"
        if pages := data.get("pages"):
            volume_info += f", Pages: {pages}"
        formatted.append(volume_info)

    # Abstract with clear section header
    if abstract := data.get("abstractNote"):
        formatted.append(f"\n### Abstract\n{abstract}")

    # Tags with formatting for better visibility
    if tags := data.get("tags"):
        tag_list = [f"`{tag['tag']}`" for tag in tags]
        formatted.append(f"\n### Tags\n{', '.join(tag_list)}")

    # URLs, DOIs, and identifiers grouped together
    identifiers = []
    if url := data.get("url"):
        identifiers.append(f"URL: {url}")
    if doi := data.get("DOI"):
        identifiers.append(f"DOI: {doi}")
    if isbn := data.get("ISBN"):
        identifiers.append(f"ISBN: {isbn}")
    if issn := data.get("ISSN"):
        identifiers.append(f"ISSN: {issn}")

    if identifiers:
        formatted.append("\n### Identifiers\n" + "\n".join(identifiers))

    # Notes and attachments
    if notes := item.get("meta", {}).get("numChildren", 0):
        formatted.append(
            f"\n### Additional Information\nNumber of notes/attachments: {notes}"
        )

    return "\n".join(formatted)


@mcp.tool(
    name="zotero_item_metadata",
    description="Get metadata information about a specific Zotero item, given the item key.",
)
def get_item_metadata(item_key: str) -> str:
    """Get metadata information about a specific Zotero item"""
    zot = get_zotero_client()

    try:
        item: Any = zot.item(item_key)
        if not item:
            return f"No item found with key: {item_key}"
        return format_item(item)
    except Exception as e:
        return f"Error retrieving item metadata: {str(e)}"


@mcp.tool(
    name="zotero_item_fulltext",
    description="Get the full text content of a Zotero item, given the item key of a parent item or specific attachment.",
)
def get_item_fulltext(item_key: str) -> str:
    """Get the full text content of a specific Zotero item"""
    zot = get_zotero_client()

    try:
        item: Any = zot.item(item_key)
        if not item:
            return f"No item found with key: {item_key}"

        # Fetch full-text content
        attachment = get_attachment_details(zot, item)

        # Prepare header with metadata
        header = format_item(item)

        # Add attachment information
        if attachment is not None:
            attachment_info = f"\n## Attachment Information\n- **Key**: `{attachment.key}`\n- **Type**: {attachment.content_type}"

            # Get the full text
            full_text_data: Any = zot.fulltext_item(attachment.key)
            if full_text_data and "content" in full_text_data:
                item_text = full_text_data["content"]
                # Calculate approximate word count
                word_count = len(item_text.split())
                attachment_info += f"\n- **Word Count**: ~{word_count}"

                # Format the content with markdown for structure
                full_text = f"\n\n## Document Content\n\n{item_text}"
            else:
                # Clear error message when text extraction isn't possible
                full_text = "\n\n## Document Content\n\n[⚠️ Attachment is available but text extraction is not possible. The document may be scanned as images or have other restrictions that prevent text extraction.]"
        else:
            attachment_info = "\n\n## Attachment Information\n[❌ No suitable attachment found for full text extraction. This item may not have any attached files or they may not be in a supported format.]"
            full_text = ""

        # Combine all sections
        return f"{header}{attachment_info}{full_text}"

    except Exception as e:
        return f"Error retrieving item full text: {str(e)}"


@mcp.tool(
    name="zotero_search_items",
    # More detail can be added if useful: https://www.zotero.org/support/dev/web_api/v3/basics#searching
    description="Search for items in your Zotero library, given a query string, query mode (titleCreatorYear or everything), and optional tag search (supports boolean searches). Returned results can be looked up with zotero_item_fulltext or zotero_item_metadata.",
)
def search_items(
    query: str,
    qmode: Literal["titleCreatorYear", "everything"] | None = "titleCreatorYear",
    tag: str | None = None,
    limit: int | None = 10,
) -> str:
    """Search for items in your Zotero library"""
    zot = get_zotero_client()

    # Search using the q parameter
    params = {"q": query, "qmode": qmode, "limit": limit}
    if tag:
        params["tag"] = tag

    zot.add_parameters(**params)
    # n.b. types for this return do not work, it's a parsed JSON object
    results: Any = zot.items()

    if not results:
        return "No items found matching your query."

    # Header with search info
    header = [
        f"# Search Results for: '{query}'",
        f"Found {len(results)} items." + (f" Using tag filter: {tag}" if tag else ""),
        "Use item keys with zotero_item_metadata or zotero_item_fulltext for more details.\n",
    ]

    # Format results
    formatted_results = []
    for i, item in enumerate(results):
        data = item["data"]
        item_key = item.get("key", "")
        item_type = data.get("itemType", "unknown")

        # Special handling for notes
        if item_type == "note":
            # Get note content
            note_content = data.get("note", "")
            # Strip HTML tags for cleaner text (simple approach)
            note_content = (
                note_content.replace("<p>", "")
                .replace("</p>", "\n")
                .replace("<br>", "\n")
            )
            note_content = note_content.replace("<strong>", "**").replace(
                "</strong>", "**"
            )
            note_content = note_content.replace("<em>", "*").replace("</em>", "*")

            # Extract a title from the first line if possible, otherwise use first few words
            title_preview = ""
            if note_content:
                lines = note_content.strip().split("\n")
                first_line = lines[0].strip()
                if first_line:
                    # Use first line if it's reasonably short, otherwise use first few words
                    if len(first_line) <= 50:
                        title_preview = first_line
                    else:
                        words = first_line.split()
                        title_preview = " ".join(words[:5]) + "..."

            # Create a good title for the note
            note_title = title_preview if title_preview else "Note"

            # Get a preview of the note content (truncated)
            preview = note_content.strip()
            if len(preview) > 150:
                preview = preview[:147] + "..."

            # Format the note entry
            entry = [
                f"## {i + 1}. 📝 {note_title}",
                f"**Type**: Note | **Key**: `{item_key}`",
                f"\n{preview}",
            ]

            # Add parent item reference if available
            if parent_item := data.get("parentItem"):
                entry.insert(2, f"**Parent Item**: `{parent_item}`")

            # Add tags if present (limited to first 5)
            if tags := data.get("tags"):
                tag_list = [f"`{tag['tag']}`" for tag in tags[:5]]
                if len(tags) > 5:
                    tag_list.append("...")
                entry.append(f"\n**Tags**: {' '.join(tag_list)}")

            formatted_results.append("\n".join(entry))
            continue

        # Regular item processing (non-notes)
        title = data.get("title", "Untitled")
        date = data.get("date", "")

        # Format primary creators (limited to first 3)
        creators = []
        for creator in data.get("creators", [])[:3]:
            if "firstName" in creator and "lastName" in creator:
                creators.append(f"{creator['lastName']}, {creator['firstName']}")
            elif "name" in creator:
                creators.append(creator["name"])

        if len(data.get("creators", [])) > 3:
            creators.append("et al.")

        creator_str = "; ".join(creators) if creators else "No authors"

        # Get publication or source info
        source = ""
        if pub := data.get("publicationTitle"):
            source = pub
        elif book := data.get("bookTitle"):
            source = f"In: {book}"
        elif publisher := data.get("publisher"):
            source = f"{publisher}"

        # Get a brief abstract (truncated if too long)
        abstract = data.get("abstractNote", "")
        if len(abstract) > 150:
            abstract = abstract[:147] + "..."

        # Build formatted entry with markdown for better structure
        entry = [
            f"## {i + 1}. {title}",
            f"**Type**: {item_type} | **Date**: {date} | **Key**: `{item_key}`",
            f"**Authors**: {creator_str}",
        ]

        if source:
            entry.append(f"**Source**: {source}")

        if abstract:
            entry.append(f"\n{abstract}")

        # Add tags if present (limited to first 5)
        if tags := data.get("tags"):
            tag_list = [f"`{tag['tag']}`" for tag in tags[:5]]
            if len(tags) > 5:
                tag_list.append("...")
            entry.append(f"\n**Tags**: {' '.join(tag_list)}")

        formatted_results.append("\n".join(entry))

    return "\n\n".join(header + formatted_results)

@mcp.tool(
    name="zotero_add_collection",
    description="Create a new collection (folder) in Zotero. Returns the collection key if successful.",
)
def add_collection(
    name: str, 
    parent_collection: str | None = None
) -> str:
    """Create a new Zotero collection with optional parent collection"""
    zot = get_zotero_client()
    
    try:
        collection_data = {
            "name": name,
            "parentCollection": parent_collection if parent_collection else False
        }
        
        # 创建分类
        response = zot.create_collections([collection_data])
        if response and response.get("success", {}).get("0"):
            collection_key = response["success"]["0"]
            return f"✅ Collection created successfully! Key: `{collection_key}`"
        else:
            return "❌ Failed to create collection. Check if the parent collection exists."
            
    except Exception as e:
        return f"🚨 Error creating collection: {str(e)}"


@mcp.tool(
    name="zotero_add_item_by_doi",
    description="Add a new item to Zotero by DOI. Automatically fetches metadata. Returns the item key and title if successful.",
)
def add_item_from_doi(
    doi: str,
    collection_key: str | None = None
) -> str:
    """Add an item to Zotero using DOI, optionally assign to a collection"""
    zot = get_zotero_client()
    
    try:
        # 通过DOI创建条目
        new_items = zot.create_items([{
            "itemType": "journalArticle",
            "DOI": doi
        }], via_doi=True)
        
        if not new_items:
            return "❌ No item was created. Check if the DOI is valid."
        
        item = new_items[0]
        item_key = item["key"]
        title = item["data"].get("title", "Untitled")
        
        # 添加到指定分类（如果提供）
        if collection_key:
            zot.addto_collection(collection_key, [item_key])
            return f"✅ Added to collection! Item: **{title}** (Key: `{item_key}`)"
            
        return f"✅ Item added: **{title}** (Key: `{item_key}`)"
        
    except Exception as e:
        return f"🚨 Error adding item: {str(e)}"
    
    
    
@mcp.tool(
    name="zotero_add_subcollection",
    description="Create a new subcollection (nested folder) under a parent collection in Zotero. "
               "Returns the subcollection key if successful. Parent collection can be specified by name or key.",
)
def add_subcollection(
    parent_identifier: str,  # 父分类名称或Key
    subcollection_name: str,
    create_parent_if_missing: bool = False  # 若父分类不存在，是否自动创建
) -> str:
    """Create a nested subcollection in Zotero"""
    zot = get_zotero_client()
    
    try:
        # Step 1: 解析父分类（通过Key或名称查找）
        parent_key = None
        
        # 情况1：直接提供父分类Key（格式如 'ABCD1234'）
        if len(parent_identifier) == 8 and parent_identifier.isalnum():
            try:
                parent = zot.collection(parent_identifier)
                if parent:
                    parent_key = parent_identifier
            except:
                pass
        
        # 情况2：通过父分类名称查找
        if not parent_key:
            all_collections = zot.collections()
            parent_candidates = [
                coll for coll in all_collections 
                if coll["data"]["name"].lower() == parent_identifier.lower()
            ]
            
            if parent_candidates:
                parent_key = parent_candidates[0]["key"]
            elif create_parent_if_missing:
                # 自动创建父分类
                parent_resp = zot.create_collections([{"name": parent_identifier}])
                if parent_resp.get("success", {}).get("0"):
                    parent_key = parent_resp["success"]["0"]
                else:
                    return "❌ Failed to auto-create parent collection"
            else:
                return f"❌ Parent collection not found: '{parent_identifier}'"

        # Step 2: 创建子分类
        subcollection_data = {
            "name": subcollection_name,
            "parentCollection": parent_key
        }
        
        response = zot.create_collections([subcollection_data])
        if response and response.get("success", {}).get("0"):
            subcollection_key = response["success"]["0"]
            return (
                f"✅ Subcollection created under '{parent_identifier}'\n"
                f"• Name: {subcollection_name}\n"
                f"• Key: `{subcollection_key}`"
            )
        else:
            return "❌ Failed to create subcollection (check permissions)"
            
    except Exception as e:
        return f"🚨 Error: {str(e)}"
    
@mcp.tool(
    name="zotero_add_tags_to_item",
    description="Add one or multiple tags to a Zotero item. Supports checking for existing tags to avoid duplicates.",
)
def add_tags_to_item(
    item_key: str,
    tags: list[str],
    skip_duplicates: bool = True  # 是否跳过已存在的标签
) -> str:
    """Add tags to a specific Zotero item"""
    zot = get_zotero_client()
    
    try:
        # Step 1: 获取目标条目
        item = zot.item(item_key)
        if not item:
            return f"❌ Item not found with key: {item_key}"
        
        # Step 2: 准备新标签列表
        existing_tags = {tag["tag"].lower() for tag in item["data"].get("tags", [])}
        new_tags = []
        
        for tag in tags:
            tag_lower = tag.lower()
            if skip_duplicates and tag_lower in existing_tags:
                continue
            new_tags.append({"tag": tag})
            existing_tags.add(tag_lower)  # 避免同批次内重复
        
        if not new_tags:
            return f"ℹ️ All tags already exist for item: {item_key}"
        
        # Step 3: 更新条目数据
        item["data"]["tags"] = item["data"].get("tags", []) + new_tags
        zot.update_item(item)
        
        # Step 4: 返回操作结果
        added_tags = [tag["tag"] for tag in new_tags]
        return (
            f"✅ Added {len(added_tags)} tag(s) to item `{item_key}`:\n"
            f"- {', '.join(added_tags)}\n"
            f"Total tags now: {len(item['data']['tags'])}"
        )
        
    except Exception as e:
        return f"🚨 Error: {str(e)}"


@mcp.tool(
    name="zotero_add_pdf_attachment",
    description="Attach a PDF file to a Zotero item. Supports both local file paths and URLs.",
)
def add_pdf_attachment(
    item_key: str,
    file_source: str,  # 本地文件路径或URL
    attachment_type: Literal["imported_file", "imported_url"] = "imported_file",
    rename_file: str = None  # 自定义附件显示名称（可选）
) -> str:
    """Add PDF attachment to a Zotero item"""
    zot = get_zotero_client()
    
    try:
        # Step 1: 验证目标条目是否存在
        item = zot.item(item_key)
        if not item:
            return f"❌ Target item not found: {item_key}"

        # Step 2: 准备附件数据模板
        attachment_template = {
            "itemType": "attachment",
            "parentItem": item_key,
            "linkMode": attachment_type,
            "title": rename_file or os.path.basename(file_source)
        }

        # Step 3: 根据来源类型处理附件
        if attachment_type == "imported_file":
            # 本地文件上传
            if not os.path.exists(file_source):
                return f"❌ File not found: {file_source}"
            
            if not file_source.lower().endswith('.pdf'):
                return "❌ Only PDF files are supported"
            
            with open(file_source, 'rb') as f:
                attachment = zot.attachment_simple(
                    [attachment_template],
                    f,
                    mimeType='application/pdf'
                )
        elif attachment_type == "imported_url":
            # 从URL抓取PDF
            if not file_source.startswith(('http://', 'https://')):
                return "❌ Invalid URL format"
            
            attachment_template['url'] = file_source
            attachment = zot.create_items([attachment_template])
        else:
            return "❌ Invalid attachment type"

        # Step 4: 验证结果
        if attachment and attachment.get('success', {}).get('0'):
            attachment_key = attachment['success']['0']
            return (
                f"✅ PDF attached to item `{item_key}`\n"
                f"• Attachment key: `{attachment_key}`\n"
                f"• Title: {attachment_template['title']}"
            )
        else:
            return "❌ Failed to add attachment (check API permissions)"
            
    except Exception as e:
        return f"🚨 Error: {str(e)}"
    
    
@mcp.tool(
    name="zotero_add_pdf_by_doi",
    description="Automatically find and attach a PDF to an item using its DOI.",
)
def add_pdf_by_doi(item_key: str, doi: str) -> str:
    """Try to fetch PDF via DOI and attach to item"""
    zot = get_zotero_client()
    
    try:
        # Step 1: 通过DOI获取PDF URL（示例使用Crossref）
        import requests
        crossref_url = f"https://api.crossref.org/works/{doi}"
        response = requests.get(crossref_url)
        
        if response.status_code != 200:
            return "❌ Failed to resolve DOI"
            
        pdf_url = None
        for link in response.json()['message'].get('link', []):
            if link.get('content-type') == 'application/pdf':
                pdf_url = link['URL']
                break
        
        if not pdf_url:
            return "ℹ️ No PDF link found for this DOI"
        
        # Step 2: 添加URL附件
        return add_pdf_attachment(
            item_key=item_key,
            file_source=pdf_url,
            attachment_type="imported_url",
            rename_file=f"Full Text - {doi}"
        )
        
    except Exception as e:
        return f"🚨 Error: {str(e)}"
    
    
@mcp.tool(
    name="zotero_add_item_to_collection",
    description="Add an existing item to additional collections without removing it from current collections.",
)
def add_item_to_collection(
    item_key: str,
    collection_keys: list[str]  # 支持同时添加到多个分类
) -> str:
    """Add an item to one or more collections while preserving existing collections"""
    zot = get_zotero_client()
    
    try:
        # Step 1: 获取目标条目
        item = zot.item(item_key)
        if not item:
            return f"❌ Item not found: {item_key}"

        # Step 2: 获取当前已关联的分类
        current_collections = set(item["data"].get("collections", []))
        
        # Step 3: 验证目标分类是否存在
        valid_collections = set()
        for coll_key in collection_keys:
            if zot.collection(coll_key):
                valid_collections.add(coll_key)
            else:
                return f"❌ Collection not found: {coll_key}"

        # Step 4: 合并新旧分类（去重）
        updated_collections = list(current_collections.union(valid_collections))
        
        # Step 5: 更新条目数据
        item["data"]["collections"] = updated_collections
        zot.update_item(item)
        
        # Step 6: 返回操作结果
        return (
            f"✅ Added item `{item_key}` to {len(valid_collections)} collection(s)\n"
            f"- New collections: {', '.join(valid_collections)}\n"
            f"- Total collections now: {len(updated_collections)}"
        )
        
    except Exception as e:
        return f"🚨 Error: {str(e)}"
    
    
@mcp.tool(
    name="zotero_add_related_item",
    description="Link two Zotero items as related works. Supports both one-way and bidirectional linking.",
)
def add_related_item(
    source_item_key: str,
    target_item_key: str,
    bidirectional: bool = True  # 是否双向关联
) -> str:
    """Add a relationship between two Zotero items"""
    zot = get_zotero_client()
    
    try:
        # Step 1: 获取源条目和目标条目
        source_item = zot.item(source_item_key)
        target_item = zot.item(target_item_key)
        
        if not source_item:
            return f"❌ Source item not found: {source_item_key}"
        if not target_item:
            return f"❌ Target item not found: {target_item_key}"

        # Step 2: 准备关联数据
        def update_relations(item, related_key, action="add"):
            relations = item["data"].get("relations", {})
            related_items = set(relations.get("dc:relation", []))
            
            if action == "add":
                related_items.add(related_key)
            elif action == "remove":
                related_items.discard(related_key)
                
            relations["dc:relation"] = list(related_items)
            item["data"]["relations"] = relations
            return item

        # Step 3: 更新源条目
        source_item = update_relations(source_item, target_item_key)
        zot.update_item(source_item)
        
        # Step 4: 双向关联（可选）
        if bidirectional:
            target_item = update_relations(target_item, source_item_key)
            zot.update_item(target_item)
            relation_type = "bidirectional"
        else:
            relation_type = "one-way"

        # Step 5: 返回结果
        return (
            f"✅ Successfully linked items ({relation_type}):\n"
            f"- Source: `{source_item_key}` → Target: `{target_item_key}`\n"
            f"- Relations now include: {len(source_item['data']['relations'].get('dc:relation', []))} links"
        )
        
    except Exception as e:
        return f"🚨 Error: {str(e)}"
    
    
@mcp.tool(
    name="zotero_restore_deleted_item",
    description="Restore a deleted item from Zotero trash. Requires the item's unique key.",
)
def restore_deleted_item(
    item_key: str,
    restore_attachments: bool = True  # 是否同时恢复关联的附件/笔记
) -> str:
    """Restore a deleted item and optionally its children"""
    zot = get_zotero_client()
    
    try:
        # Step 1: 检查条目是否在回收站中
        trash_items = zot.deleted_items(since=0, item_type="trash")
        if item_key not in [item["key"] for item in trash_items["items"]]:
            return f"❌ Item not found in trash: {item_key}"

        # Step 2: 恢复主条目
        restore_payload = {
            "items": [item_key],
            "collections": [],
            "searches": [],
            "tags": [],
            "relations": []
        }
        
        if restore_attachments:
            # 获取条目下的所有子项（附件/笔记）
            children = zot.children(item_key)
            restore_payload["items"].extend([child["key"] for child in children])

        # Step 3: 发送恢复请求
        response = zot._request(
            "POST", 
            f"{zot.endpoint}users/{zot.user_id}/restore",
            json=restore_payload,
            headers={"Zotero-API-Version": "3"}
        )
        
        if response.status_code != 204:
            return f"❌ Restoration failed (HTTP {response.status_code})"

        # Step 4: 验证恢复结果
        restored_item = zot.item(item_key)
        if restored_item and restored_item["data"]["deleted"] == 0:
            return (
                f"✅ Successfully restored item `{item_key}`\n"
                f"- Restored attachments/notes: {len(restore_payload['items']) - 1}"
            )
        else:
            return "❌ Item still marked as deleted (check library sync status)"
            
    except Exception as e:
        return f"🚨 Error: {str(e)}"