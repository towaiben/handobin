from datetime import date
from html import escape
from io import BytesIO
import re
import zipfile

import streamlit as st

st.set_page_config(
    page_title="Financing Rate Calculator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MONTHS = [
    "JANUARY",
    "FEBRUARY",
    "MARCH",
    "APRIL",
    "MAY",
    "JUNE",
    "JULY",
    "AUGUST",
    "SEPTEMBER",
    "OCTOBER",
    "NOVEMBER",
    "DECEMBER",
]

LENDER = "HYUNDAI CORPORATION"
LENDER_SIGNER = "YONGHWAN PARK"
LENDER_TITLE = "GENERAL MANAGER"

COUNTRIES = [
    "Afghanistan",
    "Albania",
    "Algeria",
    "Andorra",
    "Angola",
    "Antigua and Barbuda",
    "Argentina",
    "Armenia",
    "Australia",
    "Austria",
    "Azerbaijan",
    "Bahamas",
    "Bahrain",
    "Bangladesh",
    "Barbados",
    "Belarus",
    "Belgium",
    "Belize",
    "Benin",
    "Bhutan",
    "Bolivia",
    "Bosnia and Herzegovina",
    "Botswana",
    "Brazil",
    "Brunei",
    "Bulgaria",
    "Burkina Faso",
    "Burundi",
    "Cabo Verde",
    "Cambodia",
    "Cameroon",
    "Canada",
    "Central African Republic",
    "Chad",
    "Chile",
    "China",
    "Colombia",
    "Comoros",
    "Congo",
    "Costa Rica",
    "Cote d'Ivoire",
    "Croatia",
    "Cuba",
    "Cyprus",
    "Czech Republic",
    "Democratic Republic of the Congo",
    "Denmark",
    "Djibouti",
    "Dominica",
    "Dominican Republic",
    "Ecuador",
    "Egypt",
    "El Salvador",
    "Equatorial Guinea",
    "Eritrea",
    "Estonia",
    "Eswatini",
    "Ethiopia",
    "Fiji",
    "Finland",
    "France",
    "Gabon",
    "Gambia",
    "Georgia",
    "Germany",
    "Ghana",
    "Greece",
    "Grenada",
    "Guatemala",
    "Guinea",
    "Guinea-Bissau",
    "Guyana",
    "Haiti",
    "Honduras",
    "Hungary",
    "Iceland",
    "India",
    "Indonesia",
    "Iran",
    "Iraq",
    "Ireland",
    "Israel",
    "Italy",
    "Jamaica",
    "Japan",
    "Jordan",
    "Kazakhstan",
    "Kenya",
    "Kiribati",
    "Kuwait",
    "Kyrgyzstan",
    "Laos",
    "Latvia",
    "Lebanon",
    "Lesotho",
    "Liberia",
    "Libya",
    "Liechtenstein",
    "Lithuania",
    "Luxembourg",
    "Madagascar",
    "Malawi",
    "Malaysia",
    "Maldives",
    "Mali",
    "Malta",
    "Marshall Islands",
    "Mauritania",
    "Mauritius",
    "Mexico",
    "Micronesia",
    "Moldova",
    "Monaco",
    "Mongolia",
    "Montenegro",
    "Morocco",
    "Mozambique",
    "Myanmar",
    "Namibia",
    "Nauru",
    "Nepal",
    "Netherlands",
    "New Zealand",
    "Nicaragua",
    "Niger",
    "Nigeria",
    "North Korea",
    "North Macedonia",
    "Norway",
    "Oman",
    "Pakistan",
    "Palau",
    "Palestine",
    "Panama",
    "Papua New Guinea",
    "Paraguay",
    "Peru",
    "Philippines",
    "Poland",
    "Portugal",
    "Qatar",
    "Romania",
    "Russia",
    "Rwanda",
    "Saint Kitts and Nevis",
    "Saint Lucia",
    "Saint Vincent and the Grenadines",
    "Samoa",
    "San Marino",
    "Sao Tome and Principe",
    "Saudi Arabia",
    "Senegal",
    "Serbia",
    "Seychelles",
    "Sierra Leone",
    "Singapore",
    "Slovakia",
    "Slovenia",
    "Solomon Islands",
    "Somalia",
    "South Africa",
    "South Korea",
    "South Sudan",
    "Spain",
    "Sri Lanka",
    "Sudan",
    "Suriname",
    "Sweden",
    "Switzerland",
    "Syria",
    "Taiwan",
    "Tajikistan",
    "Tanzania",
    "Thailand",
    "Timor-Leste",
    "Togo",
    "Tonga",
    "Trinidad and Tobago",
    "Tunisia",
    "Turkey",
    "Turkmenistan",
    "Tuvalu",
    "Uganda",
    "Ukraine",
    "United Arab Emirates",
    "United Kingdom",
    "United States",
    "Uruguay",
    "Uzbekistan",
    "Vanuatu",
    "Vatican City",
    "Venezuela",
    "Vietnam",
    "Yemen",
    "Zambia",
    "Zimbabwe",
]

