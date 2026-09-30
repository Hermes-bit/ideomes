from .a01_demeter import Demeter
from .a02_themis import Themis
from .a03_athena import Athena
from .a04_hestia import Hestia
from .a05_gaia import Gaia
from .a06_artemis import Artemis
from .a07_kairos import Kairos
from .a08_hephaistos import Hephaistos
from .a09_hera import Hera
from .a10_iris import Iris
from .a11_nike import Nike
from .a12_helios import Helios
from .apollon import Apollon
from .base import Agent  # noqa: F401

TOUS = {
    c.id: c
    for c in (Demeter, Themis, Athena, Hestia, Gaia, Artemis, Kairos, Hephaistos, Hera, Iris, Nike, Helios, Apollon)
}
