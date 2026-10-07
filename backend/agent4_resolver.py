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

# Words that carry no part identity at all.
FILLER_WORDS = {
    "a", "an", "the", "my", "for", "of", "car", "need", "replace",
    "broken", "cracked", "damaged", "faulty", "shattered", "bad",
}

# Position words identify a part only when the catalog name carries one
# (Front Bumper vs Rear Bumper). BM25 keeps them; normalize() drops them.
POSITION_WORDS = {"front", "rear", "left", "right", "side"}

# Dropped by normalize() so that "front brake pad" cannot rank Front Bumper
# and Front Fender over Brake Pads.
STOPWORDS = FILLER_WORDS | POSITION_WORDS

BM25_ACCEPT = 0.60
# The best part must also beat the runner-up by this much. Two parts that
# score alike ("pads and rotor both worn") are a tie, and a tie is reported
# with candidates rather than broken by index order.
BM25_MARGIN = 0.10
FUZZY_ACCEPT = 80
# A query word shorter than this is never spelling-corrected: three letters
# sit within one edit of too many unrelated part words.
MIN_CORRECTABLE = 4

# Context that takes a named part out of the running. "not" counts only when
# it sits directly on the part ("not the alternator"); after the part it is
# describing the symptom ("dynamo not charging").
_ARTICLES = {"the", "a", "an", "its"}
_DONE_BEFORE = {"replaced", "changed", "already"}
_DONE_AFTER = {"replaced", "changed", "fitted", "installed", "already", "fine", "ok", "okay", "good"}
# These four describe finished work only when nobody is asking for it:
# "pads replaced last week" is done, "pads need to be replaced" is the job.
_WORK_VERBS = {"replaced", "changed", "fitted", "installed"}
_REQUEST_WORDS = {"need", "needs", "needed", "to", "must", "should", "want", "wants", "please"}
_CLAUSE_STARTERS = {"but", "now", "however", "still"}
_CONTEXT_WINDOW = 3

# Confidence for a surface form found inside a longer query. Below an exact
# whole-string match, because the surrounding words might change the intent,
# but high: the match itself is an exact hit on curated trade vocabulary, not
# an approximation. Kept above Agent 4's 0.7 pricing floor deliberately.
ALIAS_PARTIAL_CONFIDENCE = 0.9

_PUNCT = re.compile(f"[{re.escape(string.punctuation)}]")
_CLAUSE_BREAK = re.compile(r"[,;.!?]")


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


def _stem(token: str) -> str:
    """Fold a plain plural onto its singular: "shocks" -> "shock"."""
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def rank_tokens(raw: str) -> list[str]:
    """Distinct stemmed tokens for BM25, with filler dropped and position kept."""
    return list(dict.fromkeys(_stem(t) for t in squash(raw).split() if t not in FILLER_WORDS))


