"""Silencia el traceback benigno de asyncio en Windows.

En Windows, cuando el navegador cierra su conexión con el servidor Tornado de
Streamlit, el bucle asyncio (ProactorEventLoop) lanza un ConnectionResetError
no capturado (WinError 10054) dentro de
_ProactorBasePipeTransport._call_connection_lost y vuelca ese traceback a la
consola. Es inofensivo. Envolvemos ese método UNA sola vez (Streamlit reejecuta
el script en cada interacción) para descartar solo ese error concreto.
"""

import sys


def silenciar_conn_reset_windows() -> None:
    """Parchea el transporte Proactor para ignorar ConnectionResetError."""
    if sys.platform != "win32":
        return

    from asyncio.proactor_events import _ProactorBasePipeTransport

    if getattr(
        _ProactorBasePipeTransport._call_connection_lost, "_conn_reset_silenciado", False
    ):
        return

    _call_connection_lost_original = _ProactorBasePipeTransport._call_connection_lost

    def _call_connection_lost(self, exc):
        if isinstance(exc, ConnectionResetError):
            return None
        return _call_connection_lost_original(self, exc)

    _call_connection_lost._conn_reset_silenciado = True
    _ProactorBasePipeTransport._call_connection_lost = _call_connection_lost
