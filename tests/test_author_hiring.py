import unittest
from unittest.mock import patch

from components.author_collaboration.author_collaboration_manager import (
    AuthorCollaborationManager,
)
from components.author_collaboration.author_collaboration_parameters import (
    AuthorCollaborationParameters as ACP,
)
from components.author_collaboration.author_factory import AuthorFactory


class AuthorHiringTest(unittest.TestCase):
    def test_retired_safety_net_authors_do_not_block_active_research_hiring(self):
        manager = AuthorCollaborationManager()

        active_author = AuthorFactory.create_author_with_explicit_params(
            author_id="active_author",
            name="Active Author",
            hire_quarter=0,
            remaining_quarters=2,
            invention_probability=0.2,
            improvement_probability=0.8,
        )
        manager.add_author(active_author)

        for i in range(5):
            retired_author = AuthorFactory.create_author_with_explicit_params(
                author_id=f"retired_author_{i}",
                name=f"Retired Author {i}",
                hire_quarter=0,
                remaining_quarters=2,
                invention_probability=0.2,
                improvement_probability=0.8,
            )
            retired_author.retire()
            manager.add_author(retired_author)

        with patch.object(ACP, "AUM_PER_AUTHOR", 30.0), patch.object(
            ACP, "MINIMUM_AUTHOR_COUNT", 2
        ):
            hired = manager._evaluate_author_hiring(
                quarter=1,
                strategy_manager=None,
                current_aum=90.0,
            )

        self.assertEqual(hired, 2)
        self.assertEqual(len(manager.get_active_authors()), 3)
        self.assertEqual(len(manager.get_all_authors()), 8)


if __name__ == "__main__":
    unittest.main()
