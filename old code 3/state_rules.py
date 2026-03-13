"""Per-state extraction rules.

Keys are state file stems (e.g., 'alabama'). Values are rule dicts.
Default behavior (when a state is not present) is conservative mode.
"""
DEFAULT = {'mode': 'conservative'}

# Per-state overrides. Add entries here to tune heuristics for difficult pages.
OVERRIDES = {
    # Examples: 'california': {'mode': 'lenient'},
}


def get_rules(state_stem: str):
    return OVERRIDES.get(state_stem, DEFAULT)