def clause_tokens(raw: str) -> tuple[list[str], list[int]]:
    """squash(raw).split(), plus the index of the clause each token sits in.

    Negation and "already done" cues only reach as far as their own clause:
    in "replaced pads already, now disc is scored" the "already" belongs to
    the pads and must not rule out the disc.
    """
    tokens: list[str] = []
    clause_of: list[int] = []
    clause = 0
    for part in _CLAUSE_BREAK.split(raw):
        for token in squash(part).split():
            if token in _CLAUSE_STARTERS:
                clause += 1
            tokens.append(token)
            clause_of.append(clause)
        clause += 1
    return tokens, clause_of


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

        # One BM25 document per surface form - every catalog name and every
        # alias - each remembering which part it names. A part scores as its
        # best-matching form.
        #
        # Pooling a name and all its aliases into one bag of words does not
        # work with the coverage score below: the bag's ceiling grows with
        # every alias, so a query that matches the catalog name word for word
        # still covers only a sliver of it ("sensor mass air" scored 0.156
        # against Mass Air Flow Sensor).
        self._forms: list[list[str]] = []
        self._form_canonical: list[str] = []
        self._rank_vocab: dict[str, set[str]] = {n: set() for n in self.names}
        seen_forms = set()
        surfaces = [(n, n) for n in self.names] + list(self.aliases.items())
        for surface, canonical in surfaces:
            tokens = rank_tokens(surface)
            self._rank_vocab.setdefault(canonical, set()).update(tokens)
            key = (canonical, " ".join(sorted(tokens)))
            if not tokens or key in seen_forms:
                continue
            seen_forms.add(key)
            self._forms.append(tokens)
            self._form_canonical.append(canonical)
        self.bm25 = BM25Okapi(self._forms)
        # What each form scores against itself: its ceiling in this index.
        self._form_ceiling = [
            float(self.bm25.get_scores(doc)[i]) for i, doc in enumerate(self._forms)
        ]

        # Fuzzy matching searches catalog names and alias surface forms
        # together, mapped back to a canonical afterwards.
        #
        # Both sides are squashed to lowercase deliberately. token_sort_ratio
        # is case-sensitive, so comparing a lowercased query against
        # capitalised catalog names cost every name about 10 points:
        # 'altenator' vs 'Alternator' scored 84.2 where 'alternator' scores
        # 94.7. Alias keys are already lowercase, so catalog names were
        # systematically handicapped against them, and typos like 'radaitor'
        # (75.0 as-is, 87.5 lowercased) fell below the acceptance floor for
        # no reason but capitalisation.
        self._fuzzy_canonical: dict[str, str] = dict(self.aliases)
        for name in self.names:
            # Names are authoritative: a surface form that is both a catalog
            # name and an alias key resolves to the name itself.
            self._fuzzy_canonical[squash(name)] = name
        self._fuzzy_choices = list(self._fuzzy_canonical)

        # Every token that legitimately belongs to a part: its own name plus
        # the words of every alias pointing at it. Used by strict mode to
        # reject a proposal padded with words the part does not own.
        self._vocab_for: dict[str, set[str]] = {n: set(squash(n).split()) for n in self.names}
        for alias_key, canonical in self.aliases.items():
            self._vocab_for.setdefault(canonical, set()).update(alias_key.split())

        # Every surface form the n-gram pre-pass can recognise inside a longer
        # query: catalog names and alias keys alike. Aliases take precedence
        # on a collision, matching the order the exact stage checks them.
        self._surface: dict[str, str] = dict(self._names_by_squash)
        self._surface.update(self.aliases)
        self._max_ngram = max((len(s.split()) for s in self._surface), default=1)

    def _ruled_out(self, tokens: list[str], clause_of: list[int], start: int, end: int) -> bool:
        """True when the part named at tokens[start:end] is not the one to quote.

        Covers a part that is explicitly excluded ("not the alternator") and
        one that has already been dealt with ("replaced pads already", "pads
        are fine").
        """
        n = len(tokens)
        before = [
            tokens[i] for i in range(max(0, start - _CONTEXT_WINDOW), start)
            if clause_of[i] == clause_of[start]
        ]
        after = [
            tokens[i] for i in range(end, min(n, end + _CONTEXT_WINDOW))
            if clause_of[i] == clause_of[end - 1]
        ]

        attached = [t for t in before if t not in _ARTICLES]
        if attached and attached[-1] == "not":
            return True

        cues = (set(before) & _DONE_BEFORE) | (set(after) & _DONE_AFTER)
        if not cues:
            return False
        clause = {tokens[i] for i in range(n) if clause_of[i] == clause_of[start]}
        if cues <= _WORK_VERBS and clause & _REQUEST_WORDS:
            return False
        return True

    def _alias_ngram(self, tokens: list[str], clause_of: list[int]) -> tuple[str | None, set[str]]:
        """Find a known surface form inside a longer query.

        A mechanic writes the symptom as well as the part: "dynamo not
        charging", "shockers gone". The trade term is an exact alias, but the
        whole string is not. This scans contiguous token runs, longest first,
        so "dicky door" wins over "door".

        Returns (canonical, ruled_out). canonical is None when nothing is
        named, or when two different parts are named at the same length - the
        query is genuinely ambiguous and ranking should decide, not this.
        ruled_out holds parts the query names only to dismiss, so that the
        ranking stages cannot bring them back.
        """
        n = len(tokens)
        ruled_out: set[str] = set()
        # Tokens inside a dismissed mention. "replaced the brake pads" must
        # not then match the shorter "pads" on its own.
        dead = [False] * n

        for size in range(min(n, self._max_ngram), 0, -1):
            hits = set()
            for start in range(n - size + 1):
                end = start + size
                if any(dead[start:end]):
                    continue
                canonical = self._surface.get(" ".join(tokens[start:end]))
                if canonical is None:
                    continue
                if self._ruled_out(tokens, clause_of, start, end):
                    ruled_out.add(canonical)
                    dead[start:end] = [True] * size
                else:
                    hits.add(canonical)

            if len(hits) == 1:
                return next(iter(hits)), ruled_out
            if len(hits) > 1:
                return None, ruled_out
        return None, ruled_out

    def _bm25_ranked(self, tokens: list[str]) -> list[tuple[str, float]]:
        """Return (name, confidence) for all names, best first.

        Confidence is coverage x agreement, both 0-1:

        coverage  - how much of the part's best-matching surface form the
                    query supplies, as BM25 score over that form's ceiling.
                    The form's last word must be among the matched words
                    unless the whole form is present: in "wheel bearing" or
                    "rad hose" the last word is the thing itself, and a query
                    that only shares the qualifier ("wheel alignment", "rad
                    leaking") is about something else.
        agreement - how much of the query's own part vocabulary this part
                    accounts for. "engine oil change" covers the alias "brake
                    oil" well, but "engine" is a part word Brake Fluid does
                    not own, so the match is marked down. Words outside the
                    catalog vocabulary ("leaking", "dirty") cost nothing, and
                    neither do position words.
        """
        best = {name: 0.0 for name in self.names}
        if not tokens:
            return list(best.items())

        idf = self.bm25.idf
        weight = {t: max(float(idf[t]), 1e-6) for t in tokens if t in idf and t not in POSITION_WORDS}
        total = sum(weight.values())
        query = set(tokens)

        scores = self.bm25.get_scores(tokens)
        for i, score in enumerate(scores):
            ceiling = self._form_ceiling[i]
            if score <= 0 or ceiling <= 0:
                continue
            coverage = min(float(score) / ceiling, 1.0)
            form = self._forms[i]
            if coverage < 0.999 and form[-1] not in query:
                continue
            canonical = self._form_canonical[i]
            owned = sum(w for t, w in weight.items() if t in self._rank_vocab[canonical])
            agreement = owned / total if total > 0 else 1.0
            best[canonical] = max(best.get(canonical, 0.0), coverage * agreement)

        return sorted(best.items(), key=lambda item: item[1], reverse=True)

    def _correct_spelling(self, tokens: list[str]) -> list[str] | None:
        """Swap misspelt words for the catalog word they are closest to.

        Returns None when nothing needed correcting. Whole-string fuzzy
        matching is diluted by every extra word, so "raditor leaking" misses
        where "raditor" alone would hit; correcting word by word and then
        ranking as usual absorbs the typo and ignores the symptom.
        """
        vocabulary = list(self.bm25.idf)
        corrected = []
        changed = False
        for token in tokens:
            if token not in self.bm25.idf and len(token) >= MIN_CORRECTABLE:
                match = process.extractOne(token, vocabulary, scorer=fuzz.ratio, score_cutoff=FUZZY_ACCEPT)
                if match:
                    corrected.append(match[0])
                    changed = True
                    continue
            corrected.append(token)
        return list(dict.fromkeys(corrected)) if changed else None

    @staticmethod
    def _clear_winner(ranked: list[tuple[str, float]]) -> bool:
        """True when the top part passes the floor and stands clear of the next."""
        if not ranked or ranked[0][1] < BM25_ACCEPT:
            return False
        return len(ranked) < 2 or ranked[0][1] - ranked[1][1] >= BM25_MARGIN

    def resolve(self, raw: str, *, allow_partial: bool = True) -> dict:
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
        #
        # Skipped when allow_partial is False. This stage exists because a
        # mechanic writes the symptom alongside the part ("dynamo not
        # charging"), which is good evidence. A machine asked to output
        # catalog part names has no such excuse: if its proposal needs a part
        # name extracted from surrounding words, the proposal is vague, and a
        # vague proposal must not become a priced line item.
        ruled_out: set[str] = set()
        embedded = None
        if allow_partial:
            embedded, ruled_out = self._alias_ngram(*clause_tokens(raw))
        if embedded:
            return {
                "canonical": embedded,
                "confidence": ALIAS_PARTIAL_CONFIDENCE,
                "method": "alias_partial",
                "candidates": [],
            }

        tokens = rank_tokens(raw)
        ranked = [(name, score) for name, score in self._bm25_ranked(tokens) if name not in ruled_out]

        # (b) BM25 - lexical overlap, handles reordering and partial phrasing.
        #
        # In strict mode the query must also be built only from words the
        # matched part actually owns. A one-token form like "horn" is fully
        # covered by any query containing it, so "maybe a horn" scores the
        # same as "Horn". No threshold can separate those; containment can.
        # Reordering still passes ("Coolant Engine"), padding does not
        # ("possibly the radiator").
        if self._clear_winner(ranked) and (
            allow_partial
            or set(norm.split()) <= self._vocab_for.get(ranked[0][0], set())
        ):
            return {
                "canonical": ranked[0][0],
                "confidence": float(ranked[0][1]),
                "method": "bm25",
                "candidates": [name for name, score in ranked[1:3] if score > 0],
            }

        # (c) FUZZY - character-level, this is the stage that absorbs typos.
        if norm:
            for matched, score, _ in process.extract(
                norm, self._fuzzy_choices, scorer=fuzz.token_sort_ratio, limit=5
            ):
                if score < FUZZY_ACCEPT:
                    break
                if self._fuzzy_canonical[matched] in ruled_out:
                    continue
                return {
                    "canonical": self._fuzzy_canonical[matched],
                    "confidence": float(score) / 100.0,
                    "method": "fuzzy",
                    "candidates": [],
                }

        # (c2) FUZZY, word by word - a typo inside a longer phrase. Human
        # input only: a model asked for catalog names has no reason to
        # misspell them.
        corrected = self._correct_spelling(tokens) if allow_partial else None
        if corrected:
            respelt = [
                (name, score) for name, score in self._bm25_ranked(corrected) if name not in ruled_out
            ]
            if self._clear_winner(respelt):
                return {
                    "canonical": respelt[0][0],
                    "confidence": float(respelt[0][1]),
                    "method": "fuzzy",
                    "candidates": [name for name, score in respelt[1:3] if score > 0],
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
            self._fuzzy_canonical[matched]
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
            add(self._alias_ngram(*clause_tokens(raw))[0])

        if use_bm25:
            # Only names BM25 actually scored. A zero score means no shared
            # token, and admitting those would fill the list with noise and
            # starve the fuzzy stage below of its slots.
            for name, score in self._bm25_ranked(rank_tokens(raw))[:k]:
                if score > 0:
                    add(name)

        if use_fuzzy and norm and len(ordered) < k:
            for matched, score, _ in process.extract(
                norm, self._fuzzy_choices, scorer=fuzz.token_sort_ratio, limit=k
            ):
                if score >= FUZZY_ACCEPT:
                    add(self._fuzzy_canonical[matched])

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
