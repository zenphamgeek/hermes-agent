"""Source Adapter Factory and Registry."""

from typing import Dict, Type, Optional, List
from .base import SourceAdapter
from .vn_gov_legal import VNGovLegalAdapter
from .vn_vbpl import VNVBPLAdapter
from .vn_customs_tariff import VNCustomsTariffAdapter
from .vn_customs_rulings import VNCustomsRulingsAdapter
from .vn_vntr import VNVNTRAdapter
from .asean_ahtn import ASEANAHTNAdapter

_ADAPTER_REGISTRY: Dict[str, Type[SourceAdapter]] = {
    "VN_GOV_LEGAL": VNGovLegalAdapter,
    "VN_VBPL": VNVBPLAdapter,
    "VN_CUSTOMS_TARIFF": VNCustomsTariffAdapter,
    "VN_CUSTOMS_RULINGS": VNCustomsRulingsAdapter,
    "VN_VNTR": VNVNTRAdapter,
    "ASEAN_AHTN": ASEANAHTNAdapter
}


def get_adapter(source_id: str) -> Optional[SourceAdapter]:
    adapter_cls = _ADAPTER_REGISTRY.get(source_id)
    if adapter_cls:
        return adapter_cls()
    return None


def list_registered_adapters() -> List[str]:
    return list(_ADAPTER_REGISTRY.keys())
