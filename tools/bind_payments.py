import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime
from difflib import SequenceMatcher

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtCore import QDate, QSettings

from base.contract import ContractDocumentData, PaymentDueType, DaysType, MonthType
from base.paymentdate import calculate_payment_date
from base.paths import db_path, settings_path

BIND_SCORE = 5
BIND_MARGIN = 2

LEGAL_FORMS = {
    "ооо", "оао", "зао", "ип", "чп", "чуп", "чупп", "чптуп", "чртуп", "птчуп", "птуп", "одо", "уп", "куп", "кпуп",
    "руп", "соо", "сооо", "итсуп", "итуп", "иооо", "иуп", "уз", "уо", "го", "гп", "тпруп", "засо", "зсао", "ао",
    "тчуп", "чтуп", "пк", "филиал", "учреждение", "ггп", "нкфо", "ддп",
}
STOP_STEMS = {"оплат", "платеж", "услуг", "расчет", "работ"}

TYPE_INVOICE, TYPE_TN, TYPE_ACT, TYPE_CONTRACT, TYPE_OTHER = 1, 2, 3, 4, 99

DOC_TYPE_PATTERNS = [
    (r"^\s*(счет|счёт)[- ]акт", TYPE_ACT),
    (r"^\s*(счет|счёт|платежное требование|платёжное требование|квитанци)", TYPE_INVOICE),
    (r"^\s*(ттн|тн\b|товарно|накладн)", TYPE_TN),
    (r"^\s*(акт|наряд)", TYPE_ACT),
    (r"^\s*(договор|спецификаци|протокол|доп)", TYPE_CONTRACT),
    (r"^\s*реестр", TYPE_OTHER),
]
CONTRACT_MENTION_RE = re.compile(r"(?:договор|контракт)[а-яё ]*?(?:№|N)\s*([^\s,;]+)(?:\s+от\s+(\d{1,2}\.\d{1,2}\.\d{4}))?",
                                 re.IGNORECASE)
DOC_NUMBER_RE = re.compile(r"№\s*([^\s,;]+)")
DATE_RE = re.compile(r"от\s+(\d{1,2})\.(\d{1,2})\.(\d{4})")


def norm_tokens(name: str) -> list[str]:
    name = (name or "").lower().replace("ё", "е")
    tokens = re.sub(r"[^0-9a-zа-я]+", " ", name).split()
    return [t for t in tokens if t not in LEGAL_FORMS]


def name_core(name: str) -> str:
    return "".join(norm_tokens(name))


def person_key(name: str):
    tokens = norm_tokens(name)
    if len(tokens) < 2:
        return None
    return tokens[0], [t[0] for t in tokens[1:]]


def contractor_match_tier(receiver: str, contractor: str) -> int:
    if (receiver or "").strip().lower() == (contractor or "").strip().lower():
        return 3
    core_r, core_c = name_core(receiver), name_core(contractor)
    if not core_r or not core_c:
        return 0
    if core_r == core_c:
        legal_r = {t for t in (receiver or "").lower().split() if t in LEGAL_FORMS}
        legal_c = {t for t in (contractor or "").lower().split() if t in LEGAL_FORMS}
        return 2 if legal_r == legal_c else 1
    pr, pc = person_key(receiver), person_key(contractor)
    if pr and pc and pr[0] == pc[0] and all(a == b for a, b in zip(pr[1], pc[1])):
        return 2
    if SequenceMatcher(None, core_r, core_c).ratio() >= 0.9:
        return 2
    return 0


def parse_date(text: str) -> QDate | None:
    if not text:
        return None
    for fmt in ("yyyy-MM-dd", "dd.MM.yyyy"):
        d = QDate.fromString(text, fmt)
        if d.isValid():
            return d
    return None


