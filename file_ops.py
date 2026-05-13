"""File operations — create, move, rename, delete, list, search, archive, batch."""

import os
import re
import shutil
import zipfile

FILE_PATTERNS = [
    re.compile(r"^create (?:a )?file (?:called |named )?(.+)$", re.I),
    re.compile(r"^(?:make|touch) (?:a )?file (.+)$", re.I),
    re.compile(r"^delete (?:the )?file (.+)$", re.I),
    re.compile(r"^remove (?:the )?file (.+)$", re.I),
    re.compile(r"^move (?:the )?file (.+?) to (.+)$", re.I),
    re.compile(r"^rename (?:the )?file (.+?) to (.+)$", re.I),
    re.compile(r"^list files (?:in )?(.+)$", re.I),
    re.compile(r"^(?:show|what(?:'s| is) in) (?:the )?folder (.+)$", re.I),
    re.compile(r"^read (?:the )?file (.+)$", re.I),
    re.compile(r"^write (?:text |content )?\"(.+?)\" to (?:the )?file (.+)$", re.I),
    re.compile(r"^search for (.+?) in (.+)$", re.I),
    re.compile(r"^zip (?:the )?folder (.+?) to (.+)$", re.I),
    re.compile(r"^unzip (?:the )?file (.+?) to (.+)$", re.I),
    re.compile(r"^batch rename (?:in )?(.+?) to (.+)$", re.I),
]


def _safe_path(path_str):
    path_str = path_str.strip().strip("'\"")
    expanded = os.path.expanduser(os.path.expandvars(path_str))
    return os.path.abspath(expanded)


def write_to_file(path_str, content):
    path = _safe_path(path_str)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False


def search_files(directory, pattern):
    results = []
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if pattern.lower() in file.lower() or file.endswith(pattern.lower()):
                    results.append(os.path.join(root, file))
                    if len(results) >= 20: # Limit results
                        return results
    except Exception as e:
        pass
    return results

def zip_folder(folder_path, output_path):
    try:
        if not output_path.endswith('.zip'):
            output_path += '.zip'
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)
        return True
    except Exception:
        return False

