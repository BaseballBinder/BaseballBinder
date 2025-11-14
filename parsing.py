# parsing.py
import re
from typing import List, Tuple, Optional
from schemas import CardParsed, ParallelParsed

FLAG_TOKENS = {
    "RC", "RD", "SP", "SSP", "VAR", "AUTO", "PATCH",
    "REL", "RS", "FS", "FYC"
}

SUBSET_KEYWORDS = [
    "Rookie Debut",
    "Season Highlights",
    "Veteran Combo",
    "Team Card",
    "League Leaders",
    "Future Stars",
    "Prospects",
    "Draft Picks",
    "Checklist",
    "Throwback",
    "Golden Mirror",
]

TEAM_NAMES = [
    "Arizona Diamondbacks",
    "Atlanta Braves",
    "Baltimore Orioles",
    "Boston Red Sox",
    "Chicago Cubs",
    "Chicago White Sox",
    "Cincinnati Reds",
    "Cleveland Guardians",
    "Colorado Rockies",
    "Detroit Tigers",
    "Houston Astros",
    "Kansas City Royals",
    "Los Angeles Angels",
    "Los Angeles Dodgers",
    "Miami Marlins",
    "Milwaukee Brewers",
    "Minnesota Twins",
    "New York Mets",
    "New York Yankees",
    "Oakland Athletics",
    "Philadelphia Phillies",
    "Pittsburgh Pirates",
    "San Diego Padres",
    "San Francisco Giants",
    "Seattle Mariners",
    "St. Louis Cardinals",
    "Tampa Bay Rays",
    "Texas Rangers",
    "Toronto Blue Jays",
    "Washington Nationals",
]

TEAM_TOKEN_MAP = {
    tuple(name.lower().split()): name for name in TEAM_NAMES
}
MAX_TEAM_TOKENS = max(len(tokens) for tokens in TEAM_TOKEN_MAP)


def match_team_tokens(tokens: List[str]) -> Tuple[Optional[str], int]:
    """Attempt to match the start of tokens to a known MLB team."""
    lowered = [t.lower() for t in tokens]
    for length in range(MAX_TEAM_TOKENS, 0, -1):
        if len(lowered) < length:
            continue
        candidate = tuple(lowered[:length])
        if candidate in TEAM_TOKEN_MAP:
            return TEAM_TOKEN_MAP[candidate], length
    return None, 0


def extract_flags(description: str) -> List[str]:
    """
    Capture descriptive subset phrases and uppercase tokens like RC, SSP, AUTO.
    """
    description = description.strip()
    if not description:
        return []

    flags: List[str] = []
    remaining = description

    for phrase in SUBSET_KEYWORDS:
        if phrase.lower() in remaining.lower():
            flags.append(phrase)
            remaining = re.sub(re.escape(phrase), "", remaining, flags=re.IGNORECASE).strip()

    for token in remaining.split():
        cleaned = re.sub(r"[^\w]", "", token).upper()
        if cleaned in FLAG_TOKENS:
            flags.append(cleaned)

    return flags


