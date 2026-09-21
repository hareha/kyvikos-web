"""Blender MCP 애드온(localhost:9876)에 직접 명령을 보내는 작은 클라이언트.

  python3 scripts/blender/bmcp.py info
  python3 scripts/blender/bmcp.py exec path/to/script.py      # Blender 안에서 파이썬 실행
  python3 scripts/blender/bmcp.py code "print(bpy.data.objects.keys())"
  python3 scripts/blender/bmcp.py shot /tmp/view.png [크기]   # 뷰포트 캡처
"""
import json
import socket
import sys


def send(command_type, params=None, timeout=float(__import__("os").environ.get("BMCP_TIMEOUT", 600))):
    with socket.create_connection(("localhost", 9876), timeout=timeout) as s:
        s.sendall(json.dumps({"type": command_type, "params": params or {}}).encode("utf-8"))
        buffer = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            buffer += chunk
            try:
                return json.loads(buffer.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
    return json.loads(buffer.decode("utf-8"))


def main():
    cmd, *args = sys.argv[1:] or ["info"]
    if cmd == "info":
        result = send("get_scene_info")
    elif cmd == "exec":
        with open(args[0], encoding="utf-8") as f:
            result = send("execute_code", {"code": f.read()})
    elif cmd == "code":
        result = send("execute_code", {"code": args[0]})
    elif cmd == "shot":
        size = int(args[1]) if len(args) > 1 else 1000
        result = send("get_viewport_screenshot", {"filepath": args[0], "max_size": size, "format": "png"})
    else:
        raise SystemExit(f"unknown command: {cmd}")

    status = result.get("status")
    body = result.get("result", result.get("message"))
    if isinstance(body, dict) and "result" in body and isinstance(body["result"], str):
        print(body["result"])
    else:
        print(json.dumps(body, ensure_ascii=False, indent=2)[:4000])
    if status != "success":
        sys.exit(1)


if __name__ == "__main__":
    main()
