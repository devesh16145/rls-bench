import pytest
import typer

from train import export


def test_resolve_state_final_and_named_checkpoint():
    rec, final = export.resolve_state("20261025T191833Z", None)
    assert rec["name"] == "rl_Qwen3.5-9B_lr4e-5_s50" and final.endswith("/weights/final")
    rec, step40 = export.resolve_state("20261025T191833Z", "000040")
    assert step40 != final and "000040" in step40


def test_resolve_state_rejects_unknown():
    with pytest.raises(typer.BadParameter):
        export.resolve_state("no-such-run", None)
    with pytest.raises(typer.BadParameter):
        export.resolve_state("20261025T191833Z", "000099")