COUNTRY_ADJECTIVES = {
    "afghanistan": "Afghan",
    "albania": "Albanian",
    "algeria": "Algerian",
    "andorra": "Andorran",
    "angola": "Angolan",
    "antigua and barbuda": "Antiguan",
    "argentina": "Argentine",
    "armenia": "Armenian",
    "australia": "Australian",
    "austrailia": "Australian",
    "austria": "Austrian",
    "azerbaijan": "Azerbaijani",
    "bahamas": "Bahamian",
    "bahrain": "Bahraini",
    "bangladesh": "Bangladeshi",
    "barbados": "Barbadian",
    "belarus": "Belarusian",
    "belgium": "Belgian",
    "belize": "Belizean",
    "benin": "Beninese",
    "bhutan": "Bhutanese",
    "bolivia": "Bolivian",
    "bosnia and herzegovina": "Bosnian",
    "botswana": "Botswanan",
    "brazil": "Brazilian",
    "brunei": "Bruneian",
    "bulgaria": "Bulgarian",
    "burkina faso": "Burkinabe",
    "burundi": "Burundian",
    "cabo verde": "Cabo Verdean",
    "cambodia": "Cambodian",
    "cameroon": "Cameroonian",
    "canada": "Canadian",
    "central african republic": "Central African",
    "chad": "Chadian",
    "chile": "Chilean",
    "china": "Chinese",
    "colombia": "Colombian",
    "comoros": "Comorian",
    "congo": "Congolese",
    "costa rica": "Costa Rican",
    "cote d'ivoire": "Ivorian",
    "croatia": "Croatian",
    "cuba": "Cuban",
    "cyprus": "Cypriot",
    "czech republic": "Czech",
    "czechia": "Czech",
    "democratic republic of the congo": "Congolese",
    "denmark": "Danish",
    "djibouti": "Djiboutian",
    "dominica": "Dominican",
    "dominican republic": "Dominican",
    "ecuador": "Ecuadorian",
    "egypt": "Egyptian",
    "el salvador": "Salvadoran",
    "equatorial guinea": "Equatoguinean",
    "eritrea": "Eritrean",
    "estonia": "Estonian",
    "eswatini": "Swazi",
    "ethiopia": "Ethiopian",
    "fiji": "Fijian",
    "finland": "Finnish",
    "france": "French",
    "gabon": "Gabonese",
    "gambia": "Gambian",
    "georgia": "Georgian",
    "germany": "German",
    "ghana": "Ghanaian",
    "greece": "Greek",
    "grenada": "Grenadian",
    "guatemala": "Guatemalan",
    "guinea": "Guinean",
    "guinea-bissau": "Bissau-Guinean",
    "guyana": "Guyanese",
    "haiti": "Haitian",
    "honduras": "Honduran",
    "hungary": "Hungarian",
    "iceland": "Icelandic",
    "india": "Indian",
    "indonesia": "Indonesian",
    "iran": "Iranian",
    "iraq": "Iraqi",
    "ireland": "Irish",
    "israel": "Israeli",
    "italy": "Italian",
    "jamaica": "Jamaican",
    "japan": "Japanese",
    "jordan": "Jordanian",
    "kazakhstan": "Kazakh",
    "kenya": "Kenyan",
    "kiribati": "I-Kiribati",
    "kuwait": "Kuwaiti",
    "kyrgyzstan": "Kyrgyz",
    "laos": "Lao",
    "latvia": "Latvian",
    "lebanon": "Lebanese",
    "lesotho": "Basotho",
    "liberia": "Liberian",
    "libya": "Libyan",
    "liechtenstein": "Liechtensteiner",
    "lithuania": "Lithuanian",
    "luxembourg": "Luxembourgish",
    "madagascar": "Malagasy",
    "malawi": "Malawian",
    "malaysia": "Malaysian",
    "maldives": "Maldivian",
    "mali": "Malian",
    "malta": "Maltese",
    "marshall islands": "Marshallese",
    "mauritania": "Mauritanian",
    "mauritius": "Mauritian",
    "mexico": "Mexican",
    "micronesia": "Micronesian",
    "moldova": "Moldovan",
    "monaco": "Monacan",
    "mongolia": "Mongolian",
    "montenegro": "Montenegrin",
    "morocco": "Moroccan",
    "mozambique": "Mozambican",
    "myanmar": "Myanmar",
    "namibia": "Namibian",
    "nauru": "Nauruan",
    "nepal": "Nepalese",
    "netherlands": "Dutch",
    "new zealand": "New Zealand",
    "nicaragua": "Nicaraguan",
    "niger": "Nigerien",
    "nigeria": "Nigerian",
    "north korea": "North Korean",
    "north macedonia": "Macedonian",
    "norway": "Norwegian",
    "oman": "Omani",
    "pakistan": "Pakistani",
    "palau": "Palauan",
    "palestine": "Palestinian",
    "panama": "Panamanian",
    "papua new guinea": "Papua New Guinean",
    "paraguay": "Paraguayan",
    "peru": "Peruvian",
    "philippines": "Philippine",
    "poland": "Polish",
    "portugal": "Portuguese",
    "qatar": "Qatari",
    "romania": "Romanian",
    "russia": "Russian",
    "rwanda": "Rwandan",
    "saint kitts and nevis": "Kittitian",
    "saint lucia": "Saint Lucian",
    "saint vincent and the grenadines": "Vincentian",
    "samoa": "Samoan",
    "san marino": "Sammarinese",
    "sao tome and principe": "Sao Tomean",
    "saudi arabia": "Saudi",
    "senegal": "Senegalese",
    "serbia": "Serbian",
    "seychelles": "Seychellois",
    "sierra leone": "Sierra Leonean",
    "singapore": "Singaporean",
    "slovakia": "Slovak",
    "slovenia": "Slovenian",
    "solomon islands": "Solomon Island",
    "somalia": "Somali",
    "south africa": "South African",
    "south korea": "Korean",
    "korea": "Korean",
    "south sudan": "South Sudanese",
    "spain": "Spanish",
    "sri lanka": "Sri Lankan",
    "sudan": "Sudanese",
    "suriname": "Surinamese",
    "sweden": "Swedish",
    "switzerland": "Swiss",
    "syria": "Syrian",
    "taiwan": "Taiwanese",
    "tajikistan": "Tajik",
    "tanzania": "Tanzanian",
    "thailand": "Thai",
    "timor-leste": "Timorese",
    "togo": "Togolese",
    "tonga": "Tongan",
    "trinidad and tobago": "Trinidadian",
    "tunisia": "Tunisian",
    "turkey": "Turkish",
    "turkmenistan": "Turkmen",
    "tuvalu": "Tuvaluan",
    "uganda": "Ugandan",
    "ukraine": "Ukrainian",
    "united arab emirates": "Emirati",
    "uae": "Emirati",
    "united kingdom": "British",
    "uk": "British",
    "britain": "British",
    "united states": "American",
    "united states of america": "American",
    "usa": "American",
    "us": "American",
    "uruguay": "Uruguayan",
    "uzbekistan": "Uzbek",
    "vanuatu": "Ni-Vanuatu",
    "vatican city": "Vatican",
    "venezuela": "Venezuelan",
    "vietnam": "Vietnamese",
    "yemen": "Yemeni",
    "zambia": "Zambian",
    "zimbabwe": "Zimbabwean",
}

