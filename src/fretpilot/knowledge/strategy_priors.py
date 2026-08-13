"""Registry of evidence-backed score-strategy prior families."""

from fretpilot.knowledge.country_priors import COUNTRY_PRIORS
from fretpilot.knowledge.fingerstyle_priors import FINGERSTYLE_PRIORS
from fretpilot.knowledge.jazz_priors import JAZZ_VOICING_PRIORS
from fretpilot.knowledge.metal_priors import METAL_PRIORS
from fretpilot.knowledge.picking_research import PICKING_RESEARCH
from fretpilot.knowledge.punk_priors import PUNK_PRIORS
from fretpilot.knowledge.rock_pop_priors import ROCK_POP_PRIORS
from fretpilot.knowledge.style_blues import BLUES_STYLE_KNOWLEDGE
from fretpilot.knowledge.syncopated_rhythm_priors import SYNCOPATED_RHYTHM_PRIORS

STYLE_STRATEGY_PRIORS = {
    "blues": BLUES_STYLE_KNOWLEDGE,
    "jazz": JAZZ_VOICING_PRIORS,
    "metal": METAL_PRIORS,
    "rock": ROCK_POP_PRIORS,
    "pop": ROCK_POP_PRIORS,
    "punk": PUNK_PRIORS,
    "country": COUNTRY_PRIORS,
    "fingerstyle": FINGERSTYLE_PRIORS,
    "rnb": SYNCOPATED_RHYTHM_PRIORS,
    "soul": SYNCOPATED_RHYTHM_PRIORS,
    "funk": SYNCOPATED_RHYTHM_PRIORS,
}

TECHNIQUE_STRATEGY_PRIORS = PICKING_RESEARCH
