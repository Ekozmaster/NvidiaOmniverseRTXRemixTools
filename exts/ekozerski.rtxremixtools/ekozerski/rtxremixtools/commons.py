import carb


def log_info(msg: str):
    carb.log_info(f"[RTX Remix Tool] {msg}")


def log_warn(msg: str):
    carb.log_warn(f"[RTX Remix Tool] {msg}")


def log_error(msg: str):
    carb.log_error(f"[RTX Remix Tool] {msg}")
