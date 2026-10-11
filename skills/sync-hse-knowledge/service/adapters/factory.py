"""Adapter Factory for instantiating source adapters."""

from typing import Optional, Dict, Any
from service.adapters.base import HSESourceAdapter
from service.adapters.vn_gov_legal import VNGovLegalAdapter
from service.adapters.vn_vbpl import VNVbplAdapter
from service.adapters.vn_osh_legal import VNOshLegalAdapter
from service.adapters.vn_health_occ import VNHealthOccAdapter
from service.adapters.vn_env_legal import VNEnvLegalAdapter
from service.adapters.vn_chemicals import VNChemicalsAdapter
from service.adapters.vn_fire_rescue import VNFireRescueAdapter
from service.adapters.vn_qcvn import VNQcvnAdapter
from service.adapters.un_ghs import UNGhsAdapter, ILOWHOIcscAdapter
from service.adapters.ifc_ehs import IFCEhsAdapter, USNioshNpgAdapter, USOSHAAdapter
from service.adapters.iso_gated import ISOGatedAdapter


_ADAPTER_REGISTRY: Dict[str, Any] = {
    "VN_GOV_LEGAL": VNGovLegalAdapter,
    "VN_VBPL": VNVbplAdapter,
    "VN_OSH_LEGAL": VNOshLegalAdapter,
    "VN_HEALTH_OCC": VNHealthOccAdapter,
    "VN_ENV_LEGAL": VNEnvLegalAdapter,
    "VN_CHEMICALS": VNChemicalsAdapter,
    "VN_FIRE_RESCUE": VNFireRescueAdapter,
    "VN_QCVN": VNQcvnAdapter,
    "UN_GHS": UNGhsAdapter,
    "ILO_WHO_ICSC": ILOWHOIcscAdapter,
    "IFC_EHS": IFCEhsAdapter,
    "US_NIOSH_NPG": USNioshNpgAdapter,
    "US_OSHA": USOSHAAdapter,
    "ISO_14001": lambda: ISOGatedAdapter("ISO_14001"),
    "ISO_45001": lambda: ISOGatedAdapter("ISO_45001")
}


def get_adapter(source_id: str) -> Optional[HSESourceAdapter]:
    cls_or_func = _ADAPTER_REGISTRY.get(source_id)
    if not cls_or_func:
        return None
    if callable(cls_or_func):
        return cls_or_func()
    return cls_or_func()
