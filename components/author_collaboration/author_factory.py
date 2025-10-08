"""
Author Factory for Author Collaboration & Outcome Component.

This module provides factory methods for creating new authors with randomized
or explicit parameters for the hedge fund simulation.
"""

import random
import uuid
from typing import Optional

from .author import Author
from .author_collaboration_parameters import AuthorCollaborationParameters as ACP


class AuthorFactory:
    """
    Factory class for creating Author instances with appropriate initialization.
    """

    @staticmethod
    def create_new_author(name: Optional[str] = None,
                         hire_quarter: int = 0,
                         author_id: Optional[str] = None) -> Author:
        """
        Create a new author with randomized parameters.

        Args:
            name: Author name (auto-generated if None)
            hire_quarter: Quarter when author was hired
            author_id: Unique identifier (auto-generated if None)

        Returns:
            Author: Fully initialized author ready for collaboration
        """
        # Generate identifiers if not provided
        if author_id is None:
            author_id = f"author_{str(uuid.uuid4())[:8]}"

        if name is None:
            name = f"Author_{author_id[-4:]}"

        # Generate randomized research duration
        remaining_quarters = random.randint(
            ACP.AUTHOR_RESEARCH_DURATION_MIN,
            ACP.AUTHOR_RESEARCH_DURATION_MAX
        )

        # Generate randomized decision probabilities
        invention_prob = random.uniform(
            ACP.AUTHOR_INVENTION_PROBABILITY_MIN,
            ACP.AUTHOR_INVENTION_PROBABILITY_MAX
        )

        improvement_prob = random.uniform(
            ACP.AUTHOR_IMPROVEMENT_PROBABILITY_MIN,
            ACP.AUTHOR_IMPROVEMENT_PROBABILITY_MAX
        )

        # Create author instance
        author = Author(
            author_id=author_id,
            name=name,
            hire_quarter=hire_quarter,
            remaining_research_quarters=remaining_quarters,
            invention_probability=invention_prob,
            improvement_probability=improvement_prob
        )

        return author

    @staticmethod
    def create_author_with_explicit_params(author_id: str,
                                         name: str,
                                         hire_quarter: int,
                                         remaining_quarters: int,
                                         invention_probability: float,
                                         improvement_probability: float) -> Author:
        """
        Create an author with explicitly specified parameters.

        Useful for testing and scenarios where precise control is needed.

        Args:
            author_id: Unique identifier
            name: Author name
            hire_quarter: Quarter when hired
            remaining_quarters: Research time remaining
            invention_probability: Probability of choosing invention (0-1)
            improvement_probability: Probability of choosing improvement (0-1)

        Returns:
            Author: Author with specified parameters

        Raises:
            ValueError: If parameters are out of valid ranges
        """
        # Validate parameters
        if remaining_quarters < ACP.AUTHOR_RESEARCH_DURATION_MIN:
            raise ValueError(f"Remaining quarters must be >= {ACP.AUTHOR_RESEARCH_DURATION_MIN}")

        if remaining_quarters > ACP.AUTHOR_RESEARCH_DURATION_MAX:
            raise ValueError(f"Remaining quarters must be <= {ACP.AUTHOR_RESEARCH_DURATION_MAX}")

        if not (0 <= invention_probability <= 1):
            raise ValueError("Invention probability must be between 0 and 1")

        if not (0 <= improvement_probability <= 1):
            raise ValueError("Improvement probability must be between 0 and 1")

        # Create author instance
        author = Author(
            author_id=author_id,
            name=name,
            hire_quarter=hire_quarter,
            remaining_research_quarters=remaining_quarters,
            invention_probability=invention_probability,
            improvement_probability=improvement_probability
        )

        return author

    @staticmethod
    def create_test_author_pool(num_authors: int, hire_quarter: int = 0) -> list[Author]:
        """
        Create a pool of authors for testing purposes.

        Args:
            num_authors: Number of authors to create
            hire_quarter: Quarter when all authors were hired

        Returns:
            List[Author]: List of randomized authors
        """
        authors = []
        for i in range(num_authors):
            author = AuthorFactory.create_new_author(
                name=f"TestAuthor_{i+1:02d}",
                hire_quarter=hire_quarter
            )
            authors.append(author)

        return authors

    @staticmethod
    def create_author_with_specific_probabilities(invention_prob: float,
                                                improvement_prob: float,
                                                hire_quarter: int = 0) -> Author:
        """
        Create an author with specific probabilities but randomized other parameters.

        Useful for testing specific probability scenarios.

        Args:
            invention_prob: Specific invention probability
            improvement_prob: Specific improvement probability
            hire_quarter: Quarter when hired

        Returns:
            Author: Author with specified probabilities
        """
        author_id = f"author_{str(uuid.uuid4())[:8]}"
        name = f"Author_{author_id[-4:]}"

        remaining_quarters = random.randint(
            ACP.AUTHOR_RESEARCH_DURATION_MIN,
            ACP.AUTHOR_RESEARCH_DURATION_MAX
        )

        return AuthorFactory.create_author_with_explicit_params(
            author_id=author_id,
            name=name,
            hire_quarter=hire_quarter,
            remaining_quarters=remaining_quarters,
            invention_probability=invention_prob,
            improvement_probability=improvement_prob
        )

    @staticmethod
    def create_authors_with_remaining_time(num_authors: int,
                                         remaining_quarters: int,
                                         hire_quarter: int = 0) -> list[Author]:
        """
        Create authors with specific remaining research time.

        Useful for testing end-of-lifecycle scenarios.

        Args:
            num_authors: Number of authors to create
            remaining_quarters: Specific remaining research time
            hire_quarter: Quarter when hired

        Returns:
            List[Author]: Authors with specified remaining time
        """
        authors = []
        for i in range(num_authors):
            invention_prob = random.uniform(
                ACP.AUTHOR_INVENTION_PROBABILITY_MIN,
                ACP.AUTHOR_INVENTION_PROBABILITY_MAX
            )

            improvement_prob = random.uniform(
                ACP.AUTHOR_IMPROVEMENT_PROBABILITY_MIN,
                ACP.AUTHOR_IMPROVEMENT_PROBABILITY_MAX
            )

            author = AuthorFactory.create_author_with_explicit_params(
                author_id=f"author_{i+1:02d}_{str(uuid.uuid4())[:8]}",
                name=f"Author_{i+1:02d}",
                hire_quarter=hire_quarter,
                remaining_quarters=remaining_quarters,
                invention_probability=invention_prob,
                improvement_probability=improvement_prob
            )
            authors.append(author)

        return authors

    @staticmethod
    def get_author_stats_summary(authors: list[Author]) -> dict:
        """
        Get summary statistics for a pool of authors.

        Useful for analysis and validation.

        Args:
            authors: List of authors to analyze

        Returns:
            Dict: Summary statistics
        """
        if not authors:
            return {
                'total_authors': 0,
                'active_authors': 0,
                'avg_remaining_quarters': 0,
                'avg_invention_probability': 0,
                'avg_improvement_probability': 0
            }

        active_authors = [a for a in authors if a.is_active]
        total_remaining = sum(a.remaining_research_quarters for a in active_authors)
        total_invention_prob = sum(a.invention_probability for a in authors)
        total_improvement_prob = sum(a.improvement_probability for a in authors)

        return {
            'total_authors': len(authors),
            'active_authors': len(active_authors),
            'avg_remaining_quarters': total_remaining / len(active_authors) if active_authors else 0,
            'avg_invention_probability': total_invention_prob / len(authors),
            'avg_improvement_probability': total_improvement_prob / len(authors),
            'authors_can_invent': len([a for a in active_authors if a.can_attempt_invention()]),
            'authors_available': len([a for a in active_authors if a.is_available_for_activity()])
        }