import platform

version = "2.3.0"
user_agent = (
    f"youte/{version} ({platform.system()} {platform.machine()}) "
    f"{platform.python_implementation()}/{platform.python_version()}"
)
