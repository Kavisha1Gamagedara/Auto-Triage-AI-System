"""Agent 4 part name resolver.

Agent 2 emits a component string ("Brake Pads"); a mechanic types whatever
they say out loud ("dynamo", "shockers", "dicky door", "MAF senser"). A plain
catalog lookup finds nothing for most of those. This module maps any incoming
string onto a canonical part_name that exists in the catalog, through four
staged attempts, and reports honest failure with candidates when none land.

The staging is the point: each stage is cheaper and more certain than the one
after it, and a stage only runs when every stage above it has missed.
"""

import re
import string

from rank_bm25 import BM25Okapi
from rapidfuzz import fuzz, process

# Words that carry no part identity. Dropped before ranking so that "front
# brake pad" cannot rank Front Bumper and Front Fender over Brake Pads.
STOPWORDS = {
    "a", "an", "the", "my", "for", "of", "car", "need", "replace",
    "broken", "cracked", "damaged", "faulty", "shattered", "bad",
    "front", "rear", "left", "right", "side",
}

BM25_ACCEPT = 0.45
FUZZY_ACCEPT = 80

# Confidence for a surface form found inside a longer query. Below an exact
# whole-string match, because the surrounding words might change the intent,
# but high: the match itself is an exact hit on curated trade vocabulary, not
# an approximation. Kept above Agent 4's 0.7 pricing floor deliberately.
ALIAS_PARTIAL_CONFIDENCE = 0.9

_PUNCT = re.compile(f"[{re.escape(string.punctuation)}]")


