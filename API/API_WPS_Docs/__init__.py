# -*- coding: utf-8 -*-
"""WPS/KDocs document download API."""

from API.API_WPS_Docs.API_WPS_Docs_File import WpsDocsFileApi
from API.API_WPS_Docs.parser_engineer_extended_warranty import (
    parse_engineer_extended_warranty_records,
    validate_engineer_extended_warranty_headers,
)
from API.API_WPS_Docs.parser_queli_daifa import (
    parse_queli_daifa_records,
    validate_queli_daifa_headers,
)

__all__ = [
    "WpsDocsFileApi",
    "parse_queli_daifa_records",
    "validate_queli_daifa_headers",
    "parse_engineer_extended_warranty_records",
    "validate_engineer_extended_warranty_headers",
]
