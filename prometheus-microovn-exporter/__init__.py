"""Import this library to collect and export service status and metrics for microovn."""
import logging

# Initialize a global logger.
# All other loggers used by each module in this package inherit from this.
logger = logging.getLogger(__package__)

console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(asctime)s %(levelname)s - %(message)s"))
logger.addHandler(console)