def parse_descr(descr: str) -> dict:
    descr = descr or ""
    doc_type = None
    for pattern, t in DOC_TYPE_PATTERNS:
        if re.search(pattern, descr, re.IGNORECASE):
            doc_type = t
            break
    mention = CONTRACT_MENTION_RE.search(descr)
    mention_number = mention.group(1).strip().rstrip(".") if mention else None
    mention_date = parse_date(mention.group(2)) if mention and mention.group(2) else None
    number = DOC_NUMBER_RE.search(descr)
    doc_number = number.group(1).strip().rstrip(".") if number and not mention else None
    doc_date = None
    m = DATE_RE.search(descr)
    if m and doc_type != TYPE_CONTRACT:
        d = QDate(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        doc_date = d if d.isValid() else None
    return {"doc_type": doc_type, "mention_number": mention_number, "mention_date": mention_date, "doc_date": doc_date,
            "doc_number": doc_number}


def keyword_stems(text: str) -> set[str]:
    words = re.sub(r"[^0-9a-zа-я]+", " ", (text or "").lower().replace("ё", "е")).split()
    return {w[:5] for w in words if len(w) >= 6 and w[:5] not in STOP_STEMS}


def number_matches(mention: str | None, number: str) -> bool:
    if not mention:
        return False
    a, b = mention.lower().strip(), (number or "").lower().strip()
    return bool(b) and a == b


def make_terms(row) -> ContractDocumentData:
    return ContractDocumentData(
        document_id=row["doc_id"], contractor_id=row["contractor_id"], contractor_name=row["contractor_name"],
        contract_id=row["contract_id"], contract_number=row["contract_number"],
        contract_date=parse_date(row["contract_date"]) or QDate(), document_type=row["document_type"],
        position_id=0, document_name=row["document_name"], description=row["description"] or "",
        payment_type=PaymentDueType(row["payment_type"]), days_count=row["days_count"] or 0,
        days_type=DaysType(row["days_type"]) if row["days_type"] else None,
        has_calendar_condition=bool(row["has_calendar_condition"]),
        month_day=row["month_day"], month_type=MonthType(row["month_type"]) if row["month_type"] else None)


def expected_dates(settings, terms: ContractDocumentData, triggers: list[QDate]) -> list[QDate]:
    result = []
    for trigger in triggers:
        if terms.payment_type == PaymentDueType.RELATIVE:
            if terms.has_calendar_condition:
                for shift in (-1, 0, 1):
                    first = trigger.addMonths(shift)
                    d = calculate_payment_date(settings, terms, trigger, first.year(), first.month())
                    if d:
                        result.append(d)
            else:
                d = calculate_payment_date(settings, terms, trigger, trigger.year(), trigger.month())
                if d:
                    result.append(d)
        elif terms.payment_type == PaymentDueType.FIXED:
            for shift in (-2, -1, 0, 1):
                first = trigger.addMonths(shift)
                d = calculate_payment_date(settings, terms, trigger, first.year(), first.month())
                if d:
                    result.append(d)
    return result


def score_candidate(settings, event, info, terms, doc_row, tier, contract_mention_hit) -> tuple[int, list[str]]:
    score, why = 0, []
    due = parse_date(event["duedate"])
    triggers = [d for d in (info["doc_date"], parse_date(event["createdate"])) if d]
    trigger_for_contract = triggers[0] if triggers else None

    contract_date = parse_date(doc_row["contract_date"])
    if contract_date and trigger_for_contract and contract_date > trigger_for_contract:
        return -100, ["договор заключен позже документа"]

    if info["mention_number"]:
        if contract_mention_hit:
            score += 5 if info["mention_date"] and contract_date == info["mention_date"] else 4
            why.append("номер договора в основании")
        else:
            score -= 6
            why.append(f"в основании другой договор {info['mention_number']}")

    if len(info["doc_number"] or "") >= 3 and number_matches(info["doc_number"], doc_row["contract_number"]):
        score += 3
        why.append("номер документа совпал с номером договора")

    doc_type = info["doc_type"]
    if doc_type and doc_row["document_type"] != TYPE_OTHER:
        if doc_type == doc_row["document_type"] or {doc_type, doc_row["document_type"]} == {TYPE_INVOICE, TYPE_ACT}:
            score += 2
            why.append("тип документа совпал")
        elif doc_type != TYPE_OTHER:
            score -= 2
            why.append("тип документа не совпал")

    if doc_row["document_type"] == TYPE_OTHER:
        doc_stems = keyword_stems(doc_row["document_name"])
        event_stems = keyword_stems(event["name"])
        if doc_stems & event_stems:
            score += 2
            why.append("название документа совпало с наименованием платежа")
        elif doc_stems:
            score -= 1
            why.append("название документа не найдено в наименовании платежа")

    if terms.payment_type == PaymentDueType.PREPAYMENT:
        why.append("срок не определен (предоплата)")
    elif due and triggers:
        dates = expected_dates(settings, terms, triggers)
        if dates:
            best = min(abs(d.daysTo(due)) for d in dates)
            if best == 0:
                score += 3
                why.append("срок совпал")
            elif best <= 3:
                score += 1
                why.append(f"срок отличается на {best} дн.")
            else:
                score -= 1
                why.append(f"срок не совпал ({best} дн.)")

    if tier == 1:
        score -= 2
        why.append("название контрагента совпало неточно")
    return score, why


def main(apply: bool) -> None:
    con = sqlite3.connect(f"file:{db_path()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    settings = QSettings(settings_path(), QSettings.Format.IniFormat)

    docs = con.execute("""
        SELECT d.id AS doc_id, d.document_type, d.document_name, d.description, c.id AS contract_id,
               c.name AS contract_number, c.date AS contract_date, k.id AS contractor_id, k.name AS contractor_name,
               t.payment_type, t.days_count, t.days_type, t.has_calendar_condition, t.month_day, t.month_type
        FROM contractdocument d
        JOIN contract c ON c.id = d.contract_id
        JOIN contractor k ON k.id = c.contractor_id
        JOIN contractpaymentterm t ON t.document_id = d.id
    """).fetchall()
    terms_by_doc = {r["doc_id"]: make_terms(r) for r in docs}
    contractors = {r["contractor_id"]: r["contractor_name"] for r in docs}
    contractors.update({r["id"]: r["name"] for r in con.execute("SELECT id, name FROM contractor")})
    docs_by_contractor: dict[int, list] = {}
    for r in docs:
        docs_by_contractor.setdefault(r["contractor_id"], []).append(r)

    events = con.execute("""
        SELECT id, receiver, createdate, duedate, descr, name, totalamount FROM event
        WHERE type = 2 AND (contractdocument_id IS NULL OR contractdocument_id = 0) ORDER BY id
    """).fetchall()

    bound, borderline, no_candidates = [], [], []
    renames: dict[int, str] = {}
    for ev in events:
        info = parse_descr(ev["descr"])
        tiers = {kid: contractor_match_tier(ev["receiver"], kname) for kid, kname in contractors.items()}
        tiers = {kid: t for kid, t in tiers.items() if t > 0}

        candidates = []
        for kid, tier in tiers.items():
            for r in docs_by_contractor.get(kid, []):
                hit = number_matches(info["mention_number"], r["contract_number"])
                candidates.append((r, tier, hit))
        if not tiers and info["mention_number"]:
            for r in docs:
                if number_matches(info["mention_number"], r["contract_number"]) and \
                        (not info["mention_date"] or parse_date(r["contract_date"]) == info["mention_date"]):
                    candidates.append((r, 0, True))
        if not candidates:
            if tiers:
                no_candidates.append((ev, "у контрагента нет документов"))
            continue

        if info["mention_number"] and not any(hit for _, _, hit in candidates):
            no_candidates.append((ev, f"в основании договор {info['mention_number']}, которого нет в БД"))
            continue

        scored = []
        for r, tier, hit in candidates:
            s, why = score_candidate(settings, ev, info, terms_by_doc[r["doc_id"]], r, tier, hit)
            if tier == 0:
                s -= 3
                why.append("контрагент найден только по номеру договора")
            scored.append((s, r, why))
        scored.sort(key=lambda x: -x[0])
        best = scored[0]
        second = scored[1][0] if len(scored) > 1 else -100
        tier_of = {r["doc_id"]: tier for r, tier, _ in candidates}
        record = (ev, scored[:3])
        if best[0] >= BIND_SCORE and best[0] - second >= BIND_MARGIN:
            bound.append(record)
            continue
        if best[1]["payment_type"] == "PREPAYMENT" and best[0] > -50 and best[0] - second >= BIND_MARGIN:
            bound.append(record)
            if tier_of[best[1]["doc_id"]] == 1:
                renames[ev["id"]] = best[1]["contractor_name"]
            continue
        adjusted = sorted(((s + (2 if tier_of[r["doc_id"]] == 1 else 0), r, why) for s, r, why in scored),
                          key=lambda x: -x[0])
        adj_second = adjusted[1][0] if len(adjusted) > 1 else -100
        if tier_of[adjusted[0][1]["doc_id"]] == 1 and adjusted[0][0] >= BIND_SCORE                 and adjusted[0][0] - adj_second >= BIND_MARGIN:
            bound.append((ev, adjusted[:3]))
            renames[ev["id"]] = adjusted[0][1]["contractor_name"]
            continue
        near = sorted(((s + (2 if any(re.search(r"отличается на [12] дн", w) for w in why) else 0), r, why)
                       for s, r, why in scored), key=lambda x: -x[0])
        near_second = near[1][0] if len(near) > 1 else -100
        if near[0][0] >= BIND_SCORE and near[0][0] - near_second >= BIND_MARGIN:
            bound.append((ev, near[:3]))
            continue
        borderline.append(record)

    report_dir = os.path.join(ROOT, "data", "export")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "bind_report.txt")

    def fmt_doc(r) -> str:
        return (f"doc#{r['doc_id']} [{r['contractor_name']} | дог. {r['contract_number']} от {r['contract_date']} | "
                f"{r['document_name']} | {r['payment_type']}]")

    def fmt_event(ev) -> str:
        descr = " ".join((ev['descr'] or '').split())[:80]
        name = " ".join((ev['name'] or '').split())[:40]
        return (f"event#{ev['id']} {ev['receiver']} | создан {ev['createdate']} срок {ev['duedate']} | "
                f"{descr!r} | {name!r} | {ev['totalamount']}")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"ПРИВЯЗАНО: {len(bound)} (с исправлением имени получателя: {len(renames)})\n")
        for ev, sc in bound:
            f.write(fmt_event(ev) + "\n")
            s, r, why = sc[0]
            rename = f" [получатель -> {renames[ev['id']]}]" if ev["id"] in renames else ""
            f.write(f"    -> {s}: {fmt_doc(r)} :: {'; '.join(why)}{rename}\n")
        f.write(f"\n\nГРАНИЧНЫЕ СЛУЧАИ: {len(borderline)}\n")
        for ev, sc in borderline:
            f.write(fmt_event(ev) + "\n")
            for s, r, why in sc:
                f.write(f"    ?? {s}: {fmt_doc(r)} :: {'; '.join(why)}\n")
        f.write(f"\n\nБЕЗ КАНДИДАТОВ: {len(no_candidates)}\n")
        for ev, reason in no_candidates:
            f.write(fmt_event(ev) + f" :: {reason}\n")

    print(f"Событий без привязки: {len(events)}")
    print(f"К привязке: {len(bound)}, граничных: {len(borderline)}, контрагент без документов: {len(no_candidates)}")
    print(f"Отчет: {report_path}")

    if apply and bound:
        backup_path = db_path() + f".before_bind_{datetime.now():%Y%m%d_%H%M%S}"
        shutil.copy2(db_path(), backup_path)
        wcon = sqlite3.connect(db_path())
        with wcon:
            wcon.executemany("UPDATE event SET contractdocument_id = ? WHERE id = ? AND (contractdocument_id IS NULL OR contractdocument_id = 0)",
                             [(sc[0][1]["doc_id"], ev["id"]) for ev, sc in bound])
            wcon.executemany("UPDATE event SET receiver = ?, receivernocase = ? WHERE id = ?",
                             [(name, name.lower(), ev_id) for ev_id, name in renames.items()])
        wcon.close()
        print(f"Записано: {len(bound)}. Копия БД: {backup_path}")


if __name__ == "__main__":
    main("--apply" in sys.argv)
