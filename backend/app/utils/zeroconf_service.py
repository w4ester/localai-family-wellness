"""
mDNS service discovery for local network using zeroconf.
"""
import logging
import socket
from typing import Optional

from zeroconf import ServiceInfo, Zeroconf

from app.core.config import settings

logger = logging.getLogger(__name__)


def register_mdns() -> Optional[ServiceInfo]:
    """
    Register the service with mDNS for local discovery.
    
    Returns:
        The ServiceInfo object if registration was successful, None otherwise.
    """
    try:
        # Get the local IP address
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Create the service info
        service_info = ServiceInfo(
            type_=settings.MDNS_SERVICE_TYPE,
            name=f"{settings.MDNS_SERVICE_NAME}.{settings.MDNS_SERVICE_TYPE}",
            addresses=[socket.inet_aton(local_ip)],
            port=8000,  # The port the FastAPI app is running on
            properties={
                "version": settings.VERSION,
                "path": "/api/v1"
            }
        )
        
        # Register the service
        zeroconf = Zeroconf()
        zeroconf.register_service(service_info)
        
        logger.info(f"Registered mDNS service: {settings.MDNS_SERVICE_NAME}.{settings.MDNS_SERVICE_TYPE}")
        logger.info(f"Service accessible at: http://{local_ip}:8000/api/v1")
        
        return service_info
    except Exception as e:
        logger.error(f"Error registering mDNS service: {e}")
        return None


def unregister_mdns(service_info: ServiceInfo) -> None:
    """
    Unregister the service from mDNS.
    
    Args:
        service_info: The ServiceInfo object returned by register_mdns.
    """
    try:
        zeroconf = Zeroconf()
        zeroconf.unregister_service(service_info)
        zeroconf.close()
        logger.info(f"Unregistered mDNS service: {settings.MDNS_SERVICE_NAME}.{settings.MDNS_SERVICE_TYPE}")
    except Exception as e:
        logger.error(f"Error unregistering mDNS service: {e}")