CURRENCIES = ["USD", "EUR", "CNY"]

REMARKS = [
    "Lender reserves the right to change or modify specification(s) of the vehicles without any prior notice in accordance with such change(s) or modification by manufacturer.",
    "All banking charges and commissions outside Korea, including charges incurring by confirming bank, are for borrower's account.",
    "All terms and Conditions shall be fixed at the time of Sales and Purchase Agreement between Borrower and Lender.",
]

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
    <w:rPr>
      <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
      <w:sz w:val="22"/>
      <w:szCs w:val="22"/>
    </w:rPr>
  </w:style>
</w:styles>"""


def format_proposal_date(value: date) -> str:
    return f"{MONTHS[value.month - 1]} {value.day}, {value.year}"


def to_country_adjective(country: str) -> str:
    key = re.sub(r"\s+", " ", str(country or "").strip().lower())
    if key in COUNTRY_ADJECTIVES:
        return COUNTRY_ADJECTIVES[key]

    if re.search(r"(?:ian|ean|an|ese|ish|i|ic)$", key, flags=re.I) and len(key) > 3:
        return country.strip()

    if re.search(r"a$", key, flags=re.I):
        return re.sub(r"a$", "an", country.strip(), flags=re.I)

    return country.strip()


def selected_or_custom(choice: str | None, custom: str) -> str:
    if not choice:
        return ""
    if choice == "Other":
        return custom.strip()
    return choice.strip()


def build_intro_text(draft: dict) -> str:
    product = (draft.get("product") or "").strip()
    market = (draft.get("country_market") or "").strip()

    if product and market:
        import_clause = f" for your import of {product} into {market} market"
    elif product:
        import_clause = f" for your import of {product}"
    elif market:
        import_clause = f" for your import into {market} market"
    else:
        import_clause = ""

    return (
        "With reference to the subject, we, Hyundai Corporation is pleased to present "
        "financing terms and conditions"
        + import_clause
        + " as below. We are keen to assist the financing arrangement and/or assistant "
        "for the subjected business and the terms and conditions set out below;"
    )


def build_draft(values: dict) -> dict:
    country = values.get("country") or ""
    return {
        **values,
        "country_market": to_country_adjective(country) if country else "",
        "date": format_proposal_date(date.today()),
    }


def safe_file_name(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", name)
    return re.sub(r"\s+", "_", cleaned)


def escape_xml(value: str) -> str:
    return escape(str(value or ""), quote=True)


def w_text(text: str) -> str:
    return f'<w:t xml:space="preserve">{escape_xml(text)}</w:t>'


def w_paragraph(text: str, options: dict | None = None) -> str:
    opts = options or {}
    align = f'<w:jc w:val="{opts["align"]}"/>' if opts.get("align") else ""
    if opts.get("before") is not None:
        before = (
            f'<w:spacing w:before="{opts["before"]}" w:after="{opts.get("after") or 0}" '
            f'w:line="{opts.get("line") or 276}" w:lineRule="auto"/>'
        )
    else:
        before = f'<w:spacing w:after="{opts.get("after") or 120}"/>'
    size = opts.get("size") or 22
    bold = "<w:b/><w:bCs/>" if opts.get("bold") else ""
    underline = '<w:u w:val="single"/>' if opts.get("underline") else ""
    return f"""
        <w:p>
          <w:pPr>{align}{before}</w:pPr>
          <w:r>
            <w:rPr>
              <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
              {bold}{underline}
              <w:sz w:val="{size}"/>
              <w:szCs w:val="{size}"/>
            </w:rPr>
            {w_text(text)}
          </w:r>
        </w:p>
    """


def w_empty(height: int) -> str:
    return f'<w:p><w:pPr><w:spacing w:before="{height}" w:after="0"/></w:pPr></w:p>'


def w_term_row(label: str, value: str, options: dict | None = None) -> str:
    opts = options or {}
    if opts.get("bullets"):
        value_xml = "".join(
            f"""
            <w:p>
              <w:pPr>
                <w:spacing w:after="80"/>
                <w:ind w:left="220"/>
              </w:pPr>
              <w:r>
                <w:rPr>
                  <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
                  <w:sz w:val="21"/>
                  <w:szCs w:val="21"/>
                </w:rPr>
                {w_text("* " + item)}
              </w:r>
            </w:p>
            """
            for item in opts["bullets"]
        )
    else:
        value_xml = f"""
            <w:p>
              <w:pPr><w:spacing w:after="40"/></w:pPr>
              <w:r>
                <w:rPr>
                  <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
                  <w:sz w:val="21"/>
                  <w:szCs w:val="21"/>
                </w:rPr>
                {w_text(value)}
              </w:r>
            </w:p>
        """

    return f"""
        <w:tr>
          <w:tc>
            <w:tcPr><w:tcW w:w="2800" w:type="dxa"/><w:vAlign w:val="top"/></w:tcPr>
            <w:p>
              <w:pPr><w:spacing w:after="40"/></w:pPr>
              <w:r>
                <w:rPr>
                  <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
                  <w:sz w:val="21"/>
                  <w:szCs w:val="21"/>
                </w:rPr>
                {w_text(label)}
              </w:r>
            </w:p>
          </w:tc>
          <w:tc>
            <w:tcPr><w:tcW w:w="300" w:type="dxa"/><w:vAlign w:val="top"/></w:tcPr>
            <w:p>
              <w:pPr><w:spacing w:after="40"/></w:pPr>
              <w:r>
                <w:rPr>
                  <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
                  <w:sz w:val="21"/>
                  <w:szCs w:val="21"/>
                </w:rPr>
                {w_text(":")}
              </w:r>
            </w:p>
          </w:tc>
          <w:tc>
            <w:tcPr><w:tcW w:w="6060" w:type="dxa"/><w:vAlign w:val="top"/></w:tcPr>
            {value_xml}
          </w:tc>
        </w:tr>
    """


def w_sign_cell(lines: list[str]) -> str:
    paragraphs = "".join(
        [
            w_paragraph(lines[0], {"after": 0}),
            w_empty(800),
            """
            <w:p>
              <w:pPr>
                <w:pBdr>
                  <w:top w:val="single" w:sz="6" w:space="1" w:color="000000"/>
                </w:pBdr>
                <w:ind w:right="1200"/>
                <w:spacing w:before="80" w:after="80"/>
              </w:pPr>
            </w:p>
            """,
            w_paragraph(lines[1], {"after": 0}),
            w_paragraph(lines[2], {"after": 0}),
        ]
    )
    return f"""
        <w:tc>
          <w:tcPr><w:tcW w:w="4580" w:type="dxa"/></w:tcPr>
          {paragraphs}
        </w:tc>
    """


def build_document_xml(draft: dict) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:body>
            {w_paragraph("Financing Proposal", {"align": "center", "bold": True, "size": 36, "after": 360})}
            {w_paragraph(draft["date"], {"align": "right", "after": 280})}
            {w_paragraph(draft["company_name"], {"bold": True, "underline": True, "after": 40}) if draft["company_name"] else ""}
            {w_paragraph(draft["company_address"], {"after": 240}) if draft["company_address"] else w_empty(200)}
            {w_paragraph(build_intro_text(draft), {"after": 240})}
            <w:tbl>
              <w:tblPr>
                <w:tblW w:w="9160" w:type="dxa"/>
                <w:tblBorders>
                  <w:top w:val="nil"/>
                  <w:left w:val="nil"/>
                  <w:bottom w:val="nil"/>
                  <w:right w:val="nil"/>
                  <w:insideH w:val="nil"/>
                  <w:insideV w:val="nil"/>
                </w:tblBorders>
              </w:tblPr>
              {w_term_row("BORROWER", draft["company_name"])}
              {w_term_row("LENDER", LENDER)}
              {w_term_row("Financing Currency", draft["currency"])}
              {w_term_row("Payment Method", draft["payment_method"])}
              {w_term_row("Payment Period", draft["payment_period"])}
              {w_term_row("Initial Credit Line", draft["credit_line"])}
              {w_term_row("Administration Fee", draft["admin_fee"])}
              {w_term_row("Interest Rate", draft["interest_rate"])}
              {w_term_row("Remarks", "", {"bullets": REMARKS})}
            </w:tbl>
            {w_empty(200)}
            {w_paragraph("We, Hyundai Corporation, are pleased to assist you to complete the financing with our full scale of experiences. Should you have any query, please do not hesitate to contact us at any time.", {"after": 360})}
            <w:tbl>
              <w:tblPr>
                <w:tblW w:w="9160" w:type="dxa"/>
                <w:tblBorders>
                  <w:top w:val="nil"/>
                  <w:left w:val="nil"/>
                  <w:bottom w:val="nil"/>
                  <w:right w:val="nil"/>
                  <w:insideH w:val="nil"/>
                  <w:insideV w:val="nil"/>
                </w:tblBorders>
              </w:tblPr>
              <w:tr>
                {w_sign_cell([LENDER, LENDER_SIGNER, LENDER_TITLE])}
                {w_sign_cell([draft["company_name"], draft["signing_person"], draft["position"]])}
              </w:tr>
            </w:tbl>
            <w:sectPr>
              <w:pgSz w:w="11906" w:h="16838"/>
              <w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"/>
            </w:sectPr>
          </w:body>
        </w:document>"""


