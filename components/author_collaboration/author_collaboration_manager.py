"""
Author Collaboration Manager for Author Collaboration & Outcome Component.

This module provides the main orchestrator for managing collaborative research
activities and quarterly group decisions of all authors in the hedge fund.
"""

import random
import uuid
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict

from .author import Author, GroupActivity
from .author_factory import AuthorFactory
from .author_collaboration_parameters import AuthorCollaborationParameters as ACP


class AuthorCollaborationManager:
    """
    Main component for managing author collaboration and outcomes.

    Orchestrates quarterly cycles of group formation, collaborative activities,
    and outcome tracking for strategy invention and improvement.
    """

    def __init__(self):
        """Initialize the Author Collaboration Manager."""
        self.authors: List[Author] = []
        self.authors_by_id: Dict[str, Author] = {}
        self.quarterly_group_activities: Dict[int, List[GroupActivity]] = {}
        self.active_invention_groups: Dict[str, List[Author]] = {}
        self.author_hiring_rate: float = 0.0

    def add_author(self, author: Author) -> None:
        """
        Add an author to the fund.

        Args:
            author: Author to add
        """
        if author.author_id in self.authors_by_id:
            raise ValueError(f"Author {author.author_id} already exists")

        self.authors.append(author)
        self.authors_by_id[author.author_id] = author

    def get_author_by_id(self, author_id: str) -> Optional[Author]:
        """Get author by ID."""
        return self.authors_by_id.get(author_id)

    def get_all_authors(self) -> List[Author]:
        """Get all authors (including retired)."""
        return self.authors

    def get_active_authors(self) -> List[Author]:
        """Get all currently active authors."""
        return [author for author in self.authors if author.is_active]

    def get_available_authors(self) -> List[Author]:
        """Get authors available for new activities this quarter."""
        return [
            author for author in self.authors
            if author.is_available_for_activity()
        ]

    def process_quarterly_collaboration_cycle(self, quarter: int, strategy_manager, current_aum: float = None) -> Tuple[List[GroupActivity], Dict[str, int]]:
        """
        Main quarterly processing function for collaborative activities.

        Args:
            quarter: Current quarter number
            strategy_manager: Strategy Lifecycle Component manager
            current_aum: Current fund AUM (optional, for hiring decisions)

        Returns:
            Tuple[List[GroupActivity], Dict[str, int]]: Group activities and quarterly stats
                Stats dict contains: authors_hired, authors_retired, strategies_created,
                capacity_improvements, return_improvements
        """
        group_activities = []
        stats = {
            'authors_hired': 0,
            'authors_retired': 0,
            'strategies_created': 0,
            'capacity_improvements': 0,
            'return_improvements': 0
        }

        # Phase 1: Hire new authors FIRST (so they can work this quarter)
        stats['authors_hired'] = self._evaluate_author_hiring(quarter, strategy_manager, current_aum)

        # Phase 2: Continue ongoing invention groups (quarter 2 of invention)
        ongoing_inventions = self._complete_ongoing_inventions(quarter, strategy_manager)
        group_activities.extend(ongoing_inventions)

        # Phase 3: Available authors make decisions
        available_authors = self.get_available_authors()
        improvement_candidates, invention_candidates = self._collect_author_decisions(available_authors)

        # Phase 4: Form improvement groups, assign strategies, and consolidate
        improvement_groups = self._form_improvement_groups(improvement_candidates)
        assigned_groups = self._assign_strategies_to_groups(improvement_groups, strategy_manager)
        consolidated_groups = self._consolidate_groups_by_strategy(assigned_groups)
        improvement_results, capacity_improvements, return_improvements = self._execute_improvement_groups(consolidated_groups, quarter, strategy_manager)
        group_activities.extend(improvement_results)
        stats['capacity_improvements'] = capacity_improvements
        stats['return_improvements'] = return_improvements

        # Phase 5: Form invention groups and start process
        invention_groups = self._form_invention_groups(invention_candidates)
        invention_starts = self._start_invention_groups(invention_groups, quarter)
        group_activities.extend(invention_starts)

        # Phase 6: Process retirements at END (after authors have worked this quarter)
        stats['authors_retired'] = self._update_author_progress()

        # Count strategies created this quarter
        stats['strategies_created'] = len([a for a in group_activities
                                          if a.activity_type == 'invention_complete' and a.success])

        # Count strategies still available for improvement
        active_strategies = strategy_manager.get_active_strategies()
        stats['strategies_improvable_capacity'] = sum(1 for s in active_strategies if s.can_improve_capacity())
        stats['strategies_improvable_return'] = sum(1 for s in active_strategies if s.can_improve_returns())

        # Store quarterly activities
        self.quarterly_group_activities[quarter] = group_activities

        return group_activities, stats

    def _update_author_progress(self) -> int:
        """
        Update all author research progress by one quarter.

        Returns:
            int: Number of authors who retired this quarter
        """
        retired_count = 0
        for author in self.authors:
            was_active = author.is_active
            author.advance_quarter()
            if was_active and not author.is_active:
                retired_count += 1
        return retired_count

    def _collect_author_decisions(self, available_authors: List[Author]) -> Tuple[List[Author], List[Author]]:
        """
        Collect individual author decisions and sort into activity pools.

        Args:
            available_authors: Authors available for activities

        Returns:
            Tuple[List[Author], List[Author]]: (improvement_candidates, invention_candidates)
        """
        improvement_candidates = []
        invention_candidates = []

        for author in available_authors:
            # Authors with 2+ quarters can choose invention or improvement
            if author.can_attempt_invention():
                if random.random() < author.invention_probability:
                    invention_candidates.append(author)
                else:
                    improvement_candidates.append(author)
            else:
                # Authors with 1 quarter can only do improvement
                improvement_candidates.append(author)

        return improvement_candidates, invention_candidates

    def _form_improvement_groups(self, candidates: List[Author]) -> List[List[Author]]:
        """
        Form improvement groups of 1-3 authors.

        Args:
            candidates: Authors wanting to do improvements

        Returns:
            List[List[Author]]: List of improvement groups
        """
        groups = []
        remaining_candidates = candidates.copy()

        while remaining_candidates:
            group_size = random.randint(ACP.GROUP_SIZE_MIN,
                                      min(ACP.GROUP_SIZE_MAX, len(remaining_candidates)))
            group = random.sample(remaining_candidates, group_size)
            groups.append(group)

            for author in group:
                remaining_candidates.remove(author)

        return groups

    def _assign_strategies_to_groups(self, groups: List[List[Author]], strategy_manager) -> List[Dict]:
        """
        Assign target strategies and improvement types to groups.

        Only assigns strategies that have room to improve (either returns or capacity).
        The improvement type is selected based on what the strategy can actually be improved in.

        Args:
            groups: List of improvement groups (list of authors)
            strategy_manager: Strategy Lifecycle Component manager

        Returns:
            List[Dict]: List of assigned groups with structure:
                {
                    'authors': List[Author],
                    'target_strategy': Strategy,
                    'improvement_type': str ('return' or 'capacity')
                }
        """
        # Get only strategies that have room to improve
        improvable_strategies = strategy_manager.get_improvable_strategies()
        assigned_groups = []

        for group in groups:
            if not improvable_strategies:
                # No improvable strategies available - group will fail later
                assigned_groups.append({
                    'authors': group,
                    'target_strategy': None,
                    'improvement_type': None
                })
                continue

            # Randomly select an improvable strategy
            target_strategy = random.choice(improvable_strategies)

            # Determine which improvement types are possible for this strategy
            can_improve_return = target_strategy.can_improve_returns()
            can_improve_capacity = target_strategy.can_improve_capacity()

            # Select improvement type based on what's possible
            if can_improve_return and can_improve_capacity:
                # Both possible - use probability to decide
                improvement_type = ('return' if random.random() < ACP.PROB_OF_IMPROVE_RETURN
                                  else 'capacity')
            elif can_improve_return:
                # Only return improvement possible
                improvement_type = 'return'
            elif can_improve_capacity:
                # Only capacity improvement possible
                improvement_type = 'capacity'
            else:
                # This shouldn't happen (strategy was in improvable list)
                # But handle it gracefully
                improvement_type = None

            assigned_groups.append({
                'authors': group,
                'target_strategy': target_strategy,
                'improvement_type': improvement_type
            })

        return assigned_groups

    def _consolidate_groups_by_strategy(self, assigned_groups: List[Dict]) -> List[Dict]:
        """
        Consolidate multiple groups working on same strategy into single groups.

        If multiple groups are assigned to the same strategy, merge them and use
        majority vote to decide improvement type (capacity vs return).

        Args:
            assigned_groups: List of assigned groups from _assign_strategies_to_groups

        Returns:
            List[Dict]: Consolidated groups (one per strategy)
        """
        # Group by strategy
        strategy_groups = defaultdict(list)

        for assigned_group in assigned_groups:
            if assigned_group['target_strategy'] is None:
                # No strategy assigned - keep as-is (will fail later)
                strategy_groups[None].append(assigned_group)
            else:
                strategy_id = assigned_group['target_strategy'].strategy_id
                strategy_groups[strategy_id].append(assigned_group)

        # Consolidate
        consolidated = []

        for strategy_id, groups_list in strategy_groups.items():
            if strategy_id is None:
                # Groups with no strategy - keep separate
                consolidated.extend(groups_list)
                continue

            if len(groups_list) == 1:
                # Only one group for this strategy - keep as-is
                consolidated.append(groups_list[0])
            else:
                # Multiple groups on same strategy - CONSOLIDATE!
                all_authors = []
                capacity_votes = 0
                return_votes = 0

                for group_dict in groups_list:
                    all_authors.extend(group_dict['authors'])
                    if group_dict['improvement_type'] == 'capacity':
                        capacity_votes += len(group_dict['authors'])
                    else:
                        return_votes += len(group_dict['authors'])

                # Majority vote decides improvement type
                if capacity_votes > return_votes:
                    final_type = 'capacity'
                elif return_votes > capacity_votes:
                    final_type = 'return'
                else:
                    # Tie - random choice
                    final_type = 'capacity' if random.random() < 0.5 else 'return'

                # Create consolidated group
                consolidated.append({
                    'authors': all_authors,
                    'target_strategy': groups_list[0]['target_strategy'],  # Same strategy for all
                    'improvement_type': final_type
                })

        return consolidated

    def _execute_improvement_groups(self, groups: List[Dict], quarter: int,
                                  strategy_manager) -> Tuple[List[GroupActivity], int, int]:
        """
        Execute improvement attempts for consolidated groups.

        Args:
            groups: List of consolidated group dicts with 'authors', 'target_strategy', 'improvement_type'
            quarter: Current quarter
            strategy_manager: Strategy Lifecycle Component manager

        Returns:
            Tuple[List[GroupActivity], int, int]: Activities, capacity_improvements, return_improvements
        """
        activities = []
        capacity_improvements = 0
        return_improvements = 0

        for group_dict in groups:
            authors = group_dict['authors']
            target_strategy = group_dict['target_strategy']
            improvement_type = group_dict['improvement_type']

            if target_strategy is None:
                # No strategy assigned - record failed attempt
                activity = GroupActivity(
                    group_members=[a.author_id for a in authors],
                    group_id=f"improvement_group_{quarter}_{str(uuid.uuid4())[:8]}",
                    activity_type='improvement',
                    quarter=quarter,
                    success=False
                )
                activities.append(activity)
                continue

            # Create activity record first
            activity = GroupActivity(
                group_members=[a.author_id for a in authors],
                group_id=f"improvement_group_{quarter}_{str(uuid.uuid4())[:8]}",
                activity_type='improvement',
                quarter=quarter,
                success=None  # Will be set after probability calculation
            )

            # Calculate group success probability (average of members)
            individual_probs = [author.improvement_probability for author in authors]
            group_prob = activity.calculate_group_success_probability(individual_probs)
            success = random.random() < group_prob
            activity.success = success

            if success:
                # Execute improvement with pre-assigned strategy and type
                improvements = [(target_strategy.strategy_id, improvement_type, quarter)]
                results = strategy_manager.process_improvements(improvements)

                if results.get(target_strategy.strategy_id, False):
                    # Improvement succeeded
                    activity.target_strategy_id = target_strategy.strategy_id
                    activity.improvement_type = improvement_type

                    # Track improvement type
                    if improvement_type == 'capacity':
                        capacity_improvements += 1
                    elif improvement_type == 'return':
                        return_improvements += 1

                    # Update ownership splits: add improvement contributors and redistribute EQUALLY
                    current_owners = set(target_strategy.ownership_splits.keys())
                    group_member_ids = [a.author_id for a in authors]
                    new_contributors = [author_id for author_id in group_member_ids
                                       if author_id not in current_owners]

                    if new_contributors:
                        # Add new contributors to ownership
                        all_owners = list(current_owners) + new_contributors
                        # Redistribute equally among ALL contributors
                        equal_share = 1.0 / len(all_owners)
                        target_strategy.ownership_splits = {
                            author_id: equal_share for author_id in all_owners
                        }

                    # Record success for all group members
                    for author in authors:
                        author.record_successful_contribution(
                            activity_type=f'improve_{improvement_type}',
                            strategy_id=target_strategy.strategy_id,
                            quarter=quarter,
                            group_members=group_member_ids
                        )
                else:
                    # Strategy improvement failed
                    activity.success = False
                    group_member_ids = [a.author_id for a in authors]
                    for author in authors:
                        author.record_failed_contribution(
                            activity_type=f'improve_{improvement_type}',
                            quarter=quarter,
                            group_members=group_member_ids
                        )
            else:
                # Group failed probability check
                group_member_ids = [a.author_id for a in authors]
                for author in authors:
                    author.record_failed_contribution(
                        activity_type='improvement',
                        quarter=quarter,
                        group_members=group_member_ids
                    )

            activities.append(activity)

        return activities, capacity_improvements, return_improvements

    def _form_invention_groups(self, candidates: List[Author]) -> List[List[Author]]:
        """
        Form invention groups of 1-3 authors.

        Args:
            candidates: Authors wanting to do invention

        Returns:
            List[List[Author]]: List of invention groups
        """
        groups = []
        remaining_candidates = candidates.copy()

        while remaining_candidates:
            group_size = random.randint(ACP.GROUP_SIZE_MIN,
                                      min(ACP.GROUP_SIZE_MAX, len(remaining_candidates)))
            group = random.sample(remaining_candidates, group_size)
            groups.append(group)

            for author in group:
                remaining_candidates.remove(author)

        return groups

    def _start_invention_groups(self, groups: List[List[Author]], quarter: int) -> List[GroupActivity]:
        """
        Start 2-quarter invention process for groups.

        Args:
            groups: List of invention groups
            quarter: Current quarter

        Returns:
            List[GroupActivity]: Invention start activities
        """
        activities = []

        for group in groups:
            # Create invention group with unique ID
            group_id = f"invention_group_{quarter}_{str(uuid.uuid4())[:8]}"

            # Mark all authors as starting invention
            for author in group:
                author.start_invention_process(group_id)

            # Store active invention group
            self.active_invention_groups[group_id] = group

            # Create activity record
            individual_probs = [author.invention_probability for author in group]
            activity = GroupActivity(
                group_members=[a.author_id for a in group],
                group_id=group_id,
                activity_type='invention_start',
                quarter=quarter,
                success=None  # To be determined in quarter 2
            )
            activity.calculate_group_success_probability(individual_probs)

            activities.append(activity)

        return activities

    def _complete_ongoing_inventions(self, quarter: int, strategy_manager) -> List[GroupActivity]:
        """
        Complete invention groups in their second quarter.

        Args:
            quarter: Current quarter
            strategy_manager: Strategy Lifecycle Component manager

        Returns:
            List[GroupActivity]: Completed invention activities
        """
        activities = []

        # Find all authors in quarter 2 of invention
        inventing_authors = [a for a in self.authors
                           if a.current_activity_state == 'inventing_quarter_1']

        # Group by invention_group_id
        invention_groups = {}
        for author in inventing_authors:
            group_id = author.invention_group_id
            if group_id not in invention_groups:
                invention_groups[group_id] = []
            invention_groups[group_id].append(author)

        # Execute invention attempt for each group
        for group_id, group in invention_groups.items():
            # Calculate group success probability (average of members)
            individual_probs = [author.invention_probability for author in group]
            group_prob = sum(individual_probs) / len(individual_probs)
            success = random.random() < group_prob

            # Create activity record
            activity = GroupActivity(
                group_members=[a.author_id for a in group],
                group_id=group_id,
                activity_type='invention_complete',
                quarter=quarter,
                success=success
            )
            activity.calculate_group_success_probability(individual_probs)

            if success:
                # Create new strategy using StrategyFactory
                from components.strategy_lifecycle.strategy_factory import StrategyFactory
                new_strategy = StrategyFactory.create_new_strategy(group, quarter)
                strategy_manager.add_strategy(new_strategy)
                activity.created_strategy_id = new_strategy.strategy_id

                # Record success for all group members
                group_member_ids = [a.author_id for a in group]
                for author in group:
                    author.record_successful_contribution(
                        activity_type='invention',
                        strategy_id=new_strategy.strategy_id,
                        quarter=quarter,
                        group_members=group_member_ids
                    )
            else:
                # Invention failed
                group_member_ids = [a.author_id for a in group]
                for author in group:
                    author.record_failed_contribution(
                        activity_type='invention',
                        quarter=quarter,
                        group_members=group_member_ids
                    )

            # Reset all group members to available state
            for author in group:
                author.complete_invention_process()

            # Remove from active invention groups
            if group_id in self.active_invention_groups:
                del self.active_invention_groups[group_id]

            activities.append(activity)

        return activities

    def _evaluate_author_hiring(self, quarter: int, strategy_manager, current_aum: float = None) -> int:
        """
        Evaluate whether to hire new authors based on AUM-per-author model.

        Hiring model based on cumulative safety net enrollment:
        - Target cumulative authors = max(MINIMUM_AUTHOR_COUNT, current_aum / AUM_PER_AUTHOR)
        - Count authors in safety net program (contributed to strategies, lifetime < $4M)
        - Hire = target - current_in_safety_net
        - Only hire above threshold AUM (except for minimum requirement)

        The AUM-per-author ratio supports authors through their entire career up to $4M guarantee,
        not just while actively working. So we count cumulative authors in safety net, not just active.

        Args:
            quarter: Current quarter
            strategy_manager: Strategy Lifecycle Component manager
            current_aum: Current fund AUM (if None, uses total_capacity as fallback)

        Returns:
            int: Number of authors hired this quarter
        """
        from components.performance_allocation.performance_allocation_parameters import PerformanceAllocationParameters as PAP

        # Get AUM (prefer actual AUM, fallback to total capacity)
        if current_aum is None:
            portfolio_metrics = strategy_manager.get_portfolio_metrics()
            current_aum = portfolio_metrics.get('total_capacity', 0)

        # Count authors currently in safety net program
        # These are authors who have contributed to strategies and have lifetime payments < $4M guarantee
        authors_in_safety_net = self._count_authors_in_safety_net(strategy_manager)

        # Calculate target cumulative author count based on AUM-per-author model
        target_cumulative_authors_from_aum = int(current_aum / ACP.AUM_PER_AUTHOR)

        # Enforce minimum author count (overrides AUM-based calculation)
        target_cumulative_authors = max(ACP.MINIMUM_AUTHOR_COUNT, target_cumulative_authors_from_aum)

        # For AUM-based hiring (above minimum), check threshold
        if authors_in_safety_net >= ACP.MINIMUM_AUTHOR_COUNT:
            if current_aum <= ACP.AUTHOR_HIRE_THRESHOLD_AUM:
                return 0

        # Hire multiple authors to reach target cumulative count
        if authors_in_safety_net < target_cumulative_authors:
            authors_to_hire = target_cumulative_authors - authors_in_safety_net
            for _ in range(authors_to_hire):
                new_author = AuthorFactory.create_new_author(hire_quarter=quarter)
                self.add_author(new_author)
            return authors_to_hire

        return 0

    def _count_authors_in_safety_net(self, strategy_manager) -> int:
        """
        Count authors currently in the safety net program.

        Authors are in safety net if:
        1. They have contributed to at least one strategy (enrolled)
        2. Their lifetime payments are below the $4M guarantee

        This includes both active and retired authors.

        Args:
            strategy_manager: Strategy Lifecycle Component manager

        Returns:
            int: Number of authors in safety net program
        """
        from components.performance_allocation.performance_allocation_parameters import PerformanceAllocationParameters as PAP

        # Get all author_ids who have contributed to strategies
        enrolled_author_ids = set()
        for strategy in strategy_manager.get_all_strategies():
            if strategy.ownership_splits:
                enrolled_author_ids.update(strategy.ownership_splits.keys())

        # Count how many are below the guarantee threshold
        count = 0
        for author_id in enrolled_author_ids:
            author = self.get_author_by_id(author_id)
            if author is not None:
                if author.get_lifetime_payments() < PAP.AUTHOR_GUARANTEED_RETURN:
                    count += 1

        return count

    def get_strategy_contributors(self) -> Dict[str, List[str]]:
        """
        Get current contributor list for each strategy (for Performance Allocation).

        Returns:
            Dict[str, List[str]]: Mapping of strategy_id to list of contributor author_ids
        """
        contributors = {}

        for author in self.authors:
            # Add to strategies created
            for strategy_id in author.strategies_created:
                if strategy_id not in contributors:
                    contributors[strategy_id] = []
                if author.author_id not in contributors[strategy_id]:
                    contributors[strategy_id].append(author.author_id)

            # Add to strategies improved
            for strategy_id in author.strategies_improved:
                if strategy_id not in contributors:
                    contributors[strategy_id] = []
                if author.author_id not in contributors[strategy_id]:
                    contributors[strategy_id].append(author.author_id)

        return contributors

    def get_author_contribution_summary(self, author_id: str) -> Optional[Dict[str, Any]]:
        """
        Get author's complete contribution record (for Performance Allocation).

        Args:
            author_id: Author to get summary for

        Returns:
            Optional[Dict]: Author contribution summary or None if not found
        """
        author = self.get_author_by_id(author_id)
        if author is None:
            return None

        return author.get_contribution_summary()

    def get_all_author_summaries(self) -> Dict[str, Dict[str, Any]]:
        """
        Get contribution summaries for all authors.

        Returns:
            Dict[str, Dict]: Mapping of author_id to contribution summary
        """
        summaries = {}
        for author in self.authors:
            summaries[author.author_id] = author.get_contribution_summary()
        return summaries

    def get_quarterly_activity_summary(self, quarter: int) -> Optional[Dict[str, Any]]:
        """
        Get summary of all activities for a specific quarter.

        Args:
            quarter: Quarter to get summary for

        Returns:
            Optional[Dict]: Quarter activity summary or None if no activities
        """
        activities = self.quarterly_group_activities.get(quarter, [])
        if not activities:
            return None

        total_groups = len(activities)
        successful_groups = len([a for a in activities if a.success])
        improvement_activities = [a for a in activities if a.is_improvement_activity()]
        invention_activities = [a for a in activities if a.is_invention_activity()]

        return {
            'quarter': quarter,
            'total_groups': total_groups,
            'successful_groups': successful_groups,
            'success_rate': successful_groups / total_groups if total_groups > 0 else 0,
            'improvement_groups': len(improvement_activities),
            'invention_groups': len(invention_activities),
            'active_authors': len(self.get_active_authors()),
            'available_authors': len(self.get_available_authors()),
            'activities': [a.get_summary() for a in activities]
        }