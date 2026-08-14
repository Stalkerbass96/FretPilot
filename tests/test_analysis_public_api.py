from fretpilot.analysis import (
    analyze_guitar_stream_section_aware as public_stream_analysis,
    analyze_guitar_track_by_sections as public_section_analysis,
)
from fretpilot.analysis.section_aware import (
    analyze_guitar_stream_section_aware as compatibility_stream_analysis,
    analyze_guitar_track_by_sections as compatibility_section_analysis,
)
from fretpilot.analysis.section_execution import (
    analyze_guitar_stream_section_aware as canonical_stream_analysis,
    analyze_guitar_track_by_sections as canonical_section_analysis,
)


def test_section_aware_import_paths_share_one_implementation():
    assert public_stream_analysis is canonical_stream_analysis
    assert compatibility_stream_analysis is canonical_stream_analysis
    assert public_section_analysis is canonical_section_analysis
    assert compatibility_section_analysis is canonical_section_analysis
