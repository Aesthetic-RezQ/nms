import asyncio
import logging
import signal
import sys
import os

# Ensure backend directory is discoverable if running outside container
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from monitoring.scheduler import MonitoringScheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('nms.worker')

async def main():
    logger.info("Initializing LAN Network Monitoring Worker...")
    scheduler = MonitoringScheduler()

    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Termination signal received. Shutting down worker...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Signal handling on Windows
            pass

    scheduler_task = asyncio.create_task(scheduler.start())

    try:
        # Wait for stop event or scheduler task
        done, pending = await asyncio.wait(
            [scheduler_task, asyncio.create_task(stop_event.wait())],
            return_when=asyncio.FIRST_COMPLETED
        )
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Keyboard interrupt received.")
    finally:
        await scheduler.stop()
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        logger.info("Worker shutdown complete.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker process exited.")
