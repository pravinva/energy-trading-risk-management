class GTMSignalBoardPlugin:
    def is_available(self) -> bool:
        return False
    async def get_signals(self, region: str) -> list[dict]:
        return []
    async def get_account_detail(self, account_id: str) -> dict | None:
        return None

_plugin: GTMSignalBoardPlugin = GTMSignalBoardPlugin()

def get_plugin() -> GTMSignalBoardPlugin:
    return _plugin

def register_plugin(plugin: GTMSignalBoardPlugin) -> None:
    global _plugin
    _plugin = plugin

def load_plugin_if_available() -> None:
    try:
        from app.plugins.gtm_signal_board import GTMSignalBoardPluginImpl  # type: ignore
        register_plugin(GTMSignalBoardPluginImpl())
    except ImportError:
        return
