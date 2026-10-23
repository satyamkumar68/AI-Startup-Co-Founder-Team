import os
import pytest

from run_niche_e2e import run_end_to_end_test, SELECTED_NICHE

@pytest.mark.asyncio
async def test_complete_niche_end_to_end_pipeline():
    """Execute end-to-end multi-agent pipeline on the selected niche."""
    result = await run_end_to_end_test()
    assert result is True, "End-to-end test on dental niche failed"
