def cleanup_str(str_in: str) -> str:
    return str_in.replace('"', "").replace("'", "").strip()