def create_docx(draft: dict) -> bytes:
    buffer = BytesIO()
    files = {
        "[Content_Types].xml": CONTENT_TYPES,
        "_rels/.rels": ROOT_RELS,
        "word/_rels/document.xml.rels": DOC_RELS,
        "word/styles.xml": STYLES,
        "word/document.xml": build_document_xml(draft),
    }
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as zf:
        for name, data in files.items():
            zf.writestr(name, data.encode("utf-8"))
    return buffer.getvalue()


def render_preview_html(draft: dict) -> str:
    company = escape(draft["company_name"])
    company_block = f'<div class="proposal-company">{company}</div>' if draft["company_name"] else ""
    address_block = (
        f'<div class="proposal-address">{escape(draft["company_address"])}</div>'
        if draft["company_address"]
        else '<div class="proposal-address"></div>'
    )
    remarks_html = "".join(f"<li>{escape(item)}</li>" for item in REMARKS)

    return f"""
    <div class="proposal-paper">
      <div class="proposal-title">Financing Proposal</div>
      <div class="proposal-date">{escape(draft["date"])}</div>
      {company_block}
      {address_block}
      <p class="proposal-intro">{escape(build_intro_text(draft))}</p>
      <table class="terms">
        <tr><td class="label">BORROWER</td><td class="colon">:</td><td>{company}</td></tr>
        <tr><td class="label">LENDER</td><td class="colon">:</td><td>{escape(LENDER)}</td></tr>
        <tr><td class="label">Financing Currency</td><td class="colon">:</td><td>{escape(draft["currency"])}</td></tr>
        <tr><td class="label">Payment Method</td><td class="colon">:</td><td>{escape(draft["payment_method"])}</td></tr>
        <tr><td class="label">Payment Period</td><td class="colon">:</td><td>{escape(draft["payment_period"])}</td></tr>
        <tr><td class="label">Initial Credit Line</td><td class="colon">:</td><td>{escape(draft["credit_line"])}</td></tr>
        <tr><td class="label">Administration Fee</td><td class="colon">:</td><td>{escape(draft["admin_fee"])}</td></tr>
        <tr><td class="label">Interest Rate</td><td class="colon">:</td><td>{escape(draft["interest_rate"])}</td></tr>
        <tr>
          <td class="label">Remarks</td>
          <td class="colon">:</td>
          <td><ul class="remarks">{remarks_html}</ul></td>
        </tr>
      </table>
      <p class="proposal-close">
        We, Hyundai Corporation, are pleased to assist you to complete the financing
        with our full scale of experiences. Should you have any query, please do not
        hesitate to contact us at any time.
      </p>
      <table class="signs">
        <tr>
          <td>
            <div>{escape(LENDER)}</div>
            <div class="sign-space"></div>
            <div class="sign-line"></div>
            <div>{escape(LENDER_SIGNER)}</div>
            <div>{escape(LENDER_TITLE)}</div>
          </td>
          <td>
            <div>{company}</div>
            <div class="sign-space"></div>
            <div class="sign-line"></div>
            <div>{escape(draft["signing_person"])}</div>
            <div>{escape(draft["position"])}</div>
          </td>
        </tr>
      </table>
    </div>
    """