def squash(raw: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace. Keeps every word.

    This is the form used for exact lookups. Six catalog names and several
    aliases are position-qualified (Front Bumper vs Rear Bumper, "front
    buffer" vs "rear buffer"), so stripping position words before an exact
    match would collapse genuinely different parts onto one key.
    """
    return " ".join(_PUNCT.sub(" ", raw.lower()).split())


def normalize(raw: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace, drop stopwords.

    This is the form used for BM25 and fuzzy ranking, where the position
    words actively hurt precision.
    """
    return " ".join(word for word in squash(raw).split() if word not in STOPWORDS)


class PartResolver:
    """Resolves free-text part descriptions to canonical catalog names.

    The catalog is loaded once at construction. Rebuilding the BM25 index per
    request would dominate the cost of every lookup.
    """

    def __init__(self, db):
        self.aliases: dict[str, str] = {}
        self.ambiguous_aliases: dict[str, set[str]] = {}

        # Raw alias keys first - these are authoritative and unique in the DB.
        for doc in db.part_aliases.find({}, {"_id": 0, "alias": 1, "canonical": 1}):
            self.aliases[squash(doc["alias"])] = doc["canonical"]

        # Then stopword-stripped variants, so "the car battery" reaches the
        # "car battery" alias. An ambiguous variant ("front buffer" and "rear
        # buffer" both reduce to "buffer") is recorded and left out: falling
        # through to a ranked guess with candidates beats answering the wrong
        # part at confidence 1.0.
        for alias_key, canonical in list(self.aliases.items()):
            reduced = normalize(alias_key)
            if not reduced or reduced in self.aliases:
                continue
            self.ambiguous_aliases.setdefault(reduced, set()).add(canonical)

        for reduced, canonicals in self.ambiguous_aliases.items():
            if len(canonicals) == 1:
                self.aliases[reduced] = next(iter(canonicals))
        self.ambiguous_aliases = {
            k: v for k, v in self.ambiguous_aliases.items() if len(v) > 1
        }

        self.names: list[str] = db.parts.distinct("part_name")
        self._names_by_squash = {squash(n): n for n in self.names}

        self._corpus = [n.lower().split() for n in self.names]
        self.bm25 = BM25Okapi(self._corpus)

        # Fuzzy matching searches catalog names and alias surface forms
        # together; an alias hit is mapped back to its canonical afterwards.
        self._fuzzy_choices = self.names + list(self.aliases.keys())

        # Every surface form the n-gram pre-pass can recognise inside a longer
        # query: catalog names and alias keys alike. Aliases take precedence
        # on a collision, matching the order the exact stage checks them.
        self._surface: dict[str, str] = dict(self._names_by_squash)
        self._surface.update(self.aliases)
        self._max_ngram = max((len(s.split()) for s in self._surface), default=1)

    def _alias_ngram(self, tokens: list[str]) -> str | None:
        """Find a known surface form inside a longer query.

        A mechanic writes the symptom as well as the part: "dynamo not
        charging", "shockers gone". The trade term is an exact alias, but the
        whole string is not, and BM25 cannot see alias vocabulary because its
        corpus holds canonical names only. This scans contiguous token runs,
        longest first, so "dicky door" wins over "door".

        Returns None when two different parts are named at the same length -
        the query is genuinely ambiguous and ranking should decide, not this.
        """
        n = len(tokens)
        for size in range(min(n, self._max_ngram), 0, -1):
            hits = {
                self._surface[phrase]
                for start in range(n - size + 1)
                if (phrase := " ".join(tokens[start : start + size])) in self._surface
            }
            if len(hits) == 1:
                return next(iter(hits))
            if len(hits) > 1:
                return None
        return None

    def _bm25_ranked(self, query: str) -> list[tuple[str, float]]:
        """Return (name, normalized_score) for all names, best first."""
        tokens = query.split()
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        order = sorted(range(len(self.names)), key=lambda i: scores[i], reverse=True)

        ranked = []
        for i in order:
            # Normalize against the score the winning name scores on itself,
            # which is that name's ceiling for this index. Without this the
            # raw BM25 score has no fixed range to threshold against.
            self_score = self.bm25.get_scores(self._corpus[i])[i]
            confidence = float(scores[i]) / float(self_score) if self_score > 0 else 0.0
            ranked.append((self.names[i], min(confidence, 1.0)))
        return ranked

    def resolve(self, raw: str) -> dict:
        """Resolve a free-text part string, stopping at the first stage that hits.

        Returns {"canonical", "confidence", "method", "candidates"}. On failure
        canonical is None and candidates holds the closest names - the resolver
        never invents a canonical name it did not match.
        """
        exact_key = squash(raw)
        norm = normalize(raw)

        # (a) EXACT - alias table, then the catalog names themselves.
        # The full string is tried against both before the stopword-stripped
        # form is tried against either. Order matters: "bumper" is an alias
        # for Front Bumper, so a reduced-form alias lookup that ran first
        # would answer Front Bumper for the literal name "Rear Bumper".
        for key in (exact_key, norm):
            if not key:
                continue
            if key in self.aliases:
                return {
                    "canonical": self.aliases[key],
                    "confidence": 1.0,
                    "method": "alias_exact",
                    "candidates": [],
                }
            if key in self._names_by_squash:
                return {
                    "canonical": self._names_by_squash[key],
                    "confidence": 1.0,
                    "method": "exact",
                    "candidates": [],
                }

        # (a2) ALIAS N-GRAM - an exact surface form embedded in a longer query.
        # Sits above ranking because it is a deterministic lexical hit, not an
        # approximation.
        embedded = self._alias_ngram(exact_key.split())
        if embedded:
            return {
                "canonical": embedded,
                "confidence": ALIAS_PARTIAL_CONFIDENCE,
                "method": "alias_partial",
                "candidates": [],
            }

        ranked = self._bm25_ranked(norm)

        # (b) BM25 - lexical overlap, handles reordering and partial phrasing.
        if ranked and ranked[0][1] >= BM25_ACCEPT:
            return {
                "canonical": ranked[0][0],
                "confidence": float(ranked[0][1]),
                "method": "bm25",
                "candidates": [name for name, _ in ranked[1:3]],
            }

        # (c) FUZZY - character-level, this is the stage that absorbs typos.
        if norm:
            match = process.extractOne(norm, self._fuzzy_choices, scorer=fuzz.token_sort_ratio)
            if match and match[1] >= FUZZY_ACCEPT:
                matched = match[0]
                return {
                    "canonical": self.aliases.get(matched, matched),
                    "confidence": float(match[1]) / 100.0,
                    "method": "fuzzy",
                    "candidates": [],
                }

        # FAIL - report the near misses rather than guessing.
        return {
            "canonical": None,
            "confidence": 0.0,
            "method": "none",
            "candidates": self._candidates(norm, ranked, 3),
        }

    def _candidates(self, norm: str, ranked: list[tuple[str, float]], n: int) -> list[str]:
        """Top n near misses: BM25 where it discriminates, else fuzzy.

        When the query shares no token with any catalog name every BM25 score
        is 0, and the "top n" would just be the first n names in index order -
        three arbitrary names presented to a mechanic as suggestions. Fuzzy
        ranking still orders those by character similarity.
        """
        scored = [name for name, score in ranked[:n] if score > 0]
        if scored:
            return scored
        if not norm:
            return []
        return [
            self.aliases.get(matched, matched)
            for matched, _, _ in process.extract(
                norm, self._fuzzy_choices, scorer=fuzz.token_sort_ratio, limit=n
            )
        ]

    def resolve_ranked(
        self,
        raw: str,
        k: int = 3,
        use_bm25: bool = True,
        use_fuzzy: bool = True,
        use_alias_ngram: bool = True,
    ) -> list[str]:
        """Return up to k canonical names in rank order, for the eval harness.

        Deliberately separate from resolve(): the procurement logic depends on
        resolve()'s single-answer contract, so ablation flags live only here.
        """
        exact_key = squash(raw)
        norm = normalize(raw)
        ordered: list[str] = []

        def add(name: str | None) -> None:
            if name and name not in ordered:
                ordered.append(name)

        for key in (exact_key, norm):
            if key:
                add(self.aliases.get(key))
                add(self._names_by_squash.get(key))

        # Same position as in resolve(): a surface form embedded in a longer
        # query outranks anything the statistical stages propose.
        if use_alias_ngram:
            add(self._alias_ngram(exact_key.split()))

        if use_bm25:
            # Only names BM25 actually scored. A zero score means no shared
            # token, and admitting those would fill the list with noise and
            # starve the fuzzy stage below of its slots.
            for name, score in self._bm25_ranked(norm)[:k]:
                if score > 0:
                    add(name)

        if use_fuzzy and norm and len(ordered) < k:
            for matched, score, _ in process.extract(
                norm, self._fuzzy_choices, scorer=fuzz.token_sort_ratio, limit=k
            ):
                if score >= FUZZY_ACCEPT:
                    add(self.aliases.get(matched, matched))

        return ordered[:k]


if __name__ == "__main__":
    from db import get_db

    resolver = PartResolver(get_db())
    print(f"Loaded {len(resolver.names)} catalog names, {len(resolver.aliases)} alias keys")
    if resolver.ambiguous_aliases:
        print("Ambiguous reduced aliases (left out of the exact map, by design):")
        for key, canonicals in sorted(resolver.ambiguous_aliases.items()):
            print(f"  {key!r} -> {sorted(canonicals)}")
    print()

    for probe in ["Brake Pads", "dynamo", "sensor mass air", "MAF senser", "flux capacitor"]:
        result = resolver.resolve(probe)
        print(f"{probe!r}")
        print(f"  canonical  : {result['canonical']}")
        print(f"  confidence : {result['confidence']:.3f}")
        print(f"  method     : {result['method']}")
        print(f"  candidates : {result['candidates']}")
        print()
