# File Transfer: Claude Computer → VPS

Transfer files from Claude's ephemeral computer to VPS via SSH MCP.

## Method: Base64 Pipeline

Claude's computer cannot SSH directly to VPS. Use base64 encoding as text bridge.

## Steps

### 1. Create/locate file on Claude's computer

```bash
# Claude's computer (bash_tool)
echo "content" > /home/claude/myfile.md
```
### 2. Base64 encode the file

```bash
# Claude's computer (bash_tool)
base64 /home/claude/myfile.md
# Output: SGVsbG8gV29ybGQK...
```

### 3. Send to VPS via SSH MCP

```bash
# VPS (SSH MCP exec)
echo 'BASE64_STRING_HERE' | base64 -d > /path/to/destination.md
```

### 4. Verify transfer

```bash
# VPS (SSH MCP exec)
cat /path/to/destination.md
```

## Complete Example

```
# Step 1: Create file (bash_tool on Claude's computer)
echo "Hello World" > /home/claude/test.txt

# Step 2: Encode (bash_tool)
base64 /home/claude/test.txt
# Returns: SGVsbG8gV29ybGQK

# Step 3: Transfer (SSH MCP exec on VPS)
echo 'SGVsbG8gV29ybGQK' | base64 -d > /root/test.txt

# Step 4: Verify (SSH MCP exec)
cat /root/test.txt
# Output: Hello World
```

## Architecture

```
Claude Computer          SSH MCP            VPS
/home/claude/    →    base64 text    →    /root/
   (source)          (transport)        (destination)
```

## Limitations

| Constraint | Limit | Workaround |
|------------|-------|------------|
| Command length | ~1000 chars | Chunk large files |
| File size | ~750 bytes/cmd | Multiple transfers |
| Binary files | Works | base64 handles binary |

## Large Files (Chunking)

For files >750 bytes, split into chunks:

```bash
# Claude's computer - split base64 into chunks
base64 /home/claude/large.md | fold -w 500 > /home/claude/chunks.txt

# Read each chunk, append on VPS
# Chunk 1:
echo 'CHUNK1...' >> /root/large.b64
# Chunk 2:
echo 'CHUNK2...' >> /root/large.b64
# ...

# VPS - decode combined file
base64 -d /root/large.b64 > /root/large.md
```

## Tips

1. **Always verify** - `cat` the file after transfer
2. **Use single quotes** - Prevents shell interpretation of base64
3. **Check file size first** - `wc -c /home/claude/file`
4. **Binary works** - Images, PDFs transfer fine via base64
5. **Append mode** - Use `>>` for chunked transfers

## Reverse: VPS → Claude Computer

```bash
# VPS (SSH MCP exec) - encode file
base64 /root/file.md
# Copy the output

# Claude's computer (bash_tool) - decode
echo 'BASE64_OUTPUT' | base64 -d > /home/claude/file.md
```