def parse_card_line(line: str) -> Optional[CardParsed]:
    """
    Parse a single card line into CardParsed.
    Expected general pattern:
    <CARDNUMBER> <Player Name> [ - Team ] [ Description/flags ]
    We keep this somewhat loose so it works with most Beckett/TCDB pastes.
    """
    original = line
    line = line.strip()
    if not line:
        return None

    # Card number = first token (no spaces)
    match = re.match(r"^(\S+)\s+(.*)$", line)
    if not match:
        return None

    card_number = match.group(1).strip()
    rest = match.group(2).strip()

    team = None
    player_name = None
    description = ""

    # Strategy:
    # 1) If " - " is present, assume "Player Name - Team [Description]"
    if " - " in rest:
        parts = [p.strip() for p in rest.split(" - ", maxsplit=2)]
        if len(parts) == 2:
            player_name, team = parts
        elif len(parts) == 3:
            player_name, team, description = parts
    else:
        # No explicit dash. Work from the END to find team/flags
        # Common formats:
        # 1. "FirstName LastName Team" (3 tokens)
        # 2. "FirstName LastName" (2 tokens)
        # 3. "FirstName MiddleName LastName Jr. Team" (5+ tokens)
        # 4. "FirstName LastName Flag Flag" (4+ tokens)
        tokens = rest.split()
        if len(tokens) <= 2:
            # Just treat everything as player name
            player_name = rest
            description = ""
        else:
            # Try to find team by scanning from different split points
            team_found = False
            for split_idx in range(2, len(tokens) + 1):
                # Try matching from this position onwards
                remainder = tokens[split_idx - 1:]
                matched_team, consumed = match_team_tokens(remainder)

                if matched_team:
                    # Found a team match!
                    player_name = " ".join(tokens[:split_idx - 1])
                    team = matched_team
                    description = " ".join(remainder[consumed:]).strip()
                    team_found = True
                    break

            if not team_found:
                # No team found by name matching
                # Check if last token is a flag
                last_token_clean = re.sub(r"[^\w]", "", tokens[-1]).upper()

                if last_token_clean in FLAG_TOKENS:
                    # Last token is a flag, everything else is player name + flags
                    player_name = " ".join(tokens[:-1])
                    description = tokens[-1]
                else:
                    # Assume last token is team abbreviation, everything before is player name
                    player_name = " ".join(tokens[:-1])
                    team = tokens[-1]
                    description = ""

    flags = extract_flags(description)

    return {
        "card_number": card_number,
        "player": player_name or "",
        "team": team or "",
        "description": description.strip(),
        "flags": flags,
        "raw_line": original,
    }


def parse_checklist_text(raw_text: str) -> List[CardParsed]:
    cards: dict[str, dict] = {}
    for line in raw_text.splitlines():
        parsed = parse_card_line(line)
        if not parsed:
            continue

        card_number = parsed["card_number"]
        bucket = cards.setdefault(
            card_number,
            {
                "card_number": card_number,
                "players": [],
                "teams": [],
                "descriptions": [],
                "flags": [],
                "raw_lines": [],
            },
        )

        if parsed["player"]:
            bucket["players"].append(parsed["player"])
        if parsed["team"]:
            bucket["teams"].append(parsed["team"])
        if parsed["description"]:
            bucket["descriptions"].append(parsed["description"])
        bucket["raw_lines"].append(parsed["raw_line"])

        for flag in parsed["flags"]:
            if flag not in bucket["flags"]:
                bucket["flags"].append(flag)

    return [CardParsed(**card) for card in cards.values()]


# PARALLEL PARSER

EXCLUSIVE_KEYWORDS = {
    "Hobby": re.compile(r"hobby exclusive", re.I),
    "Retail": re.compile(r"retail exclusive", re.I),
    "Hanger": re.compile(r"hanger exclusive", re.I),
    "Value Box": re.compile(r"value box exclusive", re.I),
    "Superbox": re.compile(r"superbox exclusive", re.I),
}


def parse_parallel_line(line: str) -> Optional[ParallelParsed]:
    original = line
    line = line.strip()
    if not line:
        return None

    # Extract print run like "/250", "/99" etc.
    pr_match = re.search(r"/(\d+)", line)
    print_run = int(pr_match.group(1)) if pr_match else None

    # Extract exclusive label from parentheses, simplify to a keyword
    exclusive = None
    notes = None

    paren_match = re.search(r"\(([^)]*)\)", line)
    if paren_match:
        notes = paren_match.group(1).strip()
        for label, pattern in EXCLUSIVE_KEYWORDS.items():
            if pattern.search(notes):
                exclusive = label
                break

    # Remove print run and parentheses to get the main name
    name = re.sub(r"/\d+", "", line)
    name = re.sub(r"\([^)]*\)", "", name)
    name = name.strip()

    return ParallelParsed(
        name=name,
        print_run=print_run,
        exclusive=exclusive,
        notes=notes,
        raw_line=original,
    )


def parse_parallel_text(raw_text: str) -> List[ParallelParsed]:
    parallels: List[ParallelParsed] = []
    for line in raw_text.splitlines():
        parsed = parse_parallel_line(line)
        if parsed:
            parallels.append(parsed)
    return parallels