def inject_styles() -> None:
    st.markdown(
        """
        <style>
          .stApp { background: #f4f6f8; }
          h1 { letter-spacing: -0.5px; }
          .placeholder { color: #5c6b7a; font-size: 15px; }
          .proposal-preview-pane {
            background: #eef1f4;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #d8dee6;
            max-height: 88vh;
            overflow: auto;
          }
          .proposal-paper {
            background: #fff;
            max-width: 780px;
            min-height: 100%;
            margin: 0 auto;
            padding: 48px 52px 40px;
            color: #111;
            font-family: Arial, "Malgun Gothic", sans-serif;
            font-size: 13px;
            line-height: 1.45;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
          }
          .proposal-title {
            text-align: center;
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 36px;
          }
          .proposal-date { text-align: right; margin-bottom: 28px; }
          .proposal-company { font-weight: 700; text-decoration: underline; }
          .proposal-address { margin: 4px 0 22px; }
          .proposal-intro, .proposal-close { text-align: justify; margin-bottom: 22px; }
          .terms { width: 100%; border-collapse: collapse; margin-bottom: 28px; }
          .terms td { vertical-align: top; padding: 3px 0; }
          .terms .label { width: 190px; white-space: nowrap; }
          .terms .colon { width: 18px; }
          .remarks { margin: 0; padding-left: 16px; }
          .remarks li { margin-bottom: 8px; }
          .signs { width: 100%; border-collapse: collapse; margin-top: 36px; }
          .signs td { width: 50%; vertical-align: top; padding-right: 24px; }
          .sign-space { height: 72px; }
          .sign-line { border-top: 1px solid #111; width: 78%; margin: 8px 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_lookup_tab() -> None:
    st.markdown('<p class="placeholder">요율조회 화면이 여기에 표시됩니다.</p>', unsafe_allow_html=True)


def render_calc_tab() -> None:
    st.markdown('<p class="placeholder">요율 산출 화면이 여기에 표시됩니다.</p>', unsafe_allow_html=True)


def render_cost_tab() -> None:
    st.markdown('<p class="placeholder">원가 구조 화면이 여기에 표시됩니다.</p>', unsafe_allow_html=True)


def render_proposal_tab() -> None:
    form_col, preview_col = st.columns([0.38, 0.62], gap="large")

    with form_col:
        company_name = st.text_input("Company Name")
        company_address = st.text_input("Registered Address")
        product = st.text_input("Commodity")

        country_choice = st.selectbox(
            "Country",
            COUNTRIES + ["Other"],
            index=None,
            placeholder="Select",
        )
        country_custom = ""
        if country_choice == "Other":
            country_custom = st.text_input("Enter country", key="country_custom")

        currency_choice = st.selectbox(
            "Currency",
            CURRENCIES + ["Other"],
            index=None,
            placeholder="Select",
        )
        currency_custom = ""
        if currency_choice == "Other":
            currency_custom = st.text_input("Enter currency", key="currency_custom")

        payment_method = st.text_input("Payment Method")
        payment_period = st.text_input("Payment Period")
        credit_line = st.text_input("Initial Credit Line")
        admin_fee = st.text_input("Administration Fee")
        interest_rate = st.text_area("Interest Rate", height=88)
        signing_person = st.text_input("Authorized Signatory")
        position = st.text_input("Title")

        draft = build_draft(
            {
                "company_name": company_name.strip(),
                "company_address": company_address.strip(),
                "product": product.strip(),
                "country": selected_or_custom(country_choice, country_custom),
                "currency": selected_or_custom(currency_choice, currency_custom),
                "payment_method": payment_method.strip(),
                "payment_period": payment_period.strip(),
                "credit_line": credit_line.strip(),
                "admin_fee": admin_fee.strip(),
                "interest_rate": interest_rate.strip(),
                "signing_person": signing_person.strip(),
                "position": position.strip(),
            }
        )

        file_name = (
            f"Financing_Proposal_{safe_file_name(draft['company_name'])}.docx"
            if draft["company_name"]
            else "Financing_Proposal.docx"
        )
        st.download_button(
            "문서생성",
            data=create_docx(draft),
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            width="stretch",
        )

    with preview_col:
        st.markdown(
            f'<div class="proposal-preview-pane">{render_preview_html(draft)}</div>',
            unsafe_allow_html=True,
        )


inject_styles()
st.title("Financing Rate Calculator")

lookup_tab, calc_tab, cost_tab, proposal_tab = st.tabs(
    ["요율조회", "요율 산출", "원가 구조", "요율제안서 작성"]
)

with lookup_tab:
    render_lookup_tab()
with calc_tab:
    render_calc_tab()
with cost_tab:
    render_cost_tab()
with proposal_tab:
    render_proposal_tab()
