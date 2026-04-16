"""
pipeline.py

runs all the preprocessing steps in order then finds candidate pairs

cleaner -> language -> abbreviations -> embeddings

TODO: add caching so we don't re-translate the same records every run
"""

from __future__ import annotations
from typing import Any, Sequence

from src.preprocessing.cleaner import clean_record
from src.preprocessing.language import enrich_record_with_translations
from src.preprocessing.abbreviations import expand_record_abbreviations
from src.preprocessing.embeddings import run_embedding_pipeline
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PreprocessingPipeline:

    def __init__(
        self,
        cleaner_module: Any | None = None,
        language_module: Any | None = None,
        abbreviations_module: Any | None = None,
        embeddings_module: Any | None = None,
    ) -> None:
        if cleaner_module is None:
            from src.preprocessing import cleaner as cleaner_module
        if language_module is None:
            from src.preprocessing import language as language_module
        if abbreviations_module is None:
            from src.preprocessing import abbreviations as abbreviations_module
        if embeddings_module is None:
            from src.preprocessing import embeddings as embeddings_module

        self.cleaner = cleaner_module
        self.language = language_module
        self.abbreviations = abbreviations_module
        self.embeddings = embeddings_module

    def run(self, records: Sequence[dict[str, Any]]) -> Any:
        if records is None:
            raise ValueError("records cannot be None")

        current_records = list(records)
        current_records = self._run_cleaner(current_records)
        current_records = self._run_language(current_records)
        current_records = self._run_abbreviations(current_records)
        candidate_pairs = self._run_embeddings(current_records)
        return candidate_pairs

    __call__ = run

    def _run_cleaner(self, records):
        return self._call_stage(self.cleaner, ["clean_records", "clean", "process", "run", "transform"], records, "cleaner")

    def _run_language(self, records):
        return self._call_stage(self.language, ["detect_languages", "annotate_language", "detect", "process", "run", "transform"], records, "language")

    def _run_abbreviations(self, records):
        return self._call_stage(self.abbreviations, ["expand_abbreviations", "normalize_abbreviations", "expand", "process", "run", "transform"], records, "abbreviations")

    def _run_embeddings(self, records):
        return self._call_stage(self.embeddings, ["generate_candidate_pairs", "build_candidate_pairs", "candidate_pairs", "embed_and_block", "process", "run", "transform"], records, "embeddings")

    @staticmethod
    def _call_stage(stage: Any, method_names: list[str], data: Any, stage_name: str) -> Any:
        if callable(stage):
            return stage(data)

        for method_name in method_names:
            method = getattr(stage, method_name, None)
            if callable(method):
                return method(data)

        available = [n for n in dir(stage) if not n.startswith("_") and callable(getattr(stage, n, None))]
        raise AttributeError(f"couldn't find entry point for '{stage_name}'. tried: {method_names}. available: {available}")


# wrappers so the pipeline class can call our per-record functions
def _batch_clean(records):
    return [clean_record(r) for r in records]

def _batch_translate(records):
    return [enrich_record_with_translations(r) for r in records]

def _batch_expand(records):
    return [expand_record_abbreviations(r) for r in records]

def _batch_embed(records):
    _, _, pairs = run_embedding_pipeline(records)
    return pairs


class MDMPreprocessingPipeline(PreprocessingPipeline):
    def _run_cleaner(self, records):
        return _batch_clean(records)

    def _run_language(self, records):
        return _batch_translate(records)

    def _run_abbreviations(self, records):
        return _batch_expand(records)

    def _run_embeddings(self, records):
        return _batch_embed(records)


def run_pipeline(records: list[dict]) -> tuple[list[dict], list[tuple]]:
    if not records:
        logger.warning("got empty records list, nothing to do")
        return [], []

    logger.info(f"starting pipeline on {len(records)} records")

    # clean -> translate -> expand abbreviations -> embed
    processed = _batch_clean(records)
    processed = _batch_translate(processed)
    processed = _batch_expand(processed)
    pairs = _batch_embed(processed)

    logger.info(f"done — found {len(pairs)} candidate pairs")
    return processed, pairs


if __name__ == "__main__":
    from src.utils.loader import load_records

    records = load_records("data/test/sample_records.csv")
    processed, pairs = run_pipeline(records)

    print(f"\nprocessed {len(processed)} records, found {len(pairs)} pairs")
    for a, b, sim in pairs:
        name_a = processed[a].get("name_expanded") or processed[a].get("name_clean", "")
        name_b = processed[b].get("name_expanded") or processed[b].get("name_clean", "")
        print(f"  {sim:.3f}  {name_a!r}  <->  {name_b!r}")