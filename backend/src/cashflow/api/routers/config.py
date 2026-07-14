from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/config", tags=["config"])
CONFIG_DIR = Path(__file__).resolve().parents[1] / "config_data"

_CATEGORIES = json.loads((CONFIG_DIR / "categories.json").read_text(encoding="utf-8"))

_I18N = {
    "en": {
        "app_name": "CashFlow Sahayak",
        "income": "Income", "expense": "Expense",
        "savings_deposit": "Savings Deposit", "savings_withdrawal": "Savings Withdrawal",
        "loan_repayment": "Loan Repayment",
        "forecast": "Forecast", "risk": "Risk", "alerts": "Alerts",
        "green": "Healthy", "amber": "Needs Attention", "red": "At Risk",
        "add_entry": "Add Entry", "amount": "Amount", "category": "Category", "note": "Note (optional)",
        "save": "Save", "offline_banner": "You're offline - entries will sync automatically",
        "synced": "Synced", "sync_pending": "Waiting to sync",
    },
    "hi": {
        "app_name": "कैशफ्लो सहायक",
        "income": "आय", "expense": "खर्च",
        "savings_deposit": "बचत जमा", "savings_withdrawal": "बचत निकासी",
        "loan_repayment": "ऋण भुगतान",
        "forecast": "पूर्वानुमान", "risk": "जोखिम", "alerts": "अलर्ट",
        "green": "स्वस्थ", "amber": "ध्यान दें", "red": "जोखिम में",
        "add_entry": "प्रविष्टि जोड़ें", "amount": "राशि", "category": "श्रेणी", "note": "टिप्पणी (वैकल्पिक)",
        "save": "सहेजें", "offline_banner": "आप ऑफलाइन हैं - प्रविष्टियाँ अपने आप सिंक होंगी",
        "synced": "सिंक हो गया", "sync_pending": "सिंक होना बाकी है",
    },
}


@router.get("/categories")
def get_categories(sector: str) -> dict:
    common = _CATEGORIES["common"]
    sector_cfg = _CATEGORIES.get(sector)
    if sector_cfg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown sector: {sector}")
    return {
        "income": sector_cfg["income"] + common["income"],
        "expense": sector_cfg["expense"] + common["expense"],
        "savings_deposit": common["savings_deposit"],
        "savings_withdrawal": common["savings_withdrawal"],
        "loan_repayment": ["loan_emi"],
    }


@router.get("/i18n/{lang}")
def get_i18n(lang: str) -> dict:
    bundle = _I18N.get(lang)
    if bundle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown language: {lang}")
    return bundle
