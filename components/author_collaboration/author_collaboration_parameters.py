"""
Author Collaboration & Outcome Component Parameters

This module contains all tunable parameters for the Author Collaboration & Outcome Component.
These parameters control group formation, collaboration success rates, research durations,
and author lifecycle mechanics.
"""

class AuthorCollaborationParameters:
    """
    Centralized parameter configuration for Author Collaboration Component
    """

    # =============================================================================
    # AUTHOR RESEARCH DURATION PARAMETERS
    # =============================================================================

    # Initial research duration when author is hired (quarters)
    AUTHOR_RESEARCH_DURATION_MIN = 2
    AUTHOR_RESEARCH_DURATION_MAX = 4  # Inclusive: 2, 3, or 4 quarters

    # =============================================================================
    # AUTHOR DECISION PROBABILITY PARAMETERS
    # =============================================================================

    # Individual author invention probability (sampled once per author at hiring)
    AUTHOR_INVENTION_PROBABILITY_MIN = 0.1
    AUTHOR_INVENTION_PROBABILITY_MAX = 0.5

    # Individual author improvement probability (sampled once per author at hiring)
    AUTHOR_IMPROVEMENT_PROBABILITY_MIN = 0.7
    AUTHOR_IMPROVEMENT_PROBABILITY_MAX = 0.99

    # =============================================================================
    # GROUP FORMATION PARAMETERS
    # =============================================================================

    # Group size limits for all activities
    GROUP_SIZE_MIN = 1
    GROUP_SIZE_MAX = 3

    # Group success probability calculation: average of member probabilities

    # =============================================================================
    # IMPROVEMENT GROUP PARAMETERS
    # =============================================================================

    # Improvement type selection (when group succeeds)
    PROB_OF_IMPROVE_RETURN = 0.9
    PROB_OF_IMPROVE_CAPACITY = 0.1

    # Improvement execution (immediate results)
    IMPROVEMENT_QUARTERS_REQUIRED = 1  # Always 1 quarter

    # =============================================================================
    # INVENTION GROUP PARAMETERS
    # =============================================================================

    # Invention process duration
    INVENTION_QUARTERS_REQUIRED = 2  # Always 2 quarters
    INVENTION_MIN_REMAINING_QUARTERS = 2  # Must have 2+ quarters to start invention

    # Invention group state tracking
    INVENTION_GROUP_ID_PREFIX = "invention_group"

    # =============================================================================
    # AUTHOR HIRING PARAMETERS
    # =============================================================================

    # Initial author count at fund inception
    INITIAL_AUTHOR_COUNT = 2  # Start with 2 authors

    # Hiring trigger threshold
    AUTHOR_HIRE_THRESHOLD_AUM = 0.0  # Start hiring at any positive AUM (in millions)

    # AUM-per-author hiring model
    AUM_PER_AUTHOR = 20.0  # Target $20M AUM per author (in millions)
    # Example: 100M AUM / 20M per author = 5 target authors

    # Minimum author count
    MINIMUM_AUTHOR_COUNT = 2  # Always maintain at least 2 active authors
    # Overrides AUM-per-author calculation if current authors < minimum

    # =============================================================================
    # SAFETY NET PARAMETERS
    # =============================================================================

    # Universal minimum guarantee
    AUTHOR_GUARANTEED_RETURN = 1.0  # $1M lifetime minimum (in millions)

    # Safety net calculation logic: max(performance_share, safety_net_minimum)



    # =============================================================================
    # VALIDATION PARAMETERS
    # =============================================================================

    @classmethod
    def validate_parameters(cls):
        """Validate parameter consistency and ranges"""

        # Research duration validation
        assert cls.AUTHOR_RESEARCH_DURATION_MIN >= 1, "Research duration must be at least 1 quarter"
        assert cls.AUTHOR_RESEARCH_DURATION_MAX >= cls.AUTHOR_RESEARCH_DURATION_MIN, "Max duration must be >= min duration"
        assert cls.AUTHOR_RESEARCH_DURATION_MAX <= 10, "Research duration should be reasonable"

        # Probability validation
        assert 0 <= cls.AUTHOR_INVENTION_PROBABILITY_MIN <= 1, "Invention probability must be between 0 and 1"
        assert 0 <= cls.AUTHOR_INVENTION_PROBABILITY_MAX <= 1, "Invention probability must be between 0 and 1"
        assert cls.AUTHOR_INVENTION_PROBABILITY_MIN <= cls.AUTHOR_INVENTION_PROBABILITY_MAX, "Min <= Max for invention probability"

        assert 0 <= cls.AUTHOR_IMPROVEMENT_PROBABILITY_MIN <= 1, "Improvement probability must be between 0 and 1"
        assert 0 <= cls.AUTHOR_IMPROVEMENT_PROBABILITY_MAX <= 1, "Improvement probability must be between 0 and 1"
        assert cls.AUTHOR_IMPROVEMENT_PROBABILITY_MIN <= cls.AUTHOR_IMPROVEMENT_PROBABILITY_MAX, "Min <= Max for improvement probability"

        # Group size validation
        assert cls.GROUP_SIZE_MIN >= 1, "Group size must be at least 1"
        assert cls.GROUP_SIZE_MAX >= cls.GROUP_SIZE_MIN, "Max group size must be >= min group size"
        assert cls.GROUP_SIZE_MAX <= 5, "Group size should be reasonable"

        # Improvement type probabilities must sum to 1
        assert abs((cls.PROB_OF_IMPROVE_RETURN + cls.PROB_OF_IMPROVE_CAPACITY) - 1.0) < 0.001, "Improvement probabilities must sum to 1"

        # Invention validation
        assert cls.INVENTION_QUARTERS_REQUIRED >= 1, "Invention must take at least 1 quarter"
        assert cls.INVENTION_MIN_REMAINING_QUARTERS >= cls.INVENTION_QUARTERS_REQUIRED, "Must have enough quarters for invention"

        # Safety net validation
        assert cls.AUTHOR_GUARANTEED_RETURN > 0, "Guaranteed return must be positive"

        # Hiring validation
        assert cls.INITIAL_AUTHOR_COUNT >= 0, "Initial author count must be non-negative"
        assert cls.AUTHOR_HIRE_THRESHOLD_AUM >= 0, "Hire threshold AUM must be non-negative"
        assert cls.AUM_PER_AUTHOR > 0, "AUM per author must be positive"
        assert cls.MINIMUM_AUTHOR_COUNT >= 0, "Minimum author count must be non-negative"

        return True

# Validate parameters on import
AuthorCollaborationParameters.validate_parameters()