def unzip_file(zip_path, output_dir):
    try:
        os.makedirs(output_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(output_dir)
        return True
    except Exception:
        return False

def batch_rename(directory, prefix):
    count = 0
    try:
        for i, filename in enumerate(os.listdir(directory)):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                ext = os.path.splitext(filename)[1]
                new_name = f"{prefix}_{i+1}{ext}"
                os.rename(filepath, os.path.join(directory, new_name))
                count += 1
        return count
    except Exception:
        return -1


def is_file_request(text):
    normalized = " ".join(str(text).strip().split())
    return any(p.match(normalized) for p in FILE_PATTERNS)


def handle_file_command(text):
    normalized = " ".join(str(text).strip().split())

    # Search files
    m = re.match(r"^search for (.+?) in (.+)$", normalized, re.I)
    if m:
        pattern = m.group(1).strip("'\"")
        directory = _safe_path(m.group(2))
        if not os.path.isdir(directory):
            return {"action": "file_search", "reply": f"Directory not found: {directory}"}
        res = search_files(directory, pattern)
        if res:
            return {"action": "file_search", "reply": f"Found {len(res)} matching files. Examples: " + ", ".join([os.path.basename(r) for r in res[:5]])}
        return {"action": "file_search", "reply": f"No files matching '{pattern}' found in {directory}."}

    # Zip
    m = re.match(r"^zip (?:the )?folder (.+?) to (.+)$", normalized, re.I)
    if m:
        folder = _safe_path(m.group(1))
        out_zip = _safe_path(m.group(2))
        if zip_folder(folder, out_zip):
            return {"action": "file_zip", "reply": f"Successfully zipped folder to {out_zip}"}
        return {"action": "file_zip", "reply": "Failed to create zip archive."}

    # Unzip
    m = re.match(r"^unzip (?:the )?file (.+?) to (.+)$", normalized, re.I)
    if m:
        zip_file = _safe_path(m.group(1))
        out_folder = _safe_path(m.group(2))
        if unzip_file(zip_file, out_folder):
            return {"action": "file_unzip", "reply": f"Successfully extracted archive to {out_folder}"}
        return {"action": "file_unzip", "reply": "Failed to extract archive."}

    # Batch rename
    m = re.match(r"^batch rename (?:in )?(.+?) to (.+)$", normalized, re.I)
    if m:
        directory = _safe_path(m.group(1))
        prefix = m.group(2).strip("'\"")
        count = batch_rename(directory, prefix)
        if count >= 0:
            return {"action": "file_batch_rename", "reply": f"Successfully renamed {count} files in {directory} with prefix '{prefix}'."}
        return {"action": "file_batch_rename", "reply": "Failed to batch rename files."}

    # Create
    m = re.match(r"^(?:create|make|touch) (?:a )?file (?:called |named )?(.+)$", normalized, re.I)
    if m:
        path = _safe_path(m.group(1))
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a"):
                pass
            return {"action": "file_create", "reply": f"Created file: {path}"}
        except Exception as e:
            return {"action": "file_create", "reply": f"Could not create file: {e}", "success": False, "error": str(e)}

    # Write content (Internal/Direct)
    m = re.match(r"^write (?:text |content )?\"(.+?)\" to (?:the )?file (.+)$", normalized, re.I)
    if m:
        content = m.group(1)
        path = m.group(2)
        if write_to_file(path, content):
            return {"action": "file_write", "reply": f"Written content to {path}", "success": True}
        return {"action": "file_write", "reply": f"Failed to write to {path}", "success": False, "error": "Unknown write error"}

    # Delete
    m = re.match(r"^(?:delete|remove) (?:the )?file (.+)$", normalized, re.I)
    if m:
        path = _safe_path(m.group(1))
        if not os.path.exists(path):
            return {"action": "file_delete", "reply": f"File not found: {path}"}
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return {"action": "file_delete", "reply": f"Deleted: {path}"}
        except Exception as e:
            return {"action": "file_delete", "reply": f"Could not delete: {e}", "success": False, "error": str(e)}

    # Move
    m = re.match(r"^move (?:the )?file (.+?) to (.+)$", normalized, re.I)
    if m:
        src = _safe_path(m.group(1))
        dst = _safe_path(m.group(2))
        try:
            shutil.move(src, dst)
            return {"action": "file_move", "reply": f"Moved {src} to {dst}"}
        except Exception as e:
            return {"action": "file_move", "reply": f"Could not move: {e}", "success": False, "error": str(e)}

    # Rename
    m = re.match(r"^rename (?:the )?file (.+?) to (.+)$", normalized, re.I)
    if m:
        src = _safe_path(m.group(1))
        dst = _safe_path(m.group(2))
        try:
            os.rename(src, dst)
            return {"action": "file_rename", "reply": f"Renamed to {dst}"}
        except Exception as e:
            return {"action": "file_rename", "reply": f"Could not rename: {e}", "success": False, "error": str(e)}

    # List
    m = re.match(r"^(?:list files (?:in )?|(?:show|what(?:'s| is) in) (?:the )?folder )(.+)$", normalized, re.I)
    if m:
        path = _safe_path(m.group(1))
        if not os.path.isdir(path):
            return {"action": "file_list", "reply": f"Not a directory: {path}"}
        try:
            entries = os.listdir(path)[:25]
            if not entries:
                return {"action": "file_list", "reply": f"{path} is empty."}
            listing = ", ".join(entries)
            return {"action": "file_list", "reply": f"Contents of {path}: {listing}"}
        except Exception as e:
            return {"action": "file_list", "reply": f"Could not list: {e}"}

    # Read
    m = re.match(r"^read (?:the )?file (.+)$", normalized, re.I)
    if m:
        path = _safe_path(m.group(1))
        if not os.path.isfile(path):
            return {"action": "file_read", "reply": f"File not found: {path}"}
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(2000)
            preview = content[:500]
            return {"action": "file_read", "reply": f"File contents: {preview}"}
        except Exception as e:
            return {"action": "file_read", "reply": f"Could not read: {e}"}

    return None
