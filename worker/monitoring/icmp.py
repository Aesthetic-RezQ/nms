import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

try:
    from icmplib import async_ping, ICMPLibError, DestinationUnreachable, TimeExceeded
    try:
        from icmplib import Timeout as ICMPTimeout
    except ImportError:
        ICMPTimeout = None
except ImportError as e:
    raise ImportError(f"icmplib is required: {e}")

logger = logging.getLogger("nms.worker.icmp")

@dataclass
class PingResult:
    is_alive: bool
    latency: Optional[float] = None       # in milliseconds (ms)
    packet_loss: float = 100.0            # 0.0 to 100.0 %
    error_message: Optional[str] = None
    packets_sent: int = 0
    packets_received: int = 0

class AsyncICMPEngine:
    def __init__(self, ping_count: int = 2):
        self.ping_count = ping_count

    async def ping(self, ip_address: str, timeout: int = 2) -> PingResult:
        """
        Execute an asynchronous ICMP ping to the target IP address.
        """
        try:
            host = await async_ping(
                address=ip_address,
                count=self.ping_count,
                interval=0.2,
                timeout=timeout,
                privileged=False
            )

            packet_loss_pct = host.packet_loss * 100.0 if host.packet_loss is not None else 100.0

            if host.is_alive:
                return PingResult(
                    is_alive=True,
                    latency=round(host.avg_rtt, 2) if host.avg_rtt is not None else None,
                    packet_loss=round(packet_loss_pct, 2),
                    packets_sent=host.packets_sent,
                    packets_received=host.packets_received,
                    error_message=None
                )
            else:
                return PingResult(
                    is_alive=False,
                    latency=None,
                    packet_loss=round(packet_loss_pct, 2),
                    packets_sent=host.packets_sent,
                    packets_received=host.packets_received,
                    error_message="Host unreachable or request timed out"
                )

        except Exception as e:
            # Catch all icmplib exceptions (Timeout, DestinationUnreachable, TimeExceeded, etc.)
            err_type = type(e).__name__
            err_msg = str(e) or err_type

            if "Timeout" in err_type or "timeout" in err_msg.lower():
                return PingResult(
                    is_alive=False,
                    latency=None,
                    packet_loss=100.0,
                    error_message="Ping timeout"
                )
            elif "Unreachable" in err_type or "unreachable" in err_msg.lower():
                return PingResult(
                    is_alive=False,
                    latency=None,
                    packet_loss=100.0,
                    error_message=f"Destination unreachable: {err_msg}"
                )
            else:
                logger.warning(f"ICMP error when pinging {ip_address} ({err_type}): {err_msg}")
                return PingResult(
                    is_alive=False,
                    latency=None,
                    packet_loss=100.0,
                    error_message=f"ICMP error ({err_type}): {err_msg}"
                )
